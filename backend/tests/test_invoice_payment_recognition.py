"""Fatura paga direto (fora do checkout de renovação) precisa ser reconhecida na conta."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.subscription import Subscription
from app.models.user import User
from app.services import checkout
from tests.test_checkout_pix_automatic import FakeDb, make_session


def _paid_pix_session(**metadata):
    session = make_session()
    session.payment_method = "pix"
    session.status = "paid"
    session.paid_at = checkout._utcnow()
    session.metadata_json = {
        "pix_mode": "automatic",
        "asaas_pix_automatic_authorization_id": "auth_webhook_123",
        **metadata,
    }
    return session


def test_paying_older_pix_invoice_by_link_renews_even_after_last_instruction_renewed(monkeypatch) -> None:
    # Outubro já renovou pela instrução; o cliente paga pela fatura a cobrança de setembro que ficou vencida.
    session = _paid_pix_session(
        asaas_pix_automatic_last_instruction_id="pai_oct",
        asaas_pix_automatic_last_instruction_due_date="2026-10-06",
        asaas_pix_automatic_last_renewed_instruction_id="pai_oct",
        asaas_pix_automatic_renewed_due_dates=["2026-10-06"],
    )
    renewed = []
    monkeypatch.setattr(checkout, "_renew_paid_pix_automatic_subscription", lambda _db, item: renewed.append(item))
    payload = {
        "event": "PAYMENT_RECEIVED",
        "payment": {"id": "pay_sep", "status": "RECEIVED", "dueDate": "2026-09-06", "externalReference": "co:checkout-token-123"},
    }
    db = FakeDb([session])

    assert checkout.handle_asaas_checkout_webhook(db, payload) is True
    assert checkout.handle_asaas_checkout_webhook(db, payload) is True

    assert renewed == [session]
    assert session.metadata_json["asaas_pix_automatic_renewed_due_dates"] == ["2026-10-06", "2026-09-06"]


def test_instruction_and_payment_of_same_cycle_renew_once(monkeypatch) -> None:
    session = _paid_pix_session(asaas_pix_automatic_last_instruction_id="pai_oct")
    renewed = []
    monkeypatch.setattr(checkout, "_renew_paid_pix_automatic_subscription", lambda _db, item: renewed.append(item))
    db = FakeDb([session])

    checkout.handle_asaas_checkout_webhook(db, {
        "event": "PIX_AUTOMATIC_RECURRING_PAYMENT_INSTRUCTION_PAID",
        "pixAutomaticPaymentInstruction": {"id": "pai_oct", "status": "PAID", "dueDate": "2026-10-06"},
    })
    checkout.handle_asaas_checkout_webhook(db, {
        "event": "PAYMENT_RECEIVED",
        "payment": {"id": "pay_oct", "status": "RECEIVED", "dueDate": "2026-10-06", "externalReference": "co:checkout-token-123"},
    })

    assert renewed == [session]


def _user_with_asaas_subscription(db_session, *, status: str) -> tuple[User, Subscription]:
    user = User(name="Cliente Fatura", email="fatura@example.com", hashed_password="hashed", plan="growth", is_active=True)
    db_session.add(user)
    db_session.flush()
    subscription = Subscription(
        user_id=user.id,
        plan="growth",
        provider="asaas",
        asaas_subscription_id="sub_painel",
        billing_cycle="monthly",
        status=status,
        failed_attempts=1,
        valid_until=datetime.now(timezone.utc) - timedelta(days=10),
        mrr_amount=Decimal("129.99"),
    )
    db_session.add(subscription)
    db_session.flush()
    user.subscription_id = subscription.id
    db_session.commit()
    return user, subscription


def _silence_side_effects(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.billing.handle_asaas_checkout_webhook", lambda db, payload: False)
    monkeypatch.setattr("app.api.v1.endpoints.billing.mark_viajechat_signed", lambda **kwargs: None)
    monkeypatch.setattr("app.api.v1.endpoints.billing.publish_subscription_notification", lambda **kwargs: None)
    monkeypatch.setattr("app.api.v1.endpoints.billing.republish_all_user_pages", lambda *args: None)


def test_invoice_without_our_reference_reactivates_by_asaas_subscription(client, db_session, monkeypatch) -> None:
    _user, subscription = _user_with_asaas_subscription(db_session, status="past_due")
    _silence_side_effects(monkeypatch)

    response = client.post("/api/v1/billing/webhook", json={
        "id": "evt_fatura_1",
        "event": "PAYMENT_RECEIVED",
        "payment": {"id": "pay_painel", "subscription": "sub_painel", "status": "RECEIVED", "value": 129.99, "dueDate": "2026-10-06"},
    })

    assert response.status_code == 200
    db_session.refresh(subscription)
    assert subscription.status == "active"
    assert subscription.failed_attempts == 0
    assert subscription.valid_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
    assert subscription.asaas_subscription_id == "sub_painel"


def test_unreferenced_payment_created_event_does_not_touch_status(client, db_session, monkeypatch) -> None:
    _user, subscription = _user_with_asaas_subscription(db_session, status="active")
    _silence_side_effects(monkeypatch)

    client.post("/api/v1/billing/webhook", json={
        "id": "evt_fatura_2",
        "event": "PAYMENT_CREATED",
        "payment": {"id": "pay_novo", "subscription": "sub_painel", "status": "PENDING", "dueDate": "2026-11-06"},
    })

    db_session.refresh(subscription)
    assert subscription.status == "active"
