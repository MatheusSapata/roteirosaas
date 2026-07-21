from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class AsaasAPIError(Exception):
    """Raised when Asaas returns an error response."""


TEMP_DISABLE_ASAAS_SPLIT = False


ASAAS_DEFAULT_SPLIT_RULES: tuple[tuple[str, float], ...] = (
    ("4f1340fa-d365-41fd-9c26-3a9299034bc2", 34),
    ("30a351e8-4def-4a03-b4fb-78ba9d5df425", 66),
)


def build_default_split_payload() -> list[dict[str, Any]]:
    if TEMP_DISABLE_ASAAS_SPLIT:
        return []
    settings = get_settings()
    wallet_matheus = (settings.wallet_matheus or "").strip()
    if wallet_matheus:
        rules = ((wallet_matheus, 34.0),)
    else:
        rules = ASAAS_DEFAULT_SPLIT_RULES
    return [
        {
            "walletId": wallet_id,
            "percentualValue": float(percentual),
        }
        for wallet_id, percentual in rules
    ]


class AsaasClient:
    def __init__(self, api_key: str, base_url: str = "https://api-sandbox.asaas.com/v3") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": self.api_key,
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        response = httpx.request(method, url, headers=self._headers, timeout=30, **kwargs)
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"errors": response.text}
            raise AsaasAPIError(data)
        if not response.content:
            return None
        return response.json()

    def create_payment_link(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/paymentLinks", json=payload)

    def create_customer(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/customers", json=payload)

    def list_customers(self, **params: Any) -> dict[str, Any]:
        return self._request("GET", "/customers", params=params)

    def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/payments", json=payload)

    def list_payments(self, **params: Any) -> dict[str, Any]:
        return self._request("GET", "/payments", params=params)

    def create_subscription(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/subscriptions", json=payload)

    def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        return self._request("GET", f"/subscriptions/{subscription_id}")

    def update_subscription(self, subscription_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not subscription_id:
            raise ValueError("Subscription id is required")
        return self._request("PUT", f"/subscriptions/{subscription_id}", json=payload)

    def list_subscription_payments(self, subscription_id: str, **params: Any) -> dict[str, Any]:
        return self._request("GET", f"/subscriptions/{subscription_id}/payments", params=params)

    def create_pix_automatic_authorization(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/pix/automatic/authorizations", json=payload)

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{payment_id}")

    def get_payment_status(self, payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{payment_id}/status")

    def get_pix_qr_code(self, payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{payment_id}/pixQrCode")

    def delete_payment_link(self, link_id: str) -> None:
        if not link_id:
            return
        self._request("DELETE", f"/paymentLinks/{link_id}")

    def cancel_subscription(self, subscription_id: str) -> None:
        if not subscription_id:
            return
        self._request("DELETE", f"/subscriptions/{subscription_id}")

    def update_subscription_card(self, subscription_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not subscription_id:
            raise ValueError("Subscription id is required to update card")
        return self._request("PUT", f"/subscriptions/{subscription_id}/creditCard", json=payload)
