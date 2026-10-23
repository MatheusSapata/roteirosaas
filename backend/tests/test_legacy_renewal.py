"""Renovação dos planos antigos (Profissional, Agência e Escala) pelo mesmo valor que o cliente pagava.
Todos os dados são fictícios."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.api.deps import get_current_active_user
from app.main import app
from app.models.checkout import CheckoutSession, CheckoutSettings
from app.models.subscription import Subscription
from app.models.user import User
from app.services import checkout
from app.services.legacy_renewal import LEGACY_RENEWAL_OFFER_KEY, legacy_renewal_info
from tests.conftest import TestingSessionLocal

BEFORE_CUTOFF = datetime(2026, 6, 1, 12, tzinfo=timezone.utc)
AFTER_CUTOFF = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
# Oferta do plano único, só para provar que a renovação não usa o valor dela.
NEW_PLAN = {
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


class FakeAsaas:
    def __init__(self):
        self.subscriptions: list[dict] = []
        self.cancelled: list[str] = []
        self.pix: list[dict] = []
        self.updates: list[tuple[str, dict]] = []

    def create_subscription(self, payload: dict) -> dict:
        self.subscriptions.append(payload)
        return {"id": "sub_renovada"}

    def list_subscription_payments(self, _subscription_id: str) -> dict:
        return {"data": [{"id": "pay_1", "status": "CONFIRMED", "dueDate": "2026-10-15"}]}

    def update_subscription(self, subscription_id: str, payload: dict) -> dict:
        self.updates.append((subscription_id, payload))
        return {"id": subscription_id}

    def cancel_subscription(self, subscription_id: str) -> None:
        self.cancelled.append(subscription_id)

    def create_pix_automatic_authorization(self, payload: dict) -> dict:
        self.pix.append(payload)
        return {"id": "auth_1", "immediateQrCode": {"payload": "pix-copia-cola", "encodedImage": "qr"}}


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(checkout, "_dispatch_meta_checkout_events", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "_notify_checkout_subscription_push", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "_notify_gateway_modified_cakto_to_asaas", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "mark_viajechat_signed", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "republish_all_user_pages", lambda *a, **k: None)


@pytest.fixture
def login_as():
    """Autentica as chamadas da API como o usuário informado."""
    sessions = []

    def _login(user_id: int) -> None:
        db = TestingSessionLocal()
        sessions.append(db)
        app.dependency_overrides[get_current_active_user] = lambda: db.get(User, user_id)

    yield _login
    app.dependency_overrides.pop(get_current_active_user, None)
    for db in sessions:
        db.close()


def _settings(db) -> None:
    db.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=[NEW_PLAN], coupons_json=[
        {"code": "DESCONTO", "title": "Desconto", "discount_type": "percent", "value": "50", "offer_keys": [], "active": True}
    ], checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    db.commit()


def _customer(
    db,
    *,
    plan="essencial",
    provider="asaas",
    cycle="monthly",
    status="active",
    legacy_amount: str | None = "49.99",
    mrr="49.99",
    created_at=BEFORE_CUTOFF,
    email="cliente@example.com",
    cpf="12345678901",
    **extra,
) -> User:
    user = User(name="Cliente Fictício", email=email, hashed_password="x", plan=plan, cpf=cpf,
                whatsapp="47999999999", address_zipcode="89000000")
    db.add(user)
    db.flush()
    sub = Subscription(
        user_id=user.id, plan=plan, provider=provider, billing_cycle=cycle, status=status,
        mrr_amount=Decimal(mrr), created_at=created_at,
        legacy_renewal_amount=Decimal(legacy_amount) if legacy_amount is not None else None,
        valid_until=datetime.now(timezone.utc) + timedelta(days=10),
        **extra,
    )
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    return user


def _card() -> dict:
    return {"holder_name": "Cliente", "card_number": "4111111111111111", "expiry_month": "12", "expiry_year": "2030",
            "ccv": "123", "installment_count": 1, "remote_ip": "200.1.2.3"}


# ---------------------------------------------------------------- quem é legado


def test_info_by_provider():
    asaas = Subscription(plan="essencial", provider="asaas", status="inactive", legacy_renewal_amount=Decimal("49.99"),
                         mrr_amount=0, created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(asaas).mode == "panel" and legacy_renewal_info(asaas).amount == Decimal("49.99")
    # Cliente novo (sem valor gravado) não é legado.
    new = Subscription(plan="scale", provider="asaas", status="active", mrr_amount=Decimal("137"), created_at=AFTER_CUTOFF)
    assert legacy_renewal_info(new).legacy is False
    # Plano teste nunca é legado.
    test = Subscription(plan="teste", provider="asaas", status="active", legacy_renewal_amount=Decimal("49.99"), created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(test).legacy is False
    # Cakto ainda cobrando: renovar no Asaas cobraria duas vezes.
    cakto_active = Subscription(plan="growth", provider="cakto", status="active", legacy_renewal_amount=Decimal("89.99"),
                                mrr_amount=Decimal("89.99"), created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(cakto_active).mode == "external"
    for status in ("past_due", "cancel_at_period_end"):
        cakto = Subscription(plan="growth", provider="cakto", status=status, legacy_renewal_amount=Decimal("89.99"), created_at=BEFORE_CUTOFF)
        assert legacy_renewal_info(cakto).mode == "external"
    cakto_ended = Subscription(plan="growth", provider="cakto", status="cancelled", legacy_renewal_amount=Decimal("89.99"),
                               mrr_amount=0, created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(cakto_ended).mode == "panel"
    cakto_no_value = Subscription(plan="growth", provider="cakto", status="inactive", mrr_amount=0, created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(cakto_no_value).mode == "support" and legacy_renewal_info(cakto_no_value).amount is None
    viajeon = Subscription(plan="infinity", provider="viajeon", status="active", mrr_amount=Decimal("100"), created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(viajeon).mode == "external" and legacy_renewal_info(viajeon).amount is None
    # Conta administrativa/teste sem pagamento continua como hoje.
    manual_admin = Subscription(plan="infinity", provider="manual", status="active", mrr_amount=0, created_at=BEFORE_CUTOFF)
    assert legacy_renewal_info(manual_admin).legacy is False


def test_billing_me_returns_legacy_fields(client, login_as):
    db = TestingSessionLocal()
    user = _customer(db, plan="agency", legacy_amount="89.99", mrr="0", status="inactive")
    login_as(user.id)

    body = client.get("/api/v1/billing/me").json()

    assert body["legacy"] is True
    assert Decimal(body["legacy_renewal_amount"]) == Decimal("89.99")
    assert body["legacy_renewal_mode"] == "panel" and body["legacy_managed_externally"] is False
    assert body["plan"] == "agency" and body["billing_cycle"] == "monthly"


def test_billing_me_external_and_not_legacy(client, login_as):
    db = TestingSessionLocal()
    external = _customer(db, plan="infinity", provider="viajeon", cycle="annual", legacy_amount=None, mrr="100.00")
    login_as(external.id)
    body = client.get("/api/v1/billing/me").json()
    assert body["legacy"] is True and body["legacy_renewal_amount"] is None
    assert body["legacy_renewal_mode"] == "external" and body["legacy_managed_externally"] is True

    new = _customer(db, plan="scale", legacy_amount=None, mrr="137.00", created_at=AFTER_CUTOFF, email="novo@example.com", cpf="98765432100")
    login_as(new.id)
    body = client.get("/api/v1/billing/me").json()
    assert body["legacy"] is False and body["legacy_renewal_mode"] is None and body["legacy_renewal_amount"] is None


# ---------------------------------------------------------------- sessão de renovação


def test_session_uses_value_from_database_not_from_client(client, login_as, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="essencial", legacy_amount="49.99", mrr="129.99")
    login_as(user.id)

    # O que o cliente mandar no corpo é ignorado: não há valor, oferta nem cupom na rota.
    response = client.post(
        "/api/v1/checkout/public/session/legacy-renewal",
        json={"amount": "1.00", "offer_key": "roteiro-online-mensal", "coupon_code": "DESCONTO"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert Decimal(body["amount"]) == Decimal("49.99")
    assert body["offer_key"] == LEGACY_RENEWAL_OFFER_KEY and body["is_legacy_renewal"] is True and body["is_upgrade"] is True
    assert body["first_payment_amount"] is None and body["applied_coupon_code"] is None
    assert [option["count"] for option in body["installment_options"]] == [1]
    assert "Roteiro Online" not in body["product_name"] and body["product_name"] == "Renovação do plano Profissional"
    session = db.query(CheckoutSession).filter(CheckoutSession.token == body["token"]).one()
    assert session.plan_key == "essencial" and session.billing_cycle == "monthly"
    assert session.metadata_json["legacy_renewal"] is True and session.metadata_json["target_user_id"] == user.id

    config = client.get("/api/v1/checkout/public/legacy-renewal/config").json()
    assert Decimal(config["offer"]["amount"]) == Decimal("49.99") and config["offer"]["first_payment_amount"] is None


def test_session_keeps_annual_cycle_and_value(client, login_as, quiet):
    db = TestingSessionLocal()
    user = _customer(db, plan="scale", cycle="annual", legacy_amount="1644.00", mrr="137.00")
    login_as(user.id)
    body = client.post("/api/v1/checkout/public/session/legacy-renewal").json()
    assert Decimal(body["amount"]) == Decimal("1644.00") and body["billing_cycle"] == "annual"
    assert [option["count"] for option in body["installment_options"]] == [1]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"plan": "free", "legacy_amount": None, "mrr": "0"}, 400),  # sem plano pago para renovar
        ({"plan": "teste", "legacy_amount": "5.00", "mrr": "5.00"}, 400),
        ({"plan": "infinity", "provider": "viajeon", "legacy_amount": None, "mrr": "100.00"}, 400),
        ({"plan": "essencial", "provider": "manual", "legacy_amount": None, "mrr": "49.99"}, 400),
        ({"plan": "essencial", "provider": "stripe", "legacy_amount": "49.99", "mrr": "49.99"}, 400),
        ({"plan": "growth", "provider": "cakto", "status": "active", "legacy_amount": "89.99", "mrr": "89.99"}, 400),
        ({"plan": "growth", "provider": "cakto", "status": "inactive", "legacy_amount": None, "mrr": "0"}, 400),
    ],
)
def test_session_is_refused(client, login_as, quiet, kwargs, expected):
    db = TestingSessionLocal()
    user = _customer(db, **kwargs)
    login_as(user.id)
    response = client.post("/api/v1/checkout/public/session/legacy-renewal")
    assert response.status_code == expected, response.text
    assert db.query(CheckoutSession).count() == 0
    assert client.get("/api/v1/checkout/public/legacy-renewal/config").status_code == expected


def test_renewal_session_cannot_be_recreated_as_public_offer(client):
    db = TestingSessionLocal()
    _settings(db)
    response = client.get(f"/api/v1/checkout/public/config/{LEGACY_RENEWAL_OFFER_KEY}")
    assert response.status_code == 404


# ---------------------------------------------------------------- depois do pagamento


def test_card_payment_keeps_plan_value_and_legacy_amount(monkeypatch, quiet):
    db = TestingSessionLocal()
    user = _customer(db, plan="essencial", legacy_amount="49.99", mrr="129.99", asaas_subscription_id="sub_antiga")
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    from app.services.legacy_renewal import create_legacy_renewal_checkout_session

    session = create_legacy_renewal_checkout_session(db, db.get(User, user.id))
    session.asaas_customer_id = "cus_1"
    db.commit()
    result = checkout.start_card_payment(db, session, _card())

    assert result.status == "paid"
    assert fake.subscriptions[0]["value"] == 49.99 and fake.subscriptions[0]["cycle"] == "MONTHLY"
    assert fake.updates == []  # nada passa ao valor de outra oferta depois
    assert fake.cancelled == ["sub_antiga"]
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "essencial" and db.get(User, user.id).plan == "essencial"
    assert sub.legacy_renewal_amount == Decimal("49.99")
    assert sub.mrr_amount == Decimal("49.99") and sub.status == "active" and sub.provider == "asaas"
    assert sub.asaas_subscription_id == "sub_renovada"
    assert legacy_renewal_info(sub).mode == "panel"  # renova de novo pelo mesmo valor


def test_annual_payment_keeps_annual_value_and_monthly_mrr(monkeypatch, quiet):
    db = TestingSessionLocal()
    user = _customer(db, plan="scale", cycle="annual", legacy_amount="1644.00", mrr="137.00", status="inactive")
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    from app.services.legacy_renewal import create_legacy_renewal_checkout_session

    session = create_legacy_renewal_checkout_session(db, db.get(User, user.id))
    session.asaas_customer_id = "cus_1"
    db.commit()
    checkout.start_card_payment(db, session, _card())

    assert fake.subscriptions[0]["value"] == 1644.0 and fake.subscriptions[0]["cycle"] == "YEARLY"
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "scale" and sub.billing_cycle == "annual" and sub.legacy_renewal_amount == Decimal("1644.00")
    assert sub.mrr_amount == Decimal("137.00")


def test_pix_automatic_uses_legacy_value_without_promo(monkeypatch, quiet):
    db = TestingSessionLocal()
    _settings(db)
    user = _customer(db, plan="agency", legacy_amount="89.99", mrr="0", status="inactive")
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    from app.services.legacy_renewal import create_legacy_renewal_checkout_session

    session = create_legacy_renewal_checkout_session(db, db.get(User, user.id))
    session.asaas_customer_id = "cus_1"
    db.commit()
    checkout.start_pix_payment(db, session)

    assert fake.pix[0]["value"] == 89.99 and fake.pix[0]["immediateQrCode"]["originalValue"] == 89.99
    assert fake.pix[0]["frequency"] == "MONTHLY"


def test_cakto_renewal_converts_to_asaas_and_detaches_cakto(monkeypatch, quiet):
    db = TestingSessionLocal()
    user = _customer(db, plan="growth", provider="cakto", status="cancelled", legacy_amount="89.99", mrr="0",
                     cakto_subscription_code="cakto_sub_1", cakto_order_id="cakto_order_1", cakto_offer_id="oferta_1")
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    from app.services.legacy_renewal import create_legacy_renewal_checkout_session

    session = create_legacy_renewal_checkout_session(db, db.get(User, user.id))
    session.asaas_customer_id = "cus_1"
    db.commit()
    result = checkout.start_card_payment(db, session, _card())

    assert result.status == "paid" and fake.subscriptions[0]["value"] == 89.99
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.provider == "asaas" and sub.plan == "growth" and sub.status == "active"
    assert sub.cakto_subscription_code is None and sub.cakto_order_id is None
    assert sub.legacy_renewal_amount == Decimal("89.99") and sub.mrr_amount == Decimal("89.99")
    saved = db.query(CheckoutSession).filter(CheckoutSession.token == session.token).one().metadata_json["replaced_cakto"]
    assert saved["subscription_code"] == "cakto_sub_1" and saved["order_id"] == "cakto_order_1"


# ---------------------------------------------------------------- regra do SQL de preenchimento

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "2026-10-15_legacy_renewal_amount.sql"
PG_URL = os.environ.get("LEGACY_SQL_TEST_DATABASE_URL")

FIXTURE = """
DROP TABLE IF EXISTS subscriptions, asaas_event_logs, checkout_sessions;
CREATE TABLE subscriptions (
  id serial primary key, user_id int not null, plan varchar(50) not null, provider varchar(50) not null,
  asaas_subscription_id varchar(120), billing_cycle varchar(20) not null, status varchar(50) not null,
  mrr_amount numeric(12,2) not null default 0, created_at timestamptz);
