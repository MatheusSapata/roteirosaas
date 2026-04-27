from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator
from pydantic.config import ConfigDict

LeadFieldType = Literal["name", "phone", "email", "city", "cpf", "birthdate"]


class LeadFormFieldSchema(BaseModel):
    id: str
    type: LeadFieldType
    label: str
    placeholder: Optional[str] = None
    required: bool = True

    @validator("id", "label")
    def sanitize_text(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("Campo obrigatório")
        return value


class LeadFormBase(BaseModel):
    name: str
    title: str
    subtitle: Optional[str] = None
    button_label: str = Field(..., alias="buttonLabel")
    button_color: Optional[str] = Field(None, alias="buttonColor")
    show_logo: bool = Field(True, alias="showLogo")
    fields: list[LeadFormFieldSchema]
    default_status_id: Optional[int] = Field(None, alias="defaultStatusId")

    @validator("name", "title", "button_label")
    def validate_text(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("Campo obrigatório")
        return value

    @validator("fields")
    def validate_fields(cls, value: list[LeadFormFieldSchema]) -> list[LeadFormFieldSchema]:
        if not value:
            raise ValueError("Selecione pelo menos um campo.")
        return value

    model_config = ConfigDict(populate_by_name=True)


class LeadFormCreate(LeadFormBase):
    agency_id: int = Field(..., alias="agencyId")


class LeadFormUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    button_label: Optional[str] = Field(None, alias="buttonLabel")
    button_color: Optional[str] = Field(None, alias="buttonColor")
    show_logo: Optional[bool] = Field(None, alias="showLogo")
    fields: Optional[list[LeadFormFieldSchema]] = None
    default_status_id: Optional[int] = Field(None, alias="defaultStatusId")

    @validator("name", "title", "button_label", pre=True)
    def sanitize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Campo obrigatório")
        return value

    @validator("fields")
    def validate_fields(cls, value: Optional[list[LeadFormFieldSchema]]) -> Optional[list[LeadFormFieldSchema]]:
        if value is not None and not value:
            raise ValueError("Selecione pelo menos um campo.")
        return value

    model_config = ConfigDict(populate_by_name=True)


class LeadFormOut(LeadFormBase):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    total_leads: int = Field(0, alias="total_leads")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    default_status_name: Optional[str] = Field(None, alias="defaultStatusName")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LeadContactOut(BaseModel):
    id: int
    form_id: int = Field(..., alias="form_id")
    form_name: str = Field(..., alias="form_name")
    page_id: Optional[int] = Field(None, alias="page_id")
    page_title: Optional[str] = Field(None, alias="page_title")
    page_slug: Optional[str] = Field(None, alias="page_slug")
    page_url: Optional[str] = Field(None, alias="page_url")
    name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    source: Optional[str] = None
    opportunity_name: Optional[str] = Field(None, alias="opportunity_name")
    estimated_value_cents: Optional[int] = Field(None, alias="estimated_value_cents")
    status_id: Optional[int] = Field(None, alias="status_id")
    status_name: Optional[str] = Field(None, alias="status_name")
    status_color: Optional[str] = Field(None, alias="status_color")
    client_id: Optional[int] = Field(None, alias="client_id")
    created_at: Optional[datetime] = Field(None, alias="created_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LeadFormPublicOut(BaseModel):
    id: int
    name: str
    title: str
    subtitle: Optional[str] = None
    button_label: str = Field(..., alias="buttonLabel")
    button_color: Optional[str] = Field(None, alias="buttonColor")
    show_logo: bool = Field(True, alias="showLogo")
    fields: list[LeadFormFieldSchema]
    default_status_id: Optional[int] = Field(None, alias="defaultStatusId")
    default_status_name: Optional[str] = Field(None, alias="defaultStatusName")
    default_status_color: Optional[str] = Field(None, alias="defaultStatusColor")
    already_submitted: bool = Field(False, alias="alreadySubmitted")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LeadFormSubmissionField(BaseModel):
    fieldId: str
    type: LeadFieldType
    value: str


class LeadFormSubmissionPayload(BaseModel):
    formId: Optional[str] = None
    values: list[LeadFormSubmissionField]
    source: Optional[str] = None
    pageId: Optional[int] = None
    pageSlug: Optional[str] = None
    pageTitle: Optional[str] = None
    pageUrl: Optional[str] = None

    @validator("values")
    def validate_values(cls, value: list[LeadFormSubmissionField]) -> list[LeadFormSubmissionField]:
        if not value:
            raise ValueError("Envie pelo menos um valor.")
        return value


class LeadStatusBase(BaseModel):
    name: str
    color: str = "#E2E8F0"

    @validator("name")
    def validate_name(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("Defina um nome para o status.")
        return value

    @validator("color")
    def validate_color(cls, value: str) -> str:
        value = (value or "#E2E8F0").strip()
        if not value.startswith("#") or len(value) not in {4, 7}:
            raise ValueError("Informe uma cor válida em formato hexadecimal.")
        return value


class LeadStatusCreate(LeadStatusBase):
    agency_id: int = Field(..., alias="agencyId")


class LeadStatusUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

    @validator("name")
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Defina um nome para o status.")
        return value

    @validator("color")
    def validate_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value.startswith("#") or len(value) not in {4, 7}:
            raise ValueError("Informe uma cor válida em formato hexadecimal.")
        return value


class LeadStatusOut(LeadStatusBase):
    id: int
    agency_id: int = Field(..., alias="agencyId")
    created_at: Optional[datetime] = Field(None, alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LeadContactStatusUpdate(BaseModel):
    status_id: Optional[int] = Field(None, alias="statusId")
