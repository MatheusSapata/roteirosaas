from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import base64
import html
from copy import deepcopy
from datetime import datetime, timedelta
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.construtor_prompt import get_active_prompt_text

settings = get_settings()
logger = logging.getLogger(__name__)
BASE_PROMPT_PATH = Path(__file__).resolve().parents[3] / "docs" / "construtor-prompt.md"
EXAMPLES_DIR = BASE_PROMPT_PATH.parent / "prompts" / "examples"
SECTION_COMPONENT_TYPES = {
    "BANNER": "hero",
    "BANNER EM CARD": "banner_card",
    "FOTO DESTACADA": "photo",
    "BIOGRAFIA": "biography",
    "PRECOS": "prices",
    "ITINERARIO": "itinerary",
    "PERGUNTAS FREQUENTES": "faq",
    "DEPOIMENTOS": "testimonials",
    "VIDEO EM DESTAQUE": "featured_video",
    "CHAMADA PARA ACAO": "cta",
    "DESCRITIVO": "story",
    "ITENS": "reasons",
    "CONTADOR": "countdown",
    "DETALHES DO VOO": "flight_details",
}
ALLOWED_SECTION_NAMES = frozenset(SECTION_COMPONENT_TYPES)
FORBIDDEN_SECTION_NAMES = frozenset({"CHECKOUT VIAJEON"})
SECTION_NAME_ALIASES = {
    "BANNER INICIAL": "BANNER",
    "BANNER DESTACADO": "BANNER EM CARD",
    "SESSAO DESCRITIVA": "DESCRITIVO",
    "CONTAGEM REGRESSIVA": "CONTADOR",
    "VIDEO": "VIDEO EM DESTAQUE",
}
MODEL_PRICING_USD = {
    "gpt-4": {"input": 30.0, "cached_input": 0.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "cached_input": 0.0, "output": 30.0},
    "gpt-4o": {"input": 2.5, "cached_input": 1.25, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.6},
    "gpt-4.1": {"input": 2.0, "cached_input": 0.5, "output": 8.0},
    "gpt-4.1-mini": {"input": 0.4, "cached_input": 0.1, "output": 1.6},
    "gpt-4.1-nano": {"input": 0.1, "cached_input": 0.025, "output": 0.4},
    "gpt-5.1": {"input": 1.25, "cached_input": 0.13, "output": 7.5},
    "gpt-5.5": {"input": 5.0, "cached_input": 0.5, "output": 30.0},
    "gpt-5.5-pro": {"input": 30.0, "cached_input": 0.0, "output": 180.0},
    "gpt-5.4": {"input": 1.25, "cached_input": 0.13, "output": 7.5},
    "gpt-5.4-mini": {"input": 0.375, "cached_input": 0.0375, "output": 2.25},
}
FIELD_ALIASES = {
    "TIPO DE PAGINA": "page_type",
    "OBJETIVO DA PAGINA": "page_goal",
    "PUBLICO PREDOMINANTE": "audience",
    "SECOES ESCOLHIDAS": "chosen_sections",
    "FUNCAO DA SECAO": "section_function",
    "CONTEUDO": "content",
    "ETIQUETA": "label",
    "TITULO": "title",
    "TITULO DA SECAO": "title",
    "SUBTITULO": "subtitle",
    "SUBTITULO OU TEXTO DESCRITIVO": "subtitle",
    "DESTAQUES": "highlights",
    "BOTAO": "button",
    "SUGESTAO DE IMAGEM OU VIDEO": "media_suggestion",
    "SUGESTAO DE IMAGEM": "image_suggestion",
    "NOME DO PLANO": "plan_name",
    "VALOR": "value",
    "OBSERVACAO": "note",
    "PERGUNTA": "question",
    "RESPOSTA": "answer",
    "DIA": "day",
    "LINK": "link",
    "TEXTO": "text",
    "TEXTO DESCRITIVO": "text",
    "CARGO": "role",
    "DESCRICAO": "description",
    "ICONE": "icon",
    "BOTAO CTA": "button",
    "INFORMACOES GERAIS": "general_info",
    "DATA DE SAIDA": "departure_date",
    "DATA DE IDA": "departure_date",
    "DATA DE VOLTA": "return_date",
    "DATA DE RETORNO": "return_date",
    "FORMAS DE PAGAMENTO": "payment_methods",
    "FORMA DE PAGAMENTO": "payment_methods",
    "PARCELAMENTO": "installments",
}
# Rótulos com variações ("Nome do plano ou pacote", "Título da seção", "Link ou referência do
# vídeo"): o prompt do superadmin pode descrever os campos com outras palavras, e um rótulo não
# reconhecido virava texto da página (ex.: "Diferenciais ou observação do plano: ..." no preço).
FIELD_ALIASES_EXACT_EXTRA = {
    "PLANO": "plan_name",
    "PACOTE": "plan_name",
    "SELO": "badge",
    "DESTAQUE": "plan_highlight",
    "PLANO EM DESTAQUE": "plan_highlight",
    "ANTES DO VALOR": "price_label",
    "TEXTO ANTES DO VALOR": "price_label",
    "CONDICOES": "note",
    "DETALHES": "note",
    "DEPOIMENTO": "text",
    "AVALIACAO": "rating",
    "LEGENDA": "caption",
    "LAYOUT": "layout",
    "TIPO DE LAYOUT": "layout",
    "LINK DO VIDEO": "link",
    "DATA FINAL": "target_date",
    "DATA E HORARIO": "target_date",
    "DATA E HORA": "target_date",
}
FIELD_ALIAS_PREFIXES = (
    ("NOME DO PLANO", "plan_name"),
    ("NOME DO PACOTE", "plan_name"),
    ("DIFERENCIAIS", "note"),
    ("OBSERVACAO DO PLANO", "note"),
    ("OBSERVACAO DO PACOTE", "note"),
    ("CONDICOES DO PLANO", "note"),
    ("DESCRICAO DO PLANO", "note"),
    ("OBSERVACAO GERAL", "general_note"),
    ("OBSERVACOES GERAIS", "general_note"),
    ("CONDICOES GERAIS", "general_note"),
    ("NOTA GERAL", "general_note"),
    ("IDENTIFICACAO", "role"),
    ("DATA DE ENCERRAMENTO", "target_date"),
    ("DATA LIMITE", "target_date"),
    ("DATA DO CONTADOR", "target_date"),
    ("LINK", "link"),
    ("SUGESTAO DE ICONE", "icon"),
    ("SUGESTAO DE IMAGEM", "image_suggestion"),
    ("SUGESTAO DE FOTO", "image_suggestion"),
    ("BOTAO", "button"),
    ("TEXTO DO BOTAO", "button"),
    ("SUBTITULO", "subtitle"),
    ("TITULO", "title"),
    ("TEXTO", "text"),
    ("DESCRICAO", "description"),
    ("FUNCAO", "section_function"),
    ("ETIQUETA", "label"),
)


def _field_alias(label: str) -> str | None:
    key = _normalize_text(label)
    if key in FIELD_ALIASES:
        return FIELD_ALIASES[key]
    if key in FIELD_ALIASES_EXACT_EXTRA:
        return FIELD_ALIASES_EXACT_EXTRA[key]
    for prefix, alias in FIELD_ALIAS_PREFIXES:
        if key.startswith(prefix):
            return alias
    return None


