"""Fotos do assistente de IA: a IA escolhe entre as candidatas, a troca não devolve a foto que já
está na página, a troca muda só o que foi pedido e o menu entende os itens atuais."""
from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.stock_image import StockImage
from app.services import photo_choice, stock_images
from app.services.ai_assistant import build_page_base_config_from_reply
from app.services.ai_assistant_context import _sections_summary


def reply_with(*blocks: str) -> str:
    return "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n" + "\n\n".join(blocks)


def _photo_db(monkeypatch):
    engine = create_engine("sqlite://")
    StockImage.__table__.create(engine)
    db = sessionmaker(bind=engine)()
    calls: list[str] = []

    def fake_pixabay(client, key, query, record=None):
        calls.append(query)
        if "nada" in query:
            return []
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
    # Sem download de verdade nem pedido de buscas novas à IA (testados à parte).
    monkeypatch.setattr(stock_images, "prepare_download", lambda client, url: None)
    monkeypatch.setattr(stock_images, "refine_queries", lambda db, slots, *, timeout: {})
    db.calls = calls
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


def test_swap_with_old_photo_field_name_still_asks_for_a_new_photo():
    # O formato antigo chamava o campo de "Sugestão de imagem": numa troca ele também pede foto nova.
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nSubstitui: banner\nSugestão de imagem: Jalapão dunas Tocantins Brazil"
    ))
    hero = config["sections"][0]
    assert hero["aiImageQuery"] == "Jalapão dunas Tocantins Brazil"
    assert hero["aiSetKeys"] == []


def test_swap_gets_a_new_photo_even_when_the_ai_refuses_every_candidate(monkeypatch):
    db = _photo_db(monkeypatch)
    monkeypatch.setattr(stock_images, "choose_photos", lambda db, client, slots, *, timeout: {slot.key: [] for slot in slots})
    swap, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nSubstitui: banner\nBusca de imagem: Gramado Brazil"
    ))
    stock_images.fill_section_photos(db, swap["sections"], exclude_urls=["/uploads/antiga.webp"])
    hero = swap["sections"][0]
    # O usuário pediu outra foto: sai a melhor do ranking em vez de ficar tudo igual.
    assert hero["aiStockPhoto"] is True
    assert hero["backgroundImage"].startswith("/uploads/Gramado Brazil-")


def test_itinerary_photo_swap_puts_one_new_photo_per_day(monkeypatch):
    from app.api.v1.endpoints.ai_assistant import _photo_days_for_itinerary_swaps

    db = _photo_db(monkeypatch)
    monkeypatch.setattr(stock_images, "choose_photos", lambda *args, **kwargs: None)
    swap, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: ROTEIRO DIA A DIA\nSubstitui: roteiro-3\nBusca de imagem: Gramado Brazil"
    ))
    _photo_days_for_itinerary_swaps(swap["sections"], {"roteiro-3": 3, "outro": 5})
    stock_images.fill_section_photos(db, swap["sections"])
    itinerary = swap["sections"][0]
    assert itinerary["aiStockPhoto"] is True
    assert len(itinerary["days"]) == 3
    assert all(day["image"].startswith("/uploads/") for day in itinerary["days"])
    assert len({day["image"] for day in itinerary["days"]}) == 3
    assert itinerary["aiSetKeys"] == []


