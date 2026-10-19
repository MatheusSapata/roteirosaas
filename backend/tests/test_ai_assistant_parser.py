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
    # O trecho vira cartão de voo (aiFlights); no texto fica só a bagagem.
    assert flight["generalInfo"] == "<p>Bagagem: 1 mala de 23 kg</p>"
    [ida] = flight["aiFlights"]
    assert ida["direction"] == "outbound" and ida["segments"][0]["departure_airport_iata"] == "GRU"
    assert ida["segments"][0]["arrival_datetime"] == "2026-07-12T11:15:00" and ida["segments"][0]["airline_name"] == "LATAM"
    for section in config["sections"]:
        for value in section.values():
            assert "Função da seção" not in str(value)


def test_multi_trip_page_with_header_links_to_sections() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER\nTítulo: Viagens de inverno 2026",
        "🟩 SEÇÃO: VITRINE DE VIAGENS\nEtiqueta: Saídas confirmadas\nTítulo: Escolha sua próxima viagem\n"
        "Viagem: Gramado e Canela\nDescrição: Serra gaúcha no auge do frio.\nData de saída: 10/07/2026\n"
        "Data de volta: 14/07/2026\nAntes do valor: A partir de\nValor: R$ 1.290\nDepois do valor: por pessoa\n"
        "Botão: Ver roteiro\n"
        "Viagem: Campos do Jordão\nDescrição: Fondue e montanhas.\n",
        "🟩 SEÇÃO: PERGUNTAS FREQUENTES\nPergunta: Tem parcelamento?\nResposta: Consulte.",
        "🟩 SEÇÃO: MENU DO TOPO\nLinks do menu:\n- Viagens\n- Dúvidas\n- Blog\nBotão: Chamar no WhatsApp",
    ), strict=True)
    header, hero, links, faq = config["sections"]
    assert header["type"] == "header" and "_menuItems" not in header
    # "Blog" não tem seção: vai sem destino para o editor ligar a uma seção existente (ou tirar).
    assert [(link["label"], link["target"]) for link in header["links"]] == [
        ("Viagens", links["anchorId"]), ("Dúvidas", faq["anchorId"]), ("Blog", ""),
    ]
    assert header["links"][2]["aiTargetLabel"] == "Blog"
    assert header["contactLabel"] == "Chamar no WhatsApp"
    assert links["headingLabel"] == "Saídas confirmadas" and links["title"] == "Escolha sua próxima viagem"
    gramado, campos = links["items"]
    assert (gramado["title"], gramado["departureDate"], gramado["returnDate"]) == ("Gramado e Canela", "2026-07-10", "2026-07-14")
    assert (gramado["pricePrefix"], gramado["priceValue"], gramado["priceSuffix"]) == ("A partir de", "R$ 1.290", "por pessoa")
    assert gramado["buttonLabel"] == "Ver roteiro" and gramado["source"] == "external"
    assert campos["description"] == "Fondue e montanhas." and "showPrice" not in campos


def test_chat_reply_problem_accepts_questions_and_rejects_broken_structure() -> None:
    from app.services.ai_assistant import _chat_reply_problem

    assert _chat_reply_problem("Antes de criar, me conta:\n1. Qual o destino?\n2. Quais as datas?") == ""
    assert _chat_reply_problem(reply_with("🟩 SEÇÃO: BANNER\nTítulo: Ok")) == ""
    assert _chat_reply_problem("") != ""
    assert _chat_reply_problem("ESTRUTURA SUGERIDA PARA A PÁGINA\nTipo de página: excursão") != ""
    assert _chat_reply_problem(reply_with("🟩 SEÇÃO: INVENTADA\nTítulo: X")) != ""


class _FakeStream:
    def __init__(self, chunks):
        self.chunks = chunks

    def __iter__(self):
        for chunk in self.chunks:
            yield SimpleNamespace(type="response.output_text.delta", delta=chunk)
        yield SimpleNamespace(
            type="response.completed",
            response=SimpleNamespace(usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15)),
        )


def test_stream_reply_emits_steps_deltas_and_done(monkeypatch) -> None:
    from app.services import ai_assistant

    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return _FakeStream(["ESTRUTURA SUGERIDA PARA A PÁGINA\n", "🟩 SEÇÃO: BANNER\n", "Título: Oi"])

    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(ai_assistant, "_load_openai_client", lambda: client)
    monkeypatch.setattr(ai_assistant, "load_system_prompt", lambda: "prompt")
    events = list(ai_assistant.stream_ai_assistant_reply(
        [ai_assistant.ChatMessage(role="user", content="Monte a página")], model_override="gpt-5.4",
    ))
    assert [event["type"] for event in events] == ["status", "status", "delta", "delta", "delta", "done"]
    assert [event.get("step") for event in events[:2]] == ["thinking", "writing"]
    assert events[-1]["reply"].endswith("Título: Oi")
    assert events[-1]["usage"]["total_tokens"] == 15
    # Modelos que raciocinam: esforço curto e sem temperature.
    assert calls[0]["reasoning"] == {"effort": "low"} and "temperature" not in calls[0] and calls[0]["stream"] is True


