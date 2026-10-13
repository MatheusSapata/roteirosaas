"""Fotos para as seções criadas pelo assistente de IA.

Busca, nesta ordem:
1) fotos cadastradas no Admin Master (banco próprio), quando as palavras-chave estão na busca;
2) a mesma busca já feita (stock_image_searches), se o banco dela continua ligado;
3) os bancos gratuitos Pixabay, Unsplash e Pexels, nessa ordem, com as chaves do Admin Master
   dentro do limite por hora de cada uma (quando uma esgota, a próxima assume);
4) só quando nenhum banco responde agora: buscas parecidas e fotos guardadas com descrição
   parecida. Busca guardada não passa na frente de uma busca nova e mais precisa.
Banco pausado no Admin Master fica de fora de tudo, inclusive das fotos já guardadas dele.

Depois a IA olha as candidatas de cada seção (photo_choice) e escolhe as que mostram o que a
seção pede. Sem fotos cadastradas nem chaves, nada é buscado e as seções ficam com a imagem
provisória.
"""
from __future__ import annotations

import logging
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.media import MediaAsset
from app.models.stock_image import StockImage, StockImageSearch
from app.models.external_api_key import ExternalApiKey
from app.services.image_api_keys import (
    IMAGE_PROVIDERS,
    ImageKey,
    available_image_keys,
    env_image_key,
    has_any_image_key,
    record_image_call,
)
from app.services.image_optimizer import optimize_image
from app.services.media_storage import media_storage
from app.services.photo_choice import PhotoSlot, choose_photos

logger = logging.getLogger(__name__)

SEARCH_TTL = timedelta(days=180)
# Fotos cadastradas à mão no Admin Master (qualquer site, com palavras-chave e crédito).
MANUAL_PROVIDER = "manual"
PER_PAGE = 30  # máximo por chamada: cada busca enche o banco com o máximo de fotos
# Para reaproveitar uma busca parecida, ela precisa cobrir esta fração das palavras da nova.
SIMILAR_SEARCH_MIN_SCORE = 0.6
STOPWORDS = frozenset(
    "a an and at by de da das do dos e em for in na nas no nos of on or para por the to with com um uma".split()
)
REQUEST_TIMEOUT = 8.0
# Tempo máximo ao aplicar uma estrutura (busca, escolha da IA e download); o que faltar fica com
# a imagem provisória. A busca para em SEARCH_SECONDS e a escolha da IA em CHOICE_SECONDS.
TIME_BUDGET_SECONDS = 40.0
SEARCH_SECONDS = 16.0
CHOICE_SECONDS = 14.0
# Texto e Imagens é um carrossel: leva mais de uma foto.
STORY_PHOTOS = 3
# Candidatas por vaga mostradas à IA, além das fotos que a vaga leva.
EXTRA_CANDIDATES = 4
MAX_CANDIDATES = 10
# Sem resultado para o destino nem para a "sensação" indicada pela IA: uma foto genérica por tipo.
FALLBACK_QUERIES = {
    "hero": "travel landscape scenic",
    "banner_card": "happy travelers vacation",
    "photo": "travel landscape scenic",
    "story": "happy travelers vacation",
    "biography": "travel agency friendly team",
    "itinerary": "travel landscape scenic",
    "links": "travel destination scenic",
}
PHOTO_FIELDS = {
    "hero": ("backgroundImage", "mobileBackgroundImage"),
    "banner_card": ("backgroundImage",),
    "photo": ("image",),
    "biography": ("image", "mobileImage"),
}


def normalize_query(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char)).lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:120]


def query_terms(value: str) -> set[str]:
    """Palavras que importam numa busca, reduzidas ao começo (street/streets, vinho/vinhos)."""
    return {word[:6] for word in normalize_query(value).split() if len(word) >= 3 and word not in STOPWORDS}


def split_queries(value: str) -> list[str]:
    """ "Gramado Brazil street | casal tomando vinho" → buscas em ordem de preferência."""
    return [part.strip() for part in re.split(r"\s*(?:\||;| ou | or )\s*", value or "") if part.strip()][:3]


