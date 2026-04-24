from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints.pages import ensure_agency_member
from app.models.flight_section import FlightSectionJourney, FlightSectionSegment
from app.models.page import Page
from app.models.user import User
from app.services.flight_lookup_service import FlightLookupService, parse_iso_datetime
from app.services.flight_provider_key_manager import FlightProviderKeyManager
from app.services.flight_sections import _serialize_journey

router = APIRouter(prefix="/admin/pages/{page_id}/sections/{section_id}")


class FlightJourneysResponse(BaseModel):
    journeys: list[dict[str, Any]]
    lookup_available: bool


class FlightJourneyCreate(BaseModel):
    direction: str = Field(..., pattern="^(outbound|inbound)$")
    title: Optional[str] = None
    sort_order: Optional[int] = None
    is_enabled: bool = True


class FlightJourneyUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None


class FlightJourneyReorderPayload(BaseModel):
    journey_ids: list[int] = Field(default_factory=list)


class FlightSegmentCreate(BaseModel):
    journey_id: int
    sort_order: Optional[int] = None
    source_mode: str = "manual"
    flight_number: Optional[str] = None
    flight_iata: Optional[str] = None
    flight_icao: Optional[str] = None
    flight_date: Optional[str] = None
    airline_name: Optional[str] = None
    airline_iata: Optional[str] = None
    airline_icao: Optional[str] = None
    airline_logo_url: Optional[str] = None
    departure_airport_iata: Optional[str] = None
    departure_airport_name: Optional[str] = None
    departure_city: Optional[str] = None
    departure_country: Optional[str] = None
    departure_terminal: Optional[str] = None
    departure_gate: Optional[str] = None
    departure_datetime: Optional[str] = None
    arrival_airport_iata: Optional[str] = None
    arrival_airport_name: Optional[str] = None
    arrival_city: Optional[str] = None
    arrival_country: Optional[str] = None
    arrival_terminal: Optional[str] = None
    arrival_gate: Optional[str] = None
    arrival_datetime: Optional[str] = None
    duration_minutes: Optional[int] = None
    cabin_class: Optional[str] = None
    status: Optional[str] = None
    included_personal_item: bool = True
    included_carry_on: bool = True
    included_checked_bag: bool = False
    notes: Optional[str] = None
    raw_provider_response: Optional[Any] = None


class FlightSegmentUpdate(BaseModel):
    sort_order: Optional[int] = None
    source_mode: Optional[str] = None
    flight_number: Optional[str] = None
    flight_iata: Optional[str] = None
    flight_icao: Optional[str] = None
    flight_date: Optional[str] = None
    airline_name: Optional[str] = None
    airline_iata: Optional[str] = None
    airline_icao: Optional[str] = None
    airline_logo_url: Optional[str] = None
    departure_airport_iata: Optional[str] = None
    departure_airport_name: Optional[str] = None
    departure_city: Optional[str] = None
    departure_country: Optional[str] = None
    departure_terminal: Optional[str] = None
    departure_gate: Optional[str] = None
    departure_datetime: Optional[str] = None
    arrival_airport_iata: Optional[str] = None
    arrival_airport_name: Optional[str] = None
    arrival_city: Optional[str] = None
    arrival_country: Optional[str] = None
    arrival_terminal: Optional[str] = None
    arrival_gate: Optional[str] = None
    arrival_datetime: Optional[str] = None
    duration_minutes: Optional[int] = None
    cabin_class: Optional[str] = None
    status: Optional[str] = None
    included_personal_item: Optional[bool] = None
    included_carry_on: Optional[bool] = None
    included_checked_bag: Optional[bool] = None
    notes: Optional[str] = None
    raw_provider_response: Optional[Any] = None


class FlightSegmentReorderPayload(BaseModel):
    journey_id: int
    segment_ids: list[int] = Field(default_factory=list)


class FlightLookupPayload(BaseModel):
    flight_number: str = Field(..., min_length=3, max_length=20)
    flight_date: str = Field(..., min_length=10, max_length=10)
    force_refresh: bool = False
    preferred_provider: Optional[str] = None
    journey_id: Optional[int] = None
    segment_id: Optional[int] = None


