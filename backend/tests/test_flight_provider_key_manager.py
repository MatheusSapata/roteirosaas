from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.flight_provider_key_manager import FlightProviderKeyManager


def test_should_auto_reset_monthly_usage_when_cycle_changes():
    record = SimpleNamespace(
        reset_day=1,
        last_used_at=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
        monthly_usage_estimated=20,
    )
    now = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
    assert FlightProviderKeyManager._should_auto_reset_monthly_usage(record, now) is True


def test_should_not_auto_reset_without_usage():
    record = SimpleNamespace(
        reset_day=5,
        last_used_at=datetime(2026, 4, 8, 10, 0, tzinfo=timezone.utc),
        monthly_usage_estimated=0,
    )
    now = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
    assert FlightProviderKeyManager._should_auto_reset_monthly_usage(record, now) is False


def test_has_available_key_false_when_no_usable_key(monkeypatch):
    manager = FlightProviderKeyManager(db=SimpleNamespace())

    def fake_list(provider: str = "airlabs"):
        assert provider == "airlabs"
        return []

    monkeypatch.setattr(manager, "list_available_keys", fake_list)
    assert manager.has_available_key("airlabs") is False


def test_has_available_key_true_when_usable_key_exists(monkeypatch):
    manager = FlightProviderKeyManager(db=SimpleNamespace())

    def fake_list(provider: str = "airlabs"):
        assert provider == "airlabs"
        return [SimpleNamespace()]

    monkeypatch.setattr(manager, "list_available_keys", fake_list)
    assert manager.has_available_key("airlabs") is True
