from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.ai_assistant import (
    _canonical_section_name,
    _validate_ai_reply_format,
    build_page_base_config_from_reply,
)


def reply_with(*blocks: str) -> str:
    return "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n" + "\n\n".join(blocks)


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        ("BANNER", "hero"),
        ("ITENS", "reasons"),
        ("BANNER EM CARD", "banner_card"),
    ],
)
def test_current_section_names_are_accepted(name: str, expected_type: str) -> None:
    text = reply_with(f"🟩 SEÇÃO: {name}\nTítulo: Exemplo")

    assert _validate_ai_reply_format(text) == (True, "")
    config, _ = build_page_base_config_from_reply(text)
    assert [section["type"] for section in config["sections"]] == [expected_type]


def test_safe_normalization_and_legacy_banner_alias() -> None:
    assert _canonical_section_name(" **  Banner   Inicial  ** ") == "BANNER"
    config, _ = build_page_base_config_from_reply(
        reply_with("🟩 SEÇÃO: **BANNER INICIAL**\nTítulo: Compatível")
    )
    assert config["sections"][0]["type"] == "hero"


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        ("FOTO DESTACADA", "photo"),
        ("BIOGRAFIA", "biography"),
        ("PREÇOS", "prices"),
        ("ITINERÁRIO", "itinerary"),
        ("PERGUNTAS FREQUENTES", "faq"),
        ("DEPOIMENTOS", "testimonials"),
        ("VÍDEO EM DESTAQUE", "featured_video"),
        ("CHAMADA PARA AÇÃO", "cta"),
        ("DESCRITIVO", "story"),
        ("CONTADOR", "countdown"),
        ("DETALHES DO VOO", "flight_details"),
    ],
)
def test_every_other_allowed_name_maps_to_existing_component(name: str, expected_type: str) -> None:
    config, _ = build_page_base_config_from_reply(reply_with(f"🟩 SEÇÃO: {name}\nTítulo: Exemplo"))
    assert config["sections"][0]["type"] == expected_type


def test_checkout_viajeon_is_forbidden_and_never_creates_component() -> None:
    text = reply_with(
        "🟩 SEÇÃO: CHECKOUT VIAJEON\nTítulo: Não criar",
        "🟩 SEÇÃO: BANNER\nTítulo: Válido",
    )
    config, _ = build_page_base_config_from_reply(text)
    assert [section["type"] for section in config["sections"]] == ["hero"]


def test_unknown_section_does_not_discard_valid_sections_and_items_are_complete() -> None:
    text = reply_with(
        "🟩 SEÇÃO: BANNER\nTítulo: Viagem",
        "🟩 SEÇÃO: DESCRITIVO\nEtiqueta: Experiência\nTítulo: Viva mais\nSubtítulo: Texto",
        (
            "🟩 SEÇÃO: ITENS\nEtiqueta: Incluso\nTítulo: Tudo preparado\n"
            "Subtítulo: Benefícios\nLista de itens:\n"
            "- Título: Hotel\n- Descrição: Três noites\n- Ícone: 🏨\n"
            "- Título: Transporte\n- Descrição: Ida e volta"
        ),
        "🟩 SEÇÃO: SEÇÃO INVENTADA\nTítulo: Ignorar",
    )

    assert _validate_ai_reply_format(text) == (True, "")
    config, _ = build_page_base_config_from_reply(text)
    assert [section["type"] for section in config["sections"]] == ["hero", "story", "reasons"]
    reasons = config["sections"][2]
    assert reasons["headingLabel"] == "Incluso"
    assert reasons["items"] == [
        {"title": "Hotel", "description": "Três noites", "icon": "🏨"},
        {"title": "Transporte", "description": "Ida e volta"},
    ]


def test_response_without_section_header_returns_controlled_error() -> None:
    text = "ESTRUTURA SUGERIDA PARA A PÁGINA\nTítulo sem cabeçalho"
    valid, error = _validate_ai_reply_format(text)
    assert valid is False
    assert error == "Nenhum bloco de seção foi encontrado."

    with pytest.raises(HTTPException) as exc_info:
        build_page_base_config_from_reply(text)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == error


def test_chat_endpoint_reply_passes_through_parser(client, db_session, monkeypatch) -> None:
    from app.api.deps import get_current_active_user
    from app.api.v1.endpoints import ai_assistant as endpoint
    from app.models.agency import Agency
    from app.models.page import Page
    from app.models.user import User

    agency = Agency(name="Agência Parser", slug="agencia-parser")
    user = User(name="Teste", email="parser@example.com", hashed_password="x", is_active=True)
    db_session.add_all([agency, user])
    db_session.flush()
    page = Page(agency_id=agency.id, title="Página", slug="pagina-parser", config_json={"sections": []})
    db_session.add(page)
    db_session.commit()

    real_reply = reply_with(
        "🟩 SEÇÃO: BANNER\nTítulo: Chapada",
        "🟩 SEÇÃO: ITENS\nTítulo: Incluso\nLista de itens:\n- Título: Guia\n- Descrição: Especializado",
    )
    client.app.dependency_overrides[get_current_active_user] = lambda: user
    monkeypatch.setattr(endpoint, "ensure_agency_member", lambda *args: None)
    monkeypatch.setattr(endpoint, "ensure_pages_editor_permission", lambda *args: None)
    monkeypatch.setattr(endpoint, "check_ai_assistant_message_limit", lambda *args: (SimpleNamespace(period_key="2026-08", message_count=0), None))
    monkeypatch.setattr(endpoint, "increment_ai_assistant_message_usage", lambda *args: SimpleNamespace(period_key="2026-08", message_count=1))
    monkeypatch.setattr(endpoint, "get_active_gpt_model", lambda *args, **kwargs: "gpt-test")
    monkeypatch.setattr(endpoint, "generate_ai_assistant_reply", lambda *args, **kwargs: real_reply)
    try:
        response = client.post(
            "/api/v1/ai-assistant/chat",
            data={"page_id": str(page.id), "conversation": '[{"role":"user","content":"Crie a página"}]'},
        )
    finally:
        client.app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 200, response.text
    config, _ = build_page_base_config_from_reply(response.json()["reply"])
    assert [section["type"] for section in config["sections"]] == ["hero", "reasons"]
