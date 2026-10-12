"""Painel do Admin Master: os números da plataforma num período. SOMENTE LEITURA.

Cada número sai da mesma fonte e da mesma regra da tela que o detalha, para o painel nunca
discordar delas:
- MRR, clientes pagantes, ticket médio e MRR em risco: services/revenue (tela Receita e MRR).
- Recebido e estornado: pagamentos confirmados da Asaas e da Cakto, cada um contado uma vez.
- Novos clientes pagantes: quem fez o primeiro pagamento no período.
- Situação das empresas, cadastros e saídas: services/company_status (tela Empresas).

As datas são agrupadas pelo dia de Brasília (sem horário de verão desde 2019).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.page import Page, PageStatus
from app.models.subscription import Subscription
from app.models.user import User
from app.services.company_status import INTERNAL_PLANS, UNPAID_PLANS, agencies_with_owner, company_status
from app.services.revenue import ZERO, Payment, _money, all_payments, is_revenue_subscription, mrr_breakdown

BRT = timezone(timedelta(hours=-3))
# Situações de quem paga (em dia, com cobrança atrasada ou cancelando no fim do período).
PAYING_STATUSES = frozenset({"active", "past_due", "cancelling"})
# Períodos longos viram semanas no gráfico, para as colunas não ficarem finas demais.
WEEKLY_AFTER_DAYS = 62
TRIAL_ENDING_DAYS = 3


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def local_day(value: datetime | None) -> date | None:
    moment = _aware(value)
    return moment.astimezone(BRT).date() if moment else None


def period_days(days: int, start: date | None, end: date | None, now: datetime) -> tuple[date, date]:
    """Primeiro e último dia (inclusive) do período: o intervalo escolhido ou os últimos N dias."""
    if start and end:
        return start, end
    last = now.astimezone(BRT).date()
    return last - timedelta(days=days - 1), last


@dataclass
class Bucket:
    start: date
    end: date
    received: Decimal = ZERO
    payments: int = 0
    new_paying: int = 0
    signups: int = 0
    signups_paying: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "received": _money(self.received),
            "payments": self.payments,
            "new_paying": self.new_paying,
            "signups": self.signups,
            "signups_paying": self.signups_paying,
        }


class Buckets:
    def __init__(self, first: date, last: date):
        self.weekly = (last - first).days + 1 > WEEKLY_AFTER_DAYS
        self.first, self.last = first, last
        self.items: dict[date, Bucket] = {}
        cursor = first
        while cursor <= last:
            key = self._key(cursor)
            bucket = self.items.get(key)
            if bucket is None:
                self.items[key] = Bucket(start=cursor, end=cursor)
            else:
                bucket.end = cursor
            cursor += timedelta(days=1)

    def _key(self, day: date) -> date:
        return day - timedelta(days=day.weekday()) if self.weekly else day

    def get(self, day: date | None) -> Bucket | None:
        if day is None or day < self.first or day > self.last:
            return None
        return self.items.get(self._key(day))


def _in(day: date | None, first: date, last: date) -> bool:
    return day is not None and first <= day <= last


def _payer_key(payment: Payment, asaas_customers: dict[str, int], emails: dict[str, int]) -> str:
    """Um cliente por pessoa: o id do cliente na Asaas ou o e-mail da Cakto viram o usuário."""
    if payment.customer and payment.customer in asaas_customers:
        return f"user:{asaas_customers[payment.customer]}"
    email = (payment.email or "").strip().lower()
    if email and email in emails:
        return f"user:{emails[email]}"
    return payment.customer or email or payment.key


def build_dashboard(db: Session, first: date, last: date, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    buckets = Buckets(first, last)
    length = (last - first).days + 1
    prev_first, prev_last = first - timedelta(days=length), first - timedelta(days=1)

    # Receita recorrente agora (mesma conta da tela Receita e MRR).
    rows = db.query(Subscription, User).join(User, User.id == Subscription.user_id).all()
    breakdown = mrr_breakdown(subscription for subscription, _user in rows if is_revenue_subscription(subscription))

    # Pagamentos: recebido no período e primeiro pagamento de cada cliente.
    asaas_customers = {s.asaas_customer_id: s.user_id for s, _u in rows if s.asaas_customer_id}
    emails = {(u.email or "").strip().lower(): u.id for _s, u in rows if u.email}
    paid, refunds = all_payments(db)
    first_payment: dict[str, date] = {}
    received = prev_received = refunded = ZERO
    payments_count = 0
    for payment in paid:
        day = local_day(payment.paid_at)
        if day is None:
            continue
        key = _payer_key(payment, asaas_customers, emails)
        if key not in first_payment or day < first_payment[key]:
            first_payment[key] = day
        if _in(day, first, last):
            received += payment.gross
            payments_count += 1
            bucket = buckets.get(day)
            bucket.received += payment.gross
            bucket.payments += 1
        elif _in(day, prev_first, prev_last):
            prev_received += payment.gross
    for payment in refunds:
        if _in(local_day(payment.paid_at), first, last):
            refunded += payment.gross
    new_paying = prev_new_paying = 0
    for day in first_payment.values():
        if _in(day, first, last):
            new_paying += 1
            buckets.get(day).new_paying += 1
        elif _in(day, prev_first, prev_last):
            prev_new_paying += 1

    # Empresas: situação de hoje, cadastros do período e quem saiu do ar no período.
    counts: dict[str, int] = defaultdict(int)
    signups = signups_paying = prev_signups = left = trials_ending = 0
    for agency, owner in agencies_with_owner(db):
        status = company_status(owner, now)
        counts[status.key] += 1
        if status.key in ("internal", "no_owner"):
            continue
        created = local_day(agency.created_at)
        if _in(created, first, last):
            signups += 1
            bucket = buckets.get(created)
            bucket.signups += 1
            if status.key in PAYING_STATUSES:
                signups_paying += 1
                bucket.signups_paying += 1
        elif _in(created, prev_first, prev_last):
            prev_signups += 1
        subscription = owner.subscription if owner else None
        plan = (subscription.plan or "").strip().lower() if subscription else ""
        if (
            status.key == "inactive"
            and plan not in UNPAID_PLANS
            and plan not in INTERNAL_PLANS
            and _in(local_day(subscription.deactivated_at), first, last)
        ):
            left += 1
        ends = _aware(status.ends)
        if status.key == "trial" and ends and ends - now <= timedelta(days=TRIAL_ENDING_DAYS):
            trials_ending += 1

    customers = breakdown.customers
    return {
        "period": {"start": first.isoformat(), "end": last.isoformat(), "days": length, "weekly": buckets.weekly},
        "mrr": _money(breakdown.mrr),
        "arr": _money(breakdown.mrr * 12),
        "mrr_at_risk": _money(breakdown.at_risk),
        "paying_customers": customers,
        "arpa": _money(breakdown.mrr / customers) if customers else 0.0,
        "mrr_by_plan": [
            {"plan": plan, "mrr": _money(value), "customers": breakdown.customers_by_plan.get(plan, 0)}
            for plan, value in sorted(breakdown.by_plan.items(), key=lambda kv: -kv[1])
        ],
        "received": _money(received),
        "received_previous": _money(prev_received),
        "refunded": _money(refunded),
        "payments": payments_count,
        "new_paying": new_paying,
        "new_paying_previous": prev_new_paying,
        "signups": signups,
        "signups_paying": signups_paying,
        "signups_previous": prev_signups,
        "left": left,
        "trials_ending": trials_ending,
        "companies": dict(counts),
        "users": db.query(User).filter(User.is_superuser.is_(False)).count(),
        "pages": db.query(Page).count(),
        "pages_published": db.query(Page).filter(Page.status == PageStatus.published).count(),
        "series": [bucket.as_dict() for bucket in buckets.items.values()],
    }
