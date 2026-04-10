from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RoomingRoom(Base):
    __tablename__ = "rooming_rooms"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variation_id = Column(Integer, ForeignKey("product_variations.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    passenger_group_id = Column(Integer, ForeignKey("passenger_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    accommodation_label = Column(String(120), nullable=True)
    accommodation_key = Column(String(64), nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    is_private = Column(Boolean, nullable=False, default=False)
    locked = Column(Boolean, nullable=False, default=False)
    origin = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product")
    variation = relationship("ProductVariation")
    sale = relationship("Sale")
    passenger_group = relationship("PassengerGroup")
    assignments = relationship(
        "RoomingAssignment",
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RoomingAssignment.created_at",
    )


class RoomingAssignment(Base):
    __tablename__ = "rooming_assignments"
    __table_args__ = (UniqueConstraint("passenger_id", name="uq_rooming_assignment_passenger"),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooming_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    room = relationship("RoomingRoom", back_populates="assignments")
    passenger = relationship("SalePassenger")
