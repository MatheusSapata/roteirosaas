from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Integer, Numeric

from app.db.base import Base


class RevenueTotal(Base):
    __tablename__ = "total_revenue"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
