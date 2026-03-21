from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.media import MediaAsset
from app.models.page import Page, PageStatus
from app.schemas.ai import (
    AiBriefingInterpretRequest,
    AiBriefingInterpretResponse,
    AiCreditTransactionOut,
    AiCreditWalletOut,
    AiFollowUpAnswers,
    AiImageSelection,
    AiPageRequest,
    AiPageResponse,
    MAX_AI_IMAGES_PER_SECTION,
)
from app.services.ai_credits import InsufficientCreditsError, get_wallet_snapshot, spend_credits
from app.services.ai_page_builder import (
    build_image_prompts,
    build_user_prompt,
    sections_to_config,
)
from app.services.ai_plan_parser import parse_plan_sections
from app.services.gemini_client import GeminiClient
from app.services.media_storage import media_storage
from app.services.plans import effective_plan

router = APIRouter()

ALLOWED_AI_PLANS = {"infinity", "teste", "trial"}


@router.post("/briefing/interpret", response_model=AiBriefingInterpretResponse)
async def interpret_briefing_with_ai(
    payload: AiBriefingInterpretRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> AiBriefingInterpretResponse:
    agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="AgǦncia nǜo encontrada.")
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == payload.agency_id, AgencyUser.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="VocǦ nǜo faz parte desta agǦncia.")

    plan_key = effective_plan(current_user).lower()
    if plan_key not in ALLOWED_AI_PLANS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Dispon��vel apenas no plano Infinity (ou teste)."
        )

    try:
        gemini = GeminiClient()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raw = await gemini.interpret_briefing(payload.briefing, payload.attachments)
    raw_answers = raw.get("answers") if isinstance(raw, dict) else {}
    answers = AiFollowUpAnswers(**(raw_answers or {}))

    missing_keys = set()
    explicit_missing = raw.get("missing") if isinstance(raw, dict) else []
    for key in explicit_missing or []:
        if isinstance(key, str):
            missing_keys.add(key)
    for key, value in answers.model_dump().items():
        if not value:
            missing_keys.add(key)
    ordered_fields = list(AiFollowUpAnswers.model_fields.keys())
    missing_ordered = [key for key in ordered_fields if key in missing_keys]

    summary = raw.get("summary") if isinstance(raw, dict) and isinstance(raw.get("summary"), str) else None
    notes_raw = raw.get("notes") if isinstance(raw, dict) else None
    notes = [str(item) for item in (notes_raw or []) if isinstance(item, str) and item.strip()]
    raw_text = json.dumps(raw, ensure_ascii=False)

    return AiBriefingInterpretResponse(
        summary=summary,
        answers=answers,
        missing=missing_ordered,
        notes=notes,
        raw_text=raw_text,
    )


