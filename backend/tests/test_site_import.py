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
from app.models.page_tag import PageTag
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


NOV = "Bate e Volta NOVEMBRO DE 2026"
ESP = "Passeios Especiais"
CATEGORIES_URL = "https://agencia.com.br/categorias"


def _central_page_with_categories() -> ImportedPage:
    # Fora da ordem do site de propósito: a ordem das categorias e dos cards vem de "position".
    links = [
        TripLink(url="https://agencia.com.br/viagens/foz", title="Foz do Iguaçu", price="R$ 1.290", text="Foz", category=ESP, position=2),
        TripLink(url="https://agencia.com.br/viagens/gramado", title="Gramado", price="R$ 1.990", text="Gramado", category=NOV, position=0),
        TripLink(url="https://agencia.com.br/viagens/gramado-2", title="Gramado", price="R$ 2.390", text="Destino: Canela", category=NOV, position=1),
        TripLink(url="https://agencia.com.br/viagens/quebra", title="Quebra", price="", text="Quebra", category=ESP, position=3),
        TripLink(url="https://agencia.com.br/viagens/praia", title="Praia", price="", text="Praia", category=None, position=4),
    ]
    return ImportedPage(title="Agência Exemplo | Viagens", text="As melhores viagens.", image_urls=[], kind="central", trip_links=links)


