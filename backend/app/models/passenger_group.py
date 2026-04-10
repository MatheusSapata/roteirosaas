from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PassengerGroupStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    partial = "partial"
    complete = "complete"


class PassengerType(str, Enum):  # type: ignore[misc]
    adult = "adult"
    child_free = "child_free"
    child_paid = "child_paid"


class PassengerGroup(Base):
    __tablename__ = "passenger_groups"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_item_id = Column(Integer, ForeignKey("sale_items.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_name_snapshot = Column(String(255), nullable=False)
    group_index = Column(Integer, nullable=False, default=1)
    label = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False, default=1)
    occupied_slots = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default=PassengerGroupStatus.pending.value)
    allows_children = Column(Boolean, nullable=False, default=False)
    children_rules_snapshot = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sale = relationship("Sale", back_populates="passenger_groups")
    sale_item = relationship("SaleItem", back_populates="passenger_groups")
    product = relationship("Product")
    passengers = relationship("SalePassenger", back_populates="passenger_group", cascade="all, delete-orphan")
