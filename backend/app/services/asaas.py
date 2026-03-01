from __future__ import annotations

from typing import Any

import httpx


class AsaasAPIError(Exception):
    """Raised when Asaas returns an error response."""


class AsaasClient:
    def __init__(self, api_key: str, base_url: str = "https://sandbox.asaas.com/api/v3") -> None:
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

    def delete_payment_link(self, link_id: str) -> None:
        if not link_id:
            return
        self._request("DELETE", f"/paymentLinks/{link_id}")

    def cancel_subscription(self, subscription_id: str) -> None:
        if not subscription_id:
            return
        self._request("DELETE", f"/subscriptions/{subscription_id}")

