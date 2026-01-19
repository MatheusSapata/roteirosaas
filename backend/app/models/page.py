from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class PageStatus(str, Enum):  # type: ignore[misc]
    draft = "draft"
    published = "published"


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("page_templates.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default=PageStatus.draft, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    config_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    agency = relationship("Agency", back_populates="pages", foreign_keys=[agency_id])
    template = relationship("PageTemplate", back_populates="pages")
    stats = relationship("PageVisitStats", back_populates="page")
