"""Modelos próprios do cliente: "Salvar como template" no editor e gerenciamento na escolha de modelo."""
from __future__ import annotations

import pytest

from app.api.deps import get_current_active_user, get_current_user
from app.main import app
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page_template import PageTemplate
from app.models.subscription import Subscription
from app.models.user import User

CONFIG = {
    "version": 1,
    "theme": {"color1": "#111111"},
    "sections": [
        {"type": "hero", "enabled": True, "title": "Paris", "logoUrl": "/uploads/logo.png"},
        {"type": "cta", "enabled": True, "link": "https://wa.me/5511999999999?text=oi"},
    ],
    "leadCapture": {"formId": 3},
    "tracking": {"metaPixel": "123"},
}


def _login(user: User) -> None:
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_current_user] = lambda: user


def _agency(db, slug: str, plan: str = "infinity") -> tuple[Agency, User]:
    owner = User(name="Dono", email=f"{slug}@x.com", hashed_password="x", plan=plan, role="owner", is_owner=True)
    agency = Agency(name=slug, slug=slug)
    db.add_all([owner, agency])
    db.commit()
    db.add(AgencyUser(agency_id=agency.id, user_id=owner.id, role="owner"))
    if plan != "free":
        owner.subscription = Subscription(user_id=owner.id, plan=plan, status="active")
    db.commit()
    return agency, owner


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


def _save(client, agency, name="Meu modelo", config=CONFIG):
    return client.post(
        "/api/v1/page-templates/agency", json={"agency_id": agency.id, "name": name, "config_json": config}
    )


def test_salvar_listar_renomear_excluir(client, db_session):
    agency, owner = _agency(db_session, "agencia-a")
    db_session.add(PageTemplate(name="Plataforma", slug="plataforma", config_json={"sections": []}))
    db_session.commit()
    _login(owner)

    res = _save(client, agency)
    assert res.status_code == 201, res.text
    saved = res.json()
    assert saved["agency_id"] == agency.id
    assert set(saved["config_json"]) == {"version", "theme", "sections"}
    assert saved["config_json"]["sections"][0]["logoUrl"] == "{{AGENCY_LOGO_URL}}"
    assert saved["config_json"]["sections"][1]["link"] == "{{WHATSAPP_LINK}}"
    # Nome repetido não quebra o slug único.
    assert _save(client, agency).status_code == 201

    listed = client.get("/api/v1/page-templates", params={"agency_id": agency.id}).json()
    assert [t["name"] for t in listed] == ["Meu modelo", "Meu modelo", "Plataforma"]
    # Sem agência: só os da plataforma (tela do admin master).
    assert [t["name"] for t in client.get("/api/v1/page-templates").json()] == ["Plataforma"]

    res = client.patch(f"/api/v1/page-templates/agency/{saved['id']}", json={"name": "Europa", "description": "10 dias"})
    assert res.status_code == 200, res.text
    assert (res.json()["name"], res.json()["description"]) == ("Europa", "10 dias")

    page = client.post(
        "/api/v1/pages",
        json={"agency_id": agency.id, "title": "Nova", "slug": "nova", "template_id": saved["id"]},
    )
    assert page.status_code == 200, page.text
    assert page.json()["config_json"]["sections"][0]["title"] == "Paris"

    assert client.delete(f"/api/v1/page-templates/agency/{saved['id']}").status_code == 204
    assert len(client.get("/api/v1/page-templates", params={"agency_id": agency.id}).json()) == 2


def test_outra_agencia_nao_ve_nem_mexe(client, db_session):
    agency_a, owner_a = _agency(db_session, "agencia-a")
    agency_b, owner_b = _agency(db_session, "agencia-b")
    _login(owner_a)
    saved = _save(client, agency_a).json()

    _login(owner_b)
    assert client.get("/api/v1/page-templates", params={"agency_id": agency_a.id}).status_code == 403
    assert [t["id"] for t in client.get("/api/v1/page-templates", params={"agency_id": agency_b.id}).json()] == []
    assert client.get(f"/api/v1/page-templates/{saved['id']}").status_code == 403
    assert client.patch(f"/api/v1/page-templates/agency/{saved['id']}", json={"name": "x"}).status_code == 403
    assert client.delete(f"/api/v1/page-templates/agency/{saved['id']}").status_code == 403
    res = client.post(
        "/api/v1/pages",
        json={"agency_id": agency_b.id, "title": "Nova", "slug": "nova", "template_id": saved["id"]},
    )
    assert res.status_code == 404


def test_plano_free_e_pagina_vazia(client, db_session):
    agency, owner = _agency(db_session, "agencia-free", plan="free")
    _login(owner)
    assert _save(client, agency).status_code == 403

    agency2, owner2 = _agency(db_session, "agencia-paga")
    _login(owner2)
    assert _save(client, agency2, config={"sections": []}).status_code == 400
    assert _save(client, agency2, name="   ").status_code in (400, 422)