def test_stream_reply_redoes_broken_structure_once(monkeypatch) -> None:
    from app.services import ai_assistant

    fixed = SimpleNamespace(output_text=reply_with("🟩 SEÇÃO: BANNER\nTítulo: Certo"), usage=None)

    def create(**kwargs):
        if kwargs.get("stream"):
            return _FakeStream(["ESTRUTURA SUGERIDA PARA A PÁGINA\nsem seções"])
        return fixed

    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(ai_assistant, "_load_openai_client", lambda: client)
    monkeypatch.setattr(ai_assistant, "load_system_prompt", lambda: "prompt")
    events = list(ai_assistant.stream_ai_assistant_reply(
        [ai_assistant.ChatMessage(role="user", content="Monte")], model_override="gpt-4.1",
    ))
    assert ("fixing" in [event.get("step") for event in events]) and events[-2]["type"] == "replace"
    assert events[-1]["reply"].endswith("Título: Certo")


def test_repeated_sections_and_menu_links_by_title_and_existing_page() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: MENU DO TOPO\nLinks do menu:\n- Nacionais\n- Internacionais\n- Sobre nós\nLado direito: redes sociais",
        "🟩 SEÇÃO: VITRINE DE VIAGENS\nTítulo: Pacotes nacionais\nViagem: Gramado e Canela\nPágina: gramado-canela\nValor: R$ 200",
        "🟩 SEÇÃO: VITRINE DE VIAGENS\nTítulo: Pacotes internacionais\nViagem: França\nAntes do valor: A partir de\nValor: R$ 4.500",
        "🟩 SEÇÃO: BIOGRAFIA\nTítulo: Nossa história\nTexto: Desde 2019.",
    ), strict=True)
    header, nacionais, internacionais, bio = config["sections"]
    assert header["actionType"] == "social"
    assert [(link["label"], link["target"]) for link in header["links"]] == [
        ("Nacionais", nacionais["anchorId"]), ("Internacionais", internacionais["anchorId"]), ("Sobre nós", bio["anchorId"]),
    ]
    assert nacionais["anchorId"] != internacionais["anchorId"]
    assert nacionais["items"][0]["pageSlug"] == "gramado-canela"
    assert "pageSlug" not in internacionais["items"][0]


def test_agency_context_lists_registered_data_and_pages(monkeypatch) -> None:
    from app.services import ai_assistant_context as ctx

    agency = SimpleNamespace(id=1, name="Rota Sul", logo_url="/logo.png")
    page = SimpleNamespace(id=10, agency=agency, title="Home", slug="home", config_json={"sections": []})
    other = SimpleNamespace(
        id=11, title="Gramado e Canela", slug="gramado-canela", status="published",
        config_json={"sections": [
            {"type": "hero", "subtitle": "<p>Inverno na serra</p>", "departureDate": "2026-12-10"},
            {"type": "prices", "items": [{"price": 1290}, {"price": 990.5}]},
        ]},
    )

    class Query:
        def filter(self, *a):
            return self

        def order_by(self, *a):
            return self

        def limit(self, *a):
            return self

        def all(self):
            return [other]

    db = SimpleNamespace(query=lambda *a: Query())
    monkeypatch.setattr(ctx, "curated_catalog", lambda db: ["beto carrero nerf", "beto carrero castelo"])
    import app.api.v1.endpoints.public_pages as public_pages

    monkeypatch.setattr(public_pages, "build_agency_profile", lambda agency: {
        "description": "Especialistas em Beto Carrero", "address": {"city": "Itajaí", "state": "SC"},
        "phone": "5547999990000", "email": "oi@rotasul.com",
        "social_links": [{"network": "instagram", "url": "https://instagram.com/rotasul"}],
    })
    text = ctx.build_agency_context(db, page)
    assert "Agência: Rota Sul" in text and "Cidade: Itajaí, SC" in text
    assert "Redes sociais cadastradas: Instagram" in text and "Logo: cadastrado" in text
    assert "Fotos cadastradas no banco" in text and "beto carrero nerf; beto carrero castelo" in text
    assert '- gramado-canela: "Gramado e Canela" (publicada, saída 10/12/2026, a partir de R$ 990,50) · Inverno na serra' in text
    assert "SEÇÕES DESTA PÁGINA: nenhuma ainda." in text
    # Seções enviadas pelo editor (com o que ainda não foi salvo) entram com o nome do editor.
    text = ctx.build_agency_context(db, page, [
        {"type": "biography", "anchorId": "nossa-historia", "title": "Nossa história"},
        {"type": "free_footer_brand"},
        {"type": "links", "anchorId": "viagens-2", "title": {"pt": "Nacionais"}, "enabled": False},
    ])
    assert '1. nossa-historia: Artigo · "Nossa história"' in text
    assert "3. viagens-2: Links/Roteiros (oculta)" in text


