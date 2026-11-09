from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PageTemplate(Base):
    __tablename__ = "page_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=False)
    is_default = Column(Boolean, default=False)
    config_json = Column(JSONB, nullable=False)
    # Vazio = modelo da plataforma (visível para todos). Preenchido = modelo salvo pelo
    # cliente no editor ("Salvar como template"), visível só para a própria agência.
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    pages = relationship("Page", back_populates="template")
