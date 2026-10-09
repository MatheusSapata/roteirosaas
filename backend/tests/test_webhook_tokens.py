from __future__ import annotations

import pytest

from app.api import cakto as cakto_api
from app.api.v1.endpoints import billing as billing_endpoint
from app.api.v1.endpoints import whatsapp_webhooks
from app.services.evolution import EvolutionService

ASAAS_URL = "/api/v1/billing/webhook"
CAKTO_URL = "/api/cakto/webhook"
EVOLUTION_URL = "/api/v1/webhooks/whatsapp/evolution"


@pytest.fixture
def asaas_token(monkeypatch):
    monkeypatch.setattr(billing_endpoint.settings, "asaas_webhook_token", "asaas-secret")
    monkeypatch.setattr(billing_endpoint, "handle_asaas_checkout_webhook", lambda db, payload: True)
    return "asaas-secret"


def test_asaas_webhook_rejects_missing_token(client, asaas_token):
    response = client.post(ASAAS_URL, json={"id": "evt_1", "event": "PAYMENT_CONFIRMED"})
    assert response.status_code == 401


def test_asaas_webhook_rejects_wrong_token(client, asaas_token):
    response = client.post(
        ASAAS_URL,
        json={"id": "evt_2", "event": "PAYMENT_CONFIRMED"},
        headers={"asaas-access-token": "errado"},
    )
    assert response.status_code == 401


def test_asaas_webhook_accepts_valid_token(client, asaas_token):
    response = client.post(
        ASAAS_URL,
        json={"id": "evt_3", "event": "PAYMENT_CONFIRMED"},
        headers={"asaas-access-token": asaas_token},
    )
    assert response.status_code == 200


def test_asaas_webhook_requires_token_configured_in_prod(client, monkeypatch):
    monkeypatch.setattr(billing_endpoint.settings, "asaas_webhook_token", None)
    monkeypatch.setattr(billing_endpoint.settings, "env", "prod")
    response = client.post(ASAAS_URL, json={"id": "evt_4", "event": "PAYMENT_CONFIRMED"})
    assert response.status_code == 503


def test_cakto_webhook_requires_secret_configured_in_prod(client, monkeypatch):
    monkeypatch.setattr(cakto_api.settings, "cakto_webhook_secret", None)
    monkeypatch.setattr(cakto_api.settings, "env", "prod")
    response = client.post(CAKTO_URL, json={"event": "purchase_approved"})
    assert response.status_code == 503


def test_cakto_webhook_rejects_wrong_secret(client, monkeypatch):
    monkeypatch.setattr(cakto_api.settings, "cakto_webhook_secret", "cakto-secret")
    response = client.post(f"{CAKTO_URL}?token=errado", json={"event": "purchase_approved"})
    assert response.status_code == 401


@pytest.fixture
def evolution_token(monkeypatch):
    monkeypatch.setattr(whatsapp_webhooks.settings, "evolution_webhook_token", "evo-secret")
    monkeypatch.setattr(whatsapp_webhooks.settings, "whatsapp_inbox_webhooks_enabled", False)
    return "evo-secret"


@pytest.mark.parametrize("url", [EVOLUTION_URL, f"{EVOLUTION_URL}/messages-upsert"])
def test_evolution_webhook_rejects_missing_token(client, evolution_token, url):
    response = client.post(url, json={"event": "messages.upsert"})
    assert response.status_code == 401


@pytest.mark.parametrize("suffix", ["", "/messages-upsert"])
def test_evolution_webhook_accepts_token_in_path(client, evolution_token, suffix):
    response = client.post(f"{EVOLUTION_URL}/t/{evolution_token}{suffix}", json={"event": "messages.upsert"})
    assert response.status_code == 200


@pytest.mark.parametrize("suffix", ["", "/messages-upsert"])
def test_evolution_webhook_rejects_wrong_token_in_path(client, evolution_token, suffix):
    response = client.post(f"{EVOLUTION_URL}/t/errado{suffix}", json={"event": "messages.upsert"})
    assert response.status_code == 401


def test_evolution_webhook_accepts_token_in_query(client, evolution_token):
    response = client.post(f"{EVOLUTION_URL}?token={evolution_token}", json={"event": "messages.upsert"})
    assert response.status_code == 200


def test_evolution_webhook_url_gets_token_in_path(monkeypatch):
    service = EvolutionService()
    monkeypatch.setattr(service.settings, "evolution_webhook_token", "evo-secret")
    assert (
        service._authenticated_webhook_url("https://api.exemplo.com/api/v1/webhooks/whatsapp/evolution/")
        == "https://api.exemplo.com/api/v1/webhooks/whatsapp/evolution/t/evo-secret"
    )


def test_manual_password_routes_were_removed(client):
    for path in ("/api/cakto/onboarding/manual-password", "/api/cakto/onboarding/manual-password/validate"):
        response = client.post(path, json={"email": "admin@exemplo.com", "password": "NovaSenha123"})
        assert response.status_code in {404, 405}