def test_editor_section_names_and_replaces() -> None:
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: TEXTO E IMAGENS\nFunção da seção: troca\nSubstitui: nossa-historia\nTítulo: Nossa história\nTexto: Desde 2019.",
        "🟩 SEÇÃO: LINKS/ROTEIROS\nTítulo: Nacionais\nViagem: Gramado",
        "🟩 SEÇÃO: DIFERENCIAIS\nTítulo: Por que nós\nItem: Guia\nDescrição: Sempre junto",
        "🟩 SEÇÃO: ARTIGO\nTítulo: Blog\nTexto: Longo.",
        "🟩 SEÇÃO: DÚVIDAS FREQUENTES\nPergunta: Tem?\nResposta: Sim.",
        "🟩 SEÇÃO: FAIXA DE CHAMADA\nTítulo: Vamos?\nBotão: Quero",
        "🟩 SEÇÃO: PREÇOS E PACOTES\nPlano: Adulto\nValor: R$ 10",
        "🟩 SEÇÃO: ROTEIRO DIA A DIA\nDia 1: Chegada\nHotel.",
        "🟩 SEÇÃO: FOTO EM DESTAQUE\nLegenda: Mar",
    ), strict=True)
    types = [section["type"] for section in config["sections"]]
    assert types == ["story", "links", "reasons", "biography", "faq", "cta", "prices", "itinerary", "photo"]
    assert config["sections"][0]["aiReplaces"] == "nossa-historia"
    assert "aiReplaces" not in config["sections"][1]


def test_diferenciais_icon_or_emoji_style() -> None:
    icons, emojis, auto_emojis, converted = (
        build_page_base_config_from_reply(reply_with(block))[0]["sections"][0]
        for block in (
            "🟩 SEÇÃO: DIFERENCIAIS\nTítulo: A\nItem: Hotel\nDescrição: Bom\nÍcone: hotel\nItem: Guia\nDescrição: Junto",
            "🟩 SEÇÃO: DIFERENCIAIS\nTítulo: B\nEstilo dos ícones: emojis\nItem: Parque\nDescrição: Diversão\nÍcone: 🎢\n"
            "Item: Hotel\nDescrição: Perto\nÍcone: hotel\nItem: Cuidado\nDescrição: Sempre",
            "🟩 SEÇÃO: DIFERENCIAIS\nTítulo: C\nItem: Família\nDescrição: Todos\nÍcone: 👨‍👩‍👧\nItem: Ônibus\nDescrição: Ida\nÍcone: 🚌",
            "🟩 SEÇÃO: DIFERENCIAIS\nTítulo: D\nEstilo dos ícones: ícones\nItem: Ônibus\nDescrição: Ida\nÍcone: 🚌",
        )
    )
    assert icons["iconMode"] == "icon" and [i["icon"] for i in icons["items"]] == ["icon:hotel", "icon:user-check"]
    assert emojis["iconMode"] == "emoji" and [i["icon"] for i in emojis["items"]] == ["🎢", "🏨", "✅"]
    assert auto_emojis["iconMode"] == "emoji" and [i["icon"] for i in auto_emojis["items"]] == ["👨‍👩‍👧", "🚌"]
    assert converted["iconMode"] == "icon" and converted["items"][0]["icon"] == "icon:bus"


def test_context_shows_diferenciais_style() -> None:
    from app.services.ai_assistant_context import _sections_summary

    assert _sections_summary([{"type": "reasons", "anchorId": "por-que", "iconMode": "emoji", "title": "Por que nós"}]) == [
        '1. por-que: Diferenciais (com emojis) · "Por que nós"'
    ]
    assert "(com ícones)" in _sections_summary([{"type": "reasons", "anchorId": "x"}])[0]


