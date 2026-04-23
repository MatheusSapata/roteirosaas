from __future__ import annotations

import uuid
from datetime import date
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProductStatus(str, Enum):  # type: ignore[misc]
    draft = "draft"
    active = "active"
    inactive = "inactive"


class ProductInventoryStrategy(str, Enum):  # type: ignore[misc]
    manual = "manual"
    unlimited = "unlimited"


class ProductScheduleMode(str, Enum):  # type: ignore[misc]
    fixed_date = "fixed_date"
    recurring = "recurring"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    template_contract_id = Column(
        Integer,
        ForeignKey("legal_contract_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=True)
    status = Column(String(20), nullable=False, default=ProductStatus.draft.value)
    trip_date = Column(Date, nullable=True)
    date_is_flexible = Column(Boolean, nullable=False, default=False)
    inventory_strategy = Column(String(20), nullable=False, default=ProductInventoryStrategy.manual.value)
    total_slots = Column(Integer, nullable=False, default=0)
    available_slots = Column(Integer, nullable=False, default=0)
    reserved_slots = Column(Integer, nullable=False, default=0)
    sold_slots = Column(Integer, nullable=False, default=0)
    allow_oversell = Column(Boolean, nullable=False, default=False)
    has_rooms = Column(Boolean, nullable=False, default=False)
    is_road_trip = Column(Boolean, nullable=False, default=False)
    card_interest_mode = Column(String(20), nullable=False, default="merchant")
    checkout_banner_url = Column(String(500), nullable=True)
    checkout_product_image_url = Column(String(500), nullable=True)
    allowed_payment_methods = Column(JSONB, nullable=True)
    schedule_mode = Column(String(20), nullable=False, default=ProductScheduleMode.fixed_date.value)
    timezone = Column(String(64), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agency = relationship("Agency", back_populates="products")
    user = relationship("User", back_populates="products")
    template_contract = relationship("LegalContractTemplate", back_populates="products")
    variations = relationship("ProductVariation", back_populates="product", cascade="all, delete-orphan")
    rooms = relationship("ProductRoom", back_populates="product", cascade="all, delete-orphan")
    departures = relationship("Departure", back_populates="product", cascade="all, delete-orphan")
    schedule_templates = relationship("ScheduleTemplate", back_populates="product", cascade="all, delete-orphan")
    schedule_exceptions = relationship("ScheduleException", back_populates="product", cascade="all, delete-orphan")
    inventory_events = relationship(
        "ProductInventoryEvent",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sales = relationship("Sale", back_populates="product")


class ProductVariationStatus(str, Enum):  # type: ignore[misc]
    active = "active"
    inactive = "inactive"


class ProductVariationStockMode(str, Enum):  # type: ignore[misc]
    shared = "shared"
    variant = "variant"


class ProductAccommodationMode(str, Enum):  # type: ignore[misc]
    private = "private"
    shared = "shared"


class ProductVariation(Base):
    __tablename__ = "product_variations"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False, unique=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    people_included = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default=ProductVariationStatus.active.value)
    stock_mode = Column(String(20), nullable=False, default=ProductVariationStockMode.shared.value)
    has_accommodation = Column(Boolean, nullable=False, default=False)
    accommodation_mode = Column(String(20), nullable=False, default=ProductAccommodationMode.private.value)
    room_capacity = Column(Integer, nullable=False, default=1)
    slots_per_unit = Column(Integer, nullable=False, default=1)
    total_slots = Column(Integer, nullable=True)
    available_slots = Column(Integer, nullable=True)
    reserved_slots = Column(Integer, nullable=True)
    sold_slots = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    child_policy_enabled = Column(Boolean, nullable=False, default=False)
    child_pricing_rules = Column(JSONB, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="variations")
    inventory_events = relationship(
        "ProductInventoryEvent",
        back_populates="variation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sale_items = relationship("SaleItem", back_populates="variation")


class ProductInventoryEventAction(str, Enum):  # type: ignore[misc]
    manual_total = "manual_total"
    manual_available = "manual_available"
    reserve = "reserve"
    release = "release"
    confirm = "confirm"
    cancel = "cancel"


class ProductInventoryEvent(Base):
    __tablename__ = "product_inventory_events"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variation_id = Column(Integer, ForeignKey("product_variations.id", ondelete="CASCADE"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_item_id = Column(Integer, ForeignKey("sale_items.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(32), nullable=False)
    quantity = Column(Integer, nullable=False)
    available_before = Column(Integer, nullable=True)
    available_after = Column(Integer, nullable=True)
    context = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="inventory_events")
    variation = relationship("ProductVariation", back_populates="inventory_events")
    sale = relationship("Sale", back_populates="inventory_events")
    sale_item = relationship("SaleItem", back_populates="inventory_events")


class ProductRoom(Base):
    __tablename__ = "product_rooms"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False, default=1)
    is_private = Column(Boolean, nullable=False, default=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="rooms")
