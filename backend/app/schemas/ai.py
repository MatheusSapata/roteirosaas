from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator

FollowUpKeyLiteral = Literal[
    "destination",
    "travel_dates",
    "audience",
    "included_services",
    "highlights",
    "pricing",
    "call_to_action",
    "urgency",
    "exclusions",
    "tone",
]

class AiAttachmentIn(BaseModel):
    name: str
    mime_type: str | None = None
    data: str = Field(..., description="Base64 encoded content")


class AiFollowUpAnswers(BaseModel):
    destination: str | None = None
    travel_dates: str | None = None
    audience: str | None = None
    highlights: str | None = None
    pricing: str | None = None
    included_services: str | None = None
    exclusions: str | None = None
    urgency: str | None = None
    call_to_action: str | None = None
    tone: str | None = None


class AiManualMedia(BaseModel):
    url: str
    label: str | None = None
    section_hint: Literal["hero", "story", "gallery", "photo", "banner"] | None = None


MAX_AI_IMAGES_PER_SECTION = 6


class AiImageSelection(BaseModel):
    section: Literal["hero", "story", "gallery", "photo", "banner", "itinerary"]
    prompt_hint: str | None = None
    count: int | None = Field(default=1, ge=1, le=MAX_AI_IMAGES_PER_SECTION)
    per_day: bool = False

    @model_validator(mode="after")
    def _validate_per_day(self) -> "AiImageSelection":
        if self.per_day and self.section != "itinerary":
            raise ValueError("O modo 'uma imagem por dia' s�� est�� dispon��vel para itiner��rios.")
        if self.count is None or self.count < 1:
            self.count = 1
        return self


class AiPageRequest(BaseModel):
    agency_id: int
    briefing: str = Field("", description="Resumo textual opcional.")
    answers: AiFollowUpAnswers = Field(default_factory=AiFollowUpAnswers)
    attachments: List[AiAttachmentIn] = Field(default_factory=list)
    manual_media: List[AiManualMedia] = Field(default_factory=list)
    video_url: HttpUrl | None = None
    preferred_title: str | None = None
    generate_ai_images: bool = False
    ai_image_targets: List[AiImageSelection] = Field(default_factory=list)
    auto_publish: bool = True
    theme_mode: Literal["light", "dark"] = "light"

    @model_validator(mode="after")
    def _validate_image_targets(self) -> "AiPageRequest":
        targets = self.ai_image_targets or []
        if not self.generate_ai_images and targets:
            raise ValueError("ai_image_targets only allowed when generate_ai_images is true")
        if len(targets) > 5:
            raise ValueError("Selecione no mǭximo 5 seções para gerar imagens.")
        return self


class AiCreditTransactionOut(BaseModel):
    id: int
    delta: int
    reason: str
    metadata: dict[str, Any] | None = None
    created_at: str


class AiCreditWalletOut(BaseModel):
    balance: int
    transactions: List[AiCreditTransactionOut] = Field(default_factory=list)


class AiPageResponse(BaseModel):
    page_id: int
    redirect_url: str
    published: bool
    credits_spent: int
    credits_balance: int
    message: str


class AiBriefingInterpretRequest(BaseModel):
    agency_id: int
    briefing: str = Field("", description="Resumo textual opcional do briefing.")
    attachments: List[AiAttachmentIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ensure_source(self) -> "AiBriefingInterpretRequest":
        trimmed = self.briefing.strip() if isinstance(self.briefing, str) else ""
        if trimmed:
            self.briefing = trimmed
        if len(trimmed) < 10 and not self.attachments:
            raise ValueError("Envie ao menos um resumo curto ou anexe arquivos do briefing.")
        return self


class AiBriefingInterpretResponse(BaseModel):
    summary: str | None = None
    answers: AiFollowUpAnswers
    missing: List[FollowUpKeyLiteral] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    raw_text: str | None = None
