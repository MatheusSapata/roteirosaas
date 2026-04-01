from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


class StripeAccountStatus(BaseModel):
    connected: bool
    account_id: str | None = None
    onboarding_completed: bool
    charges_enabled: bool
    payouts_enabled: bool
    email: str | None = None
    country: str | None = None
    currency: str | None = None
    requirements: list[str] | None = None


class StripeOnboardingLinkResponse(BaseModel):
    url: str


class SaleCustomerPayload(BaseModel):
    name: str
    email: EmailStr
    phone: str


class PublicCheckoutRequest(BaseModel):
    page_id: int
    product_id: str
    section_id: str | None = None
    page_slug: str | None = None
    agency_slug: str | None = None
    source_url: str | None = None
    customer: SaleCustomerPayload


class PublicCheckoutResponse(BaseModel):
    sale_id: int
    client_secret: str
    passenger_token: str


class PassengerInput(BaseModel):
    name: str
    cpf: str | None = None
    birthdate: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    boarding_location: str | None = None
    extras: str | None = None


class SalePassengerOut(BaseModel):
    id: int
    name: str
    cpf: str | None = None
    birthdate: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    boarding_location: str | None = None
    extras: str | None = None


class SaleSummary(BaseModel):
    id: int
    created_at: Optional[datetime] = None
    product_title: str
    product_description: str | None = None
    amount_cents: int
    currency: str
    commission_cents: int
    stripe_fee_cents: int | None = None
    net_amount_cents: int | None = None
    payment_method: str | None = None
    installments: int
    payment_status: str
    financial_status: str
    payout_status: str
    passenger_status: str
    passengers_required: int
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


class SaleDetail(SaleSummary):
    passengers: list[SalePassengerOut]


class SaleListResponse(BaseModel):
    items: list[SaleSummary]
    total: int
    page: int
    page_size: int


class PassengerLinkResponse(BaseModel):
    token: str
    url: str


class PassengerFormResponse(BaseModel):
    sale_id: int
    product_title: str
    passengers_required: int
    passenger_status: str
    passengers: list[SalePassengerOut]

