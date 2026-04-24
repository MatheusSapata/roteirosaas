from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.flight_provider_interface import FlightProviderInterface


class AirlabsClientError(Exception):
    """Raised when AirLabs request fails."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AirlabsQuotaExceededError(AirlabsClientError):
    """Raised when AirLabs indicates quota/rate exhaustion."""


@dataclass(slots=True)
class AirlabsResult:
    payload: dict[str, Any]
    selected_flight: dict[str, Any] | None
    lookup_mode: str = "exact"


def split_flight_designator(value: str) -> tuple[str | None, str | None]:
    clean = "".join((value or "").strip().upper().split())
    if not clean:
        return None, None

    # IATA designator usually: AA1234 or G31241 (2 chars + number),
    # where the second airline char can be a digit.
    iata_match = re.match(r"^([A-Z0-9]{2})(\d{1,5}[A-Z]?)$", clean)
    if iata_match:
        return iata_match.group(1), iata_match.group(2)

    # ICAO designator: GLO1241 (3 letters + number).
    icao_match = re.match(r"^([A-Z]{3})(\d{1,5}[A-Z]?)$", clean)
    if icao_match:
        return icao_match.group(1), icao_match.group(2)

    legacy_match = re.match(r"^([A-Z]+)(\d+)$", clean)
    if legacy_match:
        return legacy_match.group(1), legacy_match.group(2)

    return None, None


class AirlabsClient(FlightProviderInterface):
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.airlabs_base_url.rstrip("/")
        self.timeout = max(5, int(settings.airlabs_timeout_seconds or 20))

    def provider_name(self) -> str:
        return "airlabs"

    def supports_future_lookup(self) -> bool:
        return False

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise AirlabsClientError("Falha ao consultar a AirLabs.") from exc

        payload: dict[str, Any]
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text}

        if response.status_code >= 400:
            message = self._extract_error_message(payload) or "Erro ao consultar AirLabs."
            if self._is_quota_error(response.status_code, message):
                raise AirlabsQuotaExceededError(message, status_code=response.status_code, payload=payload)
            raise AirlabsClientError(message, status_code=response.status_code, payload=payload)

        error = payload.get("error")
        if error:
            message = self._extract_error_message(payload) or "Erro ao consultar AirLabs."
            if self._is_quota_error(response.status_code, message):
                raise AirlabsQuotaExceededError(message, status_code=response.status_code, payload=payload)
            raise AirlabsClientError(message, status_code=response.status_code, payload=payload)
        return payload

    @staticmethod
    def _extract_error_message(payload: Any) -> str:
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                return str(error.get("message") or error.get("description") or error.get("code") or "").strip()
            if isinstance(error, str):
                return error.strip()
            message = payload.get("message")
            if isinstance(message, str):
                return message.strip()
        return ""

    @staticmethod
    def _is_quota_error(status_code: int | None, message: str) -> bool:
        if status_code == 429:
            return True
        normalized = (message or "").lower()
        if not normalized:
            return False
        triggers = ("quota", "rate limit", "limit exceeded", "too many requests", "monthly limit")
        return any(term in normalized for term in triggers)

    @staticmethod
    def _is_not_found_error(exc: AirlabsClientError) -> bool:
        if int(exc.status_code or 0) == 404:
            return True
        message = str(exc).strip().lower()
        if "not found" in message or "nao encontrado" in message:
            return True
        payload = exc.payload if isinstance(exc.payload, dict) else {}
        error = payload.get("error")
        if isinstance(error, dict):
            code = str(error.get("code") or "").strip().lower()
            if code in {"not_found", "flight_not_found"}:
                return True
        return False

    @staticmethod
    def _response_to_list(response: Any) -> list[dict[str, Any]]:
        if isinstance(response, list):
            return [item for item in response if isinstance(item, dict)]
        if isinstance(response, dict):
            return [response]
        return []

    @staticmethod
    def _select_best_flight(
        candidates: list[dict[str, Any]],
        *,
        normalized_flight: str,
        flight_numeric: str | None,
    ) -> dict[str, Any] | None:
        if not candidates:
            return None
        numeric = str(flight_numeric or "").upper()
        preferred = next(
            (
                item
                for item in candidates
                if (
                    str(item.get("flight_iata") or "").upper() == normalized_flight
                    or str(item.get("flight_icao") or "").upper() == normalized_flight
                    or (numeric and str(item.get("flight_number") or "").upper() == numeric)
                )
            ),
            None,
        )
        return preferred or candidates[0]

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        raw = str(value).strip()
        if not raw:
            return None
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    @staticmethod
    def _parse_time(value: Any):
        raw = str(value or "").strip()
        if not raw:
            return None
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt).time()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_duration_minutes(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return max(0, int(value))
        text = str(value).strip().lower()
        if not text:
            return None
        if text.isdigit():
            return int(text)
        if ":" in text:
            parts = text.split(":")
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                return int(parts[0]) * 60 + int(parts[1])
            if len(parts) == 3 and all(part.isdigit() for part in parts):
                return int(parts[0]) * 60 + int(parts[1])
        return None

    @classmethod
    def _combine_date_time(cls, base_date: date, raw_time: Any) -> datetime | None:
        parsed_dt = cls._parse_datetime(raw_time)
        if parsed_dt is not None:
            return parsed_dt
        parsed_time = cls._parse_time(raw_time)
        if parsed_time is None:
            return None
        return datetime.combine(base_date, parsed_time)

    @staticmethod
    def _build_lookup_params(
        *,
        api_key: str,
        normalized_flight: str,
        airline_code: str | None,
        flight_numeric: str | None,
        is_icao: bool,
        dep_date: date | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"api_key": api_key}
        if dep_date:
            params["dep_date"] = dep_date.isoformat()
        if is_icao:
            params["flight_icao"] = normalized_flight
        else:
            params["flight_iata"] = normalized_flight
        if airline_code:
            if is_icao:
                params["airline_icao"] = airline_code
            else:
                params["airline_iata"] = airline_code
        if flight_numeric:
            params["flight_number"] = flight_numeric
        return params

    @staticmethod
    def _weekday_matches(route_days: Any, target_date: date) -> bool:
        raw = str(route_days or "").strip().lower()
        if not raw:
            return True
        tokens = [token for token in re.split(r"[^a-z0-9]+", raw) if token]
        if not tokens:
            return True

        weekday_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        target_name = weekday_names[target_date.weekday()]
        target_num_iso = str(target_date.isoweekday())
        target_num_weekday = str(target_date.weekday())
        target_num_sun0 = str((target_date.weekday() + 1) % 7)

        return (
            target_name in tokens
            or target_num_iso in tokens
            or target_num_weekday in tokens
            or target_num_sun0 in tokens
            or any(token.startswith(target_name) for token in tokens)
        )

    @classmethod
    def _route_to_flight_like(
        cls,
        route: dict[str, Any],
        *,
        flight_date: date,
        fallback_flight_number: str,
    ) -> dict[str, Any]:
        dep_dt = cls._combine_date_time(flight_date, route.get("dep_time") or route.get("departure_time"))
        arr_dt = cls._combine_date_time(flight_date, route.get("arr_time") or route.get("arrival_time"))
        duration_minutes = cls._parse_duration_minutes(route.get("duration") or route.get("duration_minutes"))

        if dep_dt and duration_minutes is not None and duration_minutes > 0:
            arr_dt = dep_dt + timedelta(minutes=duration_minutes)
        elif dep_dt and arr_dt and arr_dt < dep_dt:
            arr_dt = arr_dt + timedelta(days=1)

        return {
            "flight_iata": route.get("flight_iata") or fallback_flight_number,
            "flight_icao": route.get("flight_icao"),
            "flight_number": route.get("flight_iata") or fallback_flight_number,
            "airline_iata": route.get("airline_iata"),
            "airline_icao": route.get("airline_icao"),
            "airline_name": route.get("airline_name") or route.get("airline_iata") or route.get("airline_icao"),
            "airline_logo": route.get("airline_logo") or route.get("airline_logo_url"),
            "dep_iata": route.get("dep_iata"),
            "dep_icao": route.get("dep_icao"),
            "arr_iata": route.get("arr_iata"),
            "arr_icao": route.get("arr_icao"),
            "dep_time": dep_dt.isoformat() if dep_dt else None,
            "arr_time": arr_dt.isoformat() if arr_dt else None,
            "duration": duration_minutes,
            "status": "scheduled",
            "lookup_mode": "route_projected",
        }

    @classmethod
    def _flight_to_projected_date(cls, flight: dict[str, Any], *, flight_date: date) -> dict[str, Any] | None:
        dep_source = (
            flight.get("dep_time")
            or flight.get("dep_time_utc")
            or flight.get("dep_scheduled")
            or flight.get("departure_time")
            or flight.get("scheduled_departure")
        )
        arr_source = (
            flight.get("arr_time")
            or flight.get("arr_time_utc")
            or flight.get("arr_scheduled")
            or flight.get("arrival_time")
            or flight.get("scheduled_arrival")
        )
        dep_dt_src = cls._parse_datetime(dep_source)
        arr_dt_src = cls._parse_datetime(arr_source)
        dep_time = dep_dt_src.time() if dep_dt_src else cls._parse_time(dep_source)
        arr_time = arr_dt_src.time() if arr_dt_src else cls._parse_time(arr_source)
        duration = cls._parse_duration_minutes(
            flight.get("duration") or flight.get("duration_minutes") or flight.get("flight_duration")
        )

        if dep_time is None and arr_time is None and duration is None:
            return None

        projected = dict(flight)
        dep_dt: datetime | None = None
        arr_dt: datetime | None = None

        if dep_time is not None:
            dep_dt = datetime.combine(flight_date, dep_time)
            projected["dep_time"] = dep_dt.isoformat()

        if arr_time is not None:
            arr_dt = datetime.combine(flight_date, arr_time)
            if dep_dt is not None and arr_dt < dep_dt:
                arr_dt = arr_dt + timedelta(days=1)
            projected["arr_time"] = arr_dt.isoformat()

        if dep_dt is not None and duration is not None and duration > 0:
            projected["arr_time"] = (dep_dt + timedelta(minutes=duration)).isoformat()
        elif dep_dt is not None and arr_dt is not None:
            computed = max(0, int((arr_dt - dep_dt).total_seconds() // 60))
            projected["duration"] = computed

        projected["status"] = projected.get("status") or "scheduled"
        projected["lookup_mode"] = "closest_projected"
        return projected

    def test_connection(self, api_key: str) -> dict[str, Any]:
        return self._request("/countries", {"api_key": api_key, "_limit": 1})

    def lookup_flight(self, api_key: str, flight_number: str, flight_date: str) -> AirlabsResult:
        normalized = "".join((flight_number or "").upper().split())
        airline_code, flight_numeric = split_flight_designator(normalized)
        is_icao = bool(airline_code and len(airline_code) == 3 and airline_code.isalpha())

        try:
            target_date = date.fromisoformat(flight_date)
        except ValueError as exc:
            raise AirlabsClientError("Data de voo invalida. Use YYYY-MM-DD.", status_code=400) from exc

        search_dates: list[date] = []
        for offset in (0, -1, 1):
            candidate_date = target_date + timedelta(days=offset)
            if candidate_date not in search_dates:
                search_dates.append(candidate_date)

        last_payload: dict[str, Any] = {}
        for dep_date in search_dates:
            params = self._build_lookup_params(
                api_key=api_key,
                normalized_flight=normalized,
                airline_code=airline_code,
                flight_numeric=flight_numeric,
                is_icao=is_icao,
                dep_date=dep_date,
            )
            try:
                payload = self._request("/flights", params)
            except AirlabsQuotaExceededError:
                raise
            except AirlabsClientError as exc:
                if self._is_not_found_error(exc):
                    if isinstance(exc.payload, dict):
                        last_payload = exc.payload
                    continue
                raise

            last_payload = payload
            selected = self._select_best_flight(
                self._response_to_list(payload.get("response")),
                normalized_flight=normalized,
                flight_numeric=flight_numeric,
            )
            if selected:
                dep_dt = self._parse_datetime(
                    selected.get("dep_time")
                    or selected.get("dep_time_utc")
                    or selected.get("dep_scheduled")
                    or selected.get("departure_time")
                )
                mode = "exact"
                if dep_dt and dep_dt.date() != target_date:
                    mode = "adjacent_date"
                selected["lookup_mode"] = mode
                return AirlabsResult(payload=payload, selected_flight=selected, lookup_mode=mode)

        try:
            closest_payload = self._request(
                "/flight",
                self._build_lookup_params(
                    api_key=api_key,
                    normalized_flight=normalized,
                    airline_code=airline_code,
                    flight_numeric=flight_numeric,
                    is_icao=is_icao,
                    dep_date=None,
                ),
            )
            closest = self._select_best_flight(
                self._response_to_list(closest_payload.get("response")),
                normalized_flight=normalized,
                flight_numeric=flight_numeric,
            )
            if closest:
                dep_dt = self._parse_datetime(
                    closest.get("dep_time")
                    or closest.get("dep_time_utc")
                    or closest.get("dep_scheduled")
                    or closest.get("departure_time")
                )
                if dep_dt and dep_dt.date() == target_date:
                    closest["lookup_mode"] = "closest_exact_date"
                    return AirlabsResult(
                        payload=closest_payload,
                        selected_flight=closest,
                        lookup_mode="closest_exact_date",
                    )

                projected_closest = self._flight_to_projected_date(closest, flight_date=target_date)
                if projected_closest:
                    return AirlabsResult(
                        payload=closest_payload,
                        selected_flight=projected_closest,
                        lookup_mode="closest_projected",
                    )

                last_payload = closest_payload
        except AirlabsQuotaExceededError:
            raise
        except AirlabsClientError:
            pass

        try:
            routes_payload = self._request(
                "/routes",
                self._build_lookup_params(
                    api_key=api_key,
                    normalized_flight=normalized,
                    airline_code=airline_code,
                    flight_numeric=flight_numeric,
                    is_icao=is_icao,
                    dep_date=None,
                ),
            )
            route_candidates = self._response_to_list(routes_payload.get("response"))
            route_candidates = [
                item
                for item in route_candidates
                if (
                    str(item.get("flight_iata") or "").upper() == normalized
                    or str(item.get("flight_icao") or "").upper() == normalized
                    or str(item.get("flight_number") or "").upper() == str(flight_numeric or "").upper()
                )
            ]
            if route_candidates:
                weekday_matched = [
                    item for item in route_candidates if self._weekday_matches(item.get("days"), target_date)
                ]
                selected_route = (weekday_matched or route_candidates)[0]
                projected = self._route_to_flight_like(
                    selected_route,
                    flight_date=target_date,
                    fallback_flight_number=normalized,
                )
                return AirlabsResult(payload=routes_payload, selected_flight=projected, lookup_mode="route_projected")
            last_payload = routes_payload
        except AirlabsQuotaExceededError:
            raise
        except AirlabsClientError:
            pass

        raise AirlabsClientError(
            "Voo nao encontrado para os dados informados.",
            status_code=404,
            payload=last_payload or {"flight_iata": normalized, "dep_date": target_date.isoformat()},
        )

    def lookup_flight_by_number(self, api_key: str, flight_number: str, flight_date: date) -> dict[str, Any]:
        result = self.lookup_flight(api_key, flight_number, flight_date.isoformat())
        return {
            "payload": result.payload,
            "selected_flight": result.selected_flight,
            "lookup_mode": result.lookup_mode,
            "marketplace": "direct",
        }
