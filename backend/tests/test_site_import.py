from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.ai_assistant_message import AiAssistantMessage
from app.models.ai_assistant_usage import AiAssistantUsage
from app.models.page import Page
from app.models.site_import_job import SiteImportJob
from app.models.user import User
from app.services import site_import
from app.services.site_import import (
    is_full_import_confirmation,
    pick_unique_title,
    relink_original_urls,
    strip_site_name,
)
from app.services.url_import import ImportedPage, TripLink


# --- Nome da página: título raspado, com desempate ---


def test_unique_title_is_kept_as_is():
    assert pick_unique_title("Gramado no inverno", "Destino: Gramado. 5 dias.", ["Beto Carrero"]) == "Gramado no inverno"


def test_repeated_title_gets_destination_from_text():
    existing = ["Excursão de inverno"]
    text = "Excursão de inverno. Destino: Campos do Jordão. Saída 23 a 28 de junho, 5 dias."
    assert pick_unique_title("Excursão de inverno", text, existing) == "Excursão de inverno — Campos do Jordão"


def test_repeated_title_with_destination_in_phrase():
    text = "Pacote para Porto Seguro com aéreo e hotel."
    assert pick_unique_title("Férias de julho", text, ["férias de julho"]) == "Férias de julho — Porto Seguro"


def test_repeated_title_falls_back_to_duration_then_date():
    # Destino já no título: usa a duração.
    text = "Gramado é linda no inverno. Pacote de 3 dias com café da manhã."
    assert pick_unique_title("Gramado", text, ["Gramado"]) == "Gramado — 3 dias"
    # Destino e duração já tomados: usa a data.
    taken = ["Gramado", "Gramado — 3 dias"]
    text = "Gramado em 3 dias. Saída de 23 a 28 de junho."
    assert pick_unique_title("Gramado", text, taken) == "Gramado — 23 a 28 de jun"


def test_repeated_title_only_solved_by_numeric_suffix():
    # Mesmo destino (no título), sem duração e sem data: só o número desempata.
    existing = ["Gramado", "Gramado (2)"]
    assert pick_unique_title("Gramado", "Venha conhecer Gramado com a gente!", existing) == "Gramado (3)"


def test_title_comparison_ignores_case_and_accents():
    assert pick_unique_title("Excursão Gramado", "", ["EXCURSAO GRAMADO"]) == "Excursão Gramado (2)"


def test_strip_site_name_from_scraped_title():
    assert strip_site_name("Pacote Gramado | Agência Exemplo", "Agência Exemplo | Viagens em grupo") == "Pacote Gramado"
    assert strip_site_name("Pacote Gramado - 5 dias", "Agência Exemplo") == "Pacote Gramado - 5 dias"


# --- Reconhecer a resposta "completo" ---


@pytest.mark.parametrize(
    "text",
    ["completo", "Completo!", "sim", "Sim, pode montar", "tudo", "quero o site inteiro", "o site todo", "pode montar tudo", "todas"],
)
def test_confirmation_variants(text):
    assert is_full_import_confirmation(text)


@pytest.mark.parametrize(
    "text",
    ["não", "só uma viagem", "nao, apenas uma", "", "Quero mudar a cor do banner para azul e trocar a foto do topo por uma praia"],
)
def test_non_confirmation(text):
    assert not is_full_import_confirmation(text)


# --- Religar links da home às páginas novas ---


def test_relink_original_urls_turns_cards_into_page_cards():
    url_map = {
        "agencia.com.br/viagens/gramado": {"page_id": 7, "url": "/agencia/gramado"},
    }
    sections = [
        {"type": "links", "items": [{"title": "Gramado", "source": "external", "url": "https://www.agencia.com.br/viagens/gramado/"}]},
        {"type": "hero", "ctaUrl": "http://agencia.com.br/viagens/gramado#datas"},
        {"type": "story", "text": '<p>Veja <a href="https://agencia.com.br/viagens/gramado">o roteiro</a></p>'},
        {"type": "hero", "ctaUrl": "https://outro-site.com/viagens/gramado"},
    ]
    assert relink_original_urls(sections, url_map) == 3
    card = sections[0]["items"][0]
    assert (card["source"], card["pageId"], card["url"], card["openInNewTab"]) == ("page", 7, "/agencia/gramado", False)
    assert sections[1]["ctaUrl"] == "/agencia/gramado"
    assert 'href="/agencia/gramado"' in sections[2]["text"]
    assert sections[3]["ctaUrl"] == "https://outro-site.com/viagens/gramado"


