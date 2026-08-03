from types import SimpleNamespace

from app.api.v1.endpoints import whatsapp_webhooks


def test_disabled_inbox_webhook_does_not_open_database_session(monkeypatch):
    monkeypatch.setattr(
        whatsapp_webhooks,
        "settings",
        SimpleNamespace(whatsapp_inbox_webhooks_enabled=False),
    )
    monkeypatch.setattr(
        whatsapp_webhooks,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("database session should not be opened")),
    )

    result = whatsapp_webhooks.evolution_webhook({"event": "messages.upsert"})

    assert result.accepted is True
    assert result.reason == "inbox_webhooks_disabled"


def test_disabled_inbox_event_webhook_does_not_open_database_session(monkeypatch):
    monkeypatch.setattr(
        whatsapp_webhooks,
        "settings",
        SimpleNamespace(whatsapp_inbox_webhooks_enabled=False),
    )
    monkeypatch.setattr(
        whatsapp_webhooks,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("database session should not be opened")),
    )

    result = whatsapp_webhooks.evolution_webhook_by_event("messages-upsert", {"data": {}})

    assert result.accepted is True
    assert result.reason == "inbox_webhooks_disabled"
