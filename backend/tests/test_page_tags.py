"""Tags de páginas: cadastro, tags de cada página e a seção Links/Roteiros no modo "Por tag"."""
from __future__ import annotations

import pytest

from app.api.deps import get_current_active_user, get_current_user
from app.main import app
from app.models.agency import Agency
from app.models.agency_domain import AgencyDomain
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.subscription import Subscription
from app.models.user import User


def _hero(dep: str = "", ret: str = "", image: str = "", subtitle: str = "") -> dict:
    return {"type": "hero", "enabled": True, "departureDate": dep, "returnDate": ret, "backgroundImage": image, "subtitle": subtitle}


def _prices(*values: float) -> dict:
    return {"type": "prices", "enabled": True, "items": [{"title": "Opção", "price": v, "currency": "BRL"} for v in values]}


def _tag_section(tag_ids: list[int], **extra) -> dict:
    return {"type": "links", "enabled": True, "title": "Outras viagens", "mode": "tag", "tagIds": tag_ids, "items": [], **extra}


@pytest.fixture
def agency(db_session):
    owner = User(name="Dono", email="dono@x.com", hashed_password="x", plan="infinity", role="owner", is_owner=True)
    agency = Agency(name="Agência", slug="agencia")
    db_session.add_all([owner, agency])
    db_session.commit()
    db_session.add(AgencyUser(agency_id=agency.id, user_id=owner.id, role="owner"))
    owner.subscription = Subscription(user_id=owner.id, plan="infinity", status="active")
    db_session.commit()
    app.dependency_overrides[get_current_active_user] = lambda: owner
    app.dependency_overrides[get_current_user] = lambda: owner
    yield agency
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


def _page(db, agency, slug, status="published", sections=None, title=None) -> Page:
    page = Page(agency_id=agency.id, title=title or slug.title(), slug=slug, status=status, config_json={"sections": sections or []})
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def _tag(client, agency, name, **extra) -> dict:
    res = client.post("/api/v1/page-tags", json={"agency_id": agency.id, "name": name, **extra})
    assert res.status_code == 200, res.text
    return res.json()


def _set_tags(client, page, *tag_ids):
    res = client.put(f"/api/v1/pages/{page.id}/tags", json={"tag_ids": list(tag_ids)})
    assert res.status_code == 200, res.text
    return res.json()


def _public_items(client, slug="vitrine") -> list[dict]:
    res = client.get(f"/api/v1/public/pages/by-slug/agencia/{slug}")
    assert res.status_code == 200, res.text
    section = next(s for s in res.json()["config"]["sections"] if s["type"] == "links")
    return section["items"]


def test_criar_tag_repetida_devolve_a_existente_e_conta_paginas(client, db_session, agency):
    europa = _tag(client, agency, "Europa")
    assert europa["color"] == "blue"
    assert _tag(client, agency, "  europa ")["id"] == europa["id"]
    page = _page(db_session, agency, "paris")
    assert [t["name"] for t in _set_tags(client, page, europa["id"])] == ["Europa"]

    tags = client.get("/api/v1/page-tags", params={"agency_id": agency.id}).json()
    assert tags == [{"id": europa["id"], "name": "Europa", "color": "blue", "page_count": 1, "sections": []}]
    listed = client.get("/api/v1/pages", params={"agency_id": agency.id}).json()
    assert listed[0]["tags"] == [{"id": europa["id"], "name": "Europa", "color": "blue"}]


def test_renomear_para_nome_existente_e_tag_de_outra_agencia_sao_recusados(client, db_session, agency):
    europa = _tag(client, agency, "Europa")
    nordeste = _tag(client, agency, "Nordeste")
    res = client.put(f"/api/v1/page-tags/{nordeste['id']}", json={"name": "EUROPA"})
    assert res.status_code == 409

    other = Agency(name="Outra", slug="outra")
    db_session.add(other)
    db_session.commit()
    from app.models.page_tag import PageTag

    foreign = PageTag(agency_id=other.id, name="Dela", slug="dela", color="blue")
    db_session.add(foreign)
    db_session.commit()
    page = _page(db_session, agency, "paris")
    res = client.put(f"/api/v1/pages/{page.id}/tags", json={"tag_ids": [europa["id"], foreign.id]})
    assert res.status_code == 400


