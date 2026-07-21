from __future__ import annotations

from copy import deepcopy
from threading import Lock
from time import monotonic
from typing import Any
from urllib.parse import urlparse

import httpx


VIAJEON_BASE_URL = "https://app.viajeon.com"
VIAJEON_API_PREFIX = "/api/public/roteiro-online"
VIAJEON_PUBLIC_DATA_URL = "https://kdwlrpvwsejcfdnbshyf.supabase.co/rest/v1"
# Public anonymous key shipped by Viajeon's own checkout frontend. It only reads
# rows exposed by Viajeon's RLS policies and is used when their integration list
# omits the package types for an otherwise valid checkout.
VIAJEON_PUBLIC_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtkd2xycHZ3c2VqY2ZkbmJzaHlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2NjA1NDAsImV4cCI6MjA5OTIzNjU0MH0."
    "lQu9cCBMDQF_f8L04AZWuBxemMsgrJLXsbXZkHYl1FY"
)


class ViajeonAPIError(Exception):
    def __init__(self, status_code: int, error: str, payload: Any = None) -> None:
        super().__init__(error)
        self.status_code = status_code
        self.error = error
        self.payload = payload


class ViajeonClient:
    def __init__(self, token: str, secret: str, *, timeout_seconds: float = 10.0) -> None:
        self.base_url = VIAJEON_BASE_URL
        self.timeout_seconds = timeout_seconds
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Token": token,
            "X-Api-Secret": secret,
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{VIAJEON_API_PREFIX}{path}",
                headers=self.headers,
                timeout=self.timeout_seconds,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise ViajeonAPIError(502, "viajeon-unavailable") from exc
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {}
        if response.status_code >= 400:
            error = str(payload.get("error") or "viajeon-error") if isinstance(payload, dict) else "viajeon-error"
            raise ViajeonAPIError(response.status_code, error, payload)
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            raise ViajeonAPIError(502, "invalid-viajeon-response", payload)
        return payload

    def list_checkouts(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/checkouts")
        rows = payload.get("checkouts")
        if not isinstance(rows, list):
            raise ViajeonAPIError(502, "invalid-viajeon-response", payload)
        normalized = [_normalize_checkout(row) for row in rows if isinstance(row, dict)]
        for checkout in normalized:
            excursion = checkout.get("excursion") or {}
            if checkout["packages"] or not excursion.get("id"):
                continue
            checkout["packages"] = self._list_public_package_types(excursion["id"])
        return normalized

    def _list_public_package_types(self, excursion_id: str) -> list[dict[str, Any]]:
        try:
            response = httpx.get(
                f"{VIAJEON_PUBLIC_DATA_URL}/excursion_package_types",
                headers={
                    "Accept": "application/json",
                    "apikey": VIAJEON_PUBLIC_ANON_KEY,
                    "Authorization": f"Bearer {VIAJEON_PUBLIC_ANON_KEY}",
                },
                params={
                    "select": "id,name,description,price,min_quantity,max_quantity,sort_order,is_active,available_in_checkout",
                    "excursion_id": f"eq.{excursion_id}",
                    "is_active": "eq.true",
                    "available_in_checkout": "eq.true",
                    "order": "sort_order.asc",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            rows = response.json()
        except (httpx.HTTPError, ValueError):
            return []
        if not isinstance(rows, list):
            return []
        return _normalize_packages(rows)

    def get_public_checkout_by_url(self, checkout_url: str) -> dict[str, Any]:
        parsed = urlparse(checkout_url.strip())
        if parsed.scheme != "https" or parsed.hostname != "app.viajeon.com":
            raise ViajeonAPIError(400, "invalid-checkout-url")
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) != 2 or path_parts[0] != "checkout" or not path_parts[1]:
            raise ViajeonAPIError(400, "invalid-checkout-url")
        slug = path_parts[1]
        try:
            response = httpx.get(
                f"{VIAJEON_PUBLIC_DATA_URL}/checkout_pages",
                headers={
                    "Accept": "application/json",
                    "apikey": VIAJEON_PUBLIC_ANON_KEY,
                    "Authorization": f"Bearer {VIAJEON_PUBLIC_ANON_KEY}",
                },
                params={
                    "select": "id,slug,title,subtitle,excursion_id,is_active",
                    "slug": f"eq.{slug}",
                    "is_active": "eq.true",
                    "limit": "1",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            rows = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ViajeonAPIError(502, "viajeon-unavailable") from exc
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise ViajeonAPIError(404, "checkout-not-found")
        row = rows[0]
        excursion_id = str(row.get("excursion_id") or "")
        packages = self._list_public_package_types(excursion_id)
        if not packages:
            raise ViajeonAPIError(404, "checkout-packages-not-found")
        return {
            "checkout_id": str(row.get("id") or ""),
            "slug": str(row.get("slug") or slug),
            "name": str(row.get("title") or "Checkout Viajeon"),
            "subtitle": row.get("subtitle"),
            "description": None,
            "checkout_url": f"https://app.viajeon.com/checkout/{slug}",
            "excursion": {"id": excursion_id},
            "packages": packages,
        }

    def create_session(self, payload: dict[str, Any]) -> str:
        response = self._request("POST", "/sessions", json=payload)
        url = str(response.get("url") or "").strip()
        if not url.startswith("https://app.viajeon.com/"):
            raise ViajeonAPIError(502, "invalid-viajeon-session-url", response)
        return url


def _normalize_checkout(raw: dict[str, Any]) -> dict[str, Any]:
    raw_excursion = raw.get("excursion") if isinstance(raw.get("excursion"), dict) else None
    package_rows: list[Any] = []
    for candidate in (
        raw.get("packages"),
        raw.get("products"),
        raw.get("package_types"),
        raw.get("excursion_package_types"),
        raw_excursion.get("packages") if raw_excursion else None,
        raw_excursion.get("products") if raw_excursion else None,
        raw_excursion.get("package_types") if raw_excursion else None,
        raw_excursion.get("excursion_package_types") if raw_excursion else None,
    ):
        if isinstance(candidate, list):
            package_rows = candidate
            if candidate:
                break

    packages = _normalize_packages(package_rows)
    excursion = None
    if raw_excursion:
        excursion = {
            "id": str(raw_excursion.get("id") or ""),
            "destination": raw_excursion.get("destination"),
            "departure_date": raw_excursion.get("departure_date"),
            "return_date": raw_excursion.get("return_date"),
        }
    return {
        "checkout_id": str(raw.get("checkout_id") or ""),
        "slug": str(raw.get("slug") or ""),
        "name": str(raw.get("name") or ""),
        "subtitle": raw.get("subtitle"),
        "description": raw.get("description"),
        # Deliberately omit operation image fields: this section is text/packages only.
        "checkout_url": str(raw.get("checkout_url") or ""),
        "excursion": deepcopy(excursion),
        "packages": packages,
    }


def _normalize_packages(package_rows: list[Any]) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for package in package_rows:
        if not isinstance(package, dict):
            continue
        if package.get("active") is False or package.get("is_active") is False:
            continue
        package_id = package.get("id") or package.get("package_id") or package.get("package_type_id")
        package_name = package.get("name") or package.get("title")
        if not package_id or not package_name:
            continue
        packages.append(
            {
                "id": str(package_id),
                "name": str(package_name),
                "description": package.get("description"),
                "price": float(package.get("price") or package.get("unit_price") or package.get("sale_price") or 0),
                "min_quantity": max(0, int(package.get("min_quantity") or 0)),
                "max_quantity": max(1, int(package.get("max_quantity") or 99)),
                "active": True,
            }
        )
    return packages


_checkout_cache: dict[int, tuple[float, list[dict[str, Any]]]] = {}
_cache_lock = Lock()


def clear_viajeon_checkout_cache(integration_id: int) -> None:
    with _cache_lock:
        _checkout_cache.pop(integration_id, None)


def get_cached_viajeon_checkouts(
    integration_id: int,
    token: str,
    secret: str,
    *,
    force_refresh: bool = False,
    ttl_seconds: int = 90,
) -> list[dict[str, Any]]:
    now = monotonic()
    with _cache_lock:
        cached = _checkout_cache.get(integration_id)
        if not force_refresh and cached and cached[0] > now:
            return deepcopy(cached[1])
    rows = ViajeonClient(token, secret).list_checkouts()
    with _cache_lock:
        if not rows and cached and cached[1]:
            _checkout_cache[integration_id] = (now + ttl_seconds, deepcopy(cached[1]))
            return deepcopy(cached[1])
        _checkout_cache[integration_id] = (now + ttl_seconds, deepcopy(rows))
    return rows
