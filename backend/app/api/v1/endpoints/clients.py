from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.client import Client
from app.models.crm_note import ClientNote
from app.models.document import Document
from app.models.lead_form import LeadForm, LeadFormSubmission, LeadStatus
from app.models.user import User
from app.schemas.crm import (
    ClientCreate,
    ClientDetailOut,
    ClientNoteOut,
    ClientOut,
    ClientSummaryOut,
    ClientUpdate,
    DocumentOut,
    LeadContactDetailsOut,
    NoteCreate,
    OpportunityUpdate,
)
from app.services.contact_normalization import normalize_cpf, normalize_email, normalize_phone
from app.services.media_storage import media_storage
from app.services.team import get_user_effective_permissions

router = APIRouter()

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"}
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024


def _ensure_leads_delete_permission(db: Session, user: User, agency_id: int) -> None:
    if user.is_superuser:
        return
    effective = set(get_user_effective_permissions(db, user, agency_id))
    if "leads_full" not in effective:
        raise HTTPException(status_code=403, detail="Seu nível gerencial não permite excluir.")


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


def _serialize_client_note(note: ClientNote) -> ClientNoteOut:
    return ClientNoteOut(
        id=note.id,
        clientId=note.client_id,
        agencyId=note.agency_id,
        userId=note.user_id,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
        author={"id": note.user.id, "name": note.user.name} if note.user else None,
    )


def _build_opportunity_display_name(opportunity: LeadFormSubmission) -> str:
    if opportunity.opportunity_name:
        return opportunity.opportunity_name
    if opportunity.name and opportunity.page_title:
        return f"{opportunity.name} - {opportunity.page_title}"
    if opportunity.name:
        return f"Nova oportunidade - {opportunity.name}"
    return "Nova oportunidade"


def _serialize_client_summary(client: Client) -> ClientSummaryOut:
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


def _serialize_opportunity(opportunity: LeadFormSubmission) -> LeadContactDetailsOut:
    return LeadContactDetailsOut(
        id=opportunity.id,
        agencyId=opportunity.agency_id,
        formId=opportunity.form_id,
        formName=opportunity.form.title if opportunity.form else "",
        pageId=opportunity.page_id,
        pageTitle=opportunity.page_title,
        pageSlug=opportunity.page_slug,
        pageUrl=opportunity.page_url,
        name=opportunity.name,
        cpf=opportunity.cpf,
        phone=opportunity.phone,
        email=opportunity.email,
        city=opportunity.city,
        birthdate=opportunity.birthdate,
        source=opportunity.source,
        statusId=opportunity.status_id,
        statusName=opportunity.status.name if opportunity.status else None,
        statusColor=opportunity.status.color if opportunity.status else None,
        opportunityName=_build_opportunity_display_name(opportunity),
        estimatedValueCents=opportunity.estimated_value_cents,
        expectedCloseDate=opportunity.expected_close_date,
        internalNotes=opportunity.internal_notes,
        autoLinkedBy=opportunity.auto_linked_by,
        autoLinkedAt=opportunity.auto_linked_at,
        closeOutcome=opportunity.close_outcome,
        closedAt=opportunity.closed_at,
        responsibleUserId=opportunity.responsible_user_id,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at,
        payload=opportunity.payload,
        client=_serialize_client_summary(opportunity.client) if opportunity.client else None,
        notes=[],
        documents=[],
        clientSuggestions=[],
    )


