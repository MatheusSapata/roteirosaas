from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.whatsapp import WhatsAppConnection, WhatsAppConversation
from app.schemas.whatsapp import WebhookAckOut
from app.services.whatsapp_domain import WhatsAppDomainService
from app.services.evolution import EvolutionService
from app.services.whatsapp_realtime import whatsapp_realtime
from app.api.v1.endpoints.whatsapp import _serialize_conversation, _serialize_message

router = APIRouter()
logger = logging.getLogger(__name__)
domain_service = WhatsAppDomainService()
evolution_service = EvolutionService()


def _should_log_ignored_event(event_name: str | None) -> bool:
    normalized = (event_name or "").strip().lower()
    if not normalized:
        return True
    # qrcode updates are very frequent and noisy in logs.
    if normalized in {"qrcode.updated", "qrcode.update", "qrcode-updated"}:
        return False
    noisy_prefixes = (
        "presence.",
        "presence-",
        "chats.",
        "chats-",
    )
    return not normalized.startswith(noisy_prefixes)


def _process_evolution_webhook(
    payload: dict[str, Any],
    *,
    db: Session,
    event_hint: str | None = None,
) -> WebhookAckOut:
    if event_hint and not payload.get("event"):
        payload = {**payload, "event": event_hint}

    def _build_candidates(source_payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw_data = source_payload.get("data")
        items: list[dict[str, Any]] = []

        # Formato A: data=[{...},{...}]
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    items.append({**source_payload, "data": item})

        # Formato B: data={ messages:[{...}], ... } (comum em messages-set na v2.3.x)
        elif isinstance(raw_data, dict):
            nested_messages = raw_data.get("messages")
            if isinstance(nested_messages, list):
                for item in nested_messages:
                    if isinstance(item, dict):
                        merged_data = {**raw_data, **item}
                        items.append({**source_payload, "data": merged_data})
            # Formato C: payload único tradicional
            items.append(source_payload)

        # Formato D: payload sem data estruturado
        else:
            items.append(source_payload)

        return items

    candidates = _build_candidates(payload)

    parsed_batch = []
    for candidate in candidates:
        parsed = domain_service.parse_inbound_webhook(candidate)
        if parsed:
            parsed_batch.append((candidate, parsed))

    if not parsed_batch:
        ignored_event = payload.get("event") or payload.get("type") or payload.get("eventName")
        if _should_log_ignored_event(ignored_event if isinstance(ignored_event, str) else None):
            logger.info(
                "Evolution webhook ignored event=%s candidates=%s payload=%s",
                ignored_event,
                len(candidates),
                domain_service.compact_payload(payload),
            )
        return WebhookAckOut(accepted=True, reason="ignored_event_or_payload")

    processed_any = False
    last_connection: WhatsAppConnection | None = None
    for candidate_payload, message_data in parsed_batch:
        connection = (
            db.query(WhatsAppConnection)
            .filter(WhatsAppConnection.instance_name == message_data.instance_name)
            .first()
        )
        if not connection:
            logger.warning("Evolution webhook instance not found: %s", message_data.instance_name)
            continue

        if not message_data.avatar_url:
            try:
                resolved_avatar = evolution_service.fetch_profile_picture_url(
                    instance_name=connection.instance_name,
                    remote=message_data.remote_phone,
                )
                if resolved_avatar:
                    message_data.avatar_url = resolved_avatar
            except Exception:
                # best effort: avatar não pode bloquear persistência da mensagem
                pass

        if (
            message_data.message_type in {"video", "audio", "image", "document", "view_once_video", "view_once_image"}
            and isinstance(message_data.media_url, str)
            and message_data.media_url.startswith("http")
        ):
            media_payload = (
                candidate_payload.get("data") if isinstance(candidate_payload.get("data"), dict) else candidate_payload
            )
            if isinstance(media_payload, dict):
                resolved_b64 = evolution_service.get_media_base64_from_message(
                    instance_name=connection.instance_name,
                    message_payload=media_payload,
                    convert_to_mp4=message_data.message_type in {"video", "view_once_video"},
                )
                if resolved_b64:
                    mime = message_data.media_mime_type or (
                        "video/mp4" if "video" in message_data.message_type else "application/octet-stream"
                    )
                    if resolved_b64.startswith("data:"):
                        message_data.media_url = resolved_b64
                    else:
                        message_data.media_url = f"data:{mime};base64,{resolved_b64}"

        conversation = domain_service.get_or_create_conversation(
            db=db,
            agency_id=connection.agency_id,
            connection=connection,
            remote_phone=message_data.remote_phone,
            remote_name=message_data.remote_name,
            avatar_url=message_data.avatar_url,
        )
        if message_data.remote_phone.lower().endswith("@g.us") and not conversation.remote_name:
            try:
                group_data = evolution_service.find_group_info(
                    instance_name=connection.instance_name,
                    group_jid=message_data.remote_phone,
                )
                subject = (
                    (group_data.get("subject") if isinstance(group_data, dict) else None)
                    or (group_data.get("name") if isinstance(group_data, dict) else None)
                )
                if isinstance(subject, str) and subject.strip():
                    conversation.remote_name = subject.strip()
                    db.add(conversation)
                    db.flush()
            except Exception:
                pass

        if message_data.direction == "outbound":
            message = domain_service.save_outbound_webhook_message(
                db=db,
                connection=connection,
                conversation=conversation,
                payload=message_data,
            )
        else:
            message = domain_service.save_inbound_message(
                db=db,
                connection=connection,
                conversation=conversation,
                payload=message_data,
            )
        db.commit()
        db.refresh(conversation)
        db.refresh(message)
        processed_any = True
        last_connection = connection

        whatsapp_realtime.broadcast_to_agency_best_effort(
            agency_id=connection.agency_id,
            payload={
                "type": "whatsapp.message.created",
                "agency_id": connection.agency_id,
                "conversation_id": conversation.id,
                "message": _serialize_message(message).model_dump(by_alias=True, mode="json"),
            },
        )
        whatsapp_realtime.broadcast_to_agency_best_effort(
            agency_id=connection.agency_id,
            payload={
                "type": "whatsapp.conversation.updated",
                "agency_id": connection.agency_id,
                "conversation": _serialize_conversation(conversation).model_dump(by_alias=True, mode="json"),
            },
        )

    if not processed_any or not last_connection:
        return WebhookAckOut(accepted=True, reason="ignored_event_or_payload")

    total_unread = (
        db.query(func.coalesce(func.sum(WhatsAppConversation.unread_count), 0))
        .filter(WhatsAppConversation.agency_id == last_connection.agency_id)
        .scalar()
        or 0
    )
    whatsapp_realtime.broadcast_to_agency_best_effort(
        agency_id=last_connection.agency_id,
        payload={
            "type": "whatsapp.unread_count.updated",
            "agency_id": last_connection.agency_id,
            "total_unread": int(total_unread),
        },
    )
    return WebhookAckOut(accepted=True, reason="processed")


@router.post("/evolution", response_model=WebhookAckOut)
def evolution_webhook(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> WebhookAckOut:
    return _process_evolution_webhook(payload, db=db)


@router.post("/evolution/{event_name}", response_model=WebhookAckOut)
def evolution_webhook_by_event(
    event_name: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> WebhookAckOut:
    # Evolution v2.3.6 pode enviar callbacks em /evolution/<event-slug>.
    # Ex.: /evolution/messages-upsert, /evolution/connection-update, /evolution/qrcode-updated
    event_hint = event_name.replace("-", ".")
    return _process_evolution_webhook(payload, db=db, event_hint=event_hint)
