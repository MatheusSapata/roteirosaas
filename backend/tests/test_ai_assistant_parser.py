from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services.ai_assistant import (
    _canonical_section_name,
    _validate_ai_reply_format,
    build_page_base_config_from_reply,
)


def reply_with(*blocks: str) -> str:
    return "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n" + "\n\n".join(blocks)


def test_campos_do_jordao_structure_preserves_fields_items_and_all_days():
    text = (Path(__file__).parent / "fixtures" / "ai_campos_do_jordao.txt").read_text(encoding="utf-8")
    config, _ = build_page_base_config_from_reply(text, strict=True)
    hero, story, reasons, itinerary, faq, biography, cta = config["sections"]
    assert story["title"] == "Viva Campos do Jordão com todo conforto e diversão"
    assert story["subtitle"].startswith("Imagine-se respirando o ar puro da serra")
    assert "Sugestão de imagem" not in story["subtitle"]
    assert reasons["title"] == "Seu pacote inclui"
    assert reasons["subtitle"] == "Aproveite cada momento com tranquilidade"
    assert [item["icon"] for item in reasons["items"]] == [
        "icon:bus", "icon:bed", "icon:utensils", "icon:camera", "icon:wine", "icon:user-check",
    ]
    assert [{key: item[key] for key in ("title", "description")} for item in reasons["items"]] == [
        {"title": "Transporte ida e volta", "description": "Ônibus confortável com paradas programadas"},
        {"title": "Hospedagem", "description": "Hotel selecionado em Campos do Jordão"},
        {"title": "Refeições", "description": "Café da manhã, almoços e jantares inclusos conforme roteiro"},
        {"title": "City tours", "description": "Passeios panorâmicos pelos principais pontos turísticos"},
        {"title": "Degustações", "description": "Chocolates, queijos, vinhos e licores artesanais"},
        {"title": "Equipe acompanhante", "description": "Apoio durante toda a viagem"},
    ]
    assert itinerary["title"] == "Roteiro detalhado da viagem"
    assert [day["day"] for day in itinerary["days"]] == [
        "Dia 1 (sexta-feira)", "Dia 2 (sábado)", "Dia 3 (domingo)",
    ]
    for number, day in enumerate(itinerary["days"], 1):
        original = text.split(f"Dia {number} (", 1)[1].split(":", 1)[1]
        original = original.split(f"Dia {number + 1} (", 1)[0].split("🟩 SEÇÃO:", 1)[0].strip()
        assert day["description"] == original
        assert len(day["title"]) <= 65
    assert len(faq["items"]) == 4


@pytest.mark.parametrize("prefix", ["", "- ", "* ", "• ", "1. "])
def test_nested_items_and_weekday_headers_with_markdown(prefix):
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: ITENS\nTítulo: Pacote\nSubtítulo: Benefícios\nItens:\n"
        f"{prefix}**Hotel:** Duas noites\n{prefix}**Transporte:** Ida e volta",
        "🟩 SEÇÃO: ITINERÁRIO\nTítulo da seção: Roteiro\n"
        f"{prefix}**Dia 1 (sexta-feira):**\nChegada ao hotel.\n"
        f"{prefix}**Dia 2 (sábado):**\nPasseio pela cidade.",
    ))
    reasons, itinerary = config["sections"]
    assert reasons["title"] == "Pacote"
    assert reasons["subtitle"] == "Benefícios"
    assert len(reasons["items"]) == 2
    assert itinerary["title"] == "Roteiro"
    assert [day["description"] for day in itinerary["days"]] == ["Chegada ao hotel.", "Passeio pela cidade."]


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
        {"title": "Hotel", "description": "Três noites", "icon": "icon:hotel"},
        {"title": "Transporte", "description": "Ida e volta", "icon": "icon:bus"},
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


