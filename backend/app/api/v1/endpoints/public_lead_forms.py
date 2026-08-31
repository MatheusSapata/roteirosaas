import hashlib
import logging
import uuid
from datetime import date, datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core.request_ip import get_client_ip
from app.models.lead_form import LeadForm, LeadFormSubmission
from app.models.agency_integration import AgencyIntegration
from app.db.session import SessionLocal
from app.schemas.lead_form import LeadFormPublicOut, LeadFormSubmissionPayload
from app.services.client_matching import find_auto_match_client
from app.services.contact_normalization import normalize_cpf, normalize_email, normalize_phone
from app.services.opportunity_whatsapp import dispatch_opportunity_welcome_message
from app.services.api_key_crypto import ApiKeyDecryptionError, decrypt_api_key
from app.services.viajechat import ViajeChatClient, ViajeChatClientError

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_form(db: Session, form_id: int) -> LeadForm:
    form = (
        db.query(LeadForm)
        .options(joinedload(LeadForm.default_status))
        .filter(LeadForm.id == form_id)
        .first()
    )
    if not form:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    return form


def _build_submission_fingerprint(form_id: int, request: Request, page_identifier: str | None = None) -> str | None:
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    page_component = page_identifier or ""
    raw = f"{form_id}:{page_component}:{ip}:{user_agent}".strip(":")
    if not raw:
        return None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_birthdate(value: str | None) -> date | None:
    raw = (value or "").strip()
    if not raw:
        return None
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            if pattern == "%Y-%m-%d":
                return date.fromisoformat(raw)
            from datetime import datetime

            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    return None


def _viajechat_phone(value: str | None) -> str | None:
    digits = normalize_phone(value)
    if digits and len(digits) in {10, 11}:
        return f"55{digits}"
    return digits


def _sync_submission_to_viajechat(submission_id: int) -> None:
    db = SessionLocal()
    try:
        submission = db.query(LeadFormSubmission).filter(LeadFormSubmission.id == submission_id).first()
        if not submission:
            return
        form = db.query(LeadForm).filter(LeadForm.id == submission.form_id).first()
        if not form or not form.viajechat_enabled:
            return
        integration = db.query(AgencyIntegration).filter(
            AgencyIntegration.agency_id == form.agency_id,
            AgencyIntegration.provider == "viajechat",
            AgencyIntegration.enabled.is_(True),
            AgencyIntegration.connection_status == "connected",
        ).first()
        phone = _viajechat_phone(submission.phone)
        if not integration or not phone:
            submission.viajechat_sync_status = "failed"
            submission.viajechat_sync_error = "Integração desconectada ou telefone ausente."
            db.commit()
            return

        notes = [f"Lead recebido pelo formulário {form.name}"]
        for item in (submission.payload or {}).get("values", []):
            field_type = str(item.get("type") or "").strip().lower()
            field_value = str(item.get("value") or "").strip()
            if field_type not in {"name", "phone"} and field_value:
                notes.append(f"{item.get('label') or 'Resposta'}: {field_value}")
        idempotency_key = str(uuid.uuid5(uuid.NAMESPACE_URL, f"roteiroonline:lead-form-submission:{submission.id}"))
        try:
            api_key = decrypt_api_key(integration.token_encrypted)
            result = ViajeChatClient(api_key).create_deal_card(
                phone=phone,
                name=submission.name or phone,
                email=submission.email,
                sector_id=form.viajechat_pipeline_id,
                column_id=form.viajechat_column_id,
                lead_source=f"Formulário — {form.name}",
                notes=notes,
                idempotency_key=idempotency_key,
            )
            data = result.get("data") if isinstance(result, dict) and isinstance(result.get("data"), dict) else result
            deal_data = (data or {}).get("deal") if isinstance((data or {}).get("deal"), dict) else data
            submission.viajechat_deal_id = str((deal_data or {}).get("id") or "") or None
            submission.viajechat_sync_status = "synced"
            submission.viajechat_sync_error = None
            submission.viajechat_synced_at = datetime.utcnow()
        except (ApiKeyDecryptionError, ViajeChatClientError, ValueError) as exc:
            logger.exception("VIAJECHAT_FORM_SYNC_FAILED submission_id=%s", submission.id)
            submission.viajechat_sync_status = "failed"
            submission.viajechat_sync_error = str(exc)[:500]
        db.commit()
    finally:
        db.close()


@router.get("/{form_id}", response_model=LeadFormPublicOut)
def read_public_form(
    form_id: int,
    request: Request,
    page_id: int | None = Query(None, alias="pageId"),
    page_slug: str | None = Query(None, alias="pageSlug"),
    db: Session = Depends(get_db),
) -> LeadFormPublicOut:
    form = _get_form(db, form_id)
    data = LeadFormPublicOut.from_orm(form)
    data.default_status_name = form.default_status.name if form.default_status else None
    data.default_status_color = form.default_status.color if form.default_status else None
    page_identifier = str(page_id or page_slug or "").strip()
    fingerprint = _build_submission_fingerprint(form.id, request, page_identifier)
    if fingerprint:
        exists = (
            db.query(LeadFormSubmission.id)
            .filter(
                LeadFormSubmission.form_id == form.id,
                LeadFormSubmission.fingerprint_hash == fingerprint,
            )
            .first()
        )
        data.already_submitted = bool(exists)
    else:
        data.already_submitted = False
    return data


