from __future__ import annotations

from app.models.agency import Agency
from app.models.flight_section import FlightSectionJourney, FlightSectionSegment
from app.models.page import Page


def test_public_page_renders_flight_details_without_provider_calls(client, db_session, monkeypatch):
    from app.services.flight_lookup_service import FlightLookupService

    def _forbidden_lookup(*_args, **_kwargs):
        raise AssertionError("Public page must not call flight providers.")

    monkeypatch.setattr(FlightLookupService, "lookup", _forbidden_lookup)

    agency = Agency(name="Agencia Teste", slug="agencia-teste")
    db_session.add(agency)
    db_session.commit()
    db_session.refresh(agency)

    page = Page(
        agency_id=agency.id,
        title="Pacote Teste",
        slug="pacote-teste",
        status="published",
        config_json={
            "sections": [
                {
                    "type": "flight_details",
                    "enabled": True,
                    "sectionId": "flight-abc",
                    "title": "Detalhes do voo",
                }
            ]
        },
    )
    db_session.add(page)
    db_session.commit()
    db_session.refresh(page)

    journey = FlightSectionJourney(
        page_id=page.id,
        section_id="flight-abc",
        direction="outbound",
        title="Ida",
        sort_order=0,
        is_enabled=True,
    )
    db_session.add(journey)
    db_session.commit()
    db_session.refresh(journey)

    segment = FlightSectionSegment(
        journey_id=journey.id,
        sort_order=0,
        source_mode="manual",
        flight_number="AD2769",
        flight_iata="AD2769",
        departure_airport_iata="POA",
        arrival_airport_iata="CWB",
    )
    db_session.add(segment)
    db_session.commit()

    response = client.get("/api/v1/public/pages/by-slug/agencia-teste/pacote-teste")
    assert response.status_code == 200
    payload = response.json()
    sections = payload["config"]["sections"]
    flight_section = next(section for section in sections if section.get("type") == "flight_details")
    assert flight_section.get("journeys")
    assert flight_section.get("lookupAvailable") in (None, False)
