"""Upgrade dos planos antigos Profissional e Agência para o plano único (valor cheio, sem promoção).
Todos os dados são fictícios."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.models.checkout import CheckoutSession, CheckoutSettings
from app.models.user import User
from app.services import checkout
from app.services.legacy_renewal import (
    create_legacy_renewal_checkout_session,
    create_legacy_upgrade_checkout_session,
    legacy_renewal_info,
    legacy_upgrade_available,
)
from tests.conftest import TestingSessionLocal
from tests.test_legacy_renewal import (  # noqa: F401 - fixtures usadas pelos testes
    AFTER_CUTOFF,
    FakeAsaas,
    _card,
    _customer,
    login_as,
    quiet,
)

MONTHLY = {
    "key": "roteiro-online-mensal",
    "title": "Roteiro Online mensal",
    "plan_key": "scale",
    "billing_cycle": "monthly",
    "amount": "137.00",
    "active": True,
    "sales_slot": "monthly",
    "first_payment_amount": "67.00",
    "checkout_key": "default",
}
ANNUAL = {
    "key": "roteiro-online-anual",
    "title": "Roteiro Online anual",
    "plan_key": "scale",
    "billing_cycle": "annual",
    "amount": "1164.00",
    "active": True,
    "sales_slot": "annual",
    "max_installments": 12,
    "checkout_key": "default",
}
FULL = {"monthly": Decimal("137.00"), "annual": Decimal("1164.00")}
OFFER_KEY = {"monthly": MONTHLY["key"], "annual": ANNUAL["key"]}


def _settings(db, offers=None) -> None:
    db.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=offers if offers is not None else [MONTHLY, ANNUAL],
                            coupons_json=[], checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    db.commit()


def _pay_by_card(monkeypatch, db, session) -> FakeAsaas:
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session.asaas_customer_id = "cus_1"
    db.commit()
    result = checkout.start_card_payment(db, session, _card())
    assert result.status == "paid"
    return fake


# ---------------------------------------------------------------- quem pode


@pytest.mark.parametrize(
    ("kwargs", "available"),
    [
        ({"plan": "essencial"}, True),
        ({"plan": "professional", "status": "inactive", "mrr": "0"}, True),
        ({"plan": "agency", "legacy_amount": "89.99", "mrr": "89.99"}, True),
        ({"plan": "growth", "status": "past_due", "legacy_amount": "89.99"}, True),
        # Cakto já encerrada com valor: renova pela tela, então também pode fazer upgrade.
        ({"plan": "growth", "provider": "cakto", "status": "cancelled", "legacy_amount": "89.99", "mrr": "0"}, True),
        # Escala antigo só renova.
        ({"plan": "scale", "legacy_amount": "129.99"}, False),
        ({"plan": "infinity", "legacy_amount": "116.99"}, False),
        # Cobrança de fora (Cakto ainda cobrando, ViajeOn, manual, Stripe) e sem valor (suporte).
        ({"plan": "growth", "provider": "cakto", "status": "active", "legacy_amount": "89.99"}, False),
        ({"plan": "essencial", "provider": "viajeon", "legacy_amount": None, "mrr": "100.00"}, False),
        ({"plan": "essencial", "provider": "manual", "legacy_amount": None}, False),
        ({"plan": "essencial", "provider": "stripe", "legacy_amount": "49.99"}, False),
        ({"plan": "growth", "provider": "cakto", "status": "inactive", "legacy_amount": None, "mrr": "0"}, False),
        # Não é legado: cliente novo e conta sem valor.
        ({"plan": "scale", "legacy_amount": None, "mrr": "137.00", "created_at": AFTER_CUTOFF}, False),
        ({"plan": "essencial", "legacy_amount": None, "mrr": "0", "status": "inactive"}, False),
    ],
)
def test_billing_me_upgrade_available(client, login_as, kwargs, available):
    db = TestingSessionLocal()
    user = _customer(db, **kwargs)
    login_as(user.id)

    body = client.get("/api/v1/billing/me").json()

    assert body["legacy_upgrade_available"] is available
    assert legacy_upgrade_available(db.get(User, user.id).subscription) is available


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"plan": "scale", "legacy_amount": "129.99"}, 400),
        ({"plan": "infinity", "cycle": "annual", "legacy_amount": "1644.00"}, 400),
        ({"plan": "growth", "provider": "cakto", "status": "active", "legacy_amount": "89.99"}, 400),
        ({"plan": "infinity", "provider": "viajeon", "legacy_amount": None, "mrr": "100.00"}, 400),
        ({"plan": "growth", "provider": "cakto", "status": "inactive", "legacy_amount": None, "mrr": "0"}, 400),
        ({"plan": "scale", "legacy_amount": None, "mrr": "137.00", "created_at": AFTER_CUTOFF}, 403),
        ({"plan": "free", "legacy_amount": None, "mrr": "0"}, 403),
    ],
)
def test_upgrade_session_is_refused(client, login_as, quiet, kwargs, expected):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, **kwargs)
    login_as(user.id)

    for cycle in ("monthly", "annual"):
        response = client.post("/api/v1/checkout/public/session/legacy-upgrade", json={"billing_cycle": cycle})
        assert response.status_code == expected, response.text
    assert db.query(CheckoutSession).count() == 0


def test_upgrade_session_validates_cycle_and_offer(client, login_as, quiet):
    db = TestingSessionLocal()
    _settings(db, offers=[MONTHLY])  # sem oferta anual ativa
    user = _customer(db, plan="essencial")
    login_as(user.id)

    assert client.post("/api/v1/checkout/public/session/legacy-upgrade", json={"billing_cycle": "weekly"}).status_code == 422
    assert client.post("/api/v1/checkout/public/session/legacy-upgrade", json={"billing_cycle": "annual"}).status_code == 404
    assert db.query(CheckoutSession).count() == 0


# ---------------------------------------------------------------- sessão: valor cheio, sem promoção


@pytest.mark.parametrize("plan", ["essencial", "professional", "agency", "growth"])
@pytest.mark.parametrize("cycle", ["monthly", "annual"])
def test_upgrade_session_charges_full_price_even_when_inactive(client, login_as, quiet, plan, cycle):
    db = TestingSessionLocal()
    _settings(db)
    # Inativo, sem mrr e sem contrato no Asaas: o código antigo trataria como 1ª assinatura (promoção).
    user = _customer(db, plan=plan, status="inactive", mrr="0", legacy_amount="49.99")
    login_as(user.id)

    # O cliente só escolhe o ciclo; valor, oferta e cupom enviados são ignorados.
    response = client.post(
        "/api/v1/checkout/public/session/legacy-upgrade",
        json={"billing_cycle": cycle, "amount": "1.00", "offer_key": "outra", "coupon_code": "DESCONTO"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert Decimal(body["amount"]) == FULL[cycle]
    assert body["first_payment_amount"] is None and body["applied_coupon_code"] is None
    assert body["offer_key"] == OFFER_KEY[cycle] and body["billing_cycle"] == cycle
    assert body["is_upgrade"] is True and body["is_legacy_upgrade"] is True and body["is_legacy_renewal"] is False
    counts = [option["count"] for option in body["installment_options"]]
    assert counts == ([1] if cycle == "monthly" else list(range(1, 13)))
    session = db.query(CheckoutSession).filter(CheckoutSession.token == body["token"]).one()
    assert session.plan_key == "scale"
    assert session.metadata_json["first_subscription"] is False and session.metadata_json["legacy_upgrade"] is True
    assert "first_payment_amount" not in session.metadata_json


@pytest.mark.parametrize(
    "kwargs",
    [
        {"plan": "essencial", "status": "inactive", "mrr": "0"},
        {"plan": "growth", "provider": "cakto", "status": "cancelled", "legacy_amount": "89.99", "mrr": "0"},
        # Escala antigo e cobrança de fora comprando o plano novo por conta própria: também sem promoção.
        {"plan": "scale", "status": "inactive", "mrr": "0", "legacy_amount": "129.99"},
        {"plan": "growth", "provider": "cakto", "status": "inactive", "legacy_amount": None, "mrr": "0"},
    ],
)
def test_generic_upgrade_route_never_gives_promo_to_legacy(client, login_as, quiet, kwargs):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, **kwargs)
    login_as(user.id)

    body = client.post("/api/v1/checkout/public/session/upgrade", json={"offer_key": MONTHLY["key"]}).json()

    assert Decimal(body["amount"]) == Decimal("137.00") and body["first_payment_amount"] is None


def test_generic_upgrade_route_keeps_promo_for_first_subscription(client, login_as, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = User(name="Cliente Fictício", email="trial@example.com", hashed_password="x", plan="free",
                cpf="11122233344", whatsapp="47999999999", address_zipcode="89000000")
    db.add(user)
    db.commit()
    login_as(user.id)

    body = client.post("/api/v1/checkout/public/session/upgrade", json={"offer_key": MONTHLY["key"]}).json()

    assert Decimal(body["first_payment_amount"]) == Decimal("67.00")


# ---------------------------------------------------------------- depois do pagamento


@pytest.mark.parametrize("plan", ["essencial", "agency"])
def test_monthly_upgrade_payment_moves_to_new_plan_and_clears_legacy_value(monkeypatch, quiet, client, login_as, plan):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan=plan, legacy_amount="49.99", mrr="49.99", asaas_subscription_id="sub_antiga")
    session = create_legacy_upgrade_checkout_session(db, db.get(User, user.id), "monthly")

    fake = _pay_by_card(monkeypatch, db, session)

    assert fake.subscriptions[0]["value"] == 137.0 and fake.subscriptions[0]["cycle"] == "MONTHLY"
    assert fake.updates == []  # nasceu no valor cheio: nada de passar ao valor cheio depois
    assert fake.cancelled == ["sub_antiga"]
    db.expire_all()
    saved = db.get(User, user.id)
    sub = saved.subscription
    assert saved.plan == "scale" and sub.plan == "scale" and sub.billing_cycle == "monthly"
    assert sub.legacy_renewal_amount is None
    assert sub.mrr_amount == Decimal("137.00") and sub.status == "active" and sub.provider == "asaas"
    assert sub.asaas_subscription_id == "sub_renovada"
    assert legacy_renewal_info(sub).legacy is False and legacy_upgrade_available(sub) is False

    login_as(user.id)
    body = client.get("/api/v1/billing/me").json()
    assert body["legacy"] is False and body["legacy_upgrade_available"] is False and body["legacy_renewal_amount"] is None


def test_annual_upgrade_payment_uses_annual_value_and_monthly_mrr(monkeypatch, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="growth", legacy_amount="89.99", mrr="0", status="inactive")
    session = create_legacy_upgrade_checkout_session(db, db.get(User, user.id), "annual")

    fake = _pay_by_card(monkeypatch, db, session)

    assert fake.subscriptions[0]["value"] == 1164.0 and fake.subscriptions[0]["cycle"] == "YEARLY"
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "scale" and sub.billing_cycle == "annual" and sub.legacy_renewal_amount is None
    assert sub.mrr_amount == Decimal("97.00")


def test_pix_automatic_upgrade_has_no_promo(monkeypatch, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="essencial", legacy_amount="49.99", mrr="0", status="inactive")
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session = create_legacy_upgrade_checkout_session(db, db.get(User, user.id), "monthly")
    session.asaas_customer_id = "cus_1"
    db.commit()

    checkout.start_pix_payment(db, session)

    assert fake.pix[0]["value"] == 137.0 and fake.pix[0]["immediateQrCode"]["originalValue"] == 137.0


def test_cakto_ended_upgrade_converts_to_asaas_and_clears_value(monkeypatch, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="growth", provider="cakto", status="cancelled", legacy_amount="89.99", mrr="0",
                     cakto_subscription_code="cakto_sub_1", cakto_order_id="cakto_order_1", cakto_offer_id="oferta_1")
    session = create_legacy_upgrade_checkout_session(db, db.get(User, user.id), "monthly")

    fake = _pay_by_card(monkeypatch, db, session)

    assert fake.subscriptions[0]["value"] == 137.0
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.provider == "asaas" and sub.plan == "scale" and sub.status == "active"
    assert sub.cakto_subscription_code is None and sub.cakto_order_id is None
    assert sub.legacy_renewal_amount is None and sub.mrr_amount == Decimal("137.00")
    saved = db.query(CheckoutSession).filter(CheckoutSession.token == session.token).one().metadata_json["replaced_cakto"]
    assert saved["subscription_code"] == "cakto_sub_1"


def test_in_place_upgrade_also_clears_legacy_value(monkeypatch, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="agency", legacy_amount="89.99", mrr="89.99", asaas_subscription_id="sub_antiga")
    session = create_legacy_upgrade_checkout_session(db, db.get(User, user.id), "annual")
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)

    checkout._apply_upgrade_after_payment(db, session)

    assert fake.updates[0][1]["value"] == 1164.0
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "scale" and sub.legacy_renewal_amount is None and sub.mrr_amount == Decimal("97.00")


def test_escala_legacy_voluntary_purchase_of_new_plan_stops_being_legacy(monkeypatch, quiet):
    """Escala antigo que compra o plano novo pela rota geral: valor cheio e o valor antigo some
    (senão o plano novo renovaria pelo valor de antes)."""
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="scale", legacy_amount="129.99", mrr="129.99", asaas_subscription_id="sub_antiga")
    offer = checkout.resolve_offer(db, MONTHLY["key"])
    session = checkout.create_upgrade_checkout_session(db, offer=offer, user=db.get(User, user.id))

    fake = _pay_by_card(monkeypatch, db, session)

    assert fake.subscriptions[0]["value"] == 137.0
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "scale" and sub.legacy_renewal_amount is None and sub.mrr_amount == Decimal("137.00")
    assert legacy_renewal_info(sub).legacy is False


def test_legacy_renewal_keeps_plan_and_value_and_upgrade_stays_available(monkeypatch, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="growth", legacy_amount="89.99", mrr="89.99", asaas_subscription_id="sub_antiga")
    session = create_legacy_renewal_checkout_session(db, db.get(User, user.id))

    fake = _pay_by_card(monkeypatch, db, session)

    assert fake.subscriptions[0]["value"] == 89.99
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "growth" and sub.legacy_renewal_amount == Decimal("89.99")
    assert legacy_renewal_info(sub).mode == "panel" and legacy_upgrade_available(sub) is True
