from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class PageTemplate(Base):
    __tablename__ = "page_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=False)
    is_default = Column(Boolean, default=False)
    config_json = Column(JSONB, nullable=False)

    pages = relationship("Page", back_populates="template")
