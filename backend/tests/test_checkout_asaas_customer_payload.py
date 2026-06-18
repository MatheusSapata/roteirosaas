from __future__ import annotations

from app.services.checkout import _build_asaas_customer_payload, _find_or_create_asaas_customer


def test_build_asaas_customer_payload_includes_group_name() -> None:
    payload = _build_asaas_customer_payload(
        name="Cliente Teste",
        email="cliente@example.com",
        document="000.000.000-00",
        phone="(47) 99999-9999",
        session_token="abc123",
    )

    assert payload["groupName"] == "Roteiro Online"
    assert payload["cpfCnpj"] == "00000000000"
    assert payload["mobilePhone"] == "47999999999"
    assert payload["externalReference"] == "checkout:abc123"


def test_find_or_create_asaas_customer_sends_group_name_on_create() -> None:
    captured_payload: dict[str, object] = {}

    class FakeClient:
        def list_customers(self, **params):
            return {"data": []}

        def create_customer(self, payload):
            captured_payload.update(payload)
            return {"id": "cus_123"}

    customer_id = _find_or_create_asaas_customer(
        FakeClient(),
        session_token="token_123",
        name="Cliente Teste",
        email="cliente@example.com",
        document="000.000.000-00",
        phone="(47) 99999-9999",
    )

    assert customer_id == "cus_123"
    assert captured_payload["groupName"] == "Roteiro Online"
