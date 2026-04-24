from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.flight_lookup_cache import FlightLookupCache
from app.services.aerodatabox_client import (
    AeroDataBoxClient,
    AeroDataBoxClientError,
    AeroDataBoxQuotaExceededError,
)
from app.services.airlabs_client import AirlabsClient, AirlabsClientError, AirlabsQuotaExceededError, split_flight_designator
from app.services.flight_provider_interface import FlightProviderInterface
from app.services.flight_provider_key_manager import FlightProviderKeyManager, ProviderKey

logger = logging.getLogger(__name__)

PRIMARY_PROVIDER = "aerodatabox"
FALLBACK_PROVIDER = "airlabs"
SUPPORTED_PROVIDERS = {PRIMARY_PROVIDER, FALLBACK_PROVIDER}
LOOKUP_FALLBACK_MESSAGE = "Nao encontramos dados automaticos para este voo. Voce pode preencher manualmente."
LOOKUP_NOT_FOUND_MESSAGE = "Voo nao encontrado para os dados informados. Confira numero e data ou preencha manualmente."


@dataclass(slots=True)
class LookupResult:
    provider: str
    marketplace: str | None
    from_cache: bool
    fallback_used: bool
    flight: dict[str, Any]
    raw_response: Any = None
    lookup_mode: str = "exact"
    success: bool = True


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