def test_contract_guides_conversation_and_photos() -> None:
    from app.services.ai_assistant import PLATFORM_FORMAT_CONTRACT

    assert "números são só para perguntas" in PLATFORM_FORMAT_CONTRACT
    assert "bancos gratuitos (Pixabay, Unsplash e Pexels)" in PLATFORM_FORMAT_CONTRACT


def test_stock_photos_fill_sections_without_saved_searches(monkeypatch) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.stock_image import StockImage
    from app.services import stock_images

    engine = create_engine("sqlite://")
    StockImage.__table__.create(engine)
    db = sessionmaker(bind=engine)()

    calls = []

    def fake_pexels(client, key, query, record=None):
        calls.append(query)
        if "gramado" not in query.lower() and "wine" not in query.lower() and "travel" not in query.lower():
            return []
        return [
            {"provider": "pexels", "provider_id": f"{query}-{n}", "download_url": f"https://img/{query}/{n}.jpg",
             "page_url": "p", "photographer": "Ana", "photographer_url": "u", "alt": "", "width": 10, "height": 5}
            for n in range(3)
        ]

    monkeypatch.setattr(stock_images, "_search_pexels", fake_pexels)
    monkeypatch.setattr(stock_images, "materialize", lambda db, client, image: f"/uploads/{image.provider_id}.webp")
    pexels_key = stock_images.ImageKey(provider="pexels", plain_key="k")
    monkeypatch.setattr(stock_images, "available_image_keys", lambda db, provider: [pexels_key] if provider == "pexels" else [])
    monkeypatch.setattr(stock_images, "has_any_image_key", lambda db: True)
    # Sem a IA escolhendo nem sugerindo buscas (testadas à parte): vale a ordem do ranking.
    monkeypatch.setattr(stock_images, "choose_photos", lambda *args, **kwargs: None)
    monkeypatch.setattr(stock_images, "refine_queries", lambda db, slots, *, timeout: {})
    monkeypatch.setattr(stock_images, "prepare_download", lambda client, url: None)

    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: BANNER INICIAL\nTítulo: Gramado\nBusca de imagem: Gramado Brazil street | couple drinking wine",
        "🟩 SEÇÃO: TEXTO E IMAGENS\nTítulo: Vinícolas\nBusca de imagem: Vale dos Vinhedos | couple drinking wine",
        "🟩 SEÇÃO: TEXTO E IMAGENS\nSubstitui: outra\nTítulo: Só texto",
        "🟩 SEÇÃO: LINKS/ROTEIROS\nTítulo: Viagens\nViagem: Gramado\nBusca de imagem: Gramado Brazil street",
    ))
    sections = config["sections"]
    assert sections[0]["aiImageQuery"].startswith("Gramado") and "aiImageQuery" not in sections[2]
    filled = stock_images.fill_section_photos(db, sections, agency_id=None)
    hero, story, swap, links = sections
    assert filled == 5
    assert hero["backgroundImage"] == hero["mobileBackgroundImage"] == "/uploads/Gramado Brazil street-0.webp"
    # Sem foto do lugar, a sensação ("couple drinking wine") entra; o carrossel leva 3 fotos e
    # nada se repete na página.
    assert story["images"] == [f"/uploads/couple drinking wine-{n}.webp" for n in range(3)] and story["aiStockPhoto"] is True
    assert "aiStockPhoto" not in swap
    assert links["items"][0]["image"] == "/uploads/Gramado Brazil street-1.webp"
    assert all("aiImageQuery" not in section for section in sections)
    # A mesma busca saiu uma vez só para o banner e o card; na próxima página ela vai ao banco de
    # novo (não há busca guardada, que devolvia sempre as mesmas fotos).
    assert calls.count("Gramado Brazil street") == 1
    before = len(calls)
    assert len(stock_images.search_stock_images(db, None, "Gramado  brazil STREET")) == 3
    assert len(calls) == before + 1


