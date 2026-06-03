from __future__ import annotations

from decimal import Decimal

from app.models.subscription import Subscription
from app.models.user import User
from app.services.ntfy import SubscriptionPushScenario


def test_asaas_subscription_cancelled_webhook_sends_push(client, db_session, monkeypatch):
    user = User(
        name="Cliente Teste",
        email="cliente@example.com",
        hashed_password="hashed",
        plan="growth",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    subscription = Subscription(
        user_id=user.id,
        plan="growth",
        provider="asaas",
        asaas_subscription_id="sub_123",
        payment_method_type="card",
        billing_cycle="monthly",
        status="active",
        mrr_amount=Decimal("89.90"),
    )
    db_session.add(subscription)
    db_session.flush()
    user.subscription_id = subscription.id
    db_session.add(user)
    db_session.commit()

    captured: dict[str, object] = {}

    monkeypatch.setattr("app.api.v1.endpoints.billing.handle_asaas_checkout_webhook", lambda db, payload: False)
    monkeypatch.setattr("app.api.v1.endpoints.billing.mark_viajechat_cancelled", lambda **kwargs: None)

    def fake_publish(**kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr("app.api.v1.endpoints.billing.publish_subscription_notification", fake_publish)

    response = client.post(
        "/api/v1/billing/webhook",
        json={
            "event": "SUBSCRIPTION_CANCELLED",
            "subscription": {
                "id": "sub_123",
                "billingType": "CREDIT_CARD",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert captured["scenario"] == SubscriptionPushScenario.CANCELLED
    assert captured["user_name"] == "Cliente Teste"
    assert captured["payment_method"] == "Cartão de crédito"
    assert captured["amount"] == subscription.mrr_amount
    assert "Assinatura growth" in str(captured["cancelled_item"])
