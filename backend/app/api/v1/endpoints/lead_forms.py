from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.lead_form import LeadForm, LeadFormSubmission, LeadStatus
from app.models.user import User
from app.schemas.lead_form import (
    LeadContactOut,
    LeadContactStatusUpdate,
    LeadFormCreate,
    LeadFormOut,
    LeadFormUpdate,
    LeadStatusCreate,
    LeadStatusOut,
    LeadStatusUpdate,
)

router = APIRouter()


def _serialize_form(form: LeadForm, total_leads: int = 0) -> LeadFormOut:
    data = LeadFormOut.from_orm(form)
    data.total_leads = total_leads
    if hasattr(data, "default_status_name"):
        data.default_status_name = form.default_status.name if form.default_status else None
    if hasattr(data, "default_status_color"):
        data.default_status_color = form.default_status.color if form.default_status else None
    return data


def _serialize_contact(submission: LeadFormSubmission) -> LeadContactOut:
    return LeadContactOut(
        id=submission.id,
        form_id=submission.form_id,
        form_name=submission.form.title if submission.form else "",
        page_id=submission.page_id,
        page_title=submission.page_title,
        page_slug=submission.page_slug,
        page_url=submission.page_url,
        name=submission.name,
        cpf=submission.cpf,
        phone=submission.phone,
        email=submission.email,
        city=submission.city,
        source=submission.source,
        opportunity_name=submission.opportunity_name,
        estimated_value_cents=submission.estimated_value_cents,
        status_id=submission.status_id,
        status_name=submission.status.name if submission.status else None,
        status_color=submission.status.color if submission.status else None,
        client_id=submission.client_id,
        created_at=submission.created_at,
    )