REQUIRED_HEADER = "ESTRUTURA SUGERIDA PARA A P\u00c1GINA"
SECTION_LINE_RE = re.compile(r"^\s*(?:.*?SE\u00c7\u00c3O:\s*)?(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
SECTION_SPLIT_RE = re.compile(r"(?=^\s*(?:.*?SE\u00c7\u00c3O:\s+))", re.IGNORECASE | re.MULTILINE)
SECTION_HEADER_RE = re.compile(r"^\s*(?:🟩\s*)?(?:SECAO|SE\u00c7\u00c3O)\s*:\s*(.+?)\s*$", re.IGNORECASE)
SECTION_HEADER_PREFIX_RE = re.compile(r"^\s*(?:🟩\s*)?", re.IGNORECASE)
DEFAULT_PROMPT = """Você é o Consultor Oficial do Construtor Roteiro Online.

Sua função é ajudar agências de viagens, excursões, receptivos turísticos e especialistas em turismo a construir páginas de vendas altamente persuasivas, emocionais, organizadas e fáceis de montar dentro da plataforma Roteiro Online.

Você não é apenas um copywriter. Você é um consultor estratégico especialista em turismo, experiência do usuário, conversão e vendas.

Sua missão é analisar as informações enviadas pelo usuário, entender o tipo de viagem e desenvolver a estrutura ideal da página, escolhendo estrategicamente quais seções utilizar e entregando todos os textos prontos para copiar e colar.

REGRA CRÍTICA DE SAÍDA

A resposta deve usar SOMENTE estes nomes de seção:

BANNER
BANNER EM CARD
FOTO DESTACADA
DESCRITIVO
ITINERÁRIO
PREÇOS
PERGUNTAS FREQUENTES
DEPOIMENTOS
VÍDEO EM DESTAQUE
BIOGRAFIA
CHAMADA PARA AÇÃO
ITENS
CONTADOR
DETALHES DO VOO

Nunca crie nomes como:
O que está incluso
Benefícios
Para quem é
Diferenciais
Hospedagem
Investimento e condições
Chamada rápida
Por que viajar com a agência

Esses temas devem ser desenvolvidos usando DESCRITIVO, ITENS ou a seção correta existente.

Nunca sugira nem gere CHECKOUT VIAJEON. O rodapé da agência é adicionado automaticamente pela plataforma.

Se a resposta usar qualquer nome de seção fora da lista permitida, ela está incorreta.

Regras finais de precisão:
- Use os nomes de seção exatamente como estão escritos acima.
- Nunca crie variações, apelidos, traduções ou complementos no nome da seção.
- Quando o conteúdo for de roteiro dia a dia, use sempre ITINERÁRIO como nome da seção.
- Nunca use títulos como ROTEIRO DIA A DIA, PROGRAMAÇÃO DIA A DIA, DIA A DIA ou qualquer variação semelhante como nome de seção.
"""


# Formato que a montagem automática da página entende. Vai sempre depois do prompt do
# superadmin (que cuida do tom e da estratégia): editar o prompt não quebra a montagem.
PLATFORM_FORMAT_CONTRACT = """FORMATO DE ENTREGA PARA A MONTAGEM AUTOMÁTICA (prevalece sobre qualquer instrução anterior sobre nomes de seções e campos)

A resposta é lida por um programa que monta a página. Escreva cada campo numa linha própria, no formato "Campo: valor", usando exatamente os nomes de campo abaixo. Não invente campos. Campo sem informação real: omita a linha inteira (não escreva "não informado", "preencher" ou colchetes).

A primeira linha é "ESTRUTURA SUGERIDA PARA A PÁGINA". Depois: "Tipo de página:", "Objetivo da página:", "Público predominante:". Cada seção começa com "🟩 SEÇÃO: NOME", com um destes nomes: BANNER, BANNER EM CARD, FOTO DESTACADA, DESCRITIVO, ITENS, ITINERÁRIO, PREÇOS, PERGUNTAS FREQUENTES, DEPOIMENTOS, VÍDEO EM DESTAQUE, BIOGRAFIA, CHAMADA PARA AÇÃO, CONTADOR, DETALHES DO VOO. Logo abaixo do cabeçalho, "Função da seção:" (não aparece na página) e depois os campos.

Campos de cada seção (Etiqueta é um selo curto de 1 a 3 palavras acima do título):

BANNER: Título (curto, até 8 palavras), Subtítulo (1 ou 2 frases), Destaques (3 a 5 itens curtos, um por linha começando com "- ", até 4 palavras cada; não repita as datas), Data de saída e Data de volta (DD/MM/AAAA, só se a viagem tiver datas), Botão, Sugestão de imagem.

BANNER EM CARD: Etiqueta, Título, Subtítulo, Botão, Sugestão de imagem.

FOTO DESTACADA: Legenda (frase curta que aparece embaixo da foto), Layout (card ou largura total), Sugestão de imagem.

DESCRITIVO: Etiqueta, Título, Texto (2 a 4 parágrafos curtos; inclusos e diferenciais entram aqui em texto corrido), Botão (opcional), Sugestão de imagem.

ITENS: Etiqueta, Título, Subtítulo, e de 3 a 6 itens, cada um assim:
Item: título curto (até 4 palavras)
Descrição: uma frase objetiva
Ícone: um destes nomes: plane, hotel, bed, bus, train-front, coffee, utensils, user-check, shield-check, camera, ticket, users, calendar-days, ship, sailboat, tree-palm, mountain, church, credit-card, headset, waves, wine, ferris-wheel, snowflake, map-pin, clock, sparkles, circle-check, star, heart, route, luggage, baby, map, compass, sun

ITINERÁRIO: Etiqueta, Título, Subtítulo, e um bloco por dia:
Dia 1: título curto do dia (até 7 palavras)
descrição do dia na linha seguinte, em 1 a 3 frases
(Sem dias definidos, use "Dia 1", "Dia 2"... na ordem das etapas. Nunca liste os dias duas vezes.)

PREÇOS: Etiqueta, Título, Subtítulo (opcional), e um bloco por plano, cada um começando por "Plano:":
Plano: nome do plano (ex.: Adulto, Criança de 6 a 12 anos, Quarto duplo)
Selo: texto curto como "Mais vendido" (opcional, no máximo um plano)
Destaque: sim (opcional, só no plano principal)
Antes do valor: ex. "A partir de" (opcional)
Valor: só o valor informado, ex. "R$ 299,00 por pessoa"
Parcelamento: ex. "em até 10x sem juros" (só se informado)
Detalhes: o que diferencia este plano, em uma frase
Depois de todos os planos (uma vez só): Formas de pagamento (só se informadas) e Observação geral (ex.: "Consulte disponibilidade, formas de pagamento e condições vigentes.").
Cada faixa de preço (adulto, criança, colo) é um plano separado. Nunca coloque vários planos ou valores dentro de um mesmo plano.

PERGUNTAS FREQUENTES: Etiqueta, Título, e pares "Pergunta:" / "Resposta:" (3 a 6).

DEPOIMENTOS (só com depoimentos reais enviados): Etiqueta, Título, e para cada um: Nome, Identificação (opcional, ex.: "Viajou em julho de 2025"), Depoimento.

VÍDEO EM DESTAQUE (só com link real): Etiqueta, Título, Subtítulo, Link (URL completa), Botão (opcional).

BIOGRAFIA: Título, Texto, Sugestão de imagem.

CHAMADA PARA AÇÃO: Etiqueta, Título, Descrição (1 frase), Botão.

CONTADOR (só com data real de encerramento): Etiqueta, Título (ex.: "O lote promocional termina em"), Data final (DD/MM/AAAA HH:MM).

DETALHES DO VOO (só com dados aéreos enviados): Título, e as linhas confirmadas, como "Ida: 12/07/2026, São Paulo (GRU) 08:00 → Recife (REC) 11:15, LATAM, voo direto", "Volta: ...", "Bagagem: ...".

O rodapé da agência é automático. Não use CHECKOUT VIAJEON. Não use tabelas, JSON, negrito em nomes de campo nem cabeçalhos com #."""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@dataclass(slots=True)
class ChatAttachment:
    filename: str
    content_type: str | None
    data: bytes


def load_system_prompt() -> str:
    prompt = get_active_prompt_text(create_if_missing=True).strip() or DEFAULT_PROMPT.strip()
    return f"{prompt}\n\n{PLATFORM_FORMAT_CONTRACT}"


def _looks_like_text(content_type: str | None, filename: str) -> bool:
    lowered_name = filename.lower()
    if content_type:
        normalized = content_type.lower()
        if normalized.startswith("text/"):
            return True
        if normalized in {"application/json", "application/xml", "application/javascript"}:
            return True
        if normalized in {"application/csv", "text/csv"}:
            return True
    return lowered_name.endswith((".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".yaml", ".yml"))


def _load_openai_client():
    if not settings.gpt_key:
        raise HTTPException(status_code=503, detail="GPT_KEY não configurada no backend.")
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise HTTPException(status_code=503, detail="Dependência openai não instalada.") from exc
    return OpenAI(api_key=settings.gpt_key)


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return ""

    parts: list[str] = []
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type != "message":
            continue
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for block in content:
            block_type = getattr(block, "type", None)
            if block_type != "output_text":
                continue
            text = getattr(block, "text", None)
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def _validate_ai_reply_format(reply: str) -> tuple[bool, str]:
    normalized_reply = reply.strip()
    if not normalized_reply:
        return False, "A resposta veio vazia."

    total_sections = 0
    valid_sections = 0
    for line in normalized_reply.splitlines():
        match = SECTION_HEADER_RE.match(line)
        if not match:
            continue
        total_sections += 1
        raw_name = match.group(1).strip()
        normalized_name = _normalize_text(_strip_surrounding_markdown(raw_name))
        canonical_name = _canonical_section_name(raw_name)
        alias_used = normalized_name in SECTION_NAME_ALIASES
        forbidden = normalized_name in FORBIDDEN_SECTION_NAMES
        status = "accepted" if canonical_name else ("forbidden" if forbidden else "ignored")
        if canonical_name:
            valid_sections += 1
        logger.info(
            "ai_section_header original=%r normalized=%r alias=%s final=%r component=%r status=%s",
            line.strip(),
            normalized_name,
            alias_used,
            canonical_name,
            SECTION_COMPONENT_TYPES.get(canonical_name or ""),
            status,
        )

    logger.info("ai_section_summary total=%d valid=%d", total_sections, valid_sections)
    if total_sections == 0:
        return False, "Nenhum bloco de seção foi encontrado."
    if valid_sections == 0:
        return False, "Nenhuma seção válida pôde ser extraída da resposta."

    return True, ""


def _build_correction_instructions(validation_error: str) -> str:
    return (
        f"{load_system_prompt()}\n\n"
        "Sua última resposta está incorreta e precisa ser reescrita do zero.\n\n"
        f"Problema detectado: {validation_error}\n\n"
        "Regras obrigatórias:\n"
        f"- Comece exatamente com '{REQUIRED_HEADER}'.\n"
        "- Use somente seções permitidas.\n"
        "- Não use JSON.\n"
        "- Não explique as regras.\n"
        "- Entregue apenas a resposta final em texto puro.\n"
    )


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", stripped).upper().strip()


def _strip_markdown_emphasis(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    text = re.sub(r"(?<!\w)_(?!\s)|(?<!\s)_(?!\w)", "", text)
    return text.strip()


def _strip_surrounding_markdown(value: str) -> str:
    text = (value or "").strip()
    wrappers = (("**", "**"), ("__", "__"), ("*", "*"), ("_", "_"), ("`", "`"))
    changed = True
    while changed and text:
        changed = False
        for opening, closing in wrappers:
            if text.startswith(opening) and text.endswith(closing) and len(text) >= len(opening) + len(closing):
                text = text[len(opening):-len(closing)].strip()
                changed = True
                break
    return text


def _canonical_section_name(section_name: str) -> str | None:
    normalized = _normalize_text(_strip_surrounding_markdown(section_name))
    canonical = SECTION_NAME_ALIASES.get(normalized, normalized)
    return canonical if canonical in ALLOWED_SECTION_NAMES else None


def _normalize_label_line(text: str) -> str:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines = [_strip_markdown_emphasis(line) for line in normalized.splitlines()]
    return "\n".join(cleaned_lines)


def _extract_first_match(block: str, label: str) -> str:
    fields = _parse_key_value_lines(block)
    return fields.get(_field_alias(label) or "", "").strip()


def _split_sections(reply: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    normalized = (reply or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()

    intro_lines: list[str] = []
    parsed_sections: list[tuple[str, str]] = []
    current_name: str | None = None
    current_body: list[str] = []
    saw_section = False
    total_sections = 0

    for line in lines:
        match = SECTION_HEADER_RE.match(line)
        if match:
            saw_section = True
            total_sections += 1
            if current_name:
                parsed_sections.append((current_name, "\n".join(current_body).strip()))
            current_body = []
            raw_section_name = match.group(1).strip()
            current_name = _canonical_section_name(raw_section_name)
            normalized_name = _normalize_text(_strip_surrounding_markdown(raw_section_name))
            status = "accepted" if current_name else ("forbidden" if normalized_name in FORBIDDEN_SECTION_NAMES else "ignored")
            logger.info(
                "ai_section_parser original=%r normalized=%r alias=%s final=%r component=%r status=%s",
                line.strip(),
                normalized_name,
                normalized_name in SECTION_NAME_ALIASES,
                current_name,
                SECTION_COMPONENT_TYPES.get(current_name or ""),
                status,
            )
            continue

        if not saw_section:
            intro_lines.append(line)
            continue

        if current_name:
            current_body.append(line)

    if current_name:
        parsed_sections.append((current_name, "\n".join(current_body).strip()))

    logger.info("ai_section_parser_summary total=%d valid=%d", total_sections, len(parsed_sections))

    intro_text = "\n".join(intro_lines).strip()
    intro_fields = _parse_key_value_lines(intro_text)
    meta = {
        "Tipo de página": intro_fields.get("page_type", ""),
        "Objetivo da página": intro_fields.get("page_goal", ""),
        "Público predominante": intro_fields.get("audience", ""),
        "Seções escolhidas": intro_fields.get("chosen_sections", ""),
    }
    return meta, parsed_sections


def _split_bullets(value: str) -> list[str]:
    normalized = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("•", "\n").replace("‣", "\n")
    items: list[str] = []
    for line in normalized.splitlines():
        cleaned = re.sub(r"^\s*[-*•‣]\s*", "", line).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _parse_key_value_lines(text: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current_key: str | None = None
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    for raw_line in normalized.splitlines():
        line = _strip_markdown_emphasis(raw_line.strip())
        line = re.sub(r"^[-*•‣]\s+", "", line).strip()
        if not line:
            if current_key:
                result.setdefault(current_key, []).append("")
            continue

        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if match:
            alias = _field_alias(match.group(1))
            if alias:
                current_key = alias
                result.setdefault(alias, [])
                value = match.group(2).strip()
                if value:
                    result[alias].append(value)
                continue

        if current_key:
            result.setdefault(current_key, []).append(line)

    return {key: "\n".join(value).strip() for key, value in result.items()}


def _parse_price_value(value: str) -> float:
    # Read one amount, without joining installment counts or other numbers.
    amount_text = (value or "").split("R$", 1)[-1]
    match = re.search(r"\d+(?:\.\d{3})*(?:,\d{1,2})?", amount_text)
    if not match:
        return 0.0
    digits = match.group(0)
    digits = digits.replace(".", "").replace(",", ".")
    try:
        return float(digits)
    except ValueError:
        return 0.0


MONTHS_PT = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}


def _parse_trip_date(value: str) -> str:
    """Data da viagem no formato da página (AAAA-MM-DD). Só aceita datas com ano."""
    text = _normalize_text(value or "")
    match = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", text)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    else:
        match = re.search(r"\b(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+(\d{4})\b", text)
        if not match or match.group(2) not in MONTHS_PT:
            return ""
        day, month, year = int(match.group(1)), MONTHS_PT[match.group(2)], int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return ""


PAYMENT_KEYWORDS = (
    ("pix", r"\bPIX\b"),
    ("boleto", r"\bBOLETO"),
    ("cartao", r"\bCARTAO|\bCREDITO\b"),
    ("visa", r"\bVISA\b"),
    ("mastercard", r"\bMASTER"),
    ("elo", r"\bELO\b"),
    ("amex", r"\bAMEX\b|AMERICAN EXPRESS"),
    ("hipercard", r"\bHIPER"),
    ("diners", r"\bDINERS\b"),
)


def _parse_payment_methods(value: str) -> tuple[list[str], str]:
    """Formas de pagamento citadas no texto e a condição de parcelamento, se houver."""
    text = _normalize_text(value or "")
    methods = [method for method, pattern in PAYMENT_KEYWORDS if re.search(pattern, text)]
    if any(brand in methods for brand in ("visa", "mastercard", "elo", "amex", "hipercard", "diners")) and "cartao" not in methods:
        methods.append("cartao")
    order = [method for method, _ in PAYMENT_KEYWORDS]
    methods.sort(key=order.index)
    installment = re.search(r"(?:em\s+ate\s+|ate\s+)?\d{1,2}\s*x[^.;,\n]*", text, re.I)
    note = ""
    if installment:
        original = value or ""
        raw = re.search(r"(?:em\s+at[eé]\s+|at[eé]\s+)?\d{1,2}\s*x[^.;,\n]*", original, re.I)
        note = (raw.group(0) if raw else installment.group(0)).strip()
        note = note[:1].upper() + note[1:]
    return methods, note


def _split_price_text(value: str) -> tuple[str, str]:
    """Separa o que vem antes do valor ("a partir de") e depois ("por pessoa")."""
    text = (value or "").strip()
    match = re.search(r"R\$\s*\d+(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:\.\d{3})*,\d{2}", text)
    if not match:
        return "", ""
    before = text[: match.start()].strip(" :-–")
    after = text[match.end():].strip(" :-–")
    label = before[:1].upper() + before[1:] if before else ""
    return label, after


def _itinerary_day_content(body: str) -> tuple[str, str]:
    lines = [
        _strip_markdown_emphasis(line.strip())
        for line in body.splitlines()
        if line.strip() and not re.fullmatch(r"\s*(?:[-*_]\s*){3,}", line)
    ]
    if not lines:
        return "Programação do dia", ""
    first = re.sub(r"^(?:[-*•]\s*)?(?:Título|Titulo)\s*:\s*", "", lines[0], flags=re.I)
    # Keep a supplied short heading; otherwise summarize without dropping details.
    if len(lines) > 1 and len(first) <= 65 and len(first.split()) <= 9:
        description = "\n".join(lines[1:])
        description = re.sub(r"^(?:Descrição|Descricao)\s*:\s*", "", description, flags=re.I)
        return first, description
    description = "\n".join(lines)
    normalized = _normalize_text(description)
    if "CHECK-OUT" in normalized or "RETORNO PARA CASA" in normalized:
        title = "Check-out e retorno" if "CHECK-OUT" in normalized else "Retorno para casa"
    elif "EMBARQUE" in normalized:
        title = "Embarque e traslado" if "TRASLADO" in normalized else "Embarque e início da viagem"
    elif "PASSEIO OPCIONAL" in normalized:
        title = "Passeio opcional"
    elif "DIA LIVRE" in normalized:
        title = "Dia livre e piscinas naturais" if "PISCINAS NATURAIS" in normalized else "Dia livre para aproveitar"
    elif "COMPRAS" in normalized and "GASTRONOM" in normalized:
        title = "Compras e gastronomia"
    else:
        sentence = re.split(r"[.!?;]\s*", first, maxsplit=1)[0]
        words = sentence.split()
        title = " ".join(words[:7])
        if len(title) > 60:
            title = title[:60].rsplit(" ", 1)[0]
        if title != sentence:
            title = title.rstrip(",:;") + "…"
        elif title.strip() == description.strip():
            title = "Programação do dia"
    return title, description


def _parse_countdown_date(value: str) -> str:
    """Data e hora do fim do contador ("20/12/2026 23:59", horário de Brasília) em ISO UTC."""
    day = _parse_trip_date(value)
    if not day:
        return ""
    time_match = re.search(r"\b(\d{1,2})\s*(?:h|:)\s*(\d{2})?\b", re.sub(r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}", "", value or ""), re.I)
    hour, minute = (int(time_match.group(1)), int(time_match.group(2) or 0)) if time_match else (23, 59)
    if hour > 23 or minute > 59:
        hour, minute = 23, 59
    local = datetime.strptime(day, "%Y-%m-%d").replace(hour=hour, minute=minute)
    return (local + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _flight_info_text(block: str) -> str:
    """Dados do voo enviados pela IA ("Companhia aérea: ...", "Ida: ..."), um por linha."""
    lines: list[str] = []
    for raw_line in (block or "").splitlines():
        line = _structure_line(raw_line)
        if not line:
            continue
        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if match and _field_alias(match.group(1)) in {"title", "subtitle", "label", "section_function", "content", "button"}:
            continue
        if match and not match.group(2).strip():
            lines.append(match.group(1).strip() + ":")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _is_yes(value: str) -> bool:
    return _normalize_text(value or "").rstrip(".!") in {"SIM", "S", "YES", "TRUE", "X", "DESTAQUE", "EM DESTAQUE"}

# Ícones da biblioteca do editor ("icon:<nome>") que a IA pode escolher, com palavras que os
# indicam quando ela não escolhe (destaques do Banner e cards de Itens).
AI_ICON_KEYWORDS: dict[str, tuple[str, ...]] = {
    "plane": ("AEREO", "AEREA", "VOO", "VOOS", "PASSAGEM", "PASSAGENS", "AVIAO"),
    "hotel": ("HOTEL", "RESORT"),
    "bed": ("HOSPEDAGEM", "POUSADA", "NOITE", "NOITES", "DIARIA", "DIARIAS", "ACOMODACAO"),
    "bus": ("ONIBUS", "TRANSPORTE", "RODOVIARIO", "RODOVIARIA", "TRASLADO", "TRASLADOS", "TRANSFER", "VAN"),
    "coffee": ("CAFE",),
    "utensils": ("REFEICAO", "REFEICOES", "ALMOCO", "ALMOCOS", "JANTAR", "JANTARES", "GASTRONOMIA", "PENSAO", "ALL INCLUSIVE"),
    "user-check": ("GUIA", "GUIAS", "ACOMPANHANTE", "COORDENADOR", "COORDENACAO", "MONITOR", "MONITORES"),
    "shield-check": ("SEGURO", "SEGURANCA"),
    "train-front": ("TREM", "TRENS", "MARIA FUMACA"),
    "ship": ("CRUZEIRO", "NAVIO"),
    "sailboat": ("BARCO", "LANCHA", "ESCUNA", "CATAMARA"),
    "camera": ("PASSEIO", "PASSEIOS", "CITY TOUR", "TOUR", "TOURS", "FOTOS"),
    "ticket": ("INGRESSO", "INGRESSOS", "ENTRADA", "ENTRADAS"),
    "users": ("GRUPO", "GRUPOS", "FAMILIA", "FAMILIAS"),
    "calendar-days": ("DATA", "DATAS", "FERIADO", "DIAS", "SAIDA", "SAIDAS"),
    "tree-palm": ("PRAIA", "PRAIAS", "LITORAL"),
    "mountain": ("SERRA", "MONTANHA", "MONTANHAS", "TRILHA", "TRILHAS"),
    "church": ("IGREJA", "SANTUARIO", "PEREGRINACAO", "MISSA", "RELIGIOSO", "RELIGIOSA", "FE"),
    "credit-card": ("PARCELA", "PARCELAS", "PARCELAMENTO", "CARTAO", "PAGAMENTO", "PIX", "SEM JUROS"),
    "headset": ("ATENDIMENTO", "SUPORTE", "ASSISTENCIA"),
    "waves": ("PISCINA", "PISCINAS", "AGUAS", "PARQUE AQUATICO"),
    "wine": ("VINHO", "VINHOS", "VINICOLA", "VINICOLAS"),
    "ferris-wheel": ("PARQUE", "PARQUES", "DISNEY"),
    "snowflake": ("NEVE", "INVERNO"),
    "map-pin": ("DESTINO", "LOCALIZACAO", "CENTRO"),
    "clock": ("HORARIO", "HORARIOS", "PONTUALIDADE"),
    "sparkles": ("EXPERIENCIA", "EXPERIENCIAS", "EXCLUSIVO", "EXCLUSIVA", "INESQUECIVEL"),
}
AI_ICON_NAMES = frozenset(AI_ICON_KEYWORDS) | frozenset({"circle-check", "star", "heart", "route", "luggage", "baby", "map", "compass", "sun"})


def _ai_icon_value(raw: str, *texts: str) -> str:
    """Ícone escolhido pela IA ("plane", "icon:plane" ou emoji); sem escolha válida, deduz pelo texto."""
    value = (raw or "").strip().strip("`\"'")
    name = value[5:] if value.lower().startswith("icon:") else value
    if name.lower() in AI_ICON_NAMES:
        return f"icon:{name.lower()}"
    # Emoji curto (sem letras), como "✈️": continua emoji.
    if value and len(value) <= 4 and not re.search(r"[A-Za-z0-9À-ÿ]", value):
        return value
    # O título decide antes da descrição ("Refeições: café da manhã e jantares" → talheres).
    for text in texts:
        haystack = " " + re.sub(r"[^A-Z ]", " ", _normalize_text(text or "")) + " "
        for icon, words in AI_ICON_KEYWORDS.items():
            if any(f" {word} " in haystack for word in words):
                return f"icon:{icon}"
    return ""


def _slug_from_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _generate_anchor(section_type: str, title: str, index: int) -> str:
    base = _slug_from_text(title) or section_type
    return f"{base}-{index + 1}"


def _structure_line(raw_line: str) -> str:
    return re.sub(r"^(?:[-*+•‣]|\d+[.)])\s+", "", _strip_markdown_emphasis(raw_line.strip())).strip()


ITINERARY_DAY_RE = re.compile(r"^Dia\s*(\d+)\s*(?:\(([^)]+)\)\s*)?:\s*(.*)$", re.I)


def _parse_reason_items(block: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] = {}
    inside_list = False

    def flush() -> None:
        nonlocal current
        if current.get("title"):
            item = {"title": current["title"]}
            if current.get("description"):
                item["description"] = current["description"]
            if current.get("icon"):
                item["icon"] = current["icon"]
            items.append(item)
        current = {}

    for raw_line in (block or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = _structure_line(raw_line)
        normalized_line = _normalize_text(line)
        if normalized_line.rstrip(":") in {"LISTA DE ITENS", "ITENS"}:
            inside_list = True
            continue
        if re.match(r"^ITEM(?:\s+\d+)?\s*:", normalized_line):
            flush()
            inside_list = True
            inline_title = line.split(":", 1)[1].strip() if ":" in line else ""
            if inline_title:
                current["title"] = inline_title
            continue
        if not inside_list:
            continue
        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if not match:
            if line and re.match(r"^\s*(?:[-*+•‣]|\d+[.)])\s+", raw_line):
                flush()
                current["title"] = line
            elif current.get("title") and line:
                current["description"] = f"{current.get('description', '')}\n{line}".strip()
            continue
        key = _field_alias(match.group(1))
        value = match.group(2).strip()
        if key == "title":
            if current.get("title"):
                flush()
            current["title"] = value
        elif key in {"description", "icon"}:
            current[key] = value
        elif key in {"label", "subtitle", "button", "image_suggestion", "section_function", "content"}:
            flush()
            inside_list = False
        else:
            # "Transporte: ida e volta" é um item (título: descrição), mesmo que a palavra
            # coincida com algum rótulo de outra seção.
            flush()
            current = {"title": match.group(1).strip(), "description": value}
    flush()
    return items


def _parse_ai_section_block(section_name: str, block: str, index: int) -> dict[str, Any] | None:
    normalized_name = _normalize_text(section_name)
    header_lines = []
    for raw_line in block.splitlines():
        line = _structure_line(raw_line)
        if normalized_name == "ITINERARIO" and ITINERARY_DAY_RE.match(line):
            break
        if normalized_name == "ITENS" and (
            _normalize_text(line).rstrip(":") in {"LISTA DE ITENS", "ITENS"}
            or re.match(r"^ITEM(?:\s+\d+)?\s*:", line, re.I)
        ):
            break
        header_lines.append(raw_line)
    fields = _parse_key_value_lines("\n".join(header_lines))

    if normalized_name == _normalize_text("BANNER"):
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        highlights_source = fields.get("highlights", "").strip()
        cta_label = fields.get("button", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        if not subtitle and content and content != title:
            subtitle = content
        highlights = _split_bullets(highlights_source)
        if not highlights and content:
            highlights = _split_bullets(content)
        # Datas da viagem alimentam o cartão de datas da capa e o calendário do roteiro dia a dia.
        departure_date = _parse_trip_date(fields.get("departure_date", ""))
        return_date = _parse_trip_date(fields.get("return_date", ""))
        trip_dates = {"departureDate": departure_date} if departure_date else {}
        if departure_date and return_date and return_date >= departure_date:
            trip_dates["returnDate"] = return_date
        chip_icons = [_ai_icon_value("", chip) for chip in highlights]
        if any(chip_icons):
            trip_dates["chipIcons"] = chip_icons
        return {
            **trip_dates,
            "type": "hero",
            "enabled": True,
            "anchorId": _generate_anchor("hero", title or "banner-inicial", index),
            "layout": "immersive",
            "title": title or "Banner inicial",
            "subtitle": subtitle or "",
            "chips": highlights,
            "ctaLabel": cta_label or "Saiba mais",
            "ctaMode": "link",
            "ctaLink": "",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
            "backgroundImage": "",
            "mobileBackgroundImage": "",
            "enableAnimation": False,
        }

    if normalized_name == _normalize_text("BANNER EM CARD"):
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        if not subtitle and content and content != title:
            subtitle = content
        return {
            "type": "banner_card",
            "enabled": True,
            "anchorId": _generate_anchor("banner-card", title or "banner-destacado", index),
            "title": title or "Banner destacado",
            "subtitle": subtitle or "",
            "backgroundImage": "",
            "ctaEnabled": False,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("FOTO DESTACADA"):
        image = fields.get("image_suggestion", "").strip() or fields.get("link", "").strip()
        caption = fields.get("caption", "").strip() or fields.get("title", "").strip() or fields.get("subtitle", "").strip()
        layout_text = _normalize_text(fields.get("layout", ""))
        return {
            "type": "photo",
            "enabled": True,
            "anchorId": _generate_anchor("photo", caption or "foto-destacada", index),
            "image": image,
            "layout": "full" if ("LARGURA" in layout_text or "FULL" in layout_text or "TOTAL" in layout_text) else "card",
            "caption": caption,
            "altText": caption or image,
        }

    if normalized_name == _normalize_text("DESCRITIVO"):

        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        body = subtitle or fields.get("text", "").strip() or fields.get("description", "").strip() or content
        return {
            "type": "story",
            "enabled": True,
            "anchorId": _generate_anchor("story", title or label or "sessao-descritiva", index),
            "layout": "single",
            "imagePosition": "right",
            "badge": label or "",
            "title": title or "Seção descritiva",
            "subtitle": body or "",
            "ctaEnabled": False,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
            "ctaLink": "",
            "ctaLabel": "",
            "ctaColor": "",
            "images": [],
            "videoUrls": [],
            "videoUrl": "",
            "backgroundColor": "",
            "borderEnabled": False,
            "borderColor": "",
        }

    if normalized_name == _normalize_text("ITINERARIO"):

        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        days: list[dict[str, Any]] = []
        day_blocks: list[tuple[str, str, list[str]]] = []
        for raw_line in block.splitlines():
            line = _structure_line(raw_line)
            match = ITINERARY_DAY_RE.match(line)
            if match:
                day_blocks.append((match.group(1), match.group(2) or "", [match.group(3)]))
            elif day_blocks:
                day_blocks[-1][2].append(line)
        for day_number, weekday, body_lines in day_blocks:
            day_body = "\n".join(body_lines).strip()
            day_title, day_description = _itinerary_day_content(day_body)
            days.append(
                {
                    "day": f"Dia {day_number}" + (f" ({weekday})" if weekday else ""),
                    "title": day_title or f"Dia {day_number}",
                    "description": day_description,
                }
            )
        if not days:
            day_text = content
            if day_text:
                day_title, day_description = _itinerary_day_content(day_text)
                days.append({"day": "Dia 1", "title": day_title, "description": day_description})
        return {
            "type": "itinerary",
            "enabled": True,
            "anchorId": _generate_anchor("itinerary", title or "itinerario", index),
            "layout": "timeline",
            "title": title or "Itinerário",
            "subtitle": subtitle or "",
            "days": days,
        }

    if normalized_name == _normalize_text("PRECOS"):
        # Cada "Nome do plano" abre um plano; o que vem antes do primeiro é da seção
        # (etiqueta, título, subtítulo) e a observação geral vale para a lista toda.
        intro_lines: list[str] = []
        plan_blocks: list[list[str]] = []
        current_plan: list[str] | None = None
        for raw_line in block.splitlines():
            line = _strip_markdown_emphasis(raw_line.strip())
            if re.fullmatch(r"(?:[-*_]\s*){3,}", line):
                continue
            line = re.sub(r"^(?:[-*+•‣]|\d+[.)])\s+", "", line)
            label = line.split(":", 1)[0]
            if ":" in line and _field_alias(label) == "plan_name":
                current_plan = [line]
                plan_blocks.append(current_plan)
            elif current_plan is not None:
                current_plan.append(line)
            else:
                intro_lines.append(line)
        intro = _parse_key_value_lines("\n".join(intro_lines))
        plans = [_parse_key_value_lines("\n".join(lines)) for lines in plan_blocks] or [fields]
        general_note = intro.get("general_note", "").strip() or next(
            (plan.get("general_note", "").strip() for plan in plans if plan.get("general_note")), ""
        )
        # Frase geral solta depois do último plano ("Consulte disponibilidade, formas de
        # pagamento..."): vale para a lista toda, não para o último plano.
        last_note = plans[-1].get("note", "").strip()
        if last_note and plan_blocks:
            note_lines = last_note.splitlines()
            while len(note_lines) > 1 and re.match(r"^(?:CONSULTE|VALORES|PRECOS|CONDICOES|SUJEITO)", _normalize_text(note_lines[-1])):
                general_note = "\n".join(part for part in (note_lines.pop().strip(), general_note) if part)
            plans[-1]["note"] = "\n".join(note_lines).strip()
        notes = [plan.get("note", "").strip() for plan in plans]
        # A mesma observação em todos os planos vira a nota única abaixo da lista.
        shared_note = notes[0] if len(notes) > 1 and notes[0] and all(note == notes[0] for note in notes) else ""
        # Formas de pagamento valem para a seção; o parcelamento de cada plano fica no próprio plano.
        payment_text = " ".join(
            source.get("payment_methods", "") for source in [intro, *plans] if source.get("payment_methods")
        )
        payment_methods, payment_note = _parse_payment_methods(payment_text)
        price_items = []
        for plan in plans:
            raw_value = plan.get("value", "").strip()
            note = plan.get("note", "").strip()
            split_label, terms = _split_price_text(raw_value)
            price = _parse_price_value(raw_value) if re.search(r"\d", raw_value) else 0.0
            if not price and raw_value and not split_label and not terms:
                # Valor sem número ("Sob consulta"): o texto vai para as condições.
                terms = raw_value
            installments = plan.get("installments", "").strip()
            details = [terms, installments, "" if note == shared_note else note]
            item: dict[str, Any] = {
                "title": plan.get("plan_name", "").strip() or "Pacote",
                "price": price,
                "priceLabel": plan.get("price_label", "").strip() or split_label,
                "description": "\n".join(part for part in details if part),
                "currency": "BRL",
            }
            badge = plan.get("badge", "").strip()
            if badge and _normalize_text(badge) not in {"NAO", "NENHUM", "SEM SELO", "-"}:
                item["badge"] = badge
            if _is_yes(plan.get("plan_highlight", "")):
                item["highlight"] = True
            price_items.append(item)
        prices_section: dict[str, Any] = {
            "type": "prices",
            "enabled": True,
            "anchorId": _generate_anchor("prices", "precos", index),
            "layout": "cards" if len(price_items) > 1 else "highlight",
            "title": intro.get("title", "").strip() or "Preços",
            "subtitle": intro.get("subtitle", "").strip(),
            "description": "\n".join(part for part in (shared_note, general_note) if part),
            "items": price_items,
        }
        if intro.get("label"):
            prices_section["headingLabel"] = intro["label"].strip()
        if payment_methods:
            prices_section.update({"showPayments": True, "paymentMethods": payment_methods, "paymentNote": payment_note})
        return prices_section

    if normalized_name == _normalize_text("PERGUNTAS FREQUENTES"):
        questions: list[dict[str, Any]] = []
        current_question = ""
        current_answer_lines: list[str] = []
        reading_answer = False
        for raw_line in block.splitlines():
            line = _strip_markdown_emphasis(raw_line.strip())
            if re.fullmatch(r"(?:[-*_]\s*){3,}", line):
                continue
            label_line = re.sub(r"^(?:[-*+•‣]|\d+[.)])\s+", "", line)
            question_match = re.match(r"^Pergunta\s*:\s*(.*)$", label_line, flags=re.IGNORECASE)
            answer_match = re.match(r"^Resposta\s*:\s*(.*)$", label_line, flags=re.IGNORECASE)
            if question_match:
                if current_question and current_answer_lines:
                    questions.append({"question": current_question, "answer": "\n".join(current_answer_lines).strip()})
                current_question = question_match.group(1).strip()
                current_answer_lines = []
                reading_answer = False
            elif answer_match and current_question:
                current_answer_lines = [answer_match.group(1).strip()]
                reading_answer = True
            elif current_question and line:
                if reading_answer:
                    current_answer_lines.append(line)
                else:
                    current_question = f"{current_question} {line}"
        if current_question and current_answer_lines:
            questions.append({"question": current_question, "answer": "\n".join(current_answer_lines).strip()})
        return {
            "type": "faq",
            "enabled": True,
            "anchorId": _generate_anchor("faq", "perguntas-frequentes", index),
            "layout": "accordion",
            "title": fields.get("title", "").strip() or "Perguntas frequentes",
            "subtitle": fields.get("subtitle", "").strip(),
            "items": questions,
        }

    if normalized_name == _normalize_text("DEPOIMENTOS"):
        # Cada "Nome" abre um depoimento; "Depoimento"/"Texto" é a fala e "Identificação"/"Cargo"
        # aparece embaixo do nome. A avaliação não tem campo na seção (as estrelas são fixas).
        items: list[dict[str, Any]] = []
        current_item: dict[str, str] = {}
        current_key = ""
        intro: dict[str, str] = {}

        def flush_testimonial() -> None:
            if current_item.get("name") and current_item.get("text"):
                items.append(dict(current_item))

        for raw_line in block.splitlines():
            line = _structure_line(raw_line)
            if not line:
                continue
            match = re.match(r"^([^:]+?):\s*(.*)$", line)
            key = _field_alias(match.group(1)) if match else None
            if match and _normalize_text(match.group(1)) == "NOME":
                flush_testimonial()
                current_item = {"name": match.group(2).strip()}
                current_key = "name"
            elif key in {"text", "description"} and current_item:
                current_item["text"] = match.group(2).strip()
                current_key = "text"
            elif key == "role" and current_item:
                current_item["role"] = match.group(2).strip()
                current_key = "role"
            elif key in {"title", "subtitle", "label"} and not current_item:
                intro[key] = match.group(2).strip()
            elif key:
                current_key = ""
            elif current_key == "text":
                current_item["text"] = f"{current_item['text']}\n{line}".strip()
        flush_testimonial()
        for item in items:
            item["text"] = item["text"].strip().strip('"“”').strip()
        section_data: dict[str, Any] = {
            "type": "testimonials",
            "enabled": True,
            "anchorId": _generate_anchor("testimonials", "depoimentos", index),
            "layout": "cards",
            "title": intro.get("title") or "Depoimentos",
            "subtitle": intro.get("subtitle", ""),
            "items": items,
        }
        if intro.get("label"):
            section_data["headingLabel"] = intro["label"]
        return section_data

    if normalized_name == _normalize_text("VIDEO EM DESTAQUE"):

        title = fields.get("title", "").strip() or fields.get("label", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        # Só um link de verdade vira vídeo; "inserir link" ou "não informado" fica vazio.
        video_url = next(iter(re.findall(r"https?://\S+", fields.get("link", ""))), "").rstrip(").,;")
        return {
            "type": "featured_video",
            "enabled": True,
            "anchorId": _generate_anchor("featured-video", title or "video", index),
            "title": title or "Vídeo",
            "subtitle": subtitle or "",
            "videoUrl": video_url or "",
            "ctaEnabled": False,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("BIOGRAFIA"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        text = fields.get("text", "").strip() or fields.get("description", "").strip() or subtitle or content
        return {
            "type": "biography",
            "enabled": True,
            "anchorId": _generate_anchor("biography", title or label or "biografia", index),
            "title": title or "Biografia",
            "text": text or "",
            "titleFontSize": 36,
            "textFontSize": 18,
            "image": "",
            "mobileImage": "",
            "overlayOpacity": 0.45,
        }

    if normalized_name == _normalize_text("CHAMADA PARA ACAO"):

        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        button = fields.get("button", "").strip()
        description = fields.get("description", "").strip() or fields.get("text", "").strip() or fields.get("content", "").strip()
        return {
            "type": "cta",
            "enabled": True,
            "anchorId": _generate_anchor("cta", title or label or "cta", index),
            "layout": "simple",
            "label": title or label or "Chamada para ação",
            **({"headingLabel": label} if title and label else {}),
            "description": fields.get("subtitle", "").strip() or description or "",
            "ctaText": button or "",
            "ctaColor": "",
            "textColor": "",
            "highlight": False,
            "fullWidth": True,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("ITENS"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        items = _parse_reason_items(block)
        # Ícone de cada card: o da biblioteca escolhido pela IA ou deduzido do título. Emoji só
        # fica quando todos os cards são emoji sem equivalente; numa grade mista, o card sem
        # ícone ganha o "incluso", para nenhum card ficar sem ícone.
        for item in items:
            chosen = _ai_icon_value(item.get("icon", ""))
            if not chosen.startswith("icon:"):
                chosen = _ai_icon_value("", item.get("title", ""), item.get("description", "")) or chosen
            if chosen:
                item["icon"] = chosen
            else:
                item.pop("icon", None)
        icon_mode = "icon"
        if any(item.get("icon") for item in items):
            if all(item.get("icon") and not item["icon"].startswith("icon:") for item in items):
                icon_mode = "emoji"
            else:
                for item in items:
                    if not str(item.get("icon", "")).startswith("icon:"):
                        item["icon"] = "icon:circle-check"
        return {
            "type": "reasons",
            "iconMode": icon_mode,
            "enabled": True,
            "anchorId": _generate_anchor("reasons", title or label or "itens", index),
            "headingLabel": label,
            "title": title or "Itens",
            "subtitle": subtitle,
            "items": items,
            "enableAnimation": False,
        }

    if normalized_name == _normalize_text("CONTADOR"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        target_date = _parse_countdown_date(fields.get("target_date", ""))
        if not target_date:
            # Sem data informada a IA não deveria usar o Contador; fica uma data provisória
            # para a agência trocar no editor.
            target_date = (datetime.utcnow() + timedelta(days=3)).replace(microsecond=0).isoformat() + "Z"
        countdown: dict[str, Any] = {
            "type": "countdown",
            "enabled": True,
            "anchorId": _generate_anchor("countdown", title or label or "contagem-regressiva", index),
            "label": title or label or "Contagem regressiva",
            "countdownMode": "fixed",
            "sessionDuration": 15,
            "sessionUnit": "minutes",
            "targetDate": target_date,
            "layout": "flip",
        }
        if title and label:
            countdown["headingLabel"] = label
        return countdown

    if normalized_name == _normalize_text("DETALHES DO VOO"):
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        return {
            "type": "flight_details",
            "enabled": True,
            "anchorId": _generate_anchor("flight-details", title or "detalhes-do-voo", index),
            "sectionId": _generate_anchor("flight", title or "detalhes-do-voo", index),
            "title": title or "Informações do voo",
            "subtitle": subtitle,
            # O texto do voo é rico (HTML): uma linha por parágrafo.
            "generalInfo": "".join(
                f"<p>{html.escape(line)}</p>"
                for line in (fields.get("general_info", "").strip() or _flight_info_text(block)).splitlines()
                if line.strip()
            ),
            "visualStyle": "decolar",
            "showOutbound": True,
            "showInbound": True,
            "journeys": [],
        }

    return None


AI_IMAGE_PLACEHOLDER = "data:image/svg+xml;base64," + base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'
    b'<rect width="1200" height="800" fill="#e2e8f0"/>'
    b'<path d="M420 460l120-140 90 100 60-70 110 110z" fill="#94a3b8"/>'
    b'<circle cx="720" cy="270" r="35" fill="#94a3b8"/>'
    b'<text x="600" y="550" text-anchor="middle" font-family="sans-serif" font-size="32" fill="#475569">Substitua pela sua imagem</text></svg>'
).decode("ascii")


def _fill_ai_image_placeholders(section: dict[str, Any]) -> None:
    image_fields = {
        "hero": ("backgroundImage", "mobileBackgroundImage"),
        "banner_card": ("backgroundImage",),
        "photo": ("image",),
        "biography": ("image", "mobileImage"),
    }
    for field in image_fields.get(section["type"], ()):
        section[field] = AI_IMAGE_PLACEHOLDER
    if section["type"] == "story":
        section["images"] = [AI_IMAGE_PLACEHOLDER]
    if section["type"] == "itinerary":
        for day in section["days"]:
            day["image"] = AI_IMAGE_PLACEHOLDER
    # Depoimentos ficam sem foto: a seção mostra as iniciais do nome até a agência enviar uma.


def build_page_base_config_from_reply(
    reply: str, current_config: Any | None = None, *, strict: bool = False
) -> tuple[Any, str | None]:
    is_valid, validation_error = _validate_ai_reply_format(reply)
    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_error)
    if strict:
        for line in reply.splitlines():
            match = SECTION_HEADER_RE.match(line)
            if match and not _canonical_section_name(match.group(1)):
                raise HTTPException(
                    status_code=400,
                    detail="A sugestão contém uma seção não suportada. Peça à IA uma nova estrutura com as seções disponíveis.",
                )
    meta, blocks = _split_sections(reply)
    sections: list[dict[str, Any]] = []
    hero_title: str | None = None

    for index, (section_name, block) in enumerate(blocks):
        parsed_section = _parse_ai_section_block(section_name, block, index)
        if not parsed_section:
            continue
        fields = _parse_key_value_lines(block)
        # "Etiqueta" é o selo acima do título nas seções que o mostram.
        if (
            parsed_section["type"] in {"banner_card", "itinerary", "faq", "featured_video"}
            and fields.get("label")
            and not parsed_section.get("headingLabel")
        ):
            parsed_section["headingLabel"] = fields["label"].strip()
        if parsed_section["type"] in {"story", "banner_card", "featured_video"} and fields.get("button"):
            parsed_section["ctaEnabled"] = True
            parsed_section["ctaLabel"] = fields["button"].strip()
        _fill_ai_image_placeholders(parsed_section)
        sections.append(parsed_section)
        if not hero_title and parsed_section.get("type") == "hero":
            hero_title = str(parsed_section.get("title") or "").strip() or None

    if not sections:
        raise HTTPException(status_code=400, detail="N?o foi poss?vel identificar se??es v?lidas na resposta da IA.")

    base_config = deepcopy(current_config) if isinstance(current_config, dict) else {}
    base_config["sections"] = sections
    return base_config, hero_title or (meta.get("Tipo de p?gina") or None)

def _request_ai_reply(
    client: object,
    model: str,
    instructions: str,
    input_items: list[dict[str, object]],
) -> str:
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_items,
        temperature=0.2,
    )
    return _extract_response_text(response)


def _request_ai_reply_response(
    client: object,
    model: str,
    instructions: str,
    input_items: list[dict[str, object]],
) -> object:
    return client.responses.create(
        model=model,
        instructions=instructions,
        input=input_items,
        temperature=0.2,
    )


def _extract_usage_data(response: object) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cached_input_tokens": 0}

    def _read_int(*names: str) -> int:
        for name in names:
            value = getattr(usage, name, None)
            if isinstance(value, (int, float)):
                return int(value)
        return 0

    input_tokens = _read_int("input_tokens", "prompt_tokens")
    output_tokens = _read_int("output_tokens", "completion_tokens")
    total_tokens = _read_int("total_tokens") or (input_tokens + output_tokens)
    cached_input_tokens = _read_int("cached_input_tokens")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
    }


def _estimate_model_cost_usd(model: str, usage: dict[str, int]) -> float:
    pricing = MODEL_PRICING_USD.get(model, MODEL_PRICING_USD["gpt-5.4"])
    input_tokens = max(int(usage.get("input_tokens", 0) or 0), 0)
    cached_input_tokens = max(int(usage.get("cached_input_tokens", 0) or 0), 0)
    output_tokens = max(int(usage.get("output_tokens", 0) or 0), 0)
    billed_input_tokens = max(input_tokens - cached_input_tokens, 0)
    estimated = (
        (billed_input_tokens / 1_000_000) * pricing["input"]
        + (cached_input_tokens / 1_000_000) * pricing["cached_input"]
        + (output_tokens / 1_000_000) * pricing["output"]
    )
    return round(estimated, 6)


def _build_ai_conversation_input(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
) -> list[dict[str, object]]:
    input_items: list[dict[str, object]] = []
    normalized_conversation = [item for item in conversation if (item.content or "").strip()]

    for item in normalized_conversation[:-1]:
        input_items.append({"role": item.role, "content": item.content.strip()})

    last_message = normalized_conversation[-1] if normalized_conversation else None
    if last_message is None:
        raise HTTPException(status_code=400, detail="Mensagem do usuário ausente.")

    last_content: list[dict[str, object]] = [
        {
            "type": "input_text",
            "text": last_message.content.strip()
            or "Analise os arquivos anexados e responda seguindo o formato do Construtor Roteiro Online.",
        }
    ]
    for attachment in attachments or []:
        encoded_file = base64.b64encode(attachment.data).decode("ascii")
        mime_type = attachment.content_type or "application/octet-stream"
        last_content.append(
            {
                "type": "input_file",
                "filename": attachment.filename or "arquivo",
                "file_data": f"data:{mime_type};base64,{encoded_file}",
                "detail": "low",
            }
        )
    input_items.append({"role": last_message.role, "content": last_content})
    return input_items


def _run_ai_reply(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
    model_override: str | None = None,
) -> tuple[str, str, dict[str, int]]:
    if not conversation:
        raise HTTPException(status_code=400, detail="Conversa vazia.")

    model = (model_override or settings.gpt_model or "gpt-5.4").strip() or "gpt-5.4"
    client = _load_openai_client()
    input_items = _build_ai_conversation_input(conversation, attachments)

    try:
        response = _request_ai_reply_response(client, model, load_system_prompt(), input_items)
        reply = _extract_response_text(response)
        if validate_output:
            is_valid, validation_error = _validate_ai_reply_format(reply)
            if not is_valid:
                response = _request_ai_reply_response(
                    client,
                    model,
                    _build_correction_instructions(validation_error),
                    input_items,
                )
                reply = _extract_response_text(response)
                is_valid, validation_error = _validate_ai_reply_format(reply)
                if not is_valid:
                    raise HTTPException(status_code=502, detail=f"A OpenAI retornou uma resposta fora do padrão: {validation_error}")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime guard
        raise HTTPException(status_code=502, detail=f"Falha ao consultar a OpenAI: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="A OpenAI não retornou uma resposta válida.")

    usage = _extract_usage_data(response)
    return reply, model, usage


def generate_ai_assistant_reply(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
) -> str:
    if not conversation:
        raise HTTPException(status_code=400, detail="Conversa vazia.")

    model = (settings.gpt_model or "gpt-5.4").strip() or "gpt-5.4"
    client = _load_openai_client()

    input_items: list[dict[str, object]] = []
    normalized_conversation = [item for item in conversation if (item.content or "").strip()]

    for item in normalized_conversation[:-1]:
        input_items.append({"role": item.role, "content": item.content.strip()})

    last_message = normalized_conversation[-1] if normalized_conversation else None
    if last_message is None:
        raise HTTPException(status_code=400, detail="Mensagem do usuário ausente.")

    last_content: list[dict[str, object]] = [
        {
            "type": "input_text",
            "text": last_message.content.strip()
            or "Analise os arquivos anexados e responda seguindo o formato do Construtor Roteiro Online.",
        }
    ]
    for attachment in attachments or []:
        encoded_file = base64.b64encode(attachment.data).decode("ascii")
        mime_type = attachment.content_type or "application/octet-stream"
        last_content.append(
            {
                "type": "input_file",
                "filename": attachment.filename or "arquivo",
                "file_data": f"data:{mime_type};base64,{encoded_file}",
                "detail": "low",
            }
        )
    input_items.append({"role": last_message.role, "content": last_content})

    try:
        reply = _request_ai_reply(client, model, load_system_prompt(), input_items)
        if validate_output:
            is_valid, validation_error = _validate_ai_reply_format(reply)
            if not is_valid:
                reply = _request_ai_reply(
                    client,
                    model,
                    _build_correction_instructions(validation_error),
                    input_items,
                )
                is_valid, validation_error = _validate_ai_reply_format(reply)
                if not is_valid:
                    raise HTTPException(status_code=502, detail=f"A OpenAI retornou uma resposta fora do padrão: {validation_error}")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime guard
        raise HTTPException(status_code=502, detail=f"Falha ao consultar a OpenAI: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="A OpenAI não retornou uma resposta válida.")
    return reply


def generate_ai_assistant_reply_with_usage(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
    model_override: str | None = None,
) -> tuple[str, str, dict[str, int], float]:
    reply, model, usage = _run_ai_reply(
        conversation,
        attachments,
        validate_output=validate_output,
        model_override=model_override,
    )
    return reply, model, usage, _estimate_model_cost_usd(model, usage)


def generate_ai_assistant_reply(
    conversation: list[ChatMessage],
    attachments: list[ChatAttachment] | None = None,
    *,
    validate_output: bool = True,
    model_override: str | None = None,
) -> str:
    reply, _, _ = _run_ai_reply(
        conversation,
        attachments,
        validate_output=validate_output,
        model_override=model_override,
    )
    return reply
