from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class FlightSectionJourney(Base):
    __tablename__ = "flight_section_journeys"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(80), nullable=False, index=True)
    direction = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    is_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    segments = relationship(
        "FlightSectionSegment",
        back_populates="journey",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FlightSectionSegment.sort_order.asc()",
    )


class FlightSectionSegment(Base):
    __tablename__ = "flight_section_segments"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("flight_section_journeys.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    source_mode = Column(String(20), nullable=False, default="manual", server_default="manual")
    flight_number = Column(String(30), nullable=True)
    flight_iata = Column(String(30), nullable=True)
    flight_icao = Column(String(30), nullable=True)
    flight_date = Column(Date, nullable=True)
    airline_name = Column(String(255), nullable=True)
    airline_iata = Column(String(20), nullable=True)
    airline_icao = Column(String(20), nullable=True)
    airline_logo_url = Column(String(600), nullable=True)
    departure_airport_iata = Column(String(20), nullable=True)
    departure_airport_name = Column(String(255), nullable=True)
    departure_city = Column(String(255), nullable=True)
    departure_country = Column(String(255), nullable=True)
    departure_terminal = Column(String(50), nullable=True)
    departure_gate = Column(String(50), nullable=True)
    departure_datetime = Column(DateTime(timezone=True), nullable=True)
    arrival_airport_iata = Column(String(20), nullable=True)
    arrival_airport_name = Column(String(255), nullable=True)
    arrival_city = Column(String(255), nullable=True)
    arrival_country = Column(String(255), nullable=True)
    arrival_terminal = Column(String(50), nullable=True)
    arrival_gate = Column(String(50), nullable=True)
    arrival_datetime = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    cabin_class = Column(String(80), nullable=True)
    status = Column(String(80), nullable=True)
    included_personal_item = Column(Boolean, nullable=False, default=True, server_default="true")
    included_carry_on = Column(Boolean, nullable=False, default=True, server_default="true")
    included_checked_bag = Column(Boolean, nullable=False, default=False, server_default="false")
    notes = Column(Text, nullable=True)
    raw_provider_response = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    journey = relationship("FlightSectionJourney", back_populates="segments")
