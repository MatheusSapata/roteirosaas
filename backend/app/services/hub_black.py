"""Implementações Black do Viaje On Hub: a equipe gera, a partir do roteiro que o cliente enviou no
Hub, uma página em rascunho no Roteiro Online, com o mesmo assistente de IA do editor.

- A conta é a do cliente (achada pelo e-mail); sem ela, a do Admin do Hub que pediu.
- A geração roda em segundo plano (a IA pode levar mais de um minuto); o andamento fica em
  config_json["hubGeneration"] da própria página e o Hub consulta até ficar pronta.
- Não desconta do limite de mensagens do assistente de ninguém e nunca publica a página.
- A prévia é um link assinado com a chave do funil do Hub (a mesma de hub_funnel), sem login.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import threading
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.user import User
from app.services import hub_funnel

logger = logging.getLogger(__name__)

MARKER = "hubGeneration"
# Geração parada há mais que isso (container reiniciado no meio) aparece como erro para refazer.
STALE_AFTER = timedelta(minutes=12)
MAX_FILES = 12
MAX_FILE_BYTES = 20 * 1024 * 1024
DOWNLOAD_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# Chave e prévia
# ---------------------------------------------------------------------------


def hub_key() -> str:
    """Chave do funil do Hub (painel do Admin Master ou ambiente); vazia sem configuração."""
    _url, key, _source = hub_funnel.hub_config()
    return key


def key_matches(received: str | None) -> bool:
    key = hub_key()
    return bool(key) and bool(received) and hmac.compare_digest(key.encode(), (received or "").strip().encode())


def preview_signature(page_id: int) -> str:
    key = hub_key()
    if not key:
        return ""
    return hmac.new(key.encode(), f"black-preview:{page_id}".encode(), hashlib.sha256).hexdigest()[:32]


def preview_token(page_id: int) -> str:
    return f"{page_id}-{preview_signature(page_id)}"


def page_id_from_token(token: str) -> int | None:
    page_part, _, signature = (token or "").partition("-")
    if not page_part.isdigit() or not signature:
        return None
    page_id = int(page_part)
    expected = preview_signature(page_id)
    if not expected or not hmac.compare_digest(expected, signature):
        return None
    return page_id


# ---------------------------------------------------------------------------
# Conta de destino
# ---------------------------------------------------------------------------


def _agency_of_email(db: Session, email: str | None) -> Agency | None:
    email = (email or "").strip().lower()
    if not email:
        return None
    user = db.query(User).filter(func.lower(User.email) == email).first()
    # Só conta já liberada: usuário ativo (desativado ou bloqueado cai na conta do Admin).
    if not user or not user.is_active or (user.status or "active").lower() not in {"active", "pending_agency_setup"}:
        return None
    memberships = db.query(AgencyUser).filter(AgencyUser.user_id == user.id).all()
    if not memberships:
        return None
    # Agência da qual a pessoa é dona vem primeiro.
    memberships.sort(key=lambda rel: 0 if (rel.role or "").lower() == "owner" else 1)
    return db.query(Agency).filter(Agency.id == memberships[0].agency_id).first()


def resolve_target_agency(db: Session, client_email: str | None, fallback_email: str | None) -> tuple[Agency, bool]:
    """(agência, usou_a_conta_do_admin)."""
    agency = _agency_of_email(db, client_email)
    if agency:
        return agency, False
    agency = _agency_of_email(db, fallback_email)
    if agency:
        return agency, True
    if fallback_email:
        raise HTTPException(
            status_code=404,
            detail="Não achei conta no Roteiro Online com o e-mail do cliente nem com o e-mail informado por você no Hub.",
        )
    raise HTTPException(
        status_code=404,
        detail="O cliente não tem conta no Roteiro Online. Informe o seu e-mail do Roteiro Online em Minha conta, no Hub, para gerar na sua conta.",
    )


# ---------------------------------------------------------------------------
# Andamento
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _config_dict(page: Page) -> dict[str, Any]:
    from app.api.v1.endpoints.pages import normalize_config

    config = normalize_config(page.config_json)
    return deepcopy(config) if isinstance(config, dict) else {}


def _set_marker(page: Page, marker: dict[str, Any] | None) -> None:
    config = _config_dict(page)
    if marker is None:
        config.pop(MARKER, None)
    else:
        config[MARKER] = marker
    page.config_json = config


def generation_state(page: Page) -> dict[str, Any]:
    """{"status": "generating" | "ready" | "error", "error": str | None}."""
    config = _config_dict(page)
    marker = config.get(MARKER)
    if not isinstance(marker, dict):
        return {"status": "ready", "error": None}
    status = marker.get("status")
    if status == "error":
        return {"status": "error", "error": marker.get("error") or "A geração falhou."}
    started = marker.get("started_at")
    try:
        started_at = datetime.fromisoformat(started) if started else None
    except ValueError:
        started_at = None
    if started_at and datetime.now(timezone.utc) - started_at > STALE_AFTER:
        return {"status": "error", "error": "A geração foi interrompida. Gere de novo."}
    return {"status": "generating", "error": None}


def page_links(page: Page) -> dict[str, str | None]:
    base = get_settings().resolved_webapp_base_url
    agency_slug = page.agency.slug if page.agency else ""
    return {
        "preview_url": f"{base}/previa-hub/{preview_token(page.id)}",
        "editor_url": f"{base}/admin/pages/{page.id}/edit",
        "public_url": f"{base}/{agency_slug}/{page.slug}" if page.status == "published" else None,
    }


def describe_page(page: Page) -> dict[str, Any]:
    state = generation_state(page)
    return {
        "page_id": page.id,
        "title": page.title,
        "agency_name": page.agency.name if page.agency else "",
        "page_status": page.status,
        "generation": state["status"],
        "error": state["error"],
        **page_links(page),
    }


# ---------------------------------------------------------------------------
# Geração
# ---------------------------------------------------------------------------


def build_request_text(title: str, description: str, general_info: str, stock_images: bool) -> str:
    images = (
        "Imagens: o cliente AUTORIZOU usar imagens de bancos de imagens onde faltar foto."
        if stock_images
        else (
            "Imagens: o cliente NÃO autorizou imagens de bancos de imagens. É EXPRESSAMENTE PROIBIDO usar qualquer imagem "
            'que não esteja em "IMAGENS ENVIADAS PELO CLIENTE": não escreva "Busca de imagem", não invente nem copie '
            'endereços de imagem e não use links de fotos de outros sites. Seção sem foto enviada fica sem "Imagem:".'
        )
    )
    return "\n".join(
        [
            "Monte agora a estrutura completa da página deste roteiro, pronta para aplicar.",
            "Não faça perguntas: use só as informações abaixo e deixe de fora o que não foi informado.",
            "",
            f"Título: {title.strip()}",
            f"Descrição: {description.strip()}",
            "",
            "Informações gerais do roteiro:",
            general_info.strip(),
            "",
            images,
        ]
    ).strip()


# Campos de uma seção que guardam endereço de imagem (texto ou lista), inclusive dentro de dias e itens.
IMAGE_FIELDS = frozenset({"backgroundImage", "mobileBackgroundImage", "image", "mobileImage", "images"})


def restrict_images_to_allowed(sections: list[Any], allowed_urls: set[str]) -> int:
    """Sem consentimento para bancos de imagens, só valem as fotos enviadas pelo cliente: qualquer outro
    endereço de imagem (inclusive um que a IA tenha escrito em "Imagem:") volta para a imagem provisória.
    Devolve quantas imagens foram trocadas."""
    from app.services.ai_assistant import AI_IMAGE_PLACEHOLDER

    def allowed(value: Any) -> bool:
        return not isinstance(value, str) or not value.strip() or value == AI_IMAGE_PLACEHOLDER or value in allowed_urls

    replaced = 0

    def walk(node: Any) -> None:
        nonlocal replaced
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key in IMAGE_FIELDS and isinstance(value, str):
                if not allowed(value):
                    node[key] = AI_IMAGE_PLACEHOLDER
                    replaced += 1
            elif key in IMAGE_FIELDS and isinstance(value, list):
                kept = [item for item in value if allowed(item)]
                replaced += len(value) - len(kept)
                node[key] = kept or ([AI_IMAGE_PLACEHOLDER] if value else [])
            else:
                walk(value)

    walk(sections)
    return replaced


def start_page(db: Session, agency: Agency, title: str, page_id: int | None = None) -> Page:
    """Página em rascunho que recebe a geração (nova, ou a mesma de uma geração anterior)."""
    from app.api.v1.endpoints.pages import _ensure_unique_slug

    page = None
    if page_id:
        page = db.query(Page).filter(Page.id == page_id, Page.agency_id == agency.id).first()
        if page and generation_state(page)["status"] == "generating":
            raise HTTPException(status_code=409, detail="Esta página já está sendo gerada.")
    if page is None:
        clean_title = (title or "").strip()[:200] or "Roteiro"
        page = Page(
            agency_id=agency.id,
            title=clean_title,
            slug=_ensure_unique_slug(db, agency.id, clean_title),
            status="draft",
            config_json={"sections": []},
        )
    _set_marker(page, {"status": "generating", "started_at": _now()})
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


async def _download_files(files: list[dict[str, Any]]) -> list[Any]:
    from app.services.ai_assistant import ChatAttachment, normalize_chat_attachment

    attachments: list[ChatAttachment] = []
    async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
        for item in files[:MAX_FILES]:
            url = str(item.get("url") or "")
            if not url.startswith("https://"):
                continue
            try:
                response = await client.get(url)
                response.raise_for_status()
            except Exception:  # pragma: no cover - rede: o anexo fica de fora
                logger.warning("hub_black_download_failed name=%s", item.get("name"))
                continue
            if not response.content or len(response.content) > MAX_FILE_BYTES:
                continue
            content_type = (item.get("content_type") or response.headers.get("content-type") or "").split(";")[0].strip()
            # AVIF e outros formatos que a OpenAI não lê viram JPEG/PNG; o que não converte fica de fora.
            attachment = normalize_chat_attachment(
                ChatAttachment(filename=str(item.get("name") or "arquivo"), content_type=content_type or None, data=response.content)
            )
            if attachment is not None:
                attachments.append(attachment)
    return attachments


async def _generate(db: Session, page: Page, payload: dict[str, Any]) -> None:
    from app.api.v1.endpoints.ai_assistant import _save_chat_photos, _save_pdf_photos
    from app.api.v1.endpoints.pages import (
        derive_cover_image_from_config,
        enforce_page_limits,
        resolve_agency_plan,
    )
    from app.services.ai_assistant import (
        ChatMessage,
        build_page_base_config_from_reply,
        generate_ai_assistant_reply,
    )
    from app.services.ai_assistant import _reply_has_structure
    from app.services.ai_assistant_context import build_agency_context
    from app.services.construtor_prompt import get_active_gpt_model
    from app.services.stock_images import clear_photo_queries, fill_section_photos

    stock_images = bool(payload.get("stock_images_consent"))
    attachments = await _download_files(payload.get("files") or [])
    # Fotos e PDFs do cliente vão para a biblioteca da agência e a IA escreve o endereço na seção.
    sent_photos = await _save_chat_photos(db, page.agency_id, attachments)
    pdf_photos, _notice = await _save_pdf_photos(db, page.agency_id, attachments)

    context = build_agency_context(db, page, [], include_images=stock_images)
    if sent_photos:
        lines = [
            "IMAGENS ENVIADAS PELO CLIENTE (já estão na biblioteca de mídia da agência). Use cada uma na seção que "
            'combina, escrevendo "Imagem: endereço" com o endereço abaixo (sem "Busca de imagem"):'
        ]
        lines.extend(f"- {name}: {url}" for name, url in sent_photos)
        context = f"{context}\n" + "\n".join(lines)
    if pdf_photos:
        lines = [
            "FOTOS EXTRAÍDAS DO PDF ENVIADO PELO CLIENTE (já estão na biblioteca de mídia da agência). Use cada foto "
            'na seção que combina, escrevendo "Imagem: endereço" com o endereço abaixo. Não repita a mesma foto:'
        ]
        lines.extend(f"- {name}: {url}" for name, url in pdf_photos)
        context = f"{context}\n" + "\n".join(lines)

    request = build_request_text(
        str(payload.get("title") or ""),
        str(payload.get("description") or ""),
        str(payload.get("general_info") or ""),
        stock_images,
    )
    model = get_active_gpt_model(db, create_if_missing=True)
    conversation = [ChatMessage(role="user", content=request)]
    reply = generate_ai_assistant_reply(conversation, attachments, model_override=model, context=context)
    if not _reply_has_structure(reply):
        # A IA respondeu com perguntas: pede a estrutura com o que já tem.
        conversation += [
            ChatMessage(role="assistant", content=reply),
            ChatMessage(
                role="user",
                content="Não pergunte nada. Monte agora a estrutura completa da página com as informações que já tem.",
            ),
        ]
        reply = generate_ai_assistant_reply(conversation, attachments, model_override=model, context=context)

    db.refresh(page)
    base = _config_dict(page)
    base.pop(MARKER, None)
    config, suggested_title = build_page_base_config_from_reply(reply, base)
    if stock_images:
        try:
            fill_section_photos(db, config["sections"], page.agency_id, exclude_page_id=page.id)
        except Exception:  # pragma: no cover - sem foto, a seção fica com a imagem provisória
            logger.exception("hub_black_stock_photos_failed")
            db.rollback()
            clear_photo_queries(config["sections"])
    else:
        clear_photo_queries(config["sections"])
        # Sem consentimento, só entram as fotos que o cliente enviou (anexos e fotos extraídas do PDF).
        allowed_urls = {url for _name, url in [*sent_photos, *pdf_photos]}
        if restrict_images_to_allowed(config["sections"], allowed_urls):
            logger.warning("hub_black_foreign_images_removed page=%s", page.id)
    for section in config["sections"]:
        for key in ("aiReplaces", "aiStockPhoto", "aiPhotoOrigins", "aiSetKeys", "aiFlights"):
            section.pop(key, None)
        if section.get("type") == "header" and isinstance(section.get("links"), list):
            section["links"] = [
                {key: value for key, value in link.items() if key != "aiTargetLabel"}
                for link in section["links"]
                if isinstance(link, dict) and (link.get("target") or link.get("targetType") != "section")
            ]
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = enforce_page_limits(db, page, publish=False, config=config, plan=plan)
    page.cover_image_url = derive_cover_image_from_config(page.config_json)
    title = (str(payload.get("title") or "").strip() or (suggested_title or "").strip())[:200]
    if title:
        page.title = title
    db.add(page)
    db.commit()


def _fail(page_id: int, message: str) -> None:
    from app.db import session as db_session

    with db_session.SessionLocal() as db:
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            return
        _set_marker(page, {"status": "error", "error": message[:500], "at": _now()})
        db.add(page)
        db.commit()


def run_generation(page_id: int, payload: dict[str, Any]) -> None:
    """Roda numa thread própria, com sessão própria do banco."""
    from app.db import session as db_session

    try:
        with db_session.SessionLocal() as db:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                return
            asyncio.run(_generate(db, page, payload))
    except HTTPException as exc:
        _fail(page_id, str(exc.detail))
    except Exception as exc:  # pragma: no cover - guarda geral
        logger.exception("hub_black_generation_failed page_id=%s", page_id)
        _fail(page_id, f"Falha ao gerar a página: {exc}")


def start_generation_thread(page_id: int, payload: dict[str, Any]) -> None:
    threading.Thread(target=run_generation, args=(page_id, payload), daemon=True).start()
