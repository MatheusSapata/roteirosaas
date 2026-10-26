"""Upgrade pago quando o Asaas recusa alterar a assinatura antiga, e fatura estornada na tela de Faturas.
Todos os dados são fictícios."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.api.v1.endpoints.billing import _normalize_asaas_payment
from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services import checkout as checkout_service
from app.services.asaas import AsaasAPIError

NOW = datetime.now(timezone.utc)


@pytest.mark.parametrize("status", ["REFUNDED", "REFUND_REQUESTED", "REFUND_IN_PROGRESS"])
def test_refunded_payment_is_not_an_open_invoice(status):
    item = _normalize_asaas_payment(
        {"id": "pay_1", "status": status, "dueDate": "2020-01-01", "value": 129.99}
    )
    assert item.bucket == "replaced"
    assert item.is_paid is False


def test_past_due_pending_payment_is_still_overdue():
    item = _normalize_asaas_payment(
        {"id": "pay_2", "status": "PENDING", "dueDate": "2020-01-01", "value": 129.99}
    )
    assert item.bucket == "overdue"


def test_paid_upgrade_is_applied_when_asaas_refuses_to_edit_old_subscription(db_session, monkeypatch):
    user = User(name="Cliente Fictício", email="upgrade@example.com", hashed_password="x", plan="essencial")
    db_session.add(user)
    db_session.flush()
    sub = Subscription(
        user_id=user.id, plan="essencial", provider="asaas", billing_cycle="monthly", status="past_due",
        mrr_amount=Decimal("129.99"), asaas_customer_id="cus_1", asaas_subscription_id="sub_old",
        payment_method_type="card", valid_until=NOW - timedelta(days=5),
    )
    db_session.add(sub)
    db_session.flush()
    user.subscription_id = sub.id
    session = CheckoutSession(
        token="tok_upgrade", offer_key="professional", product_name="Plano Profissional", plan_key="professional",
        billing_cycle="monthly", amount=Decimal("49.99"), status="paid", payment_method="card",
        customer_name="Cliente Fictício", customer_email="upgrade@example.com", customer_document="12345678909",
        customer_phone="47999999999", customer_zipcode="89000000", asaas_customer_id="cus_1", user_id=user.id,
        metadata_json={"upgrade_mode": True, "target_user_id": user.id, "current_plan": "essencial"},
    )
    db_session.add(session)
    db_session.commit()

    class FakeClient:
        cancelled: list[str] = []

        def update_subscription(self, *_args, **_kwargs):
            raise AsaasAPIError({"errors": [{"description": "Não é possível alterar o valor"}]})

        def cancel_subscription(self, subscription_id):
            self.cancelled.append(subscription_id)

    client = FakeClient()
    monkeypatch.setattr(checkout_service, "_ensure_asaas_client", lambda: client)
    monkeypatch.setattr(checkout_service, "_announce_checkout_purchase", lambda *a, **k: None)
    monkeypatch.setattr(checkout_service, "republish_all_user_pages", lambda *a, **k: None)
    monkeypatch.setattr(checkout_service, "mark_viajechat_signed", lambda **k: None)

    result = checkout_service._complete_paid_checkout_session(db_session, session)

    db_session.refresh(sub)
    assert result.id == user.id
    assert sub.plan == "professional" and sub.status == "active"
    assert client.cancelled == ["sub_old"]
    assert session.metadata_json["upgrade_in_place"] is False
    assert "upgrade_in_place_error" in session.metadata_json