def test_ensure_created_pages_linked_adds_showcase_before_footer():
    created = [{"page_id": 1, "url": "/a/gramado", "title": "Gramado", "price": "R$ 999"}]
    sections = [{"type": "hero"}, {"type": "agency_footer"}]
    assert site_import.ensure_created_pages_linked(sections, created)
    assert [section["type"] for section in sections] == ["hero", "links", "agency_footer"]
    assert sections[1]["items"][0]["pageId"] == 1
    # Já ligada: não acrescenta outra vitrine.
    assert not site_import.ensure_created_pages_linked(sections, created)


# --- Fluxo completo (raspagem e IA simuladas) ---


def _agency(db, slug: str = "agencia") -> tuple[Agency, User, Page]:
    user = User(name=slug, email=f"{slug}@x.com", hashed_password="x")
    agency = Agency(name=f"Agência {slug}", slug=slug)
    db.add_all([user, agency])
    db.commit()
    db.add(AgencyUser(agency_id=agency.id, user_id=user.id, role="owner"))
    home = Page(agency_id=agency.id, title="Página inicial", slug="inicio", status="draft", config_json={"sections": []})
    db.add(home)
    db.commit()
    return agency, user, home


def _central_page() -> ImportedPage:
    links = [
        TripLink(url="https://agencia.com.br/viagens/gramado", title="Gramado", price="R$ 1.990", text="Gramado R$ 1.990"),
        TripLink(url="https://agencia.com.br/viagens/gramado-2", title="Gramado", price="R$ 2.390", text="Gramado Destino: Canela"),
        TripLink(url="https://agencia.com.br/viagens/foz", title="Foz do Iguaçu", price="R$ 1.290", text="Foz"),
        TripLink(url="https://agencia.com.br/viagens/quebra", title="Quebra", price="", text="Quebra"),
    ]
    return ImportedPage(title="Agência Exemplo | Viagens", text="As melhores viagens em grupo.", image_urls=[], kind="central", trip_links=links)


TRIP_PAGES = {
    "https://agencia.com.br/viagens/gramado": ImportedPage(title="Gramado | Agência Exemplo", text="Destino: Gramado. 5 dias.", image_urls=[]),
    "https://agencia.com.br/viagens/gramado-2": ImportedPage(title="Gramado | Agência Exemplo", text="Destino: Canela. 3 dias.", image_urls=[]),
    "https://agencia.com.br/viagens/foz": ImportedPage(title="Foz do Iguaçu", text="Cataratas.", image_urls=[]),
}


def _fake_reply(conversation, attachments, model_override=None, context=""):
    if "PÁGINAS CRIADAS NESTA IMPORTAÇÃO" in context:
        return (
            "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n"
            "🟩 SEÇÃO: BANNER\nTítulo: Agência Exemplo\n\n"
            "🟩 SEÇÃO: VITRINE DE VIAGENS\nTítulo: Nossas viagens\n"
            "Viagem: Gramado\nPágina: gramado\nValor: R$ 1.990\n"
            "Viagem: Foz do Iguaçu\nPágina: foz-do-iguacu\n"
        )
    return "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n🟩 SEÇÃO: BANNER\nTítulo: Viagem incrível\nSubtítulo: Venha com a gente"


