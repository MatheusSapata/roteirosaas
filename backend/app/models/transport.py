from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func

from app.db.base import Base


class VehicleType(str, Enum):  # type: ignore[misc]
    executivo = "executivo"
    semi_leito = "semi_leito"
    leito = "leito"
    micro = "micro"
    double_deck = "double_deck"
    custom = "custom"


class VehicleLayout(Base):
    __tablename__ = "vehicle_layouts"
    __table_args__ = (UniqueConstraint("agency_id", "slug", name="uq_vehicle_layout_slug"),)

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), nullable=True)
    vehicle_type = Column(String(50), nullable=False, default=VehicleType.custom.value)
    seat_count = Column(Integer, nullable=False, default=0)
    row_count = Column(Integer, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)
    layout_schema = Column(JSONB, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vehicles = relationship("Vehicle", back_populates="layout")
    trip_configs = relationship("TripTransportConfig", back_populates="layout")
    trip_seats = relationship("TripSeat", back_populates="layout")


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("agency_id", "plate", name="uq_vehicle_plate_per_agency"),)

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    plate = Column(String(32), nullable=True)
    partner_name = Column(String(120), nullable=True)
    layout_id = Column(Integer, ForeignKey("vehicle_layouts.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    layout = relationship("VehicleLayout", back_populates="vehicles")
    trip_configs = relationship("TripTransportConfig", back_populates="vehicle")


class TripTransportConfig(Base):
    __tablename__ = "trip_transport_configs"
    __table_args__ = (UniqueConstraint("product_id", name="uq_trip_transport_product"),)

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    is_road_trip = Column(Boolean, nullable=False, default=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    layout_id = Column(Integer, ForeignKey("vehicle_layouts.id", ondelete="RESTRICT"), nullable=True, index=True)
    layout_schema_checksum = Column(String(128), nullable=True)
    seat_generation_locked = Column(Boolean, nullable=False, default=False)
    boarding_notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product")
    vehicle = relationship("Vehicle", back_populates="trip_configs")
    layout = relationship("VehicleLayout", back_populates="trip_configs")
    seats = relationship(
        "TripSeat",
        primaryjoin=lambda: TripTransportConfig.product_id == foreign(TripSeat.product_id),
        viewonly=True,
        back_populates="trip_config",
    )
    trip_vehicles = relationship(
        "TripVehicle",
        primaryjoin=lambda: TripTransportConfig.product_id == foreign(TripVehicle.product_id),
        back_populates="trip_config",
        cascade="all, delete-orphan",
    )


class TripVehicleStatus(str, Enum):  # type: ignore[misc]
    inactive = "inactive"
    active = "active"
    full = "full"


class TripVehicle(Base):
    __tablename__ = "trip_vehicles"
    __table_args__ = (UniqueConstraint("product_id", "order_index", name="uq_trip_vehicle_order"),)

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    layout_id = Column(Integer, ForeignKey("vehicle_layouts.id", ondelete="SET NULL"), nullable=True, index=True)
    display_name = Column(String(120), nullable=True)
    capacity = Column(Integer, nullable=False, default=0)
    order_index = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default=TripVehicleStatus.inactive.value)
    is_active = Column(Boolean, nullable=False, default=True)
    auto_activate_next = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    trip_config = relationship(
        "TripTransportConfig",
        primaryjoin=lambda: foreign(TripVehicle.product_id) == TripTransportConfig.product_id,
        back_populates="trip_vehicles",
    )
    vehicle = relationship("Vehicle")
    layout = relationship("VehicleLayout")
    seats = relationship("TripSeat", back_populates="trip_vehicle")
    assignments = relationship("SeatAssignment", back_populates="trip_vehicle")


class SeatCellType(str, Enum):  # type: ignore[misc]
    seat = "seat"
    preferential = "preferential"
    driver = "driver"
    door = "door"
    wc = "wc"
    stairs = "stairs"
    aisle = "aisle"
    empty = "empty"
    blocked = "blocked"


class TripSeat(Base):
    __tablename__ = "trip_seats"
    __table_args__ = (
        UniqueConstraint("product_id", "trip_vehicle_id", "seat_number", name="uq_trip_seat_number_per_vehicle"),
        UniqueConstraint(
            "trip_vehicle_id", "deck_key", "row_index", "col_index", name="uq_trip_seat_grid_per_vehicle"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("vehicle_layouts.id", ondelete="SET NULL"), nullable=True, index=True)
    trip_vehicle_id = Column(Integer, ForeignKey("trip_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_number = Column(String(32), nullable=False)
    seat_label = Column(String(64), nullable=True)
    seat_type = Column(String(32), nullable=False, default=SeatCellType.seat.value)
    row_index = Column(Integer, nullable=False)
    col_index = Column(Integer, nullable=False)
    deck_key = Column(String(64), nullable=False, server_default="andar_unico")
    deck_label = Column(String(120), nullable=True)
    deck_order = Column(Integer, nullable=False, server_default="0")
    is_selectable = Column(Boolean, nullable=False, default=True)
    is_blocked = Column(Boolean, nullable=False, default=False)
    meta_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    layout = relationship("VehicleLayout", back_populates="trip_seats")
    trip_vehicle = relationship("TripVehicle", back_populates="seats")
    trip_config = relationship(
        "TripTransportConfig",
        primaryjoin=lambda: foreign(TripSeat.product_id) == TripTransportConfig.product_id,
        viewonly=True,
        back_populates="seats",
    )
    assignments = relationship(
        "SeatAssignment",
        back_populates="seat",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SeatAssignmentActor(str, Enum):  # type: ignore[misc]
    customer = "customer"
    admin = "admin"
    system = "system"


class SeatAssignmentStatus(str, Enum):  # type: ignore[misc]
    selected_by_customer = "selected_by_customer"
    confirmed = "confirmed"
    changed_by_admin = "changed_by_admin"


class SeatAssignment(Base):
    __tablename__ = "seat_assignments"
    __table_args__ = (
        UniqueConstraint("product_id", "passenger_id", name="uq_seat_assignment_passenger"),
        UniqueConstraint("product_id", "seat_id", name="uq_seat_assignment_seat"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("trip_seats.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_vehicle_id = Column(Integer, ForeignKey("trip_vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(String(20), nullable=False, default=SeatAssignmentActor.customer.value)
    assignment_status = Column(String(30), nullable=False, default=SeatAssignmentStatus.selected_by_customer.value)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    seat = relationship("TripSeat", back_populates="assignments")
    trip_vehicle = relationship("TripVehicle", back_populates="assignments")
    passenger = relationship("SalePassenger")
    sale = relationship("Sale")


class SeatChangeActorRole(str, Enum):  # type: ignore[misc]
    customer = "customer"
    admin = "admin"
    system = "system"


class SeatChangeLog(Base):
    __tablename__ = "seat_change_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id", ondelete="CASCADE"), nullable=True, index=True)
    trip_vehicle_id = Column(Integer, ForeignKey("trip_vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=True, index=True)
    old_seat_id = Column(Integer, ForeignKey("trip_seats.id", ondelete="SET NULL"), nullable=True, index=True)
    new_seat_id = Column(Integer, ForeignKey("trip_seats.id", ondelete="SET NULL"), nullable=True, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    changed_by_role = Column(String(20), nullable=False)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    passenger = relationship("SalePassenger")
    trip_vehicle = relationship("TripVehicle")
    sale = relationship("Sale")
    old_seat = relationship("TripSeat", foreign_keys=[old_seat_id])
    new_seat = relationship("TripSeat", foreign_keys=[new_seat_id])