def _client_out(client: Client, db: Session) -> ClientOut:
    opportunity_rows = (
        db.query(
            func.count(LeadFormSubmission.id),
            func.coalesce(func.sum(LeadFormSubmission.estimated_value_cents), 0),
            func.max(LeadFormSubmission.created_at),
        )
        .filter(LeadFormSubmission.client_id == client.id)
        .first()
    )
    total_count = int(opportunity_rows[0] or 0) if opportunity_rows else 0
    total_value = int(opportunity_rows[1] or 0) if opportunity_rows else 0
    last_at = opportunity_rows[2] if opportunity_rows else None
    open_count = (
        db.query(func.count(LeadFormSubmission.id))
        .filter(
            LeadFormSubmission.client_id == client.id,
            LeadFormSubmission.closed_at.is_(None),
        )
        .scalar()
        or 0
    )
    return ClientOut(
        id=client.id,
        agencyId=client.agency_id,
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
        birthdate=client.birthdate,
        notes=client.notes,
        tags=client.tags,
        opportunitiesCount=total_count,
        openOpportunitiesCount=int(open_count),
        totalEstimatedValueCents=total_value,
        lastOpportunityAt=last_at,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


def _get_client_or_404(client_id: int, db: Session) -> Client:
    client = db.query(Client).filter(Client.id == client_id, Client.deleted_at.is_(None)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    return client


def _get_manual_form_id(agency_id: int, db: Session) -> int:
    form_id = (
        db.query(LeadForm.id)
        .filter(LeadForm.agency_id == agency_id)
        .order_by(LeadForm.created_at.asc())
        .limit(1)
        .scalar()
    )
    if form_id is None:
        raise HTTPException(
            status_code=400,
            detail="Nao ha formulario disponivel para criar oportunidade manual nesta agencia.",
        )
    return int(form_id)


def _apply_client_normalization(client: Client) -> None:
    client.cpf_normalized = normalize_cpf(client.cpf)
    client.phone_normalized = normalize_phone(client.phone)
    client.email_normalized = normalize_email(client.email)


def _ensure_unique_client_identity(client: Client, db: Session) -> None:
    if client.cpf_normalized:
        existing = (
            db.query(Client)
            .filter(
                Client.agency_id == client.agency_id,
                Client.cpf_normalized == client.cpf_normalized,
                Client.deleted_at.is_(None),
                Client.id != getattr(client, "id", None),
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Ja existe um cliente com este CPF nesta agencia.")


@router.get("", response_model=list[ClientOut])
def list_clients(
    agency_id: int = Query(..., alias="agencyId"),
    q: str | None = Query(None),
    city: str | None = Query(None),
    has_open_opportunities: bool | None = Query(None, alias="hasOpenOpportunities"),
    without_opportunities: bool | None = Query(None, alias="withoutOpportunities"),
    created_from: datetime | None = Query(None, alias="createdFrom"),
    created_to: datetime | None = Query(None, alias="createdTo"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ClientOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    query = db.query(Client).filter(Client.agency_id == agency_id, Client.deleted_at.is_(None))
    if q:
        pattern = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Client.name).like(pattern),
                func.lower(func.coalesce(Client.email, "")).like(pattern),
                func.lower(func.coalesce(Client.cpf, "")).like(pattern),
                func.lower(func.coalesce(Client.phone, "")).like(pattern),
            )
        )
    if city:
        query = query.filter(func.lower(func.coalesce(Client.city, "")) == city.strip().lower())
    if created_from:
        query = query.filter(Client.created_at >= created_from)
    if created_to:
        query = query.filter(Client.created_at <= created_to)
    clients = query.order_by(Client.created_at.desc()).all()

    if without_opportunities:
        clients = [client for client in clients if not client.opportunities]
    if has_open_opportunities is True:
        clients = [
            client
            for client in clients
            if any(op.closed_at is None for op in client.opportunities or [])
        ]
    return [_client_out(client, db) for client in clients]


@router.get("/search", response_model=list[ClientSummaryOut])
def search_clients(
    agency_id: int = Query(..., alias="agencyId"),
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ClientSummaryOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    pattern = f"%{q.strip().lower()}%"
    rows = (
        db.query(Client)
        .filter(
            Client.agency_id == agency_id,
            Client.deleted_at.is_(None),
            or_(
                func.lower(Client.name).like(pattern),
                func.lower(func.coalesce(Client.email, "")).like(pattern),
                func.lower(func.coalesce(Client.cpf, "")).like(pattern),
                func.lower(func.coalesce(Client.phone, "")).like(pattern),
            ),
        )
        .order_by(Client.updated_at.desc(), Client.created_at.desc())
        .limit(20)
        .all()
    )
    return [_serialize_client_summary(client) for client in rows]


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientOut:
    require_agency_membership(db=db, agency_id=payload.agency_id, user_id=current_user.id)
    client = Client(**payload.model_dump(by_alias=False))
    _apply_client_normalization(client)
    _ensure_unique_client_identity(client, db)
    db.add(client)
    db.commit()
    db.refresh(client)
    return _client_out(client, db)


@router.get("/{client_id}", response_model=ClientDetailOut)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientDetailOut:
    client = (
        db.query(Client)
        .options(
            joinedload(Client.opportunities).joinedload(LeadFormSubmission.form),
            joinedload(Client.opportunities).joinedload(LeadFormSubmission.status),
            joinedload(Client.client_notes).joinedload(ClientNote.user),
            joinedload(Client.documents),
        )
        .filter(Client.id == client_id, Client.deleted_at.is_(None))
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    base = _client_out(client, db)
    notes = sorted(client.client_notes or [], key=lambda item: item.created_at or datetime.min, reverse=True)
    documents = [document for document in (client.documents or []) if document.deleted_at is None]
    return ClientDetailOut(
        **base.model_dump(),
        opportunities=[_serialize_opportunity(opportunity) for opportunity in sorted(client.opportunities or [], key=lambda item: item.created_at or datetime.min, reverse=True)],
        notesTimeline=[_serialize_client_note(note) for note in notes],
        documents=[_serialize_document(document) for document in documents],
    )


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientOut:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    _apply_client_normalization(client)
    _ensure_unique_client_identity(client, db)
    db.add(client)
    db.commit()
    db.refresh(client)
    return _client_out(client, db)


@router.delete("/{client_id}", status_code=204, response_class=Response)
def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    _ensure_leads_delete_permission(db, current_user, client.agency_id)
    client.deleted_at = datetime.utcnow()
    db.add(client)
    db.commit()
    return Response(status_code=204)


@router.get("/{client_id}/notes", response_model=list[ClientNoteOut])
def list_client_notes(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ClientNoteOut]:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    rows = (
        db.query(ClientNote)
        .options(joinedload(ClientNote.user))
        .filter(ClientNote.client_id == client.id, ClientNote.agency_id == client.agency_id)
        .order_by(ClientNote.created_at.desc())
        .all()
    )
    return [_serialize_client_note(note) for note in rows]


@router.post("/{client_id}/notes", response_model=ClientNoteOut, status_code=201)
def create_client_note(
    client_id: int,
    payload: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ClientNoteOut:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    note = ClientNote(
        agency_id=client.agency_id,
        client_id=client.id,
        user_id=current_user.id,
        content=payload.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    note = db.query(ClientNote).options(joinedload(ClientNote.user)).filter(ClientNote.id == note.id).first()
    assert note is not None
    return _serialize_client_note(note)


@router.get("/{client_id}/documents", response_model=list[DocumentOut])
def list_client_documents(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    documents = (
        db.query(Document)
        .filter(Document.client_id == client.id, Document.agency_id == client.agency_id, Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_serialize_document(document) for document in documents]


@router.post("/{client_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_client_document(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentOut:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo nao suportado.")
    content = await file.read()
    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Arquivo excede o limite de 10MB.")

    file_url = media_storage.save(content, file.filename or "documento", getattr(file, "content_type", None))
    document = Document(
        agency_id=client.agency_id,
        client_id=client.id,
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


@router.post("/{client_id}/opportunities", response_model=LeadContactDetailsOut, status_code=201)
def create_client_opportunity(
    client_id: int,
    payload: OpportunityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LeadContactDetailsOut:
    client = _get_client_or_404(client_id, db)
    require_agency_membership(db=db, agency_id=client.agency_id, user_id=current_user.id)
    opportunity = LeadFormSubmission(
        agency_id=client.agency_id,
        form_id=_get_manual_form_id(client.agency_id, db),
        client_id=client.id,
        name=client.name,
        cpf=client.cpf,
        cpf_normalized=client.cpf_normalized,
        phone=client.phone,
        phone_normalized=client.phone_normalized,
        email=client.email,
        email_normalized=client.email_normalized,
        city=client.city,
        birthdate=client.birthdate,
        payload={"values": [], "source": "manual"},
        source="Criada manualmente",
        opportunity_name=payload.opportunity_name,
        estimated_value_cents=payload.estimated_value_cents,
        expected_close_date=payload.expected_close_date,
        internal_notes=payload.internal_notes,
        responsible_user_id=payload.responsible_user_id or current_user.id,
        status_id=payload.status_id,
    )
    db.add(opportunity)
    db.commit()
    opportunity = (
        db.query(LeadFormSubmission)
        .options(joinedload(LeadFormSubmission.form), joinedload(LeadFormSubmission.status), joinedload(LeadFormSubmission.client))
        .filter(LeadFormSubmission.id == opportunity.id)
        .first()
    )
    assert opportunity is not None
    return _serialize_opportunity(opportunity)
