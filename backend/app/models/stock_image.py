from sqlalchemy import Column, DateTime, Integer, JSON, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class StockImage(Base):
    """Foto de um banco gratuito (Pexels, Unsplash) já vista pelo assistente de IA.

    stored_url é o endereço usado nas páginas: a cópia otimizada no nosso armazenamento
    (Pexels) ou o link oficial (Unsplash, que exige link direto). Fica vazio até a foto
    ser usada pela primeira vez, e a partir daí é reaproveitado sem baixar de novo.
    """

    __tablename__ = "stock_images"
    __table_args__ = (UniqueConstraint("provider", "provider_id", name="uq_stock_image_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), nullable=False)
    provider_id = Column(String(80), nullable=False)
    download_url = Column(String(1000), nullable=False)
    stored_url = Column(String(1000), nullable=True)
    page_url = Column(String(500), nullable=True)
    photographer = Column(String(255), nullable=True)
    photographer_url = Column(String(500), nullable=True)
    alt = Column(String(500), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    # Para escolher melhor: tags e local da foto (ou do fotógrafo) e quando foi publicada.
    tags = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    # Fotos cadastradas à mão no Admin Master (provider "manual"): nome da fonte para o crédito
    # (ex.: "Wikimedia Commons", "Embratur"); o link da fonte fica em page_url.
    source_name = Column(String(120), nullable=True)
    uses = Column(Integer, nullable=False, default=0)
    # Unsplash pede o aviso de uso (download) quando a foto é usada; avisamos uma vez por foto.
    tracked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StockImageSearch(Base):
    """Busca já feita num banco de fotos: os mesmos termos não consultam o banco de novo."""

    __tablename__ = "stock_image_searches"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(200), nullable=False, unique=True, index=True)
    provider = Column(String(20), nullable=True)
    image_ids = Column(JSON, nullable=False, default=list)
    uses = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
