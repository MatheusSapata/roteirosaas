from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from app.db.base import Base


class AsaasEventLog(Base):
    __tablename__ = "asaas_event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(120), nullable=True, index=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at = Column(DateTime(timezone=True), nullable=True)
