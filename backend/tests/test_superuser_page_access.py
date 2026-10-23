"""Superusuário (Admin Master) editando a página de outra conta: lê a agência, o domínio e o perfil
dela e envia imagens para ela. Quem não é membro nem superusuário continua barrado."""
from __future__ import annotations

import pytest

from app.api.deps import get_current_active_user, get_current_user
from app.main import app
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.user import User


@pytest.fixture
def setup(db_session):
    owner = User(name="Dono", email="dono@x.com", hashed_password="x")
    agency = Agency(name="Agência Cliente", slug="cliente")
    db_session.add_all([owner, agency])
    db_session.commit()
    db_session.add(AgencyUser(agency_id=agency.id, user_id=owner.id, role="owner"))
    page = Page(agency_id=agency.id, title="Roteiro", slug="roteiro", status="draft", config_json={"sections": []})
    db_session.add(page)
    db_session.commit()
    yield agency, page
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


def _as(user: User) -> None:
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_current_user] = lambda: user


def test_superusuario_le_agencia_dominio_e_perfil(client, setup):
    agency, page = setup
    _as(User(id=999, email="admin@x.com", is_superuser=True, is_active=True))
    assert client.get(f"/api/v1/agencies/{agency.id}").json()["slug"] == "cliente"
    assert client.get("/api/v1/agencies/me/domains", params={"agency_id": agency.id}).status_code == 200
    profile = client.get(f"/api/v1/pages/{page.id}/agency-profile")
    assert profile.status_code == 200 and profile.json()["agency_id"] == agency.id


def test_quem_nao_e_membro_continua_barrado(client, setup):
    agency, page = setup
    _as(User(id=998, email="outro@x.com", is_superuser=False, is_active=True, role="owner"))
    assert client.get(f"/api/v1/agencies/{agency.id}").status_code == 403
    assert client.get("/api/v1/agencies/me/domains", params={"agency_id": agency.id}).status_code == 403
    assert client.get(f"/api/v1/pages/{page.id}/agency-profile").status_code == 403
    upload = client.post(
        "/api/v1/media/upload",
        params={"agency_id": agency.id},
        files={"file": ("a.png", b"x", "image/png")},
    )
    assert upload.status_code == 403