# Estados e destinos brasileiros: com eles, a busca leva "Brazil" e prefere fotos daqui.
BRAZIL_HINTS = frozenset(
    """brazil brasil brazilian brasileiro brasileira acre alagoas amapa amazonas bahia ceara
    goias maranhao paraiba parana pernambuco piaui rondonia roraima sergipe tocantins pantanal
    gramado canela jericoacoara maragogi trancoso recife olinda maceio fortaleza florianopolis
    floripa buzios paraty ilhabela brotas holambra blumenau pomerode curitiba brasilia manaus
    ipanema copacabana pelourinho capitolio tiradentes ubatuba bombinhas penha garopaba""".split()
) | frozenset(
    {
        "distrito federal", "espirito santo", "mato grosso", "minas gerais", "rio de janeiro",
        "rio grande do norte", "rio grande do sul", "santa catarina", "sao paulo", "foz do iguacu",
        "fernando de noronha", "porto de galinhas", "lencois maranhenses", "chapada diamantina",
        "chapada dos veadeiros", "beto carrero", "balneario camboriu", "arraial do cabo",
        "angra dos reis", "joao pessoa", "porto seguro", "morro de sao paulo", "campos do jordao",
        "monte verde", "alter do chao", "sao miguel dos milagres", "bento goncalves",
        "vale dos vinhedos", "ouro preto", "belo horizonte", "christ the redeemer", "cristo redentor",
        "sugarloaf", "praia do forte", "salvador bahia", "pipa beach", "praia da pipa",
    }
)
BRAZIL_WORDS = frozenset({"brazil", "brasil", "brazilian", "brasileiro", "brasileira"})


def mentions_brazil(text: str) -> bool:
    padded = f" {normalize_query(text)} "
    return any(f" {hint} " in padded for hint in BRAZIL_HINTS)


def with_country(query: str) -> str:
    """Destino brasileiro sem o país na busca ganha "Brazil" (o banco acerta mais o lugar)."""
    if mentions_brazil(query) and not BRAZIL_WORDS & set(normalize_query(query).split()):
        return f"{query} Brazil"
    return query


