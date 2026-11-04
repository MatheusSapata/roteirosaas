"""Registros que aparecem na página da empresa no Admin Master.

- admin_action_logs: o que alguém do Admin Master fez na conta (plano, situação, validade, teste,
  cancelamento, reembolso). Quem fez, quando e o antes/depois.
- email_logs: cada e-mail que o sistema mandou (ou tentou mandar), com assunto e resultado. Os avisos
  de cobrança têm o registro próprio (billing_notice_sends) e não entram aqui.

Sem chave estrangeira de propósito: o registro fica mesmo se a conta for apagada.
"""
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    target_user_id = Column(Integer, nullable=True, index=True)
    actor_user_id = Column(Integer, nullable=True)
    actor_name = Column(String(255), nullable=True)
    action = Column(String(60), nullable=False)
    summary = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    # Chave do e-mail do sistema (boas_vindas_checkout, redefinir_senha...) ou vazio.
    kind = Column(String(60), nullable=True)
    # sent, failed ou not_configured (SMTP sem configuração: não saiu).
    status = Column(String(20), nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