def test_generated_structure_replaces_sections_preserves_config_and_fills_images() -> None:
    from copy import deepcopy
    from app.services.ai_assistant import AI_IMAGE_PLACEHOLDER

    original = {"theme": {"color1": "#123456"}, "sections": [{"type": "gallery", "images": ["old.jpg"]}]}
    snapshot = deepcopy(original)
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER\nTítulo: Chapada\nSubtítulo: Viva essa experiência",
        "🟩 SEÇÃO: DESCRITIVO\nTítulo: A viagem\nSubtítulo: Natureza e descanso",
        "🟩 SEÇÃO: FOTO DESTACADA\nSugestão de imagem: Uma cachoeira",
        "🟩 SEÇÃO: BIOGRAFIA\nTítulo: Sua agência\nConteúdo: Viaje com quem conhece",
        "🟩 SEÇÃO: ITINERÁRIO\nDia 1: Chegada\nPasseio no centro",
        "🟩 SEÇÃO: DEPOIMENTOS\nNome: Ana\nTexto: Adorei a viagem",
    ), original)
    assert original == snapshot
    assert config["theme"] == original["theme"]
    assert [s["type"] for s in config["sections"]] == ["hero", "story", "photo", "biography", "itinerary", "testimonials"]
    hero, story, photo, biography, itinerary, testimonials = config["sections"]
    assert hero["title"] == "Chapada"
    assert hero["subtitle"] == "Viva essa experiência"
    assert story["subtitle"] == "Natureza e descanso"
    assert biography["text"] == "Viaje com quem conhece"
    assert hero["backgroundImage"] == hero["mobileBackgroundImage"] == AI_IMAGE_PLACEHOLDER
    assert story["images"] == [AI_IMAGE_PLACEHOLDER]
    assert photo["image"] == biography["image"] == AI_IMAGE_PLACEHOLDER
    assert itinerary["days"][0]["image"] == AI_IMAGE_PLACEHOLDER
    assert "avatar" not in testimonials["items"][0]
    anchors = [s["anchorId"] for s in config["sections"]]
    assert len(set(anchors)) == len(anchors)


def test_apply_structure_rejects_partial_conversion() -> None:
    text = reply_with("🟩 SEÇÃO: BANNER\nTítulo: Viagem", "🟩 SEÇÃO: INVENTADA\nTítulo: Não suportada")
    with pytest.raises(HTTPException) as exc_info:
        build_page_base_config_from_reply(text, strict=True)
    assert exc_info.value.status_code == 400


def test_apply_structure_keeps_cta_title_and_button_text() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: CHAMADA PARA AÇÃO\nEtiqueta: Vagas abertas\nTítulo: Viva essa viagem\nBotão: Reservar agora",
        "🟩 SEÇÃO: BANNER EM CARD\nTítulo: Aproveite\nBotão: Quero viajar",
    ), strict=True)
    cta, banner = config["sections"]
    assert cta["label"] == "Viva essa viagem"
    assert cta["ctaText"] == "Reservar agora"
    assert banner["ctaEnabled"] is True
    assert banner["ctaLabel"] == "Quero viajar"


@pytest.mark.parametrize("prefix", ["", "- ", "* ", "• ", "1. "])
def test_faq_keeps_each_question_and_answer_separate(prefix: str) -> None:
    pairs = [
        ("O ingresso do parque está incluso?", "Sim, o ingresso para um dia inteiro no Beto Carrero World já está incluso no pacote."),
        ("O transporte é feito em ônibus de turismo?", "Sim, utilizamos ônibus de turismo confortável, com acompanhamento durante todo o trajeto."),
        ("Posso parcelar o valor da viagem?", "Sim, oferecemos opções de parcelamento. Consulte as condições no momento da reserva."),
        ("Crianças pagam o mesmo valor?", "Consulte condições especiais para crianças no momento da reserva."),
        ("Como faço para reservar minha vaga?", "Basta clicar no botão de WhatsApp e falar com nossa equipe para garantir sua vaga."),
    ]
    block = "🟩 SEÇÃO: PERGUNTAS FREQUENTES\n- Função da seção: Reduzir dúvidas\n- Conteúdo:\n"
    block += "\n".join(f"{prefix}Pergunta: {q}\n  Resposta: {a}" for q, a in pairs)
    block += "\n\n---"
    config, _ = build_page_base_config_from_reply(reply_with(block))
    assert config["sections"][0]["items"] == [{"question": q, "answer": a} for q, a in pairs]


