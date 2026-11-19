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


def _two_segment_pattern(page_slugs: set[str]) -> re.Pattern[str] | None:
    """`/qualquer-slug/pagina-da-agencia`: o primeiro trecho é um slug antigo da agência (ela pode ter
    mudado de slug depois de salvar o link), então vale a regra pelo segundo trecho ser uma página dela."""
    slugs = [re.escape(slug) for slug in page_slugs if slug]
    if not slugs:
        return None
    hosts = "|".join(re.escape(host) for host in PLATFORM_HOSTS)
    return re.compile(
        rf"^(?:https?://(?:{hosts})(?::\d+)?)?/(?:p/)?[^/?#\s]+/(?:{'|'.join(slugs)})(?=[/?#]|$)",
        re.IGNORECASE,
    )


def _rewrite_two(node: Any, pattern: re.Pattern[str]) -> Any:
    if isinstance(node, str):
        match = pattern.match(node)
        if not match:
            return node
        return _drop_first_segment(node)
    if isinstance(node, list):
        return [_rewrite_two(item, pattern) for item in node]
    if isinstance(node, dict):
        return {key: _rewrite_two(value, pattern) for key, value in node.items()}
    return node


def _drop_first_segment(value: str) -> str:
    path = re.sub(r"^https?://[^/]+", "", value, flags=re.IGNORECASE)
    path = re.sub(r"^/p/", "/", path, flags=re.IGNORECASE)
    return "/" + path.split("/", 2)[2]


def strip_agency_slug_from_links(config: Any, agency_slug: str, page_slugs: set[str] | None = None) -> Any:
    pattern = _pattern(agency_slug)
    if pattern is not None:
        config = _rewrite(config, pattern)
    two = _two_segment_pattern(page_slugs or set())
    return config if two is None else _rewrite_two(config, two)