def test_secao_por_tag_monta_cards_e_deixa_de_fora_rascunho_viagem_passada_e_a_propria_pagina(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    vitrine = _page(db_session, agency, "vitrine", sections=[_tag_section([europa])])
    italia = _page(
        db_session, agency, "italia",
        sections=[_hero("2099-05-03", "2099-05-14", "/uploads/italia.jpg", "<p>Roma e <b>Veneza</b></p>"), _prices(18400, 15900.5)],
        title="Itália",
    )
    paris = _page(db_session, agency, "paris", sections=[_hero("2099-04-12")], title="Paris")
    rascunho = _page(db_session, agency, "rascunho", status="draft")
    passada = _page(db_session, agency, "lisboa", sections=[_hero("2000-01-10")])
    sem_tag = _page(db_session, agency, "maragogi")
    for page in (vitrine, italia, paris, rascunho, passada):
        _set_tags(client, page, europa)

    items = _public_items(client)
    assert [item["pageId"] for item in items] == [paris.id, italia.id]  # próxima saída primeiro
    card = items[1]
    assert card["url"] == "/agencia/italia"
    assert card["title"] == "Itália"
    assert card["description"] == "Roma e Veneza"
    assert card["image"] == "/uploads/italia.jpg"
    assert card["showDates"] is True and card["departureDate"] == "2099-05-03"
    assert card["showPrice"] is True and card["priceValue"] == "R$ 15.900,50"
    assert items[0]["showPrice"] is False
    assert sem_tag.id not in [item["pageId"] for item in items]

    preview = client.post(f"/api/v1/pages/{vitrine.id}/tag-cards", json={"section": _tag_section([europa])}).json()
    reasons = {row["pageId"]: row["reason"] for row in preview["excluded"]}
    assert reasons == {vitrine.id: "current", rascunho.id: "draft", passada.id: "past"}


def test_regras_da_secao_ordem_limite_grade_e_todas_as_tags(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    grupos = _tag(client, agency, "Grupos")["id"]
    pages = [_page(db_session, agency, f"roteiro-{i}", sections=[_hero(f"2099-0{9 - i}-01")], title=f"Roteiro {chr(74 - i)}") for i in range(9)]
    for page in pages:
        _set_tags(client, page, europa)
    _set_tags(client, pages[0], europa, grupos)

    section = _tag_section([europa], tagSort="title", tagLimit=0, tagHidePast=False, tagShowPrice=False)
    _page(db_session, agency, "vitrine", sections=[section])
    items = _public_items(client)
    assert [item["title"] for item in items] == sorted(item["title"] for item in items)
    assert len(items) == 9

    vit = db_session.query(Page).filter(Page.slug == "vitrine").one()
    vit.config_json = {"sections": [{**section, "carouselEnabled": False}]}
    db_session.commit()
    assert len(_public_items(client)) == 8  # a grade mostra até 8

    vit.config_json = {"sections": [_tag_section([europa, grupos], tagMatch="all")]}
    db_session.commit()
    assert [item["pageId"] for item in _public_items(client)] == [pages[0].id]


def test_dominio_proprio_ativo_usa_link_sem_slug_da_agencia(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    _page(db_session, agency, "vitrine", sections=[_tag_section([europa])])
    _set_tags(client, _page(db_session, agency, "paris"), europa)
    db_session.add(AgencyDomain(agency_id=agency.id, host="agencia.com.br", is_primary=True, is_active=True, is_verified=True, verification_token="t"))
    db_session.commit()
    assert _public_items(client)[0]["url"] == "/paris"


def test_juntar_e_apagar_tag_atualizam_paginas_e_secoes(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    duplicada = _tag(client, agency, "europa 2027")["id"]
    vitrine = _page(db_session, agency, "vitrine", sections=[_tag_section([duplicada])])
    paris = _page(db_session, agency, "paris")
    _set_tags(client, paris, duplicada)

    usada = next(t for t in client.get("/api/v1/page-tags", params={"agency_id": agency.id}).json() if t["id"] == duplicada)
    assert usada["sections"] == [{"page_id": vitrine.id, "page_title": "Vitrine"}]

    merged = client.post(f"/api/v1/page-tags/{duplicada}/merge", json={"into_tag_id": europa})
    assert merged.status_code == 200, merged.text
    assert merged.json()["page_count"] == 1
    db_session.expire_all()
    assert [t.id for t in db_session.get(Page, paris.id).tags] == [europa]
    assert db_session.get(Page, vitrine.id).config_json["sections"][0]["tagIds"] == [europa]
    assert [item["pageId"] for item in _public_items(client)] == [paris.id]

    assert client.delete(f"/api/v1/page-tags/{europa}").status_code == 200
    db_session.expire_all()
    assert db_session.get(Page, paris.id).tags == []
    assert db_session.get(Page, vitrine.id).config_json["sections"][0]["tagIds"] == []
    assert _public_items(client) == []


def test_aplicar_e_tirar_tags_em_lote(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    grupos = _tag(client, agency, "Grupos")["id"]
    a, b = _page(db_session, agency, "a"), _page(db_session, agency, "b")
    _set_tags(client, a, grupos)
    res = client.post(
        "/api/v1/page-tags/bulk",
        json={"agency_id": agency.id, "page_ids": [a.id, b.id], "add_tag_ids": [europa], "remove_tag_ids": [grupos]},
    )
    assert res.status_code == 200, res.text
    counts = {t["id"]: t["page_count"] for t in res.json()}
    assert counts == {europa: 2, grupos: 0}


def test_quem_nao_e_membro_nao_mexe_nas_tags(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    page = _page(db_session, agency, "paris")
    stranger = User(id=998, email="outro@x.com", is_superuser=False, is_active=True, role="owner")
    app.dependency_overrides[get_current_active_user] = lambda: stranger
    assert client.get("/api/v1/page-tags", params={"agency_id": agency.id}).status_code == 403
    assert client.put(f"/api/v1/pages/{page.id}/tags", json={"tag_ids": [europa]}).status_code == 403
    assert client.delete(f"/api/v1/page-tags/{europa}").status_code == 403


def test_preco_do_checkout_e_datas_da_excursao_entram_no_card(client, db_session, agency):
    europa = _tag(client, agency, "Europa")["id"]
    _page(db_session, agency, "vitrine", sections=[_tag_section([europa])])
    checkout = {
        "type": "viajeon_checkout",
        "enabled": True,
        "checkoutSnapshot": {
            "excursion": {"departure_date": "2099-07-01T00:00:00", "return_date": "2099-07-08"},
            "packages": [
                {"id": "a", "name": "Duplo", "price": 4200, "active": True},
                {"id": "b", "name": "Inativo", "price": 100, "active": False},
            ],
        },
    }
    page = _page(db_session, agency, "bariloche", sections=[_hero(), _prices(5000), checkout])
    _set_tags(client, page, europa)
    card = _public_items(client)[0]
    assert card["priceValue"] == "R$ 4.200"
    assert (card["departureDate"], card["returnDate"]) == ("2099-07-01", "2099-07-08")
