"""Renovação dos planos antigos (Profissional, Agência e Escala) pelo mesmo valor que o cliente pagava.

Quem já assinava antes do plano único (vendido desde 14/10/2026) renova no plano e no valor que
tinha. O valor de cada cliente fica em subscriptions.legacy_renewal_amount, preenchido uma vez pelo
SQL de backend/sql/2026-10-15_legacy_renewal_amount.sql (a regra está lá).
O cliente nunca envia valor: a sessão do checkout é montada aqui, a partir do banco.

Profissional e Agência que renovam pela tela também podem fazer upgrade para o plano único (oferta
mensal ou anual do Admin Master), no valor cheio e sem a promoção da 1ª mensalidade. Depois do
upgrade pago o cliente deixa de ser legado: o checkout apaga legacy_renewal_amount.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.checkout import CheckoutOfferOut
from app.services.company_status import ENDED_STATUSES

# Corte: assinaturas criadas antes de 15/10/2026 00:00 em Brasília são dos planos antigos.
LEGACY_CUTOFF = datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc)
LEGACY_PLANS = frozenset({"professional", "essencial", "agency", "growth", "scale", "infinity"})
# Renovam pela tela (a Cakto é convertida para o Asaas na renovação).
PANEL_RENEWAL_PROVIDERS = frozenset({"asaas", "cakto"})
# Oferta "virtual" da renovação: não existe no Admin Master, então não aceita cupom nem promoção.
LEGACY_RENEWAL_OFFER_KEY = "renovacao-assinatura"
# Planos antigos que podem fazer upgrade para o plano único (o Escala antigo só renova).
LEGACY_UPGRADE_PLANS = frozenset({"professional", "essencial", "agency", "growth"})

PLAN_NAMES = {
    "professional": "Profissional",
    "essencial": "Profissional",
    "agency": "Agência",
    "growth": "Agência",
    "scale": "Escala",
    "infinity": "Escala",
}

# panel: renova pela tela. external: a cobrança é de outro canal (ViajeOn, manual, Stripe ou a
# Cakto ainda cobrando). support: plano antigo sem valor conhecido; renova falando com o suporte.
LegacyRenewalMode = Literal["panel", "external", "support"]


@dataclass(frozen=True)
class LegacyRenewalInfo:
    legacy: bool = False
    amount: Decimal | None = None
    mode: LegacyRenewalMode | None = None

    @property
    def managed_externally(self) -> bool:
        return self.mode == "external"


NOT_LEGACY = LegacyRenewalInfo()


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _created_before_cutoff(subscription: Subscription) -> bool:
    created = _aware(subscription.created_at)
    return created is not None and created < LEGACY_CUTOFF


def _positive(value: object) -> Decimal | None:
    try:
        amount = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None
    return amount if amount > 0 else None


def legacy_plan_name(plan: str | None) -> str:
    return PLAN_NAMES.get(str(plan or "").strip().lower(), "")


def legacy_renewal_info(subscription: Subscription | None) -> LegacyRenewalInfo:
    """Se a assinatura é de plano antigo e como ela renova. Decidido só com dados do banco."""
    if subscription is None:
        return NOT_LEGACY
    plan = str(subscription.plan or "").strip().lower()
    if plan not in LEGACY_PLANS:
        return NOT_LEGACY
    provider = str(subscription.provider or "").strip().lower()
    amount = _positive(subscription.legacy_renewal_amount)
    status = str(subscription.status or "").strip().lower()

    if provider == "asaas":
        # Sem valor: não é cliente pagante dos planos antigos; segue como hoje.
        return LegacyRenewalInfo(True, amount, "panel") if amount is not None else NOT_LEGACY
    if provider == "cakto":
        if not _created_before_cutoff(subscription):
            return NOT_LEGACY
        if amount is None:
            return LegacyRenewalInfo(True, None, "support")
        # Enquanto a Cakto ainda cobra (ativa, em atraso ou cancelando no fim do ciclo), renovar no
        # Asaas cobraria duas vezes. Só renova pela tela quando a assinatura da Cakto já terminou.
        if status in ENDED_STATUSES:
            return LegacyRenewalInfo(True, amount, "panel")
        return LegacyRenewalInfo(True, amount, "external")
    # ViajeOn, manual, Stripe e outros: a cobrança é de fora. Contas sem valor (teste e contas
    # administrativas com mrr 0) seguem como hoje.
    if _positive(subscription.mrr_amount) is None:
        return NOT_LEGACY
    return LegacyRenewalInfo(True, None, "external")


def build_legacy_renewal_offer(subscription: Subscription, amount: Decimal) -> CheckoutOfferOut:
    plan = str(subscription.plan or "").strip().lower()
    name = legacy_plan_name(plan)
    cycle = "annual" if str(subscription.billing_cycle or "").strip().lower() == "annual" else "monthly"
    return CheckoutOfferOut(
        key=LEGACY_RENEWAL_OFFER_KEY,
        title=f"Renovação do plano {name}",
        footer_product_label=f"Plano {name}",
        plan_key=plan,
        billing_cycle=cycle,
        amount=amount,
        active=True,
        # À vista: o valor cobrado é exatamente o que o cliente pagava (parcelar somaria as taxas).
        max_installments=1,
        first_payment_amount=None,
    )


def require_panel_renewal(user: User) -> tuple[Subscription, Decimal]:
    subscription = user.subscription
    info = legacy_renewal_info(subscription)
    if not info.legacy:
        raise HTTPException(status_code=403, detail="Sua assinatura não tem renovação pelo plano antigo.")
    if info.mode != "panel" or info.amount is None or subscription is None:
        raise HTTPException(
            status_code=400,
            detail="A renovação da sua assinatura é gerida pelo local onde ela foi contratada.",
        )
    return subscription, info.amount


def legacy_renewal_offer_for_user(user: User) -> CheckoutOfferOut:
    subscription, amount = require_panel_renewal(user)
    return build_legacy_renewal_offer(subscription, amount)


def create_legacy_renewal_checkout_session(db: Session, user: User) -> CheckoutSession:
    """Sessão de checkout da renovação: plano, ciclo e valor da assinatura atual, sem cupom e sem
    promoção. Usa o fluxo de upgrade (cartão e Pix automático), que cria o contrato novo no Asaas e
    encerra o anterior depois do pagamento."""
    from app.services.checkout import create_upgrade_checkout_session

    subscription, amount = require_panel_renewal(user)
    offer = build_legacy_renewal_offer(subscription, amount)
    return create_upgrade_checkout_session(
        db,
        offer=offer,
        user=user,
        coupon_code=None,
        plan_key=str(subscription.plan or "").strip().lower(),
        extra_metadata={
            "legacy_renewal": True,
            "first_subscription": False,
            "legacy_previous_provider": str(subscription.provider or "").strip().lower(),
        },
    )


def is_legacy_renewal_session(session: CheckoutSession) -> bool:
    return bool((session.metadata_json or {}).get("legacy_renewal"))


# ---------------------------------------------------------------- upgrade para o plano único


def legacy_upgrade_available(subscription: Subscription | None) -> bool:
    """Profissional ou Agência dos planos antigos que renova pela tela pode fazer upgrade para o
    plano único. Escala antigo, cobrança de fora (external) e sem valor (support) não."""
    if subscription is None:
        return False
    info = legacy_renewal_info(subscription)
    plan = str(subscription.plan or "").strip().lower()
    return info.legacy and info.mode == "panel" and info.amount is not None and plan in LEGACY_UPGRADE_PLANS


def require_legacy_upgrade(user: User) -> Subscription:
    subscription = user.subscription
    if not legacy_renewal_info(subscription).legacy:
        raise HTTPException(status_code=403, detail="Sua assinatura não tem upgrade pelo plano antigo.")
    if not legacy_upgrade_available(subscription) or subscription is None:
        raise HTTPException(status_code=400, detail="O upgrade não está disponível para a sua assinatura.")
    return subscription


def create_legacy_upgrade_checkout_session(db: Session, user: User, billing_cycle: str) -> CheckoutSession:
    """Upgrade de Profissional ou Agência antigo para o plano único: a oferta é a ativa do Admin
    Master para o ciclo escolhido (mensal ou anual), no valor cheio, sem cupom e sem a promoção da
    1ª mensalidade. Segue o fluxo de upgrade (contrato novo no Asaas, o anterior é encerrado depois
    do pagamento e a nova validade conta a partir do pagamento)."""
    from app.services.checkout import create_upgrade_checkout_session, get_public_sales_plan, resolve_offer

    subscription = require_legacy_upgrade(user)
    cycle = str(billing_cycle or "").strip().lower()
    if cycle not in {"monthly", "annual"}:
        raise HTTPException(status_code=400, detail="Escolha o pagamento mensal ou anual.")
    chosen = get_public_sales_plan(db).get(cycle)
    if not chosen:
        raise HTTPException(status_code=404, detail="O plano não está disponível no momento. Fale com o suporte.")
    offer = resolve_offer(db, chosen["key"])
    return create_upgrade_checkout_session(
        db,
        offer=offer,
        user=user,
        coupon_code=None,
        extra_metadata={
            "legacy_upgrade": True,
            "first_subscription": False,
            "legacy_previous_plan": str(subscription.plan or "").strip().lower(),
            "legacy_previous_provider": str(subscription.provider or "").strip().lower(),
            "legacy_previous_amount": str(legacy_renewal_info(subscription).amount),
        },
    )
