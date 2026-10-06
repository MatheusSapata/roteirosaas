from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services import subscription as subscription_service
from app.services.asaas import AsaasAPIError
from tests.conftest import TestingSessionLocal

TOKEN = "T" * 32


class FakeAsaasClient:
    created: list[dict] = []
    existing: list[dict] = []
    fail_with: str | None = None
    reject_split: bool = False

    def __init__(self, *_args, **_kwargs) -> None:
        return None

    def list_payments(self, **params) -> dict:
        assert params["externalReference"] == f"co:{TOKEN}"
        return {"data": list(self.existing)}

    def create_payment(self, payload: dict) -> dict:
        if self.fail_with:
            raise AsaasAPIError({"errors": [{"description": self.fail_with}]})
        if self.reject_split and "split" in payload:
            raise AsaasAPIError({"errors": [{"code": "invalid_split", "description": "split não permitido"}]})
        self.created.append(payload)
        return {"id": f"pay_{len(self.created)}", "status": "PENDING"}


@pytest.fixture(autouse=True)
def _fake_asaas(monkeypatch: pytest.MonkeyPatch):
    FakeAsaasClient.created = []
    FakeAsaasClient.existing = []
    FakeAsaasClient.fail_with = None
    FakeAsaasClient.reject_split = False
    monkeypatch.setattr(subscription_service, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(subscription_service, "AsaasClient", FakeAsaasClient)
    monkeypatch.setattr(subscription_service.settings, "asaas_api_key", "test-key")
    monkeypatch.setattr(subscription_service, "build_default_split_payload", lambda: [{"walletId": "w", "percentualValue": 34.0}])


def _setup(db, *, due: str, sub_status: str = "active", method: str = "pix", reference: str | None = None) -> CheckoutSession:
    user = User(email="cliente@example.com", name="Cliente", hashed_password="x", plan="scale", is_active=True)
    db.add(user)
    db.flush()
    sub = Subscription(
        user_id=user.id,
        provider="asaas",
        plan="scale",
        status=sub_status,
        billing_cycle="monthly",
        payment_method_type=method,
        external_reference=reference or f"checkout:{TOKEN}",
        asaas_customer_id="cus_1",
    )
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    session = CheckoutSession(
        token=TOKEN,
        offer_key="escala-mensal",
        product_name="Plano Escala",
        plan_key="scale",
        billing_cycle="monthly",
        amount=Decimal("129.90"),
        status="paid",
        payment_method="pix",
        customer_name="Cliente",
        customer_email="cliente@example.com",
        customer_document="12345678901",
        customer_phone="47999999999",
        customer_zipcode="89000000",
        asaas_customer_id="cus_1",
        user_id=user.id,
        paid_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
        metadata_json={
            "pix_mode": "automatic",
            "asaas_pix_automatic_authorization_id": "auth_1",
            "asaas_pix_automatic_authorization_status": "ACTIVE",
            "asaas_pix_automatic_next_due_date": due,
        },
    )
    db.add(session)
    db.commit()
    return session


def _metadata(db) -> dict:
    db.expire_all()
    return dict(db.query(CheckoutSession).first().metadata_json)


def test_creates_charge_linked_to_authorization_and_advances_due_date(db_session):
    _setup(db_session, due="2026-09-03")  # quinta-feira
    created = subscription_service.create_due_pix_automatic_charges(today=date(2026, 8, 25))
    assert created == 1
    assert FakeAsaasClient.created == [
        {
            "customer": "cus_1",
            "billingType": "PIX",
            "value": 129.9,
            "dueDate": "2026-09-03",
            "description": "Renovação Plano Escala",
            "externalReference": f"co:{TOKEN}",
            "pixAutomaticAuthorizationId": "auth_1",
            "split": [{"walletId": "w", "percentualValue": 34.0}],
        }
    ]
    metadata = _metadata(db_session)
    assert metadata["asaas_pix_automatic_renewal_payment_ids"] == ["pay_1"]
    assert metadata["asaas_pix_automatic_next_due_date"] == "2026-10-03"
    # Rodar de novo no mesmo dia não cria outra cobrança.
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 8, 25)) == 0
    assert len(FakeAsaasClient.created) == 1


def test_waits_until_inside_the_ten_business_day_window(db_session):
    _setup(db_session, due="2026-09-30")
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 9, 1)) == 0
    assert FakeAsaasClient.created == []


def test_due_date_too_close_is_moved_to_three_business_days_ahead(db_session):
    _setup(db_session, due="2026-09-02")
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 9, 1)) == 1  # terça
    assert FakeAsaasClient.created[0]["dueDate"] == "2026-09-04"  # sexta
    assert _metadata(db_session)["asaas_pix_automatic_next_due_date"] == "2026-10-02"


def test_recently_missed_cycle_is_recovered(db_session):
    _setup(db_session, due="2026-08-28")
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 9, 1)) == 1
    assert FakeAsaasClient.created[0]["dueDate"] == "2026-09-04"


def test_old_missed_cycle_is_not_charged_and_is_flagged_for_review(db_session):
    _setup(db_session, due="2026-07-01")
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 9, 1)) == 0
    assert FakeAsaasClient.created == []
    assert _metadata(db_session)["asaas_pix_automatic_renewal_needs_review"] == "2026-07-01"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"sub_status": "cancel_at_period_end"}, "assinatura cancelada"),
        ({"sub_status": "cancelled"}, "assinatura cancelada"),
        ({"method": "card"}, "assinatura atual não é Pix"),
        ({"reference": "checkout:" + "X" * 32}, "assinatura atual veio de outro checkout"),
        ({"reference": "scheduled_downgrade:essencial"}, "downgrade agendado: revisar o valor antes de cobrar"),
    ],
)
def test_does_not_charge_when_subscription_no_longer_uses_this_authorization(db_session, kwargs, reason):
    _setup(db_session, due="2026-09-03", **kwargs)
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 8, 25)) == 0
    assert FakeAsaasClient.created == []
    assert _metadata(db_session)["asaas_pix_automatic_renewal_skipped"] == reason


def test_reuses_charge_that_already_exists_in_asaas(db_session):
    _setup(db_session, due="2026-09-03")
    FakeAsaasClient.existing = [{"id": "pay_existente", "dueDate": "2026-09-03", "status": "PENDING"}]
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 8, 25)) == 1
    assert FakeAsaasClient.created == []
    assert _metadata(db_session)["asaas_pix_automatic_renewal_payment_ids"] == ["pay_existente"]


def test_asaas_error_keeps_due_date_and_records_error(db_session):
    _setup(db_session, due="2026-09-03")
    FakeAsaasClient.fail_with = "Autorização inválida"
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 8, 25)) == 0
    metadata = _metadata(db_session)
    assert metadata["asaas_pix_automatic_next_due_date"] == "2026-09-03"
    assert "Autorização inválida" in metadata["asaas_pix_automatic_last_error"]


def test_creates_charge_without_split_when_asaas_rejects_split(db_session):
    _setup(db_session, due="2026-09-03")
    FakeAsaasClient.reject_split = True
    assert subscription_service.create_due_pix_automatic_charges(today=date(2026, 8, 25)) == 1
    assert "split" not in FakeAsaasClient.created[0]


def test_business_day_helpers():
    assert subscription_service._business_days_between(date(2026, 9, 4), date(2026, 9, 7)) == 1  # sex -> seg
    assert subscription_service._add_business_days(date(2026, 9, 4), 3) == date(2026, 9, 9)
    assert subscription_service._business_days_between(date(2026, 9, 7), date(2026, 9, 4)) == -1
