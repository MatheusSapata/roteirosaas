from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

import anyio
from functools import partial
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.api.deps import get_db
from app.api.v1.endpoints.pages import (
    derive_cover_image_from_config,
    ensure_agency_member,
    ensure_pages_editor_permission,
    normalize_config,
    resolve_agency_plan,
    enforce_page_limits,
)
from app.models.page import Page
from app.db.session import SessionLocal
from app.models.ai_assistant_message import AiAssistantMessage
from app.models.ai_assistant_usage import AiAssistantUsage
from app.models.user import User
from app.schemas.page import PageOut
from app.api.v1.endpoints.flight_sections import import_flight_journeys
from app.services.ai_assistant import (
    CHAT_IMAGE_TYPES,
    ChatAttachment,
    ChatMessage,
    build_page_base_config_from_reply,
    generate_ai_assistant_reply,
    stream_ai_assistant_reply,
    transcribe_audio,
)
from app.models.media import MediaAsset
from app.services.ai_assistant_context import build_agency_context
from app.services.image_optimizer import optimize_image
from app.services.media_storage import media_storage
from app.services.stock_images import clear_photo_queries, fill_section_photos
from app.services.ai_assistant_usage import (
    check_ai_assistant_message_limit,
    get_ai_assistant_usage_record,
    get_ai_assistant_usage_summary,
    increment_ai_assistant_message_usage,
)
from app.services.construtor_prompt import get_active_gpt_model

router = APIRouter()
logger = logging.getLogger(__name__)


class AiAssistantChatResponse(BaseModel):
    reply: str


class AiAssistantTranscriptionResponse(BaseModel):
    text: str


class AiAssistantConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AiAssistantHistoryMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class AiAssistantCreatePageBaseRequest(BaseModel):
    page_id: int
    reply: str
    # Opção "Inserir imagens" do assistente: desligada, nenhuma foto de banco entra.
    include_images: bool = True
    # Fotos que já estão na página: a troca de foto não devolve a mesma.
    current_photos: list[str] = Field(default_factory=list, max_length=400)
    # Dias de cada Roteiro dia a dia da página ({identificador: dias}): a troca só da foto do
    # roteiro não traz os dias, e cada dia recebe uma foto.
    itinerary_days: dict[str, int] = Field(default_factory=dict)


class AiAssistantCreatePageBaseResponse(BaseModel):
    page: PageOut


class AiAssistantUsageResponse(BaseModel):
    period_key: str
    used: int
    limit: int | None = None
    remaining: int | None = None
    unlimited: bool = False
    renewal_at: datetime | None = None


def _pending_history_messages(
    existing_messages: list[AiAssistantMessage],
    incoming_messages: list[AiAssistantConversationMessage],
) -> list[AiAssistantConversationMessage]:
    prefix_matches = len(existing_messages) <= len(incoming_messages) and all(
        stored.role == incoming.role and stored.content == incoming.content
        for stored, incoming in zip(existing_messages, incoming_messages)
    )
    if prefix_matches:
        return incoming_messages[len(existing_messages):]
    last_user_message = next((item for item in reversed(incoming_messages) if item.role == "user"), None)
    return [last_user_message] if last_user_message else []