@router.get("/credits", response_model=AiCreditWalletOut)
def get_my_ai_credits(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> AiCreditWalletOut:
    wallet = get_wallet_snapshot(db, current_user.id)
    transactions = [
        AiCreditTransactionOut(
            id=tx.id,
            delta=tx.delta,
            reason=tx.reason,
            metadata=tx.metadata_json,
            created_at=tx.created_at.isoformat() if tx.created_at else "",
        )
        for tx in wallet.transactions[:10]
    ]
    return AiCreditWalletOut(balance=wallet.balance, transactions=transactions)


@router.post("/pages", response_model=AiPageResponse)
async def create_page_with_ai(
    payload: AiPageRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
) -> AiPageResponse:
    agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == payload.agency_id, AgencyUser.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta agência.")

    plan_key = effective_plan(current_user).lower()
    if plan_key not in ALLOWED_AI_PLANS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Disponível apenas no plano Infinity (ou teste).")

    if (not payload.briefing or len(payload.briefing.strip()) < 10) and not payload.attachments:
        raise HTTPException(
            status_code=400,
            detail="Envie um resumo curto ou anexe o briefing antes de continuar.",
        )

    additional_credit = 1 if payload.generate_ai_images and payload.ai_image_targets else 0
    required_credits = 1 + additional_credit
    try:
        spend_credits(
            db,
            current_user.id,
            amount=required_credits,
            reason="ai_page_reservation",
            metadata={"preview": True},
            dry_run=True,
        )
    except InsufficientCreditsError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    try:
        gemini = GeminiClient()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    user_prompt = build_user_prompt(payload.briefing, payload.answers)
    plan_text = await gemini.generate_page_plan(user_prompt, payload.attachments)

    try:
        sections_plan = parse_plan_sections(plan_text)
    except ValueError as exc:
        snippet = plan_text.strip()
        separator = "-" * 80
        raise HTTPException(
            status_code=502,
            detail=(
                f"Não foi possível interpretar o retorno da IA: {exc}\n\n"
                f"Resposta bruta da IA (debug):\n{separator}\n{snippet}\n{separator}"
            ),
        ) from exc

    generated_media: Dict[str, List[List[str]]] = {}
    image_credit_applied = False
    if payload.generate_ai_images and payload.ai_image_targets:
        generated_media = await _generate_ai_images(
            gemini=gemini,
            selections=payload.ai_image_targets,
            answers=payload.answers,
            db=db,
            agency=agency,
            sections_plan=sections_plan,
        )
        image_credit_applied = bool(generated_media)

    video_url = str(payload.video_url) if payload.video_url else None
    config = sections_to_config(
        sections_plan,
        agency,
        payload.manual_media,
        generated_media,
        video_url,
        payload.theme_mode,
    )
    whatsapp_digits = _sanitize_digits(agency.cta_whatsapp or current_user.whatsapp or "")
    if whatsapp_digits:
        link = _build_whatsapp_link(whatsapp_digits, payload.preferred_title or "")
        _replace_whatsapp_links(config, link)

    page_title = payload.preferred_title or _extract_hero_title(config) or f"Roteiro {agency.name}"
    slug = _build_unique_slug(db, agency.id, page_title)
    cover_image_url = _extract_cover_image(config)

    page = Page(
        agency_id=agency.id,
        title=page_title.strip(),
        slug=slug,
        status=PageStatus.published if payload.auto_publish else PageStatus.draft,
        published_at=datetime.utcnow() if payload.auto_publish else None,
        config_json=config,
        cover_image_url=cover_image_url,
    )
    db.add(page)
    db.flush()

    credits_to_charge = 1 + (1 if image_credit_applied else 0)
    try:
        wallet = spend_credits(
            db,
            current_user.id,
            amount=credits_to_charge,
            reason="ai_page_generation",
            metadata={"page_id": page.id, "agency_id": agency.id},
        )
    except InsufficientCreditsError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    db.commit()
    db.refresh(page)

    redirect_url = f"/admin/pages/{page.id}/edit"
    message = "Página criada com IA e publicada." if payload.auto_publish else "Página criada com IA."
    if payload.generate_ai_images and not image_credit_applied:
        message += " Não foi possível gerar novas imagens, então usamos placeholders."

    return AiPageResponse(
        page_id=page.id,
        redirect_url=redirect_url,
        published=payload.auto_publish,
        credits_spent=credits_to_charge,
        credits_balance=wallet.balance,
        message=message,
    )


async def _generate_ai_images(
    gemini: GeminiClient,
    selections: List[AiImageSelection],
    answers: AiFollowUpAnswers,
    db: Session,
    agency: Agency,
    sections_plan: List[dict[str, Any]],
) -> Dict[str, List[List[str]]]:
    prompts = build_image_prompts(selections, answers)
    media_map: Dict[str, List[List[str]]] = {}
    itinerary_days = _count_itinerary_days(sections_plan)

    for selection, prompt_text in prompts:
        target_key = _media_key_from_selection(selection.section)
        desired_count = selection.count or 1
        if selection.section == "itinerary" and selection.per_day:
            desired_count = itinerary_days or desired_count
        desired_count = max(1, min(desired_count, MAX_AI_IMAGES_PER_SECTION))
        if desired_count <= 0:
            continue
        urls_bundle: List[str] = []
        for _ in range(desired_count):
            data = await gemini.generate_image(prompt_text)
            if not data:
                continue
            try:
                url = media_storage.save(data, f"ai-{target_key}.png", "image/png")
            except Exception:
                continue
            asset = MediaAsset(agency_id=agency.id, url=url, type="image", original_file_name=f"AI {target_key}")
            db.add(asset)
            urls_bundle.append(url)
        if urls_bundle:
            media_map.setdefault(target_key, []).append(urls_bundle)

    return media_map


def _extract_hero_title(config: dict[str, Any]) -> str | None:
    for section in config.get("sections", []):
        if section.get("type") == "hero":
            return section.get("title")
    return None


def _extract_cover_image(config: dict[str, Any]) -> str | None:
    for section in config.get("sections", []):
        if section.get("type") == "hero" and section.get("backgroundImage"):
            return section["backgroundImage"]
    return None


def _build_unique_slug(db: Session, agency_id: int, title: str) -> str:
    base = _slugify(title)
    slug = base
    counter = 2
    while (
        db.query(Page)
        .filter(Page.agency_id == agency_id, Page.slug == slug)
        .first()
        is not None
    ):
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _slugify(value: str) -> str:
    norm = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
    if not slug:
        slug = f"pagina-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return slug


def _sanitize_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _build_whatsapp_link(digits: str, context: str) -> str:
    title = context or "Roteiro"
    message = f"Oi, tenho interesse no roteiro: {title}"
    return f"https://wa.me/{digits}?text={quote(message)}"


_WHATSAPP_LACUNA = re.compile(r"\[LACUNA[^]]*whats", re.IGNORECASE)


def _replace_whatsapp_links(node: Any, new_link: str) -> Any:
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                stripped = value.strip()
                key_lower = key.lower() if isinstance(key, str) else ""
                if "wa.me" in stripped or _WHATSAPP_LACUNA.search(stripped) or (
                    not stripped and (key_lower.endswith("link") or key_lower.endswith("url"))
                ):
                    node[key] = new_link
                    continue
            _replace_whatsapp_links(value, new_link)
    elif isinstance(node, list):
        for item in node:
            _replace_whatsapp_links(item, new_link)
    return node


def _count_itinerary_days(sections_plan: List[dict[str, Any]]) -> int:
    for section in sections_plan:
        if section.get("type") != "itinerary":
            continue
        fields = section.get("fields") or {}
        days = fields.get("days")
        if isinstance(days, list):
            return len(days)
    return 0


def _media_key_from_selection(section: str) -> str:
    if section == "banner":
        return "banner_card"
    return section
