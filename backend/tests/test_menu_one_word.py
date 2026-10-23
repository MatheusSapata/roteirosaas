import pytest

from app.services.ai_assistant import FIXED_RULES, _instructions, build_page_base_config_from_reply, one_word_menu_label


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Roteiro", "Roteiro"),
        ("O que inclui", "Inclui"),
        ("Perguntas frequentes", "Dúvidas"),
        ("Roteiro dia a dia", "Roteiro"),
        ("Fale conosco", "Contato"),
        ("Quem somos", "Sobre"),
        ("Nossos depoimentos", "Depoimentos"),
        ("Pacotes nacionais", "Pacotes"),
        ("  Preços  ", "Preços"),
        ("", ""),
    ],
)
def test_nome_do_menu_tem_uma_palavra(label, expected):
    assert one_word_menu_label(label) == expected


def test_regra_fixa_vai_para_a_ia(monkeypatch):
    monkeypatch.setattr("app.services.ai_assistant.load_system_prompt", lambda: "PROMPT")
    assert FIXED_RULES in _instructions("")
    assert _instructions("CONTEXTO").endswith("CONTEXTO")


def test_menu_da_pagina_sai_com_uma_palavra_e_ligado_a_secao():
    reply = (
        "ESTRUTURA SUGERIDA PARA A PÁGINA\n\n"
        "🟩 SEÇÃO: MENU DO TOPO\nLinks do menu:\n- Roteiro dia a dia\n- Perguntas frequentes\n\n"
        "🟩 SEÇÃO: ROTEIRO DIA A DIA\n- Título: Roteiro dia a dia\n- Dia 1: Chegada e check-in\n\n"
        "🟩 SEÇÃO: PERGUNTAS FREQUENTES\n- Título: Perguntas frequentes\n"
        "- Pergunta: Tem guia?\n- Resposta: Sim.\n"
    )
    config, _ = build_page_base_config_from_reply(reply)
    header = next(s for s in config["sections"] if s["type"] == "header")
    labels = [link["label"] for link in header["links"]]
    assert labels == ["Roteiro", "Dúvidas"]
    assert all(link["target"] for link in header["links"])
