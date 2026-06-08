from __future__ import annotations

from decimal import Decimal

from app.models.subscription import Subscription
from app.models.user import User
from app.services.cakto import CaktoIntegrationService, PlanMapping


def test_cakto_cancelled_webhook_still_notifies_when_previous_offer_is_ignored(db_session, monkeypatch):
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
        provider="cakto",
        cakto_subscription_code="sub_123",
        cakto_offer_id="growth_monthly_offer",
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

    def fake_publish_subscription_notification(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("app.services.cakto.publish_subscription_notification", fake_publish_subscription_notification)

    service = CaktoIntegrationService(db_session)
    service.plan_mappings = [PlanMapping(plan_key="essencial", cycle="monthly", offer_id="essencial_monthly_offer", product_id=None)]

    payload = {
        "event": "subscription_canceled",
        "data": {
            "subscription": {
                "code": "sub_123",
            },
            "order": {
                "offer": {
                    "id": "essencial_monthly_offer",
                    "name": "Oferta Essencial Mensal",
                },
            },
        },
    }

    result = service._handle_subscription_status(payload, status="cancelled")

    assert "cancelamento ignorado" in result.lower()
    assert captured["scenario"].value == "assinatura_cancelada"
    assert captured["offer_name"] == "Oferta Essencial Mensal"
    assert "Cancelamento ignorado após upgrade" in str(captured["cancelled_item"])
    db_session.refresh(subscription)
    assert subscription.status == "active"
    assert subscription.plan == "growth"
