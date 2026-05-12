from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.lead_form import LeadFormSubmission
from app.models.whatsapp import WhatsAppConnection, WhatsAppConversation, WhatsAppMessage
from app.services.contact_normalization import normalize_phone
from app.services.evolution import EvolutionService


@dataclass
class WebhookMessageData:
    instance_name: str
    remote_phone: str
    remote_name: str | None
    avatar_url: str | None
    direction: str
    body: str
    message_type: str
    external_message_id: str | None
    status: str | None
    received_at: datetime
    media_url: str | None = None
    media_mime_type: str | None = None
    media_file_name: str | None = None
    media_size: int | None = None
    media_duration: int | None = None


class WhatsAppDomainService:
    def __init__(self) -> None:
        self.evolution = EvolutionService()

    def create_connection(
        self,
        *,
        db: Session,
        agency_id: int,
        name: str,
        created_by_user_id: int | None,
    ) -> WhatsAppConnection:
        existing_active = (
            db.query(WhatsAppConnection)
            .filter(
                WhatsAppConnection.agency_id == agency_id,
                WhatsAppConnection.status.in_(["connected", "connecting", "qr_needed"]),
            )
            .first()
        )
        if existing_active:
            raise HTTPException(
                status_code=409,
                detail="A agência já possui uma conexão ativa no MVP.",
            )

        instance_name = self._build_instance_name(agency_id=agency_id, name=name)
        evolution_result = self.evolution.create_instance(instance_name=instance_name)

        connection = WhatsAppConnection(
            agency_id=agency_id,
            name=name.strip(),
            instance_name=instance_name,
            phone_number=None,
            status="connecting",
            is_default=True,
            created_by_user_id=created_by_user_id,
            connected_at=None,
            disconnected_at=None,
        )
        db.add(connection)
        db.flush()

        # Se a Evolution retornar hash/token, guardamos como phone_number temporário? Não.
        # Apenas persistimos status da criação.
        if isinstance(evolution_result, dict):
            status = (
                (evolution_result.get("instance") or {}).get("status")
                if isinstance(evolution_result.get("instance"), dict)
                else None
            )
            if isinstance(status, str):
                connection.status = self._normalize_connection_status(status)
        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection

    def get_connection_or_404(self, *, db: Session, agency_id: int, connection_id: int) -> WhatsAppConnection:
        connection = (
            db.query(WhatsAppConnection)
            .filter(
                WhatsAppConnection.id == connection_id,
                WhatsAppConnection.agency_id == agency_id,
            )
            .first()
        )
        if not connection:
            raise HTTPException(status_code=404, detail="Conexão WhatsApp não encontrada.")
        return connection

    def update_connection_status_from_evolution(
        self, *, db: Session, connection: WhatsAppConnection
    ) -> tuple[str, str | None, dict[str, Any]]:
        status_data = self.evolution.get_connection_status(instance_name=connection.instance_name)
        mapped = status_data.get("status") or "disconnected"
        raw_state = status_data.get("raw_state")
        raw = status_data.get("raw") or {}
        phone = status_data.get("phone")

        connection.status = self._normalize_connection_status(mapped)
        if isinstance(phone, str) and phone.strip():
            connection.phone_number = phone.strip()
        now = datetime.now(timezone.utc)
        if connection.status == "connected":
            connection.connected_at = connection.connected_at or now
            connection.disconnected_at = None
        elif connection.status == "disconnected":
            connection.disconnected_at = now
        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection.status, raw_state, raw

    def get_or_create_conversation(
        self,
        *,
        db: Session,
        agency_id: int,
        connection: WhatsAppConnection,
        remote_phone: str,
        remote_name: str | None,
        avatar_url: str | None = None,
    ) -> WhatsAppConversation:
        normalized_remote = normalize_phone(remote_phone) or remote_phone
        candidates = self._phone_match_candidates(normalized_remote)
        if remote_phone not in candidates:
            candidates.append(remote_phone)

        phone_filter = (
            or_(*[WhatsAppConversation.remote_phone == value for value in candidates])
            if candidates
            else (WhatsAppConversation.remote_phone == remote_phone)
        )

        conversation = (
            db.query(WhatsAppConversation)
            .filter(
                WhatsAppConversation.agency_id == agency_id,
                WhatsAppConversation.connection_id == connection.id,
                phone_filter,
            )
            .order_by(WhatsAppConversation.updated_at.desc())
            .first()
        )
        if conversation:
            if remote_name:
                conversation.remote_name = remote_name
            if avatar_url:
                conversation.avatar_url = avatar_url
            db.add(conversation)
            db.flush()
            return conversation

        client = None
        if not self._is_group_jid(remote_phone):
            client = self.find_client_by_phone(db=db, agency_id=agency_id, remote_phone=remote_phone)
        opportunity_id = self.find_latest_opportunity_id(db=db, agency_id=agency_id, client_id=client.id if client else None)
        conversation = WhatsAppConversation(
            agency_id=agency_id,
            connection_id=connection.id,
            client_id=client.id if client else None,
            opportunity_id=opportunity_id,
            remote_phone=remote_phone,
            remote_name=remote_name,
            avatar_url=avatar_url,
            unread_count=0,
        )
        db.add(conversation)
        db.flush()
        return conversation

    def save_inbound_message(
        self,
        *,
        db: Session,
        connection: WhatsAppConnection,
        conversation: WhatsAppConversation,
        payload: WebhookMessageData,
    ) -> WhatsAppMessage:
        if payload.external_message_id:
            existing = (
                db.query(WhatsAppMessage)
                .filter(WhatsAppMessage.external_message_id == payload.external_message_id)
                .first()
            )
            if existing:
                return existing

        message = WhatsAppMessage(
            agency_id=connection.agency_id,
            connection_id=connection.id,
            conversation_id=conversation.id,
            external_message_id=payload.external_message_id,
            direction="inbound",
            message_type=payload.message_type or "text",
            body=payload.body,
            status=payload.status,
            remote_phone=payload.remote_phone,
            media_url=payload.media_url,
            media_mime_type=payload.media_mime_type,
            media_file_name=payload.media_file_name,
            media_size=payload.media_size,
            media_duration=payload.media_duration,
            received_at=payload.received_at,
        )
        db.add(message)
        db.flush()

        conversation.last_message_text = payload.body
        conversation.last_message_at = payload.received_at
        conversation.unread_count = int(conversation.unread_count or 0) + 1
        if payload.remote_name:
            conversation.remote_name = payload.remote_name
        if payload.avatar_url:
            conversation.avatar_url = payload.avatar_url
        # Backfill de vinculo: se a conversa nasceu sem cliente/oportunidade,
        # tentamos vincular novamente a cada inbound com base no telefone normalizado.
        if conversation.client_id is None and not self._is_group_jid(payload.remote_phone):
            matched_client = self.find_client_by_phone(
                db=db,
                agency_id=connection.agency_id,
                remote_phone=payload.remote_phone,
            )
            if matched_client:
                conversation.client_id = matched_client.id
                if conversation.opportunity_id is None:
                    conversation.opportunity_id = self.find_latest_opportunity_id(
                        db=db,
                        agency_id=connection.agency_id,
                        client_id=matched_client.id,
                    )
        db.add(conversation)
        return message

    def save_outbound_webhook_message(
        self,
        *,
        db: Session,
        connection: WhatsAppConnection,
        conversation: WhatsAppConversation,
        payload: WebhookMessageData,
    ) -> WhatsAppMessage:
        if payload.external_message_id:
            existing = (
                db.query(WhatsAppMessage)
                .filter(WhatsAppMessage.external_message_id == payload.external_message_id)
                .first()
            )
            if existing:
                return existing

        message = WhatsAppMessage(
            agency_id=connection.agency_id,
            connection_id=connection.id,
            conversation_id=conversation.id,
            external_message_id=payload.external_message_id,
            direction="outbound",
            message_type=payload.message_type or "text",
            body=payload.body,
            status=payload.status,
            remote_phone=payload.remote_phone,
            media_url=payload.media_url,
            media_mime_type=payload.media_mime_type,
            media_file_name=payload.media_file_name,
            media_size=payload.media_size,
            media_duration=payload.media_duration,
            sent_at=payload.received_at,
        )
        db.add(message)
        db.flush()

        conversation.last_message_text = payload.body
        conversation.last_message_at = payload.received_at
        if payload.avatar_url:
            conversation.avatar_url = payload.avatar_url
        db.add(conversation)
        return message

    def save_outbound_message(
        self,
        *,
        db: Session,
        connection: WhatsAppConnection,
        conversation: WhatsAppConversation,
        text: str,
        evolution_response: dict[str, Any],
        message_type: str | None = None,
        media_url: str | None = None,
        media_mime_type: str | None = None,
        media_file_name: str | None = None,
        media_size: int | None = None,
        media_duration: int | None = None,
    ) -> WhatsAppMessage:
        external_message_id = self._extract_outbound_external_id(evolution_response)
        if external_message_id:
            existing = (
                db.query(WhatsAppMessage)
                .filter(WhatsAppMessage.external_message_id == external_message_id)
                .first()
            )
            if existing:
                return existing

        remote_phone = conversation.remote_phone
        now = datetime.now(timezone.utc)
        message = WhatsAppMessage(
            agency_id=connection.agency_id,
            connection_id=connection.id,
            conversation_id=conversation.id,
            external_message_id=external_message_id,
            direction="outbound",
            message_type=str(message_type or evolution_response.get("messageType") or "text"),
            body=text,
            status=str(evolution_response.get("status")) if evolution_response.get("status") else None,
            remote_phone=remote_phone,
            media_url=media_url,
            media_mime_type=media_mime_type,
            media_file_name=media_file_name,
            media_size=media_size,
            media_duration=media_duration,
            sent_at=now,
        )
        db.add(message)
        db.flush()

        conversation.last_message_text = text
        conversation.last_message_at = now
        db.add(conversation)
        return message

    def find_client_by_phone(self, *, db: Session, agency_id: int, remote_phone: str) -> Client | None:
        normalized = normalize_phone(remote_phone)
        if not normalized:
            return None
        candidates = self._phone_match_candidates(normalized)
        return (
            db.query(Client)
            .filter(
                Client.agency_id == agency_id,
                Client.deleted_at.is_(None),
                or_(*[Client.phone_normalized == value for value in candidates]),
            )
            .first()
        )

    def find_latest_opportunity_id(self, *, db: Session, agency_id: int, client_id: int | None) -> int | None:
        if not client_id:
            return None
        row = (
            db.query(LeadFormSubmission.id)
            .filter(
                LeadFormSubmission.agency_id == agency_id,
                LeadFormSubmission.client_id == client_id,
            )
            .order_by(desc(LeadFormSubmission.created_at))
            .first()
        )
        return int(row[0]) if row else None

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> WebhookMessageData | None:
        event = self._extract_event_name(payload)
        if event and not self._is_supported_inbound_event(event):
            return None
        instance_name = self._extract_instance_name(payload)
        if not instance_name:
            return None
        remote_jid = self._extract_remote_jid(payload)
        is_from_me = self._is_from_me(payload)
        is_group = self._is_group_jid(remote_jid)
        if is_group:
            remote_phone = (remote_jid or "").strip().lower()
        else:
            remote_phone = self._phone_from_jid(remote_jid) or self._extract_digits(payload, {"phone", "number"})
        if not remote_phone:
            return None
        body = self._extract_message_body(payload)
        external_message_id = self._extract_message_id(payload)
        msg_type = self._extract_message_type(payload)
        media = self._extract_media(payload, msg_type=msg_type)
        if not body:
            body, msg_type = self._build_non_text_fallback(payload, msg_type)
            if not body:
                # Em alguns eventos da Evolution (v2.3.x), mensagens inbound podem vir
                # encapsuladas em secretEncryptedMessage sem conteúdo textual decodificado.
                # Nesses casos, mantemos o registro e a notificação com fallback genérico.
                has_encrypted_payload = bool(self._dig(payload, "data", "message", "secretEncryptedMessage"))
                has_reaction_payload = bool(self._dig(payload, "data", "message", "reactionMessage"))
                normalized_status = (self._extract_status(payload) or "").strip().lower()
                is_receipt_only = normalized_status in {"delivery_ack", "read", "played", "server_ack"}
                if has_reaction_payload:
                    return None
                if has_encrypted_payload and not is_from_me:
                    body = "Nova mensagem"
                    msg_type = "encrypted"
                elif is_receipt_only:
                    return None
            if not body:
                return None
        remote_name = self._extract_group_name(payload) if is_group else self._extract_remote_name(payload)
        avatar_url = self._extract_avatar_url(payload)
        if is_group:
            sender_name = self._extract_remote_name(payload)
            if sender_name and not body.startswith("["):
                body = f"[{sender_name}] {body}"
        elif is_from_me:
            # Evita sobrescrever o contato com o nome do próprio operador.
            remote_name = None
        status = self._extract_status(payload)
        received_at = datetime.now(timezone.utc)
        return WebhookMessageData(
            instance_name=instance_name,
            remote_phone=remote_phone,
            remote_name=remote_name,
            avatar_url=avatar_url,
            direction="outbound" if is_from_me else "inbound",
            body=body,
            message_type=msg_type,
            external_message_id=external_message_id,
            status=status,
            received_at=received_at,
            media_url=media.get("url"),
            media_mime_type=media.get("mime_type"),
            media_file_name=media.get("file_name"),
            media_size=media.get("size"),
            media_duration=media.get("duration"),
        )

    def _build_instance_name(self, *, agency_id: int, name: str) -> str:
        seed = f"{agency_id}:{name.strip().lower()}:{datetime.now(timezone.utc).isoformat()}"
        suffix = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
        return f"wa-ag{agency_id}-{suffix}"

    def _normalize_connection_status(self, value: str) -> str:
        state = (value or "").strip().lower()
        if state in {"open", "connected"}:
            return "connected"
        if state in {"connecting", "pairing"}:
            return "connecting"
        if state in {"qrcode", "qr", "qr_needed"}:
            return "qr_needed"
        return "disconnected"

    def _extract_event_name(self, payload: dict[str, Any]) -> str | None:
        for key in ("event", "type", "eventName"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _is_supported_inbound_event(self, event: str) -> bool:
        normalized = event.lower()
        if "messages.upsert" in normalized:
            return True
        if "message.upsert" in normalized:
            return True
        if "messages.set" in normalized:
            return True
        if "messages.update" in normalized:
            return True
        if "messages-set" in normalized or "messages_set" in normalized:
            return True
        if "messages-update" in normalized or "messages_update" in normalized:
            return True
        if "message" in normalized and "create" in normalized:
            return True
        return normalized in {"messages-upsert", "messages_upsert"}

    def _extract_instance_name(self, payload: dict[str, Any]) -> str | None:
        direct_keys = ("instance", "instanceName", "instance_name")
        for key in direct_keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested = value.get("instanceName") or value.get("name")
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("instanceName", "instance", "instance_name"):
                nested = data.get(key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
                if isinstance(nested, dict):
                    inner = nested.get("instanceName") or nested.get("name")
                    if isinstance(inner, str) and inner.strip():
                        return inner.strip()
        return None

    def _extract_remote_jid(self, payload: dict[str, Any]) -> str | None:
        paths = [
            ("data", "key", "remoteJid"),
            ("data", "key", "remoteJidAlt"),
            ("key", "remoteJid"),
            ("key", "remoteJidAlt"),
            ("data", "remoteJidAlt"),
            ("data", "remoteJid"),
            ("remoteJidAlt",),
            ("remoteJid",),
            ("data", "key", "participantAlt"),
            ("key", "participantAlt"),
            ("data", "sender"),
            ("sender",),
        ]
        for path in paths:
            value = self._dig(payload, *path)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_message_id(self, payload: dict[str, Any]) -> str | None:
        paths = [("data", "key", "id"), ("key", "id"), ("data", "id"), ("id",)]
        for path in paths:
            value = self._dig(payload, *path)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_message_type(self, payload: dict[str, Any]) -> str:
        value = self._dig(payload, "data", "messageType") or self._dig(payload, "messageType")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
        # Fallback para payloads que não trazem messageType explícito.
        if self._dig(payload, "data", "message", "viewOnceMessage"):
            return "view_once"
        if self._dig(payload, "data", "message", "imageMessage"):
            return "image"
        if self._dig(payload, "data", "message", "videoMessage"):
            return "video"
        if self._dig(payload, "data", "message", "audioMessage"):
            return "audio"
        if self._dig(payload, "data", "message", "documentMessage"):
            return "document"
        return "text"

    def _extract_message_body(self, payload: dict[str, Any]) -> str | None:
        candidates = [
            self._dig(payload, "data", "message", "conversation"),
            self._dig(payload, "data", "message", "extendedTextMessage", "text"),
            self._dig(payload, "data", "message", "imageMessage", "caption"),
            self._dig(payload, "data", "body"),
            self._dig(payload, "body"),
            self._dig(payload, "message", "conversation"),
        ]
        for item in candidates:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    return cleaned
        return None

    def _build_non_text_fallback(self, payload: dict[str, Any], msg_type: str) -> tuple[str | None, str]:
        normalized = (msg_type or "").strip().lower()

        # View once costuma vir encapsulada e sem texto/caption.
        view_once = self._dig(payload, "data", "message", "viewOnceMessage")
        if isinstance(view_once, dict):
            inner = view_once.get("message")
            if isinstance(inner, dict):
                if inner.get("imageMessage") is not None:
                    return "📷 Foto de visualização única", "view_once_image"
                if inner.get("videoMessage") is not None:
                    return "🎥 Vídeo de visualização única", "view_once_video"
            return "📩 Mensagem de visualização única", "view_once"

        if normalized in {"image", "imagem", "imagemessage"} or self._dig(payload, "data", "message", "imageMessage"):
            return "📷 Imagem", "image"
        if normalized in {"video", "videomessage"} or self._dig(payload, "data", "message", "videoMessage"):
            return "🎥 Vídeo", "video"
        if normalized in {"audio", "audiomessage"} or self._dig(payload, "data", "message", "audioMessage"):
            return "🎵 Áudio", "audio"
        if normalized in {"document", "documentmessage"} or self._dig(payload, "data", "message", "documentMessage"):
            return "📄 Documento", "document"
        if normalized in {"sticker", "stickermessage"} or self._dig(payload, "data", "message", "stickerMessage"):
            return "🖼️ Sticker", "sticker"

        return None, msg_type

    def _extract_media(self, payload: dict[str, Any], *, msg_type: str) -> dict[str, Any]:
        root_message = self._dig(payload, "data", "message")
        if not isinstance(root_message, dict):
            return {"url": None, "mime_type": None, "file_name": None, "size": None, "duration": None}
        candidates: list[dict[str, Any]] = []
        direct_key_map = {
            "image": "imageMessage",
            "video": "videoMessage",
            "audio": "audioMessage",
            "document": "documentMessage",
            "view_once_image": "imageMessage",
            "view_once_video": "videoMessage",
        }
        direct_key = direct_key_map.get((msg_type or "").lower())
        if direct_key and isinstance(root_message.get(direct_key), dict):
            candidates.append(root_message[direct_key])
        view_once = root_message.get("viewOnceMessage")
        if isinstance(view_once, dict) and isinstance(view_once.get("message"), dict):
            inner = view_once["message"]
            for key in ("imageMessage", "videoMessage", "audioMessage", "documentMessage"):
                if isinstance(inner.get(key), dict):
                    candidates.append(inner[key])
        for candidate in candidates:
            url = candidate.get("url") or candidate.get("directPath") or candidate.get("mediaUrl")
            if isinstance(url, str) and url.strip() and url.strip().startswith(("http://", "https://", "data:")):
                media_url = url.strip()
            else:
                media_url = None
            mime_type = candidate.get("mimetype") or candidate.get("mimeType")
            file_name = candidate.get("fileName")
            size = candidate.get("fileLength") or candidate.get("size")
            duration = candidate.get("seconds") or candidate.get("duration")
            if not media_url:
                maybe_b64 = candidate.get("base64")
                if isinstance(maybe_b64, str) and maybe_b64.strip():
                    normalized_b64 = maybe_b64.strip()
                    if not normalized_b64.startswith("data:"):
                        mt = mime_type if isinstance(mime_type, str) and mime_type else "application/octet-stream"
                        media_url = f"data:{mt};base64,{normalized_b64}"
            size_int = int(size) if isinstance(size, (int, float)) else None
            duration_int = int(duration) if isinstance(duration, (int, float)) else None
            return {
                "url": media_url,
                "mime_type": mime_type if isinstance(mime_type, str) else None,
                "file_name": file_name if isinstance(file_name, str) else None,
                "size": size_int,
                "duration": duration_int,
            }
        # Fallback amplo: algumas versões/eventos da Evolution trazem mídia fora do bloco padrão.
        fallback_url = self._find_first_media_url(payload)
        fallback_b64 = self._find_first_base64(payload)
        fallback_mime = self._find_first_text(payload, {"mimetype", "mimeType"})
        fallback_name = self._find_first_text(payload, {"fileName", "filename", "title"})
        fallback_size = self._find_first_number(payload, {"fileLength", "size"})
        fallback_duration = self._find_first_number(payload, {"seconds", "duration"})
        if fallback_b64 and not fallback_url:
            mt = fallback_mime or "application/octet-stream"
            fallback_url = f"data:{mt};base64,{fallback_b64}"
        return {
            "url": fallback_url,
            "mime_type": fallback_mime,
            "file_name": fallback_name,
            "size": int(fallback_size) if isinstance(fallback_size, (int, float)) else None,
            "duration": int(fallback_duration) if isinstance(fallback_duration, (int, float)) else None,
        }

    def _find_first_media_url(self, obj: Any) -> str | None:
        keys = {"url", "mediaUrl", "directPath"}
        stack = [obj]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key in keys and isinstance(value, str):
                        cleaned = value.strip()
                        if cleaned.startswith(("http://", "https://", "data:")):
                            return cleaned
                    stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)
        return None

    def _find_first_base64(self, obj: Any) -> str | None:
        keys = {"base64", "mediaBase64", "fileBase64"}
        stack = [obj]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key in keys and isinstance(value, str):
                        cleaned = value.strip()
                        if cleaned and len(cleaned) > 32:
                            return cleaned
                    stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)
        return None

    def _find_first_text(self, obj: Any, keys: set[str]) -> str | None:
        stack = [obj]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key in keys and isinstance(value, str) and value.strip():
                        return value.strip()
                    stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)
        return None

    def _find_first_number(self, obj: Any, keys: set[str]) -> float | None:
        stack = [obj]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if key in keys and isinstance(value, (int, float)):
                        return float(value)
                    stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)
        return None

    def _extract_remote_name(self, payload: dict[str, Any]) -> str | None:
        for path in [("data", "pushName"), ("pushName",), ("data", "senderName"), ("senderName",)]:
            value = self._dig(payload, *path)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_group_name(self, payload: dict[str, Any]) -> str | None:
        for path in [
            ("data", "chatName"),
            ("chatName",),
            ("data", "groupName"),
            ("groupName",),
            ("data", "chat", "name"),
            ("chat", "name"),
            ("data", "chat", "subject"),
            ("chat", "subject"),
            ("data", "group", "subject"),
            ("group", "subject"),
            ("data", "conversationName"),
            ("conversationName",),
        ]:
            value = self._dig(payload, *path)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_avatar_url(self, payload: dict[str, Any]) -> str | None:
        for path in [
            ("data", "profilePicUrl"),
            ("profilePicUrl",),
            ("data", "profilePictureUrl"),
            ("profilePictureUrl",),
            ("data", "picture"),
            ("picture",),
            ("data", "contact", "imgUrl"),
            ("contact", "imgUrl"),
        ]:
            value = self._dig(payload, *path)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned.startswith("http://") or cleaned.startswith("https://"):
                    return cleaned
        return None

    def _extract_status(self, payload: dict[str, Any]) -> str | None:
        value = self._dig(payload, "data", "status") or self._dig(payload, "status")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
        return None

    def _extract_outbound_external_id(self, payload: dict[str, Any]) -> str | None:
        value = self._dig(payload, "key", "id") or self._dig(payload, "id")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _phone_from_jid(self, jid: str | None) -> str | None:
        if not jid:
            return None
        normalized = jid.strip().lower()
        # IDs @lid não representam o telefone real para reply em algumas versões do baileys/evolution.
        if normalized.endswith("@lid"):
            return None
        left = jid.split("@")[0]
        digits = "".join(ch for ch in left if ch.isdigit())
        return digits or None

    def _extract_digits(self, payload: dict[str, Any], keys: set[str]) -> str | None:
        expanded_keys = set(keys) | {
            "remoteJidAlt",
            "participantAlt",
            "remoteJid",
            "participant",
        }

        def visit(value: Any) -> str | None:
            if isinstance(value, dict):
                for k, v in value.items():
                    if k in expanded_keys and isinstance(v, str):
                        candidate = v.strip()
                        if candidate.lower().endswith("@lid"):
                            continue
                        digits = "".join(ch for ch in candidate if ch.isdigit())
                        if digits:
                            return digits
                    nested = visit(v)
                    if nested:
                        return nested
            elif isinstance(value, list):
                for item in value:
                    nested = visit(item)
                    if nested:
                        return nested
            return None

        return visit(payload)

    def _is_group_message(self, payload: dict[str, Any]) -> bool:
        # Grupos no WhatsApp usam JID com sufixo @g.us.
        group_paths = [
            ("data", "key", "remoteJid"),
            ("key", "remoteJid"),
            ("data", "remoteJid"),
            ("remoteJid",),
        ]
        for path in group_paths:
            value = self._dig(payload, *path)
            if isinstance(value, str) and self._is_group_jid(value):
                return True
        return False

    def _is_group_jid(self, value: str | None) -> bool:
        return bool(isinstance(value, str) and value.strip().lower().endswith("@g.us"))

    def _is_from_me(self, payload: dict[str, Any]) -> bool:
        for path in [("data", "key", "fromMe"), ("key", "fromMe"), ("data", "fromMe"), ("fromMe",)]:
            value = self._dig(payload, *path)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "1", "yes"}:
                    return True
                if lowered in {"false", "0", "no"}:
                    return False
        return False

    def _dig(self, source: dict[str, Any], *path: str) -> Any:
        current: Any = source
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _phone_match_candidates(self, normalized: str) -> list[str]:
        digits = "".join(ch for ch in normalized if ch.isdigit())
        if not digits:
            return []

        values: set[str] = {digits}

        national = digits[2:] if digits.startswith("55") and len(digits) > 2 else digits
        values.add(national)
        values.add(f"55{national}")

        if len(national) >= 10:
            ddd = national[:2]
            local = national[2:]
            values.add(f"{ddd}{local}")
            values.add(f"55{ddd}{local}")

            # Variação com/sem nono dígito após DDD.
            if len(local) >= 1 and local.startswith("9"):
                without_nine = local[1:]
                if without_nine:
                    values.add(f"{ddd}{without_nine}")
                    values.add(f"55{ddd}{without_nine}")

            with_nine = f"9{local}"
            values.add(f"{ddd}{with_nine}")
            values.add(f"55{ddd}{with_nine}")

        return [v for v in values if v]

    def compact_payload(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False)[:2000]
