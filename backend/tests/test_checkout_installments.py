"""Anual parcelado no cartão (12x de R$ 97 fixo, demais parcelas repassando as taxas do Asaas),
1ª mensalidade promocional, migração de plano pelo painel e renovações no cartão."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.checkout import CheckoutSession, CheckoutSettings
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.checkout import CheckoutOfferIn, CheckoutOfferOut
from app.services import checkout
from app.services.card_installments import installment_options
from tests.conftest import TestingSessionLocal

ANNUAL = {
    "key": "roteiro-online-anual",
    "title": "Roteiro Online anual",
    "footer_product_label": "Roteiro Online",
    "plan_key": "scale",
    "billing_cycle": "annual",
    "amount": "997.00",
    "active": True,
    "checkout_key": "default",
    "max_installments": 12,
    "installment_fixed_values": {"12": "97.00"},
}
MONTHLY = {
    "key": "roteiro-online-mensal",
    "title": "Roteiro Online mensal",
    "footer_product_label": "Roteiro Online",
    "plan_key": "scale",
    "billing_cycle": "monthly",
    "amount": "137.00",
    "active": True,
    "checkout_key": "default",
    "first_payment_amount": "67.00",
}


def _aware(value: datetime) -> datetime:
    """O SQLite dos testes devolve datas sem fuso (o Postgres devolve com)."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class FakeAsaas:
    def __init__(self, *, status: str = "CONFIRMED", token: str | None = "tok_card", existing: list | None = None, fail_update: bool = False):
        self.status = status
        self.token = token
        self.existing = existing or []
        self.fail_update = fail_update
        self.payments: list[dict] = []
        self.subscriptions: list[dict] = []
        self.updates: list[tuple[str, dict]] = []
        self.cancelled: list[str] = []
        self.pix: list[dict] = []

    def create_payment(self, payload: dict) -> dict:
        self.payments.append(payload)
        response = {"id": f"pay_{len(self.payments)}", "status": self.status}
        if payload.get("installmentCount"):
            response["installment"] = f"ins_{len(self.payments)}"
        if self.token:
            response["creditCard"] = {"creditCardToken": self.token}
        return response

    def tokenize_credit_card(self, _payload: dict) -> dict:
        return {"creditCardToken": "tok_separado"}

    def create_subscription(self, payload: dict) -> dict:
        self.subscriptions.append(payload)
        return {"id": "sub_novo"}

    def list_subscription_payments(self, _subscription_id: str) -> dict:
        return {"data": [{"id": "pay_sub_1", "status": self.status, "dueDate": "2026-10-14"}]}

    def update_subscription(self, subscription_id: str, payload: dict) -> dict:
        if self.fail_update:
            raise RuntimeError("Asaas fora")
        self.updates.append((subscription_id, payload))
        return {"id": subscription_id}

    def cancel_subscription(self, subscription_id: str) -> None:
        self.cancelled.append(subscription_id)

    def list_payments(self, **_params) -> dict:
        return {"data": self.existing}

    def create_pix_automatic_authorization(self, payload: dict) -> dict:
        self.pix.append(payload)
        return {"id": "auth_1", "immediateQrCode": {"payload": "pix-copia-cola", "encodedImage": "qr"}}


@pytest.fixture
def quiet(monkeypatch):
    """Sem rede: Meta, ViaJeChat, notificações e checagem de cadastro."""
    monkeypatch.setattr(checkout, "_dispatch_meta_checkout_events", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "_notify_checkout_subscription_push", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "mark_viajechat_signed", lambda *a, **k: None)
    monkeypatch.setattr(checkout, "_raise_if_registered_checkout_identity", lambda *_a: None)


def _settings(db, *offers: dict) -> None:
    db.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=list(offers), coupons_json=[], checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    db.commit()


def _new_session(db, offer: dict, **metadata) -> CheckoutSession:
    session = checkout.create_checkout_session(
        db,
        offer=CheckoutOfferOut.model_validate(offer),
        customer_name="Cliente",
        customer_email="cliente@example.com",
        customer_document="12345678901",
        customer_phone="47999999999",
        customer_zipcode="89000000",
        coupon_code=None,
        metadata=metadata or None,
        allow_existing_user=bool(metadata.get("upgrade_mode")),
    )
    session.asaas_customer_id = "cus_1"
    db.commit()
    return session