def _published(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None
    except ValueError:
        return None


def rank_images(images: list[StockImage], query: str, *, prefer_brazil: bool = False, now: datetime | None = None) -> list[StockImage]:
    """Reordena as fotos de uma busca: descrição e tags com as palavras do destino, foto do
    Brasil quando o destino é daqui, fotos recentes e a ordem de relevância do banco."""
    now = now or datetime.now(timezone.utc)
    terms = query_terms(query) - {word[:6] for word in BRAZIL_WORDS}

    def score(item: tuple[int, StockImage]) -> float:
        position, image = item
        text = " ".join(part for part in (image.alt, image.tags, image.location) if part)
        value = -0.03 * position  # a ordem do banco ainda conta, como desempate
        if image.provider == MANUAL_PROVIDER:
            value += 4.0  # escolhida a dedo no Admin Master
        if terms:
            value += 3.0 * len(terms & query_terms(text)) / len(terms)
        if prefer_brazil and mentions_brazil(text):
            value += 2.0
        published = image.published_at
        if published is not None:
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age = (now - published).days / 365
            # Até uns 6 anos ganha ponto (mais recente, mais ponto); muito antiga perde.
            value += max(0.0, 1.5 - 0.25 * age) - (1.0 if age > 9 else 0.0)
        if image.width and image.height and image.height > image.width:
            value -= 2.5  # as seções usam fotos deitadas: em pé, o corte perde quase tudo
        return value

    ranked = sorted(enumerate(images), key=score, reverse=True)
    return [image for _, image in ranked]


def stock_search_enabled(db: Session) -> bool:
    # Fotos cadastradas no Admin Master funcionam mesmo sem chave de Unsplash/Pexels.
    return has_any_image_key(db) or db.query(StockImage.id).filter(StockImage.provider == MANUAL_PROVIDER).first() is not None


def curated_catalog(db: Session, limit: int = 120) -> list[str]:
    """Palavras-chave mais específicas das fotos cadastradas (ex.: "beto carrero nerf"), para a
    IA usar o termo exato na "Busca de imagem" e acertar a foto."""
    counts: dict[str, int] = {}
    for (tags,) in db.query(StockImage.tags).filter(StockImage.provider == MANUAL_PROVIDER).all():
        keywords = keyword_list(tags)
        longest = max((len(keyword.split()) for keyword in keywords), default=0)
        for keyword in keywords:
            # Só as mais específicas de cada foto (a do lugar + contexto); as gerais repetem.
            if len(keyword.split()) == longest:
                counts[keyword] = counts.get(keyword, 0) + 1
    ranked = sorted(counts, key=lambda keyword: (-counts[keyword], keyword))
    return ranked[:limit]


def _search_pexels(client: httpx.Client, key: str, query: str, record=None) -> list[dict[str, Any]]:
    response = client.get(
        "https://api.pexels.com/v1/search",
        params={"query": query, "per_page": PER_PAGE, "orientation": "landscape"},
        headers={"Authorization": key},
    )
    if record:
        record(response)
    response.raise_for_status()
    results = []
    for photo in response.json().get("photos") or []:
        src = photo.get("src") or {}
        download = src.get("large2x") or src.get("large") or src.get("original")
        if not download:
            continue
        results.append({
            "provider": "pexels",
            "provider_id": str(photo.get("id")),
            "download_url": download,
            "preview_url": src.get("medium") or src.get("small"),
            "page_url": photo.get("url"),
            "photographer": photo.get("photographer"),
            "photographer_url": photo.get("photographer_url"),
            "alt": (photo.get("alt") or "")[:500],
            "width": photo.get("width"),
            "height": photo.get("height"),
        })
    return results


def _search_pixabay(client: httpx.Client, key: str, query: str, record=None) -> list[dict[str, Any]]:
    # O Pixabay não permite usar a foto direto do site deles: ela é baixada e guardada
    # (materialize), como as do Pexels.
    response = client.get(
        "https://pixabay.com/api/",
        params={
            "key": key, "q": query[:100], "image_type": "photo", "orientation": "horizontal",
            "safesearch": "true", "per_page": PER_PAGE, "order": "popular",
        },
    )
    if record:
        record(response)
    if response.status_code >= 400:
        # Sem repetir o endereço: a chave do Pixabay vai nele.
        raise RuntimeError(f"Pixabay respondeu {response.status_code}")
    results = []
    for photo in response.json().get("hits") or []:
        download = photo.get("largeImageURL") or photo.get("webformatURL")
        if not download:
            continue
        user, user_id = photo.get("user") or "", photo.get("user_id")
        results.append({
            "provider": "pixabay",
            "provider_id": str(photo.get("id")),
            "download_url": download,
            "preview_url": photo.get("webformatURL") or photo.get("previewURL"),
            "page_url": photo.get("pageURL"),
            "photographer": user or None,
            "photographer_url": f"https://pixabay.com/users/{user}-{user_id}/" if user and user_id else None,
            "alt": (photo.get("tags") or "")[:500],
            "tags": (photo.get("tags") or "")[:500] or None,
            "width": photo.get("imageWidth"),
            "height": photo.get("imageHeight"),
        })
    return results


def _search_unsplash(client: httpx.Client, key: str, query: str, record=None) -> list[dict[str, Any]]:
    response = client.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": PER_PAGE, "orientation": "landscape", "content_filter": "high"},
        headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"},
    )
    if record:
        record(response)
    response.raise_for_status()
    results = []
    for photo in response.json().get("results") or []:
        raw = (photo.get("urls") or {}).get("raw")
        if not raw:
            continue
        user = photo.get("user") or {}
        results.append({
            "provider": "unsplash",
            "provider_id": str(photo.get("id")),
            # Unsplash pede link direto (hotlink) e um aviso de uso no download_location.
            "download_url": (photo.get("links") or {}).get("download_location") or raw,
            "stored_url": f"{raw}&w=2000&q=80&fm=jpg&fit=max",
            "preview_url": (photo.get("urls") or {}).get("small"),
            "page_url": (photo.get("links") or {}).get("html"),
            "photographer": user.get("name"),
            "photographer_url": (user.get("links") or {}).get("html"),
            "alt": " ".join(dict.fromkeys(part for part in (photo.get("description"), photo.get("alt_description")) if part))[:500],
            "tags": ", ".join(
                tag.get("title") for tag in photo.get("tags") or [] if isinstance(tag, dict) and tag.get("title")
            )[:500] or None,
            # O local da foto quase nunca vem na busca; o do fotógrafo ajuda a achar fotos daqui.
            "location": ((photo.get("location") or {}).get("name") or user.get("location") or "")[:255] or None,
            "published_at": _published(photo.get("created_at")),
            "width": photo.get("width"),
            "height": photo.get("height"),
        })
    return results