CREATE TABLE asaas_event_logs (id serial primary key, event_type varchar(120), payload json not null, created_at timestamptz);
CREATE TABLE checkout_sessions (id serial primary key, user_id int, plan_key varchar(50), amount numeric(12,2), paid_at timestamptz);
INSERT INTO subscriptions (id, user_id, plan, provider, asaas_subscription_id, billing_cycle, status, mrr_amount, created_at) VALUES
 (1, 1, 'essencial', 'asaas', 'sub_a', 'monthly', 'active', 49.99, '2026-05-01'),
 (2, 2, 'agency', 'asaas', 'sub_b', 'monthly', 'inactive', 0, '2026-04-01'),
 (3, 3, 'scale', 'asaas', 'sub_c', 'monthly', 'active', 49.99, '2026-03-01'),
 (4, 4, 'infinity', 'asaas', NULL, 'monthly', 'active', 116.99, '2026-02-01'),
 (5, 5, 'infinity', 'asaas', NULL, 'annual', 'active', 137.00, '2026-07-01'),
 (6, 6, 'growth', 'asaas', NULL, 'monthly', 'inactive', 0, '2026-01-01'),
 (7, 7, 'teste', 'asaas', 'sub_g', 'monthly', 'active', 5, '2026-01-01'),
 (8, 8, 'essencial', 'cakto', NULL, 'monthly', 'inactive', 89.99, '2026-01-01'),
 (9, 9, 'growth', 'cakto', NULL, 'monthly', 'cancelled', 0, '2026-01-01'),
 (10, 10, 'infinity', 'viajeon', NULL, 'monthly', 'active', 100, '2026-08-01'),
 (11, 11, 'infinity', 'asaas', 'sub_k', 'monthly', 'active', 137, '2026-10-16'),
 (12, 12, 'essencial', 'asaas', 'sub_l', 'monthly', 'active', 49.99, '2026-06-01'),
 (13, 13, 'infinity', 'asaas', 'sub_m', 'monthly', 'inactive', 0, '2026-03-01'),
 (14, 14, 'essencial', 'asaas', 'sub_n', 'monthly', 'active', 49.99, '2026-06-01'),
 (15, 15, 'agency', 'asaas', 'sub_o', 'monthly', 'active', 89.99, '2026-06-01'),
 (16, 16, 'growth', 'cakto', NULL, 'annual', 'inactive', 75.00, '2026-01-01');
