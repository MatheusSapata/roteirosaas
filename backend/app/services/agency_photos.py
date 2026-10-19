"""Fotos da própria agência para as seções que a IA monta: as que ela já usou nas outras páginas e
as que saíram dos PDFs que ela mandou ao assistente (guardadas com palavras-chave).

Ficam só dentro da agência: entram como candidatas na escolha das fotos, antes das dos bancos
gratuitos, mas não são StockImage, não são gravadas em lugar nenhum e nunca vão para o banco comum
de fotos, que serve a todos os clientes.

O encaixe é pelas palavras do lugar e da cena: "Jalapão" e "fervedouros" na seção nova acham a foto
do dia dos fervedouros da página antiga do Jalapão. Palavra que aparece em quase todas as páginas da
agência (o nome dela, "viagem", "roteiro"...) não conta; palavra que só uma página tem vale mais.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.models.agency import Agency
from app.models.media import MediaAsset
from app.models.page import Page
from app.services.pdf_photos import PDF_SOURCE

AGENCY_PROVIDER = "agencia"
MAX_PAGES = 40
MAX_PDF_PHOTOS = 200
MAX_PHOTOS = 600
MAX_PER_SLOT = 3
PLACEHOLDER_PREFIX = "data:"
PROPER_NOUN = re.compile(r"\b[A-ZÀ-Ý][a-zà-ÿ]{3,}")

# Palavras que não dizem qual é o lugar nem a cena (e as dos rótulos das seções).
COMMON_WORDS = frozenset(
    """
    dia dias viagem viagens roteiro roteiros pacote pacotes saida saidas volta para pela pelo como mais
    menos voce voces nosso nossa nossos nossas seus suas sua seu todo toda todos todas tudo cada este
    esta estes estas isso aqui onde quando muito muita foto fotos imagem imagens pagina secao titulo
    texto busca banner inicial card fundo larga cima lado carrossel destaque sozinha vitrine ordem
    artigo capa espaco cena para inclui incluso inclusos valor valores preco precos reserva reservar
    garanta vagas agora conheca venha travel trip tour tours brazil brasil with from that this your
    beautiful landscape scenic vacation people happy view family friends
    """.split()
)


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text)


def _stem(word: str) -> str:
    # Plural e o começo da palavra: praias/praia, fervedouros/fervedouro, dunas/duna.
    if len(word) > 4 and word.endswith("s"):
        word = word[:-1]
    return word[:6]


def terms(value: str) -> frozenset[str]:
    """Palavras do lugar e da cena, reduzidas (fervedouros → ferved, praias → praia)."""
    return frozenset(_stem(word) for word in _normalize(value).split() if len(word) >= 4 and word not in COMMON_WORDS)


def _plain(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("pt") or value.get("es") or next(iter(value.values()), "")
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _photo_url(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("url") or value.get("src") or value.get("image")
    if not isinstance(value, str) or not value or value.startswith(PLACEHOLDER_PREFIX):
        return None
    return value if value.startswith(("http://", "https://", "/")) else None


def section_photos(section: dict[str, Any]) -> list[tuple[str, str, str]]:
    """(endereço, texto em volta, destino próprio) de cada foto de uma seção: banner, foto,
    carrossel, dias do roteiro e cards da vitrine (o card tem a viagem dele no título)."""
    base = " ".join(_plain(section.get(key)) for key in ("title", "subtitle", "label", "caption"))
    found: list[tuple[str, str, str]] = []

    def add(value: Any, text: str, anchor: str = "") -> None:
        url = _photo_url(value)
        if url:
            found.append((url, text, anchor))

    for key in ("backgroundImage", "image"):
        add(section.get(key), base)
    for image in section.get("images") or []:
        add(image, f"{base} {_plain(image.get('caption')) if isinstance(image, dict) else ''}")
    for day in section.get("days") or []:
        if isinstance(day, dict):
            add(day.get("image"), f"{base} {_plain(day.get('title'))} {_plain(day.get('description'))[:200]}")
    for item in section.get("items") or []:
        if isinstance(item, dict):
            title = _plain(item.get("title"))
            add(item.get("image"), f"{title} {_plain(item.get('description'))[:160]}", title)
    return found


@dataclass
class Appearance:
    """Uma página (ou PDF) em que a foto aparece."""

    origin: str  # 'página "Jalapão 6 dias"' ou 'PDF "roteiro.pdf"'
    destination: frozenset[str]  # palavras do destino: título da página (ou do card da vitrine)
    words: frozenset[str]  # palavras do texto em volta da foto nessa página
    own: bool  # o destino vem do título da própria página/PDF (e não de um card que aponta para outra)


@dataclass(eq=False)
class AgencyPhoto:
    """Candidata da própria agência. Tem os mesmos campos que a escolha e a colocação das fotos
    leem de um StockImage, mas não é um modelo do banco de dados."""

    id: int  # negativo: não se confunde com as fotos dos bancos
    url: str
    origin: str
    keywords: str
    appearances: list[Appearance] = field(default_factory=list)
    credit: dict[str, str] | None = None
    provider: str = AGENCY_PROVIDER
    uses: int = 0
    width: int | None = None
    height: int | None = None
    location: str | None = None
    published_at: Any = None
    preview_url: str | None = None
    photographer: str | None = None
    source_name: str | None = None
    tracked_at: Any = None

    @property
    def alt(self) -> str:
        return f"usada pela agência: {self.origin}"

    @property
    def tags(self) -> str:
        return " ".join(self.keywords.split())[:200]

    @property
    def stored_url(self) -> str:
        return self.url

    @property
    def download_url(self) -> str:
        return self.url

    @property
    def terms(self) -> frozenset[str]:
        return frozenset().union(*(item.words for item in self.appearances))


class AgencyPhotos:
    def __init__(self, photos: list[AgencyPhoto], agency_name: str = "") -> None:
        self.photos = photos
        # O nome da agência (ex.: "Rota Sul" em todos os títulos) não diz qual é o destino.
        self.name_terms = terms(agency_name)
        # Em quantas origens (páginas ou PDFs) cada palavra aparece.
        by_origin: dict[str, set[str]] = {}
        for photo in photos:
            for item in photo.appearances:
                by_origin.setdefault(item.origin, set()).update(item.words)
        self.spread = Counter(word for words in by_origin.values() for word in words)
        origins = len(by_origin)
        # Palavra de mais da metade das páginas (com 4 ou mais): é da agência, não do lugar.
        self.common = {word for word, count in self.spread.items() if origins >= 4 and count > origins / 2}

    def match(self, text: str, *, skip_urls: Iterable[str] = (), limit: int = MAX_PER_SLOT) -> list[AgencyPhoto]:
        """Fotos do mesmo destino da vaga (cachoeira de Bonito não serve para o Jalapão); entre elas,
        sobem as que têm mais palavras da cena, e palavra de uma página só vale mais. O destino conta
        mesmo quando está em quase todas as páginas (agência que só vende Jalapão)."""
        place = terms(text) - self.name_terms
        wanted = place - self.common
        if not place:
            return []
        skip = set(skip_urls)
        scored: list[tuple[float, int, AgencyPhoto]] = []
        for order, photo in enumerate(self.photos):
            if photo.url in skip:
                continue
            matches = [item for item in photo.appearances if item.destination & place]
            if not matches:
                continue
            best = next((item for item in matches if item.own), matches[0])
            score = sum(1 / self.spread[word] for word in wanted & best.words) + (0.5 if best.own else 0)
            chosen = photo if best.origin == photo.origin else replace(photo, origin=best.origin)
            scored.append((score, -order, chosen))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [photo for _, _, photo in scored[:limit]]


def load_agency_photos(db: Session, agency_id: int | None, *, exclude_page_id: int | None = None) -> AgencyPhotos:
    """Fotos das outras páginas da agência (as mais recentes primeiro) e dos PDFs que ela mandou."""
    if not agency_id:
        return AgencyPhotos([])
    agency = db.get(Agency, agency_id)
    found: dict[str, AgencyPhoto] = {}

    def add(url: str, origin: str, text: str, destination: str, own: bool, credit: dict[str, str] | None = None) -> None:
        photo = found.get(url)
        if photo is None:
            if len(found) >= MAX_PHOTOS:
                return
            photo = found[url] = AgencyPhoto(id=-(len(found) + 1), url=url, origin=origin, keywords=text[:600], credit=credit)
        else:
            photo.credit = photo.credit or credit
        destination_terms = terms(destination)
        if destination_terms:
            photo.appearances.append(Appearance(origin, destination_terms, terms(text) | destination_terms, own))

    query = db.query(Page).filter(Page.agency_id == agency_id, Page.status.in_(("published", "draft")))
    if exclude_page_id:
        query = query.filter(Page.id != exclude_page_id)
    for page in query.order_by(Page.updated_at.desc()).limit(MAX_PAGES).all():
        config = page.config_json if isinstance(page.config_json, dict) else {}
        title = _plain(page.title) or page.slug
        for section in config.get("sections") or []:
            if not isinstance(section, dict):
                continue
            # Crédito do banco (ex.: Unsplash pede o nome do fotógrafo) segue com a foto.
            credits = {
                credit.get("url"): credit
                for credit in section.get("photoCredits") or []
                if isinstance(credit, dict) and credit.get("url")
            }
            for url, text, card in section_photos(section):
                # Card da vitrine aponta para outra viagem: o destino é o do card, não o da página.
                add(url, f'página "{title}"', f"{title} {text}", card or title, not card, credits.get(url))

    pdf_rows = (
        db.query(MediaAsset)
        .filter(MediaAsset.agency_id == agency_id, MediaAsset.keywords.isnot(None))
        .order_by(MediaAsset.id.desc())
        .limit(MAX_PDF_PHOTOS)
        .all()
    )
    for asset in pdf_rows:
        name = (asset.original_file_name or "PDF").split(" - página")[0]
        keywords = asset.keywords or ""
        # O destino de uma foto do PDF: o nome do arquivo e os nomes próprios do texto da página
        # dela ("Fervedouros do Jalapão" → Fervedouros, Jalapão; "cachoeira" é cena, não destino).
        names = " ".join(PROPER_NOUN.findall(keywords[:400]))
        add(asset.url, f'PDF "{name}"', keywords, f"{name} {names}", True)

    return AgencyPhotos(list(found.values()), agency.name if agency else "")


def mark_pdf_photos(db: Session, agency_id: int | None, sections: list[dict[str, Any]]) -> None:
    """Seção com foto tirada de um PDF da agência (a IA escreveu "Imagem: endereço") ganha a origem,
    como as fotos das outras páginas, para o editor avisar de onde veio."""
    urls = {url for section in sections for url, _, _ in section_photos(section)}
    if not agency_id or not urls:
        return
    rows = (
        db.query(MediaAsset.url, MediaAsset.original_file_name)
        .filter(MediaAsset.agency_id == agency_id, MediaAsset.source == PDF_SOURCE, MediaAsset.url.in_(urls))
        .all()
    )
    origins = {url: f'PDF "{(name or "PDF").split(" - página")[0]}"' for url, name in rows}
    for section in sections:
        found = {url: origins[url] for url, _, _ in section_photos(section) if url in origins}
        if found:
            section["aiPhotoOrigins"] = {**(section.get("aiPhotoOrigins") or {}), **found}
