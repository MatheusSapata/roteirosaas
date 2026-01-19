from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True)
    whatsapp = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    plan = Column(String(50), nullable=False, server_default="free")
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    trial_plan = Column(String(50), nullable=True)
    trial_original_plan = Column(String(50), nullable=True)
    trial_started_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_ack_start = Column(Boolean, default=False)
    trial_ack_end = Column(Boolean, default=False)

    agencies = relationship("AgencyUser", back_populates="user")
    subscription = relationship("Subscription", uselist=False, foreign_keys=[subscription_id])
    pixels = relationship("Pixel", back_populates="user", cascade="all, delete-orphan")
