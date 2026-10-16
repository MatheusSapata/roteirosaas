from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class PushoverAccount(Base):
    """Conta do Pushover que recebe os avisos do Admin Master (uma por pessoa, sem Pushover Teams).
    A chave do usuário e o token do aplicativo ficam criptografados; a tela só vê o final deles."""

    __tablename__ = "pushover_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    user_key_encrypted = Column(Text, nullable=False)
    user_key_last4 = Column(String(8), nullable=False, default="")
    app_token_encrypted = Column(Text, nullable=False)
    app_token_last4 = Column(String(8), nullable=False, default="")
    # Aparelho específico da conta (vazio: todos os aparelhos dela).
    device = Column(String(60), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    # Eventos (event_key das regras) que esta conta recebe.
    event_keys = Column(JSON, nullable=False, default=list)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
