from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WebhookNotificationRuleBase(BaseModel):
    event_key: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    enabled: bool = True
    title_template: str = Field(min_length=1, max_length=255)
    body_template: str = Field(min_length=1)
    icon_tag: str | None = Field(default=None, max_length=80)
    priority: int = Field(default=3, ge=1, le=5)
    topic: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0)
    is_builtin: bool = True


class WebhookNotificationRuleCreate(WebhookNotificationRuleBase):
    pass


class WebhookNotificationRuleUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    enabled: bool | None = None
    title_template: str | None = Field(default=None, min_length=1, max_length=255)
    body_template: str | None = Field(default=None)
    icon_tag: str | None = Field(default=None, max_length=80)
    priority: int | None = Field(default=None, ge=1, le=5)
    topic: str | None = Field(default=None, max_length=255)
    sort_order: int | None = None
    is_builtin: bool | None = None


class WebhookNotificationRuleOut(WebhookNotificationRuleBase):
    id: int
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


class WebhookNotificationTestResponse(BaseModel):
    success: bool
    message: str | None = None