async def _prepare_chat(
    db: Session,
    current_user: User,
    page_id: int,
    conversation: str,
    attachments: list[UploadFile] | None,
    page_sections: str = "",
    include_images: bool = True,
) -> tuple[Page, list[AiAssistantConversationMessage], AiAssistantUsage, int | None, list[ChatAttachment], str]:
    """Valida a conversa e a permissão, confere o limite do plano e grava as mensagens novas do usuário."""
    try:
        conversation_payload = json.loads(conversation or "[]")
        if not isinstance(conversation_payload, list):
            raise ValueError("conversation must be a list")
        parsed_conversation = [AiAssistantConversationMessage.model_validate(item) for item in conversation_payload]
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Conversa inválida.") from exc

    if not parsed_conversation:
        raise HTTPException(status_code=400, detail="Nenhuma mensagem enviada.")

    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)

    usage_record, usage_limit = check_ai_assistant_message_limit(db, current_user)

    existing_messages = (
        db.query(AiAssistantMessage)
        .filter(
            AiAssistantMessage.page_id == page.id,
            AiAssistantMessage.user_id == current_user.id,
        )
        .order_by(AiAssistantMessage.id.asc())
        .all()
    )
    for item in _pending_history_messages(existing_messages, parsed_conversation):
        content = item.content.strip()
        if not content:
            continue
        db.add(AiAssistantMessage(page_id=page.id, user_id=current_user.id, role=item.role, content=content))
    db.commit()

    attachment_payload: list[ChatAttachment] = []
    for upload in attachments or []:
        data = await upload.read()
        attachment_payload.append(
            ChatAttachment(filename=upload.filename or "arquivo", content_type=upload.content_type, data=data)
        )
    sent_photos = await _save_chat_photos(db, page.agency_id, attachment_payload)
    try:
        sections_payload = json.loads(page_sections) if page_sections else None
    except json.JSONDecodeError:
        sections_payload = None
    if not isinstance(sections_payload, list):
        sections_payload = None
    else:
        sections_payload = [item for item in sections_payload if isinstance(item, dict)][:80]
    context = build_agency_context(db, page, sections_payload, include_images=include_images)
    if sent_photos:
        # A resposta é aplicada depois (sem os anexos): a IA escreve o endereço da foto na seção.
        lines = [
            "IMAGENS ENVIADAS NESTA MENSAGEM (já estão na biblioteca de mídia da agência). Para usar uma numa seção, "
            'escreva "Imagem: endereço" com o endereço abaixo (sem "Busca de imagem"):'
        ]
        lines.extend(f"- {name}: {url}" for name, url in sent_photos)
        context = f"{context}\n" + "\n".join(lines)
    return page, parsed_conversation, usage_record, usage_limit, attachment_payload, context


def _photo_days_for_itinerary_swaps(sections: list[dict], itinerary_days: dict[str, int]) -> None:
    """Troca só da foto do Roteiro dia a dia: a resposta não traz os dias; aqui o roteiro ganha um
    dia vazio por dia da página, para cada um receber uma foto (o editor junta pela ordem)."""
    for section in sections:
        if section.get("type") != "itinerary" or section.get("days") or section.get("aiImageQuery") is None:
            continue
        target = str(section.get("aiReplaces") or "")
        count = itinerary_days.get(target) or (next(iter(itinerary_days.values())) if len(itinerary_days) == 1 else 0)
        if count:
            section["days"] = [{} for _ in range(min(int(count), 30))]


MAX_CHAT_PHOTO_BYTES = 15 * 1024 * 1024


async def _save_chat_photos(db: Session, agency_id: int, attachments: list[ChatAttachment]) -> list[tuple[str, str]]:
    """Fotos enviadas no chat vão para a biblioteca da agência (versões leves em WebP, como no
    envio do editor). Devolve (nome, endereço) de cada uma, na ordem em que foram enviadas."""
    saved: list[tuple[str, str]] = []
    for attachment in attachments:
        if (attachment.content_type or "").lower() not in CHAT_IMAGE_TYPES or not attachment.data:
            continue
        if len(attachment.data) > MAX_CHAT_PHOTO_BYTES:
            continue
        try:
            variants = await anyio.to_thread.run_sync(optimize_image, attachment.data)
            if variants:
                url = await anyio.to_thread.run_sync(media_storage.save_image_variants, variants)
            else:
                url = await anyio.to_thread.run_sync(
                    partial(media_storage.save, attachment.data, attachment.filename or "imagem", attachment.content_type)
                )
        except Exception:  # pragma: no cover - sem a cópia, a foto só serve de referência para a IA
            logger.exception("ai_assistant_chat_photo_save_failed")
            continue
        db.add(MediaAsset(agency_id=agency_id, url=url, type="image", original_file_name=attachment.filename))
        saved.append((attachment.filename or f"imagem {len(saved) + 1}", url))
    if saved:
        db.commit()
    return saved


def _usage_headers(usage_record: AiAssistantUsage, usage_limit: int | None) -> dict[str, str]:
    used = int(usage_record.message_count or 0)
    return {
        "X-AI-Assistant-Period": usage_record.period_key,
        "X-AI-Assistant-Usage": str(used),
        "X-AI-Assistant-Limit": "unlimited" if usage_limit is None else str(usage_limit),
        "X-AI-Assistant-Remaining": "unlimited" if usage_limit is None else str(max(int(usage_limit) - used, 0)),
    }


def _usage_payload(usage_record: AiAssistantUsage, usage_limit: int | None) -> dict:
    used = int(usage_record.message_count or 0)
    return {
        "period_key": usage_record.period_key,
        "used": used,
        "limit": usage_limit,
        "remaining": None if usage_limit is None else max(int(usage_limit) - used, 0),
        "unlimited": usage_limit is None,
    }