def test_stock_search_rotates_keys_and_respects_paused_banks(monkeypatch) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.external_api_key import ExternalApiKey
    from app.models.stock_image import StockImage
    from app.services import image_api_keys, stock_images

    engine = create_engine("sqlite://")
    for table in (StockImage.__table__, ExternalApiKey.__table__):
        table.create(engine)
    db = sessionmaker(bind=engine)()
    monkeypatch.setattr(image_api_keys, "decrypt_api_key", lambda value: value)
    monkeypatch.setattr(image_api_keys, "get_settings", lambda: SimpleNamespace(unsplash_access_key=None, pexels_api_key=None))
    # Duas chaves do Unsplash: a primeira só tem 5 chamadas na hora (com a folga, 2).
    db.add_all([
        ExternalApiKey(provider="unsplash", label="A", api_key_encrypted="key-a", priority=1, monthly_limit=5, status="active", is_active=True),
        ExternalApiKey(provider="unsplash", label="B", api_key_encrypted="key-b", priority=2, monthly_limit=50, status="active", is_active=True),
    ])
    db.commit()
    calls = []

    def fake_unsplash(client, key, query, record=None):
        calls.append((key, query))
        if record:
            record(SimpleNamespace(status_code=200, headers={}))
        alt = "couple drinking red wine at vineyard" if "wine" in query else f"{query} view"
        return [
            {"provider": "unsplash", "provider_id": f"{query}-{n}", "download_url": "d", "stored_url": f"https://u/{query}/{n}",
             "page_url": "p", "photographer": "Ana", "photographer_url": "https://unsplash.com/@ana", "alt": alt, "width": 1, "height": 1}
            for n in range(4)
        ]

    monkeypatch.setattr(stock_images, "_search_unsplash", fake_unsplash)
    from datetime import datetime, timezone

    def search(query):
        return stock_images.search_stock_images(db, None, query)

    assert len(search("Gramado Brazil street")) == 4
    assert len(search("red wine couple")) == 4
    # A chave A esgotou na hora: a busca seguinte vai para a B. A mesma busca de antes vai ao
    # banco de novo (nada fica guardado).
    key_a = db.query(ExternalApiKey).filter_by(label="A").one()
    key_b = db.query(ExternalApiKey).filter_by(label="B").one()
    assert key_a.monthly_usage_estimated == 2
    assert len(search("Gramado Brazil street")) == 4 and db.query(StockImage).count() == 8
    assert calls[-1] == ("key-b", "Gramado Brazil street") and [key for key, _ in calls] == ["key-a", "key-a", "key-b"]
    # Sem chamada sobrando na hora: nada vem de busca guardada nem de foto parecida já vista.
    key_b.monthly_usage_estimated, key_b.last_used_at = 50, datetime.now(timezone.utc)
    db.flush()
    assert search("vineyard couple drinking") == [] and len(calls) == 3
    # Unsplash pausado no Admin Master: nenhuma busca.
    key_a.is_active = key_b.is_active = False
    key_b.monthly_usage_estimated = 0
    db.flush()
    assert search("Gramado Brazil street") == [] and len(calls) == 3
    key_a.is_active = key_b.is_active = True
    # Chave recusada pelo banco fica "com erro"; esgotada volta na hora seguinte.
    image_api_keys.record_image_call(db, image_api_keys.ImageKey("unsplash", "key-b", key_b), SimpleNamespace(status_code=401, headers={}))
    assert key_b.status == "error"
    image_api_keys.record_image_call(db, image_api_keys.ImageKey("unsplash", "key-a", key_a), SimpleNamespace(status_code=429, headers={}))
    assert key_a.status == "exhausted"
    from datetime import datetime, timedelta, timezone

    key_a.last_used_at = datetime.now(timezone.utc) - timedelta(hours=1, minutes=5)
    assert image_api_keys.roll_hour(key_a) and key_a.status == "active" and key_a.monthly_usage_estimated == 0
    # Crédito com os links pedidos pelo Unsplash.
    credit = stock_images.credit_for(db.query(StockImage).first(), "https://u/x")
    assert credit["provider"] == "Unsplash" and credit["link"].endswith("utm_source=roteiro_online&utm_medium=referral")


