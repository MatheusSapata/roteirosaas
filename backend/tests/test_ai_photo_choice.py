"""Fotos do assistente de IA: a IA escolhe entre as candidatas, a troca não devolve a foto que já
está na página, a troca muda só o que foi pedido e o menu entende os itens atuais."""
from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.stock_image import StockImage, StockImageSearch
from app.services import photo_choice, stock_images
from app.services.ai_assistant import build_page_base_config_from_reply
from app.services.ai_assistant_context import _sections_summary


def reply_with(*blocks: str) -> str:
    return "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n" + "\n\n".join(blocks)


def _photo_db(monkeypatch):
    engine = create_engine("sqlite://")
    StockImage.__table__.create(engine)
    StockImageSearch.__table__.create(engine)
    db = sessionmaker(bind=engine)()

    def fake_pixabay(client, key, query, record=None):
        return [
            {"provider": "pixabay", "provider_id": f"{query}-{n}", "download_url": f"https://img/{query}/{n}.jpg",
             "preview_url": f"https://img/{query}/{n}_640.jpg", "page_url": "p", "photographer": "Ana",
             "photographer_url": "u", "alt": f"{query} {n}", "width": 10, "height": 6}
            for n in range(4)
        ]

    monkeypatch.setattr(stock_images, "_search_pixabay", fake_pixabay)
    monkeypatch.setattr(stock_images, "materialize", lambda db, client, image: f"/uploads/{image.provider_id}.webp")
    key = stock_images.ImageKey(provider="pixabay", plain_key="k")
    monkeypatch.setattr(stock_images, "available_image_keys", lambda db, provider: [key] if provider == "pixabay" else [])
    monkeypatch.setattr(stock_images, "has_any_image_key", lambda db: True)
    return db


def test_ai_choice_decides_the_photo_and_can_refuse(monkeypatch):
    db = _photo_db(monkeypatch)
    seen_slots = []

    def fake_choice(db, client, slots, *, timeout):
        seen_slots.extend(slots)
        hero, story = slots
        # Banner: a IA prefere a terceira candidata. Texto e Imagens: nenhuma serve.
        return {hero.key: [hero.candidates[2]], story.key: []}

    monkeypatch.setattr(stock_images, "choose_photos", fake_choice)
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nTítulo: Gramado no inverno\nBusca de imagem: Gramado Rua Coberta Brazil | couple winter",
        "🟩 SEÇÃO: TEXTO E IMAGENS\nTítulo: Hotel\nTexto: Hotel no centro.\nBusca de imagem: Gramado hotel Brazil",
    ))
    hero, story = config["sections"]
    stock_images.fill_section_photos(db, config["sections"])
    # A IA viu o contexto da seção, e as candidatas da primeira busca vêm antes das da segunda.
    assert "Banner Inicial" in seen_slots[0].context and 'título "Gramado no inverno"' in seen_slots[0].context
    assert seen_slots[0].candidates[0].provider_id == "Gramado Rua Coberta Brazil-0"
    assert any(image.provider_id.startswith("couple winter") for image in seen_slots[0].candidates)
    assert hero["backgroundImage"] == "/uploads/Gramado Rua Coberta Brazil-2.webp" and hero["aiStockPhoto"] is True
    # Nenhuma serviu: a seção fica sem foto de banco (com a imagem provisória), em vez de uma foto errada.
    assert "aiStockPhoto" not in story and story["images"][0].startswith("data:image/svg+xml")
    # O carrossel do Texto e Imagens pede 3 fotos.
    assert seen_slots[1].count == 3


def test_swap_does_not_return_the_photo_already_on_the_page(monkeypatch):
    db = _photo_db(monkeypatch)
    monkeypatch.setattr(stock_images, "choose_photos", lambda *args, **kwargs: None)
    first, _ = build_page_base_config_from_reply(reply_with("🟩 SEÇÃO: BANNER INICIAL\nTítulo: Gramado\nBusca de imagem: Gramado Brazil"))
    stock_images.fill_section_photos(db, first["sections"])
    current = first["sections"][0]["backgroundImage"]
    db.query(StockImage).filter(StockImage.provider_id == "Gramado Brazil-0").update({"stored_url": current})
    swap, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nSubstitui: banner\nBusca de imagem: Gramado Brazil"
    ))
    stock_images.fill_section_photos(db, swap["sections"], exclude_urls=[current])
    assert swap["sections"][0]["backgroundImage"] not in (current, None)


