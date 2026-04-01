from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class StripeAccount(Base):
    __tablename__ = "stripe_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    stripe_account_id = Column(String(120), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True)
    country = Column(String(2), nullable=True)
    default_currency = Column(String(3), nullable=True)
    charges_enabled = Column(Boolean, default=False)
    payouts_enabled = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    details_submitted = Column(Boolean, default=False)
    requirements = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="stripe_account")

