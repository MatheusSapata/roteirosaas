import json
from copy import deepcopy
from typing import Any, Optional
from urllib.parse import quote

WHATSAPP_PLACEHOLDER = "{{WHATSAPP_LINK}}"
LOGO_PLACEHOLDER = "{{AGENCY_LOGO_URL}}"


def normalize_config(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _walk(node: Any, visitor) -> None:
    if isinstance(node, dict):
        for key, value in list(node.items()):
            visitor(node, key, value)
            _walk(value, visitor)
    elif isinstance(node, list):
        for idx, value in enumerate(list(node)):
            visitor(node, idx, value)
            _walk(value, visitor)


def scrub_template_config(raw: Any) -> Any:
    """Remove dados específicos da agência antes de salvar como template."""
    data = deepcopy(normalize_config(raw))
    if data is None:
        return None

    def visitor(container: Any, key: Any, value: Any) -> None:
        if isinstance(container, dict) and isinstance(key, str):
            if key in {"logoUrl", "logo_url"}:
                container[key] = LOGO_PLACEHOLDER
        if isinstance(value, str) and "wa.me" in value:
            container[key] = WHATSAPP_PLACEHOLDER

    _walk(data, visitor)
    return data


def apply_template_branding(raw: Any, *, logo_url: Optional[str], whatsapp_link: Optional[str]) -> Any:
    data = deepcopy(normalize_config(raw))
    if data is None:
        return None

    def visitor(container: Any, key: Any, value: Any) -> None:
        if isinstance(value, str):
            if value == WHATSAPP_PLACEHOLDER:
                container[key] = whatsapp_link or ""
            elif value == LOGO_PLACEHOLDER:
                container[key] = logo_url or ""
        if isinstance(container, dict) and isinstance(key, str):
            if key in {"logoUrl", "logo_url"} and isinstance(container[key], str):
                if container[key] == LOGO_PLACEHOLDER:
                    container[key] = logo_url or ""

    _walk(data, visitor)
    return data


def sanitize_digits(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isdigit())


def build_whatsapp_link(digits: str, title: str) -> str:
    if not digits:
        return ""
    message = f"Oi, tenho interesse no roteiro: {title or 'Roteiro'}"
    return f"https://wa.me/{digits}?text={quote(message)}"