@pytest.fixture
def fake_pipeline(monkeypatch):
    from app.services import ai_assistant, construtor_prompt, url_import

    async def fake_scrape(url):
        if url.rstrip("/") == "https://agencia.com.br":
            return _central_page()
        if url in TRIP_PAGES:
            return TRIP_PAGES[url]
        raise url_import.UrlImportError("Não encontrei conteúdo nessa página.")

    async def no_images(_page):
        return []

    monkeypatch.setattr(site_import, "scrape_page", fake_scrape)
    monkeypatch.setattr(site_import, "download_page_images", no_images)
    monkeypatch.setattr(ai_assistant, "generate_ai_assistant_reply", _fake_reply)
    monkeypatch.setattr(construtor_prompt, "get_active_gpt_model", lambda *_a, **_k: "gpt-test")
    monkeypatch.setattr("app.services.stock_images.fill_section_photos", lambda *_a, **_k: None)
    monkeypatch.setattr(site_import, "start_job_thread", lambda _job_id: None)
    return fake_scrape


def test_full_job_creates_pages_and_relinks_home(db_session, fake_pipeline):
    agency, user, home = _agency(db_session)
    job = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", _central_page())
    reply = site_import.start_job(db_session, job)
    assert "Comecei a montar o site inteiro" in reply
    assert job.status == "running"

    asyncio.run(site_import._run(job.id))
    db_session.expire_all()
    job = db_session.get(SiteImportJob, job.id)
    assert job.status == "completed" and job.home_stage == "done"

    stages = [item["stage"] for item in job.items]
    assert stages == ["done", "done", "done", "error"]
    titles = [item["title"] for item in job.items]
    # Nome raspado sem o nome do site; o repetido ganhou o destino do texto.
    assert titles[:3] == ["Gramado", "Gramado — Canela", "Foz do Iguaçu"]
    assert job.items[3]["page_id"] is None and "conteúdo" in job.items[3]["error"]

    pages = {page.title: page for page in db_session.query(Page).filter(Page.agency_id == agency.id).all()}
    gramado = pages["Gramado"]
    assert gramado.slug == "gramado" and gramado.status == "draft"
    assert gramado.config_json["sections"] and site_import.PAGE_MARKER not in gramado.config_json

    home = db_session.get(Page, home.id)
    assert home.title == "Página inicial"  # a home mantém o nome
    links = next(section for section in home.config_json["sections"] if section["type"] == "links")
    by_title = {card["title"]: card for card in links["items"]}
    assert by_title["Gramado"]["pageId"] == gramado.id and by_title["Gramado"]["url"] == "/agencia/gramado"
    assert by_title["Foz do Iguaçu"]["pageId"] == pages["Foz do Iguaçu"].id
    assert all("pageSlug" not in card for card in links["items"])

    described = site_import.describe_job(job, home)
    assert (described["total"], described["done"], described["failed"]) == (4, 3, 1)


def test_only_one_running_job_per_agency(db_session, fake_pipeline):
    _agency_, user, home = _agency(db_session)
    first = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", _central_page())
    second = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", _central_page())
    site_import.start_job(db_session, first)
    assert site_import.start_job(db_session, second) == site_import.ALREADY_RUNNING_MESSAGE
    assert db_session.get(SiteImportJob, second.id).status == "awaiting_confirmation"


def test_stale_running_job_is_released(db_session, fake_pipeline):
    agency, user, home = _agency(db_session)
    job = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", _central_page())
    site_import.start_job(db_session, job)
    job.updated_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    db_session.commit()
    assert site_import.running_job(db_session, agency.id) is None
    job = db_session.get(SiteImportJob, job.id)
    assert job.status == "failed" and all(item["stage"] == "error" for item in job.items)


# --- Chat: pergunta sem IA e confirmação "completo" ---


def _auth(client, db_session):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Tester", "email": "dono@x.com", "password": "SenhaForte123", "cpf": "12345678909", "whatsapp": "5511999999999"},
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "dono@x.com", "password": "SenhaForte123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    agency = client.post("/api/v1/agencies", json={"name": "Agência Chat", "slug": "agencia-chat"}, headers=headers).json()
    page = client.post("/api/v1/pages", json={"agency_id": agency["id"], "title": "Início", "slug": "inicio"}, headers=headers).json()
    return headers, agency, page


