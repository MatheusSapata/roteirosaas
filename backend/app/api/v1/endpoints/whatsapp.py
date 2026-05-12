from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, field_validator
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.client import Client
from app.models.lead_form import LeadFormSubmission
from app.models.user import User
from app.models.whatsapp import WhatsAppConnection, WhatsAppConversation, WhatsAppMessage
from app.schemas.whatsapp import (
    WhatsAppInboxAccessOut,
    EnsureConversationPayload,
    SendTextPayload,
    WhatsAppConversationUpdatePayload,
    WhatsAppConnectionCreate,
    WhatsAppConnectionOut,
    WhatsAppConnectionStatusOut,
    WhatsAppConversationOut,
    WhatsAppMessageOut,
)
from app.services.evolution import EvolutionService
from app.services.whatsapp_domain import WhatsAppDomainService
from app.services.whatsapp_realtime import whatsapp_realtime
from app.services.whatsapp_access import has_whatsapp_inbox_access

router = APIRouter()
evolution_service = EvolutionService()
domain_service = WhatsAppDomainService()


class TestSendPayload(BaseModel):
    number: str
    text: str

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: str) -> str:
        digits = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("Numero invalido para envio.")
        return digits

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Texto obrigatorio.")
        return cleaned


def _serialize_connection(connection: WhatsAppConnection) -> WhatsAppConnectionOut:
    return WhatsAppConnectionOut(
        id=connection.id,
        agencyId=connection.agency_id,
        name=connection.name,
        instanceName=connection.instance_name,
        phoneNumber=connection.phone_number,
        status=connection.status,
        isDefault=bool(connection.is_default),
        createdByUserId=connection.created_by_user_id,
        connectedAt=connection.connected_at,
        disconnectedAt=connection.disconnected_at,
        createdAt=connection.created_at,
        updatedAt=connection.updated_at,
    )


def _serialize_conversation(item: WhatsAppConversation) -> WhatsAppConversationOut:
    return WhatsAppConversationOut(
        id=item.id,
        agencyId=item.agency_id,
        connectionId=item.connection_id,
        clientId=item.client_id,
        opportunityId=item.opportunity_id,
        remotePhone=item.remote_phone,
        remoteName=item.remote_name,
        avatarUrl=item.avatar_url,
        lastMessageText=item.last_message_text,
        lastMessageAt=item.last_message_at,
        unreadCount=int(item.unread_count or 0),
        openOpportunitiesCount=getattr(item, "open_opportunities_count", None),
        openOpportunitiesValueCents=getattr(item, "open_opportunities_value_cents", None),
        createdAt=item.created_at,
        updatedAt=item.updated_at,
    )


def _serialize_message(item: WhatsAppMessage) -> WhatsAppMessageOut:
    return WhatsAppMessageOut(
        id=item.id,
        agencyId=item.agency_id,
        connectionId=item.connection_id,
        conversationId=item.conversation_id,
        externalMessageId=item.external_message_id,
        direction=item.direction,
        messageType=item.message_type,
        body=item.body,
        status=item.status,
        remotePhone=item.remote_phone,
        mediaUrl=item.media_url,
        mediaMimeType=item.media_mime_type,
        mediaFileName=item.media_file_name,
        mediaSize=item.media_size,
        mediaDuration=item.media_duration,
        sentAt=item.sent_at,
        receivedAt=item.received_at,
        createdAt=item.created_at,
    )


def _emit_conversation_updated(conversation: WhatsAppConversation) -> None:
    whatsapp_realtime.broadcast_to_agency_best_effort(
        agency_id=conversation.agency_id,
        payload={
            "type": "whatsapp.conversation.updated",
            "agency_id": conversation.agency_id,
            "conversation": _serialize_conversation(conversation).model_dump(by_alias=True, mode="json"),
        },
    )


def _emit_message_created(message: WhatsAppMessage) -> None:
    whatsapp_realtime.broadcast_to_agency_best_effort(
        agency_id=message.agency_id,
        payload={
            "type": "whatsapp.message.created",
            "agency_id": message.agency_id,
            "conversation_id": message.conversation_id,
            "message": _serialize_message(message).model_dump(by_alias=True, mode="json"),
        },
    )