def _upsert_images(db: Session, results: Iterable[dict[str, Any]]) -> list[StockImage]:
    images: list[StockImage] = []
    for data in results:
        image = (
            db.query(StockImage)
            .filter(StockImage.provider == data["provider"], StockImage.provider_id == data["provider_id"])
            .first()
        )
        if image is None:
            image = StockImage(**{key: value for key, value in data.items() if key != "stored_url"})
            db.add(image)
            db.flush()
        for field in ("tags", "location", "published_at"):
            if data.get(field) and not getattr(image, field):
                setattr(image, field, data[field])
        if data.get("preview_url"):
            image.preview_url = data["preview_url"]  # a do Pixabay expira: fica a mais nova
        if data["provider"] == "unsplash" and not image.stored_url:
            image.stored_url = data.get("stored_url")
        images.append(image)
    return images


def _images_by_ids(db: Session, ids: list[int]) -> list[StockImage]:
    if not ids:
        return []
    by_id = {image.id: image for image in db.query(StockImage).filter(StockImage.id.in_(ids)).all()}
    return [by_id[image_id] for image_id in ids if image_id in by_id]


def _fresh(search: StockImageSearch, now: datetime) -> bool:
    created = search.created_at
    if created is None:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created > now - SEARCH_TTL


def _similar_search(db: Session, terms: set[str], now: datetime, allowed: set[str]) -> StockImageSearch | None:
    """Busca guardada que cobre a maior parte das palavras da nova (ex.: mesmo destino)."""
    if not terms:
        return None
    best, best_score = None, 0.0
    for search in db.query(StockImageSearch).filter(StockImageSearch.provider.in_(allowed)).all():
        other = query_terms(search.query)
        if not other or not _fresh(search, now):
            continue
        score = len(terms & other) / len(terms)
        if score > best_score or (score == best_score and best is not None and (search.uses or 0) > (best.uses or 0)):
            best, best_score = search, score
    return best if best_score >= SIMILAR_SEARCH_MIN_SCORE else None


def _photos_by_description(db: Session, terms: set[str], limit: int = PER_PAGE) -> list[StockImage]:
    """Fotos guardadas cuja descrição tem as palavras da busca (as mais usadas primeiro)."""
    if not terms:
        return []
    needed = max(1, round(len(terms) * SIMILAR_SEARCH_MIN_SCORE))
    first = sorted(terms, key=len, reverse=True)[0]
    candidates = (
        db.query(StockImage)
        .filter(or_(StockImage.alt.ilike(f"%{first}%"), StockImage.tags.ilike(f"%{first}%")))
        .limit(400)
        .all()
    )
    scored = []
    for image in candidates:
        alt_terms = query_terms(" ".join(part for part in (image.alt, image.tags, image.location) if part))
        hits = len(terms & alt_terms)
        if hits >= needed:
            scored.append((hits, image.uses or 0, image))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [image for _, _, image in scored[:limit]]


def keyword_list(value: str | None) -> list[str]:
    """ "Beto Carrero, parque; theme park" → ["beto carrero", "parque", "theme park"]."""
    seen: dict[str, None] = {}
    for part in re.split(r"[,;\n]+", value or ""):
        normalized = normalize_query(part)
        if normalized:
            seen.setdefault(normalized, None)
    return list(seen)


def _curated_matches(db: Session, terms: set[str]) -> list[StockImage]:
    """Fotos cadastradas à mão cujas palavras-chave estão na busca: uma palavra-chave conta
    quando todas as palavras dela aparecem (ex.: "beto carrero" em "Beto Carrero World Brazil")."""
    if not terms:
        return []
    scored = []
    for image in db.query(StockImage).filter(StockImage.provider == MANUAL_PROVIDER).all():
        hits = 0
        for keyword in keyword_list(image.tags):
            words = query_terms(keyword)
            if words and words <= terms:
                hits += len(words)
        if hits:
            scored.append((hits, -(image.uses or 0), image))
    # Mais palavras em comum primeiro; empate: a menos usada, para variar entre páginas.
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [image for _, _, image in scored]