def test_chat_asks_before_full_import_and_starts_on_confirmation(client, db_session, fake_pipeline, monkeypatch):
    from app.api.v1.endpoints import ai_assistant as endpoint

    monkeypatch.setattr(endpoint, "scrape_page", fake_pipeline)

    def no_ai(*_args, **_kwargs):
        raise AssertionError("a IA não pode ser chamada nesse fluxo")

    monkeypatch.setattr(endpoint, "generate_ai_assistant_reply", no_ai)
    started: list[int] = []
    monkeypatch.setattr(site_import, "start_job_thread", started.append)
    headers, agency, page = _auth(client, db_session)

    first = [{"role": "user", "content": "Importar informações de: https://agencia.com.br/"}]
    res = client.post(
        "/api/v1/ai-assistant/chat",
        data={"page_id": page["id"], "conversation": json.dumps(first), "import_url": "https://agencia.com.br/"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    question = res.json()["reply"]
    assert question.startswith(site_import.CENTRAL_QUESTION_PREFIX) and "4 links" in question

    second = first + [{"role": "assistant", "content": question}, {"role": "user", "content": "completo"}]
    res = client.post(
        "/api/v1/ai-assistant/chat",
        data={"page_id": page["id"], "conversation": json.dumps(second)},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert "Comecei a montar o site inteiro" in res.json()["reply"]
    job = db_session.query(SiteImportJob).one()
    assert job.status == "running" and started == [job.id]
    # Nenhuma das duas respostas contou no limite de mensagens do mês.
    assert all(int(row.message_count or 0) == 0 for row in db_session.query(AiAssistantUsage).all())
    roles = [row.role for row in db_session.query(AiAssistantMessage).order_by(AiAssistantMessage.id)]
    assert roles == ["user", "assistant", "user", "assistant"]

    res = client.get(f"/api/v1/ai-assistant/import-jobs/active?agency_id={agency['id']}", headers=headers)
    assert res.status_code == 200
    body = res.json()["job"]
    assert body["status"] == "running" and body["total"] == 4
    assert body["items"][0] == {
        "url": "https://agencia.com.br/viagens/gramado",
        "title": "Gramado",
        "stage": "waiting",
        "page_id": None,
        "slug": None,
        "error": None,
    }
    assert body["home"]["page_id"] == page["id"]


def test_same_link_again_after_question_goes_to_single_page_flow(client, db_session, fake_pipeline, monkeypatch):
    from app.api.v1.endpoints import ai_assistant as endpoint

    monkeypatch.setattr(endpoint, "scrape_page", fake_pipeline)
    monkeypatch.setattr(endpoint, "download_page_images", lambda _page: asyncio.sleep(0, result=[]))
    calls: list[str] = []

    def fake_ai(conversation, attachments, model_override=None, context=""):
        calls.append(context)
        return "Certo! Vou montar a página."

    monkeypatch.setattr(endpoint, "generate_ai_assistant_reply", fake_ai)
    monkeypatch.setattr(endpoint, "get_active_gpt_model", lambda *_a, **_k: "gpt-test")
    headers, _agency_, page = _auth(client, db_session)

    first = [{"role": "user", "content": "Importar informações de: https://agencia.com.br/"}]
    question = client.post(
        "/api/v1/ai-assistant/chat",
        data={"page_id": page["id"], "conversation": json.dumps(first), "import_url": "https://agencia.com.br/"},
        headers=headers,
    ).json()["reply"]
    second = first + [{"role": "assistant", "content": question}, {"role": "user", "content": "Importar informações de: https://agencia.com.br/"}]
    res = client.post(
        "/api/v1/ai-assistant/chat",
        data={"page_id": page["id"], "conversation": json.dumps(second), "import_url": "https://agencia.com.br"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["reply"] == "Certo! Vou montar a página."
    assert calls and "CONTEÚDO EXTRAÍDO DO LINK ENVIADO" in calls[0]
