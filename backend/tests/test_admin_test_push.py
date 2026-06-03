from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.deps import get_current_superuser
from app.services.ntfy import SubscriptionPushScenario, build_subscription_push_message


def test_build_subscription_push_message_includes_subscription_context():
    title, message, tags = build_subscription_push_message(
        scenario=SubscriptionPushScenario.CANCELLED,
        user_name="Carla Teste",
        payment_method="Boleto",
        amount="297.00",
        plan_name="Plano Growth",
        offer_name="Oferta Growth Mensal",
        cancelled_item="Assinatura mensal do Plano Growth",
    )

    assert title == "Assinatura cancelada - Plano Growth"
    assert message == "R$ 297,00 | Carla Teste"
    assert "subscription" in tags


def test_build_subscription_push_message_upgrade_format():
    title, message, tags = build_subscription_push_message(
        scenario=SubscriptionPushScenario.UPGRADED,
        user_name="Daniel Teste",
        payment_method="Cartão de crédito",
        amount="149.90",
        previous_plan_name="Plano Essencial",
        upgraded_plan_name="Plano Growth",
    )

    assert title == "Upgrade realizado - Plano Essencial para Plano Growth"
    assert message == "R$ 149,90 | Daniel Teste"
    assert "arrow_up" in tags


@pytest.mark.parametrize(
    ("scenario", "expected_phrase"),
    [
        (SubscriptionPushScenario.NEW, "Assinatura criada"),
        (SubscriptionPushScenario.RENEWED, "Assinatura renovada"),
        (SubscriptionPushScenario.CANCELLED, "Assinatura cancelada"),
        (SubscriptionPushScenario.UPGRADED, "Upgrade realizado"),
        (SubscriptionPushScenario.TEST, "Assinatura de teste"),
    ],
)
def test_admin_subscription_push_endpoint(client, monkeypatch, scenario, expected_phrase):
    app_user = SimpleNamespace(is_superuser=True)
    captured = {}

    def fake_superuser():
        return app_user

    def fake_publish(self, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr("app.api.v1.endpoints.admin.NtfyService.publish", fake_publish)
    client.app.dependency_overrides[get_current_superuser] = fake_superuser
    try:
        response = client.post("/api/v1/admin/test-push/subscription", json={"scenario": scenario})
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": None}
    assert captured["title"].startswith("Assinatura ")
    assert expected_phrase in captured["title"]
    assert captured["message"].count("\n") == 0
    if scenario == SubscriptionPushScenario.CANCELLED:
        assert captured["message"].count("|") == 1
    elif scenario == SubscriptionPushScenario.UPGRADED:
        assert captured["message"].count("|") == 1
    else:
        assert captured["message"].count("|") == 2
