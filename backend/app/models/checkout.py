from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class CheckoutSettings(Base):
    __tablename__ = "checkout_settings"

    id = Column(Integer, primary_key=True, index=True)
    theme_mode = Column(String(20), nullable=False, default="dark")
    desktop_image_url = Column(String(500), nullable=True)
    mobile_banner_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    offers_json = Column(JSONB, nullable=False, default=list)
    coupons_json = Column(JSONB, nullable=False, default=list)
    checkouts_json = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    offer_key = Column(String(120), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    plan_key = Column(String(50), nullable=False, default="professional")
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="draft", index=True)
    payment_method = Column(String(30), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_document = Column(String(32), nullable=False, index=True)
    customer_phone = Column(String(32), nullable=False)
    customer_zipcode = Column(String(16), nullable=False)
    coupon_code = Column(String(80), nullable=True)
    asaas_customer_id = Column(String(120), nullable=True, index=True)
    asaas_payment_id = Column(String(120), nullable=True, index=True)
    pix_copy_paste = Column(Text, nullable=True)
    pix_qr_code_base64 = Column(Text, nullable=True)
    pix_expiration_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    password_defined_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class CheckoutLead(Base):
    __tablename__ = "checkout_leads"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("checkout_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    offer_key = Column(String(120), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_document = Column(String(32), nullable=False, index=True)
    customer_phone = Column(String(32), nullable=False)
    customer_zipcode = Column(String(16), nullable=False)
    payment_method_selected = Column(String(30), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    password_defined_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("CheckoutSession", foreign_keys=[session_id])


class CheckoutTrackingEvent(Base):
    __tablename__ = "checkout_tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("checkout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(64), nullable=False, index=True)
    offer_key = Column(String(120), nullable=False, index=True)
    event_name = Column(String(80), nullable=False, index=True)
    step = Column(String(40), nullable=True, index=True)
    status = Column(String(40), nullable=True, index=True)
    payment_method = Column(String(30), nullable=True, index=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    ip_country = Column(String(80), nullable=True)
    ip_region = Column(String(120), nullable=True)
    ip_city = Column(String(120), nullable=True)
    ip_timezone = Column(String(120), nullable=True)
    ip_lat = Column(String(30), nullable=True)
    ip_lon = Column(String(30), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    session = relationship("CheckoutSession", foreign_keys=[session_id])
