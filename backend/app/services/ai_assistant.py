from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import base64
from copy import deepcopy
from datetime import datetime, timedelta
import re
import unicodedata
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.construtor_prompt import get_active_prompt_text

settings = get_settings()
BASE_PROMPT_PATH = Path(__file__).resolve().parents[3] / "docs" / "construtor-prompt.md"
EXAMPLES_DIR = BASE_PROMPT_PATH.parent / "prompts" / "examples"
ALLOWED_SECTION_NAMES = {
    "BANNER INICIAL",
    "BANNER DESTACADO",
    "SESSAO DESCRITIVA",
    "ITINERARIO",
    "PRECOS",
    "PERGUNTAS FREQUENTES",
    "DEPOIMENTOS",
    "VIDEO",
    "BIOGRAFIA",
    "CHAMADA PARA ACAO",
    "CONTAGEM REGRESSIVA",
}
SECTION_NAME_OPTIONS = (
    "BANNER INICIAL",
    "BANNER DESTACADO",
    "SESSAO DESCRITIVA",
    "ITINERARIO",
    "PRECOS",
    "PERGUNTAS FREQUENTES",
    "DEPOIMENTOS",
    "VIDEO",
    "BIOGRAFIA",
    "CHAMADA PARA ACAO",
    "CONTAGEM REGRESSIVA",
)
SECTION_NAME_ALIASES = {
    "ROTEIRO DIA A DIA": "ITINERARIO",
    "DIA A DIA": "ITINERARIO",
    "PROGRAMACAO DIA A DIA": "ITINERARIO",
    "PROGRAMACAO": "ITINERARIO",
    "ITINERARIO": "ITINERARIO",
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
    "SUBTITULO": "subtitle",
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
    "CARGO": "role",
}
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

BANNER INICIAL
BANNER DESTACADO
SESSÃO DESCRITIVA
ITINERÁRIO
PREÇOS
PERGUNTAS FREQUENTES
DEPOIMENTOS
VÍDEO
BIOGRAFIA
CHAMADA PARA AÇÃO
CONTAGEM REGRESSIVA

Nunca crie nomes como:
O que está incluso
Benefícios
Para quem é
Diferenciais
Hospedagem
Investimento e condições
Chamada rápida
Por que viajar com a agência

Esses temas devem ser desenvolvidos usando SESSÃO DESCRITIVA ou a seção correta existente.

Se a resposta usar qualquer nome de seção fora da lista permitida, ela está incorreta.

