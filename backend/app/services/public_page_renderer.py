from __future__ import annotations

import html
import io
import json
import hashlib
import re
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
MAX_OG_SOURCE_BYTES = 30 * 1024 * 1024
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


def _resolve_page_share_description(page: PublicPageOut, fallback_title: str, agency_name: str) -> str:
    config = page.config if isinstance(page.config, dict) else {}
    general = config.get("general") if isinstance(config, dict) else None
    if isinstance(general, dict):
        short_description = general.get("shortDescription")
        if isinstance(short_description, str):
            trimmed = short_description.strip()
            if trimmed:
                return trimmed

    seo_description = page.seo_description
    if isinstance(seo_description, str):
        trimmed = seo_description.strip()
        if trimmed:
            return trimmed

    sections = config.get("sections") if isinstance(config, dict) else None
    if isinstance(sections, list):
        hero = next((item for item in sections if isinstance(item, dict) and item.get("type") == "hero"), None)
        if hero:
            subtitle = hero.get("subtitle")
            if isinstance(subtitle, dict):
                subtitle = subtitle.get("pt") or subtitle.get("es") or next(iter(subtitle.values()), "")
            if isinstance(subtitle, str):
                trimmed = re.sub(r"<[^>]+>", "", subtitle).strip()
                if trimmed:
                    return trimmed

    return f"{agency_name} preparou um roteiro personalizado: {fallback_title}."


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
    final_title = (page.title or "").strip() or "Roteiro Online"

    description = _resolve_page_share_description(page, page.title, agency_name)

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


# Mesmo padrão do front (utils/media.ts): imagens enviadas com versões leves em WebP.
_VARIANT_RE = re.compile(r"_2400\.webp(?=$|[?#])")
_VARIANT_WIDTHS = (640, 1280, 2400)
# Larguras que o Banner Inicial v2 ocupa (V2Hero.vue): o pré-carregamento pede a mesma versão.
_HERO_SIZES = {"split": "(max-width: 640px) 100vw, 50vw"}
_HERO_MOBILE_MEDIA = "(max-width: 640px)"


def _responsive_srcset(url: str) -> str:
    if not _VARIANT_RE.search(url):
        return ""
    return ", ".join(f"{_VARIANT_RE.sub(f'_{width}.webp', url)} {width}w" for width in _VARIANT_WIDTHS)


def _image_preload_tag(url: str, sizes: str, media: Optional[str] = None) -> str:
    attrs = [f'rel="preload"', 'as="image"', f'href="{html.escape(url)}"', 'fetchpriority="high"']
    srcset = _responsive_srcset(url)
    if srcset:
        attrs += [f'imagesrcset="{html.escape(srcset)}"', f'imagesizes="{html.escape(sizes)}"']
    if media:
        attrs.append(f'media="{html.escape(media)}"')
    return f"<link {' '.join(attrs)} />"


# Mesmo endereço do @import de v2.css: pedido aqui, chega em paralelo e o @import usa o cache.
_V2_FONTS_HREF = (
    "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800"
    "&family=Figtree:wght@400;500;600;700&display=swap"
)


def _absolute(value: object) -> Optional[str]:
    url = str(value or "").strip()
    return url if url.startswith(("https://", "http://")) else None


def _v2_visible_sections(page: PublicPageOut) -> Optional[list[dict]]:
    config = page.config
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except ValueError:
            return None
    if not isinstance(config, dict) or not page.design_v2_enabled or config.get("design") == "legacy":
        return None
    return [section for section in config.get("sections") or [] if isinstance(section, dict) and section.get("enabled")]


def _hero_preload_tags(page: PublicPageOut) -> list[str]:
    """Pede no HTML, antes do JavaScript, o que a primeira tela do visual novo usa.

    Fontes do visual novo (sem travar a pintura), foto do Banner Inicial quando ele é a
    primeira seção (depois do Menu do topo) e logo da agência. Endereços relativos ficam de
    fora: o front pode resolvê-los em outro domínio e a imagem seria baixada duas vezes.
    """
    sections = _v2_visible_sections(page)
    if sections is None:
        return []
    tags = [
        f'<link rel="stylesheet" href="{html.escape(_V2_FONTS_HREF)}" media="print" onload="this.media=\'all\'" />',
    ]
    hero = next((section for section in sections if section.get("type") == "hero"), None)
    first = next((section for section in sections if section.get("type") != "header"), None)
    has_header = any(section.get("type") == "header" for section in sections)

    if first is not None and first is hero:
        layout = hero.get("layout") or "immersive"
        # Imersivo e Clássico com vídeo mostram o vídeo no lugar da foto.
        if not (layout in {"immersive", "classic"} and str(hero.get("videoUrl") or "").strip()):
            image = _absolute(hero.get("backgroundImage"))
            mobile = _absolute(hero.get("mobileBackgroundImage")) if layout == "immersive" else None
            sizes = _HERO_SIZES.get(layout, "100vw")
            if image and mobile:
                tags.append(_image_preload_tag(image, sizes, "(min-width: 641px)"))
                tags.append(_image_preload_tag(mobile, "100vw", _HERO_MOBILE_MEDIA))
            elif image:
                tags.append(_image_preload_tag(image, sizes))

    # Logo do Menu do topo ou do Banner Inicial: o do banner (se a página trocou) ou o da agência.
    if has_header or (first is not None and first is hero):
        logo = _absolute((hero or {}).get("logoUrl")) or _absolute((page.branding or {}).get("logo_url"))
        if logo:
            tags.append(_image_preload_tag(logo, "320px"))
    return tags


def _page_data_script(page: PublicPageOut, path: str) -> str:
    """Os dados da página já no HTML: o front monta a página sem esperar a chamada à API.

    É a mesma resposta da API pública (serialize_public_page), com as mesmas regras do plano
    da agência (marca do plano gratuito, página fora do ar sem assinatura ativa). `path` diz
    para qual endereço ela vale; o front só usa se for o endereço aberto.
    """
    payload = json.dumps({"path": path, "page": page.model_dump(mode="json")}, ensure_ascii=False, separators=(",", ":"))
    # Dentro de <script>, "</" e "<!--" encerrariam a tag; \u2028/\u2029 quebram JS antigo.
    payload = payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return f'<script id="ro-page-data" type="application/json">{payload}</script>'


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
    preload_tags = _hero_preload_tags(page_data)
    if preload_tags:
        meta_block += "    " + "\n    ".join(preload_tags) + "\n"
    meta_block += "    " + _page_data_script(page_data, urlsplit(canonical_url).path) + "\n"
    base_html = _load_frontend_template()
    return _replace_default_meta(base_html, meta_block)
