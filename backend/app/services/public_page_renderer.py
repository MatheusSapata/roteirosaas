from __future__ import annotations

import html
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints import public_pages
from app.schemas.page import PublicPageOut

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_PATH = FRONTEND_DIST_DIR / "index.html"
DEFAULT_META_START = "<!--default-meta-->"
DEFAULT_META_END = "<!--/default-meta-->"


class FrontendTemplateNotReady(RuntimeError):
    """Indica que o build do frontend ainda não está disponível."""


class PublicPageNotAvailable(RuntimeError):
    """Levanta quando não existe página pública para o slug informado."""


@lru_cache
def _load_frontend_template() -> str:
    if not FRONTEND_INDEX_PATH.exists():
        raise FrontendTemplateNotReady(
            f"Arquivo {FRONTEND_INDEX_PATH} não encontrado. Execute o build do frontend."
        )
    return FRONTEND_INDEX_PATH.read_text(encoding="utf-8")


def load_frontend_index() -> str:
    """Retorna o HTML base do frontend sem alterações."""
    return _load_frontend_template()


def _replace_default_meta(html_template: str, meta_block: str) -> str:
    start = html_template.find(DEFAULT_META_START)
    end = html_template.find(DEFAULT_META_END, start + len(DEFAULT_META_START)) if start >= 0 else -1
    if start >= 0 and end >= 0:
        end += len(DEFAULT_META_END)
        return html_template[:start] + meta_block + html_template[end:]
    if "</head>" in html_template:
        return html_template.replace("</head>", f"{meta_block}\n  </head>", 1)
    return f"{meta_block}\n{html_template}"


def _absolute_url(value: Optional[str], origin: str) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("//"):
        return f"{origin.split(':', 1)[0]}:{value}"
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/"):
        return f"{origin}{value}"
    return f"{origin}/{value}"


def _canonicalize_url(page_url: str) -> tuple[str, str]:
    parsed = urlsplit(page_url)
    canonical = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return canonical, origin


def _build_meta_block(page: PublicPageOut, canonical_url: str, origin: str) -> str:
    branding = page.branding or {}
    agency_name = str(branding.get("agency_name") or "Roteiro Online").strip()
    seo_title = (page.seo_title or page.title).strip()
    final_title = seo_title if agency_name.lower() in seo_title.lower() else f"{agency_name} | {seo_title}"

    description = (
        page.seo_description
        or f"{agency_name} preparou um roteiro personalizado: {page.title}."
    ).strip()

    image_candidate = page.cover_image_url or branding.get("logo_url")
    image_url = _absolute_url(image_candidate, origin)
    logo_url = _absolute_url(branding.get("logo_url"), origin)

    escaped_title = html.escape(final_title)
    escaped_description = html.escape(description)
    escaped_canonical = html.escape(canonical_url)

    meta_lines = [
        f"<title>{escaped_title}</title>",
        f'<link rel="canonical" href="{escaped_canonical}" />',
        f'<meta name="description" content="{escaped_description}" />',
        f'<meta property="og:title" content="{escaped_title}" />',
        f'<meta property="og:description" content="{escaped_description}" />',
        f'<meta property="og:url" content="{escaped_canonical}" />',
        '<meta property="og:type" content="website" />',
        f'<meta property="og:site_name" content="{html.escape(agency_name or "Roteiro Online")}" />',
        '<meta property="og:locale" content="pt_BR" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{escaped_title}" />',
        f'<meta name="twitter:description" content="{escaped_description}" />',
    ]
    image_reference = image_url or logo_url
    if image_reference:
        escaped_image = html.escape(image_reference)
        meta_lines.append(f'<meta property="og:image" content="{escaped_image}" />')
        meta_lines.append(f'<meta name="twitter:image" content="{escaped_image}" />')

    meta_block = "    " + "\n    ".join(meta_lines) + "\n"
    return meta_block


def _fetch_page_payload(db: Session, agency_slug: str, page_slug: Optional[str]) -> PublicPageOut:
    try:
        if page_slug:
            return public_pages.get_public_page(agency_slug, page_slug, db)
        return public_pages.get_default_public_page(agency_slug, db)
    except HTTPException as exc:  # pragma: no cover - FastAPI específica
        raise PublicPageNotAvailable(exc.detail) from exc


def render_public_page_html(
    agency_slug: str,
    page_slug: Optional[str],
    page_url: str,
    db: Session,
) -> str:
    page_data = _fetch_page_payload(db, agency_slug, page_slug)
    canonical_url, origin = _canonicalize_url(page_url)
    meta_block = _build_meta_block(page_data, canonical_url, origin)
    base_html = _load_frontend_template()
    return _replace_default_meta(base_html, meta_block)
