"""Fotos de um PDF enviado ao assistente e fotos das outras páginas da agência: ficam só na agência
(nunca no banco comum de fotos), o chat avisa que foram extraídas, a busca usa as fotos dela antes
dos bancos e o assistente aprende o tom e a história da agência pelas outras páginas."""
from __future__ import annotations

import io
from functools import partial

import anyio
from PIL import Image

from app.api.v1.endpoints import ai_assistant as endpoint
from app.models.agency import Agency
from app.models.media import MediaAsset
from app.models.page import Page
from app.models.stock_image import StockImage
from app.services import pdf_photos, stock_images
from app.services.agency_photos import load_agency_photos, mark_pdf_photos
from app.services.ai_assistant import ChatAttachment, build_page_base_config_from_reply
from app.services.ai_assistant_context import build_agency_context

PAGE_TEXT = "Dia 2: Fervedouros do Jalapão, banho nas águas cristalinas e trilha leve até a cachoeira."


def _pdf(*sizes: tuple[int, int]) -> bytes:
    pages = [Image.new("RGB", size, (30 + index * 40, 120, 200)) for index, size in enumerate(sizes)]
    buffer = io.BytesIO()
    pages[0].save(buffer, "PDF", save_all=True, append_images=pages[1:])
    return buffer.getvalue()


def _agency(db, name: str, slug: str) -> Agency:
    agency = Agency(name=name, slug=slug)
    db.add(agency)
    db.flush()
    return agency


def _page(db, agency: Agency, title: str, slug: str, sections: list[dict]) -> Page:
    page = Page(agency_id=agency.id, title=title, slug=slug, status="published", config_json={"sections": sections})
    db.add(page)
    db.flush()
    return page


def test_pdf_photos_skip_small_images_and_scanned_pages(monkeypatch):
    data = _pdf((1600, 1000), (64, 64), (1200, 1500))
    # Página escaneada (imagem do tamanho da página, sem texto de verdade): nada sai.
    assert pdf_photos.extract_pdf_photos(data) == []

    monkeypatch.setattr(pdf_photos, "_page_text", lambda page, limit=600: PAGE_TEXT)
    photos = pdf_photos.extract_pdf_photos(data)
    assert [(photo.page, photo.orientation) for photo in photos] == [(1, "horizontal"), (3, "vertical")]  # ícone fica de fora
    assert photos[0].content_type == "image/jpeg" and photos[0].page_text == PAGE_TEXT
    # Passando do limite, ficam as maiores (na ordem das páginas).
    assert [photo.page for photo in pdf_photos.extract_pdf_photos(data, limit=1)] == [3]
    assert pdf_photos.extract_pdf_photos(b"isto nao e um pdf") == []
    assert pdf_photos.is_pdf(None, "Roteiro.PDF") and not pdf_photos.is_pdf("image/png", "foto.png")


