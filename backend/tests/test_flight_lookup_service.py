from datetime import date, datetime

from app.services.airlabs_client import AirlabsClient, split_flight_designator
from app.services.flight_lookup_service import parse_duration_minutes, parse_iso_datetime


def test_parse_duration_minutes_accepts_hh_mm_and_number():
    assert parse_duration_minutes("01:10") == 70
    assert parse_duration_minutes("70") == 70
    assert parse_duration_minutes(95) == 95


def test_parse_iso_datetime_handles_z_suffix():
    parsed = parse_iso_datetime("2026-12-02T05:30:00Z")
    assert isinstance(parsed, datetime)
    assert parsed is not None
    assert parsed.hour == 5
    assert parsed.minute == 30


def test_split_flight_designator_supports_iata_with_digit():
    airline, number = split_flight_designator("G31241")
    assert airline == "G3"
    assert number == "1241"


def test_split_flight_designator_supports_icao():
    airline, number = split_flight_designator("GLO1241")
    assert airline == "GLO"
    assert number == "1241"


def test_weekday_match_accepts_numeric_and_short_name():
    assert AirlabsClient._weekday_matches("6", date(2026, 4, 25)) is True
    assert AirlabsClient._weekday_matches("sat", date(2026, 4, 25)) is True


def test_route_projection_builds_datetimes():
    projected = AirlabsClient._route_to_flight_like(
        {"flight_iata": "AD6407", "dep_iata": "VCP", "arr_iata": "GIG", "dep_time": "08:10", "duration": 65},
        flight_date=date(2026, 4, 25),
        fallback_flight_number="AD6407",
    )
    assert projected["dep_time"] == "2026-04-25T08:10:00"
    assert projected["arr_time"] == "2026-04-25T09:15:00"
