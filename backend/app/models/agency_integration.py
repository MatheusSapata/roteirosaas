from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgencyIntegration(Base):
    __tablename__ = "agency_integrations"
    __table_args__ = (UniqueConstraint("agency_id", "provider", name="uq_agency_integrations_agency_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    token_encrypted = Column(Text, nullable=False)
    secret_encrypted = Column(Text, nullable=False)
    token_last4 = Column(String(4), nullable=True)
    sso_email = Column(String(255), nullable=True)
    sso_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    connection_status = Column(String(30), nullable=False, default="disconnected")
    last_error = Column(String(500), nullable=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    agency = relationship("Agency")