def _lookup_available(db: Session) -> bool:
    manager = FlightProviderKeyManager(db)
    return manager.has_any_available_key(("aerodatabox", "airlabs"))


def _ensure_page_access(db: Session, page_id: int, current_user: User) -> Page:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Pagina nao encontrada.")
    ensure_agency_member(db, page.agency_id, current_user)
    return page


def _load_journeys(db: Session, page_id: int, section_id: str) -> list[FlightSectionJourney]:
    return (
        db.query(FlightSectionJourney)
        .filter(FlightSectionJourney.page_id == page_id, FlightSectionJourney.section_id == section_id)
        .order_by(FlightSectionJourney.sort_order.asc(), FlightSectionJourney.id.asc())
        .all()
    )


def _build_response(db: Session, page_id: int, section_id: str) -> FlightJourneysResponse:
    journeys = _load_journeys(db, page_id, section_id)
    return FlightJourneysResponse(
        journeys=[_serialize_journey(journey) for journey in journeys],
        lookup_available=_lookup_available(db),
    )


def _parse_optional_date(value: Any) -> date | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Data de voo invalida. Use YYYY-MM-DD.") from exc


def _resolve_journey_or_404(db: Session, page_id: int, section_id: str, journey_id: int) -> FlightSectionJourney:
    journey = (
        db.query(FlightSectionJourney)
        .filter(
            FlightSectionJourney.id == journey_id,
            FlightSectionJourney.page_id == page_id,
            FlightSectionJourney.section_id == section_id,
        )
        .first()
    )
    if not journey:
        raise HTTPException(status_code=404, detail="Jornada nao encontrada.")
    return journey


def _resolve_segment_or_404(db: Session, page_id: int, section_id: str, segment_id: int) -> FlightSectionSegment:
    segment = (
        db.query(FlightSectionSegment)
        .join(FlightSectionJourney, FlightSectionJourney.id == FlightSectionSegment.journey_id)
        .filter(
            FlightSectionSegment.id == segment_id,
            FlightSectionJourney.page_id == page_id,
            FlightSectionJourney.section_id == section_id,
        )
        .first()
    )
    if not segment:
        raise HTTPException(status_code=404, detail="Trecho nao encontrado.")
    return segment


def _next_segment_order(db: Session, journey_id: int) -> int:
    segment = (
        db.query(FlightSectionSegment)
        .filter(FlightSectionSegment.journey_id == journey_id)
        .order_by(FlightSectionSegment.sort_order.desc(), FlightSectionSegment.id.desc())
        .first()
    )
    return int(segment.sort_order or 0) + 1 if segment else 0


