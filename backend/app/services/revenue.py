"""Receita para o Admin Master: MRR, ARR, recebido no mês, a receber, em atraso e próximas
renovações.

SOMENTE LEITURA. Nada aqui cria, altera ou cancela cobrança: os números saem do nosso banco
(assinaturas e eventos de webhook da Asaas e da Cakto já recebidos). A conferência opcional
com a Asaas usa ReadOnlyAsaas, que só aceita consultas (GET) e recusa qualquer outra coisa.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.models.asaas import AsaasEventLog
from app.models.cakto import CaktoEventLog
from app.models.subscription import Subscription
from app.models.user import User
from app.services.asaas import AsaasClient

ZERO = Decimal("0")
CENT = Decimal("0.01")
# Planos que não são receita (teste interno, contas da casa).
NON_REVENUE_PLANS = frozenset({"teste", "infinity", "free"})
ASAAS_PAID_EVENTS = frozenset({"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED", "PAYMENT_RECEIVED_IN_CASH"})
ASAAS_REFUND_EVENTS = frozenset({"PAYMENT_REFUNDED", "PAYMENT_CHARGEBACK_REQUESTED", "PAYMENT_CHARGEBACK_DISPUTE"})
CAKTO_PAID_EVENTS = frozenset({"purchase_approved", "subscription_renewed"})
CAKTO_REFUND_EVENTS = frozenset({"refund", "chargeback", "purchase_refunded", "purchase_chargeback"})
CYCLE_LABELS = {"monthly": "Mensal", "annual": "Anual"}
METHOD_LABELS = {"card": "Cartão", "credit_card": "Cartão", "pix": "Pix", "boleto": "Boleto"}


class ReadOnlyAsaas(AsaasClient):
    """Cliente da Asaas que só consulta. Qualquer método que não seja GET é recusado aqui,
    antes de sair do servidor: o painel de receita nunca gera, altera nem cancela cobrança."""

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if method.upper() != "GET":
            raise PermissionError(f"Painel de receita é somente leitura (bloqueado: {method} {path}).")
        return super()._request(method, path, **kwargs)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _money(value: Decimal) -> float:
    return float(value.quantize(CENT, rounding=ROUND_HALF_UP))


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value)) if value not in (None, "") else ZERO
    except Exception:  # noqa: BLE001
        return ZERO


def is_revenue_subscription(subscription: Subscription) -> bool:
    return (subscription.plan or "").strip().lower() not in NON_REVENUE_PLANS and _decimal(subscription.mrr_amount) > 0


def charge_amount(subscription: Subscription) -> Decimal:
    """Valor de cada cobrança: o mensal, ou o anual cheio (o MRR guarda o anual dividido por 12)."""
    monthly = _decimal(subscription.mrr_amount)
    if (subscription.billing_cycle or "monthly").lower() == "annual":
        return (monthly * 12).quantize(CENT, rounding=ROUND_HALF_UP)
    return monthly


def renews(subscription: Subscription) -> bool:
    """Vai ter nova cobrança? Ativa (mesmo com falha recente) e sem cancelamento agendado."""
    return (subscription.status or "").lower() in {"active", "past_due"} and int(subscription.failed_attempts or 0) < 3


@dataclass
class Payment:
    key: str
    source: str
    paid_at: datetime
    gross: Decimal
    net: Decimal
    method: str
    email: str | None = None
    description: str = ""
    # Quem pagou: id do cliente na Asaas ou e-mail na Cakto (para achar o primeiro pagamento).
    customer: str | None = None


def _asaas_payment(row: AsaasEventLog) -> tuple[str, dict[str, Any]] | None:
    payload = row.payload if isinstance(row.payload, dict) else {}
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else None
    event = str(payload.get("event") or row.event_type or "").upper()
    if not payment or not payment.get("id"):
        return None
    return event, payment


def _asaas_date(payment: dict[str, Any], *keys: str) -> datetime | None:
    for key in keys:
        raw = payment.get(key)
        if raw:
            try:
                return datetime.combine(date.fromisoformat(str(raw)[:10]), time(12), tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def all_payments(db: Session) -> tuple[list[Payment], list[Payment]]:
    """Todos os pagamentos confirmados e estornos já recebidos, cada pagamento contado uma vez só."""
    from app.api.v1.endpoints.admin import _extract_cakto_amount, _extract_customer_email  # evita import circular

    paid: dict[str, Payment] = {}
    refunds: dict[str, Payment] = {}
    for row in db.query(AsaasEventLog).all():
        parsed = _asaas_payment(row)
        if not parsed:
            continue
        event, payment = parsed
        key = f"asaas:{payment['id']}"
        if event in ASAAS_PAID_EVENTS:
            # Cartão: CONFIRMED (aprovado) e depois RECEIVED (dinheiro na conta) — conta uma vez,
            # na data da confirmação.
            moment = _asaas_date(payment, "confirmedDate", "paymentDate", "clientPaymentDate") or _aware(row.created_at)
            current = paid.get(key)
            if current is None or (moment and moment < current.paid_at):
                paid[key] = Payment(
                    key=key, source="Asaas", paid_at=moment, gross=_decimal(payment.get("value")),
                    net=_decimal(payment.get("netValue") or payment.get("value")),
                    method=str(payment.get("billingType") or "").lower(), description=str(payment.get("description") or ""),
                    customer=str(payment.get("customer") or "") or None,
                )
        elif event in ASAAS_REFUND_EVENTS:
            moment = _asaas_date(payment, "refundedDate") or _aware(row.created_at)
            refunds[key] = Payment(
                key=key, source="Asaas", paid_at=moment, gross=_decimal(payment.get("value")),
                net=_decimal(payment.get("netValue") or payment.get("value")), method=str(payment.get("billingType") or "").lower(),
            )
    for row in db.query(CaktoEventLog).filter(CaktoEventLog.event_type.isnot(None)).all():
        event = (row.event_type or "").strip().lower()
        if event not in CAKTO_PAID_EVENTS and event not in CAKTO_REFUND_EVENTS:
            continue
        payload = row.payload if isinstance(row.payload, dict) else {}
        moment = _aware(row.processed_at or row.created_at)
        amount = _extract_cakto_amount(payload)
        key = f"cakto:{row.event_id or row.id}"
        email = _extract_customer_email(payload)
        item = Payment(key=key, source="Cakto", paid_at=moment, gross=amount, net=amount, method="", email=email, customer=email)
        (paid if event in CAKTO_PAID_EVENTS else refunds)[key] = item
    return list(paid.values()), list(refunds.values())


def collect_payments(db: Session, start: datetime, end: datetime) -> tuple[list[Payment], list[Payment]]:
    """Pagamentos confirmados e estornos no período, cada pagamento contado uma vez só."""
    paid, refunds = all_payments(db)

    def in_range(items: list[Payment]) -> list[Payment]:
        return [item for item in items if item.paid_at and start <= item.paid_at < end]

    return in_range(paid), in_range(refunds)


@dataclass
class Renewal:
    subscription_id: int
    user_id: int
    name: str
    email: str
    plan: str
    cycle: str
    provider: str
    method: str
    due_on: date
    amount: Decimal
    alerts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subscription_id": self.subscription_id, "user_id": self.user_id, "name": self.name, "email": self.email,
            "plan": self.plan, "cycle": CYCLE_LABELS.get(self.cycle, self.cycle), "provider": self.provider,
            "method": METHOD_LABELS.get(self.method, self.method or "—"), "due_on": self.due_on.isoformat(),
            "amount": _money(self.amount), "alerts": self.alerts,
        }


def _renewal(subscription: Subscription, user: User) -> Renewal | None:
    valid_until = _aware(subscription.valid_until)
    if valid_until is None:
        return None
    alerts = []
    if int(subscription.failed_attempts or 0) > 0:
        alerts.append(f"{subscription.failed_attempts} falha(s) de cobrança")
    if (subscription.payment_method_type or "").lower() in {"boleto", "pix"} and (subscription.provider or "") == "asaas":
        alerts.append("Depende do cliente pagar")
    return Renewal(
        subscription_id=subscription.id, user_id=user.id, name=user.name or "", email=user.email or "",
        plan=(subscription.plan or user.plan or "").title(), cycle=(subscription.billing_cycle or "monthly").lower(),
        provider=(subscription.provider or "").title(), method=(subscription.payment_method_type or "").lower(),
        due_on=valid_until.date(), amount=charge_amount(subscription), alerts=alerts,
    )


@dataclass
class MrrBreakdown:
    mrr: Decimal = ZERO
    at_risk: Decimal = ZERO
    customers: int = 0
    by_plan: dict[str, Decimal] = field(default_factory=lambda: defaultdict(lambda: ZERO))
    customers_by_plan: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_cycle: dict[str, Decimal] = field(default_factory=lambda: defaultdict(lambda: ZERO))
    by_method: dict[str, Decimal] = field(default_factory=lambda: defaultdict(lambda: ZERO))


def mrr_breakdown(subscriptions: Iterable[Subscription]) -> MrrBreakdown:
    """MRR das assinaturas que vão renovar; "em risco" = cancelamento agendado ou falha de
    cobrança. Recebe só assinaturas de receita (is_revenue_subscription)."""
    result = MrrBreakdown()
    for subscription in subscriptions:
        status = (subscription.status or "").lower()
        if status not in {"active", "past_due", "cancel_at_period_end"}:
            continue
        monthly = _decimal(subscription.mrr_amount)
        if status == "cancel_at_period_end" or int(subscription.failed_attempts or 0) > 0:
            result.at_risk += monthly
        if status == "cancel_at_period_end":
            continue
        plan = (subscription.plan or "—").title()
        result.customers += 1
        result.mrr += monthly
        result.by_plan[plan] += monthly
        result.customers_by_plan[plan] += 1
        result.by_cycle[CYCLE_LABELS.get((subscription.billing_cycle or "monthly").lower(), "Mensal")] += monthly
        result.by_method[METHOD_LABELS.get((subscription.payment_method_type or "").lower(), "Outro")] += monthly
    return result


def revenue_overview(db: Session, month: date | None = None, horizon_days: int = 60, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    today = now.date()
    month = (month or today).replace(day=1)
    next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    start = datetime.combine(month, time.min, tzinfo=timezone.utc)
    end = datetime.combine(next_month, time.min, tzinfo=timezone.utc)
    rows = db.query(Subscription, User).join(User, User.id == Subscription.user_id).all()
    paying = [(s, u) for s, u in rows if is_revenue_subscription(s)]
    breakdown = mrr_breakdown(subscription for subscription, _user in paying)
    mrr, at_risk, customers = breakdown.mrr, breakdown.at_risk, breakdown.customers
    by_plan, by_cycle, by_method = breakdown.by_plan, breakdown.by_cycle, breakdown.by_method

    # Mês: recebido (eventos), a receber (renovações até o fim do mês) e em atraso.
    paid, refunded = collect_payments(db, start, end)
    received_gross = sum((item.gross for item in paid), ZERO)
    received_net = sum((item.net for item in paid), ZERO)
    refunded_total = sum((item.gross for item in refunded), ZERO)
    renewals = [r for s, u in paying if renews(s) for r in [_renewal(s, u)] if r]
    month_last = next_month - timedelta(days=1)
    to_receive = [r for r in renewals if today <= r.due_on <= month_last and month <= r.due_on]
    overdue = [r for r in renewals if r.due_on < today]
    upcoming = sorted((r for r in renewals if today <= r.due_on <= today + timedelta(days=horizon_days)), key=lambda r: (r.due_on, r.name))
    is_current_month = month.year == today.year and month.month == today.month

    def total(items: list[Renewal]) -> Decimal:
        return sum((item.amount for item in items), ZERO)

    weeks: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for item in upcoming:
        weeks[(item.due_on - timedelta(days=item.due_on.weekday())).isoformat()] += item.amount

    return {
        "month": month.isoformat(),
        "mrr": _money(mrr),
        "arr": _money(mrr * 12),
        "mrr_at_risk": _money(at_risk),
        "paying_customers": customers,
        "arpa": _money(mrr / customers) if customers else 0.0,
        "mrr_by_plan": {key: _money(value) for key, value in sorted(by_plan.items(), key=lambda kv: -kv[1])},
        "mrr_by_cycle": {key: _money(value) for key, value in by_cycle.items()},
        "mrr_by_method": {key: _money(value) for key, value in by_method.items()},
        "month_received_gross": _money(received_gross),
        "month_received_net": _money(received_net),
        "month_refunded": _money(refunded_total),
        "month_payments": len(paid),
        "month_to_receive": _money(total(to_receive)) if is_current_month else None,
        "month_to_receive_count": len(to_receive) if is_current_month else None,
        "month_expected": _money(received_gross - refunded_total + (total(to_receive) if is_current_month else ZERO)),
        "overdue": _money(total(overdue)),
        "overdue_items": [item.as_dict() for item in sorted(overdue, key=lambda r: r.due_on)],
        "upcoming": [item.as_dict() for item in upcoming],
        "upcoming_total": _money(total(upcoming)),
        "upcoming_by_week": {key: _money(value) for key, value in sorted(weeks.items())},
        "horizon_days": horizon_days,
        "payments": [
            {"source": p.source, "paid_at": p.paid_at.isoformat(), "gross": _money(p.gross), "net": _money(p.net),
             "method": METHOD_LABELS.get(p.method.lower().replace("credit_card", "card"), p.method or "—"), "email": p.email,
             "description": p.description}
            for p in sorted(paid, key=lambda p: p.paid_at, reverse=True)[:200]
        ],
    }


def asaas_open_charges(api_key: str, base_url: str, until: date) -> dict[str, Any]:
    """Cobranças já geradas na Asaas e ainda não pagas (pendentes e vencidas), só consulta."""
    client = ReadOnlyAsaas(api_key, base_url)
    totals: dict[str, dict[str, Any]] = {}
    for status in ("PENDING", "OVERDUE"):
        amount, count, offset = ZERO, 0, 0
        while True:
            data = client.list_payments(status=status, **{"dueDate[le]": until.isoformat()}, limit=100, offset=offset) or {}
            items = data.get("data") or []
            for item in items:
                amount += _decimal(item.get("value"))
                count += 1
            if not data.get("hasMore") or not items or offset > 5000:
                break
            offset += len(items)
        totals[status.lower()] = {"count": count, "amount": _money(amount)}
    return totals