@router.post("/chat", response_model=AiAssistantChatResponse)
async def chat_with_assistant(
    page_id: int = Form(...),
    conversation: str = Form("[]"),
    attachments: list[UploadFile] | None = File(default=None),
    page_sections: str = Form(""),
    include_images: bool = Form(True),
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAssistantChatResponse:
    page, parsed_conversation, usage_record, usage_limit, attachment_payload, context = await _prepare_chat(
        db, current_user, page_id, conversation, attachments, page_sections, include_images
    )
    reply = await anyio.to_thread.run_sync(
        partial(
            generate_ai_assistant_reply,
            [ChatMessage(role=item.role, content=item.content) for item in parsed_conversation],
            attachment_payload,
            model_override=get_active_gpt_model(db, create_if_missing=True),
            context=context,
        )
    )
    usage_record = increment_ai_assistant_message_usage(db, usage_record)
    db.add(AiAssistantMessage(page_id=page.id, user_id=current_user.id, role="assistant", content=reply))
    db.commit()
    for key, value in _usage_headers(usage_record, usage_limit).items():
        response.headers[key] = value
    return AiAssistantChatResponse(reply=reply)


@router.post("/chat-stream")
async def chat_with_assistant_stream(
    page_id: int = Form(...),
    conversation: str = Form("[]"),
    attachments: list[UploadFile] | None = File(default=None),
    page_sections: str = Form(""),
    include_images: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """Mesma conversa do /chat, em linhas JSON (NDJSON) enviadas enquanto a IA escreve:
    etapas, trechos do texto e, no fim, a resposta completa com o uso do mês."""
    page, parsed_conversation, usage_record, usage_limit, attachment_payload, context = await _prepare_chat(
        db, current_user, page_id, conversation, attachments, page_sections, include_images
    )
    model = get_active_gpt_model(db, create_if_missing=True)
    page_id_value, user_id, period_key = page.id, current_user.id, usage_record.period_key
    messages = [ChatMessage(role=item.role, content=item.content) for item in parsed_conversation]

    def line(payload: dict) -> bytes:
        return (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode("utf-8")

    def events():
        yield line({"type": "status", "step": "reading", "attachments": len(attachment_payload)})
        try:
            for event in stream_ai_assistant_reply(messages, attachment_payload, model_override=model, context=context):
                if event["type"] != "done":
                    yield line(event)
                    continue
                # A sessão da requisição já foi fechada: grava resposta e uso numa sessão própria.
                with SessionLocal() as session:
                    record = get_ai_assistant_usage_record(session, user_id, period_key)
                    record = increment_ai_assistant_message_usage(session, record)
                    session.add(AiAssistantMessage(page_id=page_id_value, user_id=user_id, role="assistant", content=event["reply"]))
                    session.commit()
                    usage = _usage_payload(record, usage_limit)
                yield line({"type": "done", "reply": event["reply"], "usage": usage})
        except HTTPException as exc:
            yield line({"type": "error", "status": exc.status_code, "detail": exc.detail})
        except Exception as exc:  # pragma: no cover - guarda de rede
            logger.exception("ai_assistant_stream_failed")
            yield line({"type": "error", "status": 502, "detail": f"Falha ao consultar a IA: {exc}"})

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        # Sem buffer no nginx: cada linha chega ao navegador assim que é escrita.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


MAX_AUDIO_BYTES = 20 * 1024 * 1024


@router.post("/transcribe", response_model=AiAssistantTranscriptionResponse)
async def transcribe_assistant_audio(
    page_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAssistantTranscriptionResponse:
    """Áudio gravado no chat do assistente vira texto (não conta como mensagem do mês)."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    check_ai_assistant_message_limit(db, current_user)
    data = await audio.read()
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="O áudio passou de 20 MB. Grave um áudio mais curto.")
    text = await anyio.to_thread.run_sync(
        partial(transcribe_audio, data, audio.filename or "audio.webm", audio.content_type)
    )
    if not text:
        raise HTTPException(status_code=422, detail="Não entendi o áudio. Tente gravar de novo, mais perto do microfone.")
    return AiAssistantTranscriptionResponse(text=text)


@router.get("/pages/{page_id}/history", response_model=list[AiAssistantHistoryMessage])
def get_page_assistant_history(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AiAssistantHistoryMessage]:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)

    rows = (
        db.query(AiAssistantMessage)
        .filter(
            AiAssistantMessage.page_id == page.id,
            AiAssistantMessage.user_id == current_user.id,
        )
        .order_by(AiAssistantMessage.id.asc())
        .all()
    )
    return [
        AiAssistantHistoryMessage(
            id=row.id,
            role=row.role,
            content=row.content,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/usage", response_model=AiAssistantUsageResponse)
def get_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAssistantUsageResponse:
    summary = get_ai_assistant_usage_summary(db, current_user)
    return AiAssistantUsageResponse(
        period_key=str(summary["period_key"]),
        used=int(summary["used"] or 0),
        limit=None if summary["limit"] is None else int(summary["limit"]),
        remaining=None if summary["remaining"] is None else int(summary["remaining"]),
        unlimited=bool(summary["unlimited"]),
        renewal_at=summary["renewal_at"],
    )


@router.post("/create-page-base", response_model=AiAssistantCreatePageBaseResponse)
def create_page_base(
    payload: AiAssistantCreatePageBaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AiAssistantCreatePageBaseResponse:
    page = db.query(Page).filter(Page.id == payload.page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")

    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)

    current_config = normalize_config(page.config_json)
    new_config, suggested_title = build_page_base_config_from_reply(payload.reply, current_config)
    try:
        fill_section_photos(db, new_config["sections"], page.agency_id)
    except Exception:  # pragma: no cover - sem foto, a seção fica com a imagem provisória
        logger.exception("ai_assistant_stock_photos_failed")
        db.rollback()
    for section in new_config["sections"]:
        section.pop("aiReplaces", None)
        section.pop("aiStockPhoto", None)
        section.pop("aiSetKeys", None)
        flights = section.pop("aiFlights", None)
        if flights and section.get("type") == "flight_details" and section.get("sectionId"):
            # Trechos do voo (com código, buscados na API; sem, manuais).
            try:
                import_flight_journeys(db, page.id, section["sectionId"], flights)
            except Exception:  # pragma: no cover - o voo pode ser montado depois no editor
                logger.exception("ai_assistant_flight_import_failed")
                db.rollback()
        if section.get("type") == "header":
            section.setdefault("links", [])
        if section.get("type") == "header" and isinstance(section.get("links"), list):
            # Aplicado direto (sem o editor): item de menu sem seção de destino não entra.
            section["links"] = [
                {key: value for key, value in link.items() if key != "aiTargetLabel"}
                for link in section["links"]
                if isinstance(link, dict) and (link.get("target") or link.get("targetType") != "section")
            ]
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = enforce_page_limits(db, page, publish=False, config=new_config, plan=plan)
    page.cover_image_url = derive_cover_image_from_config(page.config_json)
    if suggested_title and suggested_title.strip():
        page.title = suggested_title.strip()

    db.add(page)
    db.commit()
    db.refresh(page)
    setattr(page, "is_default", bool(page.agency and page.agency.default_page_id == page.id))
    return AiAssistantCreatePageBaseResponse(page=page)


@router.post("/preview-page-base")
def preview_page_base(
    payload: AiAssistantCreatePageBaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """Build an editable structure without changing the saved/published page."""
    page = db.query(Page).filter(Page.id == payload.page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    config, _ = build_page_base_config_from_reply(payload.reply, normalize_config(page.config_json), strict=True)
    _photo_days_for_itinerary_swaps(config["sections"], payload.itinerary_days)
    # Fotos dos bancos no lugar das imagens provisórias (a IA escolhe entre as candidatas), a não
    # ser que o usuário tenha desligado "Inserir imagens".
    if payload.include_images:
        try:
            fill_section_photos(db, config["sections"], page.agency_id, exclude_urls=payload.current_photos)
        except Exception:  # pragma: no cover - sem foto, a seção fica com a imagem provisória
            logger.exception("ai_assistant_stock_photos_failed")
            db.rollback()
            clear_photo_queries(config["sections"])
    else:
        clear_photo_queries(config["sections"])
    # Menu do topo com redes sociais: usa as redes cadastradas da agência.
    networks = [link for link in (page.agency.social_links if page.agency else []) if (link.url or "").strip()]
    for section in config["sections"]:
        if section.get("type") == "header" and section.get("actionType") == "social":
            if networks:
                section["socialLinks"] = [{"platform": link.network, "url": link.url.strip()} for link in networks]
            else:
                section["actionType"] = "contact"
    plan = resolve_agency_plan(db, page.agency_id)
    config = enforce_page_limits(db, page, publish=False, config=config, plan=plan)
    return {"sections": config["sections"]}
