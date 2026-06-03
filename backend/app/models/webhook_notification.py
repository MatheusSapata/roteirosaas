from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class WebhookNotificationRule(Base):
    __tablename__ = "webhook_notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    event_key = Column(String(120), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    icon_tag = Column(String(80), nullable=True)
    priority = Column(Integer, nullable=False, default=3, server_default="3")
    topic = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    is_builtin = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
