from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class LocalizedText(BaseModel):
    pt: str = Field(default="")
    es: str = Field(default="")


class LegalVariableDefinition(BaseModel):
    key: str
    placeholder: str
    label: LocalizedText
    description: LocalizedText
    sample_value: str


class LegalVariableCategory(BaseModel):
    key: str
    label: LocalizedText
    variables: list[LegalVariableDefinition]


class LegalVariablesResponse(BaseModel):
    categories: list[LegalVariableCategory]


class LegalTemplatePayload(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = Field(default=None, max_length=500)
    content: str
    is_active: bool = True


class LegalTemplateSummary(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class LegalTemplateDetail(LegalTemplateSummary):
    content: str


class LegalTemplateListResponse(BaseModel):
    items: list[LegalTemplateSummary]


class LegalContractOut(BaseModel):
    id: int
    sale_id: int
    template_id: int | None = None
    buyer_name: str
    product_name: str
    total_amount: int
    currency: str
    status: str
    pdf_url: str | None = None
    created_at: datetime
    generated_at: datetime | None = None
    last_error: str | None = None
    signature_status: str
    signature_token: str | None = None
    signature_link: str | None = None
    signature_signed_at: datetime | None = None
    signature_name: str | None = None
    signature_type: str | None = None
    signature_image_url: str | None = None
    signature_ip: str | None = None
    signature_user_agent: str | None = None
    signed_pdf_url: str | None = None
    signed_pdf_generated_at: datetime | None = None
    signed_pdf_size_bytes: int | None = None
    document_hash: str | None = None
    document_hash_algorithm: str | None = None
    verification_token: str | None = None
    verification_url: str | None = None
    verification_qr_image_data: str | None = None
    verification_generated_at: datetime | None = None
    agency_signature_status: str
    agency_signature_signed_at: datetime | None = None
    agency_signature_type: str | None = None
    agency_signature_name: str | None = None
    agency_signature_role: str | None = None
    agency_signature_company: str | None = None
    agency_signature_city: str | None = None
    agency_signature_font_style: str | None = None
    agency_signature_typed_value: str | None = None
    agency_signature_image_url: str | None = None


class LegalContractListResponse(BaseModel):
    items: list[LegalContractOut]


class LegalContractDetail(LegalContractOut):
    pass


class LegalContractSignaturePublic(BaseModel):
    contract_id: int
    sale_id: int
    token: str
    buyer_name: str
    product_name: str
    currency: str
    total_amount: int
    status: str
    pdf_url: str | None = None
    signature_status: str
    signature_signed_at: datetime | None = None
    signature_name: str | None = None
    signature_type: str | None = None
    signature_image_url: str | None = None
    agency_name: str | None = None
    agency_logo_url: str | None = None
    created_at: datetime
    generated_at: datetime | None = None
    signed_pdf_url: str | None = None
    signed_pdf_generated_at: datetime | None = None
    signed_pdf_size_bytes: int | None = None
    document_hash: str | None = None
    document_hash_algorithm: str | None = None
    verification_token: str | None = None
    verification_url: str | None = None
    verification_qr_image_data: str | None = None
    verification_generated_at: datetime | None = None
    agency_signature_status: str
    agency_signature_signed_at: datetime | None = None
    agency_signature_type: str | None = None
    agency_signature_name: str | None = None
    agency_signature_role: str | None = None
    agency_signature_company: str | None = None
    agency_signature_city: str | None = None
    agency_signature_font_style: str | None = None
    agency_signature_typed_value: str | None = None
    agency_signature_image_url: str | None = None


class LegalContractSignatureSubmitPayload(BaseModel):
    signature_type: Literal["typed", "drawn"]
    full_name: str | None = None
    signature_image: str | None = None
    accepted_terms: bool = False


class LegalContractSignatureSubmitResponse(BaseModel):
    detail: LegalContractSignaturePublic


class LegalContractVerificationStatus(str, Enum):
    valid = "valid"
    pending = "pending"
    incomplete = "incomplete"
    invalid = "invalid"
    not_found = "not_found"


class LegalContractVerificationDetail(BaseModel):
    status: LegalContractVerificationStatus
    contract_id: int | None = None
    sale_id: int | None = None
    buyer_name: str | None = None
    product_name: str | None = None
    agency_name: str | None = None
    agency_logo_url: str | None = None
    created_at: datetime | None = None
    generated_at: datetime | None = None
    signature_signed_at: datetime | None = None
    signature_status: str | None = None
    signature_type: str | None = None
    agency_signature_status: str | None = None
    agency_signature_signed_at: datetime | None = None
    document_hash: str | None = None
    document_hash_algorithm: str | None = None
    signed_pdf_url: str | None = None
    signed_pdf_generated_at: datetime | None = None
    signed_pdf_size_bytes: int | None = None
    pdf_url: str | None = None
    verification_token: str | None = None
    verification_url: str | None = None
    verification_qr_image_data: str | None = None
    verification_generated_at: datetime | None = None
    message: str


class LegalContractAuditEventOut(BaseModel):
    id: int
    contract_id: int
    event_type: str
    title: str
    description: str | None = None
    actor_type: str
    occurred_at: datetime
    is_reconstructed: bool = False
    metadata: dict[str, Any] | None = None


class LegalContractAuditEventList(BaseModel):
    items: list[LegalContractAuditEventOut]
    has_more: bool = False


class LegalSignatureProfilePayload(BaseModel):
    signature_type: Literal["drawn", "typed"]
    signature_drawn_image: str | None = None
    signature_typed_value: str | None = None
    signature_font_style: str | None = None
    signature_display_name: str
    signature_role: str | None = None
    signature_company_name: str | None = None
    signature_city: str | None = None


class LegalSignatureProfileResponse(BaseModel):
    signature_type: str
    signature_drawn_image_url: str | None = None
    signature_drawn_image_data: str | None = None
    signature_typed_value: str | None = None
    signature_font_style: str | None = None
    signature_display_name: str
    signature_role: str | None = None
    signature_company_name: str | None = None
    signature_city: str | None = None
    updated_at: datetime | None = None
