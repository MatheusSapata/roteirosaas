from __future__ import annotations

from types import SimpleNamespace

from app.api.deps import get_current_superuser
from app.main import app

BASE = "/api/v1/admin/master/image-api-keys"


def test_image_api_keys_crud_and_separation_from_flight_keys(client):
    app.dependency_overrides[get_current_superuser] = lambda: SimpleNamespace(is_superuser=True)
    try:
        first = client.post(BASE, json={"provider": "unsplash", "label": "Conta 1", "api_key": "abcd-1234-unsplash"})
        assert first.status_code == 200, first.text
        body = first.json()
        assert body["monthly_limit"] == 50 and body["status"] == "active" and body["key_masked"].endswith("lash")
        assert client.post(BASE, json={"provider": "pexels", "label": "Pexels", "api_key": "pexels-key-0001", "hourly_limit": 180}).json()["monthly_limit"] == 180
        assert client.post(BASE, json={"provider": "airlabs", "label": "Outra", "api_key": "abcdef"}).status_code == 400
        client.post("/api/v1/admin/master/flight-api-keys", json={"provider": "airlabs", "label": "Voo", "api_key": "airlabs-key-1"})

        listed = client.get(BASE).json()
        assert {item["provider"] for item in listed["items"]} == {"unsplash", "pexels"}
        assert listed["summary"]["unsplash"]["active_keys"] == 1 and listed["summary"]["photos"] == 0
        flights = client.get("/api/v1/admin/master/flight-api-keys").json()
        assert {item["provider"] for item in flights["items"]} == {"airlabs"}
        # Uma rota não mexe na chave da outra.
        assert client.post(f"/api/v1/admin/master/flight-api-keys/{body['id']}/pause").status_code == 404
        flight_id = flights["items"][0]["id"]
        assert client.delete(f"{BASE}/{flight_id}").status_code == 404

        paused = client.post(f"{BASE}/{body['id']}/pause").json()
        assert paused["status"] == "paused" and not paused["is_active"]
        edited = client.patch(f"{BASE}/{body['id']}", json={"hourly_limit": 40, "is_active": True}).json()
        assert edited["monthly_limit"] == 40 and edited["status"] == "active"
        assert client.delete(f"{BASE}/{body['id']}").status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)