INSERT INTO asaas_event_logs (event_type, payload, created_at) VALUES
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_a","value":45.00,"paymentDate":"2026-07-01"}}', '2026-07-01'),
 ('PAYMENT_RECEIVED', '{"payment":{"subscription":"sub_a","value":49.99,"paymentDate":"2026-09-01"}}', '2026-09-01'),
 ('PAYMENT_OVERDUE', '{"payment":{"subscription":"sub_a","value":99.00,"paymentDate":"2026-10-01"}}', '2026-10-01'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_a","value":"abc","paymentDate":"xx"}}', '2026-08-01'),
 ('PAYMENT_CONFIRMED', '"payload sem objeto"', '2026-08-01'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_b","value":71.99,"paymentDate":"2026-06-19"}}', '2026-06-19'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_c","value":129.99}}', '2026-09-20'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_m","value":5.0,"paymentDate":"2026-06-09"}}', '2026-06-09'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_n","value":129.99,"paymentDate":"2026-08-26"}}', '2026-08-26'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_o","value":89.99,"paymentDate":"2026-09-10"}}', '2026-09-10'),
 ('PAYMENT_CONFIRMED', '{"payment":{"subscription":"sub_o","value":137.00,"paymentDate":"2026-10-20"}}', '2026-10-20');
INSERT INTO checkout_sessions (user_id, plan_key, amount, paid_at) VALUES
 (2, 'agency', 89.99, '2026-07-21 12:00-03'),
 (5, 'scale', 1644.00, '2026-07-27 10:00-03'),
 (12, 'scale', 137.00, '2026-10-15 09:00-03'),
 (13, 'professional', 5.00, '2026-06-09 10:00-03'),
 (14, 'professional', 49.99, '2026-08-26 15:00-03'),
 (1, 'professional', 0, NULL);
