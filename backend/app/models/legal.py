from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class LegalContractStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    generated = "generated"
    failed = "failed"


class LegalContractSignatureStatus(str, Enum):  # type: ignore[misc]
    pending = "pending"
    signed = "signed"


class LegalContractSignatureType(str, Enum):  # type: ignore[misc]
    typed = "typed"
    drawn = "drawn"


class LegalSignatureProfile(Base):
    __tablename__ = "legal_signature_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_legal_signature_user"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    signature_type = Column(String(20), nullable=False)
    drawn_image_url = Column(String(500), nullable=True)
    drawn_image_data = Column(Text, nullable=True)
    typed_value = Column(String(255), nullable=True)
    font_style = Column(String(50), nullable=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="legal_signature_profile")
    agency = relationship("Agency")


class LegalContractTemplate(Base):
    __tablename__ = "legal_contract_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="legal_contract_templates")
    agency = relationship("Agency", back_populates="legal_contract_templates")
    products = relationship("Product", back_populates="template_contract")
    contracts = relationship("LegalContract", back_populates="template")


class LegalContract(Base):
    __tablename__ = "legal_contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    template_id = Column(Integer, ForeignKey("legal_contract_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    buyer_name = Column(String(255), nullable=False)
    product_name = Column(String(255), nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    total_amount = Column(Integer, nullable=False, default=0)
    pdf_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default=LegalContractStatus.pending.value)
    last_error = Column(String(1000), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    signature_status = Column(
        String(20),
        nullable=False,
        default=LegalContractSignatureStatus.pending.value,
    )
    signature_token = Column(String(120), nullable=True, unique=True, index=True)
    signature_link = Column(String(500), nullable=True)
    signature_signed_at = Column(DateTime(timezone=True), nullable=True)
    signature_name = Column(String(255), nullable=True)
    signature_type = Column(String(20), nullable=True)
    signature_image_url = Column(String(500), nullable=True)
    signature_image_data = Column(Text, nullable=True)
    signature_ip = Column(String(100), nullable=True)
    signature_user_agent = Column(String(500), nullable=True)
    signed_pdf_url = Column(String(500), nullable=True)
    signed_pdf_generated_at = Column(DateTime(timezone=True), nullable=True)
    signed_pdf_size_bytes = Column(BigInteger, nullable=True)
    document_hash = Column(String(128), nullable=True)
    document_hash_algorithm = Column(String(50), nullable=True, default="sha256")
    verification_token = Column(String(120), nullable=True, unique=True, index=True)
    verification_url = Column(String(500), nullable=True)
    verification_qr_image_data = Column(Text, nullable=True)
    verification_generated_at = Column(DateTime(timezone=True), nullable=True)
    agency_signature_status = Column(String(20), nullable=False, default=LegalContractSignatureStatus.pending.value)
    agency_signature_signed_at = Column(DateTime(timezone=True), nullable=True)
    agency_signature_type = Column(String(20), nullable=True)
    agency_signature_name = Column(String(255), nullable=True)
    agency_signature_role = Column(String(255), nullable=True)
    agency_signature_company = Column(String(255), nullable=True)
    agency_signature_city = Column(String(255), nullable=True)
    agency_signature_font_style = Column(String(50), nullable=True)
    agency_signature_typed_value = Column(String(255), nullable=True)
    agency_signature_image_url = Column(String(500), nullable=True)
    agency_signature_image_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="legal_contracts")
    agency = relationship("Agency", back_populates="legal_contracts")
    sale = relationship("Sale", back_populates="contract")
    template = relationship("LegalContractTemplate", back_populates="contracts")


class LegalContractAuditEventType(str, Enum):  # type: ignore[misc]
    contract_created = "contract_created"
    agency_signature_applied = "agency_signature_applied"
    signature_link_created = "signature_link_created"
    signer_opened = "signer_opened"
    customer_signed = "customer_signed"
    signed_pdf_generated = "signed_pdf_generated"
    document_hashed = "document_hashed"
    verification_published = "verification_published"
    qr_generated = "qr_generated"
    verification_regenerated = "verification_regenerated"


class LegalContractAuditActorType(str, Enum):  # type: ignore[misc]
    system = "system"
    customer = "customer"
    agency = "agency"


class LegalContractAuditEvent(Base):
    __tablename__ = "legal_contract_audit_events"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("legal_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    actor_type = Column(String(20), nullable=False, default=LegalContractAuditActorType.system.value)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    metadata_json = Column(JSONB, nullable=True)
    is_reconstructed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("LegalContract", backref="audit_events")
