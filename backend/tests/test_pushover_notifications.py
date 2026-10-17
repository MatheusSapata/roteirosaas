"""Pushover como segundo canal de avisos: várias contas (uma por pessoa, sem Pushover Teams), cada
uma escolhe os eventos; chaves guardadas criptografadas; eventos de compra aprovada, checkout
iniciado e cobrança vencida."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.deps import get_current_superuser
from app.main import app
from app.models.pushover_account import PushoverAccount
from app.services import pushover, webhook_notifications
from app.services.ntfy import SubscriptionPushScenario, publish_subscription_notification
from app.services.webhook_notifications import contact_context, notify_payment_overdue, send_notification


@pytest.fixture
def pushover_calls(monkeypatch):
    sent: list[dict] = []
    validated: list[dict] = []

    def fake_send(**kwargs):
        if kwargs["user_key"] == "u-recusa":
            raise pushover.PushoverError("user identifier is invalid")
        sent.append(kwargs)

    def fake_validate(**kwargs):
        if kwargs["user_key"].startswith("invalida"):
            raise pushover.PushoverError("user key is invalid")
        validated.append(kwargs)

    monkeypatch.setattr(pushover, "send_message", fake_send)
    monkeypatch.setattr(pushover, "validate_user", fake_validate)
    # Sem ntfy de verdade: os eventos antigos ainda mandam para o tópico.
    ntfy_calls: list[dict] = []
    monkeypatch.setattr("app.services.ntfy.NtfyService.publish", lambda self, **kwargs: ntfy_calls.append(kwargs))
    webhook_notifications._RECENT.clear()
    return SimpleNamespace(sent=sent, validated=validated, ntfy=ntfy_calls)


@pytest.fixture
def admin(client):
    app.dependency_overrides[get_current_superuser] = lambda: SimpleNamespace(is_superuser=True, id=1)
    yield client
    app.dependency_overrides.pop(get_current_superuser, None)


def test_accounts_keep_keys_encrypted_and_share_the_app_token(admin, db_session, pushover_calls):
    first = admin.post(
        "/api/v1/admin-master/webhook-notifications/pushover-accounts",
        json={"name": "Matheus", "user_key": "uQiRzpo4DXghDmr9QzzfQu27cmVRsG", "app_token": "azGDORePK8gMaC0QOYAMyEEuzJnyUi"},
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["user_key_masked"].endswith("sG") and "uQiRzpo4" not in str(body)
    assert body["app_token_masked"].endswith("Ui") and "azGDOR" not in str(body)
    # Conta nova começa recebendo os três eventos de vendas.
    assert body["event_keys"] == ["purchase_approved", "checkout_started", "payment_overdue"]

    # Segunda pessoa, sem o token: usa o do aplicativo já cadastrado.
    second = admin.post(
        "/api/v1/admin-master/webhook-notifications/pushover-accounts",
        json={"name": "Jardel", "user_key": "uJardelKey000000000000000000001", "event_keys": ["purchase_approved", "inexistente"]},
    )
    assert second.status_code == 201, second.text
    assert second.json()["event_keys"] == ["purchase_approved"]
    assert pushover_calls.validated[-1]["app_token"] == "azGDORePK8gMaC0QOYAMyEEuzJnyUi"

    stored = db_session.query(PushoverAccount).order_by(PushoverAccount.id).all()
    assert len(stored) == 2
    assert "uQiRzpo4DXghDmr9QzzfQu27cmVRsG" not in stored[0].user_key_encrypted  # criptografada no banco

    refused = admin.post(
        "/api/v1/admin-master/webhook-notifications/pushover-accounts",
        json={"name": "Errada", "user_key": "invalida123", "app_token": "azGDORePK8gMaC0QOYAMyEEuzJnyUi"},
    )
    assert refused.status_code == 400 and "não aceitou" in refused.json()["detail"]

    listed = admin.get("/api/v1/admin-master/webhook-notifications/pushover-accounts").json()
    assert [item["name"] for item in listed] == ["Matheus", "Jardel"]
    # Alterar só os eventos não pede a chave de novo.
    updated = admin.put(
        f"/api/v1/admin-master/webhook-notifications/pushover-accounts/{listed[1]['id']}",
        json={"event_keys": ["checkout_started"], "enabled": False},
    )
    assert updated.json()["event_keys"] == ["checkout_started"] and updated.json()["enabled"] is False
    assert admin.delete(f"/api/v1/admin-master/webhook-notifications/pushover-accounts/{listed[1]['id']}").status_code == 204


def _account(
    db_session, name: str, user_key: str, event_keys: list[str], enabled: bool = True, app_token: str = "token-app"
) -> PushoverAccount:
    from app.services.api_key_crypto import encrypt_api_key

    account = PushoverAccount(
        name=name, user_key_encrypted=encrypt_api_key(user_key), user_key_last4=user_key[-4:],
        app_token_encrypted=encrypt_api_key(app_token), app_token_last4=app_token[-4:], event_keys=event_keys, enabled=enabled,
    )
    db_session.add(account)
    db_session.commit()
    return account


def test_each_account_gets_only_its_events_and_a_failure_does_not_stop_the_others(db_session, pushover_calls):
    _account(db_session, "Matheus", "u-matheus", ["purchase_approved", "checkout_started", "payment_overdue"])
    _account(db_session, "Vendas", "u-vendas", ["checkout_started"])
    _account(db_session, "Desligada", "u-off", ["checkout_started"], enabled=False)
    broken = _account(db_session, "Quebrada", "u-recusa", ["checkout_started"])

    delivered = send_notification(
        event_key="checkout_started",
        context={"user_name": "Ana", "plan_name": "Roteiro Online", "amount": "R$ 67,00",
                 **contact_context("ana@x.com", "11987654321")},
    )
    assert delivered is True
    assert sorted(call["user_key"] for call in pushover_calls.sent) == ["u-matheus", "u-vendas"]
    call = pushover_calls.sent[0]
    assert call["title"] == "📢 Checkout iniciado - Roteiro Online"
    assert call["message"] == "Ana | (11) 98765-4321 | R$ 67,00"
    assert call["url"] == "https://wa.me/5511987654321" and call["url_title"] == "Chamar no WhatsApp"
    assert call["sound"] is None  # checkout iniciado: som padrão do aparelho
    assert pushover_calls.ntfy == []  # evento novo: ntfy começa desligado
    db_session.refresh(broken)
    assert "invalid" in broken.last_error

    # Evento antigo continua no ntfy e não vai para quem não escolheu.
    pushover_calls.sent.clear()
    send_notification(event_key="subscription_created", context={"user_name": "Ana"})
    assert len(pushover_calls.ntfy) == 1 and pushover_calls.sent == []


def test_purchase_approved_for_new_renewal_and_upgrade_but_not_cancellation(db_session, pushover_calls):
    _account(db_session, "Matheus", "u-matheus", ["purchase_approved"])
    for scenario in (SubscriptionPushScenario.NEW, SubscriptionPushScenario.RENEWED, SubscriptionPushScenario.CANCELLED):
        publish_subscription_notification(
            scenario=scenario, user_name="Bia", payment_method="PIX", amount="97.00", plan_name="Roteiro Online",
            customer_phone="11999990000",
        )
    publish_subscription_notification(
        scenario=SubscriptionPushScenario.UPGRADED, user_name="Bia", payment_method="Cartão", amount="970",
        previous_plan_name="Mensal", upgraded_plan_name="Anual",
    )
    messages = [call["message"] for call in pushover_calls.sent]
    assert messages == [
        "R$ 97,00 | Bia | PIX | Nova assinatura",
        "R$ 97,00 | Bia | PIX | Renovação",
        "R$ 970,00 | Bia | Cartão | Upgrade",
    ]
    assert pushover_calls.sent[-1]["title"] == "💰 Compra aprovada - Anual"
    # Receita nova: o som personalizado "viajeonvenda".
    assert {call["sound"] for call in pushover_calls.sent} == {"viajeonvenda"}


def test_overdue_charge_is_sent_once_per_charge(db_session, pushover_calls):
    _account(db_session, "Matheus", "u-matheus", ["payment_overdue"])
    for _ in range(2):  # o Asaas reenvia o mesmo aviso
        notify_payment_overdue(
            user_name="Caio", plan_name="Roteiro Online", amount="97", due_date="2026-10-10",
            payment_method="Boleto", kind="Renovação", phone="11988887777", dedupe_key="pay_123",
        )
    assert len(pushover_calls.sent) == 1
    assert pushover_calls.sent[0]["message"] == "R$ 97,00 | Caio | venceu 10/10/2026 | Renovação"


def test_rule_test_reports_each_channel(admin, db_session, pushover_calls):
    _account(db_session, "Matheus", "u-matheus", ["payment_overdue"])
    _account(db_session, "Quebrada", "u-recusa", ["payment_overdue"])
    rules = admin.get("/api/v1/admin-master/webhook-notifications").json()
    overdue = next(rule for rule in rules if rule["event_key"] == "payment_overdue")
    assert overdue["ntfy_enabled"] is False
    result = admin.post(f"/api/v1/admin-master/webhook-notifications/{overdue['id']}/test", json={"event_key": "payment_overdue"}).json()
    assert result["success"] is True and result["message"] == "Alguns envios falharam."
    assert [(item["target"], item["ok"]) for item in result["deliveries"]] == [("Matheus", True), ("Quebrada", False)]

    checkout = next(rule for rule in rules if rule["event_key"] == "checkout_started")
    empty = admin.post(f"/api/v1/admin-master/webhook-notifications/{checkout['id']}/test", json={"event_key": "checkout_started"}).json()
    assert empty["success"] is False and "Nenhum canal" in empty["message"]


def test_sound_can_be_changed_per_event_and_missing_custom_sound_falls_back(db_session, monkeypatch, pushover_calls):
    from app.models.webhook_notification import WebhookNotificationRule

    _account(db_session, "Matheus", "u-matheus", ["purchase_approved", "payment_overdue"])
    attempts: list[str | None] = []

    def picky_send(**kwargs):
        attempts.append(kwargs.get("sound"))
        if kwargs.get("sound") == "viajeonvenda":
            raise pushover.PushoverError("sound is invalid")  # conta sem o som personalizado
        pushover_calls.sent.append(kwargs)

    monkeypatch.setattr(pushover, "send_message", picky_send)
    assert send_notification(event_key="purchase_approved", context={"user_name": "Bia"}) is True
    assert attempts == ["viajeonvenda", None]  # reenviou com o som padrão do app
    account = db_session.query(PushoverAccount).first()
    db_session.refresh(account)
    assert "viajeonvenda" in account.last_error

    # O teste do evento conta que o som não existe e o aviso saiu com o som padrão.
    rule = db_session.query(WebhookNotificationRule).filter_by(event_key="purchase_approved").first()
    result = webhook_notifications.test_notification(rule_id=rule.id, db=db_session)
    assert "viajeonvenda" in result["deliveries"][0]["error"] and result["deliveries"][0]["ok"] is True

    # Som escolhido na tela vale no lugar do padrão; evento sem padrão não manda som.
    rule = db_session.query(WebhookNotificationRule).filter_by(event_key="purchase_approved").first()
    rule.pushover_sound = "cashregister"
    db_session.commit()
    attempts.clear()
    send_notification(event_key="purchase_approved", context={"user_name": "Bia"})
    send_notification(event_key="payment_overdue", context={"user_name": "Bia"}, dedupe_key="x1")
    assert attempts == ["cashregister", None]


def test_rules_show_the_default_sound_and_list_account_sounds(admin, db_session, monkeypatch, pushover_calls):
    _account(db_session, "Matheus", "u-matheus", ["purchase_approved"])
    monkeypatch.setattr(pushover, "list_sounds", lambda **kwargs: {"pushover": "Pushover (default)", "viajeonvenda": "Viaje On venda"})
    rules = {rule["event_key"]: rule for rule in admin.get("/api/v1/admin-master/webhook-notifications").json()}
    assert rules["purchase_approved"]["default_pushover_sound"] == "viajeonvenda"
    assert rules["subscription_renewed"]["default_pushover_sound"] == "viajeonvenda"
    assert rules["checkout_started"]["default_pushover_sound"] is None
    sounds = admin.get("/api/v1/admin-master/webhook-notifications/pushover-sounds").json()
    assert {"value": "viajeonvenda", "label": "Viaje On venda"} in sounds

    # Outra conta com outro aplicativo, sem o som personalizado: a lista só traz o que toca em todas.
    _account(db_session, "Outra", "u-outra", ["purchase_approved"], app_token="token-outro")
    monkeypatch.setattr(
        pushover, "list_sounds",
        lambda **kwargs: {"pushover": "Pushover (default)", **({"viajeonvenda": "Viaje On venda"} if kwargs["app_token"] == "token-app" else {})},
    )
    sounds = admin.get("/api/v1/admin-master/webhook-notifications/pushover-sounds").json()
    assert [sound["value"] for sound in sounds] == ["pushover"]
