"""Operação de cobrança: alerta de pagamento recebido com conta bloqueada, varredura e Pix Automático
encerrado. Todos os dados são fictícios."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.api.deps import get_current_superuser
from app.main import app
from app.models.asaas import AsaasEventLog
from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services import billing_operations, webhook_notifications

NOW = datetime.now(timezone.utc)


def make_user(db, *, status="past_due", valid_until_days=-10, email="cliente@example.com", payment_type="pix") -> User:
    user = User(name="Cliente Fictício", email=email, hashed_password="x", plan="scale", whatsapp="47999999999")
    db.add(user)
    db.flush()
    sub = Subscription(
        user_id=user.id, plan="scale", provider="asaas", billing_cycle="monthly", status=status,
        mrr_amount=Decimal("129.99"), asaas_customer_id=f"cus_{user.id}", payment_method_type=payment_type,
        valid_until=NOW + timedelta(days=valid_until_days),
    )
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    return user


def paid_event(db, user, payment_id="pay_1", minutes_ago=30, event="PAYMENT_RECEIVED") -> None:
    db.add(AsaasEventLog(
        event_id=f"asaas:{payment_id}:{event}", event_type=event, status="processed",
        payload={"event": event, "payment": {"id": payment_id, "value": 129.99, "billingType": "PIX",
                                              "dueDate": "2026-10-06", "customer": f"cus_{user.id}"}},
        created_at=(NOW - timedelta(minutes=minutes_ago)).replace(tzinfo=None),
    ))
    db.commit()


def capture(monkeypatch) -> list[dict]:
    sent: list[dict] = []
    monkeypatch.setattr(webhook_notifications, "notify_safely", lambda **kwargs: sent.append(kwargs))
    return sent


def test_alerts_once_when_paid_account_is_still_blocked(db_session, monkeypatch):
    user = make_user(db_session)
    paid_event(db_session, user)
    sent = capture(monkeypatch)

    assert billing_operations.alert_paid_but_blocked(db_session) == 1
    assert billing_operations.alert_paid_but_blocked(db_session) == 0

    assert len(sent) == 1 and sent[0]["event_key"] == "paid_but_blocked"
    assert sent[0]["context"]["user_name"] == "Cliente Fictício"


def test_no_alert_before_15_minutes_or_when_account_is_released(db_session, monkeypatch):
    waiting = make_user(db_session, email="a@example.com")
    paid_event(db_session, waiting, "pay_recent", minutes_ago=5)
    released = make_user(db_session, status="active", valid_until_days=25, email="b@example.com")
    paid_event(db_session, released, "pay_ok", minutes_ago=60)
    sent = capture(monkeypatch)

    assert billing_operations.alert_paid_but_blocked(db_session) == 0
    assert sent == []


def test_alert_found_by_checkout_token_and_ignores_unknown_payments(db_session, monkeypatch):
    user = make_user(db_session, status="inactive", valid_until_days=-5)
    db_session.add(CheckoutSession(
        token="tok-1", offer_key="x", product_name="x", plan_key="scale", billing_cycle="monthly", amount=Decimal("1"),
        status="paid", customer_name="x", customer_email="x@example.com", customer_document="1", customer_phone="1",
        customer_zipcode="1", user_id=user.id,
    ))
    db_session.add(AsaasEventLog(
        event_id="asaas:a", event_type="PAYMENT_CONFIRMED", status="processed",
        payload={"payment": {"id": "pay_tok", "externalReference": "checkout:tok-1"}},
        created_at=(NOW - timedelta(hours=1)).replace(tzinfo=None),
    ))
    db_session.add(AsaasEventLog(
        event_id="asaas:b", event_type="PAYMENT_RECEIVED", status="processed",
        payload={"payment": {"id": "pay_nobody", "customer": "cus_desconhecido"}},
        created_at=(NOW - timedelta(hours=1)).replace(tzinfo=None),
    ))
    db_session.commit()
    sent = capture(monkeypatch)

    assert billing_operations.alert_paid_but_blocked(db_session) == 1
    assert len(sent) == 1


class FakeAsaas:
    def __init__(self, payments):
        self.payments = payments

    def list_payments(self, limit=100, offset=0, **params):
        rows = [row for row in self.payments if row["status"] == params.get("status")]
        return {"data": rows[offset : offset + limit]}


def test_scan_lists_only_paid_payments_of_accounts_still_stuck(db_session):
    stuck = make_user(db_session, email="a@example.com")
    fine = make_user(db_session, status="active", valid_until_days=20, email="b@example.com")
    client = FakeAsaas([
        {"id": "pay_a", "status": "RECEIVED", "customer": f"cus_{stuck.id}", "value": 129.99, "paymentDate": "2026-10-20"},
        {"id": "pay_b", "status": "CONFIRMED", "customer": f"cus_{fine.id}", "value": 129.99, "paymentDate": "2026-10-21"},
        {"id": "pay_x", "status": "RECEIVED", "customer": "cus_ninguem", "value": 10, "paymentDate": "2026-10-21"},
    ])

    report = billing_operations.scan_paid_not_released(db_session, client, days=60)

    assert [item["payment_id"] for item in report["items"]] == ["pay_a"]
    assert report["items"][0]["email"] == "a@example.com" and report["items"][0]["applied"] is False
    assert report["unmatched_payments"] == 1 and report["complete"] is True


def test_pix_automatic_ended_lists_active_accounts_without_authorization(db_session):
    ended = make_user(db_session, status="active", valid_until_days=10, email="a@example.com")
    healthy = make_user(db_session, status="active", valid_until_days=10, email="b@example.com")
    card = make_user(db_session, status="active", valid_until_days=10, email="c@example.com", payment_type="card")
    for user, auth_status in ((ended, "CANCELLED"), (healthy, "ACTIVE")):
        db_session.add(CheckoutSession(
            token=f"tok-{user.id}", offer_key="x", product_name="x", plan_key="scale", billing_cycle="monthly",
            amount=Decimal("1"), status="paid", payment_method="pix", customer_name="x", customer_email=user.email,
            customer_document="1", customer_phone="1", customer_zipcode="1", user_id=user.id,
            metadata_json={"pix_mode": "automatic", "asaas_pix_automatic_authorization_id": f"auth_{user.id}",
                           "asaas_pix_automatic_authorization_status": auth_status},
        ))
    db_session.commit()

    rows = billing_operations.pix_automatic_ended(db_session)

    assert [row["email"] for row in rows] == ["a@example.com"]
    assert rows[0]["pix_automatic_status"] == "CANCELLED" and card.id not in {row["user_id"] for row in rows}


def test_admin_endpoints_need_superuser_and_return_lists(client, db_session):
    make_user(db_session, status="active", valid_until_days=10)
    assert client.get("/api/v1/admin/billing-operations/pix-automatic-ended").status_code in {401, 403}

    app.dependency_overrides[get_current_superuser] = lambda: object()
    try:
        response = client.get("/api/v1/admin/billing-operations/pix-automatic-ended")
        assert response.status_code == 200 and response.json() == {"items": []}
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)


def test_new_rule_reaches_accounts_that_already_get_overdue_alerts(db_session):
    from app.models.pushover_account import PushoverAccount

    db_session.add(PushoverAccount(
        name="Cobrança", user_key_encrypted="x", app_token_encrypted="y", enabled=True, event_keys=["payment_overdue"],
    ))
    db_session.commit()

    webhook_notifications.ensure_default_rules(db_session)

    account = db_session.query(PushoverAccount).one()
    assert "paid_but_blocked" in account.event_keys and "payment_overdue" in account.event_keys
