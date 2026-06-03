from __future__ import annotations

from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.models.whatsapp import WhatsAppInboxPermission
from app.services.auth import get_password_hash


def _create_user(db_session, *, email: str, plan: str) -> User:
    user = User(
        name=email.split("@")[0],
        email=email,
        hashed_password=get_password_hash("SenhaForte123"),
        is_active=True,
        plan=plan,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_agency(db_session, *, name: str, slug: str, owner: User) -> Agency:
    agency = Agency(name=name, slug=slug)
    db_session.add(agency)
    db_session.commit()
    db_session.refresh(agency)

    owner.primary_agency_id = agency.id
    db_session.add(owner)
    db_session.add(AgencyUser(agency_id=agency.id, user_id=owner.id, role="owner"))
    db_session.commit()
    db_session.refresh(owner)
    return agency


def _login(client, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SenhaForte123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_whatsapp_connections_available_for_scale_and_blocked_for_free(client, db_session):
    scale_user = _create_user(db_session, email="scale@example.com", plan="escala")
    scale_agency = _create_agency(db_session, name="Scale Agency", slug="scale-agency", owner=scale_user)
    scale_token = _login(client, scale_user.email)

    ok_response = client.get(
        "/api/v1/whatsapp/connections",
        params={"agencyId": scale_agency.id},
        headers={"Authorization": f"Bearer {scale_token}"},
    )
    assert ok_response.status_code == 200

    free_user = _create_user(db_session, email="free@example.com", plan="free")
    free_agency = _create_agency(db_session, name="Free Agency", slug="free-agency", owner=free_user)
    free_token = _login(client, free_user.email)

    blocked_response = client.get(
        "/api/v1/whatsapp/connections",
        params={"agencyId": free_agency.id},
        headers={"Authorization": f"Bearer {free_token}"},
    )
    assert blocked_response.status_code == 403
    assert "Escala e Teste" in blocked_response.json()["detail"]


def test_whatsapp_inbox_requires_scale_or_test_plus_permission(client, db_session):
    user = _create_user(db_session, email="inbox@example.com", plan="escala")
    agency = _create_agency(db_session, name="Inbox Agency", slug="inbox-agency", owner=user)
    token = _login(client, user.email)

    no_permission_response = client.get(
        "/api/v1/whatsapp/inbox-access",
        params={"agencyId": agency.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert no_permission_response.status_code == 200
    assert no_permission_response.json()["enabled"] is False

    db_session.add(WhatsAppInboxPermission(agency_id=agency.id, user_id=user.id, enabled=True, granted_at=None, revoked_at=None))
    db_session.commit()

    permission_response = client.get(
        "/api/v1/whatsapp/inbox-access",
        params={"agencyId": agency.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert permission_response.status_code == 200
    assert permission_response.json()["enabled"] is True

    db_session.query(WhatsAppInboxPermission).delete()
    db_session.commit()

    free_user = _create_user(db_session, email="inbox-free@example.com", plan="free")
    free_agency = _create_agency(db_session, name="Free Inbox Agency", slug="free-inbox-agency", owner=free_user)
    free_token = _login(client, free_user.email)

    blocked_response = client.get(
        "/api/v1/whatsapp/inbox-access",
        params={"agencyId": free_agency.id},
        headers={"Authorization": f"Bearer {free_token}"},
    )
    assert blocked_response.status_code == 200
    assert blocked_response.json()["enabled"] is False