Regras finais de precisão:
- Use os nomes de seção exatamente como estão escritos acima.
- Nunca crie variações, apelidos, traduções ou complementos no nome da seção.
- Quando o conteúdo for de roteiro dia a dia, use sempre ITINERARIO como nome da seção.
- Nunca use títulos como ROTEIRO DIA A DIA, PROGRAMAÇÃO DIA A DIA, DIA A DIA ou qualquer variação semelhante como nome de seção.
"""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@dataclass(slots=True)
class ChatAttachment:
    filename: str
    content_type: str | None
    data: bytes


def load_system_prompt() -> str:
    prompt = get_active_prompt_text(create_if_missing=True).strip()
    if prompt:
        return prompt
    return DEFAULT_PROMPT.strip()


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

    first_non_empty_line = next((line.strip() for line in normalized_reply.splitlines() if line.strip()), "")
    if _normalize_text(_strip_markdown_emphasis(first_non_empty_line)) != _normalize_text(REQUIRED_HEADER):
        return False, f"A resposta deve começar com '{REQUIRED_HEADER}'."

    section_names = []
    for line in normalized_reply.splitlines():
        match = SECTION_HEADER_RE.match(line)
        if not match:
            continue
        section_name = match.group(1).strip()
        if section_name:
            section_names.append(section_name)

    if not section_names:
        return False, "A resposta não trouxe blocos de seção."

    for section_name in section_names:
        canonical_name = _canonical_section_name(section_name)
        if canonical_name is None or canonical_name not in ALLOWED_SECTION_NAMES:
            return False, f"Seção inválida detectada: {section_name}."

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
    return stripped.upper().strip()


def _strip_markdown_emphasis(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    text = re.sub(r"(?<!\w)_(?!\s)|(?<!\s)_(?!\w)", "", text)
    return text.strip()


def _canonical_section_name(section_name: str) -> str | None:
    normalized = _normalize_text(section_name)
    for alias, canonical in SECTION_NAME_ALIASES.items():
        if normalized == alias:
            return canonical
        if normalized.startswith(f"{alias} "):
            return canonical
        if normalized.startswith(f"{alias}-"):
            return canonical
        if normalized.startswith(f"{alias} -"):
            return canonical
        if normalized.startswith(f"{alias} â€“"):
            return canonical
    for candidate in SECTION_NAME_OPTIONS:
        if normalized == candidate:
            return candidate
        if normalized.startswith(f"{candidate} "):
            return candidate
        if normalized.startswith(f"{candidate}-"):
            return candidate
        if normalized.startswith(f"{candidate} -"):
            return candidate
        if normalized.startswith(f"{candidate} -"):
            return candidate
        if normalized.startswith(f"{candidate} –"):
            return candidate
    return None


def _normalize_label_line(text: str) -> str:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines = [_strip_markdown_emphasis(line) for line in normalized.splitlines()]
    return "\n".join(cleaned_lines)


def _extract_first_match(block: str, label: str) -> str:
    fields = _parse_key_value_lines(block)
    key = _normalize_text(label)
    return fields.get(FIELD_ALIASES.get(key, ""), "").strip()


def _split_sections(reply: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    normalized = _normalize_label_line(reply.strip())
    lines = normalized.splitlines()

    intro_lines: list[str] = []
    parsed_sections: list[tuple[str, str]] = []
    current_name: str | None = None
    current_body: list[str] = []
    saw_section = False

    for line in lines:
        cleaned_line = _strip_markdown_emphasis(line)
        cleaned_line = SECTION_HEADER_PREFIX_RE.sub("", cleaned_line, count=1).strip()
        match = SECTION_HEADER_RE.match(cleaned_line)
        if match:
            saw_section = True
            if current_name and current_body:
                parsed_sections.append((current_name, "\n".join(current_body).strip()))
            current_body = []
            raw_section_name = match.group(1).strip()
            current_name = _canonical_section_name(raw_section_name)
            continue

        if not saw_section:
            intro_lines.append(line)
            continue

        if current_name:
            current_body.append(line)

    if current_name and current_body:
        parsed_sections.append((current_name, "\n".join(current_body).strip()))

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
        if not line:
            if current_key:
                result.setdefault(current_key, []).append("")
            continue

        match = re.match(r"^([^:]+?):\s*(.*)$", line)
        if match:
            key_name = _normalize_text(match.group(1))
            alias = FIELD_ALIASES.get(key_name)
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
    digits = re.sub(r"[^0-9,\.]", "", value or "")
    if not digits:
        return 0.0
    digits = digits.replace(".", "").replace(",", ".")
    try:
        return float(digits)
    except ValueError:
        return 0.0


def _slug_from_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _generate_anchor(section_type: str, title: str, index: int) -> str:
    base = _slug_from_text(title) or section_type
    return f"{base}-{index + 1}"


def _parse_ai_section_block(section_name: str, block: str, index: int) -> dict[str, Any] | None:
    normalized_name = _normalize_text(section_name)
    fields = _parse_key_value_lines(block)

    if normalized_name == _normalize_text("BANNER INICIAL"):
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
        return {
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

    if normalized_name == _normalize_text("BANNER DESTACADO"):
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

    if normalized_name == _normalize_text("SESSAO DESCRITIVA"):

        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        content = fields.get("content", "").strip()
        if not title:
            title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        body = subtitle or content
        return {
            "type": "story",
            "enabled": True,
            "anchorId": _generate_anchor("story", title or label or "sessao-descritiva", index),
            "layout": "single",
            "imagePosition": "right",
            "badge": label or "",
            "title": title or "Sess?o descritiva",
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
        day_matches = re.finditer(
            r"(?ims)^\s*Dia\s*(\d+)\s*:\s*(.*?)(?=^\s*Dia\s*\d+\s*:|\Z)",
            block,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        for day_match in day_matches:
            day_number = day_match.group(1)
            day_body = day_match.group(2).strip()
            day_lines = [line.strip() for line in day_body.splitlines() if line.strip()]
            day_title = day_lines[0] if day_lines else ""
            day_description = "\n".join(day_lines[1:]).strip()
            days.append(
                {
                    "day": f"Dia {day_number}",
                    "title": day_title or f"Dia {day_number}",
                    "description": day_description or day_body,
                }
            )
        if not days:
            day_text = content or block.strip()
            if day_text:
                day_lines = [line.strip() for line in day_text.splitlines() if line.strip()]
                day_title = day_lines[0] if day_lines else "Roteiro"
                day_description = "\n".join(day_lines[1:]).strip()
                days.append({"day": "Dia 1", "title": day_title, "description": day_description or day_text})
        return {
            "type": "itinerary",
            "enabled": True,
            "anchorId": _generate_anchor("itinerary", title or "itinerario", index),
            "layout": "timeline",
            "title": title or "Itiner?rio",
            "subtitle": subtitle or "",
            "days": days,
        }

    if normalized_name == _normalize_text("PRECOS"):

        plan_name = fields.get("plan_name", "").strip()
        raw_value = fields.get("value", "").strip()
        note = fields.get("note", "").strip()
        price_item = {
            "title": plan_name or "Pacote",
            "price": _parse_price_value(raw_value),
            "description": raw_value.replace("R$", "").strip() if raw_value else "",
            "currency": "BRL",
        }
        return {
            "type": "prices",
            "enabled": True,
            "anchorId": _generate_anchor("prices", plan_name or "precos", index),
            "layout": "highlight",
            "title": "Pre?os",
            "subtitle": "",
            "description": note or "",
            "items": [price_item],
        }

    if normalized_name == _normalize_text("PERGUNTAS FREQUENTES"):
        questions: list[dict[str, Any]] = []
        current_question = ""
        current_answer_lines: list[str] = []
        for line in block.splitlines():
            question_match = re.match(r"^\s*Pergunta\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            answer_match = re.match(r"^\s*Resposta\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            if question_match:
                if current_question and current_answer_lines:
                    questions.append({"question": current_question, "answer": "\n".join(current_answer_lines).strip()})
                current_question = question_match.group(1).strip()
                current_answer_lines = []
            elif answer_match and current_question:
                current_answer_lines = [answer_match.group(1).strip()]
            elif current_question and current_answer_lines:
                current_answer_lines.append(line.strip())
        if current_question and current_answer_lines:
            questions.append({"question": current_question, "answer": "\n".join(current_answer_lines).strip()})
        elif fields.get("question") and fields.get("answer"):
            questions.append({"question": fields["question"].strip(), "answer": fields["answer"].strip()})
        return {
            "type": "faq",
            "enabled": True,
            "anchorId": _generate_anchor("faq", "perguntas-frequentes", index),
            "layout": "accordion",
            "title": "Perguntas frequentes",
            "subtitle": "",
            "items": questions,
        }

    if normalized_name == _normalize_text("DEPOIMENTOS"):
        items: list[dict[str, Any]] = []
        current_item: dict[str, str] = {}
        for line in block.splitlines():
            name_match = re.match(r"^\s*Nome\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            text_match = re.match(r"^\s*Texto\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            role_match = re.match(r"^\s*Cargo\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            if name_match:
                if current_item.get("name") and current_item.get("text"):
                    items.append(current_item)
                    current_item = {}
                current_item["name"] = name_match.group(1).strip()
            elif text_match:
                current_item["text"] = text_match.group(1).strip()
            elif role_match:
                current_item["role"] = role_match.group(1).strip()
            elif current_item.get("text"):
                current_item["text"] = f"{current_item['text']}\n{line.strip()}".strip()
        if current_item.get("name") and current_item.get("text"):
            items.append(current_item)
        elif fields.get("title") and fields.get("text"):
            items.append({"name": fields["title"].strip(), "text": fields["text"].strip()})
        return {
            "type": "testimonials",
            "enabled": True,
            "anchorId": _generate_anchor("testimonials", "depoimentos", index),
            "layout": "cards",
            "title": "Depoimentos",
            "subtitle": "",
            "items": items,
        }

    if normalized_name == _normalize_text("VIDEO"):

        title = fields.get("title", "").strip() or fields.get("label", "").strip()
        subtitle = fields.get("subtitle", "").strip()
        video_url = fields.get("link", "").strip()
        return {
            "type": "featured_video",
            "enabled": True,
            "anchorId": _generate_anchor("featured-video", title or "video", index),
            "title": title or "V?deo",
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
        text = subtitle or content
        return {
            "type": "biography",
            "enabled": True,
            "anchorId": _generate_anchor("biography", title or label or "biografia", index),
            "title": title or "Biografia",
            "text": text or "",
            "image": "",
            "mobileImage": "",
            "overlayOpacity": 0.45,
        }

    if normalized_name == _normalize_text("CHAMADA PARA ACAO"):

        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        button = fields.get("button", "").strip()
        description = fields.get("content", "").strip()
        return {
            "type": "cta",
            "enabled": True,
            "anchorId": _generate_anchor("cta", title or label or "cta", index),
            "layout": "simple",
            "label": label or "Chamada para a??o",
            "description": description or "",
            "ctaText": button or "",
            "ctaColor": "",
            "textColor": "",
            "highlight": False,
            "fullWidth": True,
            "ctaMode": "link",
            "ctaSectionId": None,
            "ctaOpenInNewTab": False,
        }

    if normalized_name == _normalize_text("CONTAGEM REGRESSIVA"):
        label = fields.get("label", "").strip()
        title = fields.get("title", "").strip()
        target_date = (datetime.utcnow() + timedelta(days=3)).replace(microsecond=0).isoformat() + "Z"
        return {
            "type": "countdown",
            "enabled": True,
            "anchorId": _generate_anchor("countdown", title or label or "contagem-regressiva", index),
            "label": label or "Contagem regressiva",
            "countdownMode": "fixed",
            "sessionDuration": 15,
            "sessionUnit": "minutes",
            "targetDate": target_date,
            "layout": "cards",
        }

    return None


def build_page_base_config_from_reply(reply: str, current_config: Any | None = None) -> tuple[Any, str | None]:
    meta, blocks = _split_sections(reply)
    sections: list[dict[str, Any]] = []
    hero_title: str | None = None

    for index, (section_name, block) in enumerate(blocks):
        parsed_section = _parse_ai_section_block(section_name, block, index)
        if not parsed_section:
            continue
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
