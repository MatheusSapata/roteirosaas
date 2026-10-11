from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class AgencyMediaArchive(Base):
    """Arquivos de uma empresa inativa movidos para camadas baratas do Azure.

    stage: hot (nada feito ou restaurado) → cool (no cancelamento) → archive (30 dias depois)
    → deleted (só manual). restoring: voltando do Archive (o Azure leva algumas horas).
    blobs guarda os nomes dos arquivos movidos, para restaurar exatamente os mesmos.
    """

    __tablename__ = "agency_media_archives"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), unique=True, nullable=False)
    stage = Column(String(20), nullable=False, default="hot")
    blobs = Column(JSON, nullable=False, default=list)
    files_count = Column(Integer, nullable=False, default=0)
    total_bytes = Column(BigInteger, nullable=False, default=0)
    shared_skipped = Column(Integer, nullable=False, default=0)
    measured_at = Column(DateTime(timezone=True), nullable=True)
    cool_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    restored_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MediaOrphan(Base):
    """Arquivo que nenhum registro usa mais (página excluída, imagem trocada...).

    Margem de segurança: só pode ser excluído quando ficou sem uso em todas as análises por
    30 dias seguidos (first_seen_at) e foi enviado há mais de 30 dias. Se voltar a ser usado
    (desfazer na edição, recolocar na página), sai desta lista.
    """

    __tablename__ = "media_orphans"

    id = Column(Integer, primary_key=True, index=True)
    file_key = Column(String(64), unique=True, nullable=False, index=True)
    names = Column(JSON, nullable=False, default=list)
    total_bytes = Column(BigInteger, nullable=False, default=0)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)
