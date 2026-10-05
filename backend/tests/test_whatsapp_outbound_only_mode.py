from types import SimpleNamespace

from app.api.v1.endpoints import whatsapp_webhooks
from starlette.requests import Request


def _request() -> Request:
    return Request({"type": "http", "query_string": b"", "headers": []})


def test_disabled_inbox_webhook_does_not_open_database_session(monkeypatch):
    monkeypatch.setattr(
        whatsapp_webhooks,
        "settings",
        SimpleNamespace(whatsapp_inbox_webhooks_enabled=False, evolution_webhook_token=None, env="test"),
    )
    monkeypatch.setattr(
        whatsapp_webhooks,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("database session should not be opened")),
    )

    result = whatsapp_webhooks.evolution_webhook({"event": "messages.upsert"}, _request())

    assert result.accepted is True
    assert result.reason == "inbox_webhooks_disabled"


def test_disabled_inbox_event_webhook_does_not_open_database_session(monkeypatch):
    monkeypatch.setattr(
        whatsapp_webhooks,
        "settings",
        SimpleNamespace(whatsapp_inbox_webhooks_enabled=False, evolution_webhook_token=None, env="test"),
    )
    monkeypatch.setattr(
        whatsapp_webhooks,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("database session should not be opened")),
    )

    result = whatsapp_webhooks.evolution_webhook_by_event("messages-upsert", {"data": {}}, _request())

    assert result.accepted is True
    assert result.reason == "inbox_webhooks_disabled"
