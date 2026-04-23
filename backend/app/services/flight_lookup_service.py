from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.flight_lookup_cache import FlightLookupCache
from app.services.airlabs_client import AirlabsClient, AirlabsClientError, AirlabsQuotaExceededError, split_flight_designator
from app.services.flight_provider_key_manager import FlightProviderKeyManager

logger = logging.getLogger(__name__)

LOOKUP_FALLBACK_MESSAGE = (
    "Nao foi possivel consultar os dados automaticos agora. Preencha manualmente ou tente novamente mais tarde."
)
LOOKUP_NOT_FOUND_MESSAGE = "Voo nao encontrado para os dados informados. Confira numero e data ou preencha manualmente."


@dataclass(slots=True)
class LookupResult:
    provider: str
    from_cache: bool
    flight: dict[str, Any]
    raw_response: dict[str, Any] | None = None
    lookup_mode: str = "exact"


def parse_iso_datetime(value: Any) -> datetime | None:
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


def pick(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def parse_duration_minutes(value: Any) -> int | None:
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
            hours, minutes = int(parts[0]), int(parts[1])
            return hours * 60 + minutes
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            hours, minutes = int(parts[0]), int(parts[1])
            return hours * 60 + minutes
    return None


def normalize_flight_number(value: str) -> str:
    return "".join((value or "").upper().split())


class FlightLookupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.key_manager = FlightProviderKeyManager(db)
        self.airlabs_client = AirlabsClient()

    def lookup(self, flight_number: str, flight_date: str, provider: str = "airlabs") -> LookupResult:
        if provider != "airlabs":
            raise HTTPException(status_code=400, detail="Provider nao suportado.")
        normalized_flight = normalize_flight_number(flight_number)
        if len(normalized_flight) < 3:
            raise HTTPException(status_code=400, detail="Numero de voo invalido.")
        try:
            flight_date_obj = date.fromisoformat(flight_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Data de voo invalida. Use YYYY-MM-DD.") from exc

        _, flight_numeric = split_flight_designator(normalized_flight)

        cached = self._find_valid_cache(provider, normalized_flight, flight_numeric, flight_date_obj)
        if cached:
            logger.info("flight_lookup cache_hit provider=%s flight=%s date=%s", provider, normalized_flight, flight_date_obj.isoformat())
            payload = cached.normalized_json or {}
            return LookupResult(
                provider=provider,
                from_cache=True,
                flight=payload,
                raw_response=cached.response_json or {},
                lookup_mode=str((payload or {}).get("lookup_mode") or "cached"),
            )

        keys = self.key_manager.list_available_keys(provider)
        if not keys:
            raise HTTPException(status_code=503, detail=LOOKUP_FALLBACK_MESSAGE)

        failures: list[str] = []
        for provider_key in keys:
            try:
                result = self.airlabs_client.lookup_flight(provider_key.plain_key, normalized_flight, flight_date_obj.isoformat())
                normalized = self._normalize_airlabs_flight(result.selected_flight or {}, normalized_flight)
                self.key_manager.mark_key_success(provider_key.record)
                self._save_cache(
                    provider=provider,
                    flight_iata=normalized.get("flight_iata") or normalized_flight,
                    flight_number=normalized.get("flight_number") or flight_numeric or normalized_flight,
                    flight_date=flight_date_obj,
                    response_json=result.payload,
                    normalized_json=normalized,
                )
                logger.info(
                    "flight_lookup external_success provider=%s key_id=%s flight=%s date=%s",
                    provider,
                    provider_key.record.id,
                    normalized_flight,
                    flight_date_obj.isoformat(),
                )
                return LookupResult(
                    provider=provider,
                    from_cache=False,
                    flight=normalized,
                    raw_response=result.payload,
                    lookup_mode=str(result.lookup_mode or normalized.get("lookup_mode") or "exact"),
                )
            except AirlabsQuotaExceededError as exc:
                message = str(exc) or "Quota da chave excedida."
                self.key_manager.mark_key_error(provider_key.record, message, quota_exceeded=True)
                failures.append(message)
                logger.warning(
                    "flight_lookup quota_exhausted provider=%s key_id=%s detail=%s",
                    provider,
                    provider_key.record.id,
                    message,
                )
                continue
            except AirlabsClientError as exc:
                message = str(exc) or "Erro ao consultar provider."
                status_code = int(getattr(exc, "status_code", 0) or 0)
                if status_code in {400, 404}:
                    # Request consumed provider quota, but this is not a key-health failure.
                    # Keep key active and return a direct user-facing response.
                    self.key_manager.mark_key_success(provider_key.record)
                    logger.info(
                        "flight_lookup provider_no_result provider=%s key_id=%s status=%s detail=%s",
                        provider,
                        provider_key.record.id,
                        status_code,
                        message,
                    )
                    detail = LOOKUP_NOT_FOUND_MESSAGE if status_code == 404 else message
                    raise HTTPException(status_code=status_code, detail=detail) from exc

                self.key_manager.mark_key_error(provider_key.record, message, quota_exceeded=False)
                failures.append(message)
                logger.warning(
                    "flight_lookup provider_error provider=%s key_id=%s detail=%s",
                    provider,
                    provider_key.record.id,
                    message,
                )
                continue

        logger.error(
            "flight_lookup failed provider=%s flight=%s date=%s failures=%s",
            provider,
            normalized_flight,
            flight_date_obj.isoformat(),
            " | ".join(failures),
        )
        raise HTTPException(status_code=503, detail=LOOKUP_FALLBACK_MESSAGE)

    def _find_valid_cache(
        self,
        provider: str,
        flight_iata: str,
        flight_number: str | None,
        flight_date: date,
    ) -> FlightLookupCache | None:
        now = datetime.now(timezone.utc)
        query = (
            self.db.query(FlightLookupCache)
            .filter(
                FlightLookupCache.provider == provider,
                FlightLookupCache.flight_date == flight_date,
                FlightLookupCache.expires_at > now,
                FlightLookupCache.flight_iata == flight_iata,
            )
            .order_by(FlightLookupCache.updated_at.desc())
        )
        cached = query.first()
        if cached:
            return cached
        if flight_number:
            return (
                self.db.query(FlightLookupCache)
                .filter(
                    FlightLookupCache.provider == provider,
                    FlightLookupCache.flight_date == flight_date,
                    FlightLookupCache.expires_at > now,
                    FlightLookupCache.flight_number == flight_number,
                )
                .order_by(FlightLookupCache.updated_at.desc())
                .first()
            )
        return None

    def _save_cache(
        self,
        *,
        provider: str,
        flight_iata: str | None,
        flight_number: str | None,
        flight_date: date,
        response_json: dict[str, Any],
        normalized_json: dict[str, Any],
    ) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=max(5, int(self.settings.flight_lookup_cache_ttl_minutes or 720)))
        cached = (
            self.db.query(FlightLookupCache)
            .filter(
                FlightLookupCache.provider == provider,
                FlightLookupCache.flight_date == flight_date,
                FlightLookupCache.flight_iata == (flight_iata or None),
                FlightLookupCache.flight_number == (flight_number or None),
            )
            .first()
        )
        if not cached:
            cached = FlightLookupCache(
                provider=provider,
                flight_iata=flight_iata or None,
                flight_number=flight_number or None,
                flight_date=flight_date,
            )
        cached.response_json = response_json
        cached.normalized_json = normalized_json
        cached.expires_at = expires_at
        self.db.add(cached)
        self.db.commit()

    def _normalize_airlabs_flight(self, source: dict[str, Any], fallback_flight_number: str) -> dict[str, Any]:
        departure_datetime = parse_iso_datetime(
            pick(
                source,
                "dep_time",
                "dep_time_utc",
                "dep_actual",
                "dep_scheduled",
                "departure_time",
                "scheduled_departure",
            )
        )
        arrival_datetime = parse_iso_datetime(
            pick(
                source,
                "arr_time",
                "arr_time_utc",
                "arr_actual",
                "arr_scheduled",
                "arrival_time",
                "scheduled_arrival",
            )
        )
        duration_minutes = parse_duration_minutes(
            pick(source, "duration", "duration_minutes", "flight_duration")
        )
        if duration_minutes is None and departure_datetime and arrival_datetime:
            delta = arrival_datetime - departure_datetime
            duration_minutes = max(0, int(delta.total_seconds() // 60))

        flight_number = str(
            pick(source, "flight_iata", "flight_number", "flight_icao") or fallback_flight_number
        ).upper()

        normalized = {
            "flight_number": flight_number,
            "flight_iata": str(pick(source, "flight_iata", "flight_number") or flight_number).upper(),
            "flight_icao": str(pick(source, "flight_icao") or "").upper() or None,
            "airline_name": pick(source, "airline_name", "airline"),
            "airline_iata": str(pick(source, "airline_iata") or "").upper() or None,
            "airline_icao": str(pick(source, "airline_icao") or "").upper() or None,
            "airline_logo_url": pick(source, "airline_logo", "airline_logo_url", "logo", "airline_logo_path"),
            "departure": {
                "iata": str(pick(source, "dep_iata", "departure_iata", "from_iata") or "").upper() or None,
                "airport": pick(source, "dep_name", "dep_airport", "dep_airport_name", "departure_airport_name"),
                "city": pick(source, "dep_city", "departure_city", "from_city"),
                "country": pick(source, "dep_country", "departure_country", "from_country"),
                "terminal": pick(source, "dep_terminal", "departure_terminal"),
                "gate": pick(source, "dep_gate", "departure_gate"),
                "datetime": departure_datetime.isoformat() if departure_datetime else None,
            },
            "arrival": {
                "iata": str(pick(source, "arr_iata", "arrival_iata", "to_iata") or "").upper() or None,
                "airport": pick(source, "arr_name", "arr_airport", "arr_airport_name", "arrival_airport_name"),
                "city": pick(source, "arr_city", "arrival_city", "to_city"),
                "country": pick(source, "arr_country", "arrival_country", "to_country"),
                "terminal": pick(source, "arr_terminal", "arrival_terminal"),
                "gate": pick(source, "arr_gate", "arrival_gate"),
                "datetime": arrival_datetime.isoformat() if arrival_datetime else None,
            },
            "duration_minutes": duration_minutes,
            "status": pick(source, "status", "flight_status"),
            "lookup_mode": pick(source, "lookup_mode"),
        }
        return normalized
