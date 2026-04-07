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
    pending = "pending"
    processing = "processing"
    paid = "paid"
    canceled = "canceled"
    refunded = "refunded"


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
    page_title = Column(String(255), nullable=True)
    section_id = Column(String(64), nullable=True)
    price_item_id = Column(String(64), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_public_id = Column(String(36), nullable=True, index=True)
    product_title = Column(String(255), nullable=False)
    product_description = Column(String(500), nullable=True)
    currency = Column(String(3), nullable=False, default="brl")
    base_amount = Column(Integer, nullable=False, default=0)
    gross_amount = Column(Integer, nullable=False, default=0)
    platform_fee_amount = Column(Integer, nullable=False, default=0)
    gateway_fee_estimated = Column(Integer, nullable=False, default=0)
    agency_net_amount = Column(Integer, nullable=False, default=0)
    spread_percentage = Column(Integer, nullable=False, default=0)
    amount = Column(Integer, nullable=False)  # legacy total kept for compatibility
    commission_amount = Column(Integer, nullable=False, default=0)  # legacy platform fee
    stripe_application_fee_amount = Column(Integer, nullable=False, default=0)  # legacy fee column
    net_amount = Column(Integer, nullable=True)
    stripe_fee_amount = Column(Integer, nullable=True)
    payment_method = Column(String(50), nullable=True)
    installments = Column(Integer, nullable=False, default=1)
    interest_mode = Column(String(20), nullable=False, default="merchant")
    max_installments_no_interest = Column(Integer, nullable=True)
    payment_status = Column(String(50), nullable=False, default=SalePaymentStatus.pending.value)
    provider_status = Column(String(50), nullable=False, default=SalePaymentStatus.pending.value)
    financial_status = Column(String(50), nullable=False, default=SaleFinancialStatus.pending.value)
    payout_status = Column(String(50), nullable=False, default=SalePayoutStatus.pending.value)
    passenger_status = Column(String(50), nullable=False, default=SalePassengerStatus.not_started.value)
    passengers_required = Column(Integer, nullable=False, default=0)
    channel = Column(String(20), nullable=False, default="page")
    passenger_form_token = Column(String(128), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False, default="blimboo")
    provider_charge_id = Column(String(120), nullable=False, unique=True, index=True)
    provider_metadata = Column(JSONB, nullable=True)
    stripe_payment_intent_id = Column(String(120), nullable=True, index=True)
    stripe_charge_id = Column(String(120), nullable=True)
    stripe_balance_transaction_id = Column(String(120), nullable=True)
    stripe_destination_account = Column(String(120), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sales")
    product = relationship("Product", back_populates="sales")
    passengers = relationship("SalePassenger", back_populates="sale", cascade="all, delete-orphan")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    inventory_events = relationship("ProductInventoryEvent", back_populates="sale", cascade="all, delete-orphan")
    payment_link = relationship("SalePaymentLink", back_populates="sale", uselist=False, cascade="all, delete-orphan")


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
