"""Plano único da página de vendas: ofertas marcadas como Mensal e Anual no Admin Master."""
from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.checkout import CheckoutSettings
from app.schemas.checkout import CheckoutSettingsUpdate
from app.services import checkout
from tests.conftest import TestingSessionLocal


def _offer(key: str, cycle: str, amount: str, *, plan: str = "scale", slot: str | None = None, active: bool = True) -> dict:
    return {
        "key": key,
        "title": f"Oferta {key}",
        "footer_product_label": "Roteiro Online",
        "plan_key": plan,
        "billing_cycle": cycle,
        "amount": amount,
        "active": active,
        "checkout_key": "default",
        **({"sales_slot": slot} if slot else {}),
    }


def _settings(db, offers: list[dict]) -> None:
    db.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=offers, coupons_json=[], checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    db.commit()


def _update(db, offers: list[dict]):
    payload = CheckoutSettingsUpdate.model_validate({"is_active": True, "offers": offers, "checkouts": checkout.DEFAULT_CHECKOUTS})
    return checkout.update_checkout_settings(db, payload)


def test_marked_offers_are_the_sales_plan():
    db = TestingSessionLocal()
    _settings(db, [
        _offer("escala_lp", "monthly", "129.99"),
        _offer("plano_mensal", "monthly", "137.00", slot="monthly"),
        _offer("plano_anual", "annual", "997.00", slot="annual"),
    ])
    plan = checkout.get_public_sales_plan(db)
    assert plan["monthly"]["key"] == "plano_mensal" and plan["monthly"]["amount"] == Decimal("137.00")
    assert plan["annual"]["key"] == "plano_anual" and plan["annual"]["amount"] == Decimal("997.00")


def test_without_marking_falls_back_to_active_scale_offer_of_the_cycle():
    db = TestingSessionLocal()
    _settings(db, [
        _offer("profissional_lp", "monthly", "49.99", plan="professional"),
        _offer("escala_velha", "monthly", "99.00", active=False),
        _offer("escala_lp", "monthly", "129.99"),
    ])
    plan = checkout.get_public_sales_plan(db)
    assert plan["monthly"]["key"] == "escala_lp"
    assert plan["annual"] is None


def test_inactive_marked_offer_is_ignored():
    db = TestingSessionLocal()
    _settings(db, [_offer("plano_mensal", "monthly", "137.00", slot="monthly", active=False)])
    assert checkout.get_public_sales_plan(db)["monthly"] is None


def test_two_offers_in_the_same_slot_are_refused():
    db = TestingSessionLocal()
    with pytest.raises(HTTPException) as err:
        _update(db, [_offer("a", "monthly", "137", slot="monthly"), _offer("b", "monthly", "120", slot="monthly")])
    assert err.value.status_code == 400 and "Só uma oferta" in err.value.detail


def test_slot_must_match_the_billing_cycle():
    db = TestingSessionLocal()
    with pytest.raises(HTTPException) as err:
        _update(db, [_offer("anual", "monthly", "997", slot="annual")])
    assert err.value.status_code == 400 and "ciclo mensal" in err.value.detail


def test_slot_is_saved_with_the_offer_and_empty_means_none():
    db = TestingSessionLocal()
    record = _update(db, [_offer("plano_anual", "annual", "997", slot="annual"), {**_offer("x", "monthly", "1"), "sales_slot": ""}])
    slots = {item["key"]: item.get("sales_slot") for item in record.offers_json}
    assert slots == {"plano_anual": "annual", "x": None}


def test_public_endpoint(client):
    db = TestingSessionLocal()
    _settings(db, [_offer("plano_mensal", "monthly", "137.00", slot="monthly"), _offer("plano_anual", "annual", "997.00", slot="annual")])
    response = client.get("/api/v1/checkout/public/sales-plan")
    assert response.status_code == 200
    body = response.json()
    assert body["monthly"]["key"] == "plano_mensal" and float(body["monthly"]["amount"]) == 137.0
    assert body["annual"]["billing_cycle"] == "annual" and float(body["annual"]["amount"]) == 997.0
