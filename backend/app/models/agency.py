from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(50), nullable=True)
    secondary_color = Column(String(50), nullable=True)
    cta_whatsapp = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    default_page_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)

    users = relationship("AgencyUser", back_populates="agency")
    pages = relationship("Page", back_populates="agency", foreign_keys="Page.agency_id")
    media = relationship("MediaAsset", back_populates="agency")
    social_links = relationship("AgencySocialLink", back_populates="agency", cascade="all, delete-orphan")
    default_page = relationship("Page", foreign_keys=[default_page_id], post_update=True)
    domains = relationship(
        "AgencyDomain",
        back_populates="agency",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    lead_forms = relationship(
        "LeadForm",
        back_populates="agency",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
