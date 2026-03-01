from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan = Column(String(50), nullable=False, default="free")
    provider = Column(String(50), nullable=False, default="asaas")
    preapproval_id = Column(String(120), nullable=True, index=True)
    stripe_customer_id = Column(String(120), nullable=True)
    stripe_subscription_id = Column(String(120), nullable=True, index=True)
    stripe_price_id = Column(String(120), nullable=True)
    asaas_customer_id = Column(String(120), nullable=True)
    asaas_subscription_id = Column(String(120), nullable=True, index=True)
    asaas_payment_link_id = Column(String(120), nullable=True)
    external_reference = Column(String(160), nullable=True)
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    failed_attempts = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
