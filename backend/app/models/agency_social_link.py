from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgencySocialLink(Base):
    __tablename__ = "agency_social_links"
    __table_args__ = (UniqueConstraint("agency_id", "network", name="uq_agency_social_network"),)

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    network = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)

    agency = relationship("Agency", back_populates="social_links")