def _card(count: int = 1) -> dict:
    return {"holder_name": "Cliente", "card_number": "4111111111111111", "expiry_month": "12", "expiry_year": "2030", "ccv": "123", "installment_count": count, "remote_ip": "200.1.2.3"}


# ---------------------------------------------------------------- tabela de parcelas


def test_installments_follow_viajeon_table_and_fixed_value_wins():
    options = {o.count: o for o in installment_options("997.00", 12)}
    assert options[1].value == Decimal("997.00") and options[1].no_interest
    # Taxa do cartão + antecipação automática + R$ 0,49, repassadas ao cliente (igual ao Sistema Viajeon).
    assert options[12].value == Decimal("98.30") and options[12].total == Decimal("1179.60")
    assert options[2].value == Decimal("531.52")
    fixed = {o.count: o for o in installment_options("997.00", 12, {"12": "97"})}
    assert fixed[12].value == Decimal("97.00") and fixed[12].total == Decimal("1164.00")
    assert fixed[11].value == options[11].value


def test_offer_rules_per_cycle():
    monthly = CheckoutOfferIn.model_validate({**MONTHLY, "max_installments": 12, "installment_fixed_values": {"12": 97}})
    assert monthly.max_installments == 1 and monthly.installment_fixed_values == {}
    annual = CheckoutOfferIn.model_validate({**ANNUAL, "first_payment_amount": "67"})
    assert annual.first_payment_amount is None
    trimmed = CheckoutOfferIn.model_validate({**ANNUAL, "max_installments": 6})
    assert trimmed.installment_fixed_values == {}


def test_promo_must_be_below_full_price():
    with pytest.raises(HTTPException):
        checkout._validate_offer_prices([CheckoutOfferIn.model_validate({**MONTHLY, "first_payment_amount": "137.00"})])


def test_sales_plan_shows_installments_and_active_promo():
    db = TestingSessionLocal()
    ends = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    _settings(db, {**ANNUAL, "sales_slot": "annual"}, {**MONTHLY, "sales_slot": "monthly", "first_payment_ends_at": ends})
    plan = checkout.get_public_sales_plan(db)
    assert plan["annual"]["max_installments"] == 12 and plan["annual"]["installment_value"] == Decimal("97.00")
    assert plan["monthly"]["first_payment_amount"] == Decimal("67.00")


def test_promo_ends_at_deadline():
    offer = CheckoutOfferIn.model_validate({**MONTHLY, "first_payment_ends_at": "2026-10-20T23:59:00-03:00"})
    assert checkout.offer_first_payment_promo(offer, now=datetime(2026, 10, 20, 12, tzinfo=timezone.utc)) == Decimal("67.00")
    assert checkout.offer_first_payment_promo(offer, now=datetime(2026, 10, 21, 3, tzinfo=timezone.utc)) is None


# ---------------------------------------------------------------- compra


def test_annual_twelve_installments_charge_97_and_save_card(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session = _new_session(db, ANNUAL)
    options = checkout.serialize_checkout_session(db, session)["installment_options"]
    assert options[-1] == {"count": 12, "value": Decimal("97.00"), "total": Decimal("1164.00"), "no_interest": False}

    result = checkout.start_card_payment(db, session, _card(12))

    assert result.status == "paid"
    sent = fake.payments[0]
    assert sent["installmentCount"] == 12 and sent["installmentValue"] == 97.0 and "value" not in sent
    assert sent["externalReference"] == f"checkout:{session.token}"
    assert fake.subscriptions == []  # parcelado não é assinatura do Asaas
    meta = result.metadata_json
    assert meta["card_installments"] == 12 and meta["card_installment_value"] == "97.00" and meta["card_token"] == "tok_card"
    user = db.query(User).filter(User.email == "cliente@example.com").one()
    assert user.subscription.status == "active" and user.subscription.asaas_subscription_id is None
    assert user.subscription.mrr_amount == Decimal("83.08")


def test_annual_installments_reject_options_not_offered(monkeypatch, quiet):
    db = TestingSessionLocal()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: FakeAsaas())
    session = _new_session(db, {**ANNUAL, "max_installments": 6})
    with pytest.raises(HTTPException) as error:
        checkout.start_card_payment(db, session, _card(12))
    assert error.value.status_code == 400


