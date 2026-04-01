from datetime import datetime, date
from enum import Enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SalePaymentStatus(str, Enum):  # type: ignore[misc]
    requires_payment_method = "requires_payment_method"
    requires_action = "requires_action"
    processing = "processing"
    succeeded = "succeeded"
    canceled = "canceled"


class SalePayoutStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    available = "available"
    payout_paid = "payout_paid"
    payout_failed = "payout_failed"


class SalePassengerStatus(str, Enum):  # type: ignore[misc]
    not_started = "not_started"
    partial = "partial"
    completed = "completed"


class SaleFinancialStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    finalized = "finalized"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    page_slug = Column(String(255), nullable=True)
    section_id = Column(String(64), nullable=True)
    price_item_id = Column(String(64), nullable=True)
    product_title = Column(String(255), nullable=False)
    product_description = Column(String(500), nullable=True)
    currency = Column(String(3), nullable=False, default="brl")
    amount = Column(Integer, nullable=False)
    commission_amount = Column(Integer, nullable=False)
    stripe_application_fee_amount = Column(Integer, nullable=False)
    net_amount = Column(Integer, nullable=True)
    stripe_fee_amount = Column(Integer, nullable=True)
    payment_method = Column(String(50), nullable=True)
    installments = Column(Integer, nullable=False, default=1)
    interest_mode = Column(String(20), nullable=False, default="merchant")
    max_installments_no_interest = Column(Integer, nullable=True)
    payment_status = Column(String(50), nullable=False, default=SalePaymentStatus.requires_payment_method.value)
    financial_status = Column(String(50), nullable=False, default=SaleFinancialStatus.pending.value)
    payout_status = Column(String(50), nullable=False, default=SalePayoutStatus.pending.value)
    passenger_status = Column(String(50), nullable=False, default=SalePassengerStatus.not_started.value)
    passengers_required = Column(Integer, nullable=False, default=0)
    passenger_form_token = Column(String(128), nullable=False, unique=True, index=True)
    stripe_payment_intent_id = Column(String(120), nullable=False, unique=True, index=True)
    stripe_charge_id = Column(String(120), nullable=True)
    stripe_balance_transaction_id = Column(String(120), nullable=True)
    stripe_destination_account = Column(String(120), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sales")
    passengers = relationship("SalePassenger", back_populates="sale", cascade="all, delete-orphan")


class SalePassenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    cpf = Column(String(20), nullable=True)
    birthdate = Column(Date, nullable=True)
    phone = Column(String(50), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    boarding_location = Column(String(255), nullable=True)
    extras = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    sale = relationship("Sale", back_populates="passengers")
