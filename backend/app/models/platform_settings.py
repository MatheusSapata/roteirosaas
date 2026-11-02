"""Configurações da plataforma editadas em Admin master › Marca e SEO e › E-mails do sistema.

Uma linha só (id = 1). Campo vazio = vale o padrão do código (logo, favicon e textos de hoje).
"""
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id = Column(Integer, primary_key=True)
    # Marca
    logo_url = Column(String(1000), nullable=True)  # logo colorido, para fundo claro
    logo_dark_url = Column(String(1000), nullable=True)  # logo branco, para fundo escuro
    favicon_url = Column(String(1000), nullable=True)
    email_logo_url = Column(String(1000), nullable=True)  # logo da faixa verde dos e-mails
    # SEO das telas da plataforma (login, painel, checkout)
    site_title = Column(String(120), nullable=True)
    site_description = Column(Text, nullable=True)
    share_image_url = Column(String(1000), nullable=True)
    theme_color = Column(String(20), nullable=True)
    # {"chave do e-mail": {"subject": str, "eyebrow": str, "title": str, "body": str, "button_label": str, "note": str}}
    email_templates_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