def test_faq_markdown_labels_and_multiline_answers() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PERGUNTAS FREQUENTES\n"
        "- **Pergunta:** O transporte é feito em ônibus de\nturismo?\n"
        "  - **Resposta:**\nSim, com acompanhamento.\nDurante todo o trajeto.\n"
        "- **Pergunta:** O que está incluso?\n"
        "**Resposta:** Confira:\n- Transporte\n- Ingresso\n---"
    ))
    assert config["sections"][0]["items"] == [
        {"question": "O transporte é feito em ônibus de turismo?", "answer": "Sim, com acompanhamento.\nDurante todo o trajeto."},
        {"question": "O que está incluso?", "answer": "Confira:\n- Transporte\n- Ingresso"},
    ]


@pytest.mark.parametrize("prefix", ["", "- ", "* ", "• ", "1. "])
def test_prices_create_one_card_per_package(prefix: str) -> None:
    packages = [
        ("Pacote Econômico", "R$ 1.890,00 por pessoa", 1890, "Parcelamento disponível."),
        ("Pacote Conforto", "R$ 2.490,00 por pessoa", 2490, "Consulte as formas de pagamento."),
        ("Pacote Premium", "R$ 3.290,00 por pessoa", 3290, "Consulte disponibilidade e condições vigentes."),
    ]
    block = "🟩 SEÇÃO: PREÇOS\n- Função da seção: Apresentar valores\n- Conteúdo:\n"
    block += "\n".join(
        f"{prefix}**Nome do plano:** {name}\n  Valor: {value}\n  Observação: {note}"
        for name, value, _, note in packages
    ) + "\n\n---"
    config, _ = build_page_base_config_from_reply(reply_with(block))
    section = config["sections"][0]
    assert section["layout"] == "cards"
    # O valor não se repete nas condições: o cartão mostra o preço uma vez, com o resto abaixo dele.
    assert section["items"] == [
        {"title": name, "price": price, "priceLabel": "", "description": f"por pessoa\n{note}", "currency": "BRL"}
        for name, value, price, note in packages
    ]


def test_single_price_preserves_multiline_terms_without_merging_numbers() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PREÇOS\nNome do plano: Econômico\n"
        "Valor: R$ 1.890,00 por pessoa em 10 parcelas\n"
        "Observação: Consulte disponibilidade.\nPagamento sujeito a condições.\n---"
    ))
    section = config["sections"][0]
    assert section["layout"] == "highlight"
    assert len(section["items"]) == 1
    assert section["items"][0]["price"] == 1890
    assert section["items"][0]["description"].endswith("Consulte disponibilidade.\nPagamento sujeito a condições.")


def test_itinerary_summarizes_headings_and_preserves_full_details() -> None:
    descriptions = [
        "Embarque com destino a Recife e traslado para Porto de Galinhas. Check-in e tempo livre para começar a explorar a praia.",
        "Dia livre para aproveitar as piscinas naturais, caminhar pelo centrinho e curtir o clima local.",
        "Sugestão de passeio opcional para Praia dos Carneiros ou Maragogi.",
        "Dia livre para relaxar, aproveitar a estrutura do hotel ou fazer passeios de jangada.",
        "Mais um dia para curtir as belezas de Porto de Galinhas, com tempo para compras e experiências gastronômicas.",
        "Check-out e traslado para o aeroporto de Recife. Retorno para casa com lembranças inesquecíveis.",
    ]
    block = "🟩 SEÇÃO: ITINERÁRIO\n" + "\n\n".join(
        f"- **Dia {index}:**\n{description}" for index, description in enumerate(descriptions, 1)
    ) + "\n---"
    config, _ = build_page_base_config_from_reply(reply_with(block))
    days = config["sections"][0]["days"]
    assert [day["description"] for day in days] == descriptions
    assert [day["title"] for day in days] == [
        "Embarque e traslado", "Dia livre e piscinas naturais", "Passeio opcional",
        "Dia livre para aproveitar", "Compras e gastronomia", "Check-out e retorno",
    ]


def test_itinerary_keeps_explicit_short_heading() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: ITINERÁRIO\nDia 1: Chegada a Recife\nTraslado ao hotel e tempo livre."
    ))
    day = config["sections"][0]["days"][0]
    assert day["title"] == "Chegada a Recife"
    assert day["description"] == "Traslado ao hotel e tempo livre."


