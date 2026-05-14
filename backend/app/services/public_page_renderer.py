from __future__ import annotations

import html
import io
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.api.v1.endpoints import public_pages
from app.schemas.page import PublicPageOut

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_PATH = FRONTEND_DIST_DIR / "index.html"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
OG_CACHE_DIR = UPLOADS_DIR / "og-cache"
DEFAULT_META_START = "<!--default-meta-->"
DEFAULT_META_END = "<!--/default-meta-->"
MAX_OG_SOURCE_BYTES = 12 * 1024 * 1024
OG_TARGET_MAX_SIDE = 1200
OG_JPEG_QUALITY = 82
HTTP_TIMEOUT_SECONDS = 12


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


def _optimize_og_image(image_url: Optional[str], origin: str) -> Optional[str]:
    if not image_url:
        return None
    parsed = urlsplit(image_url)
    if parsed.scheme not in {"http", "https"}:
        return image_url

    try:
        OG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:24]
        target_path = OG_CACHE_DIR / f"{digest}.jpg"
        if target_path.exists() and target_path.stat().st_size > 0:
            return f"{origin}/uploads/og-cache/{target_path.name}"

        req = Request(
            image_url,
            headers={
                "User-Agent": "RoteiroOnlineBot/1.0 (+https://roteiroonline.com)",
                "Accept": "image/*",
            },
        )
        with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_OG_SOURCE_BYTES + 1)
        if len(raw) > MAX_OG_SOURCE_BYTES:
            return image_url

        with Image.open(io.BytesIO(raw)) as img:
            # Normaliza para JPEG otimizado para compartilhamento social
            if img.mode not in {"RGB", "L"}:
                img = img.convert("RGB")
            elif img.mode == "L":
                img = img.convert("RGB")

            width, height = img.size
            max_side = max(width, height)
            if max_side > OG_TARGET_MAX_SIDE:
                scale = OG_TARGET_MAX_SIDE / float(max_side)
                img = img.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.LANCZOS)

            img.save(
                target_path,
                format="JPEG",
                quality=OG_JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )

        return f"{origin}/uploads/og-cache/{target_path.name}"
    except (HTTPError, URLError, TimeoutError, OSError, UnidentifiedImageError, ValueError):
        return image_url


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
    image_reference = _optimize_og_image(image_url, origin) if image_url else None
    image_reference = image_reference or _optimize_og_image(logo_url, origin) if logo_url else image_reference
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
