"""Operação de cobrança: pagamento recebido de conta que segue bloqueada, varredura dos últimos dias
e quem está no Pix Automático sem autorização ativa. Só lê e avisa: nada aqui libera conta sozinho."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.asaas import AsaasEventLog
from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services.asaas import AsaasAPIError, AsaasClient
from app.services.billing_account import (
    PAID_PAYMENT_STATUSES,
    mark_event_once,
    parse_date,
    payment_applied,
    pix_automatic_status,
)
from app.services.company_status import ENDED_STATUSES

logger = logging.getLogger(__name__)

ALERTED_PREFIX = "alerted:"
PAID_EVENTS = ("PAYMENT_RECEIVED", "PAYMENT_CONFIRMED")
# Passado este tempo do aviso de pagamento, a conta já devia ter sido liberada.
ALERT_AFTER_MINUTES = 15
ALERT_WINDOW_HOURS = 48


def _resource_id(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("id") or "").strip()
    return str(value or "").strip()


def owner_of_payment(db: Session, payment: dict[str, Any]) -> User | None:
    """Conta dona do pagamento: pela referência do checkout ou nossa (id:plano:ciclo), pela assinatura
    do Asaas ou, sem assinatura (Pix Automático), pelo cliente."""
    reference = str(payment.get("externalReference") or "").strip()
    for prefix in ("checkout_upgrade:", "checkout_renewal:", "checkout:", "co:"):
        if reference.startswith(prefix):
            token = reference[len(prefix):].split(":", 1)[0].strip()
            session = db.query(CheckoutSession).filter(CheckoutSession.token == token).first() if token else None
            if session is not None and session.user_id:
                return db.get(User, session.user_id)
    parts = reference.split(":")
    if len(parts) == 3 and parts[0].isdigit():
        user = db.get(User, int(parts[0]))
        if user is not None:
            return user
    subscription_id = _resource_id(payment.get("subscription"))
    if subscription_id:
        sub = db.query(Subscription).filter(Subscription.asaas_subscription_id == subscription_id).first()
        if sub is not None:
            return db.get(User, sub.user_id)
    customer_id = _resource_id(payment.get("customer"))
    if customer_id:
        owners = db.query(Subscription).filter(Subscription.asaas_customer_id == customer_id).limit(2).all()
        if len(owners) == 1:
            return db.get(User, owners[0].user_id)
    return None


def account_stuck(user: User) -> bool:
    """A conta segue sem acesso apesar do pagamento: bloqueada, em atraso ou encerrada com o período
    pago já vencido."""
    sub = user.subscription
    if sub is None:
        return False
    status = str(sub.status or "").strip().lower()
    if user.subscription_blocked or status == "past_due":
        return True
    if status in ENDED_STATUSES:
        valid_until = sub.valid_until
        if valid_until is None:
            return True
        aware = valid_until if valid_until.tzinfo else valid_until.replace(tzinfo=timezone.utc)
        return aware <= datetime.now(timezone.utc)
    return False


def _row(db: Session, user: User, payment: dict[str, Any], paid_on: date | None) -> dict[str, Any]:
    sub = user.subscription
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.whatsapp,
        "payment_id": str(payment.get("id") or ""),
        "value": float(payment.get("value") or 0),
        "billing_type": payment.get("billingType"),
        "due_date": payment.get("dueDate"),
        "paid_on": paid_on.isoformat() if paid_on else None,
        "account_status": sub.status if sub else None,
        "access_until": sub.valid_until.isoformat() if sub and sub.valid_until else None,
        "applied": payment_applied(db, str(payment.get("id") or "")),
    }


# ---------------------------------------------------------------- alerta (job a cada poucos minutos)


def alert_paid_but_blocked(db: Session, now: datetime | None = None) -> int:
    """Pagamento recebido há mais de 15 minutos de uma conta que continua sem acesso vira aviso no
    Pushover (uma vez por pagamento). Usa os avisos do Asaas já guardados, sem chamar o Asaas."""
    from app.services.webhook_notifications import contact_context, notify_safely

    now = now or datetime.now(timezone.utc)
    newest = (now - timedelta(minutes=ALERT_AFTER_MINUTES)).replace(tzinfo=None)
    oldest = (now - timedelta(hours=ALERT_WINDOW_HOURS)).replace(tzinfo=None)
    events = (
        db.query(AsaasEventLog)
        .filter(
            AsaasEventLog.event_type.in_(PAID_EVENTS),
            AsaasEventLog.created_at <= newest,
            AsaasEventLog.created_at >= oldest,
        )
        .all()
    )
    sent = 0
    for event in events:
        payment = (event.payload or {}).get("payment") if isinstance(event.payload, dict) else None
        if not isinstance(payment, dict) or not payment.get("id"):
            continue
        payment_id = str(payment["id"])
        if db.query(AsaasEventLog.id).filter(AsaasEventLog.event_id == f"{ALERTED_PREFIX}{payment_id}").first():
            continue
        user = owner_of_payment(db, payment)
        if user is None or not account_stuck(user):
            continue
        if not mark_event_once(db, f"{ALERTED_PREFIX}{payment_id}", "PAYMENT_ALERTED", {"payment_id": payment_id}):
            continue
        notify_safely(
            event_key="paid_but_blocked",
            context={
                "event_label": "Pagamento recebido, conta bloqueada",
                "user_name": user.name or "Não informado",
                "amount": payment.get("value"),
                "payment_method": payment.get("billingType") or "Não informado",
                "due_date": payment.get("dueDate"),
                "plan_name": (user.subscription.plan if user.subscription else "") or "Plano",
                **contact_context(user.email, user.whatsapp),
            },
            dedupe_key=f"paid_but_blocked:{payment_id}",
        )
        sent += 1
    return sent


# ---------------------------------------------------------------- varredura para revisão (Admin Master)


def scan_paid_not_released(db: Session, client: AsaasClient, days: int = 60) -> dict[str, Any]:
    """Cobranças pagas nos últimos dias cruzadas com contas ainda inadimplentes ou encerradas. É uma
    lista para revisão: nada é liberado sozinho."""
    since = date.today() - timedelta(days=max(1, min(days, 180)))
    found: list[dict[str, Any]] = []
    unmatched = 0
    complete = True
    for status in sorted(PAID_PAYMENT_STATUSES):
        offset = 0
        while True:
            try:
                data = client.list_payments(
                    status=status, limit=100, offset=offset, **{"paymentDate[ge]": since.isoformat()}
                ) or {}
            except AsaasAPIError:
                complete = False
                break
            batch = [row for row in (data.get("data") or []) if isinstance(row, dict)]
            for payment in batch:
                user = owner_of_payment(db, payment)
                if user is None:
                    unmatched += 1
                    continue
                if account_stuck(user):
                    paid_on = parse_date(payment.get("paymentDate") or payment.get("confirmedDate"))
                    found.append(_row(db, user, payment, paid_on))
            if len(batch) < 100 or offset >= 2000:
                break
            offset += 100
    found.sort(key=lambda row: row["paid_on"] or "", reverse=True)
    return {"since": since.isoformat(), "complete": complete, "unmatched_payments": unmatched, "items": found}


def pix_automatic_ended(db: Session) -> list[dict[str, Any]]:
    """Contas pagando por Pix Automático sem autorização ativa: precisam reativar antes do próximo
    vencimento. Só lê o banco."""
    rows: list[dict[str, Any]] = []
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.payment_method_type == "pix", Subscription.status.in_(("active", "past_due")))
        .all()
    )
    for sub in subscriptions:
        user = db.get(User, sub.user_id)
        if user is None:
            continue
        status = pix_automatic_status(db, user)
        if status is None or status == "ACTIVE":
            continue
        rows.append(
            {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.whatsapp,
                "plan": sub.plan,
                "account_status": sub.status,
                "pix_automatic_status": status,
                "access_until": sub.valid_until.isoformat() if sub.valid_until else None,
            }
        )
    rows.sort(key=lambda row: row["access_until"] or "")
    return rows