@pytest.mark.parametrize("body_label", ["Texto descritivo", "Texto", "Descrição", "Subtítulo", "Conteúdo"])
def test_biography_keeps_body_out_of_image_heading(body_label: str) -> None:
    body = (
        "Somos apaixonados por criar experiências inesquecíveis e cuidar de cada detalhe da sua viagem.\n"
        "Com atendimento próximo e personalizado, garantimos segurança, tranquilidade e suporte do início ao fim."
    )
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BIOGRAFIA\n"
        "- Função da seção: apresentar a agência e transmitir confiança.\n"
        "- Conteúdo:\n- Etiqueta: Sobre nós\n- Título: Sua viagem, nosso cuidado\n"
        f"- {body_label}: {body}\n"
        "- Sugestão de imagem: Foto da equipe da agência."
    ))
    section = config["sections"][0]
    assert section["title"] == "Sua viagem, nosso cuidado"
    assert section["text"] == body
    assert section["titleFontSize"] == 36
    assert section["textFontSize"] == 18


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


def test_prices_keep_price_label_installments_and_shared_note() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PREÇOS\nNome do plano: Pacote Adulto\nValor: A partir de R$ 5.859,00 por pessoa\n"
        "Parcelamento: ou 12x de R$ 586,00\nObservação: Consulte disponibilidade.\n"
        "Nome do plano: Pacote Criança\nValor: R$ 4.988,00\nObservação: Consulte disponibilidade.\n---"
    ))
    section = config["sections"][0]
    adult, child = section["items"]
    assert adult["priceLabel"] == "A partir de"
    assert adult["price"] == 5859
    assert adult["description"] == "por pessoa\nou 12x de R$ 586,00"
    assert child["description"] == ""
    assert section["description"] == "Consulte disponibilidade."


def test_prices_detect_payment_methods_and_condition() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PREÇOS\nNome do plano: Pacote\nValor: R$ 3.000\n"
        "Formas de pagamento: Pix, boleto e cartão Visa, Mastercard e Elo em até 12x sem juros\n---"
    ))
    section = config["sections"][0]
    assert section["showPayments"] is True
    assert section["paymentMethods"] == ["pix", "boleto", "cartao", "visa", "mastercard", "elo"]
    assert section["paymentNote"] == "Em até 12x sem juros"


def test_prices_without_payment_methods_keep_strip_off() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PREÇOS\nNome do plano: Pacote\nValor: R$ 3.000\n---"
    ))
    assert "showPayments" not in config["sections"][0]


def test_banner_reads_trip_dates_only_with_year() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER\nTítulo: Santiago\nData de saída: 31/10/2026\nData de volta: 5 de novembro de 2026\n---"
    ))
    hero = config["sections"][0]
    assert hero["departureDate"] == "2026-10-31"
    assert hero["returnDate"] == "2026-11-05"
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER\nTítulo: Santiago\nData de saída: 31/10\n---"
    ))
    assert "departureDate" not in config["sections"][0]


def test_prices_with_prompt_labels_split_plans_and_never_show_raw_labels() -> None:
    # Resposta no formato do prompt do superadmin, que quebrava o card ("Nome do plano ou
    # pacote: ..." e "Diferenciais ou observação do plano: ..." apareciam como texto).
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PREÇOS\n"
        "- Função da seção: apresentar os valores.\n"
        "- Conteúdo:\n"
        "  - Título da seção: Escolha como embarcar\n"
        "  - Etiqueta: Investimento\n"
        "  - Nome do plano ou pacote: Adulto\n"
        "  - Valor: R$ 299,00\n"
        "  - Diferenciais ou observação do plano: Inclui todos os benefícios do Expresso Chocolate\n"
        "  - Nome do plano ou pacote: Criança (6 a 12 anos)\n"
        "  - Valor: R$ 199\n"
        "  - Diferenciais ou observação do plano: Válido para crianças acompanhadas de adulto pagante\n"
        "  - Nome do plano ou pacote: Criança até 5 anos (no colo)\n"
        "  - Valor: R$ 25\n"
        "  - Diferenciais ou observação do plano: Vaga no colo, sem assento reservado\n"
        "  - Consulte disponibilidade, formas de pagamento e condições vigentes."
    ))
    prices = config["sections"][0]
    assert prices["title"] == "Escolha como embarcar"
    assert prices["headingLabel"] == "Investimento"
    assert [(item["title"], item["price"], item["description"]) for item in prices["items"]] == [
        ("Adulto", 299.0, "Inclui todos os benefícios do Expresso Chocolate"),
        ("Criança (6 a 12 anos)", 199.0, "Válido para crianças acompanhadas de adulto pagante"),
        ("Criança até 5 anos (no colo)", 25.0, "Vaga no colo, sem assento reservado"),
    ]
    assert prices["description"] == "Consulte disponibilidade, formas de pagamento e condições vigentes."
    assert prices["layout"] == "cards"