def pick_nested(source: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = source
        valid = True
        for chunk in path.split("."):
            if not isinstance(current, dict):
                valid = False
                break
            current = current.get(chunk)
        if not valid:
            continue
        if current is None:
            continue
        if isinstance(current, str) and not current.strip():
            continue
        return current
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
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


class FlightLookupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.key_manager = FlightProviderKeyManager(db)
        self.providers: dict[str, FlightProviderInterface] = {
            PRIMARY_PROVIDER: AeroDataBoxClient(),
            FALLBACK_PROVIDER: AirlabsClient(),
        }

    def lookup(
        self,
        flight_number: str,
        flight_date: str,
        provider: str | None = None,
        *,
        preferred_provider: str | None = None,
        force_refresh: bool = False,
    ) -> LookupResult:
        normalized_flight = normalize_flight_number(flight_number)
        if len(normalized_flight) < 3:
            raise HTTPException(status_code=400, detail="Numero de voo invalido.")
        try:
            flight_date_obj = date.fromisoformat(flight_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Data de voo invalida. Use YYYY-MM-DD.") from exc

        requested_provider = (preferred_provider or provider or "").strip().lower() or None
        provider_order = self._resolve_provider_order(requested_provider, flight_date_obj)
        primary_provider = provider_order[0]

        _, flight_numeric = split_flight_designator(normalized_flight)
        provider_failures: list[str] = []
        saw_not_found = False

        for current_provider in provider_order:
            if not force_refresh:
                cached = self._find_valid_cache(current_provider, normalized_flight, flight_numeric, flight_date_obj)
                if cached:
                    payload = cached.normalized_json or {}
                    lookup_mode = str((payload or {}).get("lookup_mode") or "cached")
                    marketplace = str((payload or {}).get("marketplace") or self._default_marketplace(current_provider))
                    logger.info(
                        "flight_lookup provider=%s marketplace=%s from_cache=true fallback_used=%s flight=%s date=%s",
                        current_provider,
                        marketplace,
                        current_provider != primary_provider,
                        normalized_flight,
                        flight_date_obj.isoformat(),
                    )
                    return LookupResult(
                        provider=current_provider,
                        marketplace=marketplace,
                        from_cache=True,
                        fallback_used=current_provider != primary_provider,
                        flight=payload,
                        raw_response=cached.response_json or {},
                        lookup_mode=lookup_mode,
                    )

            keys = self.key_manager.list_available_keys(current_provider)
            if not keys:
                provider_failures.append(f"{current_provider}: no_active_key")
                continue

            for provider_key in keys:
                try:
                    provider_result = self._provider_lookup(
                        current_provider,
                        provider_key,
                        normalized_flight,
                        flight_date_obj,
                    )
                    normalized = self._normalize_provider_flight(
                        provider=current_provider,
                        source=provider_result.get("selected_flight") or {},
                        fallback_flight_number=normalized_flight,
                        flight_date=flight_date_obj,
                        raw_response=provider_result.get("payload"),
                        marketplace=provider_result.get("marketplace") or provider_key.marketplace,
                    )
                    self.key_manager.mark_key_success(provider_key.record)
                    self._save_cache(
                        provider=current_provider,
                        flight_iata=normalized.get("flight_iata") or normalized_flight,
                        flight_number=normalized.get("flight_number") or flight_numeric or normalized_flight,
                        flight_date=flight_date_obj,
                        response_json=provider_result.get("payload") or {},
                        normalized_json=normalized,
                    )
                    logger.info(
                        "flight_lookup provider=%s marketplace=%s from_cache=false fallback_used=%s status_code=%s flight=%s date=%s",
                        current_provider,
                        normalized.get("marketplace") or provider_key.marketplace or self._default_marketplace(current_provider),
                        current_provider != primary_provider,
                        200,
                        normalized_flight,
                        flight_date_obj.isoformat(),
                    )
                    return LookupResult(
                        provider=current_provider,
                        marketplace=str(normalized.get("marketplace") or provider_key.marketplace or self._default_marketplace(current_provider)),
                        from_cache=False,
                        fallback_used=current_provider != primary_provider,
                        flight=normalized,
                        raw_response=provider_result.get("payload") or {},
                        lookup_mode=str(provider_result.get("lookup_mode") or normalized.get("lookup_mode") or "exact"),
                    )
                except (AeroDataBoxQuotaExceededError, AirlabsQuotaExceededError) as exc:
                    message = str(exc) or "Quota da chave excedida."
                    self.key_manager.mark_key_error(provider_key.record, message, quota_exceeded=True)
                    provider_failures.append(f"{current_provider}:{message}")
                    logger.warning(
                        "flight_lookup provider=%s marketplace=%s from_cache=false fallback_used=%s status_code=%s error=%s flight=%s date=%s",
                        current_provider,
                        provider_key.marketplace or self._default_marketplace(current_provider),
                        current_provider != primary_provider,
                        int(getattr(exc, "status_code", 429) or 429),
                        message,
                        normalized_flight,
                        flight_date_obj.isoformat(),
                    )
                    continue
                except (AeroDataBoxClientError, AirlabsClientError) as exc:
                    message = str(exc) or "Erro ao consultar provider."
                    status_code = int(getattr(exc, "status_code", 0) or 0)
                    if status_code in {400, 404}:
                        self.key_manager.mark_key_success(provider_key.record)
                        provider_failures.append(f"{current_provider}:{status_code}:{message}")
                        saw_not_found = saw_not_found or status_code == 404
                        logger.info(
                            "flight_lookup provider=%s marketplace=%s from_cache=false fallback_used=%s status_code=%s error=%s flight=%s date=%s",
                            current_provider,
                            provider_key.marketplace or self._default_marketplace(current_provider),
                            current_provider != primary_provider,
                            status_code,
                            message,
                            normalized_flight,
                            flight_date_obj.isoformat(),
                        )
                        break

                    self.key_manager.mark_key_error(provider_key.record, message, quota_exceeded=False)
                    provider_failures.append(f"{current_provider}:{status_code}:{message}")
                    logger.warning(
                        "flight_lookup provider=%s marketplace=%s from_cache=false fallback_used=%s status_code=%s error=%s flight=%s date=%s",
                        current_provider,
                        provider_key.marketplace or self._default_marketplace(current_provider),
                        current_provider != primary_provider,
                        status_code or 500,
                        message,
                        normalized_flight,
                        flight_date_obj.isoformat(),
                    )
                    continue

        logger.error(
            "flight_lookup failed provider_order=%s flight=%s date=%s failures=%s",
            ",".join(provider_order),
            normalized_flight,
            flight_date_obj.isoformat(),
            " | ".join(provider_failures),
        )
        if saw_not_found:
            raise HTTPException(status_code=404, detail=LOOKUP_NOT_FOUND_MESSAGE)
        raise HTTPException(status_code=503, detail=LOOKUP_FALLBACK_MESSAGE)

    def _resolve_provider_order(self, requested_provider: str | None, flight_date_obj: date) -> list[str]:
        if requested_provider:
            if requested_provider not in SUPPORTED_PROVIDERS:
                raise HTTPException(status_code=400, detail="Provider nao suportado.")
            if requested_provider == PRIMARY_PROVIDER:
                return [PRIMARY_PROVIDER, FALLBACK_PROVIDER]
            return [requested_provider, PRIMARY_PROVIDER] if requested_provider != PRIMARY_PROVIDER else [PRIMARY_PROVIDER]
        if flight_date_obj >= date.today():
            return [PRIMARY_PROVIDER, FALLBACK_PROVIDER]
        return [PRIMARY_PROVIDER, FALLBACK_PROVIDER]

    def _provider_lookup(
        self,
        provider: str,
        provider_key: ProviderKey,
        flight_number: str,
        flight_date_obj: date,
    ) -> dict[str, Any]:
        client = self.providers.get(provider)
        if not client:
            raise HTTPException(status_code=400, detail="Provider nao suportado.")
        return client.lookup_flight_by_number(provider_key.plain_key, flight_number, flight_date_obj)

    @staticmethod
    def _default_marketplace(provider: str) -> str:
        return "rapidapi" if provider == PRIMARY_PROVIDER else "direct"

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
        response_json: Any,
        normalized_json: dict[str, Any],
    ) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=max(5, int(self.settings.flight_lookup_cache_ttl_minutes or 720))
        )
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

    def _normalize_provider_flight(
        self,
        *,
        provider: str,
        source: dict[str, Any],
        fallback_flight_number: str,
        flight_date: date,
        raw_response: Any,
        marketplace: str | None,
    ) -> dict[str, Any]:
        if provider == PRIMARY_PROVIDER:
            return self._normalize_aerodatabox_flight(
                source,
                fallback_flight_number=fallback_flight_number,
                flight_date=flight_date,
                raw_response=raw_response,
                marketplace=marketplace,
            )
        return self._normalize_airlabs_flight(
            source,
            fallback_flight_number=fallback_flight_number,
            flight_date=flight_date,
            raw_response=raw_response,
            marketplace=marketplace,
        )

    def _normalize_airlabs_flight(
        self,
        source: dict[str, Any],
        *,
        fallback_flight_number: str,
        flight_date: date,
        raw_response: Any,
        marketplace: str | None,
    ) -> dict[str, Any]:
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
        duration_minutes = parse_duration_minutes(pick(source, "duration", "duration_minutes", "flight_duration"))
        if duration_minutes is None and departure_datetime and arrival_datetime:
            delta = arrival_datetime - departure_datetime
            duration_minutes = max(0, int(delta.total_seconds() // 60))

        flight_number = str(pick(source, "flight_iata", "flight_number", "flight_icao") or fallback_flight_number).upper()
        flight_iata = str(pick(source, "flight_iata", "flight_number") or flight_number).upper()
        departure_iata = str(pick(source, "dep_iata", "departure_iata", "from_iata") or "").upper() or None
        arrival_iata = str(pick(source, "arr_iata", "arrival_iata", "to_iata") or "").upper() or None

        normalized = {
            "provider": FALLBACK_PROVIDER,
            "marketplace": (marketplace or "direct").lower(),
            "flight_number": flight_number,
            "flight_iata": flight_iata,
            "flight_icao": str(pick(source, "flight_icao") or "").upper() or None,
            "flight_date": flight_date.isoformat(),
            "airline_name": pick(source, "airline_name", "airline"),
            "airline_iata": str(pick(source, "airline_iata") or "").upper() or None,
            "airline_icao": str(pick(source, "airline_icao") or "").upper() or None,
            "airline_logo_url": pick(source, "airline_logo", "airline_logo_url", "logo", "airline_logo_path"),
            "departure_airport_iata": departure_iata,
            "departure_airport_name": pick(source, "dep_name", "dep_airport", "dep_airport_name", "departure_airport_name"),
            "departure_city": pick(source, "dep_city", "departure_city", "from_city"),
            "departure_country": pick(source, "dep_country", "departure_country", "from_country"),
            "departure_terminal": pick(source, "dep_terminal", "departure_terminal"),
            "departure_gate": pick(source, "dep_gate", "departure_gate"),
            "departure_datetime": departure_datetime.isoformat() if departure_datetime else None,
            "arrival_airport_iata": arrival_iata,
            "arrival_airport_name": pick(source, "arr_name", "arr_airport", "arr_airport_name", "arrival_airport_name"),
            "arrival_city": pick(source, "arr_city", "arrival_city", "to_city"),
            "arrival_country": pick(source, "arr_country", "arrival_country", "to_country"),
            "arrival_terminal": pick(source, "arr_terminal", "arrival_terminal"),
            "arrival_gate": pick(source, "arr_gate", "arrival_gate"),
            "arrival_datetime": arrival_datetime.isoformat() if arrival_datetime else None,
            "duration_minutes": duration_minutes,
            "status": pick(source, "status", "flight_status"),
            "lookup_mode": pick(source, "lookup_mode") or "exact",
            "raw_provider_response": raw_response,
        }
        normalized["departure"] = {
            "iata": normalized["departure_airport_iata"],
            "airport": normalized["departure_airport_name"],
            "city": normalized["departure_city"],
            "country": normalized["departure_country"],
            "terminal": normalized["departure_terminal"],
            "gate": normalized["departure_gate"],
            "datetime": normalized["departure_datetime"],
        }
        normalized["arrival"] = {
            "iata": normalized["arrival_airport_iata"],
            "airport": normalized["arrival_airport_name"],
            "city": normalized["arrival_city"],
            "country": normalized["arrival_country"],
            "terminal": normalized["arrival_terminal"],
            "gate": normalized["arrival_gate"],
            "datetime": normalized["arrival_datetime"],
        }
        return normalized

    def _normalize_aerodatabox_flight(
        self,
        source: dict[str, Any],
        *,
        fallback_flight_number: str,
        flight_date: date,
        raw_response: Any,
        marketplace: str | None,
    ) -> dict[str, Any]:
        departure_datetime = parse_iso_datetime(
            pick_nested(
                source,
                "departure.revisedTime.local",
                "departure.scheduledTime.local",
                "departure.runwayTime.local",
                "departure.revisedTime.utc",
                "departure.scheduledTime.utc",
            )
        )
        arrival_datetime = parse_iso_datetime(
            pick_nested(
                source,
                "arrival.revisedTime.local",
                "arrival.scheduledTime.local",
                "arrival.runwayTime.local",
                "arrival.revisedTime.utc",
                "arrival.scheduledTime.utc",
            )
        )
        duration_minutes = None
        if departure_datetime and arrival_datetime:
            duration_minutes = max(0, int((arrival_datetime - departure_datetime).total_seconds() // 60))

        flight_number = str(pick(source, "number", "flightNumber") or fallback_flight_number).upper()
        flight_iata = normalize_flight_number(flight_number)
        airline_iata = str(pick_nested(source, "airline.iata") or "").upper() or None
        airline_icao = str(pick_nested(source, "airline.icao") or "").upper() or None
        departure_iata = str(pick_nested(source, "departure.airport.iata") or "").upper() or None
        arrival_iata = str(pick_nested(source, "arrival.airport.iata") or "").upper() or None

        normalized = {
            "provider": PRIMARY_PROVIDER,
            "marketplace": (marketplace or "rapidapi").lower(),
            "flight_number": flight_iata,
            "flight_iata": flight_iata,
            "flight_icao": str(pick(source, "callSign") or "").upper() or None,
            "flight_date": flight_date.isoformat(),
            "airline_name": pick_nested(source, "airline.name"),
            "airline_iata": airline_iata or (flight_iata[:2] if len(flight_iata) >= 2 else None),
            "airline_icao": airline_icao,
            "airline_logo_url": None,
            "departure_airport_iata": departure_iata,
            "departure_airport_name": pick_nested(source, "departure.airport.name", "departure.airport.shortName"),
            "departure_city": pick_nested(source, "departure.airport.municipalityName"),
            "departure_country": pick_nested(source, "departure.airport.countryCode"),
            "departure_terminal": pick_nested(source, "departure.terminal"),
            "departure_gate": pick_nested(source, "departure.gate"),
            "departure_datetime": departure_datetime.isoformat() if departure_datetime else None,
            "arrival_airport_iata": arrival_iata,
            "arrival_airport_name": pick_nested(source, "arrival.airport.name", "arrival.airport.shortName"),
            "arrival_city": pick_nested(source, "arrival.airport.municipalityName"),
            "arrival_country": pick_nested(source, "arrival.airport.countryCode"),
            "arrival_terminal": pick_nested(source, "arrival.terminal"),
            "arrival_gate": pick_nested(source, "arrival.gate"),
            "arrival_datetime": arrival_datetime.isoformat() if arrival_datetime else None,
            "duration_minutes": duration_minutes,
            "status": pick(source, "status"),
            "lookup_mode": pick(source, "lookupMode") or "exact",
            "raw_provider_response": raw_response,
        }
        normalized["departure"] = {
            "iata": normalized["departure_airport_iata"],
            "airport": normalized["departure_airport_name"],
            "city": normalized["departure_city"],
            "country": normalized["departure_country"],
            "terminal": normalized["departure_terminal"],
            "gate": normalized["departure_gate"],
            "datetime": normalized["departure_datetime"],
        }
        normalized["arrival"] = {
            "iata": normalized["arrival_airport_iata"],
            "airport": normalized["arrival_airport_name"],
            "city": normalized["arrival_city"],
            "country": normalized["arrival_country"],
            "terminal": normalized["arrival_terminal"],
            "gate": normalized["arrival_gate"],
            "datetime": normalized["arrival_datetime"],
        }
        return normalized
