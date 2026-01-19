from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class PageVisitStats(Base):
    __tablename__ = "page_visit_stats"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    visits = Column(Integer, default=0, nullable=False)
    clicks_whatsapp = Column(Integer, default=0, nullable=False)
    clicks_cta = Column(Integer, default=0, nullable=False)

    page = relationship("Page", back_populates="stats")