TRIP_PAGES = {
    "https://agencia.com.br/viagens/gramado": ImportedPage(title="Gramado | Agência Exemplo", text="Destino: Gramado. 5 dias.", image_urls=[]),
    "https://agencia.com.br/viagens/gramado-2": ImportedPage(title="Gramado | Agência Exemplo", text="Destino: Canela. 3 dias.", image_urls=[]),
    "https://agencia.com.br/viagens/foz": ImportedPage(title="Foz do Iguaçu", text="Cataratas.", image_urls=[]),
    "https://agencia.com.br/viagens/praia": ImportedPage(title="Praia do Forte", text="Bahia.", image_urls=[]),
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
        if url.rstrip("/") == CATEGORIES_URL:
            return _central_page_with_categories()
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


def test_publish_all_after_completion(client, db_session, fake_pipeline):
    # Pergunta do aviso global, depois que o job termina: publica de uma vez as viagens prontas
    # (a que deu erro fica de fora, nunca virou página) e a página principal.
    headers, agency, page = _auth(client, db_session)
    home = db_session.get(Page, page["id"])
    user = db_session.query(AgencyUser).filter(AgencyUser.agency_id == agency["id"]).first().user

    job = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", _central_page())
    site_import.start_job(db_session, job)
    asyncio.run(site_import._run(job.id))
    db_session.expire_all()
    job = db_session.get(SiteImportJob, job.id)
    assert job.status == "completed"
    assert [item["stage"] for item in job.items] == ["done", "done", "done", "error"]

    res = client.post(f"/api/v1/ai-assistant/import-jobs/{job.id}/publish-all", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    # As 3 viagens prontas + a home; a que deu erro não ganhou página, não entra na conta.
    assert body == {"published": 4, "already_published": 0, "blocked": 0, "blocked_reason": None}

    db_session.expire_all()
    pages = db_session.query(Page).filter(Page.agency_id == agency["id"]).all()
    assert len(pages) == 4
    assert all(p.status == "published" and p.published_at is not None for p in pages)

    # Rodar de novo não publica nada a mais (já estavam publicadas).
    res = client.post(f"/api/v1/ai-assistant/import-jobs/{job.id}/publish-all", headers=headers)
    assert res.json() == {"published": 0, "already_published": 4, "blocked": 0, "blocked_reason": None}


def test_publish_all_rejects_job_not_completed(client, db_session, fake_pipeline):
    headers, agency, page = _auth(client, db_session)
    home = db_session.get(Page, page["id"])
    user = db_session.query(AgencyUser).filter(AgencyUser.agency_id == agency["id"]).first().user
    job = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", _central_page())

    res = client.post(f"/api/v1/ai-assistant/import-jobs/{job.id}/publish-all", headers=headers)
    assert res.status_code == 409


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


def test_confirmation_sent_as_import_url_still_starts_job(client, db_session, fake_pipeline, monkeypatch):
    # A pessoa respondeu "completo" colando na caixa de link (confusão natural: acabou de usar
    # aquela caixa para o link da home) em vez de digitar na conversa. Isso não pode virar erro de
    # "link inválido": tem que disparar a importação igual à confirmação por texto.
    from app.api.v1.endpoints import ai_assistant as endpoint

    monkeypatch.setattr(endpoint, "scrape_page", fake_pipeline)

    def no_ai(*_args, **_kwargs):
        raise AssertionError("a IA não pode ser chamada nesse fluxo")

    monkeypatch.setattr(endpoint, "generate_ai_assistant_reply", no_ai)
    started: list[int] = []
    monkeypatch.setattr(site_import, "start_job_thread", started.append)
    headers, _agency, page = _auth(client, db_session)

    first = [{"role": "user", "content": "Importar informações de: https://agencia.com.br/"}]
    res = client.post(
        "/api/v1/ai-assistant/chat",
        data={"page_id": page["id"], "conversation": json.dumps(first), "import_url": "https://agencia.com.br/"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    question = res.json()["reply"]

    second = first + [{"role": "assistant", "content": question}, {"role": "user", "content": "Importar informações de: completo"}]
    res = client.post(
        "/api/v1/ai-assistant/chat",
        data={"page_id": page["id"], "conversation": json.dumps(second), "import_url": "completo"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert "Comecei a montar o site inteiro" in res.json()["reply"]
    job = db_session.query(SiteImportJob).one()
    assert job.status == "running" and started == [job.id]


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


# --- Categorias do site: segunda pergunta, tags e home com uma seção por categoria ---


@pytest.mark.parametrize(
    "text",
    ["manter", "Manter!", "sim", "pode manter", "mantém as categorias", "separar", "quero separado por categoria", "não junta não"],
)
def test_categories_answer_keep(text):
    assert site_import.categories_answer(text) is True


@pytest.mark.parametrize(
    "text",
    ["juntar", "Junta tudo", "não", "tudo junto", "uma lista só", "pode juntar", "não precisa separar", "sem categoria"],
)
def test_categories_answer_join(text):
    assert site_import.categories_answer(text) is False


@pytest.mark.parametrize("text", ["", "manter separado mas juntar", "Quero mudar a cor do banner para azul e trocar a foto"])
def test_categories_answer_unknown(text):
    assert site_import.categories_answer(text) is None


def test_categories_question_lists_examples_in_site_order():
    question = site_import.categories_question(["A", "B", "C", "D", "E"])
    assert question.startswith(site_import.CATEGORIES_QUESTION_PREFIX)
    assert '"A", "B", "C" e mais 2 categorias' in question
    assert "'manter'" in question and "'juntar'" in question


def test_job_categories_follow_position_not_list_order(db_session):
    _agency_, user, home = _agency(db_session)
    job = site_import.create_pending_job(db_session, home, user.id, CATEGORIES_URL, _central_page_with_categories())
    assert site_import.job_categories(job) == [NOV, ESP]
    assert job.items[0]["category"] == ESP and job.items[0]["position"] == 2


def test_group_created_by_category_puts_loose_trips_last():
    created = [
        {"page_id": 3, "title": "Foz", "category": ESP, "position": 2},
        {"page_id": 9, "title": "Praia", "category": None, "position": 0},
        {"page_id": 2, "title": "Canela", "category": NOV, "position": 1},
        {"page_id": 1, "title": "Gramado", "category": NOV, "position": 0},
    ]
    groups = site_import.group_created_by_category(created)
    assert [(name, [item["page_id"] for item in items]) for name, items in groups] == [
        (NOV, [1, 2]),
        (ESP, [3]),
        (site_import.UNCATEGORIZED_TITLE, [9]),
    ]
    # Nenhuma página com categoria: nada a agrupar (a home segue com a vitrine única).
    assert site_import.group_created_by_category([{"page_id": 1, "title": "x", "category": None}]) == []


def test_place_category_sections_replaces_showcase_in_place():
    ai_card = {"source": "page", "pageId": 1, "url": "/a/gramado", "title": "Gramado", "description": "Da IA", "priceValue": "R$ 1"}
    sections = [
        {"type": "hero", "anchorId": "banner-1"},
        {"type": "links", "anchorId": "viagens-2", "title": "Nossas viagens", "items": [ai_card]},
        {"type": "story", "anchorId": "sobre-3"},
        {"type": "agency_footer"},
    ]
    groups = [
        (NOV, [{"page_id": 1, "url": "/a/gramado", "title": "Gramado"}, {"page_id": 2, "url": "/a/canela", "title": "Canela", "price": "R$ 2"}]),
        (ESP, [{"page_id": 3, "url": "/a/foz", "title": "Foz"}]),
    ]
    site_import.place_category_sections(sections, groups)
    assert [section["type"] for section in sections] == ["hero", "links", "links", "story", "agency_footer"]
    nov, esp = sections[1], sections[2]
    assert (nov["title"], nov["mode"], nov["anchorId"]) == (NOV, "manual", "bate-e-volta-novembro-de-2026")
    assert nov["items"][0]["description"] == "Da IA"  # card da IA reaproveitado
    assert (nov["items"][1]["pageId"], nov["items"][1]["source"], nov["items"][1]["priceValue"]) == (2, "page", "R$ 2")
    assert esp["title"] == ESP and [card["pageId"] for card in esp["items"]] == [3]

    # Sem vitrine da IA: entram antes do rodapé.
    sections = [{"type": "hero"}, {"type": "agency_footer"}]
    site_import.place_category_sections(sections, groups)
    assert [section.get("title") for section in sections] == [None, NOV, ESP, None]


def _run_categories_job(db_session, preserve, plan="infinity"):
    agency, user, home = _agency(db_session)
    user.plan = plan
    db_session.add(PageTag(agency_id=agency.id, name="Passeios especiais", slug="passeios-especiais", color="rose"))
    db_session.commit()
    job = site_import.create_pending_job(db_session, home, user.id, CATEGORIES_URL, _central_page_with_categories())
    reply = site_import.start_job(db_session, job, preserve_categories=preserve)
    asyncio.run(site_import._run(job.id))
    db_session.expire_all()
    return agency, db_session.get(SiteImportJob, job.id), db_session.get(Page, home.id), reply


def test_full_job_keeping_categories_tags_pages_and_builds_one_section_per_category(db_session, fake_pipeline):
    agency, job, home, reply = _run_categories_job(db_session, True)
    assert "uma seção por categoria" in reply
    assert job.status == "completed" and job.preserve_categories is True
    pages = {page.title: page for page in db_session.query(Page).filter(Page.agency_id == agency.id).all()}

    # Tag nova com o nome exato do site; a que já existia (mesmo slug) é reaproveitada, sem duplicar.
    tags = {tag.slug: tag for tag in db_session.query(PageTag).filter(PageTag.agency_id == agency.id).all()}
    assert set(tags) == {"bate-e-volta-novembro-de-2026", "passeios-especiais"}
    assert tags["bate-e-volta-novembro-de-2026"].name == NOV
    assert [tag.name for tag in pages["Gramado"].tags] == [NOV]
    assert [tag.name for tag in pages["Gramado — Canela"].tags] == [NOV]
    assert [tag.name for tag in pages["Foz do Iguaçu"].tags] == ["Passeios especiais"]
    assert pages["Praia do Forte"].tags == []

    links = [section for section in home.config_json["sections"] if section["type"] == "links"]
    assert [section["title"] for section in links] == [NOV, ESP, site_import.UNCATEGORIZED_TITLE]
    assert [card["pageId"] for card in links[0]["items"]] == [pages["Gramado"].id, pages["Gramado — Canela"].id]
    assert [card["pageId"] for card in links[1]["items"]] == [pages["Foz do Iguaçu"].id]  # "Quebra" deu erro
    assert [card["pageId"] for card in links[2]["items"]] == [pages["Praia do Forte"].id]
    assert all(card["source"] == "page" and "pageSlug" not in card for section in links for card in section["items"])
    # As seções entram onde a vitrine da IA estava (logo depois do banner).
    types = [section["type"] for section in home.config_json["sections"]]
    assert types.index("links") == 1


def test_full_job_joining_categories_keeps_single_showcase_and_no_tags(db_session, fake_pipeline):
    agency, job, home, _reply = _run_categories_job(db_session, False)
    assert job.status == "completed" and job.preserve_categories is False
    assert db_session.query(PageTag).filter(PageTag.agency_id == agency.id).count() == 1  # só a que já existia
    links = [section for section in home.config_json["sections"] if section["type"] == "links"]
    assert [section["title"] for section in links] == ["Nossas viagens"]


def test_categories_fall_back_to_single_showcase_when_plan_section_limit_is_hit(db_session, fake_pipeline, monkeypatch):
    # O plano limita as seções por página (free: 4). Se banner + uma seção por categoria não cabe,
    # a home fica com a vitrine única de sempre em vez de falhar. Limite de 2 para forçar o caso.
    monkeypatch.setattr("app.services.plans.plan_limits", lambda _plan: (None, 2))
    agency, job, home, _reply = _run_categories_job(db_session, True)
    assert job.status == "completed"
    links = [section for section in home.config_json["sections"] if section["type"] == "links"]
    assert [section["title"] for section in links] == ["Nossas viagens"]
    # A tag continua ligada às páginas (independe de caber na home).
    assert db_session.query(PageTag).filter(PageTag.agency_id == agency.id).count() == 2


def _chat(client, headers, page_id, conversation, import_url=None):
    data = {"page_id": page_id, "conversation": json.dumps(conversation)}
    if import_url:
        data["import_url"] = import_url
    res = client.post("/api/v1/ai-assistant/chat", data=data, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()["reply"]


@pytest.mark.parametrize(("answer", "preserve"), [("manter", True), ("juntar", False)])
def test_chat_asks_categories_after_full_confirmation(client, db_session, fake_pipeline, monkeypatch, answer, preserve):
    from app.api.v1.endpoints import ai_assistant as endpoint

    monkeypatch.setattr(endpoint, "scrape_page", fake_pipeline)

    def no_ai(*_args, **_kwargs):
        raise AssertionError("a IA não pode ser chamada nesse fluxo")

    monkeypatch.setattr(endpoint, "generate_ai_assistant_reply", no_ai)
    started: list[int] = []
    monkeypatch.setattr(site_import, "start_job_thread", started.append)
    headers, _agency, page = _auth(client, db_session)

    conversation = [{"role": "user", "content": f"Importar informações de: {CATEGORIES_URL}"}]
    question = _chat(client, headers, page["id"], conversation, CATEGORIES_URL)
    # A primeira pergunta continua sendo só a de site completo/específico.
    assert question.startswith(site_import.CENTRAL_QUESTION_PREFIX) and "categoria" not in question

    conversation += [{"role": "assistant", "content": question}, {"role": "user", "content": "completo"}]
    second = _chat(client, headers, page["id"], conversation)
    assert second.startswith(site_import.CATEGORIES_QUESTION_PREFIX)
    assert f'"{NOV}", "{ESP}"' in second  # na ordem do site
    job = db_session.query(SiteImportJob).one()
    assert job.status == "awaiting_categories" and started == []

    conversation += [{"role": "assistant", "content": second}, {"role": "user", "content": answer}]
    third = _chat(client, headers, page["id"], conversation)
    assert "Comecei a montar o site inteiro" in third
    db_session.expire_all()
    job = db_session.query(SiteImportJob).one()
    assert job.status == "running" and job.preserve_categories is preserve and started == [job.id]
    # Nenhuma das três respostas contou no limite de mensagens do mês.
    assert all(int(row.message_count or 0) == 0 for row in db_session.query(AiAssistantUsage).all())


def test_categories_answer_sent_as_import_url_still_starts_job(client, db_session, fake_pipeline, monkeypatch):
    from app.api.v1.endpoints import ai_assistant as endpoint

    monkeypatch.setattr(endpoint, "scrape_page", fake_pipeline)
    monkeypatch.setattr(endpoint, "generate_ai_assistant_reply", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError()))
    started: list[int] = []
    monkeypatch.setattr(site_import, "start_job_thread", started.append)
    headers, _agency, page = _auth(client, db_session)

    conversation = [{"role": "user", "content": f"Importar informações de: {CATEGORIES_URL}"}]
    question = _chat(client, headers, page["id"], conversation, CATEGORIES_URL)
    conversation += [{"role": "assistant", "content": question}, {"role": "user", "content": "Importar informações de: completo"}]
    second = _chat(client, headers, page["id"], conversation, "completo")
    assert second.startswith(site_import.CATEGORIES_QUESTION_PREFIX)
    conversation += [{"role": "assistant", "content": second}, {"role": "user", "content": "Importar informações de: manter"}]
    assert "Comecei a montar o site inteiro" in _chat(client, headers, page["id"], conversation, "manter")
    db_session.expire_all()
    assert db_session.query(SiteImportJob).one().preserve_categories is True


def test_single_category_does_not_ask(db_session, fake_pipeline):
    # Um título só em cima de todos os cards ("Próximas saídas") não é separação: segue direto.
    _agency_, user, home = _agency(db_session)
    imported = _central_page()
    for link in imported.trip_links:
        link.category = "Próximas saídas"
    job = site_import.create_pending_job(db_session, home, user.id, "https://agencia.com.br/", imported)
    reply = site_import.confirm_full_import(db_session, job)
    assert "Comecei a montar o site inteiro" in reply
    assert job.status == "running" and job.preserve_categories is None
