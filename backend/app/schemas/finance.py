from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class PaymentBreakdown(BaseModel):
    base_amount_cents: int
    gross_amount_cents: int
    platform_fee_amount_cents: int
    gateway_fee_estimated_cents: int
    agency_net_amount_cents: int
    installment_amount_cents: int
    installments: int
    currency: str
    payment_method: str
    spread_percentage: float


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


class CheckoutChildSelection(BaseModel):
    key: str
    quantity: int = Field(0, ge=0)


class CheckoutCartItem(BaseModel):
    variation_id: str
    quantity: int = Field(..., ge=1)
    children: list[CheckoutChildSelection] = Field(default_factory=list)


class ProductCheckoutRequest(BaseModel):
    product_id: str
    items: list[CheckoutCartItem]
    customer: SaleCustomerPayload
    page_id: int | None = None
    page_slug: str | None = None
    agency_slug: str | None = None
    source_url: str | None = None
    channel: str = "page"


class PosCheckoutRequest(BaseModel):
    product_id: str
    items: list[CheckoutCartItem]
    customer: SaleCustomerPayload
    channel: str = "pos"


class PaymentLinkRequest(PosCheckoutRequest):
    expires_in_minutes: int | None = Field(default=60, ge=5, le=1440)


class PublicCheckoutResponse(BaseModel):
    sale_id: int
    checkout_reference: str
    passenger_token: str | None = None
    provider: str
    provider_status: str
    breakdown: PaymentBreakdown


class PaymentLinkResponse(BaseModel):
    sale_id: int
    token: str
    url: str


class PaymentConfirmationRequest(BaseModel):
    payment_method: str = "credit_card"
    installments: int = Field(1, ge=1, le=12)
    customer: SaleCustomerPayload | None = None


class SaleStatusSimulationRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|processing|paid|canceled|refunded)$")


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
    passenger_group_id: int | None = None
    passenger_index: int | None = None
    type: str
    name: str
    cpf: str | None = None
    birthdate: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    boarding_location: str | None = None
    extras: str | None = None


class PassengerGroupPassengerInput(BaseModel):
    passenger_index: int = Field(..., ge=1)
    type: str = "adult"
    name: str
    cpf: str | None = None
    birthdate: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    boarding_location: str | None = None
    extras: str | None = None


class PassengerGroupSaveRequest(BaseModel):
    passengers: list[PassengerGroupPassengerInput]


class PassengerGroupOut(BaseModel):
    id: int
    sale_item_id: int
    product_id: int | None = None
    product_name: str
    label: str
    group_index: int
    capacity: int
    occupied_slots: int
    status: str
    allows_children: bool
    passengers: list[SalePassengerOut]


class PassengerGroupListResponse(BaseModel):
    sale_id: int
    passenger_status: str
    passengers_required: int
    total_capacity: int
    groups: list[PassengerGroupOut]
    contract_id: int | None = None
    contract_signature_link: str | None = None
    contract_signature_token: str | None = None


class AgencyBlimbooSettings(BaseModel):
    token: str | None = None
    has_token: bool = False
    updated_at: Optional[datetime] = None


class AgencyBlimbooSettingsPayload(BaseModel):
    token: str | None = None


class SaleSummary(BaseModel):
    id: int
    created_at: Optional[datetime] = None
    product_public_id: str | None = None
    product_title: str
    product_description: str | None = None
    page_title: str | None = None
    page_slug: str | None = None
    amount_cents: int
    base_amount_cents: int
    gross_amount_cents: int
    currency: str
    commission_cents: int
    platform_fee_amount_cents: int
    gateway_fee_estimated_cents: int
    agency_net_amount_cents: int
    installment_amount_cents: int
    net_amount_cents: int | None = None
    spread_percentage: float
    provider: str
    provider_charge_id: str | None = None
    provider_status: str
    paid_at: Optional[datetime] = None
    payment_method: str | None = None
    installments: int
    payment_status: str
    financial_status: str
    payout_status: str
    passenger_status: str
    passengers_required: int
    consumed_capacity: int
    channel: str
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    has_rooms: bool
    is_road_trip: bool
    requires_passengers: bool
    requires_rooming: bool


class SaleItemChildBreakdown(BaseModel):
    key: str
    label: str
    quantity: int
    unit_amount_cents: int
    total_amount_cents: int
    counts_towards_capacity: bool
    counts_as_passenger: bool


class SaleItemOut(BaseModel):
    id: int
    variation_public_id: str | None = None
    variation_name: str
    quantity: int
    unit_price: int
    total_price: int
    currency: str
    people_count: int
    consumed_capacity: int
    accommodation_mode: str
    room_capacity: int
    slots_per_unit: int
    slots_reserved: int
    occupancy_status: str
    child_extra_amount_cents: int
    child_breakdown: list[SaleItemChildBreakdown]
    status: str


class SaleDetail(SaleSummary):
    passengers: list[SalePassengerOut]
    items: list[SaleItemOut]
    passenger_groups: list[PassengerGroupOut] | None = None


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
    product_description: str | None = None
    passengers_required: int
    consumed_capacity: int
    passenger_status: str
    payment_status: str
    payout_status: str
    amount_cents: int
    gross_amount_cents: int
    installment_amount_cents: int
    installments: int
    channel: str
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    boarding_locations: list[str] = Field(default_factory=list)
    passengers: list[SalePassengerOut]
    items: list[SaleItemOut]
    contract_id: int | None = None
    contract_signature_link: str | None = None
    contract_signature_token: str | None = None
    groups: list[PassengerGroupOut]
    has_rooms: bool
    is_road_trip: bool
    requires_passengers: bool
    requires_rooming: bool

