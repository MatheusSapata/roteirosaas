from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.user import User
from app.services import hub_black

KEY = "chave-do-funil"
REPLY = (Path(__file__).parent / "fixtures" / "ai_campos_do_jordao.txt").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def hub_key(monkeypatch):
    monkeypatch.setattr(hub_black.hub_funnel, "hub_config", lambda: ("https://hub/api", KEY, "painel"))


def _agency(db, email: str, slug: str, role: str = "owner") -> Agency:
    user = User(name=slug, email=email, hashed_password="x")
    agency = Agency(name=f"Agência {slug}", slug=slug)
    db.add_all([user, agency])
    db.commit()
    db.add(AgencyUser(agency_id=agency.id, user_id=user.id, role=role))
    db.commit()
    return agency


def test_token_da_previa_so_vale_com_a_assinatura_certa():
    token = hub_black.preview_token(42)
    assert hub_black.page_id_from_token(token) == 42
    assert hub_black.page_id_from_token("42-assinaturaerrada") is None
    assert hub_black.page_id_from_token(token.replace("42-", "43-")) is None
    assert hub_black.page_id_from_token("") is None


def test_sem_chave_nao_ha_previa_nem_entrada(monkeypatch):
    monkeypatch.setattr(hub_black.hub_funnel, "hub_config", lambda: ("", "", ""))
    assert hub_black.preview_signature(1) == ""
    assert hub_black.page_id_from_token("1-abc") is None
    assert hub_black.key_matches("") is False


def test_chave_confere():
    assert hub_black.key_matches(KEY)
    assert not hub_black.key_matches("outra")
    assert not hub_black.key_matches(None)


def test_conta_do_cliente_vem_primeiro(db_session):
    cliente = _agency(db_session, "cliente@x.com", "cliente")
    _agency(db_session, "admin@x.com", "admin")
    agency, fallback = hub_black.resolve_target_agency(db_session, "CLIENTE@x.com", "admin@x.com")
    assert (agency.id, fallback) == (cliente.id, False)


def test_sem_conta_do_cliente_usa_a_do_admin(db_session):
    admin = _agency(db_session, "admin@x.com", "admin")
    agency, fallback = hub_black.resolve_target_agency(db_session, "nao-existe@x.com", "admin@x.com")
    assert (agency.id, fallback) == (admin.id, True)


def test_sem_nenhuma_conta_explica_o_que_fazer(db_session):
    with pytest.raises(HTTPException) as error:
        hub_black.resolve_target_agency(db_session, "nao-existe@x.com", None)
    assert error.value.status_code == 404
    assert "Minha conta" in error.value.detail


def test_andamento_parado_vira_erro(db_session):
    agency = _agency(db_session, "cliente@x.com", "cliente")
    page = hub_black.start_page(db_session, agency, "Campos do Jordão")
    assert hub_black.generation_state(page)["status"] == "generating"
    config = dict(page.config_json)
    config[hub_black.MARKER] = {
        "status": "generating",
        "started_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
    }
    page.config_json = config
    assert hub_black.generation_state(page)["status"] == "error"


def test_nao_gera_duas_vezes_ao_mesmo_tempo(db_session):
    agency = _agency(db_session, "cliente@x.com", "cliente")
    page = hub_black.start_page(db_session, agency, "Campos do Jordão")
    with pytest.raises(HTTPException) as error:
        hub_black.start_page(db_session, agency, "Campos do Jordão", page.id)
    assert error.value.status_code == 409


def test_pedido_para_a_ia_traz_o_consentimento():
    sim = hub_black.build_request_text("T", "D", "Info", True)
    nao = hub_black.build_request_text("T", "D", "Info", False)
    assert "AUTORIZOU" in sim and "NÃO autorizou" in nao
    assert "Não faça perguntas" in sim