def test_stock_search_prefers_brazil_recent_and_matching_photos(monkeypatch):
    from datetime import datetime, timedelta, timezone

    import httpx

    from app.models.stock_image import StockImage
    from app.services import stock_images

    # Destino brasileiro sem o país ganha "Brazil"; fora do Brasil, nada muda.
    assert stock_images.with_country("Beto Carrero World Penha") == "Beto Carrero World Penha Brazil"
    assert stock_images.with_country("Gramado Brazil street") == "Gramado Brazil street"
    assert stock_images.with_country("Lisbon Alfama") == "Lisbon Alfama"
    assert stock_images.mentions_brazil("Praia em Santa Catarina") and not stock_images.mentions_brazil("Paris")

    now = datetime(2026, 10, 1, tzinfo=timezone.utc)

    def photo(pid, alt="", tags=None, location=None, years=None, width=10, height=6):
        published = now - timedelta(days=365 * years) if years is not None else None
        return StockImage(provider="unsplash", provider_id=pid, download_url="d", alt=alt, tags=tags,
                          location=location, published_at=published, width=width, height=height)

    images = [
        photo("velho", "roller coaster amusement park", years=11),
        photo("outro-pais", "roller coaster", location="Orlando, USA", years=1),
        photo("deitada-nao", "Beto Carrero World park", tags="brazil, theme park", years=1, width=6, height=10),
        photo("brasil", "theme park ride", tags="beto carrero, santa catarina", location="Penha, Brazil", years=2),
    ]
    ranked = stock_images.rank_images(images, "Beto Carrero World Brazil", prefer_brazil=True, now=now)
    assert [image.provider_id for image in ranked][:2] == ["brasil", "deitada-nao"]
    assert ranked[-1].provider_id == "velho"

    # Do Unsplash vêm descrição, tags, local do fotógrafo e data, que vão para o banco de fotos.
    payload = {"results": [{
        "id": "x1", "urls": {"raw": "https://images.unsplash.com/x1?ixid=1"},
        "links": {"download_location": "dl", "html": "h"}, "description": "Parque em Penha",
        "alt_description": "roller coaster", "tags": [{"title": "brasil"}, {"title": "parque"}],
        "created_at": "2024-05-02T10:00:00Z", "user": {"name": "Ana", "location": "Florianópolis, Brasil", "links": {}},
        "width": 3000, "height": 2000,
    }]}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with httpx.Client(transport=transport) as client:
        [result] = stock_images._search_unsplash(client, "k", "Beto Carrero Brazil")
    assert result["alt"] == "Parque em Penha roller coaster" and result["tags"] == "brasil, parque"
    assert result["location"] == "Florianópolis, Brasil" and result["published_at"].year == 2024


def test_pixabay_comes_first_after_curated_and_hides_key(monkeypatch):
    import httpx
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.stock_image import StockImage
    from app.services import stock_images

    engine = create_engine("sqlite://")
    StockImage.__table__.create(engine)
    db = sessionmaker(bind=engine)()

    calls = []
    keys = {name: [stock_images.ImageKey(provider=name, plain_key=f"chave-{name}")] for name in ("pixabay", "unsplash", "pexels")}
    monkeypatch.setattr(stock_images, "available_image_keys", lambda db, provider: keys[provider])
    monkeypatch.setattr(stock_images, "record_image_call", lambda *a: None)

    def fake(name):
        def search(client, key, query, record=None):
            calls.append(name)
            return [{"provider": name, "provider_id": f"{name}-1", "download_url": "https://x/1.jpg", "page_url": "p",
                     "photographer": "Ana", "photographer_url": "u", "alt": "beach", "width": 10, "height": 6}]
        return search

    monkeypatch.setattr(stock_images, "_search_unsplash", fake("unsplash"))
    monkeypatch.setattr(stock_images, "_search_pexels", fake("pexels"))

    payload = {"hits": [{"id": 7, "pageURL": "https://pixabay.com/photos/7", "tags": "beach, sea, brazil",
                         "largeImageURL": "https://pixabay.com/get/7_1280.jpg", "imageWidth": 1920, "imageHeight": 1280,
                         "user": "ana", "user_id": 42}]}
    seen_urls = []

    def handler(request):
        seen_urls.append(str(request.url))
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        found = stock_images.search_stock_images(db, client, "Copacabana beach Brazil")
    assert calls == [] and found[0].provider == "pixabay" and found[0].tags == "beach, sea, brazil"
    assert "key=chave-pixabay" in seen_urls[0] and "safesearch=true" in seen_urls[0]
    assert stock_images.credit_for(found[0], "u") == {
        "url": "u", "name": "ana", "link": "https://pixabay.com/users/ana-42/?utm_source=roteiro_online&utm_medium=referral",
        "provider": "Pixabay", "providerLink": "https://pixabay.com/?utm_source=roteiro_online&utm_medium=referral",
    }

    # Erro do Pixabay: a mensagem não leva o endereço (que tem a chave) e o Unsplash assume.
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429))) as client:
        try:
            stock_images._search_pixabay(client, "chave-secreta", "x")
        except RuntimeError as exc:
            assert "chave-secreta" not in str(exc)
        found = stock_images.search_stock_images(db, client, "Gramado street winter")
    assert found[0].provider == "unsplash" and calls == ["unsplash"]


def test_header_adjustment_changes_only_what_was_asked():
    # "Deixa o menu transparente e fixo": só aparência, nada de itens (os atuais ficam).
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: MENU DO TOPO\nSubstitui: header-menu-0\nAparência: transparente (por cima do banner)\nFixo ao rolar: não\nCor do texto: #FFFFFF",
    ))
    [header] = [s for s in config["sections"] if s["type"] == "header"]
    assert header["mode"] == "transparent" and header["stickyEnabled"] is False
    assert header["textColor"] == header["linkTextColor"] == "#FFFFFF"
    assert set(header["aiSetKeys"]) == {"mode", "stickyEnabled", "textColor", "linkTextColor"}
    assert "links" not in header and header["aiReplaces"] == "header-menu-0"

    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: MENU DO TOPO\nSubstitui: header-menu-0\nAparência: vidro fosco",
    ))
    assert config["sections"][0]["mode"] == "blurred"


