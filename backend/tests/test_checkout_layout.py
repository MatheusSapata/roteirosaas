"""Modelo do checkout: "classic" (imagem na lateral) ou "banner" (banner no topo, estilo Viaje On)."""
from __future__ import annotations

from app.models.checkout import CheckoutSettings
from app.schemas.checkout import CheckoutSettingsUpdate
from app.services import checkout
from tests.conftest import TestingSessionLocal

OFFER = {
    "key": "roteiro-online-mensal",
    "title": "Roteiro Online mensal",
    "footer_product_label": "Roteiro Online",
    "plan_key": "scale",
    "billing_cycle": "monthly",
    "amount": "137.00",
    "active": True,
    "checkout_key": "vendas",
}


def _save(db, checkouts: list[dict]):
    db.add(CheckoutSettings(theme_mode="dark", is_active=True, offers_json=[], coupons_json=[], checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[]))
    db.commit()
    payload = CheckoutSettingsUpdate.model_validate({"is_active": True, "offers": [OFFER], "checkouts": checkouts})
    return checkout.update_checkout_settings(db, payload)


def test_checkout_sem_modelo_continua_classico():
    db = TestingSessionLocal()
    record = _save(db, [{"key": "vendas", "name": "Vendas", "theme_mode": "light", "active": True}])
    assert checkout._serialize_checkouts(record)[0]["layout"] == "classic"


def test_modelo_banner_e_salvo_e_vai_para_o_checkout_publico(client):
    db = TestingSessionLocal()
    _save(db, [
        {"key": "vendas", "name": "Vendas", "theme_mode": "light", "layout": "banner", "desktop_image_url": "/media/banner.webp", "active": True},
    ])
    response = client.get("/api/v1/checkout/public/config/roteiro-online-mensal")
    assert response.status_code == 200
    data = response.json()
    assert data["layout"] == "banner"
    assert data["theme_mode"] == "light"
    assert data["desktop_image_url"] == "/media/banner.webp"