def test_geracao_monta_a_pagina_sem_publicar(db_session, monkeypatch):
    from app.services import ai_assistant, stock_images

    agency = _agency(db_session, "cliente@x.com", "cliente")
    page = hub_black.start_page(db_session, agency, "Campos do Jordão")
    calls = []
    monkeypatch.setattr(ai_assistant, "generate_ai_assistant_reply", lambda *args, **kwargs: calls.append(1) or REPLY)
    monkeypatch.setattr(stock_images, "fill_section_photos", lambda *args, **kwargs: pytest.fail("sem consentimento"))
    monkeypatch.setattr("app.services.construtor_prompt.get_active_gpt_model", lambda *args, **kwargs: "gpt-teste")
    monkeypatch.setattr("app.api.v1.endpoints.pages.resolve_agency_plan", lambda *args, **kwargs: "growth")

    hub_black.run_generation(
        page.id,
        {"title": "Campos do Jordão", "description": "Serra", "general_info": "Info", "stock_images_consent": False},
    )

    db_session.expire_all()
    saved = db_session.query(Page).filter(Page.id == page.id).first()
    assert calls == [1]
    assert saved.status == "draft"
    assert hub_black.generation_state(saved) == {"status": "ready", "error": None}
    assert hub_black.MARKER not in saved.config_json
    assert len(saved.config_json["sections"]) > 3
    info = hub_black.describe_page(saved)
    assert info["generation"] == "ready" and info["public_url"] is None
    assert info["preview_url"].endswith(f"/previa-hub/{hub_black.preview_token(page.id)}")


def test_falha_da_ia_fica_como_erro(db_session, monkeypatch):
    from app.services import ai_assistant

    agency = _agency(db_session, "cliente@x.com", "cliente")
    page = hub_black.start_page(db_session, agency, "Campos do Jordão")

    def boom(*args, **kwargs):
        raise HTTPException(status_code=502, detail="A OpenAI não respondeu.")

    monkeypatch.setattr(ai_assistant, "generate_ai_assistant_reply", boom)
    monkeypatch.setattr("app.services.construtor_prompt.get_active_gpt_model", lambda *args, **kwargs: "gpt-teste")
    hub_black.run_generation(page.id, {"title": "T", "general_info": "Info"})
    db_session.expire_all()
    saved = db_session.query(Page).filter(Page.id == page.id).first()
    assert hub_black.generation_state(saved) == {"status": "error", "error": "A OpenAI não respondeu."}


def test_entrada_exige_a_chave(client):
    assert client.get("/api/v1/hub/black/pages/1").status_code == 401
    assert client.get("/api/v1/hub/black/pages/1", headers={"x-funnel-key": "errada"}).status_code == 401
    assert client.get("/api/v1/hub/black/pages/1", headers={"x-funnel-key": KEY}).status_code == 404


def test_previa_publica_com_token(client, db_session):
    agency = _agency(db_session, "cliente@x.com", "cliente")
    page = hub_black.start_page(db_session, agency, "Campos do Jordão")
    ok = client.get(f"/api/v1/public/pages/hub-preview/{hub_black.preview_token(page.id)}")
    assert ok.status_code == 200 and ok.json()["id"] == page.id
    assert client.get(f"/api/v1/public/pages/hub-preview/{page.id}-errado").status_code == 404


def test_limite_do_plano_vira_erro_explicado(db_session, monkeypatch):
    from app.services import ai_assistant

    agency = _agency(db_session, "cliente@x.com", "cliente")
    page = hub_black.start_page(db_session, agency, "Campos do Jordão")
    monkeypatch.setattr(ai_assistant, "generate_ai_assistant_reply", lambda *args, **kwargs: REPLY)
    monkeypatch.setattr("app.services.construtor_prompt.get_active_gpt_model", lambda *args, **kwargs: "gpt-teste")
    monkeypatch.setattr("app.api.v1.endpoints.pages.resolve_agency_plan", lambda *args, **kwargs: "free")
    hub_black.run_generation(page.id, {"title": "T", "general_info": "Info"})
    db_session.expire_all()
    saved = db_session.query(Page).filter(Page.id == page.id).first()
    state = hub_black.generation_state(saved)
    assert state["status"] == "error" and "plano free" in state["error"]
