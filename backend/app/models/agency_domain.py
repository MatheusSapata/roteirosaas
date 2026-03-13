from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AgencyDomain(Base):
    __tablename__ = "agency_domains"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    host = Column(String(255), nullable=False, unique=True, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_token = Column(String(255), nullable=False)
    dns_target_type = Column(String(50), nullable=True)
    dns_target_value = Column(String(255), nullable=True)
    ssl_status = Column(String(50), nullable=False, default="pending")
    ssl_last_error = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    agency = relationship("Agency", back_populates="domains")
