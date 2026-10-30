from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Uma página pode ter várias tags e uma tag pode estar em várias páginas.
page_tag_links = Table(
    "page_tag_links",
    Base.metadata,
    Column("page_id", Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("page_tags.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class PageTag(Base):
    """Tag de páginas de uma agência: organiza a lista e alimenta a seção Links/Roteiros por tag."""

    __tablename__ = "page_tags"
    __table_args__ = (UniqueConstraint("agency_id", "slug", name="uq_page_tags_agency_slug"),)

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(60), nullable=False)
    slug = Column(String(80), nullable=False)
    color = Column(String(20), nullable=False, default="blue")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pages = relationship("Page", secondary=page_tag_links, back_populates="tags")
