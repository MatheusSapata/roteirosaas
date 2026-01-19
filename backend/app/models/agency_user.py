from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgencyUser(Base):
    __tablename__ = "agency_users"
    __table_args__ = (UniqueConstraint("agency_id", "user_id", name="uq_agency_user"),)

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False, default="editor")

    agency = relationship("Agency", back_populates="users")
    user = relationship("User", back_populates="agencies")
