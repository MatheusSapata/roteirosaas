from __future__ import annotations

import httpx
import pytest

from app.services.viajeon import ViajeonAPIError, ViajeonClient


def _response(status_code: int, payload: dict) -> httpx.Response:
    return httpx.Response(status_code, json=payload, request=httpx.Request("GET", "https://app.viajeon.com"))


def test_list_checkouts_uses_server_credentials_and_omits_operation_images(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_request(method: str, url: str, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return _response(
            200,
            {
                "ok": True,
                "checkouts": [
                    {
                        "checkout_id": "checkout-1",
                        "slug": "caldas",
                        "name": "Caldas Novas",
                        "image_url": "https://cdn.example/operation.webp",
                        "mobile_image_url": "https://cdn.example/operation-mobile.webp",
                        "excursion": {
                            "id": "excursion-1",
                            "destination": "Caldas Novas - GO",
                            "departure_date": "2026-07-18",
                            "return_date": "2026-07-22",
                            "image_url": "https://cdn.example/hidden.webp",
                        },
                        "packages": [
                            {
                                "id": "package-1",
                                "name": "Adulto",
                                "price": 1890,
                                "min_quantity": 0,
                                "max_quantity": 10,
                                "active": True,
                            }
                        ],
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    rows = ViajeonClient("rvo_token", "rvs_secret").list_checkouts()

    assert captured["method"] == "GET"
    assert captured["url"] == "https://app.viajeon.com/api/public/roteiro-online/checkouts"
    assert captured["headers"]["X-Api-Token"] == "rvo_token"
    assert captured["headers"]["X-Api-Secret"] == "rvs_secret"
    assert captured["timeout"] == 10.0
    assert "image_url" not in rows[0]
    assert "mobile_image_url" not in rows[0]
    assert "image_url" not in rows[0]["excursion"]


def test_create_session_forwards_selection_and_accepts_only_viajeon_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_request(method: str, url: str, **kwargs):
        captured.update(method=method, url=url, **kwargs)
        return _response(200, {"ok": True, "url": "https://app.viajeon.com/checkout/caldas?prefill=test"})

    monkeypatch.setattr(httpx, "request", fake_request)
    payload = {"checkout_id": "checkout-1", "items": [{"package_id": "package-1", "quantity": 2}]}
    url = ViajeonClient("rvo_token", "rvs_secret").create_session(payload)

    assert captured["method"] == "POST"
    assert captured["url"] == "https://app.viajeon.com/api/public/roteiro-online/sessions"
    assert captured["json"] == payload
    assert url == "https://app.viajeon.com/checkout/caldas?prefill=test"


def test_list_checkouts_normalizes_nested_viajeon_package_types(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(*args, **kwargs):
        return _response(
            200,
            {
                "ok": True,
                "checkouts": [
                    {
                        "checkout_id": "checkout-1",
                        "name": "Pindamonhangaba",
                        "excursion": {
                            "id": "excursion-1",
                            "package_types": [
                                {
                                    "id": "plus",
                                    "name": "Pacote Plus",
                                    "unit_price": 400,
                                    "min_quantity": 0,
                                    "max_quantity": 5,
                                    "is_active": True,
                                },
                                {
                                    "id": "disabled",
                                    "name": "Pacote desativado",
                                    "unit_price": 100,
                                    "is_active": False,
                                },
                            ],
                        },
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    rows = ViajeonClient("rvo_token", "rvs_secret").list_checkouts()

    assert rows[0]["packages"] == [
        {
            "id": "plus",
            "name": "Pacote Plus",
            "description": None,
            "price": 400.0,
            "min_quantity": 0,
            "max_quantity": 5,
            "active": True,
        }
    ]


def test_create_session_rejects_redirect_to_untrusted_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        httpx,
        "request",
        lambda *args, **kwargs: _response(200, {"ok": True, "url": "https://app.viajeon.com.evil.example/checkout"}),
    )

    with pytest.raises(ViajeonAPIError, match="invalid-viajeon-session-url"):
        ViajeonClient("rvo_token", "rvs_secret").create_session(
            {"checkout_id": "checkout-1", "items": [{"package_id": "package-1", "quantity": 1}]}
        )