def _emit_unread_count(db: Session, agency_id: int) -> None:
    total = (
        db.query(func.coalesce(func.sum(WhatsAppConversation.unread_count), 0))
        .filter(WhatsAppConversation.agency_id == agency_id)
        .scalar()
        or 0
    )


def _resolve_inbox_granted_at(db: Session, *, user_id: int, agency_id: int) -> Any | None:
    from app.models.whatsapp import WhatsAppInboxPermission

    permission = (
        db.query(WhatsAppInboxPermission)
        .filter(
            WhatsAppInboxPermission.enabled.is_(True),
            WhatsAppInboxPermission.revoked_at.is_(None),
            or_(
                WhatsAppInboxPermission.user_id == user_id,
                WhatsAppInboxPermission.agency_id == agency_id,
            ),
        )
        .order_by(WhatsAppInboxPermission.granted_at.desc().nullslast(), WhatsAppInboxPermission.id.desc())
        .first()
    )
    if not permission:
        return None
    return permission.granted_at
    whatsapp_realtime.broadcast_to_agency_best_effort(
        agency_id=agency_id,
        payload={
            "type": "whatsapp.unread_count.updated",
            "agency_id": agency_id,
            "total_unread": int(total),
        },
    )


@router.get("/health")
def whatsapp_health(current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    evolution = evolution_service.check_evolution_health()
    redis = evolution_service.check_redis_health()
    return {
        "status": "ok" if evolution.ok and redis.ok else "degraded",
        "instance": evolution_service.test_instance_name,
        "evolution": {"ok": evolution.ok, "detail": evolution.detail},
        "redis": {"ok": redis.ok, "detail": redis.detail},
        "checked_by_user_id": current_user.id,
    }


@router.get("/inbox-access", response_model=WhatsAppInboxAccessOut)
def get_inbox_access(
    agency_id: int | None = Query(default=None, alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppInboxAccessOut:
    resolved_agency_id = agency_id or current_user.primary_agency_id
    if resolved_agency_id and not current_user.is_superuser:
        require_agency_membership(db=db, agency_id=resolved_agency_id, user_id=current_user.id)
    enabled = has_whatsapp_inbox_access(db, user=current_user, agency_id=resolved_agency_id)
    return WhatsAppInboxAccessOut(enabled=enabled)


@router.post("/test-instance")
def create_test_instance(current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    try:
        created = evolution_service.create_instance()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao criar instância de teste: {exc}") from exc
    return {
        "status": "created" if not created.get("idempotent") else "already_exists",
        "instance": evolution_service.test_instance_name,
        "data": created,
        "requested_by_user_id": current_user.id,
    }


@router.get("/test-instance/qr")
def get_test_instance_qr(current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    try:
        qr_data = evolution_service.get_qr_code()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao buscar QR Code: {exc}") from exc
    return {
        "instance": evolution_service.test_instance_name,
        "qr_code_base64": qr_data.get("qr_code_base64"),
        "pairing_code": qr_data.get("pairing_code"),
        "code": qr_data.get("code"),
        "count": qr_data.get("count"),
        "diagnosis": qr_data.get("diagnosis"),
        "diagnostics": qr_data.get("diagnostics"),
        "attempts": qr_data.get("attempts"),
        "raw": qr_data.get("raw"),
        "requested_by_user_id": current_user.id,
    }


@router.post("/test-instance/reset")
def reset_test_instance(current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    try:
        result = evolution_service.reset_instance()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao resetar instância de teste: {exc}") from exc
    return {
        "status": "reset_done",
        "instance": evolution_service.test_instance_name,
        "result": result,
        "next_step": "Chame GET /api/v1/whatsapp/test-instance/qr para obter o QR/pairing code.",
        "requested_by_user_id": current_user.id,
    }


@router.get("/connections", response_model=list[WhatsAppConnectionOut])
def list_connections(
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[WhatsAppConnectionOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    rows = (
        db.query(WhatsAppConnection)
        .filter(WhatsAppConnection.agency_id == agency_id)
        .order_by(WhatsAppConnection.created_at.desc())
        .all()
    )
    return [_serialize_connection(item) for item in rows]


@router.post("/connections", response_model=WhatsAppConnectionOut, status_code=201)
def create_connection(
    payload: WhatsAppConnectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppConnectionOut:
    require_agency_membership(db=db, agency_id=payload.agency_id, user_id=current_user.id)
    created = domain_service.create_connection(
        db=db,
        agency_id=payload.agency_id,
        name=payload.name,
        created_by_user_id=current_user.id,
    )
    return _serialize_connection(created)


@router.get("/connections/{connection_id}/qr")
def get_connection_qr(
    connection_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    connection = domain_service.get_connection_or_404(db=db, agency_id=agency_id, connection_id=connection_id)
    qr_data = evolution_service.get_qr_code(instance_name=connection.instance_name)
    return {
        "connectionId": connection.id,
        "instanceName": connection.instance_name,
        "qr_code_base64": qr_data.get("qr_code_base64"),
        "pairing_code": qr_data.get("pairing_code"),
        "code": qr_data.get("code"),
        "count": qr_data.get("count"),
        "diagnosis": qr_data.get("diagnosis"),
        "diagnostics": qr_data.get("diagnostics"),
        "attempts": qr_data.get("attempts"),
        "raw": qr_data.get("raw"),
    }


@router.get("/connections/{connection_id}/status", response_model=WhatsAppConnectionStatusOut)
def get_connection_status(
    connection_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppConnectionStatusOut:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    connection = domain_service.get_connection_or_404(db=db, agency_id=agency_id, connection_id=connection_id)
    status, raw_state, raw = domain_service.update_connection_status_from_evolution(db=db, connection=connection)
    whatsapp_realtime.broadcast_to_agency_best_effort(
        agency_id=agency_id,
        payload={
            "type": "whatsapp.connection.status_changed",
            "agency_id": agency_id,
            "connection_id": connection.id,
            "status": status,
        },
    )
    return WhatsAppConnectionStatusOut(
        connectionId=connection.id,
        instanceName=connection.instance_name,
        status=status,
        rawState=raw_state,
        raw=raw if isinstance(raw, dict) else {"data": raw},
    )


@router.post("/connections/{connection_id}/disconnect")
def disconnect_connection(
    connection_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    connection = domain_service.get_connection_or_404(db=db, agency_id=agency_id, connection_id=connection_id)
    response = evolution_service.disconnect_instance(instance_name=connection.instance_name)
    connection.status = "disconnected"
    db.add(connection)
    db.commit()
    db.refresh(connection)
    whatsapp_realtime.broadcast_to_agency_best_effort(
        agency_id=agency_id,
        payload={
            "type": "whatsapp.connection.status_changed",
            "agency_id": agency_id,
            "connection_id": connection.id,
            "status": "disconnected",
        },
    )
    return {
        "status": "disconnected",
        "connection": _serialize_connection(connection).model_dump(by_alias=True),
        "evolution": response,
    }


@router.post("/connections/{connection_id}/reapply-webhook")
def reapply_connection_webhook(
    connection_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    connection = domain_service.get_connection_or_404(db=db, agency_id=agency_id, connection_id=connection_id)
    try:
        result = evolution_service.reapply_instance_webhook_events(instance_name=connection.instance_name)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao reaplicar webhook da conexão: {exc}") from exc
    return {
        "status": "ok",
        "connectionId": connection.id,
        "instanceName": connection.instance_name,
        "result": result,
    }


@router.get("/conversations", response_model=list[WhatsAppConversationOut])
def list_conversations(
    agency_id: int = Query(..., alias="agencyId"),
    connection_id: int | None = Query(None, alias="connectionId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[WhatsAppConversationOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    granted_at = _resolve_inbox_granted_at(db, user_id=current_user.id, agency_id=agency_id)
    query = db.query(WhatsAppConversation).filter(WhatsAppConversation.agency_id == agency_id)
    if granted_at:
        query = query.filter(
            or_(
                WhatsAppConversation.last_message_at >= granted_at,
                WhatsAppConversation.created_at >= granted_at,
            )
        )
    if connection_id:
        query = query.filter(WhatsAppConversation.connection_id == connection_id)
    rows = query.order_by(WhatsAppConversation.last_message_at.desc(), WhatsAppConversation.updated_at.desc()).all()
    client_ids = [int(item.client_id) for item in rows if item.client_id]
    metrics_by_client: dict[int, tuple[int, int]] = {}
    if client_ids:
        metric_rows = (
            db.query(
                LeadFormSubmission.client_id,
                func.count(LeadFormSubmission.id),
                func.coalesce(func.sum(LeadFormSubmission.estimated_value_cents), 0),
            )
            .filter(
                LeadFormSubmission.agency_id == agency_id,
                LeadFormSubmission.client_id.in_(client_ids),
                LeadFormSubmission.closed_at.is_(None),
            )
            .group_by(LeadFormSubmission.client_id)
            .all()
        )
        metrics_by_client = {int(cid): (int(total or 0), int(value or 0)) for cid, total, value in metric_rows if cid}
    for item in rows:
        cid = int(item.client_id) if item.client_id else None
        total, value = metrics_by_client.get(cid, (0, 0)) if cid else (0, 0)
        setattr(item, "open_opportunities_count", total)
        setattr(item, "open_opportunities_value_cents", value)
    return [_serialize_conversation(item) for item in rows]


@router.get("/conversations/{conversation_id}/messages", response_model=list[WhatsAppMessageOut])
def list_conversation_messages(
    conversation_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[WhatsAppMessageOut]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    granted_at = _resolve_inbox_granted_at(db, user_id=current_user.id, agency_id=agency_id)
    conversation = (
        db.query(WhatsAppConversation)
        .filter(
            WhatsAppConversation.id == conversation_id,
            WhatsAppConversation.agency_id == agency_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    rows = (
        db.query(WhatsAppMessage)
        .filter(
            WhatsAppMessage.agency_id == agency_id,
            WhatsAppMessage.conversation_id == conversation_id,
        )
    )
    if granted_at:
        rows = rows.filter(WhatsAppMessage.created_at >= granted_at)
    rows = rows.order_by(WhatsAppMessage.created_at.asc()).all()
    return [_serialize_message(item) for item in rows]


@router.post("/conversations/{conversation_id}/mark-read")
def mark_conversation_read(
    conversation_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    conversation = (
        db.query(WhatsAppConversation)
        .filter(
            WhatsAppConversation.id == conversation_id,
            WhatsAppConversation.agency_id == agency_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    conversation.unread_count = 0
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    _emit_conversation_updated(conversation)
    _emit_unread_count(db, agency_id)
    return {"status": "ok", "conversation": _serialize_conversation(conversation).model_dump(by_alias=True)}


@router.patch("/conversations/{conversation_id}", response_model=WhatsAppConversationOut)
def update_conversation(
    conversation_id: int,
    payload: WhatsAppConversationUpdatePayload,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppConversationOut:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    conversation = (
        db.query(WhatsAppConversation)
        .filter(
            WhatsAppConversation.id == conversation_id,
            WhatsAppConversation.agency_id == agency_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    if payload.remote_name is not None:
        conversation.remote_name = payload.remote_name

    if payload.client_id is not None:
        client = (
            db.query(Client)
            .filter(
                Client.id == payload.client_id,
                Client.agency_id == agency_id,
                Client.deleted_at.is_(None),
            )
            .first()
        )
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado para esta agência.")
        conversation.client_id = client.id

    if payload.opportunity_id is not None:
        opportunity = (
            db.query(LeadFormSubmission)
            .filter(
                LeadFormSubmission.id == payload.opportunity_id,
                LeadFormSubmission.agency_id == agency_id,
            )
            .first()
        )
        if not opportunity:
            raise HTTPException(status_code=404, detail="Oportunidade não encontrada para esta agência.")
        if conversation.client_id and opportunity.client_id and opportunity.client_id != conversation.client_id:
            raise HTTPException(status_code=400, detail="Oportunidade não pertence ao cliente selecionado.")
        conversation.opportunity_id = opportunity.id

    if payload.opportunity_id is None and payload.client_id is not None and conversation.opportunity_id:
        existing_opp = (
            db.query(LeadFormSubmission)
            .filter(
                LeadFormSubmission.id == conversation.opportunity_id,
                LeadFormSubmission.agency_id == agency_id,
            )
            .first()
        )
        if existing_opp and existing_opp.client_id and existing_opp.client_id != conversation.client_id:
            conversation.opportunity_id = None
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    _emit_conversation_updated(conversation)
    return _serialize_conversation(conversation)


@router.post("/conversations/ensure", response_model=WhatsAppConversationOut)
def ensure_conversation(
    payload: EnsureConversationPayload,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppConversationOut:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)

    def _digits(raw: str | None) -> str:
        return "".join(ch for ch in (raw or "") if ch.isdigit())

    def _to_e164_br(raw: str | None) -> str | None:
        digits = _digits(raw)
        if not digits:
            return None
        if len(digits) in {10, 11}:
            return f"55{digits}"
        return digits

    def _equivalent_br(a: str | None, b: str | None) -> bool:
        da = _digits(a)
        db = _digits(b)
        if da.startswith("55") and len(da) > 11:
            da = da[2:]
        if db.startswith("55") and len(db) > 11:
            db = db[2:]
        if not da or not db:
            return False
        if da == db:
            return True
        if len(da) >= 10 and len(db) >= 10:
            ddd_a, local_a = da[:2], da[2:]
            ddd_b, local_b = db[:2], db[2:]
            if ddd_a == ddd_b:
                if local_a.startswith("9") and local_a[1:] == local_b:
                    return True
                if local_b.startswith("9") and local_b[1:] == local_a:
                    return True
        return False

    normalized_phone = None
    resolved_name = payload.remote_name

    if payload.client_id is not None:
        client = (
            db.query(Client)
            .filter(
                Client.id == payload.client_id,
                Client.agency_id == agency_id,
                Client.deleted_at.is_(None),
            )
            .first()
        )
        if not client:
            raise HTTPException(status_code=404, detail="Cliente nÃ£o encontrado para esta agÃªncia.")

        existing_for_client = (
            db.query(WhatsAppConversation)
            .filter(
                WhatsAppConversation.agency_id == agency_id,
                WhatsAppConversation.client_id == client.id,
            )
            .order_by(WhatsAppConversation.updated_at.desc())
            .first()
        )
        if existing_for_client:
            return _serialize_conversation(existing_for_client)

        normalized_phone = _to_e164_br(client.phone_normalized or client.phone)
        if not normalized_phone or len(normalized_phone) < 10:
            raise HTTPException(status_code=400, detail="Cliente selecionado nÃ£o possui telefone vÃ¡lido.")
        if not resolved_name:
            resolved_name = (client.name or "").strip() or None
    else:
        normalized_phone = _to_e164_br(payload.remote_phone)

    if not normalized_phone or len(normalized_phone) < 10:
        raise HTTPException(status_code=400, detail="Numero invalido.")

    existing_for_phone = None
    candidates = (
        db.query(WhatsAppConversation)
        .filter(WhatsAppConversation.agency_id == agency_id)
        .order_by(WhatsAppConversation.updated_at.desc())
        .all()
    )
    for row in candidates:
        if _equivalent_br(row.remote_phone, normalized_phone):
            existing_for_phone = row
            break
    if existing_for_phone:
        return _serialize_conversation(existing_for_phone)

    connection = (
        db.query(WhatsAppConnection)
        .filter(
            WhatsAppConnection.agency_id == agency_id,
            WhatsAppConnection.status == "connected",
        )
        .order_by(WhatsAppConnection.is_default.desc(), WhatsAppConnection.updated_at.desc())
        .first()
    )
    if not connection:
        raise HTTPException(status_code=400, detail="Nenhuma conexÃ£o WhatsApp conectada para iniciar conversa.")

    conversation = domain_service.get_or_create_conversation(
        db=db,
        agency_id=agency_id,
        connection=connection,
        remote_phone=normalized_phone,
        remote_name=resolved_name,
    )
    if payload.client_id and conversation.client_id is None:
        conversation.client_id = payload.client_id
        db.add(conversation)
    db.commit()
    db.refresh(conversation)
    _emit_conversation_updated(conversation)
    return _serialize_conversation(conversation)


@router.post("/conversations/{conversation_id}/send-text", response_model=WhatsAppMessageOut, status_code=201)
def send_text_message(
    conversation_id: int,
    payload: SendTextPayload,
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppMessageOut:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    conversation = (
        db.query(WhatsAppConversation)
        .filter(
            WhatsAppConversation.id == conversation_id,
            WhatsAppConversation.agency_id == agency_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    connection = domain_service.get_connection_or_404(
        db=db,
        agency_id=agency_id,
        connection_id=conversation.connection_id,
    )
    if not conversation.remote_phone:
        raise HTTPException(status_code=400, detail="Conversa sem destino remoto.")
    try:
        evolution_raw = evolution_service.send_text_target(
            target=conversation.remote_phone,
            text=payload.text,
            instance_name=connection.instance_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar via Evolution: {exc}") from exc
    message = domain_service.save_outbound_message(
        db=db,
        connection=connection,
        conversation=conversation,
        text=payload.text,
        evolution_response=evolution_raw,
    )
    db.commit()
    db.refresh(message)
    db.refresh(conversation)
    _emit_message_created(message)
    _emit_conversation_updated(conversation)
    return _serialize_message(message)


@router.post("/conversations/{conversation_id}/send-media", response_model=WhatsAppMessageOut, status_code=201)
async def send_media_message(
    conversation_id: int,
    agency_id: int = Query(..., alias="agencyId"),
    file: UploadFile = File(...),
    caption: str = Form(""),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WhatsAppMessageOut:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    conversation = (
        db.query(WhatsAppConversation)
        .filter(
            WhatsAppConversation.id == conversation_id,
            WhatsAppConversation.agency_id == agency_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    connection = domain_service.get_connection_or_404(
        db=db,
        agency_id=agency_id,
        connection_id=conversation.connection_id,
    )
    if not conversation.remote_phone:
        raise HTTPException(status_code=400, detail="Conversa sem destino remoto.")
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    if len(file_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo maior que 15MB.")
    mime_type = (file.content_type or "application/octet-stream").strip().lower()
    message_type = "document"
    if mime_type.startswith("image/"):
        message_type = "image"
    elif mime_type.startswith("video/"):
        message_type = "video"
    elif mime_type.startswith("audio/"):
        message_type = "audio"
    text_body = (caption or "").strip()
    if not text_body:
        fallback = {
            "image": "📷 Imagem",
            "video": "🎥 Vídeo",
            "audio": "🎵 Áudio",
            "document": "📄 Documento",
        }
        text_body = fallback.get(message_type, "📎 Arquivo")
    try:
        evolution_raw = evolution_service.send_media_target(
            target=conversation.remote_phone,
            file_bytes=file_bytes,
            file_name=file.filename or "arquivo",
            mime_type=mime_type,
            media_type=message_type,
            caption=caption,
            ptt=message_type == "audio",
            instance_name=connection.instance_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar mídia via Evolution: {exc}") from exc
    message = domain_service.save_outbound_message(
        db=db,
        connection=connection,
        conversation=conversation,
        text=text_body,
        evolution_response=evolution_raw,
        message_type=message_type,
        media_url=f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('ascii')}",
        media_mime_type=mime_type,
        media_file_name=file.filename,
        media_size=len(file_bytes),
    )
    db.commit()
    db.refresh(message)
    db.refresh(conversation)
    _emit_message_created(message)
    _emit_conversation_updated(conversation)
    return _serialize_message(message)


@router.get("/unread-count")
def get_unread_count(
    agency_id: int = Query(..., alias="agencyId"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    granted_at = _resolve_inbox_granted_at(db, user_id=current_user.id, agency_id=agency_id)
    unread_query = db.query(func.coalesce(func.sum(WhatsAppConversation.unread_count), 0)).filter(
        WhatsAppConversation.agency_id == agency_id
    )
    if granted_at:
        unread_query = unread_query.filter(
            or_(
                WhatsAppConversation.last_message_at >= granted_at,
                WhatsAppConversation.created_at >= granted_at,
            )
        )
    total = unread_query.scalar() or 0
    return {"total_unread": int(total)}


@router.get("/test-instance/status")
def get_test_instance_status(current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    try:
        status_data = evolution_service.get_connection_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao buscar status da conexão: {exc}") from exc
    return {
        "instance": evolution_service.test_instance_name,
        "status": status_data["status"],
        "raw_state": status_data.get("raw_state"),
        "raw": status_data.get("raw"),
        "requested_by_user_id": current_user.id,
    }


@router.post("/test-send")
def test_send_message(
    payload: TestSendPayload,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    try:
        response = evolution_service.send_text(number=payload.number, text=payload.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar mensagem de teste: {exc}") from exc
    return {
        "status": "sent",
        "instance": evolution_service.test_instance_name,
        "number": payload.number,
        "data": response,
        "requested_by_user_id": current_user.id,
    }