def test_pdf_photos_go_only_to_the_agency_library_and_the_chat_warns(db_session, monkeypatch):
    agency = _agency(db_session, "Rota Sul", "rotasul")
    stored: list[str] = []

    def fake_save(data, filename, content_type=None):
        stored.append(filename)
        return f"/uploads/pdf-{len(stored)}.jpg"

    monkeypatch.setattr(pdf_photos, "_page_text", lambda page, limit=600: PAGE_TEXT)
    monkeypatch.setattr(endpoint, "optimize_image", lambda data: None)
    monkeypatch.setattr(endpoint.media_storage, "save", fake_save)
    attachments = [
        ChatAttachment(filename="Jalapão folheto.pdf", content_type="application/pdf", data=_pdf((1600, 1000), (1200, 1500))),
        ChatAttachment(filename="foto.jpg", content_type="image/jpeg", data=b"x"),
    ]
    saved, notice = anyio.run(partial(endpoint._save_pdf_photos, db_session, agency.id, attachments))

    assert [url for _, url in saved] == ["/uploads/pdf-1.jpg", "/uploads/pdf-2.jpg"]
    assert saved[0][0].startswith('Jalapão folheto.pdf, página 1 ("Dia 2: Fervedouros')
    assert "Extraí 2 fotos" in notice and "sem compartilhar com outros clientes" in notice
    assert "responsabilidade" in notice and "rodapé" in notice
    rows = db_session.query(MediaAsset).all()
    assert {(row.agency_id, row.source) for row in rows} == {(agency.id, "pdf")}
    assert "fervedouros" in rows[0].keywords.lower()
    # Nada no banco comum de fotos (o que serve a todos os clientes).
    assert db_session.query(StockImage).count() == 0

    # O mesmo PDF de novo: as fotos já guardadas são reaproveitadas, sem cópias na biblioteca.
    again, _ = anyio.run(partial(endpoint._save_pdf_photos, db_session, agency.id, attachments))
    assert [url for _, url in again] == ["/uploads/pdf-1.jpg", "/uploads/pdf-2.jpg"]
    assert db_session.query(MediaAsset).count() == 2 and len(stored) == 2

    monkeypatch.setattr(pdf_photos, "_page_text", lambda page, limit=600: "")
    scanned = [ChatAttachment(filename="escaneado.pdf", content_type="application/pdf", data=_pdf((1240, 1754)))]
    saved, notice = anyio.run(partial(endpoint._save_pdf_photos, db_session, agency.id, scanned))
    assert saved == [] and notice.startswith("Não encontrei fotos")
    assert anyio.run(partial(endpoint._save_pdf_photos, db_session, agency.id, attachments[1:])) == ([], "")


def _jalapao_sections() -> list[dict]:
    return [
        {"type": "hero", "title": "Jalapão 6 dias", "backgroundImage": "/uploads/jala-hero.webp",
         "photoCredits": [{"url": "/uploads/jala-hero.webp", "name": "Ana", "provider": "Unsplash"}]},
        {"type": "itinerary", "title": "Roteiro", "days": [
            {"title": "Dunas ao pôr do sol", "image": "/uploads/dunas.webp"},
            {"title": "Fervedouros", "description": "Banho nos fervedouros", "image": "/uploads/ferv.webp"},
        ]},
    ]


def test_agency_photos_match_the_destination_and_stay_inside_the_agency(db_session):
    agency = _agency(db_session, "Rota Sul", "rotasul")
    other_agency = _agency(db_session, "Outra", "outra")
    current = _page(db_session, agency, "Jalapão 8 dias", "jalapao-8", [{"type": "hero", "backgroundImage": "/uploads/atual.webp"}])
    _page(db_session, agency, "Jalapão 6 dias", "jalapao-6", _jalapao_sections())
    _page(db_session, agency, "Bonito em família", "bonito", [
        {"type": "story", "title": "Cachoeiras", "images": ["/uploads/bonito-cachoeira.webp"]},
    ])
    # Card da vitrine em outra página, com a mesma foto do Jalapão: a origem é a página do Jalapão.
    _page(db_session, agency, "Chile e vinícolas", "chile", [
        {"type": "links", "items": [{"title": "Jalapão 6 dias", "image": "/uploads/jala-hero.webp"}]},
    ])
    _page(db_session, agency, "Praias do Nordeste", "nordeste", [{"type": "hero", "backgroundImage": "/uploads/nordeste.webp"}])
    _page(db_session, agency, "Rota Sul em Gramado", "gramado", [{"type": "hero", "backgroundImage": "/uploads/gramado.webp"}])
    _page(db_session, other_agency, "Jalapão da concorrência", "jalapao-x", [
        {"type": "hero", "backgroundImage": "/uploads/de-outra-agencia.webp"},
    ])
    db_session.add(MediaAsset(agency_id=agency.id, url="/uploads/pdf-1.jpg", type="image", source="pdf",
                              original_file_name="folheto-jalapao - página 2 - foto 1", keywords=f"folheto-jalapao {PAGE_TEXT}"))
    db_session.flush()

    agency_photos = load_agency_photos(db_session, agency.id, exclude_page_id=current.id)
    urls = {photo.url for photo in agency_photos.photos}
    assert "/uploads/de-outra-agencia.webp" not in urls and "/uploads/atual.webp" not in urls

    found = agency_photos.match("Roteiro dia a dia · dias: Fervedouros · busca: Jalapao waterfall", limit=5)
    assert found[0].url in {"/uploads/ferv.webp", "/uploads/pdf-1.jpg"}
    assert {photo.url for photo in found} >= {"/uploads/ferv.webp", "/uploads/pdf-1.jpg", "/uploads/jala-hero.webp"}
    assert "/uploads/bonito-cachoeira.webp" not in {photo.url for photo in found}  # cachoeira de outro destino
    hero = next(photo for photo in found if photo.url == "/uploads/jala-hero.webp")
    assert hero.origin == 'página "Jalapão 6 dias"' and hero.credit["name"] == "Ana"
    assert next(photo for photo in found if photo.url == "/uploads/pdf-1.jpg").origin == 'PDF "folheto-jalapao"'
    assert agency_photos.match("Roteiro dia a dia · dias: cachoeira · busca: Chapada waterfall") == []
    assert agency_photos.match('Banner Inicial · título "Rota Sul em Paris"') == []  # o nome da agência não é destino
    # Plural: "Praias do Nordeste" serve para uma praia do Nordeste.
    assert [photo.url for photo in agency_photos.match('Banner Inicial · título "Praia no Nordeste"')] == ["/uploads/nordeste.webp"]


