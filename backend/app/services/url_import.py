"""Importa o conteúdo de uma página externa para o assistente de IA: busca a página com
navegador headless (sites que montam o conteúdo via JavaScript não aparecem no HTML cru),
extrai o texto principal e as imagens, baixa as imagens e devolve tudo no formato que o
assistente já entende (``ChatAttachment``, o mesmo das fotos anexadas no chat)."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

from app.services.ai_assistant import ChatAttachment, normalize_chat_attachment

logger = logging.getLogger(__name__)

MAX_PAGE_TEXT_CHARS = 8000
MAX_IMAGES = 10
MAX_IMAGE_BYTES = 8 * 1024 * 1024
PAGE_LOAD_TIMEOUT_S = 25
IMAGE_FETCH_TIMEOUT_S = 15
# Imagem pequena demais para ser foto de capa/ambiente (ícone, selo, pixel de rastreio).
MIN_IMAGE_WIDTH = 200

# Chromium headless é pesado: no máximo duas raspagens ao mesmo tempo, para não derrubar o
# servidor se várias pessoas colarem um link junto.
_browser_semaphore = asyncio.Semaphore(2)


class UrlImportError(Exception):
    """Erro para mostrar direto ao usuário (link inválido, bloqueado, página vazia...)."""


@dataclass(slots=True)
class ImportedPage:
    title: str
    text: str
    image_urls: list[str]


def _ensure_public_http_url(url: str) -> None:
    """Barra esquema que não seja http(s) e endereço que resolva para rede interna (SSRF):
    sem isso, um link tipo http://169.254.169.254/ ou http://localhost:5432 faria o servidor
    bater em si mesmo ou na rede interna da VPS a pedido de quem só devia poder colar um link
    de agência de viagem."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UrlImportError("Link inválido. Use um endereço começando com http:// ou https://.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise UrlImportError("Não consegui encontrar esse endereço.") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise UrlImportError("Esse endereço não pode ser acessado.")


async def _fetch_rendered_html(url: str) -> str:
    """Renderiza a página num Chromium headless e devolve o HTML final (depois do JavaScript
    rodar). Sites que nunca terminam de carregar (contador, chat ao vivo) ainda devolvem o que
    já carregou: o navegador não trava a raspagem esperando um recurso que nunca some."""
    from playwright.async_api import async_playwright  # import tardio: só quando a raspagem roda

    async with _browser_semaphore:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (compatible; RoteiroOnlineImportBot/1.0; +https://roteiro.online)"
                )
                page.set_default_navigation_timeout(PAGE_LOAD_TIMEOUT_S * 1000)
                try:
                    await page.goto(url, wait_until="networkidle")
                except Exception:
                    logger.info("url_import_navigation_timeout url=%s", url)
                return await page.content()
            finally:
                await browser.close()


def _candidate_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Imagem de capa (og:image) primeiro, depois as do corpo da página, maiores que um ícone."""
    candidates: list[str] = []
    for meta_name in ("og:image", "og:image:secure_url", "twitter:image"):
        tag = soup.find("meta", property=meta_name) or soup.find("meta", attrs={"name": meta_name})
        if tag and tag.get("content"):
            candidates.append(tag["content"])
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src or src.startswith("data:"):
            continue
        width = img.get("width")
        try:
            if width and int(float(width)) < MIN_IMAGE_WIDTH:
                continue
        except ValueError:
            pass
        candidates.append(src)

    seen: set[str] = set()
    result: list[str] = []
    for src in candidates:
        absolute = urljoin(base_url, src.strip())
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https") or absolute in seen:
            continue
        seen.add(absolute)
        result.append(absolute)
        if len(result) >= MAX_IMAGES:
            break
    return result


def _extract(html: str, url: str) -> ImportedPage:
    text = (
        trafilatura.extract(
            html, url=url, include_comments=False, include_tables=True, favor_recall=True
        )
        or ""
    ).strip()
    if not text:
        raise UrlImportError("Não encontrei conteúdo nessa página. Confira o link e tente de novo.")
    if len(text) > MAX_PAGE_TEXT_CHARS:
        text = text[:MAX_PAGE_TEXT_CHARS].rsplit(" ", 1)[0] + "…"

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    og_title = soup.find("meta", property="og:title")
    title = (
        (og_title.get("content") if og_title else None)
        or (title_tag.get_text(strip=True) if title_tag else None)
        or urlparse(url).hostname
        or url
    )
    return ImportedPage(title=title.strip(), text=text, image_urls=_candidate_images(soup, url))


async def _download_image(client: httpx.AsyncClient, url: str) -> ChatAttachment | None:
    try:
        _ensure_public_http_url(url)
        async with client.stream("GET", url, timeout=IMAGE_FETCH_TIMEOUT_S) as response:
            if response.status_code != 200:
                return None
            content_type = (response.headers.get("content-type") or "").split(";")[0].strip()
            if not content_type.startswith("image/"):
                return None
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > MAX_IMAGE_BYTES:
                    return None
            filename = urlparse(url).path.rsplit("/", 1)[-1] or "imagem"
            return normalize_chat_attachment(
                ChatAttachment(filename=filename, content_type=content_type, data=bytes(data))
            )
    except UrlImportError:
        return None
    except Exception:
        logger.warning("url_import_image_failed url=%s", url)
        return None


async def import_page(url: str) -> tuple[ImportedPage, list[ChatAttachment]]:
    """Busca a página (navegador headless), extrai texto e imagens, baixa as imagens e devolve
    pronto para entrar na mesma conversa do assistente de IA."""
    _ensure_public_http_url(url)
    html = await _fetch_rendered_html(url)
    page = _extract(html, url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        downloads = await asyncio.gather(*(_download_image(client, src) for src in page.image_urls))
    attachments = [item for item in downloads if item is not None]
    return page, attachments
