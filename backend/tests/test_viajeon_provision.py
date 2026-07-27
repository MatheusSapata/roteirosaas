import hashlib
import hmac
import json
import time
from datetime import datetime, timezone

from app.api.v1.endpoints import viajeon_provision
from app.models.agency import Agency
from app.models.subscription import Subscription
from app.models.user import User
from app.models.viajeon_webhook_event import ViajeonWebhookEvent
from app.services.auth import verify_password


TOKEN = "rvo_platform_test"
SECRET = "rvs_platform_test_secret"
URL = "/api/v1/public/integrations/viajeon/provision"


def _payload(**overrides):
    payload = {
        "event": "subscription.paid",
        "event_id": "evt_test_1",
        "sent_at": "2026-07-27T14:32:11.412Z",
        "environment": "production",
        "plan": "profissional",
        "billing_cycle": "monthly",
        "account": {
            "email": "  CONTATO@agenciaexemplo.com.br ",
            "password": "Xq7!kd92Lm4pZa0R",
            "name": "Maria Souza",
            "phone": "+5551999998888",
            "document": "12345678000199",
            "company_name": "Agência Exemplo Viagens",
            "future_field": "ignored",
        },
        "order": {
            "id": "b1f0f9c2-uuid",
            "code": "VJ-2026-000431",
            "amount": 397.00,
            "currency": "BRL",
            "paid_at": "2026-07-27T14:31:58.000Z",
        },
        "future_field": "ignored",
    }
    payload.update(overrides)
    return payload


def _signed_headers(body: bytes, timestamp: int | None = None):
    timestamp = timestamp if timestamp is not None else int(time.time())
    signature = hmac.new(SECRET.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Viajeon-Token": TOKEN,
        "X-Viajeon-Timestamp": str(timestamp),
        "X-Viajeon-Signature": f"sha256={signature}",
    }


def _post(client, payload, timestamp: int | None = None):
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return client.post(URL, content=body, headers=_signed_headers(body, timestamp))


def setup_module():
    viajeon_provision.settings.viajeon_provision_token = TOKEN
    viajeon_provision.settings.viajeon_provision_secret = SECRET
    viajeon_provision.settings.webapp_base_url = "https://app.roteiroonline.com"


def test_rejects_invalid_signature_before_parsing_json(client):
    response = client.post(
        URL,
        content=b'{"account":{"password":"must-not-be-parsed"',
        headers={
            "X-Viajeon-Token": TOKEN,
            "X-Viajeon-Timestamp": str(int(time.time())),
            "X-Viajeon-Signature": "sha256=bad",
        },
    )
    assert response.status_code == 401
    assert response.json() == {"error": "invalid-signature"}


def test_rejects_expired_timestamp(client):
    response = _post(client, _payload(), timestamp=int(time.time()) - 301)
    assert response.status_code == 401
    assert response.json() == {"error": "expired-timestamp"}


def test_creates_account_agency_subscription_and_idempotency_event(client, db_session):
    response = _post(client, _payload())
    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["plan"] == "profissional"
    assert response.json()["login_url"] == "https://app.roteiroonline.com/login"

    user = db_session.query(User).one()
    agency = db_session.query(Agency).one()
    subscription = db_session.query(Subscription).one()
    event = db_session.query(ViajeonWebhookEvent).one()
    assert user.email == "contato@agenciaexemplo.com.br"
    assert user.plan == "essencial"
    assert user.source == "viajeon"
    assert user.must_change_password is True
    assert verify_password("Xq7!kd92Lm4pZa0R", user.hashed_password)
    assert agency.name == "Agência Exemplo Viagens"
    assert subscription.plan == "essencial"
    assert subscription.provider == "viajeon"
    assert subscription.valid_until.replace(tzinfo=timezone.utc) == datetime(
        2026, 8, 26, 14, 31, 58, tzinfo=timezone.utc
    )
    assert event.status == "processed"

    duplicate = _post(client, _payload())
    assert duplicate.status_code == 200
    assert duplicate.json() == {"status": "duplicate"}
    assert db_session.query(User).count() == 1


def test_existing_user_is_updated_without_password_overwrite(client, db_session):
    original_hash = viajeon_provision._password_hash("Original9Password")
    user = User(
        email="contato@agenciaexemplo.com.br",
        name="Existing",
        hashed_password=original_hash,
        plan="free",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = _post(client, _payload(event_id="evt_update", plan="escala"))
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    db_session.refresh(user)
    assert user.hashed_password == original_hash
    assert user.plan == "infinity"
    assert user.subscription.plan == "infinity"


def test_annual_subscription_uses_explicit_expiration_and_duplicate_keeps_it(client, db_session):
    payload = _payload(
        event_id="evt_annual",
        billing_cycle="annual",
        subscription={
            "billing_cycle": "annual",
            "period_days": 365,
            "starts_at": "2026-07-27T14:31:58.000Z",
            "expires_at": "2027-07-27T14:31:58.000Z",
        },
    )
    response = _post(client, payload)
    assert response.status_code == 200
    subscription = db_session.query(Subscription).one()
    expected = datetime(2027, 7, 27, 14, 31, 58, tzinfo=timezone.utc)
    assert subscription.valid_until.replace(tzinfo=timezone.utc) == expected

    duplicate_payload = dict(payload)
    duplicate_payload["subscription"] = {
        **payload["subscription"],
        "expires_at": "2030-07-27T14:31:58.000Z",
    }
    duplicate = _post(client, duplicate_payload)
    assert duplicate.status_code == 200
    assert duplicate.json() == {"status": "duplicate"}
    db_session.refresh(subscription)
    assert subscription.valid_until.replace(tzinfo=timezone.utc) == expected


def test_legacy_annual_payload_falls_back_to_365_days(client, db_session):
    response = _post(client, _payload(event_id="evt_legacy_annual", billing_cycle="annual"))
    assert response.status_code == 200
    subscription = db_session.query(Subscription).one()
    assert subscription.valid_until.replace(tzinfo=timezone.utc) == datetime(
        2027, 7, 27, 14, 31, 58, tzinfo=timezone.utc
    )


def test_subscription_cycle_must_match_top_level(client):
    response = _post(
        client,
        _payload(
            event_id="evt_bad_cycle",
            billing_cycle="monthly",
            subscription={
                "billing_cycle": "annual",
                "period_days": 365,
                "starts_at": "2026-07-27T14:31:58.000Z",
                "expires_at": "2027-07-27T14:31:58.000Z",
            },
        ),
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid-payload"


def test_invalid_plan_returns_contract_422(client):
    response = _post(client, _payload(plan="enterprise"))
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid-payload"
    assert any(detail["field"] == "plan" for detail in body["details"])


def test_unknown_event_is_authenticated_then_ignored(client, db_session):
    response = _post(client, _payload(event="subscription.cancelled"))
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    assert db_session.query(ViajeonWebhookEvent).count() == 0
