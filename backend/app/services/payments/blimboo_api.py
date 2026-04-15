from __future__ import annotations

from typing import Any

import httpx


class BlimbooAPIError(Exception):
    """Raised whenever the Blimboo API returns an error payload."""


class BlimbooAPIClient:
    """Small HTTP client tailored for the Blimboo API."""

    def __init__(self, base_url: str, api_token: str) -> None:
        if not base_url:
            raise ValueError("Blimboo base URL must be configured.")
        if not api_token:
            raise ValueError("Blimboo API token must be configured.")
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self._headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_token}",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        try:
            response = httpx.request(method, url, headers=self._headers, timeout=30, **kwargs)
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            raise BlimbooAPIError(str(exc)) from exc
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:  # pragma: no cover - best effort
                data = {"error": response.text}
            raise BlimbooAPIError(data)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def ping(self) -> Any:
        """Utility helper to validate connectivity with the API."""
        return self._request("GET", "/")

    def quote_payment(self, payload: dict[str, Any]) -> Any:
        """Requests a financial quote for an upcoming charge."""
        return self._request("POST", "/charges/quote", json=payload)

    def create_charge(self, payload: dict[str, Any]) -> Any:
        """Creates a charge on Blimboo using the provided payload."""
        return self._request("POST", "/charges", json=payload)

    def get_pricing(self, payload: dict[str, Any]) -> Any:
        """Fetches the pricing table for the informed payment scenario."""
        return self._request("POST", "/pricing", json=payload)

    def get_charge(self, charge_id: str) -> Any:
        """Fetch a charge information by its id/reference."""
        return self._request("GET", f"/charges/{charge_id}")

    def update_charge_status(self, charge_id: str, status: str) -> Any:
        """Requests a status change for an existing charge."""
        payload = {"status": status}
        return self._request("POST", f"/charges/{charge_id}/status", json=payload)

    def refund_charge(self, charge_id: str, payload: dict[str, Any] | None = None) -> Any:
        """Starts a refund process for a charge."""
        return self._request("POST", f"/charges/{charge_id}/refunds", json=payload or {})
