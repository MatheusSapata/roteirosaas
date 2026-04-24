from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.services.aerodatabox_client import AeroDataBoxClientError, AeroDataBoxQuotaExceededError
from app.services.flight_lookup_service import FlightLookupService, normalize_flight_number
from app.services.flight_provider_key_manager import ProviderKey


def _service(monkeypatch):
    service = FlightLookupService(db=SimpleNamespace())
    monkeypatch.setattr(service, "_save_cache", lambda **_: None)
    return service


def _sample_aerodatabox_flight():
    return {
        "number": "AD2769",
        "status": "Scheduled",
        "airline": {"name": "Azul", "iata": "AD", "icao": "AZU"},
        "departure": {
            "airport": {"iata": "POA", "name": "Salgado Filho", "municipalityName": "Porto Alegre", "countryCode": "BR"},
            "scheduledTime": {"local": "2026-12-02T08:00:00-03:00"},
            "terminal": "1",
            "gate": "A1",
        },
        "arrival": {
            "airport": {"iata": "CWB", "name": "Afonso Pena", "municipalityName": "Curitiba", "countryCode": "BR"},
            "scheduledTime": {"local": "2026-12-02T09:10:00-03:00"},
            "terminal": "2",
            "gate": "B2",
        },
    }


def _sample_airlabs_flight():
    return {
        "flight_iata": "AD2769",
        "airline_name": "Azul",
        "airline_iata": "AD",
        "dep_iata": "POA",
        "dep_name": "Salgado Filho",
        "dep_city": "Porto Alegre",
        "dep_country": "BR",
        "dep_time": "2026-12-02T08:00:00-03:00",
        "arr_iata": "CWB",
        "arr_name": "Afonso Pena",
        "arr_city": "Curitiba",
        "arr_country": "BR",
        "arr_time": "2026-12-02T09:10:00-03:00",
        "duration": 70,
        "status": "scheduled",
    }


def test_normalize_flight_number():
    assert normalize_flight_number("AD 2769") == "AD2769"
    assert normalize_flight_number("AD-2769") == "AD2769"
    assert normalize_flight_number("ad2769") == "AD2769"


def test_cache_hit_aerodatabox(monkeypatch):
    service = _service(monkeypatch)
    cached = SimpleNamespace(
        normalized_json={"flight_number": "AD2769", "lookup_mode": "cached", "marketplace": "rapidapi"},
        response_json={"cached": True},
    )
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: cached)
    monkeypatch.setattr(service.key_manager, "list_available_keys", lambda *_: [])

    result = service.lookup("AD 2769", "2026-12-02")
    assert result.provider == "aerodatabox"
    assert result.from_cache is True
    assert result.marketplace == "rapidapi"


def test_cache_miss_aerodatabox(monkeypatch):
    service = _service(monkeypatch)
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: None)

    record = SimpleNamespace(id=10)
    keys = [ProviderKey(record=record, plain_key="x", provider="aerodatabox", marketplace="rapidapi")]
    monkeypatch.setattr(service.key_manager, "list_available_keys", lambda provider: keys if provider == "aerodatabox" else [])

    success_marks: list[object] = []
    monkeypatch.setattr(service.key_manager, "mark_key_success", lambda rec: success_marks.append(rec))
    monkeypatch.setattr(service.key_manager, "mark_key_error", lambda *_, **__: None)

    class _Provider:
        def lookup_flight_by_number(self, *_args):
            return {"payload": {"ok": True}, "selected_flight": _sample_aerodatabox_flight(), "lookup_mode": "exact", "marketplace": "rapidapi"}

    service.providers["aerodatabox"] = _Provider()

    saved = {"called": False}
    monkeypatch.setattr(service, "_save_cache", lambda **_: saved.__setitem__("called", True))
    result = service.lookup("AD-2769", "2026-12-02")

    assert result.provider == "aerodatabox"
    assert result.from_cache is False
    assert saved["called"] is True
    assert success_marks == [record]


def test_usage_of_rapidapi_key_on_success(monkeypatch):
    service = _service(monkeypatch)
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: None)
    record = SimpleNamespace(id=77)
    keys = [ProviderKey(record=record, plain_key="key", provider="aerodatabox", marketplace="rapidapi")]
    monkeypatch.setattr(service.key_manager, "list_available_keys", lambda provider: keys if provider == "aerodatabox" else [])
    success_marks: list[object] = []
    monkeypatch.setattr(service.key_manager, "mark_key_success", lambda rec: success_marks.append(rec))
    monkeypatch.setattr(service.key_manager, "mark_key_error", lambda *_, **__: None)

    class _Provider:
        def lookup_flight_by_number(self, *_args):
            return {"payload": {"ok": True}, "selected_flight": _sample_aerodatabox_flight(), "lookup_mode": "exact", "marketplace": "rapidapi"}

    service.providers["aerodatabox"] = _Provider()
    result = service.lookup("AD2769", "2026-12-02")
    assert result.provider == "aerodatabox"
    assert success_marks == [record]