def _fake_banks(monkeypatch) -> None:
    def fake_pixabay(client, key, query, record=None):
        return [{"provider": "pixabay", "provider_id": f"{query}-{n}", "download_url": f"https://img/{n}.jpg",
                 "preview_url": f"https://img/{n}_640.jpg", "page_url": "p", "photographer": "Bia",
                 "photographer_url": "u", "alt": f"{query} {n}", "width": 10, "height": 6} for n in range(3)]

    monkeypatch.setattr(stock_images, "_search_pixabay", fake_pixabay)
    monkeypatch.setattr(stock_images, "prepare_download", lambda client, url: None)
    monkeypatch.setattr(stock_images, "materialize", lambda db, client, image: f"/uploads/{image.provider_id}.webp")
    key = stock_images.ImageKey(provider="pixabay", plain_key="k")
    monkeypatch.setattr(stock_images, "available_image_keys", lambda db, provider: [key] if provider == "pixabay" else [])
    monkeypatch.setattr(stock_images, "has_any_image_key", lambda db: True)
    monkeypatch.setattr(stock_images, "active_providers", lambda db: {"manual", "pixabay"})
    monkeypatch.setattr(stock_images, "refine_queries", lambda db, slots, *, timeout: {})


def test_photo_already_in_the_answer_is_not_repeated_in_other_sections(db_session, monkeypatch):
    agency = _agency(db_session, "Rota Sul", "rotasul")
    current = _page(db_session, agency, "Jalapão 8 dias", "jalapao-8", [])
    _page(db_session, agency, "Jalapão 6 dias", "jalapao-6", _jalapao_sections())
    _fake_banks(monkeypatch)
    monkeypatch.setattr(stock_images, "choose_photos", lambda db, client, slots, *, timeout: None)
    config, _ = build_page_base_config_from_reply(
        "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n🟩 SEÇÃO: BANNER INICIAL\nTítulo: Jalapão 8 dias\nImagem: /uploads/dunas.webp\n\n"
        "🟩 SEÇÃO: ROTEIRO DIA A DIA\nTítulo: Roteiro\nDia 1: Dunas\nPôr do sol.\nDia 2: Fervedouros\nBanho.\n"
        "Busca de imagem: Jalapao Brazil"
    )
    stock_images.fill_section_photos(db_session, config["sections"], agency.id, exclude_page_id=current.id)
    hero = next(section for section in config["sections"] if section["type"] == "hero")
    days = next(section for section in config["sections"] if section["type"] == "itinerary")["days"]
    assert hero["backgroundImage"] == "/uploads/dunas.webp"
    assert all(day.get("image") and day["image"] != "/uploads/dunas.webp" for day in days)


