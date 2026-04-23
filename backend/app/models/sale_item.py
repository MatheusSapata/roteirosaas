from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.product import ProductAccommodationMode


class SaleItemStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    confirmed = "confirmed"
    canceled = "canceled"
    refunded = "refunded"


class SaleItemOccupancyStatus(str, Enum):  # type: ignore[misc]
    pending = "pending_assignment"
    partial = "partial"
    complete = "complete"


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    departure_id = Column(Integer, ForeignKey("departures.id", ondelete="SET NULL"), nullable=True, index=True)
    product_public_id = Column(String(36), nullable=True)
    variation_id = Column(Integer, ForeignKey("product_variations.id", ondelete="SET NULL"), nullable=True, index=True)
    variation_public_id = Column(String(36), nullable=True)
    variation_name = Column(String(255), nullable=False)
    variation_description = Column(String(500), nullable=True)
    currency = Column(String(3), nullable=False, default="BRL")
    unit_price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal_amount_cents = Column(Integer, nullable=False, default=0)
    discount_amount_cents = Column(Integer, nullable=False, default=0)
    total_amount_cents = Column(Integer, nullable=False, default=0)
    total_price = Column(Integer, nullable=False)
    people_count = Column(Integer, nullable=False, default=1)
    occupancy = Column(Integer, nullable=False, default=1)
    allows_children = Column(Boolean, nullable=False, default=False)
    children_rules_snapshot = Column(JSONB, nullable=True)
    stock_mode = Column(String(20), nullable=False, default="shared")
    accommodation_mode = Column(String(20), nullable=False, default=ProductAccommodationMode.private.value)
    room_capacity = Column(Integer, nullable=False, default=1)
    slots_per_unit = Column(Integer, nullable=False, default=1)
    slots_reserved = Column(Integer, nullable=False, default=0)
    occupancy_status = Column(
        String(20),
        nullable=False,
        default=SaleItemOccupancyStatus.pending.value,
    )
    reserved_from_product = Column(Integer, nullable=False, default=0)
    reserved_from_variant = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default=SaleItemStatus.pending.value)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")
    departure = relationship("Departure", back_populates="sale_items")
    variation = relationship("ProductVariation", back_populates="sale_items")
    inventory_events = relationship("ProductInventoryEvent", back_populates="sale_item", cascade="all, delete-orphan")
    passenger_groups = relationship("PassengerGroup", back_populates="sale_item", cascade="all, delete-orphan")


class SalePaymentLinkStatus(str, Enum):  # type: ignore[misc]
    open = "open"
    paid = "paid"
    expired = "expired"
    canceled = "canceled"


class SalePaymentLink(Base):
    __tablename__ = "sale_payment_links"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, unique=True)
    token = Column(String(64), default=lambda: uuid.uuid4().hex, nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default=SalePaymentLinkStatus.open.value)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sale = relationship("Sale", back_populates="payment_link")
    created_by = relationship("User")
