from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.models.checkout import CheckoutSession
from app.services import subscription as subscription_service


class FakeQuery:
    def __init__(self, rows: list[CheckoutSession]) -> None:
        self.rows = rows

    def filter(self, *_args) -> "FakeQuery":
        return self

    def all(self) -> list[CheckoutSession]:
        return self.rows


class FakeDb:
    def __init__(self, rows: list[CheckoutSession]) -> None:
        self.rows = rows

    def query(self, _model) -> FakeQuery:
        return FakeQuery(self.rows)

    def add(self, _instance) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


class FakeAsaasClient:
    payloads: list[dict] = []

    def __init__(self, *_args, **_kwargs) -> None:
        return None

    def create_pix_automatic_payment_instruction(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"id": "pai_automatic_123", "status": "AWAITING_REQUEST"}


def test_pix_automatic_renewal_job_creates_instruction_and_advances_due_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout_session = CheckoutSession(
        id=1,
        token="checkout-token-123",
        offer_key="growth-monthly",
        product_name="Plano Growth",
        plan_key="growth",
        billing_cycle="monthly",
        amount=Decimal("99.90"),
        status="paid",
        payment_method="pix",
        customer_name="Cliente",
        customer_email="cliente@example.com",
        customer_document="12345678901",
        customer_phone="47999999999",
        customer_zipcode="89000000",
        metadata_json={
            "pix_mode": "automatic",
            "asaas_pix_automatic_authorization_id": "auth_automatic_123",
            "asaas_pix_automatic_authorization_status": "ACTIVE",
            "asaas_pix_automatic_next_due_date": "2026-08-25",
        },
    )
    fake_db = FakeDb([checkout_session])
    FakeAsaasClient.payloads = []
    monkeypatch.setattr(subscription_service, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(subscription_service, "AsaasClient", FakeAsaasClient)
    monkeypatch.setattr(subscription_service.settings, "asaas_api_key", "test-key")

    created = subscription_service.create_due_pix_automatic_instructions(today=date(2026, 8, 20))

    assert created == 1
    assert FakeAsaasClient.payloads == [
        {
            "pixAutomaticAuthorizationId": "auth_automatic_123",
            "value": 99.9,
            "dueDate": "2026-08-25",
            "description": "Renovação assinatura - Roteiro Onli",
            "externalReference": "co:checkout-token-123",
        }
    ]
    assert checkout_session.metadata_json["asaas_pix_automatic_last_instruction_id"] == "pai_automatic_123"
    assert checkout_session.metadata_json["asaas_pix_automatic_next_due_date"] == "2026-09-25"