def test_card_without_token_in_response_is_saved_separately(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas(token=None)
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    result = checkout.start_card_payment(db, _new_session(db, ANNUAL), _card(3))
    assert result.metadata_json["card_token"] == "tok_separado"


def test_monthly_promo_on_card_charges_67_then_full_price(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session = _new_session(db, MONTHLY)
    assert checkout.serialize_checkout_session(db, session)["first_payment_amount"] == Decimal("67.00")

    result = checkout.start_card_payment(db, session, _card())

    assert fake.subscriptions[0]["value"] == 67.0
    # Próximas mensalidades no valor cheio, sem mexer na cobrança de agora.
    assert fake.updates == [("sub_novo", {"value": 137.0, "updatePendingPayments": False})]
    assert "pending_subscription_value" not in result.metadata_json
    user = db.query(User).filter(User.email == "cliente@example.com").one()
    assert user.subscription.mrr_amount == Decimal("137.00")


def test_monthly_promo_update_failure_is_retried_by_the_job(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas(fail_update=True)
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    result = checkout.start_card_payment(db, _new_session(db, MONTHLY), _card())
    assert result.metadata_json["pending_subscription_value"] == "137.00"

    fake.fail_update = False
    assert checkout.apply_pending_subscription_values(db, fake) == 1
    assert fake.updates == [("sub_novo", {"value": 137.0, "updatePendingPayments": True})]
    db.expire_all()
    assert "pending_subscription_value" not in db.get(CheckoutSession, result.id).metadata_json


def test_monthly_promo_on_pix_automatic(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    checkout.start_pix_payment(db, _new_session(db, MONTHLY))
    assert fake.pix[0]["immediateQrCode"]["originalValue"] == 67.0
    assert fake.pix[0]["value"] == 137.0


def test_trial_user_subscribing_in_the_panel_gets_the_promo(quiet):
    db = TestingSessionLocal()
    _settings(db, MONTHLY)
    trial = User(name="Teste", email="teste@example.com", hashed_password="x", plan="free", cpf="12345678901")
    db.add(trial)
    db.commit()
    session = checkout.create_upgrade_checkout_session(db, offer=CheckoutOfferOut.model_validate(MONTHLY), user=trial)
    assert checkout.session_first_payment_amount(session) == Decimal("67.00")


def test_paying_customer_migrating_does_not_get_the_promo(quiet):
    db = TestingSessionLocal()
    _settings(db, MONTHLY)
    user = _subscriber(db)
    session = checkout.create_upgrade_checkout_session(db, offer=CheckoutOfferOut.model_validate(MONTHLY), user=user)
    assert checkout.session_first_payment_amount(session) is None


def test_promo_is_not_for_plan_migration_nor_expired(quiet):
    db = TestingSessionLocal()
    upgrade = _new_session(db, MONTHLY, upgrade_mode=True)
    assert checkout.session_first_payment_amount(upgrade) is None
    expired = _new_session(db, {**MONTHLY, "first_payment_ends_at": "2020-01-01T00:00:00-03:00"})
    assert checkout.session_first_payment_amount(expired) is None


# ---------------------------------------------------------------- migração de plano


def _subscriber(db, *, plan="professional", cycle="monthly", asaas_subscription_id="sub_antiga") -> User:
    user = User(name="Cliente", email="cliente@example.com", hashed_password="x", plan=plan, cpf="12345678901", whatsapp="47999999999", address_zipcode="89000000")
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, plan=plan, status="active", provider="asaas", billing_cycle=cycle,
                       asaas_subscription_id=asaas_subscription_id, mrr_amount=Decimal("49.99"),
                       valid_until=datetime.now(timezone.utc) + timedelta(days=10))
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    return user


@pytest.mark.parametrize("count", [1, 12])
def test_migration_to_annual_creates_new_contract_and_cancels_old(monkeypatch, quiet, count):
    db = TestingSessionLocal()
    user = _subscriber(db)
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session = _new_session(db, ANNUAL, upgrade_mode=True, target_user_id=user.id, current_plan="professional")

    result = checkout.start_card_payment(db, session, _card(count))

    assert result.status == "paid" and result.metadata_json["upgrade_in_place"] is False
    assert fake.cancelled == ["sub_antiga"]
    assert not any(update for update in fake.updates)  # a assinatura antiga não é reaproveitada
    db.expire_all()
    sub = db.get(User, user.id).subscription
    assert sub.plan == "scale" and sub.billing_cycle == "annual" and sub.status == "active"
    assert sub.asaas_subscription_id == (None if count > 1 else "sub_novo")
    assert sub.external_reference == f"checkout:{session.token}"


# ---------------------------------------------------------------- renovação de assinatura no cartão


def _paid_card_session(db, offer=MONTHLY, *, paid_days_ago=31) -> tuple[CheckoutSession, Subscription]:
    session = _new_session(db, offer)
    paid_at = datetime.now(timezone.utc) - timedelta(days=paid_days_ago)
    session.status = "paid"
    session.paid_at = paid_at
    session.payment_method = "card"
    session.metadata_json = {**session.metadata_json, "asaas_subscription_id": "sub_1", "first_payment_id": "pay_0"}
    user = User(name="Cliente", email="cliente@example.com", hashed_password="x", plan="scale")
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, plan="scale", status="past_due", provider="asaas", billing_cycle=session.billing_cycle,
                       asaas_subscription_id="sub_1", mrr_amount=Decimal("137"), external_reference=f"checkout:{session.token}",
                       valid_until=paid_at + timedelta(days=30))
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    session.user_id = user.id
    db.commit()
    return session, sub


def _webhook(db, session, event, payment_id, due, **extra):
    payment = {"id": payment_id, "status": "CONFIRMED" if event != "PAYMENT_CREATED" else "PENDING", "subscription": "sub_1",
               "externalReference": f"checkout:{session.token}", "dueDate": due, **extra}
    return checkout.handle_asaas_checkout_webhook(db, {"event": event, "payment": payment})


def test_card_renewal_extends_subscription_once(quiet):
    db = TestingSessionLocal()
    session, sub = _paid_card_session(db)
    due = (session.paid_at + timedelta(days=30)).date().isoformat()
    assert _webhook(db, session, "PAYMENT_CREATED", "pay_1", due)
    db.expire_all()
    assert db.get(CheckoutSession, session.id).status == "paid"  # aviso de cobrança criada não desfaz a compra

    _webhook(db, session, "PAYMENT_CONFIRMED", "pay_1", due)
    db.expire_all()
    renewed = db.get(Subscription, sub.id)
    first_valid_until = renewed.valid_until
    assert renewed.status == "active"
    assert first_valid_until.date() == date.fromisoformat(due) + timedelta(days=30) or first_valid_until.date() == date.fromisoformat(due) + timedelta(days=31)

    _webhook(db, session, "PAYMENT_RECEIVED", "pay_1", due)  # mesmo pagamento, 30 dias depois
    db.expire_all()
    assert db.get(Subscription, sub.id).valid_until == first_valid_until


def test_initial_payment_received_later_is_not_a_renewal(quiet):
    db = TestingSessionLocal()
    session, sub = _paid_card_session(db)
    before = sub.valid_until
    _webhook(db, session, "PAYMENT_RECEIVED", "pay_legado", session.paid_at.date().isoformat())
    db.expire_all()
    assert db.get(Subscription, sub.id).valid_until == before


def test_purchase_installments_do_not_touch_the_subscription(quiet):
    db = TestingSessionLocal()
    session, sub = _paid_card_session(db, ANNUAL)
    before = sub.valid_until
    _webhook(db, session, "PAYMENT_CONFIRMED", "pay_parcela_5", "2027-03-14", installment="ins_1", subscription=None)
    db.expire_all()
    assert db.get(Subscription, sub.id).valid_until == before


# ---------------------------------------------------------------- renovação do anual parcelado


def _installment_subscriber(db, *, status="active", days_overdue=0) -> tuple[CheckoutSession, Subscription]:
    session = _new_session(db, ANNUAL)
    session.status = "paid"
    session.paid_at = datetime.now(timezone.utc) - timedelta(days=365 + days_overdue)
    session.payment_method = "card"
    session.metadata_json = {**session.metadata_json, "card_installments": 12, "card_installment_value": "97.00",
                             "card_token": "tok_card", "remote_ip": "200.1.2.3", "first_payment_id": "pay_0"}
    user = User(name="Cliente", email="cliente@example.com", hashed_password="x", plan="scale")
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, plan="scale", status=status, provider="asaas", billing_cycle="annual",
                       mrr_amount=Decimal("83.08"), external_reference=f"checkout:{session.token}",
                       valid_until=datetime.now(timezone.utc) - timedelta(hours=1, days=days_overdue))
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    session.user_id = user.id
    db.commit()
    return session, sub


def test_installment_renewal_charges_same_installments_on_saved_card(quiet):
    db = TestingSessionLocal()
    session, sub = _installment_subscriber(db)
    old_valid_until = sub.valid_until
    fake = FakeAsaas()

    assert checkout.renew_due_installment_subscriptions(db, fake) == 1

    sent = fake.payments[0]
    assert sent["creditCardToken"] == "tok_card" and sent["installmentCount"] == 12 and sent["installmentValue"] == 97.0
    assert sent["externalReference"].startswith(f"checkout_renewal:{session.token}:")
    db.expire_all()
    renewed = db.get(Subscription, sub.id)
    assert renewed.status == "active" and renewed.valid_until > old_valid_until + timedelta(days=360)
    # Já renovado: a próxima rodada não cobra de novo.
    assert checkout.renew_due_installment_subscriptions(db, fake) == 0 and len(fake.payments) == 1


def test_installment_renewal_refused_tries_once_a_day(quiet):
    db = TestingSessionLocal()
    session, sub = _installment_subscriber(db)
    fake = FakeAsaas(status="REFUSED")
    checkout.renew_due_installment_subscriptions(db, fake)
    checkout.renew_due_installment_subscriptions(db, fake)  # mesmo dia
    assert len(fake.payments) == 1
    db.expire_all()
    assert db.get(CheckoutSession, session.id).metadata_json["installment_renewal"]["state"] == "failed"
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    checkout.renew_due_installment_subscriptions(db, fake, now=tomorrow)
    assert len(fake.payments) == 2


def test_installment_renewal_reuses_existing_charge(quiet):
    db = TestingSessionLocal()
    session, sub = _installment_subscriber(db)
    fake = FakeAsaas(existing=[{"id": "pay_ja", "status": "CONFIRMED"}])
    assert checkout.renew_due_installment_subscriptions(db, fake) == 1
    assert fake.payments == []


def test_cancelled_installment_subscription_is_not_charged(quiet):
    db = TestingSessionLocal()
    _installment_subscriber(db, status="cancel_at_period_end")
    fake = FakeAsaas()
    assert checkout.renew_due_installment_subscriptions(db, fake) == 0 and fake.payments == []


def test_installment_renewal_webhook_confirms_pending_charge(quiet):
    db = TestingSessionLocal()
    session, sub = _installment_subscriber(db)
    fake = FakeAsaas(status="PENDING")
    checkout.renew_due_installment_subscriptions(db, fake)
    db.expire_all()
    assert _aware(db.get(Subscription, sub.id).valid_until) < datetime.now(timezone.utc)
    reference = fake.payments[0]["externalReference"]
    checkout.handle_asaas_checkout_webhook(db, {"event": "PAYMENT_CONFIRMED", "payment": {"id": "pay_r", "status": "CONFIRMED", "installment": "ins_r", "externalReference": reference}})
    db.expire_all()
    assert _aware(db.get(Subscription, sub.id).valid_until) > datetime.now(timezone.utc) + timedelta(days=300)
