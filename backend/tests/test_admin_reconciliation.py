from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints import admin_reconciliation as endpoint


@pytest.fixture
def reconciliation_client(monkeypatch):
    application = FastAPI()
    application.include_router(endpoint.router, prefix="/admin")
    db = Mock()
    application.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(endpoint, "get_settings", lambda: SimpleNamespace(asaas_api_key="test-key", asaas_base_url="https://api-sandbox.asaas.com/v3"))
    monkeypatch.setattr(endpoint, "sao_paulo_today", lambda: date(2026, 9, 25))
    monkeypatch.setattr(endpoint, "load_local", lambda _: ([], []))
    remote = {key: {"data": [], "complete": True, "error": None} for key in ("payments", "subscriptions", "authorizations", "instructions")}
    fetch = Mock(return_value=remote)
    monkeypatch.setattr(endpoint, "fetch_remote", fetch)
    endpoint._cache.clear()
    with TestClient(application) as client:
        yield client, application, fetch, db
    endpoint._cache.clear()


def test_unauthenticated_and_nonmaster_cannot_access_financial_report(reconciliation_client):
    client, application, fetch, db = reconciliation_client
    assert client.get("/admin/billing-reconciliation").status_code == 401
    application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_superuser=False)
    assert client.get("/admin/billing-reconciliation").status_code == 403
    fetch.assert_not_called()


def test_master_gets_report_without_mutating_financial_records(reconciliation_client):
    client, application, fetch, db = reconciliation_client
    application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_superuser=True)
    response = client.get("/admin/billing-reconciliation")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["end_date"] == "2026-09-24"
    assert response.json()["environment"] == "sandbox"
    assert response.json()["complete"]
    db.commit.assert_not_called()
    db.add.assert_not_called()
    db.delete.assert_not_called()


def test_cached_report_and_manual_refresh(reconciliation_client):
    client, application, fetch, db = reconciliation_client
    application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_superuser=True)
    assert client.get("/admin/billing-reconciliation").json()["cached"] is False
    assert client.get("/admin/billing-reconciliation").json()["cached"] is True
    assert fetch.call_count == 1
    assert client.get("/admin/billing-reconciliation?refresh=true").json()["cached"] is False
    assert fetch.call_count == 2


@pytest.mark.parametrize("query", ["start_date=2026-09-24&end_date=2026-09-01", "end_date=2026-09-26", "start_date=invalid"])
def test_bad_date_ranges_never_query_gateway(reconciliation_client, query):
    client, application, fetch, db = reconciliation_client
    application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_superuser=True)
    assert client.get(f"/admin/billing-reconciliation?{query}").status_code == 422
    fetch.assert_not_called()


def test_missing_key_is_actionable(reconciliation_client, monkeypatch):
    client, application, fetch, db = reconciliation_client
    application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_superuser=True)
    monkeypatch.setattr(endpoint, "get_settings", lambda: SimpleNamespace(asaas_api_key=None))
    assert client.get("/admin/billing-reconciliation").status_code == 503
    fetch.assert_not_called()


def test_overlapping_consultation_returns_retry_hint(reconciliation_client):
    client, application, fetch, db = reconciliation_client
    application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_superuser=True)
    endpoint._lock.acquire()
    try:
        response = client.get("/admin/billing-reconciliation")
        assert response.status_code == 429
        assert response.headers["retry-after"] == "15"
        fetch.assert_not_called()
    finally:
        endpoint._lock.release()