def search_stock_images(db: Session, client: httpx.Client, query: str, *, minimum: int = 1) -> list[StockImage]:
    """Fotos para os termos. As cadastradas à mão no Admin Master vêm primeiro; se bastarem,
    nem consulta o resto. Depois, a mesma busca já feita ou os bancos ao vivo (_search_bank)."""
    curated = _curated_matches(db, query_terms(normalize_query(query)))
    if len(curated) >= minimum:
        return curated
    found = _search_bank(db, client, query, minimum=minimum - len(curated))
    return curated + [image for image in found if image not in curated]


def active_providers(db: Session) -> set[str]:
    """Bancos ligados no Admin Master (ou com chave de reserva no servidor), mais as fotos
    cadastradas à mão. Chave esgotada na hora continua ligada; chave pausada, não."""
    active = {MANUAL_PROVIDER} | {provider for provider in IMAGE_PROVIDERS if env_image_key(provider).strip()}
    try:
        rows = (
            db.query(ExternalApiKey.provider)
            .filter(ExternalApiKey.provider.in_(IMAGE_PROVIDERS), ExternalApiKey.is_active.is_(True))
            .distinct()
            .all()
        )
    except Exception:  # noqa: BLE001 - sem a tabela de chaves (testes), nenhum banco é cortado
        return active | set(IMAGE_PROVIDERS)
    return active | {provider for (provider,) in rows}


def _search_bank(db: Session, client: httpx.Client, query: str, *, minimum: int = 1) -> list[StockImage]:
    """1) a mesma busca, se o banco dela continua ligado; 2) os bancos ao vivo, se ainda houver
    chamadas na hora; 3) só sem banco ao vivo: busca parecida e fotos com descrição parecida."""
    normalized = normalize_query(query)
    if not normalized:
        return []
    now = datetime.now(timezone.utc)
    terms = query_terms(normalized)
    allowed = active_providers(db)

    def usable(images: list[StockImage]) -> list[StockImage]:
        return [image for image in images if image.provider in allowed]

    cached = db.query(StockImageSearch).filter(StockImageSearch.query == normalized).first()
    if cached and _fresh(cached, now) and cached.provider in allowed:
        images = usable(_images_by_ids(db, list(cached.image_ids or [])))
        if images:
            cached.uses = (cached.uses or 0) + 1
            cached.last_used_at = now
            return images

    results: list[dict[str, Any]] = []
    provider = None
    # Pixabay primeiro, depois Unsplash e Pexels (as fotos cadastradas já vieram antes); em cada
    # banco, as chaves na ordem do Admin Master. Chave esgotada na hora (ou recusada) passa a vez.
    for name, search in (("pixabay", _search_pixabay), ("unsplash", _search_unsplash), ("pexels", _search_pexels)):
        if name not in allowed:
            continue
        for key in available_image_keys(db, name):
            try:
                results = search(client, key.plain_key, query, record=lambda response, key=key: record_image_call(db, key, response))
            except Exception as exc:  # pragma: no cover - rede/limite do provedor
                logger.warning("stock_search_failed key=%s query=%r error=%s", key.ident, query, exc)
                continue
            provider = name
            break
        if provider and results:
            break

    images = _upsert_images(db, results) if provider else []
    if provider:
        if cached is None:
            cached = StockImageSearch(query=normalized)
            db.add(cached)
        cached.provider = provider
        cached.image_ids = [image.id for image in images]
        cached.created_at = now
        cached.last_used_at = now
        cached.uses = (cached.uses or 0) + 1
        db.flush()
    if images:
        return images

    # Nenhum banco respondeu agora (sem chave, limite da hora ou sem resultado): o que já está
    # guardado de bancos ligados, de uma busca parecida ou com descrição parecida.
    similar = _similar_search(db, terms, now, allowed)
    reused = usable(_images_by_ids(db, list(similar.image_ids or []))) if similar else []
    if len(reused) >= minimum:
        similar.uses = (similar.uses or 0) + 1
        similar.last_used_at = now
        return reused
    return usable(_photos_by_description(db, terms)) or reused


