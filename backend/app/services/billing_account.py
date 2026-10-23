"""Situação de cobrança da conta: fatura que libera o acesso, dívida real, oferta de renovação e
Pix Automático.

Marcas de pagamento ficam em asaas_event_logs (event_id único), sem tabela nova:
- applied:<id>  : o pagamento já mexeu na conta (acesso e receita); webhook e conferência manual não repetem.
- replaced:<id> : cobrança cancelada no Asaas porque outra a substituiu (renovação, nova autorização).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.asaas import AsaasEventLog
from app.models.checkout import CheckoutSession
from app.models.user import User
from app.services.asaas import AsaasAPIError, AsaasClient

APPLIED_PREFIX = "applied:"
REPLACED_PREFIX = "replaced:"
PAID_PAYMENT_STATUSES = frozenset({"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"})
OPEN_PAYMENT_STATUSES = ("PENDING", "OVERDUE")


# ---------------------------------------------------------------- marcas de pagamento


def _mark(db: Session, event_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    if db.query(AsaasEventLog.id).filter(AsaasEventLog.event_id == event_id).first():
        return False
    db.add(
        AsaasEventLog(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status="processed",
            processed_at=datetime.utcnow(),
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False
    return True


def mark_event_once(db: Session, event_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    """Marca um fato em asaas_event_logs; False quando já estava marcado."""
    return _mark(db, event_id, event_type, payload)


def payment_applied(db: Session, payment_id: str | None) -> bool:
    if not payment_id:
        return False
    return db.query(AsaasEventLog.id).filter(AsaasEventLog.event_id == f"{APPLIED_PREFIX}{payment_id}").first() is not None


def mark_payment_applied(db: Session, payment_id: str | None, event: str) -> bool:
    """True quando esta chamada foi a primeira a marcar (quem recebe False não repete o efeito)."""
    if not payment_id:
        return False
    return _mark(db, f"{APPLIED_PREFIX}{payment_id}", "PAYMENT_APPLIED", {"payment_id": payment_id, "event": event})


def mark_payment_replaced(db: Session, payment_id: str, *, reason: str, replaced_by: str | None = None) -> bool:
    return _mark(
        db,
        f"{REPLACED_PREFIX}{payment_id}",
        "PAYMENT_REPLACED",
        {"payment_id": payment_id, "reason": reason, "replaced_by": replaced_by},
    )


def replaced_payment_ids(db: Session, payment_ids: Iterable[str]) -> set[str]:
    ids = [item for item in payment_ids if item]
    if not ids:
        return set()
    keys = {f"{REPLACED_PREFIX}{item}": item for item in ids}
    rows = db.query(AsaasEventLog.event_id).filter(AsaasEventLog.event_id.in_(list(keys))).all()
    return {keys[row[0]] for row in rows if row[0] in keys}


def is_paid_payment(payment: dict[str, Any]) -> bool:
    return str(payment.get("status") or "").strip().upper() in PAID_PAYMENT_STATUSES


# ---------------------------------------------------------------- período coberto


def parse_date(value: Any) -> date | None:
    raw = str(value or "").strip()[:10]
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def add_months(base: date, months: int) -> date:
    index = base.month - 1 + months
    year = base.year + index // 12
    month = index % 12 + 1
    return date(year, month, min(base.day, calendar.monthrange(year, month)[1]))


def covered_period(due: date | None, cycle: str | None) -> tuple[date, date] | None:
    """Período que a fatura cobre: do vencimento até um ciclo depois (o fim não entra)."""
    if due is None:
        return None
    months = 12 if str(cycle or "").strip().lower() == "annual" else 1
    return due, add_months(due, months)


def covered_by_paid(due: date | None, paid_periods: list[tuple[date, date]]) -> bool:
    """Fatura em aberto de um período que outra fatura paga já cobre."""
    if due is None:
        return False
    return any(start <= due < end for start, end in paid_periods)


# ---------------------------------------------------------------- oferta do contrato


@dataclass(frozen=True)
class ContractOffer:
    plan_key: str
    billing_cycle: str
    amount: Decimal
    title: str


def _decimal(value: Any) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None
    return parsed if parsed > 0 else None


def current_contract_offer(db: Session, user: User) -> ContractOffer | None:
    """Plano, ciclo e valor do contrato do cliente, a partir do banco: nunca a vitrine do momento e
    nunca a tabela antiga.

    Planos antigos usam o valor gravado em legacy_renewal_amount. Os demais, o valor cheio do último
    checkout pago (sem cupom e sem a promoção da 1ª mensalidade); sem checkout, o valor da assinatura.
    """
    from app.services.legacy_renewal import legacy_plan_name, legacy_renewal_info

    subscription = user.subscription
    if subscription is None:
        return None
    plan = str(subscription.plan or "").strip().lower()
    if not plan or plan in {"free", "trial", "teste", "test"}:
        return None
    cycle = "annual" if str(subscription.billing_cycle or "").strip().lower() == "annual" else "monthly"

    legacy = legacy_renewal_info(subscription)
    if legacy.legacy and legacy.amount is not None:
        name = legacy_plan_name(plan) or plan.title()
        return ContractOffer(plan, cycle, legacy.amount, f"Renovação do plano {name}")

    last_paid = (
        db.query(CheckoutSession)
        .filter(CheckoutSession.user_id == user.id, CheckoutSession.status == "paid")
        .order_by(CheckoutSession.paid_at.desc().nullslast(), CheckoutSession.id.desc())
        .first()
    )
    if last_paid is not None:
        metadata = dict(last_paid.metadata_json or {})
        amount = _decimal(metadata.get("original_amount")) or _decimal(last_paid.amount)
        if amount is not None:
            return ContractOffer(
                str(last_paid.plan_key or plan).strip().lower() or plan,
                "annual" if str(last_paid.billing_cycle or "").strip().lower() == "annual" else "monthly",
                amount,
                str(last_paid.product_name or "").strip() or "Renovação da assinatura",
            )

    mrr = _decimal(subscription.mrr_amount)
    if mrr is None:
        return None
    amount = mrr * 12 if cycle == "annual" else mrr
    return ContractOffer(plan, cycle, amount.quantize(Decimal("0.01")), "Renovação da assinatura")


# ---------------------------------------------------------------- Pix Automático


def pix_automatic_status(db: Session, user: User) -> str | None:
    """ACTIVE, CANCELLED, EXPIRED ou REFUSED para quem paga por Pix Automático; None nos demais."""
    subscription = user.subscription
    if subscription is None or str(subscription.payment_method_type or "").strip().lower() != "pix":
        return None
    rows = (
        db.query(CheckoutSession)
        .filter(
            CheckoutSession.user_id == user.id,
            CheckoutSession.payment_method == "pix",
            CheckoutSession.metadata_json.isnot(None),
        )
        .order_by(CheckoutSession.created_at.desc(), CheckoutSession.id.desc())
        .all()
    )
    for row in rows:
        metadata = dict(row.metadata_json or {})
        if str(metadata.get("pix_mode") or "").strip().lower() != "automatic":
            continue
        if not metadata.get("asaas_pix_automatic_authorization_id"):
            continue
        status = str(metadata.get("asaas_pix_automatic_authorization_status") or "").strip().upper()
        if row.status == "cancelled" and status in {"", "ACTIVE"}:
            status = "CANCELLED"
        if status in {"ACTIVE", "CANCELLED", "EXPIRED", "REFUSED"}:
            return status
        if status in {"CREATED", "PENDING", "AWAITING_AUTHORIZATION"}:
            continue
        return "ACTIVE" if row.status == "paid" else None
    return None


# ---------------------------------------------------------------- uma fatura aberta por vez


def cancel_open_payments(
    db: Session,
    client: AsaasClient,
    *,
    customer_id: str | None,
    session: CheckoutSession | None = None,
    keep_ids: Iterable[str] = (),
    new_subscription_id: str | None = None,
    replaced_by: str | None = None,
) -> list[str]:
    """Cancela no Asaas as cobranças PENDING e OVERDUE do cliente que a compra nova substitui.

    Só roda depois que a cobrança nova existe (assim o cliente nunca fica sem fatura para pagar).
    Nunca cancela cobrança paga: o Asaas só lista e aceita cancelar as abertas. Falha em uma não
    impede as outras. Devolve os ids cancelados, que passam a aparecer como "Substituída".
    """
    if not customer_id:
        return []
    keep = {str(item) for item in keep_ids if item}
    token = ""
    started: date | None = None
    if session is not None:
        keep.add(str(session.asaas_payment_id or ""))
        token = str(session.token or "")
        new_subscription_id = new_subscription_id or str((session.metadata_json or {}).get("asaas_subscription_id") or "")
        replaced_by = replaced_by or session.asaas_payment_id
        # Nada criado a partir do início desta compra é cancelado (o QR Code do Pix Automático, por
        # exemplo, nasce como cobrança sem a nossa referência).
        started = session.created_at.date() if session.created_at else None
    cancelled: list[str] = []
    for status in OPEN_PAYMENT_STATUSES:
        try:
            rows = (client.list_payments(customer=customer_id, status=status, limit=100) or {}).get("data") or []
        except AsaasAPIError:
            continue
        for payment in rows:
            if not isinstance(payment, dict) or not payment.get("id"):
                continue
            payment_id = str(payment["id"])
            if payment_id in cancelled or payment_id in keep:
                continue
            if token and token in str(payment.get("externalReference") or ""):
                continue
            created = parse_date(payment.get("dateCreated"))
            if started is not None and created is not None and created >= started:
                continue
            payment_subscription = payment.get("subscription")
            if isinstance(payment_subscription, dict):
                payment_subscription = payment_subscription.get("id")
            if new_subscription_id and str(payment_subscription or "") == new_subscription_id:
                continue
            try:
                client.delete_payment(payment_id)
            except AsaasAPIError:
                # Paga naquele minuto ou já cancelada: fica como está; o webhook mostra o resultado.
                continue
            mark_payment_replaced(db, payment_id, reason="renewal", replaced_by=replaced_by)
            cancelled.append(payment_id)
    return cancelled


__all__ = [
    "ContractOffer",
    "add_months",
    "cancel_open_payments",
    "covered_by_paid",
    "covered_period",
    "current_contract_offer",
    "is_paid_payment",
    "mark_payment_applied",
    "mark_payment_replaced",
    "parse_date",
    "payment_applied",
    "pix_automatic_status",
    "replaced_payment_ids",
]
