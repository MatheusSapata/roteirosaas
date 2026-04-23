from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChildPricingRulePayload(BaseModel):
    key: Literal["under_5", "age_5_12"]
    label: str
    min_age: int = Field(ge=0)
    max_age: int = Field(ge=0)
    enabled: bool = False
    pricing_mode: Literal["free", "extra"] = "free"
    extra_amount_cents: int = Field(0, ge=0)
    counts_towards_capacity: bool = False
    counts_as_passenger: bool = True
    max_quantity: int | None = Field(default=None, ge=0)


class ProductVariationPayload(BaseModel):
    public_id: str | None = None
    name: str
    description: str | None = None
    price_cents: int = Field(..., ge=0)
    currency: str = Field("BRL", min_length=3, max_length=3)
    people_included: int = Field(1, ge=1)
    status: Literal["active", "inactive"] = "active"
    stock_mode: Literal["shared", "variant"] = "shared"
    has_accommodation: bool = False
    accommodation_mode: Literal["private", "shared"] = "private"
    room_capacity: int = Field(1, ge=1)
    slots_per_unit: int = Field(1, ge=1)
    total_slots: int | None = Field(default=None, ge=0)
    available_slots: int | None = Field(default=None, ge=0)
    child_policy_enabled: bool = False
    child_pricing_rules: list[ChildPricingRulePayload] | None = None
    sort_order: int = 0


class ProductRoomPayload(BaseModel):
    id: int | None = None
    name: str
    capacity: int = Field(1, ge=1)
    is_private: bool = False
    stock_quantity: int = Field(0, ge=0)


class ProductPayload(BaseModel):
    name: str
    description: str | None = None
    status: Literal["draft", "active", "inactive"] = "draft"
    agency_id: int | None = None
    template_contract_id: int | None = None
    trip_date: date | None = None
    date_is_flexible: bool = False
    inventory_strategy: Literal["manual", "unlimited"] = "manual"
    total_slots: int = Field(0, ge=0)
    available_slots: int = Field(0, ge=0)
    allow_oversell: bool = False
    card_interest_mode: Literal["merchant", "customer"] | None = None
    allowed_payment_methods: list[Literal["pix", "credit_card", "boleto"]] = Field(
        default_factory=lambda: ["pix", "credit_card", "boleto"]
    )
    checkout_banner_url: str | None = Field(default=None, max_length=500)
    checkout_product_image_url: str | None = Field(default=None, max_length=500)
    schedule_mode: Literal["fixed_date", "recurring"] = "fixed_date"
    timezone: str | None = Field(default=None, max_length=64)
    variations: list[ProductVariationPayload] = Field(default_factory=list)
    boarding_locations: list[str] = Field(default_factory=list)
    has_rooms: bool | None = None
    is_road_trip: bool = False
    rooms: list[ProductRoomPayload] = Field(default_factory=list)


class InventoryAdjustmentPayload(BaseModel):
    total_slots: int | None = Field(default=None, ge=0)
    available_slots: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)


class ProductBoardingLocationsPayload(BaseModel):
    locations: list[str] = Field(default_factory=list)


class ProductVariationOut(BaseModel):
    id: int
    public_id: str
    name: str
    description: str | None = None
    price_cents: int
    currency: str
    people_included: int
    status: str
    stock_mode: str
    has_accommodation: bool
    accommodation_mode: str
    room_capacity: int
    slots_per_unit: int
    total_slots: int | None = None
    available_slots: int | None = None
    reserved_slots: int | None = None
    sold_slots: int | None = None
    sort_order: int
    child_policy_enabled: bool
    child_pricing_rules: list[ChildPricingRulePayload]


class ProductRoomOut(BaseModel):
    id: int
    name: str
    capacity: int
    is_private: bool
    stock_quantity: int


class ProductSummary(BaseModel):
    id: int
    public_id: str
    agency_id: int | None = None
    template_contract_id: int | None = None
    template_contract_name: str | None = None
    name: str
    description: str | None = None
    status: str
    trip_date: date | None = None
    date_is_flexible: bool
    total_slots: int
    available_slots: int
    reserved_slots: int
    sold_slots: int
    inventory_strategy: str
    allow_oversell: bool
    card_interest_mode: str
    allowed_payment_methods: list[str] = Field(default_factory=lambda: ["pix", "credit_card", "boleto"])
    checkout_banner_url: str | None = None
    checkout_product_image_url: str | None = None
    schedule_mode: str
    timezone: str | None = None
    variations: list[ProductVariationOut]
    boarding_locations: list[str] = Field(default_factory=list)
    has_rooms: bool
    is_road_trip: bool


class ProductDetail(ProductSummary):
    created_at: datetime
    updated_at: datetime | None = None
    rooms: list[ProductRoomOut] = Field(default_factory=list)


class ProductListResponse(BaseModel):
    items: list[ProductSummary]


class ProductInventoryRebuildResponse(BaseModel):
    scanned_products: int
    updated_products: int
