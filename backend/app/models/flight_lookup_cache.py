from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class FlightLookupCache(Base):
    __tablename__ = "flight_lookup_cache"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    flight_iata = Column(String(20), nullable=True, index=True)
    flight_number = Column(String(20), nullable=True, index=True)
    flight_date = Column(Date, nullable=False, index=True)
    response_json = Column(JSONB, nullable=True)
    normalized_json = Column(JSONB, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