def test_header_menu_items_link_to_existing_sections_by_identifier():
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: MENU DO TOPO\nSubstitui: header-menu-0\nLinks do menu:\n"
        "- Roteiro → roteiro-dia-a-dia\n- Preços (#precos-1)\n- Dúvidas\n- Instagram → https://instagram.com/agencia",
    ))
    links = config["sections"][0]["links"]
    assert [(l["label"], l["targetType"], l["target"]) for l in links] == [
        ("Roteiro", "section", "roteiro-dia-a-dia"),
        ("Preços", "section", "precos-1"),
        ("Dúvidas", "section", ""),
        ("Instagram", "external", "https://instagram.com/agencia"),
    ]
    # "Dúvidas" não veio com identificador nem tem seção na resposta: o editor liga pelo título.
    assert links[2]["aiTargetLabel"] == "Dúvidas" and config["sections"][0]["aiSetKeys"] == ["links"]


def test_new_page_menu_still_links_by_title():
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: MENU DO TOPO\nLinks do menu:\n- Roteiro\n- Dúvidas\nLado direito: botão\nBotão: Falar com a gente",
        "🟩 SEÇÃO: ROTEIRO DIA A DIA\nTítulo: Seu roteiro\nDia 1: Chegada",
        "🟩 SEÇÃO: DÚVIDAS FREQUENTES\nTítulo: Dúvidas\nPergunta: Tem seguro?\nResposta: Sim.",
    ))
    header = config["sections"][0]
    itinerary = next(s for s in config["sections"] if s["type"] == "itinerary")
    faq = next(s for s in config["sections"] if s["type"] == "faq")
    assert [l["target"] for l in header["links"]] == [itinerary["anchorId"], faq["anchorId"]]
    assert header["contactLabel"] == "Falar com a gente" and header["actionType"] == "contact"


def test_flight_import_uses_api_for_codes_and_manual_otherwise(db_session, monkeypatch):
    from types import SimpleNamespace

    from app.api.v1.endpoints import flight_sections
    from app.models.flight_section import FlightSectionJourney, FlightSectionSegment
    from app.services.ai_flights import parse_flight_legs

    legs, _ = parse_flight_legs(
        "Ida: 12/07/2026, voo LA3456, São Paulo (GRU) 08:00 → Recife (REC) 11:15\n"
        "Volta: 19/07/2026, Recife (REC) 22:40 → São Paulo (GRU) 02:05 +1, GOL\n"
        "Volta 2: 20/07/2026, voo XX999, São Paulo (GRU) 06:30 → Curitiba (CWB) 07:45\n"
        "Bagagem: 1 mala de 23 kg"
    )

    class FakeLookup:
        def __init__(self, db):
            pass

        def lookup(self, number, day):
            if number != "LA3456":
                raise RuntimeError("voo não encontrado")
            return SimpleNamespace(provider="aerodatabox", raw_response=None, flight={
                "flight_number": "LA3456", "airline_name": "LATAM Airlines", "airline_logo_url": "https://logo/la.png",
                "departure": {"iata": "GRU", "airport": "Guarulhos", "city": "São Paulo", "datetime": "2026-07-12T08:05:00-03:00"},
                "arrival": {"iata": "REC", "airport": "Guararapes", "city": "Recife", "datetime": "2026-07-12T11:20:00-03:00"},
                "duration_minutes": 195,
            })

    monkeypatch.setattr(flight_sections, "FlightLookupService", FakeLookup)
    counts = flight_sections.import_flight_journeys(db_session, 1, "flight-1", legs)
    assert counts == {"from_api": 1, "manual": 2}
    journeys = db_session.query(FlightSectionJourney).filter_by(section_id="flight-1").order_by(FlightSectionJourney.sort_order).all()
    assert [j.direction for j in journeys] == ["outbound", "inbound"]
    ida = db_session.query(FlightSectionSegment).filter_by(journey_id=journeys[0].id).one()
    # Com código: dados da API (logo, aeroporto, horário certo).
    assert ida.source_mode == "aerodatabox" and ida.airline_logo_url == "https://logo/la.png" and ida.departure_airport_name == "Guarulhos"
    assert ida.included_checked_bag is True
    volta = db_session.query(FlightSectionSegment).filter_by(journey_id=journeys[1].id).order_by(FlightSectionSegment.sort_order).all()
    # Sem código, ou código que a API não achou: manual, com o que a mensagem trouxe.
    assert [(s.source_mode, s.departure_airport_iata, s.arrival_airport_iata) for s in volta] == [
        ("manual", "REC", "GRU"), ("manual", "GRU", "CWB"),
    ]
    assert volta[0].arrival_datetime.day == 20 and volta[1].flight_number == "XX999"

    # De novo (troca da seção pelo assistente): substitui, não duplica.
    flight_sections.import_flight_journeys(db_session, 1, "flight-1", legs[:1])
    assert db_session.query(FlightSectionJourney).filter_by(section_id="flight-1").count() == 1