def test_refused_photos_get_new_searches_from_the_ai(monkeypatch):
    db = _photo_db(monkeypatch)
    rounds = []
    asked = []

    def fake_choice(db, client, slots, *, timeout):
        rounds.append([slot.key for slot in slots])
        if len(rounds) == 1:
            return {slot.key: [] for slot in slots}  # nenhuma mostra o hotel
        [story] = slots
        return {story.key: story.candidates[:2]}

    def fake_refine(db, slots, *, timeout):
        asked.extend((slot.key, list(slot.tried), [image.provider_id for image in slot.rejected]) for slot in slots)
        return {slot.key: ["Gramado boutique hotel lobby", "Gramado Brazil hotel"] for slot in slots if slot.rejected}

    monkeypatch.setattr(stock_images, "choose_photos", fake_choice)
    monkeypatch.setattr(stock_images, "refine_queries", fake_refine)
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: TEXTO E IMAGENS\nTítulo: Hotel\nTexto: Hotel no centro.\nBusca de imagem: Gramado hotel Brazil",
    ))
    [story] = config["sections"]
    stock_images.fill_section_photos(db, config["sections"])
    # A IA recusou todas: pediu buscas novas contando o que já tinha buscado e recusado.
    key, tried, rejected = asked[-1]
    assert tried == ["Gramado hotel Brazil"] and len(rejected) == 4 and all(pid.startswith("Gramado hotel Brazil") for pid in rejected)
    # Destino brasileiro: a busca nova também ganha "Brazil".
    assert "Gramado boutique hotel lobby Brazil" in db.calls and rounds == [["V1"], ["V1"]]
    # A segunda escolha valeu (as duas da busca nova) e o carrossel completou com o ranking delas.
    assert story["images"][:2] == [
        "/uploads/Gramado boutique hotel lobby Brazil-0.webp", "/uploads/Gramado boutique hotel lobby Brazil-1.webp",
    ]
    assert story["aiStockPhoto"] is True and len(story["images"]) == 3


def test_slot_without_results_asks_the_ai_for_broader_searches(monkeypatch):
    db = _photo_db(monkeypatch)
    monkeypatch.setattr(stock_images, "choose_photos", lambda *args, **kwargs: None)
    asked = []

    def fake_refine(db, slots, *, timeout):
        asked.extend(slot.key for slot in slots)
        return {slot.key: ["Snowland indoor snow park", "Gramado snow"] for slot in slots}

    monkeypatch.setattr(stock_images, "refine_queries", fake_refine)
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nTítulo: Snowland\nBusca de imagem: nada Snowland Gramado",
    ))
    stock_images.fill_section_photos(db, config["sections"])
    hero = config["sections"][0]
    # A busca da IA não achou nada: a IA sugeriu buscas novas (destino brasileiro ganha "Brazil").
    assert asked == ["V1"] and "Gramado snow Brazil" in db.calls
    assert hero["backgroundImage"] == "/uploads/Snowland indoor snow park-0.webp"


def test_same_search_in_two_sections_goes_once_to_the_bank_and_never_comes_from_storage(monkeypatch):
    db = _photo_db(monkeypatch)
    monkeypatch.setattr(stock_images, "choose_photos", lambda *args, **kwargs: None)
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nTítulo: Gramado\nBusca de imagem: Gramado Brazil",
        "🟩 SEÇÃO: FOTO EM DESTAQUE\nBusca de imagem: Gramado Brazil",
    ))
    stock_images.fill_section_photos(db, config["sections"])
    assert db.calls.count("Gramado Brazil") == 1
    # Na próxima página a mesma busca vai ao banco de novo (não há busca guardada).
    stock_images.search_stock_images(db, None, "Gramado Brazil")
    assert db.calls.count("Gramado Brazil") == 2


def test_refine_queries_reads_the_answer_and_skips_repeated_searches(monkeypatch):
    slot = photo_choice.PhotoSlot(key="V1", context="Banner Inicial · busca: Snowland", count=1)
    slot.tried = ["Snowland Gramado Brazil"]
    sent = {}

    class FakeResponses:
        def create(self, **kwargs):
            sent.update(kwargs)
            return SimpleNamespace(output_text='{"V1": ["snowland gramado brazil", "Snowland indoor ski slope", "family snow park", "x", "y"]}')

    import openai

    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: SimpleNamespace(responses=FakeResponses()))
    monkeypatch.setattr(photo_choice, "get_settings", lambda: SimpleNamespace(gpt_key="k"))
    from app.services import construtor_prompt

    monkeypatch.setattr(construtor_prompt, "get_active_gpt_model", lambda db, create_if_missing=False: "gpt-4o-mini")
    suggestions = photo_choice.refine_queries(None, [slot], timeout=5)
    # A busca já feita não volta, e no máximo 3 por vaga.
    assert suggestions == {"V1": ["Snowland indoor ski slope", "family snow park", "x"]}
    assert "Buscas feitas: Snowland Gramado Brazil" in sent["input"] and "nenhuma foto encontrada" in sent["input"]