"""

EXPECTED = {
    1: Decimal("49.99"),  # último pagamento Asaas antes do corte (eventos que não são pagamento não contam)
    2: Decimal("89.99"),  # compra no checkout mais recente que o pagamento Asaas
    3: Decimal("129.99"),  # pagamento Asaas vale mais que o mrr defasado
    4: Decimal("116.99"),  # sem pagamento: mrr mensal
    5: Decimal("1644.00"),  # anual: valor do ano
    6: None,  # sem pagamento e sem mrr
    7: None,  # plano teste
    8: Decimal("89.99"),  # Cakto: mrr mensal
    9: None,  # Cakto sem valor
    10: None,  # ViajeOn não entra
    11: None,  # criada depois do corte
    12: None,  # comprou no checkout depois do corte
    13: None,  # valor de teste (R$ 5,00)
    14: Decimal("49.99"),  # empate no mesmo dia: vale a compra do checkout
    15: Decimal("89.99"),  # pagamento depois do corte não conta
    16: None,  # Cakto anual: mrr é do mês, não do ano
}


@pytest.mark.skipif(not PG_URL, reason="Defina LEGACY_SQL_TEST_DATABASE_URL (Postgres descartável) para testar o SQL.")
def test_backfill_sql_rule_on_postgres():
    import psycopg2

    script = SQL_FILE.read_text(encoding="utf-8")
    connection = psycopg2.connect(PG_URL)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(FIXTURE)
            cursor.execute(script)
            cursor.execute("SELECT id, legacy_renewal_amount FROM subscriptions ORDER BY id")
            first = dict(cursor.fetchall())
            assert first == EXPECTED
            # Rodar de novo não muda nada, nem o valor já gravado (mesmo se alguém corrigiu à mão).
            cursor.execute("UPDATE subscriptions SET legacy_renewal_amount = 77.77 WHERE id = 1")
            cursor.execute(script)
            cursor.execute("SELECT id, legacy_renewal_amount FROM subscriptions ORDER BY id")
            assert dict(cursor.fetchall()) == {**EXPECTED, 1: Decimal("77.77")}
            # Funciona também com payload em jsonb.
            cursor.execute("ALTER TABLE asaas_event_logs ALTER COLUMN payload TYPE jsonb USING payload::jsonb")
            cursor.execute("UPDATE subscriptions SET legacy_renewal_amount = NULL")
            cursor.execute(script)
            cursor.execute("SELECT id, legacy_renewal_amount FROM subscriptions ORDER BY id")
            assert dict(cursor.fetchall()) == EXPECTED
            cursor.execute("DROP TABLE subscriptions, asaas_event_logs, checkout_sessions")
    finally:
        connection.close()
