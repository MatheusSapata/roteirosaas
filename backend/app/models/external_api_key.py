from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class ExternalApiKey(Base):
    __tablename__ = "external_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, index=True, default="aerodatabox")
    marketplace = Column(String(50), nullable=True, index=True)
    api_host = Column(String(255), nullable=True)
    label = Column(String(255), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    api_key_last4 = Column(String(12), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    status = Column(String(20), nullable=False, default="active", server_default="active")
    priority = Column(Integer, nullable=False, default=1, server_default="1")
    monthly_limit = Column(Integer, nullable=False, default=1000, server_default="1000")
    monthly_usage_estimated = Column(Integer, nullable=False, default=0, server_default="0")
    total_usage_estimated = Column(Integer, nullable=False, default=0, server_default="0")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    reset_day = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
