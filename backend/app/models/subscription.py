from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan = Column(String(50), nullable=False, default="free")
    provider = Column(String(50), nullable=False, default="asaas")
    preapproval_id = Column(String(120), nullable=True, index=True)
    stripe_customer_id = Column(String(120), nullable=True)
    stripe_subscription_id = Column(String(120), nullable=True, index=True)
    stripe_price_id = Column(String(120), nullable=True)
    asaas_customer_id = Column(String(120), nullable=True)
    asaas_subscription_id = Column(String(120), nullable=True, index=True)
    asaas_payment_link_id = Column(String(120), nullable=True)
    payment_method_type = Column(String(30), nullable=True)
    card_brand = Column(String(40), nullable=True)
    card_last4 = Column(String(8), nullable=True)
    cakto_customer_code = Column(String(120), nullable=True)
    cakto_subscription_code = Column(String(120), nullable=True, index=True)
    cakto_order_id = Column(String(120), nullable=True, index=True)
    cakto_offer_id = Column(String(120), nullable=True)
    external_reference = Column(String(160), nullable=True)
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    failed_attempts = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")
    valid_until = Column(DateTime(timezone=True), nullable=True)
    mrr_amount = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    # Quando a conta deixou de estar no ar (página pública indisponível). Registrado pelo job
    # horário; para quem já estava inativo antes, é estimado (deactivation_estimated).
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivation_estimated = Column(Boolean, nullable=False, default=False, server_default="false")
    # Valor da renovação (por ciclo: mensal = do mês, anual = do ano) de quem já assinava um plano
    # antigo antes do plano único. Preenchido uma vez por backend/sql/2026-10-15_legacy_renewal_amount.sql
    # e nunca alterado pelo pagamento. Vazio = não renova pelo valor antigo.
    legacy_renewal_amount = Column(Numeric(12, 2), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