def _apply_segment_updates(segment: FlightSectionSegment, updates: dict[str, Any]) -> None:
    if "sort_order" in updates and updates["sort_order"] is not None:
        segment.sort_order = int(updates["sort_order"])
    if "source_mode" in updates and updates["source_mode"] is not None:
        segment.source_mode = str(updates["source_mode"]).strip() or "manual"
    if "flight_number" in updates:
        segment.flight_number = updates["flight_number"]
    if "flight_iata" in updates:
        segment.flight_iata = updates["flight_iata"]
    if "flight_icao" in updates:
        segment.flight_icao = updates["flight_icao"]
    if "flight_date" in updates:
        segment.flight_date = _parse_optional_date(updates["flight_date"])
    if "airline_name" in updates:
        segment.airline_name = updates["airline_name"]
    if "airline_iata" in updates:
        segment.airline_iata = updates["airline_iata"]
    if "airline_icao" in updates:
        segment.airline_icao = updates["airline_icao"]
    if "airline_logo_url" in updates:
        segment.airline_logo_url = updates["airline_logo_url"]
    if "departure_airport_iata" in updates:
        segment.departure_airport_iata = updates["departure_airport_iata"]
    if "departure_airport_name" in updates:
        segment.departure_airport_name = updates["departure_airport_name"]
    if "departure_city" in updates:
        segment.departure_city = updates["departure_city"]
    if "departure_country" in updates:
        segment.departure_country = updates["departure_country"]
    if "departure_terminal" in updates:
        segment.departure_terminal = updates["departure_terminal"]
    if "departure_gate" in updates:
        segment.departure_gate = updates["departure_gate"]
    if "departure_datetime" in updates:
        segment.departure_datetime = parse_iso_datetime(updates["departure_datetime"])
    if "arrival_airport_iata" in updates:
        segment.arrival_airport_iata = updates["arrival_airport_iata"]
    if "arrival_airport_name" in updates:
        segment.arrival_airport_name = updates["arrival_airport_name"]
    if "arrival_city" in updates:
        segment.arrival_city = updates["arrival_city"]
    if "arrival_country" in updates:
        segment.arrival_country = updates["arrival_country"]
    if "arrival_terminal" in updates:
        segment.arrival_terminal = updates["arrival_terminal"]
    if "arrival_gate" in updates:
        segment.arrival_gate = updates["arrival_gate"]
    if "arrival_datetime" in updates:
        segment.arrival_datetime = parse_iso_datetime(updates["arrival_datetime"])
    if "duration_minutes" in updates and updates["duration_minutes"] is not None:
        segment.duration_minutes = max(0, int(updates["duration_minutes"]))
    if "cabin_class" in updates:
        segment.cabin_class = updates["cabin_class"]
    if "status" in updates:
        segment.status = updates["status"]
    if "included_personal_item" in updates and updates["included_personal_item"] is not None:
        segment.included_personal_item = bool(updates["included_personal_item"])
    if "included_carry_on" in updates and updates["included_carry_on"] is not None:
        segment.included_carry_on = bool(updates["included_carry_on"])
    if "included_checked_bag" in updates and updates["included_checked_bag"] is not None:
        segment.included_checked_bag = bool(updates["included_checked_bag"])
    if "notes" in updates:
        segment.notes = updates["notes"]
    if "raw_provider_response" in updates:
        segment.raw_provider_response = updates["raw_provider_response"]