@router.post("/{form_id}/submit", status_code=201)
def submit_public_form(
    form_id: int,
    payload: LeadFormSubmissionPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    form = _get_form(db, form_id)
    values_map = {value.fieldId: value for value in payload.values}

    normalized_fields: list[dict[str, str | bool]] = []
    name = cpf = phone = email = city = None
    birthdate = None

    for field in form.fields or []:
        field_id = field.get("id")
        submission_value = values_map.get(field_id)
        value = (submission_value.value if submission_value else "").strip()
        if field.get("required") and not value:
            raise HTTPException(status_code=422, detail=f"O campo {field.get('label') or field_id} e obrigatorio.")
        if submission_value and submission_value.type != field.get("type"):
            raise HTTPException(status_code=422, detail="Tipo de campo invalido.")
        normalized_fields.append(
            {
                "id": field_id,
                "label": field.get("label"),
                "type": field.get("type"),
                "value": value,
            }
        )
        field_type = (field.get("type") or "").lower()
        if field_type == "name":
            name = value
        elif field_type == "cpf":
            cpf = value
        elif field_type == "phone":
            phone = value
        elif field_type == "email":
            email = value
        elif field_type == "city":
            city = value
        elif field_type == "birthdate":
            birthdate = _parse_birthdate(value)

    page_identifier = str(payload.pageId or payload.pageSlug or "").strip()
    fingerprint = _build_submission_fingerprint(form.id, request, page_identifier)
    cpf_normalized = normalize_cpf(cpf)
    phone_normalized = normalize_phone(phone)
    email_normalized = normalize_email(email)

    linked_client_id, auto_linked_by = find_auto_match_client(
        db=db,
        agency_id=form.agency_id,
        cpf_normalized=cpf_normalized,
        email_normalized=email_normalized,
        phone_normalized=phone_normalized,
    )

    # O disparo inteligente e opt-in: sem template configurado o recebimento
    # do formulario nao deve gerar uma mensagem padrao inesperada.
    should_send_auto_message = bool((form.auto_whatsapp_message_template or "").strip())
    if form.auto_whatsapp_skip_if_client and linked_client_id:
        should_send_auto_message = False

    contact_clauses = []
    if email_normalized:
        contact_clauses.append(LeadFormSubmission.email_normalized == email_normalized)
    if phone_normalized:
        contact_clauses.append(LeadFormSubmission.phone_normalized == phone_normalized)

    if should_send_auto_message and contact_clauses and form.auto_whatsapp_skip_if_form_already_submitted:
        already_in_form = (
            db.query(LeadFormSubmission.id)
            .filter(
                LeadFormSubmission.form_id == form.id,
                or_(*contact_clauses),
            )
            .first()
        )
        if already_in_form:
            should_send_auto_message = False

    if (
        should_send_auto_message
        and contact_clauses
        and form.auto_whatsapp_skip_if_page_already_submitted
        and (payload.pageId is not None or (payload.pageSlug or "").strip())
    ):
        page_filters = [LeadFormSubmission.agency_id == form.agency_id]
        if payload.pageId is not None:
            page_filters.append(LeadFormSubmission.page_id == payload.pageId)
        else:
            page_filters.append(LeadFormSubmission.page_slug == (payload.pageSlug or "").strip())
        already_in_page = (
            db.query(LeadFormSubmission.id)
            .filter(*page_filters)
            .filter(or_(*contact_clauses))
            .first()
        )
        if already_in_page:
            should_send_auto_message = False

    if should_send_auto_message and contact_clauses and form.auto_whatsapp_skip_if_open_opportunity:
        has_open_opportunity = (
            db.query(LeadFormSubmission.id)
            .filter(
                LeadFormSubmission.agency_id == form.agency_id,
                LeadFormSubmission.closed_at.is_(None),
                or_(*contact_clauses),
            )
            .first()
        )
        if has_open_opportunity:
            should_send_auto_message = False

    submission = LeadFormSubmission(
        agency_id=form.agency_id,
        form_id=form.id,
        page_id=payload.pageId,
        page_title=payload.pageTitle,
        page_slug=payload.pageSlug,
        page_url=payload.pageUrl,
        name=name,
        cpf=cpf,
        cpf_normalized=cpf_normalized,
        phone=phone,
        phone_normalized=phone_normalized,
        email=email,
        email_normalized=email_normalized,
        city=city,
        birthdate=birthdate,
        payload={"values": normalized_fields, "source": payload.source},
        source=payload.source,
        status_id=form.default_status_id,
        client_id=linked_client_id,
        auto_linked_by=auto_linked_by,
        auto_linked_at=datetime.utcnow() if auto_linked_by else None,
        fingerprint_hash=fingerprint,
        viajechat_sync_status="pending" if form.viajechat_enabled else None,
    )
    db.add(submission)
    db.commit()
    if form.viajechat_enabled:
        background_tasks.add_task(_sync_submission_to_viajechat, submission.id)
    if should_send_auto_message:
        dispatch_opportunity_welcome_message(
            opportunity_id=submission.id,
            delay_seconds=form.auto_whatsapp_delay_seconds or 0,
        )
    return {"status": "ok"}
