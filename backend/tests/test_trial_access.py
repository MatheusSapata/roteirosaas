"""Teste liberado (7 dias do plano Escala pelo Admin Master): a conta fica no ar no período,
mesmo com a assinatura encerrada ou sem assinatura."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.deps import get_current_superuser
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.subscription import Subscription
from app.models.user import User
from app.services.trial import trial_is_active


def _agency_with_page(db, *, subscription: dict | None, slug: str = "agencia-trial", **user_fields) -> User:
    agency = Agency(name="Agencia Trial", slug=slug)
    db.add(agency)
    db.commit()
    owner = User(name="Dono", email=f"dono@{slug}.com", hashed_password="x", plan=user_fields.pop("plan", "growth"), **user_fields)
    db.add(owner)
    db.commit()
    db.add(AgencyUser(agency_id=agency.id, user_id=owner.id, role="owner"))
    if subscription is not None:
        owner.subscription = Subscription(user_id=owner.id, **subscription)
    db.add(Page(agency_id=agency.id, title="Roteiro", slug="roteiro", status="published", config_json={"sections": []}))
    db.commit()
    db.expire_all()
    return owner


def test_trial_is_active_only_inside_the_period():
    now = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
    user = User(trial_plan="infinity", trial_ends_at=now + timedelta(days=7), trial_blocked=False)
    assert trial_is_active(user, now)
    assert not trial_is_active(user, now + timedelta(days=8))
    user.trial_blocked = True
    assert not trial_is_active(user, now)
    assert not trial_is_active(User(trial_plan=None, trial_ends_at=now + timedelta(days=7)), now)


def test_public_page_is_online_during_trial_even_with_cancelled_subscription(client, db_session):
    ends = datetime.now(timezone.utc) + timedelta(days=7)
    _agency_with_page(
        db_session,
        subscription={"plan": "growth", "status": "cancelled", "valid_until": datetime.now(timezone.utc) - timedelta(days=30)},
        trial_plan="infinity",
        trial_started_at=datetime.now(timezone.utc),
        trial_ends_at=ends,
        trial_blocked=False,
    )
    assert client.get("/api/v1/public/pages/by-slug/agencia-trial/roteiro").status_code == 200


def test_public_page_is_online_during_trial_without_subscription(client, db_session):
    _agency_with_page(
        db_session,
        subscription=None,
        trial_plan="infinity",
        trial_started_at=datetime.now(timezone.utc),
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=7),
        trial_blocked=False,
    )
    assert client.get("/api/v1/public/pages/by-slug/agencia-trial/roteiro").status_code == 200


def test_without_trial_a_cancelled_subscription_keeps_the_page_offline(client, db_session):
    _agency_with_page(
        db_session,
        subscription={"plan": "growth", "status": "cancelled", "valid_until": datetime.now(timezone.utc) - timedelta(days=30)},
    )
    response = client.get("/api/v1/public/pages/by-slug/agencia-trial/roteiro")
    assert response.status_code == 503 and response.json()["detail"] == "PAGE_TEMPORARILY_UNAVAILABLE"


def test_panel_is_not_blocked_by_subscription_during_trial():
    sub = Subscription(plan="growth", status="inactive", failed_attempts=3)
    user = User(trial_plan="infinity", trial_ends_at=datetime.now(timezone.utc) + timedelta(days=7), trial_blocked=False)
    user.subscription = sub
    assert user.subscription_blocked is False
    user.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
    assert user.subscription_blocked is True


def test_granting_trial_to_a_blocked_account_republishes_pages_and_takes_it_online(client, db_session):
    owner = _agency_with_page(
        db_session,
        subscription={"plan": "trial", "status": "active"},
        plan="trial",
        trial_plan="trial",
        trial_started_at=datetime.now(timezone.utc) - timedelta(days=10),
        trial_ends_at=datetime.now(timezone.utc) - timedelta(days=3),
        trial_blocked=True,
    )
    # Fim do teste anterior: as páginas foram para rascunho.
    page = db_session.query(Page).filter(Page.slug == "roteiro").first()
    page.status = "draft"
    db_session.commit()
    assert client.get("/api/v1/public/pages/by-slug/agencia-trial/roteiro").status_code == 404

    client.app.dependency_overrides[get_current_superuser] = lambda: User(id=999, is_superuser=True)
    try:
        response = client.post(f"/api/v1/admin/users/{owner.id}/grant-trial", json={"plan": "infinity", "days": 7})
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)
    assert response.status_code == 200

    db_session.expire_all()
    refreshed = db_session.get(User, owner.id)
    assert refreshed.trial_plan == "infinity" and refreshed.trial_blocked is False
    assert db_session.query(Page).filter(Page.slug == "roteiro").first().status == "published"
    assert client.get("/api/v1/public/pages/by-slug/agencia-trial/roteiro").status_code == 200
