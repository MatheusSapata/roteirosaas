from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class CaktoEventLog(Base):
    __tablename__ = "cakto_event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), unique=True, nullable=True)
    event_type = Column(String(120), nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class CaktoOnboardingToken(Base):
    __tablename__ = "cakto_onboarding_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    order_id = Column(String(255), index=True, nullable=True)
    order_ref = Column(String(255), index=True, nullable=True)
    subscription_code = Column(String(255), index=True, nullable=True)
    offer_id = Column(String(255), nullable=True)
    plan_key = Column(String(50), nullable=False)
    billing_cycle = Column(String(20), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", backref="cakto_onboarding_tokens")


class CaktoCheckoutSession(Base):
    __tablename__ = "cakto_checkout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    plan_key = Column(String(50), nullable=False)
    cycle = Column(String(20), nullable=False)
    checkout_url = Column(String(512), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    order_id = Column(String(255), nullable=True)
    order_ref = Column(String(255), nullable=True)
    onboarding_token_id = Column(Integer, ForeignKey("cakto_onboarding_tokens.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    onboarding_token = relationship("CaktoOnboardingToken")
