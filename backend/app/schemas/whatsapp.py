from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WhatsAppConnectionCreate(BaseModel):
    agency_id: int = Field(..., alias="agencyId")
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Nome da conexão obrigatório.")
        return cleaned

    model_config = ConfigDict(populate_by_name=True)


class WhatsAppConnectionOut(BaseModel):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    name: str
    instance_name: str = Field(..., alias="instanceName")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    status: str
    is_default: bool = Field(..., alias="isDefault")
    created_by_user_id: Optional[int] = Field(None, alias="createdByUserId")
    connected_at: Optional[datetime] = Field(None, alias="connectedAt")
    disconnected_at: Optional[datetime] = Field(None, alias="disconnectedAt")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WhatsAppConnectionStatusOut(BaseModel):
    connection_id: int = Field(..., alias="connectionId")
    instance_name: str = Field(..., alias="instanceName")
    status: str
    raw_state: Optional[str] = Field(None, alias="rawState")
    raw: dict[str, Any] = {}

    model_config = ConfigDict(populate_by_name=True)


class WhatsAppConversationOut(BaseModel):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    connection_id: int = Field(..., alias="connectionId")
    client_id: Optional[int] = Field(None, alias="clientId")
    opportunity_id: Optional[int] = Field(None, alias="opportunityId")
    remote_phone: str = Field(..., alias="remotePhone")
    remote_name: Optional[str] = Field(None, alias="remoteName")
    avatar_url: Optional[str] = Field(None, alias="avatarUrl")
    last_message_text: Optional[str] = Field(None, alias="lastMessageText")
    last_message_at: Optional[datetime] = Field(None, alias="lastMessageAt")
    unread_count: int = Field(0, alias="unreadCount")
    open_opportunities_count: Optional[int] = Field(None, alias="openOpportunitiesCount")
    open_opportunities_value_cents: Optional[int] = Field(None, alias="openOpportunitiesValueCents")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WhatsAppMessageOut(BaseModel):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    connection_id: int = Field(..., alias="connectionId")
    conversation_id: int = Field(..., alias="conversationId")
    external_message_id: Optional[str] = Field(None, alias="externalMessageId")
    direction: str
    message_type: str = Field(..., alias="messageType")
    body: str
    status: Optional[str] = None
    remote_phone: str = Field(..., alias="remotePhone")
    media_url: Optional[str] = Field(None, alias="mediaUrl")
    media_mime_type: Optional[str] = Field(None, alias="mediaMimeType")
    media_file_name: Optional[str] = Field(None, alias="mediaFileName")
    media_size: Optional[int] = Field(None, alias="mediaSize")
    media_duration: Optional[int] = Field(None, alias="mediaDuration")
    sent_at: Optional[datetime] = Field(None, alias="sentAt")
    received_at: Optional[datetime] = Field(None, alias="receivedAt")
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SendTextPayload(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Texto obrigatório.")
        return cleaned

class EnsureConversationPayload(BaseModel):
    remote_phone: Optional[str] = Field(None, alias="remotePhone")
    remote_name: Optional[str] = Field(None, alias="remoteName")
    client_id: Optional[int] = Field(None, alias="clientId")

    @field_validator("remote_phone")
    @classmethod
    def validate_remote_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("Numero invalido.")
        return digits

    @field_validator("remote_name")
    @classmethod
    def validate_remote_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            return None
        if len(cleaned) > 120:
            raise ValueError("Nome muito longo.")
        return cleaned

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("ID invalido.")
        return value

    model_config = ConfigDict(populate_by_name=True)

class WebhookAckOut(BaseModel):
    accepted: bool = True
    reason: Optional[str] = None

class WhatsAppConversationUpdatePayload(BaseModel):
    remote_name: Optional[str] = Field(None, alias="remoteName")
    client_id: Optional[int] = Field(None, alias="clientId")
    opportunity_id: Optional[int] = Field(None, alias="opportunityId")

    @field_validator("remote_name")
    @classmethod
    def validate_remote_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Nome obrigatorio.")
        if len(cleaned) > 120:
            raise ValueError("Nome muito longo.")
        return cleaned

    @field_validator("client_id", "opportunity_id")
    @classmethod
    def validate_ids(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("ID invalido.")
        return value

    model_config = ConfigDict(populate_by_name=True)


class WhatsAppInboxAccessOut(BaseModel):
    enabled: bool


class AdminMasterWhatsAppOverviewOut(BaseModel):
    total_connections: int
    connected_connections: int
    disconnected_connections: int
    connecting_connections: int
    agencies_with_whatsapp: int
    inbox_enabled_users: int
    inbox_enabled_agencies: int


class AdminMasterWhatsAppConnectionOut(BaseModel):
    id: int
    agency_id: int
    agency_name: str | None = None
    owner_user_id: int | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    name: str
    phone_number: str | None = None
    status: str
    instance_name: str
    created_at: datetime | None = None
    connected_at: datetime | None = None
    updated_at: datetime | None = None


class AdminMasterWhatsAppInboxPermissionOut(BaseModel):
    id: int
    user_id: int | None = None
    user_name: str | None = None
    user_email: str | None = None
    agency_id: int | None = None
    agency_name: str | None = None
    enabled: bool
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    granted_by_user_id: int | None = None
    granted_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminMasterWhatsAppInboxPermissionUpsertIn(BaseModel):
    user_id: int | None = Field(default=None, alias="userId")
    agency_id: int | None = Field(default=None, alias="agencyId")
    enabled: bool = True

    @field_validator("user_id", "agency_id")
    @classmethod
    def validate_target_id(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("ID inválido.")
        return value

    @field_validator("enabled")
    @classmethod
    def validate_enabled(cls, value: bool) -> bool:
        return bool(value)

    model_config = ConfigDict(populate_by_name=True)

