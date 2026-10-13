"""Cobrança que falhou não é cancelamento: a conta fica inadimplente, no ar por 3 dias depois do
vencimento, a cobrança segue por 30 dias e só então a assinatura é encerrada."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.subscription import Subscription
from app.models.user import User
from app.services import company_status as rules
from app.services import subscription as job
from app.services.cakto import CaktoIntegrationService, PlanMapping

NOW = datetime(2026, 10, 13, 12, tzinfo=timezone.utc)


def _owner(status, due_days_ago, provider="asaas", failed=1):
    subscription = SimpleNamespace(
        plan="growth", provider=provider, status=status, valid_until=NOW - timedelta(days=due_days_ago), failed_attempts=failed,
        created_at=NOW - timedelta(days=200), deactivated_at=None, deactivation_estimated=False, mrr_amount=Decimal("89.99"),
    )
    return SimpleNamespace(subscription=subscription, is_superuser=False, trial_plan=None, trial_ends_at=None,
                           trial_started_at=None, trial_blocked=False, created_at=NOW - timedelta(days=200))


def test_overdue_stays_online_three_days_then_keeps_charging_until_thirty():
    status = rules.company_status
    within_grace = status(_owner("past_due", 2), NOW)
    assert (within_grace.key, within_grace.online, within_grace.label) == ("past_due", True, "Inadimplente")
    assert within_grace.ends == NOW - timedelta(days=2) + timedelta(days=3)
    # Passou dos 3 dias: sai do ar, mas continua inadimplente (cobrando), não "Cancelando".
    charging = status(_owner("past_due", 10, failed=4), NOW)
    assert (charging.key, charging.online) == ("past_due", False)
    # Depois dos 30 dias, se o job ainda não encerrou, já conta como desativada.
    assert status(_owner("past_due", 31), NOW).key == "inactive"


@pytest.fixture
def session_factory(monkeypatch):
    from tests.conftest import TestingSessionLocal

    monkeypatch.setattr(job, "SessionLocal", TestingSessionLocal)
    return TestingSessionLocal


def _sub(db, email, **fields):
    user = User(name=email, email=email, hashed_password="x", plan=fields.get("plan", "growth"))
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, **{"plan": "growth", "status": "active", **fields})
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    return sub.id


def test_due_date_without_renewal_turns_overdue_not_inactive(db_session, session_factory):
    yesterday = datetime.utcnow() - timedelta(days=1)
    paid = _sub(db_session, "asaas@x.com", provider="asaas", mrr_amount=Decimal("89.99"), valid_until=yesterday, asaas_subscription_id="sub_1")
    manual = _sub(db_session, "manual@x.com", provider="manual", mrr_amount=Decimal("0"), valid_until=yesterday)
    leaving = _sub(db_session, "sai@x.com", provider="asaas", status="cancel_at_period_end", mrr_amount=Decimal("89.99"), valid_until=yesterday)
    job.expire_subscriptions()
    db_session.expire_all()
    rows = {row.id: row for row in db_session.query(Subscription).all()}
    # Cobrada pela Asaas: inadimplente, mantendo a data de vencimento (conta 3 dias de carência).
    assert rows[paid].status == "past_due" and rows[paid].valid_until is not None
    # Sem cobrança automática ou com cancelamento pedido: encerra como antes.
    assert rows[manual].status == "inactive" and rows[leaving].status == "inactive"


def test_thirty_days_unpaid_ends_subscription_on_the_gateway(db_session, session_factory, monkeypatch):
    calls: list[tuple[str, str]] = []

    class FakeAsaas:
        def __init__(self, *_args):
            pass

        def list_payments(self, **params):
            return {"data": [{"paymentDate": "2026-01-01"}] if params.get("subscription") == "sub_pago" else []}

        def cancel_subscription(self, subscription_id):
            calls.append(("cancel", subscription_id))

    monkeypatch.setattr(job, "AsaasClient", FakeAsaas)
    monkeypatch.setattr(job.settings, "asaas_api_key", "chave")
    old = datetime.utcnow() - timedelta(days=31)
    unpaid = _sub(db_session, "deve@x.com", provider="asaas", status="past_due", mrr_amount=Decimal("89.99"), valid_until=old, asaas_subscription_id="sub_deve")
    recent = _sub(db_session, "recente@x.com", provider="asaas", status="past_due", mrr_amount=Decimal("89.99"),
                  valid_until=datetime.utcnow() - timedelta(days=10), asaas_subscription_id="sub_recente")
    job.end_unpaid_subscriptions()
    db_session.expire_all()
    rows = {row.id: row for row in db_session.query(Subscription).all()}
    assert calls == [("cancel", "sub_deve")]
    assert rows[unpaid].status == "inactive" and rows[unpaid].asaas_subscription_id is None and rows[unpaid].mrr_amount == 0
    # Ainda dentro dos 30 dias: segue cobrando.
    assert rows[recent].status == "past_due" and rows[recent].asaas_subscription_id == "sub_recente"


def test_payment_found_on_asaas_is_not_cancelled(db_session, session_factory, monkeypatch):
    calls: list[str] = []

    class FakeAsaas:
        def __init__(self, *_args):
            pass

        def list_payments(self, **params):
            return {"data": [{"paymentDate": "2099-01-01"}]}

        def cancel_subscription(self, subscription_id):
            calls.append(subscription_id)

    monkeypatch.setattr(job, "AsaasClient", FakeAsaas)
    monkeypatch.setattr(job.settings, "asaas_api_key", "chave")
    sub_id = _sub(db_session, "pagou@x.com", provider="asaas", status="past_due", mrr_amount=Decimal("89.99"),
                  valid_until=datetime.utcnow() - timedelta(days=31), asaas_subscription_id="sub_pago")
    job.end_unpaid_subscriptions()
    db_session.expire_all()
    assert calls == [] and db_session.get(Subscription, sub_id).status == "past_due"


def test_cakto_refused_renewal_is_overdue_not_cancelled(db_session, monkeypatch):
    monkeypatch.setattr("app.services.cakto.publish_subscription_notification", lambda **_kwargs: None)
    user = User(name="Cliente", email="c@x.com", hashed_password="x", plan="growth")
    db_session.add(user)
    db_session.flush()
    sub = Subscription(user_id=user.id, plan="growth", provider="cakto", cakto_subscription_code="sub_9", status="active",
                       billing_cycle="monthly", mrr_amount=Decimal("89.99"), valid_until=datetime.now(timezone.utc) - timedelta(days=1))
    db_session.add(sub)
    db_session.flush()
    user.subscription_id = sub.id
    db_session.commit()
    service = CaktoIntegrationService(db_session)
    service.plan_mappings = [PlanMapping(plan_key="growth", cycle="monthly", offer_id="growth_offer", product_id=None)]
    payload = {"event": "subscription_renewal_refused", "data": {"subscription": {"code": "sub_9"}, "order": {"offer": {"id": "growth_offer"}}}}
    service._handle_subscription_status(payload, status="past_due", downgrade_plan=True)
    db_session.refresh(sub)
    db_session.refresh(user)
    # Antes: "cancelled" (aparecia como Cancelando), MRR zerado e plano rebaixado.
    assert (sub.status, sub.mrr_amount, sub.failed_attempts, user.plan) == ("past_due", Decimal("89.99"), 1, "growth")
    assert rules.company_status(user).key == "past_due"