def materialize(db: Session, client: httpx.Client, image: StockImage) -> str | None:
    """Endereço da foto para a página: baixa e guarda a cópia otimizada só na primeira vez."""
    if image.provider == MANUAL_PROVIDER:
        return image.stored_url or image.download_url
    if image.provider == "unsplash":
        # Aviso de uso pedido pelo Unsplash: uma vez por foto, e só se ainda houver chamadas na hora.
        keys = available_image_keys(db, "unsplash") if image.tracked_at is None else []
        if keys:
            try:
                response = client.get(image.download_url, headers={"Authorization": f"Client-ID {keys[0].plain_key}"})
                record_image_call(db, keys[0], response)
                image.tracked_at = datetime.now(timezone.utc)
            except Exception:  # pragma: no cover - o aviso de uso não pode travar a página
                pass
        return image.stored_url
    if image.stored_url:
        return image.stored_url
    try:
        response = client.get(image.download_url)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - rede
        logger.warning("stock_download_failed id=%s error=%s", image.id, exc)
        return None
    variants = optimize_image(response.content)
    url = media_storage.save_image_variants(variants) if variants else media_storage.save(response.content, "foto.jpg", "image/jpeg")
    image.stored_url = url
    db.flush()
    return url


UTM = "utm_source=roteiro_online&utm_medium=referral"


def _with_utm(link: str | None) -> str:
    if not link:
        return ""
    return f"{link}{'&' if '?' in link else '?'}{UTM}"


def credit_for(image: StockImage, url: str) -> dict[str, str] | None:
    """Crédito mostrado na página: "Foto: Nome (Unsplash)", com links pedidos pelo banco.
    Foto cadastrada à mão sem autor nem fonte não leva crédito."""
    if image.provider == MANUAL_PROVIDER:
        if not (image.photographer or image.source_name):
            return None
        return {
            "url": url,
            "name": image.photographer or image.source_name or "",
            "link": image.photographer_url or "",
            "provider": image.source_name or "",
            "providerLink": image.page_url or "",
        }
    provider = image.provider.title()
    provider_home = {
        "unsplash": "https://unsplash.com/", "pexels": "https://www.pexels.com/", "pixabay": "https://pixabay.com/",
    }.get(image.provider, "")
    return {
        "url": url,
        "name": image.photographer or provider,
        "link": _with_utm(image.photographer_url),
        "provider": provider,
        "providerLink": _with_utm(provider_home),
    }


SECTION_LABELS = {
    "hero": "Banner Inicial (foto de fundo larga, com o título por cima)",
    "banner_card": "Banner em Card (foto de fundo larga)",
    "photo": "Foto em destaque (foto larga sozinha)",
    "biography": "Artigo (capa larga com o título por cima)",
    "story": "Texto e Imagens (carrossel de fotos ao lado do texto)",
    "itinerary": "Roteiro dia a dia (uma foto para cada dia, na ordem dos dias)",
    "links": "Card de viagem na vitrine",
}


def _plain_text(value: Any, limit: int) -> str:
    if isinstance(value, dict):
        value = value.get("pt") or value.get("es") or ""
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


@dataclass
class _Slot(PhotoSlot):
    queries: list[str] = field(default_factory=list)
    assign: Callable[[list[str], list[dict[str, str]]], None] | None = None
    # Troca pedida pelo usuário ("troca a foto do banner"): sempre sai uma foto nova.
    swap: bool = False


