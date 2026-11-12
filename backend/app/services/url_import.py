"""Importa o conteúdo de uma página externa para o assistente de IA: busca a página com
navegador headless (sites que montam o conteúdo via JavaScript não aparecem no HTML cru),
extrai o texto principal e as imagens, baixa as imagens e devolve tudo no formato que o
assistente já entende (``ChatAttachment``, o mesmo das fotos anexadas no chat)."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import socket
import threading
from dataclasses import dataclass, field
from typing import Literal
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
# servidor se várias pessoas colarem um link junto. É um semáforo de thread (e não do asyncio)
# porque a importação do site inteiro roda numa thread própria, com outro event loop: um
# asyncio.Semaphore fica preso ao loop da primeira espera e quebra quando usado pelos dois.
_browser_semaphore = threading.BoundedSemaphore(2)
_BROWSER_WAIT_POLL_S = 0.5


class UrlImportError(Exception):
    """Erro para mostrar direto ao usuário (link inválido, bloqueado, página vazia...)."""


# --- Classificação: página de uma viagem ("specific") ou página central com várias ("central") ---

# Mínimo de cards de viagem (cada um levando para um link diferente) para tratar a página como a
# principal de um site. Uma página de viagem costuma ter no máximo 2 ou 3 "viagens relacionadas"
# no rodapé; uma home de agência lista bem mais que isso. Com 4, um carrossel de "outras viagens"
# ainda pode enganar, por isso a página com roteiro dia a dia próprio (Dia 1, Dia 2, Dia 3 fora
# dos cards) continua "specific" mesmo com 4 ou mais cards.
MIN_TRIP_CARDS = 4
# Teto de cards guardados na classificação (o job de importação usa só os primeiros 20).
MAX_TRIP_CARDS = 60
# Um card tem um link principal (às vezes repetido na foto, no título e no botão). Subindo do
# preço/botão até achar o link, um bloco com mais links diferentes que isso já é a grade inteira.
MAX_LINKS_PER_CARD = 3
# Quantos níveis de HTML subir, a partir do preço ou do botão, procurando o bloco do card.
CARD_CLIMB_LEVELS = 6
CARD_TEXT_CHARS = 300

# Preço em real (e as moedas mais comuns em pacote internacional): "R$ 999,99", "R$1.290", "US$ 850".
# "\s*" (e não só um espaço) é de propósito: o preço de verdade de muitos sites vem quebrado em
# várias linhas no HTML ("R$\n   \n  680,00"), lado a lado na tela mas separado por quebras de
# linha e tabulação no código-fonte.
PRICE_RE = re.compile(r"(?:R\$|US\$|U\$|USD|EUR|€|£)\s*\d{1,3}(?:[.\s]?\d{3})*(?:,\d{1,2})?", re.IGNORECASE)
# Botão típico de card de viagem.
CTA_RE = re.compile(
    r"\b(saiba mais|ver mais|veja mais|ver detalhes|mais detalhes|detalhes|ver roteiro|ver pacote|ver viagem|"
    r"ver oferta|conhe[cç]a|quero conhecer|quero ir|mais informa[cç](?:ão|ões|ao|oes)|confira|reservar|reserve)\b",
    re.IGNORECASE,
)
# "Dia 1", "dia 02", "1º dia", "2o dia": marca de roteiro dia a dia.
_ITINERARY_RE = re.compile(r"\bdia\s*0?(\d{1,2})\b|\b(\d{1,2})\s*[ºo°]\s*dia\b", re.IGNORECASE)
# Redes sociais, WhatsApp e mapas aparecem em todo card ("Reservar pelo WhatsApp") e nunca são a viagem.
_IGNORED_LINK_HOSTS = (
    "wa.me", "whatsapp.com", "instagram.com", "facebook.com", "fb.com", "youtube.com", "youtu.be",
    "tiktok.com", "twitter.com", "x.com", "linkedin.com", "pinterest.com", "google.com", "goo.gl", "t.me",
)
_IGNORED_LINK_SCHEMES = ("mailto:", "tel:", "javascript:", "whatsapp:", "sms:", "data:")
_FILE_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".zip", ".mp4")


@dataclass(slots=True)
class TripLink:
    """Um card de viagem achado numa página central: link absoluto e o texto do card."""

    url: str
    title: str
    price: str
    text: str


@dataclass(slots=True)
class PageClassification:
    kind: Literal["specific", "central"]
    trip_links: list[TripLink]


def normalize_url(url: str) -> str:
    """Forma de comparar dois links: sem esquema, sem "www.", sem âncora e sem barra no fim.
    Usada para achar o mesmo link escrito de jeitos diferentes (http/https, com e sem barra)."""
    parsed = urlparse((url or "").strip())
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{host}{path}{query}"


def _trip_href(href: str | None, base_url: str, page_key: str) -> str | None:
    """Link absoluto que pode ser de uma viagem, ou None (âncora, WhatsApp, rede social, arquivo,
    a própria página ou a raiz do site, que é o link do logo)."""
    href = (href or "").strip()
    if not href or href.startswith("#") or href.lower().startswith(_IGNORED_LINK_SCHEMES):
        return None
    absolute = urljoin(base_url, href).split("#", 1)[0]
    parsed = urlparse(absolute)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        return None
    if any(host == item or host.endswith(f".{item}") for item in _IGNORED_LINK_HOSTS):
        return None
    if parsed.path.lower().endswith(_FILE_EXTENSIONS):
        return None
    key = normalize_url(absolute)
    if key == page_key or not parsed.path.strip("/") and not parsed.query:
        return None
    return absolute


def _links_in(element, base_url: str, page_key: str) -> list[str]:
    anchors = ([element] if element.name == "a" and element.get("href") else []) + element.find_all("a", href=True)
    found: dict[str, str] = {}
    for anchor in anchors:
        url = _trip_href(anchor.get("href"), base_url, page_key)
        if url:
            found.setdefault(normalize_url(url), url)
    return list(found.values())


def _card_around(start, base_url: str, page_key: str):
    """Sobe do preço (ou do botão) até o bloco que tem o link do card. Devolve (bloco, link) ou None.
    Depois de achar o link, continua subindo enquanto o bloco de cima não traz nenhum link novo,
    para pegar o card inteiro (foto e título costumam estar ao lado do preço, não dentro)."""
    element = start
    for _ in range(CARD_CLIMB_LEVELS):
        if element is None or element.name in (None, "body", "html", "[document]"):
            return None
        links = _links_in(element, base_url, page_key)
        if len(links) > MAX_LINKS_PER_CARD:
            return None
        if links:
            keys = {normalize_url(link) for link in links}
            parent = element.parent
            while parent is not None and parent.name not in ("body", "html", "[document]"):
                parent_keys = {normalize_url(link) for link in _links_in(parent, base_url, page_key)}
                if parent_keys != keys:
                    break
                element, parent = parent, parent.parent
            return element, links[0]
        element = element.parent
    return None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _card_title(card, link: str) -> str:
    heading = card.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    if heading and _clean(heading.get_text(" ")):
        return _clean(heading.get_text(" "))[:160]
    titled = card.find(class_=re.compile(r"(title|titulo|nome|name)", re.IGNORECASE))
    if titled and _clean(titled.get_text(" ")):
        return _clean(titled.get_text(" "))[:160]
    texts = [
        _clean(anchor.get_text(" "))
        for anchor in ([card] if card.name == "a" else []) + card.find_all("a")
        if _clean(anchor.get_text(" ")) and not CTA_RE.fullmatch(_clean(anchor.get_text(" ")))
    ]
    texts = [text for text in texts if not PRICE_RE.search(text) or len(text) > 40]
    if texts:
        return max(texts, key=len)[:160]
    image = card.find("img", alt=True)
    if image and _clean(image.get("alt")):
        return _clean(image.get("alt"))[:160]
    # Último recurso: o fim do link ("/pacote-gramado-5-dias" vira "Pacote gramado 5 dias").
    slug = urlparse(link).path.rstrip("/").rsplit("/", 1)[-1]
    return _clean(re.sub(r"[-_]+", " ", slug)).capitalize()[:160]


def _classify_soup(soup: BeautifulSoup, url: str) -> PageClassification:
    page_key = normalize_url(url)
    starts: list = []
    # Sinal 1: preços. Cada preço "R$ ..." com um link por perto é um card de viagem.
    for node in soup.find_all(string=PRICE_RE):
        if node.parent is not None and node.parent.name not in ("script", "style", "noscript", "title"):
            starts.append(node.parent)
    # Sinal 2: botões "Saiba mais"/"Ver roteiro" (cards sem preço). Só vale com título no card.
    cta_starts = {
        id(anchor)
        for anchor in soup.find_all("a", href=True)
        if len(_clean(anchor.get_text(" "))) <= 40 and CTA_RE.search(_clean(anchor.get_text(" ")))
    }
    starts.extend(anchor for anchor in soup.find_all("a", href=True) if id(anchor) in cta_starts)

    cards: dict[str, TripLink] = {}
    containers: list = []
    for start in starts:
        found = _card_around(start, url, page_key)
        if not found:
            continue
        card, link = found
        key = normalize_url(link)
        if key in cards:
            continue
        text = _clean(card.get_text(" "))
        price_match = PRICE_RE.search(text)
        has_heading = card.find(["h1", "h2", "h3", "h4", "h5", "h6"]) is not None
        if id(start) in cta_starts and not price_match and not has_heading:
            continue  # botão solto (ex.: "Saiba mais sobre a agência"), sem cara de card
        cards[key] = TripLink(
            url=link,
            title=_card_title(card, link),
            price=_clean(price_match.group(0)) if price_match else "",
            text=text[:CARD_TEXT_CHARS],
        )
        containers.append(card)
        if len(cards) >= MAX_TRIP_CARDS:
            break

    trip_links = list(cards.values())
    if len(trip_links) < MIN_TRIP_CARDS:
        return PageClassification(kind="specific", trip_links=[])

    # Página de uma viagem com carrossel de "outras viagens": tem o próprio roteiro dia a dia
    # (Dia 1, Dia 2 e Dia 3) fora dos cards. Continua sendo "specific".
    inside = {id(card) for card in containers}
    outside_text: list[str] = []
    for node in soup.find_all(string=True):
        parent = node.parent
        if parent is None or parent.name in ("script", "style", "noscript"):
            continue
        if any(id(ancestor) in inside for ancestor in [parent, *parent.parents]):
            continue
        outside_text.append(str(node))
    days = {int(a or b) for a, b in _ITINERARY_RE.findall(" ".join(outside_text))}
    if {1, 2, 3} <= days:
        return PageClassification(kind="specific", trip_links=[])
    return PageClassification(kind="central", trip_links=trip_links)


def classify_page(html: str, url: str) -> PageClassification:
    """Diz se a página é de uma viagem só ("specific") ou a principal de um site, listando várias
    viagens ("central"), e no segundo caso devolve os links de cada viagem com título e preço.

    Sinais genéricos, sem depender de plataforma: (1) preços ("R$ 999,99") com um link por perto e
    (2) botões de card ("Saiba mais", "Ver roteiro") num bloco com título. Cada sinal sobe pelo HTML
    até o bloco do card; links diferentes viram cards. Com MIN_TRIP_CARDS ou mais, é "central"."""
    return _classify_soup(BeautifulSoup(html or "", "html.parser"), url)


@dataclass(slots=True)
class ImportedPage:
    title: str
    text: str
    image_urls: list[str]
    kind: Literal["specific", "central"] = "specific"
    trip_links: list[TripLink] = field(default_factory=list)

    @property
    def is_central(self) -> bool:
        return self.kind == "central"


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

    # Espera a vaga sem bloquear o event loop e sem prender permissão se a requisição for cancelada.
    while not _browser_semaphore.acquire(blocking=False):
        await asyncio.sleep(_BROWSER_WAIT_POLL_S)
    try:
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
    finally:
        _browser_semaphore.release()


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
    soup = BeautifulSoup(html, "html.parser")
    classification = _classify_soup(soup, url)
    text = (
        trafilatura.extract(
            html, url=url, include_comments=False, include_tables=True, favor_recall=True
        )
        or ""
    ).strip()
    # Home de agência pode não ter "texto principal" (só cards): ainda serve, pelos links.
    if not text and classification.kind != "central":
        raise UrlImportError("Não encontrei conteúdo nessa página. Confira o link e tente de novo.")
    if len(text) > MAX_PAGE_TEXT_CHARS:
        text = text[:MAX_PAGE_TEXT_CHARS].rsplit(" ", 1)[0] + "…"

    title_tag = soup.find("title")
    og_title = soup.find("meta", property="og:title")
    title = (
        (og_title.get("content") if og_title else None)
        or (title_tag.get_text(strip=True) if title_tag else None)
        or urlparse(url).hostname
        or url
    )
    return ImportedPage(
        title=title.strip(),
        text=text,
        image_urls=_candidate_images(soup, url),
        kind=classification.kind,
        trip_links=classification.trip_links,
    )


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


async def scrape_page(url: str) -> ImportedPage:
    """Busca a página (navegador headless) e extrai título, texto, imagens candidatas e a
    classificação (viagem específica ou página central), sem baixar as imagens ainda."""
    _ensure_public_http_url(url)
    html = await _fetch_rendered_html(url)
    return _extract(html, url)


async def download_page_images(page: ImportedPage) -> list[ChatAttachment]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        downloads = await asyncio.gather(*(_download_image(client, src) for src in page.image_urls))
    return [item for item in downloads if item is not None]


async def import_page(url: str) -> tuple[ImportedPage, list[ChatAttachment]]:
    """Busca a página (navegador headless), extrai texto e imagens, baixa as imagens e devolve
    pronto para entrar na mesma conversa do assistente de IA."""
    page = await scrape_page(url)
    return page, await download_page_images(page)


def build_url_context_block(url: str, page: ImportedPage) -> str:
    """Texto raspado no formato de bloco de contexto da IA (o mesmo do chat e da importação do site)."""
    return (
        f"CONTEÚDO EXTRAÍDO DO LINK ENVIADO ({url}). Use estas informações (título, texto, preço, "
        'itinerário etc.) para montar a página, como se o usuário tivesse descrito a viagem:\n'
        f"Título da página: {page.title}\n\n{page.text}"
    )
