"""Em domínio próprio da agência, links internos precisam ser `/slug-da-pagina`, nunca
`/slug-da-agencia/slug-da-pagina` (dá "Pagina nao encontrada"). Links salvos antes de o domínio ser
ativado ainda trazem o slug da agência; aqui eles são corrigidos ao servir a página, para todas as
agências de uma vez, sem mexer no que está salvo no banco."""
import re
from typing import Any

PLATFORM_HOSTS = ("roteiroonline.com", "www.roteiroonline.com", "app.roteiroonline.com")


def _pattern(agency_slug: str) -> re.Pattern[str] | None:
    slug = (agency_slug or "").strip().strip("/")
    if not slug:
        return None
    hosts = "|".join(re.escape(host) for host in PLATFORM_HOSTS)
    return re.compile(
        rf"^(?:https?://(?:{hosts})(?::\d+)?)?/(?:p/)?{re.escape(slug)}(?=[/?#]|$)(/?)",
        re.IGNORECASE,
    )


def _rewrite(node: Any, pattern: re.Pattern[str]) -> Any:
    if isinstance(node, str):
        if any(ch.isspace() for ch in node):
            return node
        match = pattern.match(node)
        if not match:
            return node
        return "/" + node[match.end():]
    if isinstance(node, list):
        return [_rewrite(item, pattern) for item in node]
    if isinstance(node, dict):
        return {key: _rewrite(value, pattern) for key, value in node.items()}
    return node


def strip_agency_slug_from_links(config: Any, agency_slug: str) -> Any:
    pattern = _pattern(agency_slug)
    return config if pattern is None else _rewrite(config, pattern)
