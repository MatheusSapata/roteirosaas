from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
import threading
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.services.flight_provider_interface import FlightProviderInterface


class AeroDataBoxClientError(Exception):
    """Raised when AeroDataBox request fails."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AeroDataBoxQuotaExceededError(AeroDataBoxClientError):
    """Raised when AeroDataBox indicates quota/rate exhaustion."""


@dataclass(slots=True)
class AeroDataBoxResult:
    payload: Any
    selected_flight: dict[str, Any] | None
    lookup_mode: str = "exact"
    marketplace: str = "rapidapi"


class AeroDataBoxClient(FlightProviderInterface):
    _rate_lock = threading.Lock()
    _last_request_at = 0.0

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.aerodatabox_rapidapi_base_url.rstrip("/")
        self.api_host = settings.aerodatabox_rapidapi_host.strip() or "aerodatabox.p.rapidapi.com"
        self.timeout = max(5, int(settings.aerodatabox_timeout_seconds or 20))

    def provider_name(self) -> str:
        return "aerodatabox"

    def supports_future_lookup(self) -> bool:
        return True

    @staticmethod
    def _normalize_flight_number(value: str) -> str:
        clean = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
        return clean

    @staticmethod
    def _extract_error_message(payload: Any) -> str:
        if isinstance(payload, dict):
            for key in ("message", "error", "detail", "description", "title"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, dict):
                    nested = value.get("message") or value.get("detail") or value.get("description")
                    if isinstance(nested, str) and nested.strip():
                        return nested.strip()
        return ""

    @staticmethod
    def _is_quota_error(status_code: int | None, message: str) -> bool:
        if status_code == 429:
            return True
        normalized = (message or "").lower()
        if not normalized:
            return False
        triggers = ("quota", "rate limit", "too many requests", "limit exceeded", "monthly limit", "units")
        return any(term in normalized for term in triggers)

    @classmethod
    def _wait_rate_slot(cls) -> None:
        with cls._rate_lock:
            now = time.monotonic()
            elapsed = now - cls._last_request_at
            wait_seconds = 1.0 - elapsed
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            cls._last_request_at = time.monotonic()

    @staticmethod
    def _response_to_list(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("items", "response", "data", "flights", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return [payload] if payload.get("number") or payload.get("flightNumber") else []
        return []

    def _request(
        self,
        path: str,
        *,
        api_key: str,
        params: dict[str, Any] | None = None,
        max_attempts: int = 2,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            self._wait_rate_slot()
            try:
                response = httpx.get(url, headers=headers, params=params, timeout=self.timeout)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    raise AeroDataBoxClientError("Falha ao consultar o AeroDataBox via RapidAPI.") from exc
                time.sleep(0.4)
                continue

            try:
                payload = response.json()
            except Exception:
                payload = {"raw": response.text}

            if response.status_code >= 400:
                message = self._extract_error_message(payload) or "Erro ao consultar AeroDataBox."
                if self._is_quota_error(response.status_code, message):
                    if response.status_code == 429 and attempt < max_attempts:
                        time.sleep(1.1)
                        continue
                    raise AeroDataBoxQuotaExceededError(message, status_code=response.status_code, payload=payload)
                raise AeroDataBoxClientError(message, status_code=response.status_code, payload=payload)

            if isinstance(payload, dict) and payload.get("error"):
                message = self._extract_error_message(payload) or "Erro ao consultar AeroDataBox."
                if self._is_quota_error(response.status_code, message):
                    raise AeroDataBoxQuotaExceededError(message, status_code=response.status_code, payload=payload)
                raise AeroDataBoxClientError(message, status_code=response.status_code, payload=payload)
            return payload

        raise AeroDataBoxClientError("Falha ao consultar o AeroDataBox via RapidAPI.") from last_exc

    @staticmethod
    def _match_flight(candidates: list[dict[str, Any]], normalized_flight: str) -> dict[str, Any] | None:
        if not candidates:
            return None
        for item in candidates:
            number = AeroDataBoxClient._normalize_flight_number(
                str(item.get("number") or item.get("flightNumber") or item.get("flight_iata") or "")
            )
            if number and number == normalized_flight:
                return item
        return candidates[0]

    def test_connection(self, api_key: str) -> dict[str, Any]:
        payload = self._request("/airports/iata/LHR", api_key=api_key)
        if isinstance(payload, dict):
            return payload
        return {"ok": True, "payload_type": type(payload).__name__}

    def lookup_flight(self, api_key: str, flight_number: str, flight_date: str) -> AeroDataBoxResult:
        try:
            target_date = date.fromisoformat(flight_date)
        except ValueError as exc:
            raise AeroDataBoxClientError("Data de voo invalida. Use YYYY-MM-DD.", status_code=400) from exc
        return AeroDataBoxResult(**self.lookup_flight_by_number(api_key, flight_number, target_date))

    def lookup_flight_by_number(self, api_key: str, flight_number: str, flight_date: date) -> dict[str, Any]:
        normalized_flight = self._normalize_flight_number(flight_number)
        if len(normalized_flight) < 3:
            raise AeroDataBoxClientError("Numero de voo invalido.", status_code=400)

        path = f"/flights/number/{quote(normalized_flight)}/{flight_date.isoformat()}"
        payload = self._request(
            path,
            api_key=api_key,
            params={"withAircraftImage": "false", "withLocation": "false"},
        )
        candidates = self._response_to_list(payload)
        selected = self._match_flight(candidates, normalized_flight)
        if not selected:
            raise AeroDataBoxClientError(
                "Voo nao encontrado para os dados informados.",
                status_code=404,
                payload=payload,
            )

        return {
            "payload": payload,
            "selected_flight": selected,
            "lookup_mode": "exact",
            "marketplace": "rapidapi",
        }
