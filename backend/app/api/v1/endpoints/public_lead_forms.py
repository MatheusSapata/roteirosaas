import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.models.lead_form import LeadForm, LeadFormSubmission
from app.schemas.lead_form import LeadFormPublicOut, LeadFormSubmissionPayload

router = APIRouter()


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


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _build_submission_fingerprint(form_id: int, request: Request, page_identifier: str | None = None) -> str | None:
    ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    page_component = page_identifier or ""
    raw = f"{form_id}:{page_component}:{ip}:{user_agent}".strip(":")
    if not raw:
        return None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
    db: Session = Depends(get_db),
) -> dict[str, str]:
    form = _get_form(db, form_id)
    values_map = {value.fieldId: value for value in payload.values}

    normalized_fields: list[dict[str, str | bool]] = []
    name = phone = email = city = None

    for field in form.fields or []:
        field_id = field.get("id")
        submission_value = values_map.get(field_id)
        value = submission_value.value if submission_value else ""
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
        elif field_type == "phone":
            phone = value
        elif field_type == "email":
            email = value
        elif field_type == "city":
            city = value

    page_identifier = str(payload.pageId or payload.pageSlug or "").strip()
    fingerprint = _build_submission_fingerprint(form.id, request, page_identifier)

    submission = LeadFormSubmission(
        agency_id=form.agency_id,
        form_id=form.id,
        page_id=payload.pageId,
        page_title=payload.pageTitle,
        page_slug=payload.pageSlug,
        page_url=payload.pageUrl,
        name=name,
        phone=phone,
        email=email,
        city=city,
        payload={"values": normalized_fields, "source": payload.source},
        source=payload.source,
        status_id=form.default_status_id,
        fingerprint_hash=fingerprint,
    )
    db.add(submission)
    db.commit()
    return {"status": "ok"}
