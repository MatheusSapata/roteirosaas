from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.client import Client
from app.models.crm_note import OpportunityNote
from app.models.document import Document
from app.models.lead_form import LeadForm, LeadFormSubmission, LeadStatus
from app.models.user import User
from app.schemas.crm import (
    ClientSummaryOut,
    DocumentOut,
    LeadContactDetailsOut,
    ManualOpportunityCreate,
    NoteCreate,
    OpportunityFinalize,
    OpportunityLinkClientPayload,
    OpportunityNoteOut,
    OpportunityUpdate,
)
from app.services.client_matching import find_auto_match_client, find_auto_match_client_id
from app.services.contact_normalization import normalize_cpf, normalize_email, normalize_phone
from app.services.media_storage import media_storage

router = APIRouter()

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"}
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024


def _get_submission_or_404(contact_id: int, db: Session) -> LeadFormSubmission:
    submission = (
        db.query(LeadFormSubmission)
        .options(
            joinedload(LeadFormSubmission.form),
            joinedload(LeadFormSubmission.status),
            joinedload(LeadFormSubmission.client),
            joinedload(LeadFormSubmission.notes).joinedload(OpportunityNote.user),
            joinedload(LeadFormSubmission.documents),
        )
        .filter(LeadFormSubmission.id == contact_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Oportunidade nao encontrada.")
    return submission


def _get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.query(Client).filter(Client.id == client_id, Client.deleted_at.is_(None)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    return client


def _serialize_client_summary(client: Client | None) -> ClientSummaryOut | None:
    if not client:
        return None
    return ClientSummaryOut(
        id=client.id,
        name=client.name,
        cpf=client.cpf,
        phone=client.phone,
        email=client.email,
        city=client.city,
        zipcode=client.zipcode,
        street=client.street,
        number=client.number,
        complement=client.complement,
        neighborhood=client.neighborhood,
        state=client.state,
    )


def _serialize_note(note: OpportunityNote) -> OpportunityNoteOut:
    return OpportunityNoteOut(
        id=note.id,
        opportunityId=note.opportunity_id,
        agencyId=note.agency_id,
        userId=note.user_id,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
        author={"id": note.user.id, "name": note.user.name} if note.user else None,
    )


def _serialize_document(document: Document) -> DocumentOut:
    source_label = "Cliente" if document.client_id and not document.opportunity_id else "Oportunidade"
    return DocumentOut(
        id=document.id,
        agencyId=document.agency_id,
        clientId=document.client_id,
        opportunityId=document.opportunity_id,
        uploadedByUserId=document.uploaded_by_user_id,
        fileName=document.file_name,
        fileUrl=document.file_url,
        fileType=document.file_type,
        fileSize=document.file_size,
        created_at=document.created_at,
        sourceLabel=source_label,
    )


def _build_opportunity_display_name(submission: LeadFormSubmission) -> str:
    if submission.opportunity_name:
        return submission.opportunity_name
    if submission.name and submission.page_title:
        return f"{submission.name} - {submission.page_title}"
    if submission.name:
        return f"Nova oportunidade - {submission.name}"
    return "Nova oportunidade"


def _get_manual_form_id(agency_id: int, db: Session) -> int:
    form_id = (
        db.query(LeadFormSubmission.form_id)
        .filter(LeadFormSubmission.agency_id == agency_id)
        .order_by(LeadFormSubmission.created_at.asc())
        .limit(1)
        .scalar()
    )
    if form_id is None:
        lead_form_id = (
            db.query(LeadForm.id)
            .filter(LeadForm.agency_id == agency_id)
            .order_by(LeadForm.created_at.asc())
            .limit(1)
            .scalar()
        )
        if lead_form_id is None:
            raise HTTPException(
                status_code=400,
                detail="Nao ha formulario disponivel para criar oportunidade manual nesta agencia.",
            )
        return int(lead_form_id)
    return int(form_id)


def _ensure_closure_status(submission: LeadFormSubmission, outcome: str, db: Session) -> LeadStatus:
    target_name = "Ganha" if outcome == "won" else "Perdida"
    target_color = "#16A34A" if outcome == "won" else "#DC2626"
    status = (
        db.query(LeadStatus)
        .filter(LeadStatus.agency_id == submission.agency_id, LeadStatus.name == target_name)
        .first()
    )
    if status:
        return status
    status = LeadStatus(agency_id=submission.agency_id, name=target_name, color=target_color)
    db.add(status)
    db.flush()
    return status


def _get_client_suggestions(submission: LeadFormSubmission, db: Session) -> list[ClientSummaryOut]:
    filters = []
    if submission.email_normalized:
        filters.append(Client.email_normalized == submission.email_normalized)
    if submission.phone_normalized:
        filters.append(Client.phone_normalized == submission.phone_normalized)
    if not filters:
        return []
    rows = (
        db.query(Client)
        .filter(
            Client.agency_id == submission.agency_id,
            Client.deleted_at.is_(None),
            or_(*filters),
        )
        .order_by(Client.updated_at.desc(), Client.created_at.desc())
        .limit(5)
        .all()
    )
    return [_serialize_client_summary(client) for client in rows if client]


def _serialize_details(submission: LeadFormSubmission, db: Session) -> LeadContactDetailsOut:
    notes = sorted(submission.notes or [], key=lambda item: item.created_at or datetime.min, reverse=True)
    documents = [document for document in (submission.documents or []) if document.deleted_at is None]
    return LeadContactDetailsOut(
        id=submission.id,
        agencyId=submission.agency_id,
        formId=submission.form_id,
        formName=submission.form.title if submission.form else "",
        pageId=submission.page_id,
        pageTitle=submission.page_title,
        pageSlug=submission.page_slug,
        pageUrl=submission.page_url,
        name=submission.name,
        cpf=submission.cpf,
        phone=submission.phone,
        email=submission.email,
        city=submission.city,
        birthdate=submission.birthdate,
        source=submission.source,
        statusId=submission.status_id,
        statusName=submission.status.name if submission.status else None,
        statusColor=submission.status.color if submission.status else None,
        opportunityName=_build_opportunity_display_name(submission),
        estimatedValueCents=submission.estimated_value_cents,
        expectedCloseDate=submission.expected_close_date,
        internalNotes=submission.internal_notes,
        autoLinkedBy=submission.auto_linked_by,
        autoLinkedAt=submission.auto_linked_at,
        closeOutcome=submission.close_outcome,
        closedAt=submission.closed_at,
        responsibleUserId=submission.responsible_user_id,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
        payload=submission.payload,
        client=_serialize_client_summary(submission.client),
        notes=[_serialize_note(note) for note in notes],
        documents=[_serialize_document(document) for document in documents],
        clientSuggestions=_get_client_suggestions(submission, db) if submission.client_id is None else [],
    )


@router.get("/contacts/{contact_id}/details", response_model=LeadContactDetailsOut)
def get_opportunity_details(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    return _serialize_details(submission, db)


@router.patch("/contacts/{contact_id}", response_model=LeadContactDetailsOut)
def update_opportunity(
    contact_id: int,
    payload: OpportunityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)

    data = payload.model_dump(exclude_unset=True, by_alias=False)
    if "status_id" in data and data["status_id"] is not None:
        status = db.query(LeadStatus).filter(LeadStatus.id == data["status_id"]).first()
        if not status or status.agency_id != submission.agency_id:
            raise HTTPException(status_code=403, detail="Status invalido para esta agencia.")
    for key, value in data.items():
        setattr(submission, key, value)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return _serialize_details(_get_submission_or_404(contact_id, db), db)


@router.post("/contacts/manual", response_model=LeadContactDetailsOut, status_code=201)
def create_manual_opportunity(
    payload: ManualOpportunityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    require_agency_membership(db=db, agency_id=payload.agency_id, user_id=current_user.id)

    cpf_normalized = normalize_cpf(payload.cpf)
    phone_normalized = normalize_phone(payload.phone)
    email_normalized = normalize_email(payload.email)

    linked_client_id = None
    auto_linked_by = None
    selected_client: Client | None = None
    if payload.client_id is not None:
        selected_client = _get_client_or_404(payload.client_id, db)
        if selected_client.agency_id != payload.agency_id:
            raise HTTPException(status_code=403, detail="Cliente invalido para esta agencia.")
        linked_client_id = selected_client.id
    else:
        linked_client_id, auto_linked_by = find_auto_match_client(
            db=db,
            agency_id=payload.agency_id,
            cpf_normalized=cpf_normalized,
            email_normalized=email_normalized,
            phone_normalized=phone_normalized,
        )

    if payload.status_id is not None:
        status = db.query(LeadStatus).filter(LeadStatus.id == payload.status_id).first()
        if not status or status.agency_id != payload.agency_id:
            raise HTTPException(status_code=403, detail="Status invalido para esta agencia.")

    submission = LeadFormSubmission(
        agency_id=payload.agency_id,
        form_id=_get_manual_form_id(payload.agency_id, db),
        name=selected_client.name if selected_client else payload.name,
        cpf=selected_client.cpf if selected_client else payload.cpf,
        cpf_normalized=selected_client.cpf_normalized if selected_client else cpf_normalized,
        phone=selected_client.phone if selected_client else payload.phone,
        phone_normalized=selected_client.phone_normalized if selected_client else phone_normalized,
        email=selected_client.email if selected_client else payload.email,
        email_normalized=selected_client.email_normalized if selected_client else email_normalized,
        city=selected_client.city if selected_client else payload.city,
        birthdate=selected_client.birthdate if selected_client else payload.birthdate,
        payload={"values": [], "source": "manual"},
        source="Criada manualmente",
        status_id=payload.status_id,
        client_id=linked_client_id,
        opportunity_name=payload.opportunity_name,
        estimated_value_cents=payload.estimated_value_cents,
        expected_close_date=payload.expected_close_date,
        internal_notes=payload.internal_notes,
        responsible_user_id=payload.responsible_user_id or current_user.id,
        auto_linked_by=auto_linked_by,
        auto_linked_at=datetime.utcnow() if auto_linked_by else None,
    )
    db.add(submission)
    db.commit()
    return _serialize_details(_get_submission_or_404(submission.id, db), db)


@router.post("/contacts/{contact_id}/finalize", response_model=LeadContactDetailsOut)
def finalize_opportunity(
    contact_id: int,
    payload: OpportunityFinalize,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)

    closure_status = _ensure_closure_status(submission, payload.outcome, db)
    submission.status_id = closure_status.id
    submission.close_outcome = payload.outcome
    submission.closed_at = datetime.utcnow()
    db.add(submission)
    db.flush()

    if payload.note:
        note = OpportunityNote(
            agency_id=submission.agency_id,
            opportunity_id=submission.id,
            user_id=current_user.id,
            content=payload.note,
        )
        db.add(note)

    db.commit()
    return _serialize_details(_get_submission_or_404(contact_id, db), db)


@router.post("/contacts/{contact_id}/link-client", response_model=LeadContactDetailsOut)
def link_opportunity_client(
    contact_id: int,
    payload: OpportunityLinkClientPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    client = _get_client_or_404(payload.client_id, db)
    if client.agency_id != submission.agency_id:
        raise HTTPException(status_code=403, detail="Cliente invalido para esta agencia.")
    submission.client_id = client.id
    submission.auto_linked_by = None
    submission.auto_linked_at = None
    db.add(submission)
    db.commit()
    return _serialize_details(_get_submission_or_404(contact_id, db), db)


@router.delete("/contacts/{contact_id}/link-client", response_model=LeadContactDetailsOut)
def unlink_opportunity_client(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    submission.client_id = None
    submission.auto_linked_by = None
    submission.auto_linked_at = None
    db.add(submission)
    db.commit()
    return _serialize_details(_get_submission_or_404(contact_id, db), db)


@router.get("/contacts/{contact_id}/notes", response_model=list[OpportunityNoteOut])
def list_opportunity_notes(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[OpportunityNoteOut]:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    notes = (
        db.query(OpportunityNote)
        .options(joinedload(OpportunityNote.user))
        .filter(OpportunityNote.opportunity_id == contact_id, OpportunityNote.agency_id == submission.agency_id)
        .order_by(OpportunityNote.created_at.desc())
        .all()
    )
    return [_serialize_note(note) for note in notes]


@router.post("/contacts/{contact_id}/notes", response_model=OpportunityNoteOut, status_code=201)
def create_opportunity_note(
    contact_id: int,
    payload: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OpportunityNoteOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    note = OpportunityNote(
        agency_id=submission.agency_id,
        opportunity_id=submission.id,
        user_id=current_user.id,
        content=payload.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    note = db.query(OpportunityNote).options(joinedload(OpportunityNote.user)).filter(OpportunityNote.id == note.id).first()
    assert note is not None
    return _serialize_note(note)


@router.get("/contacts/{contact_id}/documents", response_model=list[DocumentOut])
def list_opportunity_documents(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    documents = (
        db.query(Document)
        .filter(
            Document.opportunity_id == submission.id,
            Document.agency_id == submission.agency_id,
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_serialize_document(document) for document in documents]


@router.post("/contacts/{contact_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_opportunity_document(
    contact_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentOut:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo nao suportado.")

    content = await file.read()
    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Arquivo excede o limite de 10MB.")

    file_url = media_storage.save(content, file.filename or "documento", getattr(file, "content_type", None))
    document = Document(
        agency_id=submission.agency_id,
        opportunity_id=submission.id,
        uploaded_by_user_id=current_user.id,
        file_name=file.filename or "documento",
        file_url=file_url,
        file_type=getattr(file, "content_type", None),
        file_size=len(content),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _serialize_document(document)


@router.get("/contacts/{contact_id}/client-suggestions", response_model=list[ClientSummaryOut])
def get_opportunity_client_suggestions(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ClientSummaryOut]:
    submission = _get_submission_or_404(contact_id, db)
    require_agency_membership(db=db, agency_id=submission.agency_id, user_id=current_user.id)
    return _get_client_suggestions(submission, db)