def test_images_switched_off_or_photo_only_swap_keeps_the_texts(monkeypatch):
    # Troca só da foto: a resposta não traz título nem texto, então nada disso muda na página.
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: ROTEIRO DIA A DIA\nSubstitui: roteiro-3\nBusca de imagem: Gramado Brazil",
        "🟩 SEÇÃO: BANNER INICIAL\nSubstitui: banner\nTítulo: Novo título\nBusca de imagem: Gramado",
    ))
    itinerary, hero = config["sections"]
    assert itinerary["aiSetKeys"] == [] and itinerary["aiReplaces"] == "roteiro-3"
    assert hero["aiSetKeys"] == ["title"]
    # Seção nova (sem "Substitui"): sem marcação, entra inteira.
    new, _ = build_page_base_config_from_reply(reply_with("🟩 SEÇÃO: BANNER INICIAL\nTítulo: Outro"))
    assert "aiSetKeys" not in new["sections"][0]
    # "Inserir imagens" desligado: as buscas somem e nenhuma foto é colocada.
    stock_images.clear_photo_queries(config["sections"])
    assert all("aiImageQuery" not in section for section in config["sections"])


def test_menu_reads_links_alias_sticky_and_current_items_in_context():
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: MENU DO TOPO\nSubstitui: menu-1\nLinks:\n- Roteiro → roteiro-3\n- Preços → precos-4\nFixo ao rolar: normal"
    ))
    header = config["sections"][0]
    assert [link["target"] for link in header["links"]] == ["roteiro-3", "precos-4"]
    assert header["stickyEnabled"] is True and {"links", "stickyEnabled"} <= set(header["aiSetKeys"])
    loose, _ = build_page_base_config_from_reply(reply_with("🟩 SEÇÃO: MENU DO TOPO\nSubstitui: menu-1\nFixo ao rolar: não fixar"))
    assert loose["sections"][0]["stickyEnabled"] is False
    # A IA recebe o menu como está (itens, aparência, lado direito) para mexer só no pedido.
    [line] = _sections_summary([{
        "type": "header", "anchorId": "menu-1", "mode": "transparent", "stickyEnabled": True, "actionType": "contact",
        "contactLabel": "Reservar", "links": [{"label": "Roteiro", "target": "roteiro-3"}, {"label": "Blog", "target": ""}],
    }])
    assert line == '1. menu-1: Menu do topo · aparência transparente · fixo ao rolar · lado direito: botão "Reservar" · itens: Roteiro → roteiro-3; Blog'


def test_context_says_when_images_are_switched_off(db_session):
    from app.models.agency import Agency
    from app.models.page import Page
    from app.services.ai_assistant_context import build_agency_context

    agency = Agency(name="Viaje", slug="viaje")
    db_session.add(agency)
    db_session.flush()
    page = Page(agency_id=agency.id, title="Gramado", slug="gramado", config_json={"sections": []})
    db_session.add(page)
    db_session.flush()
    assert "DESLIGADAS" in build_agency_context(db_session, page, [], include_images=False)
    assert "DESLIGADAS" not in build_agency_context(db_session, page, [])


def test_photo_choice_sends_thumbnails_and_reads_the_answer(monkeypatch):
    images = [StockImage(id=n, provider="pexels", provider_id=str(n), download_url="d", alt=f"foto {n}",
                         preview_url=f"https://img.test/{n}.jpg", width=10, height=6) for n in range(1, 4)]
    slot = photo_choice.PhotoSlot(key="V1", context="Banner Inicial · busca: Gramado", count=1, candidates=images)
    requests = []

    class FakeResponses:
        def create(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(output_text='Aqui: {"V1": ["V1-3", "V9-1", "V1-1"]}')

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(photo_choice, "get_settings", lambda: SimpleNamespace(gpt_key="k"))
    monkeypatch.setattr("app.services.construtor_prompt.get_active_gpt_model", lambda db, create_if_missing=True: "gpt-4.1")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"jpg", headers={"content-type": "image/jpeg"})
        if not request.url.path.endswith("2.jpg") else httpx.Response(404)
    )
    with httpx.Client(transport=transport) as client:
        chosen = photo_choice.choose_photos(None, client, [slot], timeout=10)
    # Só códigos da própria vaga, na ordem da IA.
    assert [image.id for image in chosen["V1"]] == [3, 1]
    content = requests[0]["input"][0]["content"]
    pictures = [part for part in content if part["type"] == "input_image"]
    # A miniatura que não abriu vai só com a descrição.
    assert len(pictures) == 2 and pictures[0]["image_url"].startswith("data:image/jpeg;base64,")
    assert any(part.get("text", "").startswith("V1-2: foto 2") for part in content)
    assert "Responda só com JSON" in requests[0]["instructions"]
    # Sem chave da IA: não pergunta (vale o ranking).
    monkeypatch.setattr(photo_choice, "get_settings", lambda: SimpleNamespace(gpt_key=None))
    assert photo_choice.choose_photos(None, None, [slot], timeout=10) is None
