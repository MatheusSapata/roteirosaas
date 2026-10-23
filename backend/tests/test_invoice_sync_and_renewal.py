"""Conferência de fatura na hora, dívida real, uma fatura aberta por vez e renovação no contrato do
cliente. Todos os dados são fictícios."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.api.deps import get_current_active_user
from app.api.v1.endpoints import billing
from app.main import app
from app.models.asaas import AsaasEventLog
from app.models.checkout import CheckoutSession, CheckoutSettings
from app.models.revenue import RevenueTotal
from app.models.subscription import Subscription
from app.models.user import User
from app.services import billing_account, checkout
from app.services.asaas import AsaasAPIError
from tests.conftest import TestingSessionLocal

TODAY = date.today()


def day(offset: int) -> str:
    return (TODAY + timedelta(days=offset)).isoformat()


class FakeAsaas:
    def __init__(self, payments: list[dict] | None = None):
        self.payments = {item["id"]: dict(item) for item in (payments or [])}
        self.deleted: list[str] = []
        self.refuse_delete: set[str] = set()

    def get_payment(self, payment_id: str) -> dict:
        if payment_id not in self.payments:
            raise AsaasAPIError({"errors": "not found"})
        return self.payments[payment_id]

    def list_payments(self, limit=100, offset=0, **params) -> dict:
        rows = list(self.payments.values())
        if "customer" in params:
            rows = [row for row in rows if row.get("customer") == params["customer"]]
        if "status" in params:
            rows = [row for row in rows if row.get("status") == params["status"]]
        return {"data": rows[offset : offset + limit]}

    def delete_payment(self, payment_id: str) -> None:
        if payment_id in self.refuse_delete:
            raise AsaasAPIError({"errors": "paga"})
        self.deleted.append(payment_id)
        self.payments.pop(payment_id, None)


def payment(payment_id: str, *, status="PENDING", due=0, value=129.99, customer="cus_1", **extra) -> dict:
    return {
        "id": payment_id,
        "customer": customer,
        "status": status,
        "dueDate": day(due),
        "value": value,
        "billingType": "PIX",
        "dateCreated": day(due - 10),
        **extra,
    }


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(billing, "republish_all_user_pages", lambda *a, **k: None)
    monkeypatch.setattr(billing, "mark_viajechat_signed", lambda *a, **k: None)
    monkeypatch.setattr(billing, "mark_viajechat_cancelled", lambda *a, **k: None)
    monkeypatch.setattr(billing, "_notify_subscription_push", lambda *a, **k: None)
    monkeypatch.setattr(billing, "notify_payment_overdue", lambda *a, **k: None)
    monkeypatch.setattr(billing, "_last_invoice_sync", {})


@pytest.fixture
def login_as():
    sessions = []

    def _login(user_id: int) -> None:
        db = TestingSessionLocal()
        sessions.append(db)
        app.dependency_overrides[get_current_active_user] = lambda: db.get(User, user_id)

    yield _login
    app.dependency_overrides.pop(get_current_active_user, None)
    for db in sessions:
        db.close()


def customer(db, *, status="past_due", valid_until_days=-10, payment_type="pix", **extra) -> User:
    user = User(name="Cliente Fictício", email="cliente@example.com", hashed_password="x", plan="scale",
                cpf="12345678901", whatsapp="47999999999", address_zipcode="89000000")
    db.add(user)
    db.flush()
    sub = Subscription(
        user_id=user.id, plan="scale", provider="asaas", billing_cycle="monthly", status=status,
        mrr_amount=Decimal("129.99"), asaas_customer_id="cus_1", payment_method_type=payment_type,
        valid_until=datetime.now(timezone.utc) + timedelta(days=valid_until_days),
        created_at=datetime(2026, 10, 20, tzinfo=timezone.utc), **extra,
    )
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    return user


# ---------------------------------------------------------------- dívida real


def test_invoice_covered_by_paid_one_is_replaced_and_not_counted(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db)
    login_as(user.id)
    fake = FakeAsaas([
        payment("pay_refused", status="OVERDUE", due=-50, value=129.99),
        payment("pay_link", status="RECEIVED", due=-50, value=129.99, paymentDate=day(-1)),
        payment("pay_open", status="OVERDUE", due=-3, value=129.99),
        payment("pay_next", status="PENDING", due=27, value=129.99),
    ])
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: fake)

    body = client.get("/api/v1/billing/invoices").json()

    buckets = {item["id"]: item["bucket"] for item in body["items"]}
    assert buckets == {"pay_refused": "replaced", "pay_link": "paid", "pay_open": "overdue", "pay_next": "upcoming"}
    assert body["counts"] == {"paid": 1, "overdue": 1, "upcoming": 1, "replaced": 1}
    account = body["account"]
    assert account["open_amount"] == 129.99 and account["open_count"] == 1
    assert account["unlocking_invoice_id"] == "pay_open"
    assert account["next_charge"] == {"due_date": day(27), "amount": 129.99}
    assert account["status"] in {"past_due", "blocked"}
    refused = next(item for item in body["items"] if item["id"] == "pay_refused")
    assert refused["period_start"] == day(-50)


def test_invoice_cancelled_by_swap_is_replaced(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db)
    login_as(user.id)
    billing_account.mark_payment_replaced(db, "pay_old", reason="renewal")
    fake = FakeAsaas([payment("pay_old", status="OVERDUE", due=-3), payment("pay_new", status="PENDING", due=0)])
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: fake)

    body = client.get("/api/v1/billing/invoices").json()

    assert {item["id"]: item["bucket"] for item in body["items"]} == {"pay_old": "replaced", "pay_new": "upcoming"}
    assert body["account"]["open_amount"] == 0


# ---------------------------------------------------------------- conferir na hora


def test_sync_applies_paid_invoice_once(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db, asaas_subscription_id="sub_1", payment_type="card")
    login_as(user.id)
    fake = FakeAsaas([payment("pay_1", status="RECEIVED", due=-3, subscription="sub_1", paymentDate=day(0))])
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: fake)

    first = client.post("/api/v1/billing/invoices/pay_1/sync")
    assert first.status_code == 200, first.text
    assert first.json()["paid"] is True and first.json()["applied"] is True

    db.expire_all()
    sub = db.query(Subscription).one()
    assert sub.status == "active" and sub.failed_attempts == 0
    assert sub.valid_until.replace(tzinfo=None) > datetime.utcnow() + timedelta(days=20)
    assert Decimal(str(db.query(RevenueTotal).one().total_amount)) == Decimal("129.99")
    valid_until = sub.valid_until

    billing._last_invoice_sync.clear()
    second = client.post("/api/v1/billing/invoices/pay_1/sync").json()
    assert second["paid"] is True and second["applied"] is False
    db.expire_all()
    assert Decimal(str(db.query(RevenueTotal).one().total_amount)) == Decimal("129.99")
    assert db.query(Subscription).one().valid_until == valid_until


def test_sync_then_webhook_of_same_payment_does_not_repeat(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db, asaas_subscription_id="sub_1", payment_type="card")
    login_as(user.id)
    paid = payment("pay_1", status="RECEIVED", due=-3, subscription="sub_1")
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: FakeAsaas([paid]))
    monkeypatch.setattr(billing, "handle_asaas_checkout_webhook", lambda db, payload: False)

    assert client.post("/api/v1/billing/invoices/pay_1/sync").json()["applied"] is True
    client.post("/api/v1/billing/webhook", json={"event": "PAYMENT_RECEIVED", "payment": paid})

    db.expire_all()
    assert Decimal(str(db.query(RevenueTotal).one().total_amount)) == Decimal("129.99")


def test_sync_not_paid_changes_nothing(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db, asaas_subscription_id="sub_1", payment_type="card")
    login_as(user.id)
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: FakeAsaas([payment("pay_1", status="PENDING", subscription="sub_1")]))

    body = client.post("/api/v1/billing/invoices/pay_1/sync").json()

    assert body["paid"] is False and body["applied"] is False
    db.expire_all()
    assert db.query(Subscription).one().status == "past_due"


def test_sync_refuses_other_customers_invoice(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db)
    login_as(user.id)
    other = payment("pay_x", status="RECEIVED", customer="cus_other")
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: FakeAsaas([other]))

    assert client.post("/api/v1/billing/invoices/pay_x/sync").status_code == 404
    assert client.post("/api/v1/billing/invoices/pay_inexistente/sync").status_code in {404, 429}
    db.expire_all()
    assert db.query(Subscription).one().status == "past_due"


def test_sync_is_limited_to_one_call_every_10_seconds(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db)
    login_as(user.id)
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: FakeAsaas([payment("pay_1", status="PENDING")]))

    assert client.post("/api/v1/billing/invoices/pay_1/sync").status_code == 200
    assert client.post("/api/v1/billing/invoices/pay_1/sync").status_code == 429


def test_sync_pix_automatic_customer_without_subscription_is_found_by_customer(client, login_as, monkeypatch, quiet):
    db = TestingSessionLocal()
    user = customer(db)
    login_as(user.id)
    monkeypatch.setattr(billing, "_get_asaas_client", lambda: FakeAsaas([payment("pay_1", status="CONFIRMED", due=-3)]))

    body = client.post("/api/v1/billing/invoices/pay_1/sync").json()

    assert body["applied"] is True
    db.expire_all()
    assert db.query(Subscription).one().status == "active"


# ---------------------------------------------------------------- avisos que não mexem no acesso


def test_payment_created_does_not_change_active_account(client, db_session, monkeypatch, quiet):
    user = customer(db_session, status="active", valid_until_days=20, asaas_subscription_id="sub_1", payment_type="card")
    monkeypatch.setattr(billing, "handle_asaas_checkout_webhook", lambda db, payload: False)

    client.post("/api/v1/billing/webhook", json={
        "event": "PAYMENT_CREATED", "payment": payment("pay_2", subscription="sub_1", externalReference=f"{user.id}:scale:monthly"),
    })

    db_session.expire_all()
    assert db_session.query(Subscription).one().status == "active"


def test_deleting_a_replaced_charge_does_not_end_the_account(client, db_session, monkeypatch, quiet):
    user = customer(db_session, status="active", valid_until_days=20)
    billing_account.mark_payment_replaced(db_session, "pay_old", reason="renewal")
    monkeypatch.setattr(billing, "handle_asaas_checkout_webhook", lambda db, payload: False)

    client.post("/api/v1/billing/webhook", json={
        "event": "PAYMENT_DELETED", "payment": payment("pay_old", externalReference=f"{user.id}:scale:monthly"),
    })

    db_session.expire_all()
    assert db_session.query(Subscription).one().status == "active"


# ---------------------------------------------------------------- renovação no contrato do cliente


def _paid_checkout(db, user, *, amount="129.99", original="199.99", cycle="monthly", plan="scale"):
    db.add(CheckoutSession(
        token="tok-paga", offer_key="roteiro-online", product_name="Roteiro Online", plan_key=plan, billing_cycle=cycle,
        amount=Decimal(amount), status="paid", payment_method="pix", customer_name="Cliente", customer_email=user.email,
        customer_document="12345678901", customer_phone="47999999999", customer_zipcode="89000000",
        metadata_json={"original_amount": original}, user_id=user.id, paid_at=datetime.now(timezone.utc),
    ))
    db.commit()


def test_contract_offer_uses_full_value_of_last_paid_checkout(db_session):
    user = customer(db_session, status="active", valid_until_days=5)
    _paid_checkout(db_session, user, amount="99.99", original="129.99")

    offer = billing_account.current_contract_offer(db_session, user)

    assert offer.amount == Decimal("129.99") and offer.billing_cycle == "monthly" and offer.plan_key == "scale"


def test_contract_offer_falls_back_to_subscription_value(db_session):
    user = customer(db_session, status="active", valid_until_days=5)
    user.subscription.billing_cycle = "annual"
    user.subscription.mrr_amount = Decimal("100.00")
    db_session.commit()

    assert billing_account.current_contract_offer(db_session, user).amount == Decimal("1200.00")


def test_billing_me_shows_renewal_offer_and_pix_status(client, login_as, db_session, quiet):
    user = customer(db_session, status="active", valid_until_days=5)
    _paid_checkout(db_session, user)
    session = db_session.query(CheckoutSession).one()
    session.metadata_json = {**session.metadata_json, "pix_mode": "automatic", "asaas_pix_automatic_authorization_id": "auth_1",
                             "asaas_pix_automatic_authorization_status": "CANCELLED"}
    db_session.commit()
    login_as(user.id)

    body = client.get("/api/v1/billing/me").json()

    assert body["pix_automatic_status"] == "CANCELLED"
    assert body["renewal_offer"] == {"plan": "scale", "billing_cycle": "monthly", "amount": 199.99, "title": "Roteiro Online"}


def test_renewal_session_for_non_legacy_customer_uses_contract_value(client, login_as, db_session, monkeypatch, quiet):
    db_session.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=[], coupons_json=[],
                                    checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    user = customer(db_session, status="past_due")
    _paid_checkout(db_session, user, original="129.99")
    monkeypatch.setattr(checkout, "_notify_checkout_started", lambda *a, **k: None)
    login_as(user.id)

    response = client.post("/api/v1/checkout/public/session/renewal")

    assert response.status_code == 201, response.text
    body = response.json()
    assert Decimal(body["amount"]) == Decimal("129.99") and body["is_legacy_renewal"] is True
    assert body["first_payment_amount"] is None and body["applied_coupon_code"] is None
    config = client.get("/api/v1/checkout/public/renewal/config").json()
    assert Decimal(config["offer"]["amount"]) == Decimal("129.99")


def test_update_payment_method_pix_returns_renewal_session(client, login_as, db_session, monkeypatch, quiet):
    db_session.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=[], coupons_json=[],
                                    checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    user = customer(db_session, status="active", valid_until_days=5)
    _paid_checkout(db_session, user)
    monkeypatch.setattr(checkout, "_notify_checkout_started", lambda *a, **k: None)
    login_as(user.id)

    body = client.post("/api/v1/billing/update-payment-method", json={"method": "pix"}).json()

    assert body["checkout_token"]
    session = db_session.query(CheckoutSession).filter(CheckoutSession.token == body["checkout_token"]).one()
    assert session.amount == Decimal("199.99") and session.metadata_json["legacy_renewal"] is True


# ---------------------------------------------------------------- uma fatura aberta por vez


def _renewal_session(db, user) -> CheckoutSession:
    session = CheckoutSession(
        token="tok-renovacao", offer_key="renovacao-assinatura", product_name="Roteiro Online", plan_key="scale",
        billing_cycle="monthly", amount=Decimal("129.99"), status="awaiting_payment", payment_method="pix",
        customer_name="Cliente", customer_email=user.email, customer_document="12345678901",
        customer_phone="47999999999", customer_zipcode="89000000", user_id=user.id, asaas_customer_id="cus_1",
        metadata_json={"upgrade_mode": True, "legacy_renewal": True, "target_user_id": user.id},
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    return session


def test_new_charge_cancels_older_open_ones_and_marks_them_replaced(db_session):
    user = customer(db_session)
    session = _renewal_session(db_session, user)
    fake = FakeAsaas([
        payment("pay_old_overdue", status="OVERDUE", due=-20),
        payment("pay_old_pending", status="PENDING", due=-1),
        payment("pay_paid", status="RECEIVED", due=-30),
        payment("pay_new", status="PENDING", due=0, dateCreated=day(0)),
        payment("pay_other_customer", status="OVERDUE", due=-5, customer="cus_other"),
    ])

    cancelled = billing_account.cancel_open_payments(db_session, fake, customer_id="cus_1", session=session)

    assert sorted(cancelled) == ["pay_old_overdue", "pay_old_pending"]
    assert sorted(fake.deleted) == ["pay_old_overdue", "pay_old_pending"]
    assert billing_account.replaced_payment_ids(db_session, ["pay_old_overdue", "pay_paid", "pay_new"]) == {"pay_old_overdue"}


def test_charge_paid_meanwhile_is_not_cancelled_and_not_marked(db_session):
    user = customer(db_session)
    session = _renewal_session(db_session, user)
    fake = FakeAsaas([payment("pay_old", status="OVERDUE", due=-5)])
    fake.refuse_delete.add("pay_old")

    assert billing_account.cancel_open_payments(db_session, fake, customer_id="cus_1", session=session) == []
    assert billing_account.replaced_payment_ids(db_session, ["pay_old"]) == set()
    assert db_session.query(AsaasEventLog).filter(AsaasEventLog.event_id == "replaced:pay_old").first() is None


def test_checkout_start_replaces_open_charges_after_creating_the_new_one(db_session, monkeypatch):
    user = customer(db_session)
    session = _renewal_session(db_session, user)
    fake = FakeAsaas([payment("pay_old", status="OVERDUE", due=-5)])

    checkout._replace_open_payments_after_renewal(db_session, fake, session)

    assert fake.deleted == ["pay_old"]


def test_non_renewal_checkout_never_cancels_charges(db_session):
    user = customer(db_session)
    session = _renewal_session(db_session, user)
    session.metadata_json = {"upgrade_mode": True}
    fake = FakeAsaas([payment("pay_old", status="OVERDUE", due=-5)])

    checkout._replace_open_payments_after_renewal(db_session, fake, session)

    assert fake.deleted == []


# ---------------------------------------------------------------- acesso depois de renovar


@pytest.mark.parametrize(
    ("previous_status", "days_left", "expected_min_days"),
    [("active", 10, 38), ("past_due", -5, 28), ("active", -2, 28)],
)
def test_renewal_extends_from_current_due_date_only_when_in_good_standing(db_session, previous_status, days_left, expected_min_days):
    user = customer(db_session, status=previous_status, valid_until_days=days_left)
    session = _renewal_session(db_session, user)

    valid_until = checkout._renewal_valid_until(session, previous_status, user.subscription.valid_until)

    left = (valid_until - checkout._utcnow()).total_seconds() / 86400
    assert expected_min_days <= left <= expected_min_days + 3


def test_renewal_of_active_account_keeps_remaining_days(db_session):
    user = customer(db_session, status="active", valid_until_days=10)
    session = _renewal_session(db_session, user)

    valid_until = checkout._renewal_valid_until(session, "active", user.subscription.valid_until)

    assert 39 <= (valid_until - checkout._utcnow()).days + 1 <= 40
