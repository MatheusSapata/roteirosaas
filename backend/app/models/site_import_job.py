from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class SiteImportJob(Base):
    """Importação do site inteiro de uma agência a partir da página principal (home) colada no
    assistente de IA. Cada viagem achada na home vira uma página; no fim, a home é montada na
    página onde a conversa aconteceu (page_id), com os cards ligados às páginas novas.

    Os itens (uma viagem cada, no máximo 20) ficam numa coluna JSONB, e não numa tabela à parte:
    são sempre lidos e gravados juntos, só a thread do job escreve neles (uma de cada vez) e
    ninguém consulta um item sozinho. Formato de cada item em ``items``:
    {"url", "card_title", "price", "category", "position", "title", "stage", "page_id", "slug", "error"}.
    """

    __tablename__ = "site_import_jobs"
    __table_args__ = (
        Index("ix_site_import_jobs_agency_status", "agency_id", "status"),
        # No máximo uma importação completa rodando por agência, garantido pelo banco (duas
        # confirmações ao mesmo tempo não disparam dois jobs).
        Index(
            "uq_site_import_jobs_running_agency",
            "agency_id",
            unique=True,
            postgresql_where=text("status = 'running'"),
            sqlite_where=text("status = 'running'"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    # Página onde a pessoa colou o link: recebe a home no fim.
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    source_url = Column(String(2000), nullable=False)
    source_title = Column(String(255), nullable=True)
    # awaiting_confirmation (pergunta feita no chat) | awaiting_categories (pergunta das categorias,
    # depois do "completo") | running | completed | failed
    status = Column(String(30), nullable=False, default="awaiting_confirmation", server_default="awaiting_confirmation")
    # Resposta à pergunta das categorias: True = cada categoria do site vira uma tag e a home ganha
    # uma seção por categoria; False = tudo numa vitrine só; None = o site não tinha categorias.
    preserve_categories = Column(Boolean, nullable=True)
    # Etapa do job em andamento: "pages" (páginas das viagens) ou "home" (página principal).
    stage = Column(String(20), nullable=True)
    home_stage = Column(String(20), nullable=True)
    include_images = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    # Quantos links de viagem a home tinha (pode passar do teto; items guarda só os primeiros).
    total_found = Column(Integer, nullable=False, default=0, server_default=text("0"))
    items = Column(JSONB, nullable=False, default=list)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    # Atualizado a cada passo: job "running" parado há muito tempo (container reiniciado) vira erro.
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
