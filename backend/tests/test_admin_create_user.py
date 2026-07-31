from datetime import date, timedelta

from app.api.deps import get_current_superuser
from app.models.agency_user import AgencyUser
from app.models.subscription import Subscription
from app.models.user import User


def test_admin_can_create_ready_to_use_user(client, db_session):
    client.app.dependency_overrides[get_current_superuser] = lambda: User(id=999, is_superuser=True)
    valid_until = (date.today() + timedelta(days=30)).isoformat()

    try:
        response = client.post(
            "/api/v1/admin/users",
            json={
                "name": "Usuária Criada",
                "email": "NOVA@EXAMPLE.COM",
                "whatsapp": "(11) 99999-0000",
                "password": "Senha123",
                "plan": "growth",
                "valid_until": valid_until,
            },
        )
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)

    assert response.status_code == 201, response.text
    user = db_session.query(User).filter(User.email == "nova@example.com").one()
    subscription = db_session.query(Subscription).filter(Subscription.user_id == user.id).one()
    membership = db_session.query(AgencyUser).filter(AgencyUser.user_id == user.id).one()

    assert user.plan == "growth"
    assert user.whatsapp == "11999990000"
    assert user.primary_agency_id == membership.agency_id
    assert membership.role == "owner"
    assert subscription.plan == "growth"
    assert subscription.provider == "manual"
    assert subscription.status == "active"
    assert subscription.valid_until.date().isoformat() == valid_until

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "nova@example.com", "password": "Senha123"},
    )
    assert login.status_code == 200, login.text


def test_admin_create_user_rejects_duplicate_email(client, db_session):
    db_session.add(User(name="Existente", email="existente@example.com", hashed_password="hash"))
    db_session.commit()
    client.app.dependency_overrides[get_current_superuser] = lambda: User(id=999, is_superuser=True)

    try:
        response = client.post(
            "/api/v1/admin/users",
            json={
                "name": "Outra pessoa",
                "email": "EXISTENTE@example.com",
                "password": "Senha123",
                "plan": "essencial",
                "valid_until": (date.today() + timedelta(days=30)).isoformat(),
            },
        )
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "E-mail já cadastrado."