def test_section_gets_the_agency_photo_first_with_its_credit_and_origin(db_session, monkeypatch):
    agency = _agency(db_session, "Rota Sul", "rotasul")
    current = _page(db_session, agency, "Jalapão 8 dias", "jalapao-8", [])
    _page(db_session, agency, "Jalapão 6 dias", "jalapao-6", _jalapao_sections())

    _fake_banks(monkeypatch)
    seen: list[list[str]] = []

    def fake_choice(db, client, slots, *, timeout):
        seen.extend([image.provider for image in slot.candidates] for slot in slots)
        return None  # sem a IA: vale a ordem das candidatas

    monkeypatch.setattr(stock_images, "choose_photos", fake_choice)
    config, _ = build_page_base_config_from_reply(
        "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n🟩 SEÇÃO: BANNER INICIAL\nTítulo: Jalapão 8 dias\nBusca de imagem: Jalapao dunes Brazil"
    )
    hero = next(section for section in config["sections"] if section["type"] == "hero")
    stock_images.fill_section_photos(db_session, config["sections"], agency.id, exclude_page_id=current.id)

    assert seen[0][0] == "agencia" and "pixabay" in seen[0]  # as da agência vêm antes das dos bancos
    assert hero["backgroundImage"] in {"/uploads/jala-hero.webp", "/uploads/dunas.webp"}
    assert hero["aiPhotoOrigins"] == {hero["backgroundImage"]: 'página "Jalapão 6 dias"'}
    if hero["backgroundImage"] == "/uploads/jala-hero.webp":
        assert hero["photoCredits"][0]["name"] == "Ana"  # o crédito do banco segue com a foto
    # A foto da agência não vira registro do banco comum.
    assert db_session.query(StockImage).filter(StockImage.stored_url == hero["backgroundImage"]).count() == 0


def test_assistant_learns_the_agency_tone_and_history_from_other_pages(db_session):
    agency = _agency(db_session, "Rota Sul Viagens", "rotasul")
    current = _page(db_session, agency, "Nova viagem", "nova", [])
    _page(db_session, agency, "Jalapão 6 dias", "jalapao-6", [
        {"type": "hero", "title": "Bora pro Jalapão? 🌵", "subtitle": "A gente cuida de tudo, você só aproveita."},
        {"type": "story", "title": "Sobre a viagem", "subtitle": "Seis dias no coração do Tocantins."},
        {"type": "biography", "title": "Quem somos", "text": "<p>Desde 2009 levamos grupos pequenos pelo Brasil.</p>"},
        {"type": "cta", "label": "Partiu?", "description": "Chama no WhatsApp e garanta sua vaga."},
    ])
    context = build_agency_context(db_session, current, [])
    assert "COMO A AGÊNCIA ESCREVE" in context
    assert '"Bora pro Jalapão? 🌵 — A gente cuida de tudo, você só aproveita."' in context
    assert '"Partiu? — Chama no WhatsApp e garanta sua vaga."' in context
    assert "HISTÓRIA DA AGÊNCIA" in context and "Desde 2009 levamos grupos pequenos pelo Brasil." in context
    assert "Seis dias no coração" not in context.split("HISTÓRIA DA AGÊNCIA")[1]


def test_photo_from_the_pdf_used_by_the_ai_is_marked_with_its_origin(db_session):
    agency = _agency(db_session, "Rota Sul", "rotasul")
    other = _agency(db_session, "Outra", "outra")
    db_session.add_all([
        MediaAsset(agency_id=agency.id, url="/uploads/pdf-1.jpg", type="image", source="pdf",
                   original_file_name="folheto-jalapao - página 2 - foto 1", keywords="folheto-jalapao"),
        MediaAsset(agency_id=other.id, url="/uploads/pdf-9.jpg", type="image", source="pdf",
                   original_file_name="de outra - página 1", keywords="x"),
    ])
    db_session.flush()
    sections = [{"type": "hero", "backgroundImage": "/uploads/pdf-1.jpg"}, {"type": "photo", "image": "/uploads/pdf-9.jpg"}]
    mark_pdf_photos(db_session, agency.id, sections)
    assert sections[0]["aiPhotoOrigins"] == {"/uploads/pdf-1.jpg": 'PDF "folheto-jalapao"'}
    assert "aiPhotoOrigins" not in sections[1]  # foto de outra agência não é desta
