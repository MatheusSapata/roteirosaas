from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.checkout import CheckoutSession
from app.services import checkout


class FakeDb:
    def add(self, _instance) -> None:
        return None

    def commit(self) -> None:
        return None

    def refresh(self, _instance) -> None:
        return None


class FakePixAutomaticClient:
    def __init__(self, *, include_qr: bool = True) -> None:
        self.include_qr = include_qr
        self.authorization_payloads: list[dict] = []

    def create_pix_automatic_authorization(self, payload: dict) -> dict:
        self.authorization_payloads.append(payload)
        immediate_qr = {
            "encodedImage": "base64-qr",
            "expirationDate": "2026-07-21T20:00:00Z",
        }
        if self.include_qr:
            immediate_qr["payload"] = "pix-copy-paste"
        return {"id": "auth_automatic_123", "immediateQrCode": immediate_qr}

    def create_payment(self, _payload: dict) -> dict:
        raise AssertionError("PIX convencional avulso não pode ser criado pelo checkout")

    def create_subscription(self, _payload: dict) -> dict:
        raise AssertionError("Fallback para assinatura PIX convencional não pode ser usado")


def make_session(*, upgrade: bool = False, cycle: str = "monthly") -> CheckoutSession:
    return CheckoutSession(
        token="checkout-token-123",
        offer_key="growth-monthly",
        product_name="Plano Growth",
        plan_key="growth",
        billing_cycle=cycle,
        amount=Decimal("99.90"),
        status="draft",
        customer_name="Cliente Teste",
        customer_email="cliente@example.com",
        customer_document="12345678901",
        customer_phone="47999999999",
        customer_zipcode="89000000",
        asaas_customer_id="cus_automatic_123",
        metadata_json={"upgrade_mode": True} if upgrade else {},
    )


def configure_pix_dependencies(monkeypatch: pytest.MonkeyPatch, client: FakePixAutomaticClient) -> None:
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: client)
    monkeypatch.setattr(checkout, "_raise_if_registered_checkout_identity", lambda _db, _session: None)
    monkeypatch.setattr(checkout, "_resolve_target_subscription_for_upgrade", lambda _db, _session: None)


@pytest.mark.parametrize(
    ("cycle", "expected_frequency"),
    [("monthly", "MONTHLY"), ("annual", "ANNUALLY")],
)
def test_pix_checkout_always_creates_automatic_authorization(
    monkeypatch: pytest.MonkeyPatch,
    cycle: str,
    expected_frequency: str,
) -> None:
    client = FakePixAutomaticClient()
    configure_pix_dependencies(monkeypatch, client)
    session = make_session(cycle=cycle)

    result = checkout.start_pix_payment(FakeDb(), session)

    assert result.payment_method == "pix"
    assert result.status == "awaiting_payment"
    assert result.pix_copy_paste == "pix-copy-paste"
    assert result.metadata_json["pix_mode"] == "automatic"
    assert result.metadata_json["asaas_pix_automatic_authorization_id"] == "auth_automatic_123"
    payload = client.authorization_payloads[0]
    assert payload["frequency"] == expected_frequency
    assert payload["value"] == 99.90
    assert payload["immediateQrCode"]["originalValue"] == 99.90
    assert payload["immediateQrCode"]["paymentCreationMode"] == "SUBSCRIPTION"
    assert "paymentCreationMode" not in payload


def test_pix_upgrade_also_uses_automatic_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakePixAutomaticClient()
    configure_pix_dependencies(monkeypatch, client)
    session = make_session(upgrade=True)

    result = checkout.start_pix_payment(FakeDb(), session)

    assert len(client.authorization_payloads) == 1
    assert result.metadata_json["pix_mode"] == "automatic"
    assert result.metadata_json["upgrade_in_place"] is False


def test_pix_checkout_never_falls_back_to_conventional_pix(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakePixAutomaticClient(include_qr=False)
    configure_pix_dependencies(monkeypatch, client)

    with pytest.raises(HTTPException) as exc_info:
        checkout.start_pix_payment(FakeDb(), make_session())

    assert exc_info.value.status_code == 502
    assert "Nenhuma cobranca PIX convencional" in str(exc_info.value.detail)


def test_existing_automatic_authorization_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakePixAutomaticClient()
    configure_pix_dependencies(monkeypatch, client)
    session = make_session()
    session.payment_method = "pix"
    session.status = "awaiting_payment"
    session.metadata_json = {
        "pix_mode": "automatic",
        "asaas_pix_automatic_authorization_id": "auth_existing",
    }

    result = checkout.start_pix_payment(FakeDb(), session)

    assert result is session
    assert client.authorization_payloads == []


@pytest.mark.parametrize(
    "payload",
    [
        {"authorization": {"id": "auth_webhook_123"}},
        {"pixAutomaticAuthorization": "auth_webhook_123"},
        {"payment": {"pixAutomaticAuthorizationId": "auth_webhook_123"}},
        {"paymentInstruction": {"authorization": {"id": "auth_webhook_123"}}},
    ],
)
def test_extracts_automatic_pix_authorization_from_webhook_variants(payload: dict) -> None:
    assert checkout._extract_pix_automatic_authorization_id(payload) == "auth_webhook_123"