@router.get("/flight-journeys", response_model=FlightJourneysResponse)
def get_flight_journeys(
    page_id: int,
    section_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    return _build_response(db, page_id, section_id)


@router.post("/flight-journeys/bootstrap", response_model=FlightJourneysResponse)
def bootstrap_flight_journeys(
    page_id: int,
    section_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    journeys = _load_journeys(db, page_id, section_id)
    if not journeys:
        db.add(
            FlightSectionJourney(
                page_id=page_id,
                section_id=section_id,
                direction="outbound",
                title="Ida",
                sort_order=0,
                is_enabled=True,
            )
        )
        db.add(
            FlightSectionJourney(
                page_id=page_id,
                section_id=section_id,
                direction="inbound",
                title="Volta",
                sort_order=1,
                is_enabled=True,
            )
        )
        db.commit()
    return _build_response(db, page_id, section_id)


@router.post("/flight-journeys", response_model=FlightJourneysResponse)
def create_flight_journey(
    page_id: int,
    section_id: str,
    payload: FlightJourneyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    sort_order = int(payload.sort_order) if payload.sort_order is not None else len(_load_journeys(db, page_id, section_id))
    journey = FlightSectionJourney(
        page_id=page_id,
        section_id=section_id,
        direction=payload.direction,
        title=payload.title,
        sort_order=sort_order,
        is_enabled=bool(payload.is_enabled),
    )
    db.add(journey)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.patch("/flight-journeys/{journey_id}", response_model=FlightJourneysResponse)
def update_flight_journey(
    page_id: int,
    section_id: str,
    journey_id: int,
    payload: FlightJourneyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    journey = _resolve_journey_or_404(db, page_id, section_id, journey_id)
    updates = payload.model_dump(exclude_unset=True)
    if "title" in updates:
        journey.title = updates["title"]
    if "sort_order" in updates and updates["sort_order"] is not None:
        journey.sort_order = int(updates["sort_order"])
    if "is_enabled" in updates and updates["is_enabled"] is not None:
        journey.is_enabled = bool(updates["is_enabled"])
    db.add(journey)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.delete("/flight-journeys/{journey_id}", response_model=FlightJourneysResponse)
def delete_flight_journey(
    page_id: int,
    section_id: str,
    journey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    journey = _resolve_journey_or_404(db, page_id, section_id, journey_id)
    db.delete(journey)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.post("/flight-journeys/reorder", response_model=FlightJourneysResponse)
def reorder_flight_journeys(
    page_id: int,
    section_id: str,
    payload: FlightJourneyReorderPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    if not payload.journey_ids:
        return _build_response(db, page_id, section_id)
    journeys = (
        db.query(FlightSectionJourney)
        .filter(
            FlightSectionJourney.page_id == page_id,
            FlightSectionJourney.section_id == section_id,
            FlightSectionJourney.id.in_(payload.journey_ids),
        )
        .all()
    )
    by_id = {journey.id: journey for journey in journeys}
    for index, journey_id in enumerate(payload.journey_ids):
        journey = by_id.get(journey_id)
        if not journey:
            continue
        journey.sort_order = index
        db.add(journey)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.post("/flight-segments", response_model=FlightJourneysResponse)
def create_flight_segment(
    page_id: int,
    section_id: str,
    payload: FlightSegmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    _resolve_journey_or_404(db, page_id, section_id, payload.journey_id)
    sort_order = int(payload.sort_order) if payload.sort_order is not None else _next_segment_order(db, payload.journey_id)
    segment = FlightSectionSegment(
        journey_id=payload.journey_id,
        sort_order=sort_order,
        source_mode=(payload.source_mode or "manual"),
    )
    _apply_segment_updates(segment, payload.model_dump(exclude_unset=True))
    db.add(segment)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.patch("/flight-segments/{segment_id}", response_model=FlightJourneysResponse)
def update_flight_segment(
    page_id: int,
    section_id: str,
    segment_id: int,
    payload: FlightSegmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    segment = _resolve_segment_or_404(db, page_id, section_id, segment_id)
    updates = payload.model_dump(exclude_unset=True)
    _apply_segment_updates(segment, updates)
    db.add(segment)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.delete("/flight-segments/{segment_id}", response_model=FlightJourneysResponse)
def delete_flight_segment(
    page_id: int,
    section_id: str,
    segment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    segment = _resolve_segment_or_404(db, page_id, section_id, segment_id)
    db.delete(segment)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.post("/flight-segments/reorder", response_model=FlightJourneysResponse)
def reorder_flight_segments(
    page_id: int,
    section_id: str,
    payload: FlightSegmentReorderPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FlightJourneysResponse:
    _ensure_page_access(db, page_id, current_user)
    _resolve_journey_or_404(db, page_id, section_id, payload.journey_id)
    if not payload.segment_ids:
        return _build_response(db, page_id, section_id)
    segments = (
        db.query(FlightSectionSegment)
        .filter(
            FlightSectionSegment.journey_id == payload.journey_id,
            FlightSectionSegment.id.in_(payload.segment_ids),
        )
        .all()
    )
    by_id = {segment.id: segment for segment in segments}
    for index, segment_id in enumerate(payload.segment_ids):
        segment = by_id.get(segment_id)
        if not segment:
            continue
        segment.sort_order = index
        db.add(segment)
    db.commit()
    return _build_response(db, page_id, section_id)


@router.post("/flight-lookup")
def lookup_flight(
    page_id: int,
    section_id: str,
    payload: FlightLookupPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _ensure_page_access(db, page_id, current_user)
    service = FlightLookupService(db)
    result = service.lookup(
        payload.flight_number,
        payload.flight_date,
        preferred_provider=payload.preferred_provider,
        force_refresh=payload.force_refresh,
    )

    target_segment: FlightSectionSegment | None = None
    if payload.segment_id:
        target_segment = _resolve_segment_or_404(db, page_id, section_id, payload.segment_id)
    elif payload.journey_id:
        journey = _resolve_journey_or_404(db, page_id, section_id, payload.journey_id)
        target_segment = (
            db.query(FlightSectionSegment)
            .filter(FlightSectionSegment.journey_id == journey.id)
            .order_by(FlightSectionSegment.sort_order.asc(), FlightSectionSegment.id.asc())
            .first()
        )
        if not target_segment:
            target_segment = FlightSectionSegment(
                journey_id=journey.id,
                sort_order=_next_segment_order(db, journey.id),
                source_mode="manual",
            )
            db.add(target_segment)
            db.flush()

    if target_segment:
        flight = result.flight or {}
        _apply_segment_updates(
            target_segment,
            {
                "source_mode": result.provider,
                "flight_number": flight.get("flight_number"),
                "flight_iata": flight.get("flight_iata"),
                "flight_icao": flight.get("flight_icao"),
                "flight_date": flight.get("flight_date") or payload.flight_date,
                "airline_name": flight.get("airline_name"),
                "airline_iata": flight.get("airline_iata"),
                "airline_icao": flight.get("airline_icao"),
                "airline_logo_url": flight.get("airline_logo_url"),
                "departure_airport_iata": flight.get("departure_airport_iata")
                or (flight.get("departure") or {}).get("iata"),
                "departure_airport_name": flight.get("departure_airport_name")
                or (flight.get("departure") or {}).get("airport"),
                "departure_city": flight.get("departure_city") or (flight.get("departure") or {}).get("city"),
                "departure_country": flight.get("departure_country")
                or (flight.get("departure") or {}).get("country"),
                "departure_terminal": flight.get("departure_terminal")
                or (flight.get("departure") or {}).get("terminal"),
                "departure_gate": flight.get("departure_gate") or (flight.get("departure") or {}).get("gate"),
                "departure_datetime": flight.get("departure_datetime")
                or (flight.get("departure") or {}).get("datetime"),
                "arrival_airport_iata": flight.get("arrival_airport_iata") or (flight.get("arrival") or {}).get("iata"),
                "arrival_airport_name": flight.get("arrival_airport_name")
                or (flight.get("arrival") or {}).get("airport"),
                "arrival_city": flight.get("arrival_city") or (flight.get("arrival") or {}).get("city"),
                "arrival_country": flight.get("arrival_country") or (flight.get("arrival") or {}).get("country"),
                "arrival_terminal": flight.get("arrival_terminal") or (flight.get("arrival") or {}).get("terminal"),
                "arrival_gate": flight.get("arrival_gate") or (flight.get("arrival") or {}).get("gate"),
                "arrival_datetime": flight.get("arrival_datetime") or (flight.get("arrival") or {}).get("datetime"),
                "duration_minutes": flight.get("duration_minutes"),
                "status": flight.get("status"),
                "raw_provider_response": result.raw_response or flight.get("raw_provider_response"),
            },
        )
        db.add(target_segment)
        db.commit()

    if result.from_cache:
        message = "Dados carregados do cache. Nenhuma requisicao externa foi consumida."
    elif result.fallback_used:
        message = "AeroDataBox falhou. Dados obtidos pelo provider fallback."
    elif result.provider == "aerodatabox":
        message = "Dados encontrados via AeroDataBox."
    else:
        message = "Consulta realizada com sucesso via provider de voo."

    provider_detail = (
        "Provider: AeroDataBox via RapidAPI."
        if result.provider == "aerodatabox" and (result.marketplace or "").lower() == "rapidapi"
        else f"Provider: {result.provider}."
    )

    return {
        "success": True,
        "provider": result.provider,
        "marketplace": result.marketplace,
        "from_cache": result.from_cache,
        "fallback_used": result.fallback_used,
        "lookup_mode": result.lookup_mode,
        "message": message,
        "provider_message": provider_detail,
        "data": result.flight,
        "flight": result.flight,
    }