@router.get("", response_model=List[LeadFormOut])
def list_lead_forms(
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[LeadFormOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    forms = (
        db.query(LeadForm)
        .options(joinedload(LeadForm.default_status))
        .filter(LeadForm.agency_id == agency_id)
        .order_by(LeadForm.created_at.desc())
        .all()
    )
    if not forms:
        return []
    form_ids = [form.id for form in forms]
    counts = dict(
        db.query(LeadFormSubmission.form_id, func.count(LeadFormSubmission.id))
        .filter(LeadFormSubmission.form_id.in_(form_ids))
        .group_by(LeadFormSubmission.form_id)
        .all()
    )
    return [_serialize_form(form, counts.get(form.id, 0)) for form in forms]


@router.post("", response_model=LeadFormOut, status_code=201)
def create_lead_form(
    form_in: LeadFormCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadFormOut:
    require_agency_membership(db=db, agency_id=form_in.agency_id, user_id=current_user.id)
    default_status_id, default_status = _validate_status_for_agency(form_in.default_status_id, form_in.agency_id, db)
    form = LeadForm(
        agency_id=form_in.agency_id,
        name=form_in.name.strip(),
        title=form_in.title.strip(),
        subtitle=form_in.subtitle.strip() if form_in.subtitle else None,
        button_label=form_in.button_label.strip(),
        button_color=form_in.button_color,
        show_logo=form_in.show_logo,
        fields=[field.dict() for field in form_in.fields],
        default_status_id=default_status_id,
    )
    if default_status is not None:
        form.default_status = default_status
    db.add(form)
    db.commit()
    db.refresh(form)
    return _serialize_form(form)


def _get_form_or_404(form_id: int, db: Session) -> LeadForm:
    form = db.query(LeadForm).filter(LeadForm.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    return form


def _get_status_or_404(status_id: int, db: Session) -> LeadStatus:
    status = db.query(LeadStatus).filter(LeadStatus.id == status_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status não encontrado.")
    return status


def _validate_status_for_agency(
    status_id: int | None, agency_id: int, db: Session
) -> tuple[int | None, LeadStatus | None]:
    if status_id is None:
        return None, None
    status = _get_status_or_404(status_id, db)
    if status.agency_id != agency_id:
        raise HTTPException(status_code=403, detail="Status inválido para esta agência.")
    return status.id, status


def _get_submission_or_404(contact_id: int, db: Session) -> LeadFormSubmission:
    submission = (
        db.query(LeadFormSubmission)
        .options(joinedload(LeadFormSubmission.form), joinedload(LeadFormSubmission.status))
        .filter(LeadFormSubmission.id == contact_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")
    return submission


@router.put("/{form_id}", response_model=LeadFormOut)
def update_lead_form(
    form_id: int,
    form_in: LeadFormUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadFormOut:
    form = _get_form_or_404(form_id, db)
    require_agency_membership(db=db, agency_id=form.agency_id, user_id=current_user.id)

    update_data = form_in.dict(exclude_unset=True)
    default_status = None
    if "subtitle" in update_data and update_data["subtitle"] is not None:
        update_data["subtitle"] = update_data["subtitle"].strip()
    if "fields" in update_data and update_data["fields"] is not None:
        update_data["fields"] = [field.dict() for field in form_in.fields or []]
    if "default_status_id" in update_data:
        status_id = update_data["default_status_id"]
        resolved_id, resolved = _validate_status_for_agency(status_id, form.agency_id, db)
        update_data["default_status_id"] = resolved_id
        default_status = resolved

    for key, value in update_data.items():
        setattr(form, key, value)
    if "default_status_id" in update_data:
        form.default_status = default_status

    db.add(form)
    db.commit()
    db.refresh(form)
    total_leads = db.query(LeadFormSubmission).filter(LeadFormSubmission.form_id == form.id).count()
    return _serialize_form(form, total_leads)


@router.delete("/{form_id}", status_code=204, response_class=Response)
def delete_lead_form(
    form_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    form = _get_form_or_404(form_id, db)
    require_agency_membership(db=db, agency_id=form.agency_id, user_id=current_user.id)
    db.delete(form)
    db.commit()
    return Response(status_code=204)


@router.get("/statuses", response_model=List[LeadStatusOut])
def list_lead_statuses(
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[LeadStatusOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    statuses = (
        db.query(LeadStatus)
        .filter(LeadStatus.agency_id == agency_id)
        .order_by(LeadStatus.created_at.asc())
        .all()
    )
    return [LeadStatusOut.from_orm(status) for status in statuses]


@router.post("/statuses", response_model=LeadStatusOut, status_code=201)
def create_lead_status(
    status_in: LeadStatusCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadStatusOut:
    require_agency_membership(db=db, agency_id=status_in.agency_id, user_id=current_user.id)
    status = LeadStatus(
        agency_id=status_in.agency_id,
        name=status_in.name.strip(),
        color=status_in.color.strip(),
    )
    db.add(status)
    db.commit()
    db.refresh(status)
    return LeadStatusOut.from_orm(status)


@router.put("/statuses/{status_id}", response_model=LeadStatusOut)
def update_lead_status(
    status_id: int,
    status_in: LeadStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadStatusOut:
    status = _get_status_or_404(status_id, db)
    require_agency_membership(db=db, agency_id=status.agency_id, user_id=current_user.id)
    if status_in.name is not None:
        status.name = status_in.name.strip()
    if status_in.color is not None:
        status.color = status_in.color.strip()
    db.add(status)
    db.commit()
    db.refresh(status)
    return LeadStatusOut.from_orm(status)


@router.delete("/statuses/{status_id}", status_code=204, response_class=Response)
def delete_lead_status(
    status_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    status = _get_status_or_404(status_id, db)
    require_agency_membership(db=db, agency_id=status.agency_id, user_id=current_user.id)
    db.delete(status)
    db.commit()
    return Response(status_code=204)


@router.get("/contacts", response_model=List[LeadContactOut])
def list_lead_contacts(
    agency_id: int = Query(..., alias="agencyId"),
    form_id: int | None = Query(None, alias="formId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[LeadContactOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    query = (
        db.query(LeadFormSubmission)
        .join(LeadForm, LeadFormSubmission.form_id == LeadForm.id)
        .options(joinedload(LeadFormSubmission.form), joinedload(LeadFormSubmission.status))
        .filter(LeadForm.agency_id == agency_id)
    )
    if form_id is not None:
        query = query.filter(LeadFormSubmission.form_id == form_id)
    submissions = query.order_by(LeadFormSubmission.created_at.desc()).all()
    return [_serialize_contact(submission) for submission in submissions]


@router.put("/contacts/{contact_id}/status", response_model=LeadContactOut)
def update_lead_contact_status(
    contact_id: int,
    payload: LeadContactStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)

    if payload.status_id is None:
        submission.status_id = None
        submission.status = None
    else:
        status = _get_status_or_404(payload.status_id, db)
        if status.agency_id != submission.agency_id:
            raise HTTPException(status_code=403, detail="Status inválido para este lead.")
        submission.status_id = status.id
        submission.status = status

    db.add(submission)
    db.commit()
    return _serialize_contact(_get_submission_or_404(contact_id, db))


@router.delete("/contacts/{contact_id}", status_code=204, response_class=Response)
def delete_lead_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    db.delete(submission)
    db.commit()
    return Response(status_code=204)
