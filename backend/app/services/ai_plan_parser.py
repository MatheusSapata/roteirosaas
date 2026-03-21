import json
import re
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError


PART4_PATTERN = re.compile(r"PARTE\s*4[^\n]*\n(?P<body>.+)", re.S | re.IGNORECASE)
JSON_BLOCK_PATTERN = re.compile(r"JSON_START\s*(?P<body>.+?)\s*JSON_END", re.S | re.IGNORECASE)


class SectionPlan(BaseModel):
    type: str
    fields: Dict[str, Any]
    observations: Dict[str, Any] | None = None


class PlannerResponsePart4(BaseModel):
    sections: List[SectionPlan]


def parse_plan_sections(raw_text: str) -> List[dict[str, Any]]:
    json_payload = extract_json_part4(raw_text)
    try:
        parsed = PlannerResponsePart4.model_validate(json_payload)
    except ValidationError as exc:  # pragma: no cover - repassado como ValueError
        raise ValueError(f"Estrutura da PARTE 4 invalida: {exc}") from exc

    if not parsed.sections:
        raise ValueError("Nenhuma secao encontrada no bloco JSON da PARTE 4.")

    return [
        {
            "type": section.type,
            "fields": section.fields,
            "observations": section.observations,
        }
        for section in parsed.sections
    ]


def extract_json_part4(raw_text: str) -> Dict[str, Any]:
    part_match = PART4_PATTERN.search(raw_text)
    if not part_match:
        raise ValueError("Resposta da IA nao contem a PARTE 4 esperada.")

    body = part_match.group("body")
    json_match = JSON_BLOCK_PATTERN.search(body)
    if not json_match:
        raise ValueError("Resposta da IA nao contem bloco JSON_START/JSON_END na PARTE 4.")

    json_text = json_match.group("body").strip()
    if not json_text:
        raise ValueError("Bloco JSON da PARTE 4 esta vazio.")

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:  # pragma: no cover - repassado como ValueError
        raise ValueError(f"Bloco JSON da PARTE 4 invalido: {exc}") from exc
