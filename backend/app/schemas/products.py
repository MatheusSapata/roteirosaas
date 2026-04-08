from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProductVariationPayload(BaseModel):
    public_id: str | None = None
    name: str
    description: str | None = None
    price_cents: int = Field(..., ge=0)
    currency: str = Field("BRL", min_length=3, max_length=3)
    people_included: int = Field(1, ge=1)
    status: Literal["active", "inactive"] = "active"
    stock_mode: Literal["shared", "variant"] = "shared"
    total_slots: int | None = Field(default=None, ge=0)
    available_slots: int | None = Field(default=None, ge=0)
    sort_order: int = 0


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
    variations: list[ProductVariationPayload] = Field(default_factory=list)


class InventoryAdjustmentPayload(BaseModel):
    total_slots: int | None = Field(default=None, ge=0)
    available_slots: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)


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
    total_slots: int | None = None
    available_slots: int | None = None
    reserved_slots: int | None = None
    sold_slots: int | None = None
    sort_order: int


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
    variations: list[ProductVariationOut]


class ProductDetail(ProductSummary):
    created_at: datetime
    updated_at: datetime | None = None


class ProductListResponse(BaseModel):
    items: list[ProductSummary]
