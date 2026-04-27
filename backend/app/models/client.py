from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    cpf = Column(String(20), nullable=True)
    cpf_normalized = Column(String(11), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    phone_normalized = Column(String(20), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    email_normalized = Column(String(255), nullable=True, index=True)
    city = Column(String(255), nullable=True)
    zipcode = Column(String(10), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(50), nullable=True)
    complement = Column(String(255), nullable=True)
    neighborhood = Column(String(255), nullable=True)
    state = Column(String(2), nullable=True)
    birthdate = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    opportunities = relationship("LeadFormSubmission", back_populates="client")
    client_notes = relationship(
        "ClientNote",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    documents = relationship(
        "Document",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
