from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.flight_section import FlightSectionJourney
from app.services.flight_provider_key_manager import FlightProviderKeyManager


def _normalize_section_id(section: dict[str, Any]) -> str:
    section_id = (
        str(section.get("sectionId") or section.get("section_id") or section.get("anchorId") or "").strip()
    )
    if not section_id:
        section_id = f"flight-{uuid4().hex[:12]}"
    section["sectionId"] = section_id
    return section_id


def ensure_flight_section_ids(config: Any) -> Any:
    if not isinstance(config, dict):
        return config
    sections = config.get("sections")
    if not isinstance(sections, list):
        return config
    for section in sections:
        if not isinstance(section, dict):
            continue
        if section.get("type") != "flight_details":
            continue
        _normalize_section_id(section)
    return config


def collect_flight_section_ids(config: Any) -> set[str]:
    ids: set[str] = set()
    if not isinstance(config, dict):
        return ids
    sections = config.get("sections")
    if not isinstance(sections, list):
        return ids
    for section in sections:
        if not isinstance(section, dict):
            continue
        if section.get("type") != "flight_details":
            continue
        section_id = _normalize_section_id(section)
        if section_id:
            ids.add(section_id)
    return ids


def cleanup_removed_flight_sections(db: Session, page_id: int, config: Any) -> None:
    valid_section_ids = collect_flight_section_ids(config)
    query = db.query(FlightSectionJourney).filter(FlightSectionJourney.page_id == page_id)
    if not valid_section_ids:
        query.delete(synchronize_session=False)
        return
    query.filter(~FlightSectionJourney.section_id.in_(valid_section_ids)).delete(synchronize_session=False)


def _serialize_segment(segment: Any) -> dict[str, Any]:
    return {
        "id": segment.id,
        "journey_id": segment.journey_id,
        "sort_order": segment.sort_order,
        "source_mode": segment.source_mode,
        "flight_number": segment.flight_number,
        "flight_iata": segment.flight_iata,
        "flight_icao": segment.flight_icao,
        "flight_date": segment.flight_date.isoformat() if segment.flight_date else None,
        "airline_name": segment.airline_name,
        "airline_iata": segment.airline_iata,
        "airline_icao": segment.airline_icao,
        "airline_logo_url": segment.airline_logo_url,
        "departure_airport_iata": segment.departure_airport_iata,
        "departure_airport_name": segment.departure_airport_name,
        "departure_city": segment.departure_city,
        "departure_country": segment.departure_country,
        "departure_terminal": segment.departure_terminal,
        "departure_gate": segment.departure_gate,
        "departure_datetime": segment.departure_datetime.isoformat() if segment.departure_datetime else None,
        "arrival_airport_iata": segment.arrival_airport_iata,
        "arrival_airport_name": segment.arrival_airport_name,
        "arrival_city": segment.arrival_city,
        "arrival_country": segment.arrival_country,
        "arrival_terminal": segment.arrival_terminal,
        "arrival_gate": segment.arrival_gate,
        "arrival_datetime": segment.arrival_datetime.isoformat() if segment.arrival_datetime else None,
        "duration_minutes": segment.duration_minutes,
        "cabin_class": segment.cabin_class,
        "status": segment.status,
        "included_personal_item": bool(segment.included_personal_item),
        "included_carry_on": bool(segment.included_carry_on),
        "included_checked_bag": bool(segment.included_checked_bag),
        "notes": segment.notes,
        "raw_provider_response": segment.raw_provider_response,
        "created_at": segment.created_at.isoformat() if segment.created_at else None,
        "updated_at": segment.updated_at.isoformat() if segment.updated_at else None,
    }


def _serialize_journey(journey: Any) -> dict[str, Any]:
    return {
        "id": journey.id,
        "page_id": journey.page_id,
        "section_id": journey.section_id,
        "direction": journey.direction,
        "title": journey.title,
        "sort_order": journey.sort_order,
        "is_enabled": bool(journey.is_enabled),
        "segments": [_serialize_segment(segment) for segment in (journey.segments or [])],
        "created_at": journey.created_at.isoformat() if journey.created_at else None,
        "updated_at": journey.updated_at.isoformat() if journey.updated_at else None,
    }


def inject_flight_sections_into_config(db: Session, page_id: int, config: Any, *, include_lookup_status: bool = False) -> Any:
    if not isinstance(config, dict):
        return config
    sections = config.get("sections")
    if not isinstance(sections, list):
        return config
    section_ids = collect_flight_section_ids(config)
    if not section_ids:
        return config

    journeys = (
        db.query(FlightSectionJourney)
        .filter(FlightSectionJourney.page_id == page_id, FlightSectionJourney.section_id.in_(section_ids))
        .order_by(FlightSectionJourney.section_id.asc(), FlightSectionJourney.sort_order.asc(), FlightSectionJourney.id.asc())
        .all()
    )
    grouped: dict[str, list[dict[str, Any]]] = {}
    for journey in journeys:
        grouped.setdefault(journey.section_id, []).append(_serialize_journey(journey))

    lookup_available = FlightProviderKeyManager(db).has_available_key("airlabs") if include_lookup_status else None
    now_iso = datetime.utcnow().isoformat()
    for section in sections:
        if not isinstance(section, dict) or section.get("type") != "flight_details":
            continue
        section_id = _normalize_section_id(section)
        section["journeys"] = grouped.get(section_id, [])
        section["lastHydratedAt"] = now_iso
        if include_lookup_status:
            section["lookupAvailable"] = lookup_available
    return config
