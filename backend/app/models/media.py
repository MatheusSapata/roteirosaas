from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, default="image")
    original_file_name = Column(String(255), nullable=True)
    # Fotos tiradas de um PDF enviado ao assistente: palavras do texto da página de onde saíram,
    # para a busca de fotos da própria agência achar depois. Só desta agência (não é o banco comum).
    keywords = Column(Text, nullable=True)
    source = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    agency = relationship("Agency", back_populates="media")