def test_prices_contract_fields_badge_highlight_and_label_before_value() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: PREÇOS\nTítulo: Pacotes\n"
        "Plano: Quarto duplo\nSelo: Mais vendido\nDestaque: sim\nAntes do valor: A partir de\n"
        "Valor: R$ 2.490,00 por pessoa\nParcelamento: em até 10x sem juros\n"
        "Plano: Quarto individual\nValor: Sob consulta\n"
        "Observação geral: Valores sujeitos à disponibilidade.\nFormas de pagamento: Pix e cartão"
    ))
    prices = config["sections"][0]
    double, single = prices["items"]
    assert double["badge"] == "Mais vendido" and double["highlight"] is True
    assert double["priceLabel"] == "A partir de" and double["price"] == 2490.0
    assert double["description"] == "por pessoa\nem até 10x sem juros"
    assert single["price"] == 0 and single["description"] == "Sob consulta"
    assert "badge" not in single and "highlight" not in single
    assert prices["description"] == "Valores sujeitos à disponibilidade."
    assert prices["paymentMethods"] == ["pix", "cartao"]


def test_other_sections_read_prompt_labels() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: DEPOIMENTOS\nEtiqueta: Quem foi\nTítulo: O que dizem\n"
        "Nome: Ana\nIdentificação complementar: Viajou em 2025\nAvaliação: 5\nDepoimento: \"Tudo perfeito.\"",
        "🟩 SEÇÃO: CONTADOR\nEtiqueta: Lote promocional\nTítulo: Termina em\nData e horário: 20/12/2026 18:00",
        "🟩 SEÇÃO: FOTO DESTACADA\nTítulo: Pôr do sol na Duna\nTipo de layout: largura total\nSugestão de imagem: duna",
        "🟩 SEÇÃO: VÍDEO EM DESTAQUE\nTítulo: Veja\nLink ou referência do vídeo: inserir link do YouTube",
        "🟩 SEÇÃO: DESCRITIVO\nEtiqueta: Experiência\nTítulo: Viva\nTexto descritivo: Um texto longo.",
        "🟩 SEÇÃO: CHAMADA PARA AÇÃO\nEtiqueta: Vagas\nTítulo: Garanta\nDescrição: Fale com a gente.\nBotão: Quero ir",
        "🟩 SEÇÃO: BANNER\nTítulo: Jalapão\nDestaques:\n- Hospedagem em pousada\n- Guia credenciado\n- Saída em julho\n- Grupo pequeno",
    ))
    testimonials, countdown, photo, video, story, cta, hero = config["sections"]
    assert testimonials["items"] == [{"name": "Ana", "role": "Viajou em 2025", "text": "Tudo perfeito."}]
    assert testimonials["title"] == "O que dizem" and testimonials["headingLabel"] == "Quem foi"
    assert countdown["label"] == "Termina em" and countdown["headingLabel"] == "Lote promocional"
    assert countdown["targetDate"] == "2026-12-20T21:00:00Z"
    assert photo["caption"] == "Pôr do sol na Duna" and photo["layout"] == "full"
    assert video["videoUrl"] == ""
    assert story["subtitle"] == "Um texto longo." and story["badge"] == "Experiência"
    assert cta["label"] == "Garanta" and cta["description"] == "Fale com a gente." and cta["headingLabel"] == "Vagas"
    assert hero["chipIcons"] == ["icon:bed", "icon:user-check", "icon:calendar-days", "icon:users"]