class _Picker:
    """Junta as candidatas de cada vaga, deixa a IA escolher e coloca as fotos, sem repetir na
    mesma página nem repetir a foto que a seção já tem."""

    def __init__(self, db: Session, client: httpx.Client, agency_id: int | None, exclude_urls: Iterable[str] = ()) -> None:
        self.db, self.client, self.agency_id = db, client, agency_id
        self.used: set[int] = set()
        self.started = time.monotonic()
        self.saved_urls: set[str] = set()
        # Crédito de cada foto escolhida (url → crédito), para a seção guardar.
        self.credits: dict[str, dict[str, str]] = {}
        urls = [url for url in dict.fromkeys(exclude_urls) if isinstance(url, str) and url.startswith(("http", "/"))][:200]
        # Fotos que já estão na página: "troca a foto" não devolve a mesma.
        self.excluded: set[int] = set()
        if urls:
            rows = db.query(StockImage.id).filter(or_(StockImage.stored_url.in_(urls), StockImage.download_url.in_(urls))).all()
            self.excluded = {image_id for (image_id,) in rows}

    def credits_for(self, urls: list[str]) -> list[dict[str, str]]:
        return [self.credits[url] for url in urls if url in self.credits]

    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def out_of_time(self) -> bool:
        return self.elapsed() > TIME_BUDGET_SECONDS

    def gather(self, slot: _Slot) -> None:
        """Candidatas da vaga: as melhores da primeira busca, algumas da segunda (outra
        sensação) e, se faltar, da busca genérica do tipo da seção."""
        queries = slot.queries
        prefer_brazil = bool(queries) and mentions_brazil(queries[0])
        if prefer_brazil:
            queries = [with_country(queries[0]), *queries[1:]]
        budget = min(MAX_CANDIDATES, slot.count + EXTRA_CANDIDATES)
        generic = len(queries) - 1  # a última é sempre a busca genérica do tipo
        seen: set[int] = set()
        for position, query in enumerate(queries):
            if len(slot.candidates) >= budget or self.elapsed() > SEARCH_SECONDS:
                break
            if position == generic and position > 0 and len(slot.candidates) > slot.count:
                break
            # Da primeira busca, deixa espaço para a segunda trazer outra opção.
            room = budget - len(slot.candidates) - (2 if position == 0 and generic > 1 else 0)
            found = search_stock_images(self.db, self.client, query, minimum=slot.count)
            for image in rank_images(found, query, prefer_brazil=prefer_brazil):
                if room <= 0:
                    break
                if image.id in seen or image.id in self.excluded or image.id in self.used:
                    continue
                seen.add(image.id)
                slot.candidates.append(image)
                room -= 1

    def place(self, slot: _Slot, ordered: list[StockImage]) -> int:
        urls: list[str] = []
        for image in ordered:
            if len(urls) >= slot.count or self.out_of_time():
                break
            if image.id in self.used:
                continue
            url = materialize(self.db, self.client, image)
            if not url:
                continue
            self.used.add(image.id)
            image.uses = (image.uses or 0) + 1
            urls.append(url)
            credit = credit_for(image, url)
            if credit:
                self.credits[url] = credit
            self._add_to_library(url, image)
        if urls and slot.assign:
            slot.assign(urls, self.credits_for(urls))
        return len(urls)

    def _add_to_library(self, url: str, image: StockImage) -> None:
        # A foto entra na biblioteca de mídia da agência, para ela reaproveitar no editor.
        if not self.agency_id or url in self.saved_urls:
            return
        self.saved_urls.add(url)
        exists = self.db.query(MediaAsset).filter(MediaAsset.agency_id == self.agency_id, MediaAsset.url == url).first()
        if not exists:
            credit = f"{image.provider.title()} - {image.photographer or 'banco de fotos'}"
            self.db.add(MediaAsset(agency_id=self.agency_id, url=url, type="image", original_file_name=credit[:255]))


def _section_context(section: dict[str, Any]) -> str:
    kind = section.get("type")
    parts = [SECTION_LABELS.get(kind, kind or "Seção")]
    title = _plain_text(section.get("title"), 90)
    if title:
        parts.append(f'título "{title}"')
    detail = _plain_text(section.get("subtitle") or section.get("text") or section.get("description"), 160)
    if detail:
        parts.append(f'texto "{detail}"')
    return " · ".join(parts)


