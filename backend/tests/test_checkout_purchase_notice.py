"""Aviso de compra do checkout próprio: um por compra, do tipo certo, venha a confirmação do cartão na
hora, do polling ou do webhook do Asaas."""
from __future__ import annotations

import pytest

from app.models.checkout import CheckoutSession
from app.services import checkout
from app.services.subscription_notifications import SubscriptionPushScenario as Scenario
from tests.conftest import TestingSessionLocal
from tests.test_checkout_installments import MONTHLY, FakeAsaas, _card, _new_session


@pytest.fixture
def notices(monkeypatch):
    sent: list[dict] = []
    monkeypatch.setattr(checkout, "_dispatch_meta_checkout_events", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "mark_viajechat_signed", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "_raise_if_registered_checkout_identity", lambda *_a: None)
    monkeypatch.setattr(checkout, "_notify_checkout_subscription_push", lambda **kwargs: sent.append(kwargs))
    return sent


def _session(**metadata) -> CheckoutSession:
    return CheckoutSession(plan_key="scale", billing_cycle="monthly", metadata_json=metadata)


@pytest.mark.parametrize(
    ("metadata", "previous", "expected"),
    [
        ({}, (None, None), Scenario.NEW),  # checkout público
        ({"upgrade_mode": True, "first_subscription": True, "current_plan": "scale"}, (None, None), Scenario.NEW),  # sai do teste grátis
        ({"upgrade_mode": True, "legacy_renewal": True, "current_plan": "profissional"}, (None, None), Scenario.RENEWED),
        ({"upgrade_mode": True, "legacy_upgrade": True, "current_plan": "profissional"}, (None, None), Scenario.UPGRADED),
        ({"upgrade_mode": True, "current_plan": "scale", "current_billing_cycle": "monthly"}, (None, None), Scenario.RENEWED),
        ({"upgrade_mode": True, "current_plan": "scale", "current_billing_cycle": "annual"}, (None, None), Scenario.UPGRADED),
        ({"upgrade_mode": True, "current_plan": "essencial"}, (None, None), Scenario.UPGRADED),
        # Sessão criada antes de guardar o ciclo: vale o da assinatura antes da compra.
        ({"upgrade_mode": True, "current_plan": "scale"}, ("scale", "annual"), Scenario.UPGRADED),
    ],
)
def test_purchase_kind(metadata, previous, expected):
    assert checkout.checkout_purchase_scenario(_session(**metadata), *previous) == expected


def test_card_approved_now_notifies_once_and_webhook_does_not_repeat(monkeypatch, notices):
    db = TestingSessionLocal()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: FakeAsaas())
    session = _new_session(db, MONTHLY)

    result = checkout.start_card_payment(db, session, _card())

    assert result.status == "paid"
    assert [notice["scenario"] for notice in notices] == [Scenario.NEW]
    # O Asaas confirma o mesmo pagamento depois: não vira outro aviso.
    checkout.handle_asaas_checkout_webhook(
        db,
        {"event": "PAYMENT_CONFIRMED", "payment": {"id": "pay_1", "status": "CONFIRMED", "externalReference": f"checkout:{session.token}"}},
    )
    assert len(notices) == 1


def test_pix_paid_by_webhook_notifies_once(notices):
    db = TestingSessionLocal()
    session = _new_session(db, MONTHLY)
    session.payment_method = "pix"
    session.status = "awaiting_payment"
    db.commit()
    payload = {"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_pix", "status": "RECEIVED", "externalReference": f"checkout:{session.token}"}}

    checkout.handle_asaas_checkout_webhook(db, payload)
    checkout.handle_asaas_checkout_webhook(db, {**payload, "event": "PAYMENT_CONFIRMED"})

    assert [notice["scenario"] for notice in notices] == [Scenario.NEW]
    assert db.query(CheckoutSession).filter_by(token=session.token).one().status == "paid"
