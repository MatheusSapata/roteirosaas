from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class ViajeonWebhookEvent(Base):
    __tablename__ = "viajeon_webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(120), nullable=False)
    environment = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="processed")
    user_id = Column(Integer, nullable=True)
    agency_id = Column(Integer, nullable=True)
    order_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
