from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WebhookNotificationRuleBase(BaseModel):
    event_key: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    enabled: bool = True
    pushover_sound: str | None = Field(default=None, max_length=40)
    title_template: str = Field(min_length=1, max_length=255)
    body_template: str = Field(min_length=1)
    icon_tag: str | None = Field(default=None, max_length=80)
    priority: int = Field(default=3, ge=1, le=5)
    sort_order: int = Field(default=0)
    is_builtin: bool = True


class WebhookNotificationRuleCreate(WebhookNotificationRuleBase):
    pass


class WebhookNotificationRuleUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    enabled: bool | None = None
    pushover_sound: str | None = Field(default=None, max_length=40)
    title_template: str | None = Field(default=None, min_length=1, max_length=255)
    body_template: str | None = Field(default=None)
    icon_tag: str | None = Field(default=None, max_length=80)
    priority: int | None = Field(default=None, ge=1, le=5)
    sort_order: int | None = None
    is_builtin: bool | None = None


class WebhookNotificationRuleOut(WebhookNotificationRuleBase):
    id: int
    # Som que toca quando pushover_sound está vazio (receita nova: "viajeonvenda").
    default_pushover_sound: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WebhookNotificationMetaIcon(BaseModel):
    tag: str
    label: str
    emoji: str


class WebhookNotificationMetaOut(BaseModel):
    icons: list[WebhookNotificationMetaIcon] = Field(default_factory=list)
    available_fields: list[str] = Field(default_factory=list)
    builtin_events: list[WebhookNotificationRuleOut] = Field(default_factory=list)
    custom_events_count: int = 0


class WebhookNotificationTestRequest(BaseModel):
    event_key: str
    context: dict[str, Any] = Field(default_factory=dict)


class WebhookNotificationDelivery(BaseModel):
    channel: str
    target: str
    ok: bool
    error: str | None = None


class WebhookNotificationTestResponse(BaseModel):
    success: bool
    message: str | None = None
    deliveries: list[WebhookNotificationDelivery] = Field(default_factory=list)


class PushoverAccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    # Em branco ao alterar: ficam os atuais. Token em branco na conta nova: usa o já cadastrado.
    user_key: str | None = Field(default=None, max_length=60)
    app_token: str | None = Field(default=None, max_length=60)
    device: str | None = Field(default=None, max_length=60)
    enabled: bool | None = None
    event_keys: list[str] | None = None


class PushoverAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    user_key: str | None = Field(default=None, max_length=60)
    app_token: str | None = Field(default=None, max_length=60)
    device: str | None = Field(default=None, max_length=60)
    enabled: bool | None = None
    event_keys: list[str] | None = None


class PushoverAccountOut(BaseModel):
    id: int
    name: str
    user_key_masked: str
    app_token_masked: str
    device: str | None = None
    enabled: bool
    event_keys: list[str] = Field(default_factory=list)
    last_sent_at: datetime | None = None
    last_error: str | None = None


class PushoverSoundOut(BaseModel):
    value: str
    label: str
