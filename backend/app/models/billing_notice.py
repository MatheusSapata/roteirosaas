"""Avisos de cobrança enviados aos clientes (e-mail e WhatsApp).

- billing_notice_settings: uma linha só (id = 1) com a configuração da tela Admin master › Avisos de
  cobrança.
- billing_notice_sends: um registro por fatura, etapa e canal. A chave única é a trava contra envio em
  dobro: o envio reserva a linha antes de sair.
"""
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class BillingNoticeSettings(Base):
    __tablename__ = "billing_notice_settings"

    id = Column(Integer, primary_key=True)
    # Chave geral: desligada, nada sai para os clientes (a prévia continua funcionando).
    enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    # Conexão de WhatsApp (Admin master › WhatsApp) que envia as mensagens.
    whatsapp_connection_id = Column(
        Integer, ForeignKey("whatsapp_connections.id", ondelete="SET NULL"), nullable=True
    )
    # "Fatura disponível" sai quando faltam até estes dias para o vencimento.
    available_lead_days = Column(Integer, nullable=False, default=10, server_default="10")
    # Avisos do próprio Asaas (e-mail e SMS das faturas). Ligados até alguém desligar na tela.
    asaas_notifications_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    # {"etapa": {"email": bool, "whatsapp": bool}}
    steps_json = Column(JSON, nullable=True)
    # {"etapa": {"whatsapp": str, "email_subject": str, "email_body": str}}; vazio = texto padrão.
    templates_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BillingNoticeSend(Base):
    __tablename__ = "billing_notice_sends"
    __table_args__ = (UniqueConstraint("payment_id", "step", "channel", name="uq_billing_notice_send"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_id = Column(String(80), nullable=False, index=True)
    step = Column(String(40), nullable=False)
    channel = Column(String(20), nullable=False)
    # sending, sent, failed ou cancelled (cancelado na tela antes de sair).
    status = Column(String(20), nullable=False, index=True)
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    recipient = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    # Dados usados no texto (nome, valor, vencimento, link): permitem tentar de novo igual.
    context_json = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
