from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClientBase(BaseModel):
    name: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    state: Optional[str] = None
    birthdate: Optional[date] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Nome obrigatorio.")
        return cleaned

    @field_validator("cpf", "phone", "email", "city", "zipcode", "street", "number", "complement", "neighborhood", "state", "notes")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class ClientCreate(ClientBase):
    agency_id: int = Field(..., alias="agencyId")

    model_config = ConfigDict(populate_by_name=True)


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    state: Optional[str] = None
    birthdate: Optional[date] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None

    @field_validator("name", "cpf", "phone", "email", "city", "zipcode", "street", "number", "complement", "neighborhood", "state", "notes")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class ClientOut(ClientBase):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    opportunities_count: int = Field(0, alias="opportunitiesCount")
    open_opportunities_count: int = Field(0, alias="openOpportunitiesCount")
    total_estimated_value_cents: int = Field(0, alias="totalEstimatedValueCents")
    last_opportunity_at: Optional[datetime] = Field(None, alias="lastOpportunityAt")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OpportunityUpdate(BaseModel):
    opportunity_name: Optional[str] = Field(None, alias="opportunityName")
    estimated_value_cents: Optional[int] = Field(None, alias="estimatedValueCents")
    status_id: Optional[int] = Field(None, alias="statusId")
    internal_notes: Optional[str] = Field(None, alias="internalNotes")
    responsible_user_id: Optional[int] = Field(None, alias="responsibleUserId")
    expected_close_date: Optional[date] = Field(None, alias="expectedCloseDate")

    @field_validator("opportunity_name", "internal_notes")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None

    model_config = ConfigDict(populate_by_name=True)


class OpportunityFinalize(BaseModel):
    outcome: str
    note: Optional[str] = None

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in {"won", "lost"}:
            raise ValueError("Outcome invalido.")
        return normalized

    @field_validator("note")
    @classmethod
    def strip_optional_note(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class ManualOpportunityCreate(BaseModel):
    agency_id: int = Field(..., alias="agencyId")
    client_id: Optional[int] = Field(None, alias="clientId")
    name: str
    opportunity_name: Optional[str] = Field(None, alias="opportunityName")
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    birthdate: Optional[date] = None
    estimated_value_cents: Optional[int] = Field(None, alias="estimatedValueCents")
    status_id: Optional[int] = Field(None, alias="statusId")
    internal_notes: Optional[str] = Field(None, alias="internalNotes")
    responsible_user_id: Optional[int] = Field(None, alias="responsibleUserId")
    expected_close_date: Optional[date] = Field(None, alias="expectedCloseDate")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Nome obrigatorio.")
        return cleaned

    @field_validator("opportunity_name", "cpf", "phone", "email", "city", "internal_notes")
    @classmethod
    def strip_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None

    model_config = ConfigDict(populate_by_name=True)


class OpportunityLinkClientPayload(BaseModel):
    client_id: int = Field(..., alias="clientId")

    model_config = ConfigDict(populate_by_name=True)


class NoteCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Conteudo obrigatorio.")
        return cleaned


class NoteAuthorOut(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OpportunityNoteOut(BaseModel):
    id: int
    opportunity_id: int = Field(..., alias="opportunityId")
    agency_id: int = Field(..., alias="agencyId")
    user_id: Optional[int] = Field(None, alias="userId")
    content: str
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    author: Optional[NoteAuthorOut] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ClientNoteOut(BaseModel):
    id: int
    client_id: int = Field(..., alias="clientId")
    agency_id: int = Field(..., alias="agencyId")
    user_id: Optional[int] = Field(None, alias="userId")
    content: str
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    author: Optional[NoteAuthorOut] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentOut(BaseModel):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    client_id: Optional[int] = Field(None, alias="clientId")
    opportunity_id: Optional[int] = Field(None, alias="opportunityId")
    uploaded_by_user_id: Optional[int] = Field(None, alias="uploadedByUserId")
    file_name: str = Field(..., alias="fileName")
    file_url: str = Field(..., alias="fileUrl")
    file_type: Optional[str] = Field(None, alias="fileType")
    file_size: Optional[int] = Field(None, alias="fileSize")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    source_label: Optional[str] = Field(None, alias="sourceLabel")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ClientSummaryOut(BaseModel):
    id: int
    name: str
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    state: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeadContactDetailsOut(BaseModel):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    form_id: int = Field(..., alias="formId")
    form_name: str = Field(..., alias="formName")
    page_id: Optional[int] = Field(None, alias="pageId")
    page_title: Optional[str] = Field(None, alias="pageTitle")
    page_slug: Optional[str] = Field(None, alias="pageSlug")
    page_url: Optional[str] = Field(None, alias="pageUrl")
    name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    birthdate: Optional[date] = None
    source: Optional[str] = None
    status_id: Optional[int] = Field(None, alias="statusId")
    status_name: Optional[str] = Field(None, alias="statusName")
    status_color: Optional[str] = Field(None, alias="statusColor")
    opportunity_name: Optional[str] = Field(None, alias="opportunityName")
    estimated_value_cents: Optional[int] = Field(None, alias="estimatedValueCents")
    expected_close_date: Optional[date] = Field(None, alias="expectedCloseDate")
    internal_notes: Optional[str] = Field(None, alias="internalNotes")
    auto_linked_by: Optional[str] = Field(None, alias="autoLinkedBy")
    auto_linked_at: Optional[datetime] = Field(None, alias="autoLinkedAt")
    close_outcome: Optional[str] = Field(None, alias="closeOutcome")
    closed_at: Optional[datetime] = Field(None, alias="closedAt")
    responsible_user_id: Optional[int] = Field(None, alias="responsibleUserId")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    payload: dict[str, Any] | None = None
    client: Optional[ClientSummaryOut] = None
    notes: list[OpportunityNoteOut] = []
    documents: list[DocumentOut] = []
    client_suggestions: list[ClientSummaryOut] = Field(default_factory=list, alias="clientSuggestions")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ClientDetailOut(ClientOut):
    opportunities: list[LeadContactDetailsOut] = []
    notes_timeline: list[ClientNoteOut] = Field(default_factory=list, alias="notesTimeline")
    documents: list[DocumentOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