def test_full_reply_in_platform_contract_format() -> None:
    from app.services.ai_assistant import PLATFORM_FORMAT_CONTRACT, load_system_prompt  # noqa: F401

    text = """ESTRUTURA SUGERIDA PARA A PÁGINA
Tipo de página: Excursão rodoviária
Objetivo da página: Vender as vagas
Público predominante: Famílias

🟩 SEÇÃO: BANNER
Função da seção: impacto
Título: Natal Luz em Gramado
Subtítulo: Quatro dias de luzes e chocolate na Serra Gaúcha.
Destaques:
- Ônibus leito
- Hotel com café da manhã
- Guia acompanhante
Data de saída: 12/12/2026
Data de volta: 15/12/2026
Botão: Quero minha vaga
Sugestão de imagem: Rua Coberta iluminada

🟩 SEÇÃO: ITENS
Função da seção: inclusos
Etiqueta: Incluso
Título: Tudo pensado para você
Subtítulo: Só aproveitar
Item: Ônibus leito
Descrição: Ida e volta com conforto
Ícone: bus
Item: Café da manhã
Descrição: Todos os dias no hotel
Ícone: coffee
Item: Ingressos
Descrição: Para o Natal Luz
Ícone: ticket

🟩 SEÇÃO: ITINERÁRIO
Função da seção: roteiro
Etiqueta: Roteiro
Título: Dia a dia
Dia 1: Embarque e chegada
Saída cedo e chegada à tarde.
Dia 2: Centro de Gramado
Passeio pelo centro e Lago Negro.

🟩 SEÇÃO: PREÇOS
Função da seção: valores
Etiqueta: Investimento
Título: Escolha seu pacote
Plano: Adulto
Selo: Mais vendido
Destaque: sim
Antes do valor: A partir de
Valor: R$ 1.890,00 por pessoa
Parcelamento: em até 10x sem juros
Detalhes: Assento no ônibus e cama no quarto duplo
Plano: Criança até 5 anos
Valor: R$ 290,00
Detalhes: No colo, dividindo a cama
Formas de pagamento: Pix, boleto e cartão
Observação geral: Consulte disponibilidade, formas de pagamento e condições vigentes.

🟩 SEÇÃO: DETALHES DO VOO
Função da seção: voo
Título: Seu voo
Ida: 12/07/2026, São Paulo (GRU) 08:00 → Recife (REC) 11:15, LATAM
Bagagem: 1 mala de 23 kg
"""
    config, title = build_page_base_config_from_reply(text, strict=True)
    hero, reasons, itinerary, prices, flight = config["sections"]
    assert title == "Natal Luz em Gramado"
    assert hero["chips"] == ["Ônibus leito", "Hotel com café da manhã", "Guia acompanhante"]
    assert hero["chipIcons"] == ["icon:bus", "icon:hotel", "icon:user-check"]
    assert (hero["departureDate"], hero["returnDate"]) == ("2026-12-12", "2026-12-15")
    assert reasons["iconMode"] == "icon"
    assert [(i["title"], i["icon"]) for i in reasons["items"]] == [
        ("Ônibus leito", "icon:bus"), ("Café da manhã", "icon:coffee"), ("Ingressos", "icon:ticket"),
    ]
    assert itinerary["headingLabel"] == "Roteiro"
    assert [(d["title"], d["description"]) for d in itinerary["days"]] == [
        ("Embarque e chegada", "Saída cedo e chegada à tarde."),
        ("Centro de Gramado", "Passeio pelo centro e Lago Negro."),
    ]
    adult, child = prices["items"]
    assert (adult["title"], adult["badge"], adult["highlight"], adult["priceLabel"], adult["price"]) == (
        "Adulto", "Mais vendido", True, "A partir de", 1890.0,
    )
    assert adult["description"] == "por pessoa\nem até 10x sem juros\nAssento no ônibus e cama no quarto duplo"
    assert (child["title"], child["price"], child["description"]) == ("Criança até 5 anos", 290.0, "No colo, dividindo a cama")
    assert prices["description"] == "Consulte disponibilidade, formas de pagamento e condições vigentes."
    assert prices["paymentMethods"] == ["pix", "boleto", "cartao"]
    assert flight["generalInfo"] == (
        "<p>Ida: 12/07/2026, São Paulo (GRU) 08:00 → Recife (REC) 11:15, LATAM</p><p>Bagagem: 1 mala de 23 kg</p>"
    )
    for section in config["sections"]:
        for value in section.values():
            assert "Função da seção" not in str(value)
