"""Endereço completo no checkout: vai para o cliente do Asaas (nota fiscal) e para o cadastro."""
from __future__ import annotations

from app.models.checkout import CheckoutSession
from app.models.user import User
from app.services import checkout
from tests.test_checkout_meta_and_utm import MONTHLY, NO_PROMO, _create, meta  # noqa: F401
from tests.test_checkout_pix_automatic import make_session

ADDRESS = {
    "street": "Rua das Flores",
    "number": "120",
    "complement": "Sala 3",
    "neighborhood": "Centro",
    "city": "Pelotas",
    "state": "RS",
}


def test_new_asaas_customer_gets_full_address() -> None:
    captured: dict = {}

    class FakeClient:
        def list_customers(self, **params):
            return {"data": []}

        def create_customer(self, payload):
            captured.update(payload)
            return {"id": "cus_123"}

    checkout._find_or_create_asaas_customer(
        FakeClient(),
        session_token="t",
        name="Cliente",
        email="c@example.com",
        document="000.000.000-00",
        phone="(53) 99157-0977",
        zipcode="96010-000",
        address=ADDRESS,
    )

    assert captured["postalCode"] == "96010000"
    assert captured["address"] == "Rua das Flores"
    assert captured["addressNumber"] == "120"
    assert captured["complement"] == "Sala 3"
    assert captured["province"] == "Centro"


def test_existing_asaas_customer_gets_address_updated_and_failure_does_not_block() -> None:
    updates: list = []

    class FakeClient:
        def list_customers(self, **params):
            return {"data": [{"id": "cus_old", "cpfCnpj": "00000000000"}]}

        def update_customer(self, customer_id, payload):
            updates.append((customer_id, payload))
            raise RuntimeError("Asaas fora")

    customer_id = checkout._find_or_create_asaas_customer(
        FakeClient(),
        session_token="t",
        name="Cliente",
        email="c@example.com",
        document="000.000.000-00",
        phone="53991570977",
        zipcode="96010000",
        address=ADDRESS,
    )

    assert customer_id == "cus_old"
    assert updates and updates[0][0] == "cus_old"


def test_session_address_goes_to_user_record() -> None:
    session = make_session()
    session.metadata_json = {"customer_address": dict(ADDRESS)}
    user = User(email="c@example.com", name="Cliente", hashed_password="x")

    checkout._apply_session_address_to_user(user, session)

    assert user.address_street == "Rua das Flores"
    assert user.address_number == "120"
    assert user.address_neighborhood == "Centro"
    assert user.address_city == "Pelotas"
    assert user.address_state == "RS"
    assert checkout.address_is_complete("96010000", checkout.user_address(user))


def test_public_session_stores_address_and_works_without_it(client, db_session, meta) -> None:
    created = _create(client, MONTHLY, customer_address={**ADDRESS, "state": "rs", "complement": "  "})
    assert created["customer_address"] == {k: v for k, v in ADDRESS.items() if k != "complement"}
    session = db_session.query(CheckoutSession).filter(CheckoutSession.token == created["token"]).one()
    assert session.metadata_json["customer_address"]["state"] == "RS"

    # Compatível com quem ainda não manda endereço (aba antiga aberta durante o deploy).
    without = _create(client, NO_PROMO)
    assert without["customer_address"] == {}


def test_address_is_complete_requires_street_number_neighborhood_city_state() -> None:
    assert checkout.address_is_complete("96010000", {}) is False
    assert checkout.address_is_complete("9601", dict(ADDRESS)) is False
    assert checkout.address_is_complete("96010000", {k: v for k, v in ADDRESS.items() if k != "complement"}) is True
