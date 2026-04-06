from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SaleItemStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    confirmed = "confirmed"
    canceled = "canceled"
    refunded = "refunded"


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_public_id = Column(String(36), nullable=True)
    variation_id = Column(Integer, ForeignKey("product_variations.id", ondelete="SET NULL"), nullable=True, index=True)
    variation_public_id = Column(String(36), nullable=True)
    variation_name = Column(String(255), nullable=False)
    variation_description = Column(String(500), nullable=True)
    currency = Column(String(3), nullable=False, default="BRL")
    unit_price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Integer, nullable=False)
    people_count = Column(Integer, nullable=False, default=1)
    stock_mode = Column(String(20), nullable=False, default="shared")
    reserved_from_product = Column(Integer, nullable=False, default=0)
    reserved_from_variant = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default=SaleItemStatus.pending.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")
    variation = relationship("ProductVariation", back_populates="sale_items")
    inventory_events = relationship("ProductInventoryEvent", back_populates="sale_item", cascade="all, delete-orphan")


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