def test_resumo_do_pacote_reads_included_and_excluded_lists():
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: RESUMO DO PACOTE\nEtiqueta: Seu pacote\nTítulo: O que está incluso\nSubtítulo: Confira antes de reservar.\n"
        "Inclui:\n- Hospedagem — 3 noites em Gramado\n- Café da manhã\n- Guia local\n"
        "Não inclui:\n- Passagem aérea\n- Seguro viagem"
    ), strict=True)
    (section,) = config["sections"]
    assert section["type"] == "inclusions"
    assert section["title"] == "O que está incluso"
    assert section["subtitle"] == "Confira antes de reservar."
    assert section["headingLabel"] == "Seu pacote"
    assert section["included"] == [
        {"title": "Hospedagem", "details": "3 noites em Gramado"},
        {"title": "Café da manhã", "details": ""},
        {"title": "Guia local", "details": ""},
    ]
    assert [item["title"] for item in section["excluded"]] == ["Passagem aérea", "Seguro viagem"]


def test_sent_photo_replaces_banner_photo_without_stock_search():
    url = "https://cdn.exemplo.com/uploads/foto_2400.webp"
    config, _ = build_page_base_config_from_reply(reply_with(
        f"🟩 SEÇÃO: BANNER INICIAL\nSubstitui: banner-inicial\nImagem: {url}"
    ), strict=True)
    (hero,) = config["sections"]
    assert hero["backgroundImage"] == url
    assert hero["mobileBackgroundImage"] == url
    assert hero["aiStockPhoto"] is True
    assert hero["photoCredits"] == []
    assert "aiImageQuery" not in hero
    # Só a foto foi pedida: título e textos da seção atual ficam como estão.
    assert hero["aiSetKeys"] == []


def test_sent_photos_fill_story_carousel_and_ignore_invalid_addresses():
    config, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: TEXTO E IMAGENS\nTítulo: Hospedagem\nTexto: Hotel no centro.\n"
        "Imagem: /uploads/a_2400.webp | https://cdn.exemplo.com/b.jpg | javascript:alert(1)"
    ), strict=True)
    (story,) = config["sections"]
    assert story["images"] == ["/uploads/a_2400.webp", "https://cdn.exemplo.com/b.jpg"]
    assert "aiImageQuery" not in story
    no_url, _ = build_page_base_config_from_reply(reply_with(
        "🟩 SEÇÃO: FOTO EM DESTAQUE\nLegenda: Pôr do sol\nImagem: foto do pôr do sol na praia"
    ), strict=True)
    # Sem endereço válido, segue a busca no banco de fotos.
    assert no_url["sections"][0].get("aiStockPhoto") is None
    assert "aiImageQuery" in no_url["sections"][0]


def test_itinerary_day_drops_leaked_prompt_instructions():
    block = (
        "ITINERÁRIO\n"
        "Título: Dia a dia\n"
        "Dia 1: Chegada em Recife (até 7 palavras)\n"
        "descrição do dia na linha seguinte, em 1 a 3 frases\n"
        "Chegada, traslado ao hotel e tarde livre na praia.\n"
        "Dia 2: título curto do dia\n"
        "Passeio de jangada pelas piscinas naturais.\n"
        "(1 a 3 frases)\n"
    )
    config, _ = build_page_base_config_from_reply(reply_with("🟩 SEÇÃO: ROTEIRO DIA A DIA\n" + block), strict=False)
    days = next(section for section in config["sections"] if section["type"] == "itinerary")["days"]
    assert days[0]["title"] == "Chegada em Recife"
    assert days[0]["description"] == "Chegada, traslado ao hotel e tarde livre na praia."
    assert days[1]["description"] == "Passeio de jangada pelas piscinas naturais."
    assert all("1 a 3" not in day["description"] and "linha seguinte" not in day["description"] for day in days)
