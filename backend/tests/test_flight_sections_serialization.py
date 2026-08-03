from datetime import date, datetime
from types import SimpleNamespace

from app.services.flight_sections import _serialize_segment


def _raw_flight(departure_date: str, arrival_date: str) -> dict:
    return {
        "number": "TP104",
        "departure": {"scheduledTime": {"local": f"{departure_date}T17:25:00-03:00"}},
        "arrival": {"scheduledTime": {"local": f"{arrival_date}T06:45:00+01:00"}},
    }


def test_serialize_segment_selects_raw_occurrence_by_departure_date():
    segment = SimpleNamespace(
        id=1,
        journey_id=1,
        sort_order=0,
        source_mode="aerodatabox",
        flight_number="TP104",
        flight_iata="TP104",
        flight_icao=None,
        flight_date=date(2026, 8, 18),
        airline_name="TAP Air Portugal",
        airline_iata="TP",
        airline_icao="TAP",
        airline_logo_url=None,
        departure_airport_iata="CNF",
        departure_airport_name="Belo Horizonte Tancredo Neves",
        departure_city="Belo Horizonte",
        departure_country="BR",
        departure_terminal=None,
        departure_gate=None,
        departure_datetime=datetime.fromisoformat("2026-08-18T17:25:00-03:00"),
        arrival_airport_iata="LIS",
        arrival_airport_name="Lisbon Portela",
        arrival_city="Lisbon",
        arrival_country="PT",
        arrival_terminal="1",
        arrival_gate=None,
        arrival_datetime=datetime.fromisoformat("2026-08-19T06:45:00+01:00"),
        duration_minutes=560,
        cabin_class=None,
        status="Expected",
        included_personal_item=True,
        included_carry_on=True,
        included_checked_bag=False,
        notes=None,
        raw_provider_response=[
            _raw_flight("2026-08-17", "2026-08-18"),
            _raw_flight("2026-08-18", "2026-08-19"),
        ],
        created_at=None,
        updated_at=None,
    )

    serialized = _serialize_segment(segment)

    assert serialized["departure_datetime"] == "2026-08-18T17:25:00-03:00"
    assert serialized["arrival_datetime"] == "2026-08-19T06:45:00+01:00"