def test_quota_429_uses_next_key(monkeypatch):
    service = _service(monkeypatch)
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: None)
    key1 = ProviderKey(record=SimpleNamespace(id=1), plain_key="key1", provider="aerodatabox", marketplace="rapidapi")
    key2 = ProviderKey(record=SimpleNamespace(id=2), plain_key="key2", provider="aerodatabox", marketplace="rapidapi")
    monkeypatch.setattr(service.key_manager, "list_available_keys", lambda provider: [key1, key2] if provider == "aerodatabox" else [])

    errors: list[tuple[object, bool]] = []
    monkeypatch.setattr(service.key_manager, "mark_key_success", lambda *_: None)
    monkeypatch.setattr(
        service.key_manager,
        "mark_key_error",
        lambda rec, _message, quota_exceeded=False: errors.append((rec, quota_exceeded)),
    )

    calls = {"count": 0}

    class _Provider:
        def lookup_flight_by_number(self, *_args):
            calls["count"] += 1
            if calls["count"] == 1:
                raise AeroDataBoxQuotaExceededError("quota", status_code=429)
            return {"payload": {"ok": True}, "selected_flight": _sample_aerodatabox_flight(), "lookup_mode": "exact", "marketplace": "rapidapi"}

    service.providers["aerodatabox"] = _Provider()
    result = service.lookup("AD2769", "2026-12-02")
    assert result.provider == "aerodatabox"
    assert calls["count"] == 2
    assert errors and errors[0][1] is True


def test_fallback_to_airlabs_when_aerodatabox_fails(monkeypatch):
    service = _service(monkeypatch)
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: None)
    key_a = ProviderKey(record=SimpleNamespace(id=11), plain_key="ka", provider="aerodatabox", marketplace="rapidapi")
    key_b = ProviderKey(record=SimpleNamespace(id=22), plain_key="kb", provider="airlabs", marketplace="direct")
    monkeypatch.setattr(
        service.key_manager,
        "list_available_keys",
        lambda provider: [key_a] if provider == "aerodatabox" else ([key_b] if provider == "airlabs" else []),
    )
    monkeypatch.setattr(service.key_manager, "mark_key_success", lambda *_: None)
    monkeypatch.setattr(service.key_manager, "mark_key_error", lambda *_args, **_kwargs: None)

    class _Aero:
        def lookup_flight_by_number(self, *_args):
            raise AeroDataBoxClientError("upstream error", status_code=502)

    class _Air:
        def lookup_flight_by_number(self, *_args):
            return {"payload": {"ok": True}, "selected_flight": _sample_airlabs_flight(), "lookup_mode": "exact", "marketplace": "direct"}

    service.providers["aerodatabox"] = _Aero()
    service.providers["airlabs"] = _Air()

    result = service.lookup("AD2769", "2026-12-02")
    assert result.provider == "airlabs"
    assert result.fallback_used is True


def test_without_aerodatabox_key_uses_airlabs(monkeypatch):
    service = _service(monkeypatch)
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: None)
    key_b = ProviderKey(record=SimpleNamespace(id=22), plain_key="kb", provider="airlabs", marketplace="direct")
    monkeypatch.setattr(
        service.key_manager,
        "list_available_keys",
        lambda provider: [] if provider == "aerodatabox" else ([key_b] if provider == "airlabs" else []),
    )
    monkeypatch.setattr(service.key_manager, "mark_key_success", lambda *_: None)
    monkeypatch.setattr(service.key_manager, "mark_key_error", lambda *_args, **_kwargs: None)

    class _Air:
        def lookup_flight_by_number(self, *_args):
            return {"payload": {"ok": True}, "selected_flight": _sample_airlabs_flight(), "lookup_mode": "exact", "marketplace": "direct"}

    service.providers["airlabs"] = _Air()
    result = service.lookup("AD2769", "2026-12-02")
    assert result.provider == "airlabs"
    assert result.fallback_used is True


def test_aerodatabox_normalization_shape(monkeypatch):
    service = _service(monkeypatch)
    normalized = service._normalize_aerodatabox_flight(
        _sample_aerodatabox_flight(),
        fallback_flight_number="AD2769",
        flight_date=date.fromisoformat("2026-12-02"),
        raw_response={"raw": 1},
        marketplace="rapidapi",
    )
    assert normalized["provider"] == "aerodatabox"
    assert normalized["marketplace"] == "rapidapi"
    assert normalized["flight_number"] == "AD2769"
    assert normalized["departure_airport_iata"] == "POA"
    assert normalized["arrival_airport_iata"] == "CWB"
    assert normalized["airline_logo_url"] is None


def test_force_refresh_ignores_cache(monkeypatch):
    service = _service(monkeypatch)
    cached = SimpleNamespace(
        normalized_json={"flight_number": "AD2769", "lookup_mode": "cached", "marketplace": "rapidapi"},
        response_json={"cached": True},
    )
    monkeypatch.setattr(service, "_find_valid_cache", lambda *_, **__: cached)
    key = ProviderKey(record=SimpleNamespace(id=1), plain_key="x", provider="aerodatabox", marketplace="rapidapi")
    monkeypatch.setattr(service.key_manager, "list_available_keys", lambda provider: [key] if provider == "aerodatabox" else [])
    monkeypatch.setattr(service.key_manager, "mark_key_success", lambda *_: None)
    monkeypatch.setattr(service.key_manager, "mark_key_error", lambda *_args, **_kwargs: None)

    calls = {"count": 0}

    class _Provider:
        def lookup_flight_by_number(self, *_args):
            calls["count"] += 1
            return {"payload": {"ok": True}, "selected_flight": _sample_aerodatabox_flight(), "lookup_mode": "exact", "marketplace": "rapidapi"}

    service.providers["aerodatabox"] = _Provider()
    result = service.lookup("AD2769", "2026-12-02", force_refresh=True)
    assert result.from_cache is False
    assert calls["count"] == 1
