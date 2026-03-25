from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class LeadStatus(Base):
  __tablename__ = "lead_statuses"

  id = Column(Integer, primary_key=True, index=True)
  agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
  name = Column(String(120), nullable=False)
  color = Column(String(20), nullable=False, server_default="#E2E8F0")
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

  submissions = relationship("LeadFormSubmission", back_populates="status")


class LeadForm(Base):
  __tablename__ = "lead_forms"

  id = Column(Integer, primary_key=True, index=True)
  agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
  name = Column(String(255), nullable=False)
  title = Column(String(255), nullable=False)
  subtitle = Column(String(1000), nullable=True)
  button_label = Column(String(120), nullable=False)
  button_color = Column(String(50), nullable=True)
  fields = Column(JSONB, nullable=False)
  default_status_id = Column(Integer, ForeignKey("lead_statuses.id", ondelete="SET NULL"), nullable=True, index=True)
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

  agency = relationship("Agency", back_populates="lead_forms")
  default_status = relationship("LeadStatus")
  submissions = relationship(
    "LeadFormSubmission",
    back_populates="form",
    cascade="all, delete-orphan",
    passive_deletes=True,
  )


class LeadFormSubmission(Base):
  __tablename__ = "lead_form_submissions"

  id = Column(Integer, primary_key=True, index=True)
  agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
  form_id = Column(Integer, ForeignKey("lead_forms.id", ondelete="CASCADE"), nullable=False, index=True)
  page_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True)
  page_title = Column(String(255), nullable=True)
  page_slug = Column(String(255), nullable=True)
  page_url = Column(String(500), nullable=True)
  name = Column(String(255), nullable=True)
  phone = Column(String(50), nullable=True)
  email = Column(String(255), nullable=True)
  city = Column(String(255), nullable=True)
  payload = Column(JSONB, nullable=False)
  source = Column(String(255), nullable=True)
  status_id = Column(Integer, ForeignKey("lead_statuses.id", ondelete="SET NULL"), nullable=True, index=True)
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  fingerprint_hash = Column(String(128), nullable=True, index=True)

  form = relationship("LeadForm", back_populates="submissions")
  status = relationship("LeadStatus", back_populates="submissions")