def _photo_slots(sections: list[dict[str, Any]]) -> list[_Slot]:
    """Uma vaga por seção com foto pedida (e uma por card da vitrine)."""
    slots: list[_Slot] = []

    swap = False

    def add(context: str, raw_query: str, fallback: str, count: int, assign) -> None:
        queries = split_queries(raw_query or "") + [fallback]
        slots.append(_Slot(key=f"V{len(slots) + 1}", context=f"{context} · busca: {raw_query or fallback}",
                           count=count, queries=queries, assign=assign, swap=swap))

    for section in sections:
        kind = section.get("type")
        swap = bool(section.get("aiReplaces"))
        raw_query = section.pop("aiImageQuery", None)
        context = _section_context(section)
        if kind in PHOTO_FIELDS and raw_query is not None:
            def assign(urls, credits, section=section, kind=kind):
                for field_name in PHOTO_FIELDS[kind]:
                    section[field_name] = urls[0]
                section["aiStockPhoto"] = True
                section["photoCredits"] = credits[:1]
            add(context, raw_query, FALLBACK_QUERIES.get(kind, "travel"), 1, assign)
        elif kind == "story" and raw_query is not None:
            def assign(urls, credits, section=section):
                section["images"] = urls
                section["aiStockPhoto"] = True
                section["photoCredits"] = credits
            add(context, raw_query, FALLBACK_QUERIES["story"], STORY_PHOTOS, assign)
        elif kind == "itinerary" and raw_query is not None:
            days = [day for day in section.get("days") or [] if isinstance(day, dict)]
            if days:
                def assign(urls, credits, section=section, days=days):
                    for day, url in zip(days, urls):
                        day["image"] = url
                    section["aiStockPhoto"] = True
                    section["photoCredits"] = credits
                day_names = "; ".join(_plain_text(day.get("title"), 50) for day in days if day.get("title"))
                add(f"{context} · dias: {day_names}" if day_names else context, raw_query, FALLBACK_QUERIES["itinerary"], len(days), assign)
        if kind == "links":
            for item in section.get("items") or []:
                if not isinstance(item, dict):
                    continue
                item_query = item.pop("aiImageQuery", None)
                # Card ligado a uma página usa a foto dela; numa troca, só o card com foto pedida.
                if item.get("pageSlug") or (swap and item_query is None):
                    continue
                title = _plain_text(item.get("title"), 80)

                def assign(urls, credits, section=section, item=item):
                    item["image"] = urls[0]
                    section.setdefault("photoCredits", []).extend(credits[:1])
                    section["aiStockPhoto"] = True
                add(f'{SECTION_LABELS["links"]} · viagem "{title}"', item_query or title, FALLBACK_QUERIES["links"], 1, assign)
    return slots


def clear_photo_queries(sections: list[dict[str, Any]]) -> None:
    for section in sections:
        section.pop("aiImageQuery", None)
        for item in section.get("items") or []:
            if isinstance(item, dict):
                item.pop("aiImageQuery", None)


def fill_section_photos(
    db: Session,
    sections: list[dict[str, Any]],
    agency_id: int | None = None,
    *,
    exclude_urls: Iterable[str] = (),
    ai_choice: bool = True,
) -> int:
    """Troca as imagens provisórias das seções da IA por fotos dos bancos.

    Para cada vaga junta candidatas da "Busca de imagem" (o lugar e, em seguida, a sensação) e de
    uma busca genérica do tipo; a IA olha as candidatas e escolhe; sem a IA, vale o ranking.
    exclude_urls: fotos que já estão na página (a troca não devolve a mesma). Devolve quantas
    fotos foram colocadas."""
    has_queries = any(
        section.get("aiImageQuery") is not None
        or any(isinstance(item, dict) and item.get("aiImageQuery") is not None for item in section.get("items") or [])
        or (section.get("type") == "links" and not section.get("aiReplaces"))
        for section in sections
    )
    if not has_queries or not stock_search_enabled(db):
        clear_photo_queries(sections)
        return 0
    filled = 0
    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        picker = _Picker(db, client, agency_id, exclude_urls)
        slots = _photo_slots(sections)
        for slot in slots:
            picker.gather(slot)
        choice = None
        if ai_choice:
            choice = choose_photos(db, client, slots, timeout=min(CHOICE_SECONDS, TIME_BUDGET_SECONDS - picker.elapsed() - 6))
        for slot in slots:
            if picker.out_of_time():
                logger.info("stock_photos_time_budget_reached filled=%s", filled)
                break
            if choice is not None and slot.key in choice and (choice[slot.key] or not slot.swap):
                picked = choice[slot.key]
                # A IA escolheu menos fotos que o carrossel ou o roteiro pedem: completa com o ranking.
                rest = [image for image in slot.candidates if image not in picked] if picked and slot.count > 1 else []
                ordered = picked + rest
            else:
                # Sem a escolha da IA, ou troca pedida em que a IA recusou todas: vale o ranking (o
                # usuário pediu outra foto; ficar com a mesma parece que nada aconteceu).
                ordered = slot.candidates
            filled += picker.place(slot, ordered)
        clear_photo_queries(sections)
    db.commit()
    return filled
