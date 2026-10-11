"""Fotos de bancos gratuitos (Pexels e Unsplash) para as seções criadas pelo assistente de IA.

Cada busca e cada foto ficam guardadas (stock_image_searches / stock_images) e são
reaproveitadas antes de qualquer chamada: a mesma busca, uma busca parecida ("Gramado Brazil
street" ≈ "Gramado street winter") ou fotos guardadas cuja descrição tem as mesmas palavras.
Só então o banco de fotos é consultado, com as chaves do Admin Master em ordem, dentro do
limite por hora de cada uma (a chave inicial do Unsplash dá 50 chamadas por hora, contando
buscas e avisos de uso); quando uma esgota, a próxima assume.
Sem PEXELS_API_KEY nem UNSPLASH_ACCESS_KEY, nada é buscado e as seções ficam com a
imagem provisória.
"""
from __future__ import annotations

import logging
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.media import MediaAsset
from app.models.stock_image import StockImage, StockImageSearch
from app.services.image_api_keys import ImageKey, available_image_keys, has_any_image_key, record_image_call
from app.services.image_optimizer import optimize_image
from app.services.media_storage import media_storage

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
# Tempo máximo buscando fotos ao aplicar uma estrutura; o que faltar fica com a imagem provisória.
TIME_BUDGET_SECONDS = 25.0
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
            "page_url": photo.get("url"),
            "photographer": photo.get("photographer"),
            "photographer_url": photo.get("photographer_url"),
            "alt": (photo.get("alt") or "")[:500],
            "width": photo.get("width"),
            "height": photo.get("height"),
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


def _similar_search(db: Session, terms: set[str], now: datetime) -> StockImageSearch | None:
    """Busca guardada que cobre a maior parte das palavras da nova (ex.: mesmo destino)."""
    if not terms:
        return None
    best, best_score = None, 0.0
    for search in db.query(StockImageSearch).filter(StockImageSearch.provider.isnot(None)).all():
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
    nem consulta o resto. Depois, reaproveita o banco antes de chamar Unsplash ou Pexels."""
    curated = _curated_matches(db, query_terms(normalize_query(query)))
    if len(curated) >= minimum:
        return curated
    found = _search_bank(db, client, query, minimum=minimum - len(curated))
    return curated + [image for image in found if image not in curated]


def _search_bank(db: Session, client: httpx.Client, query: str, *, minimum: int = 1) -> list[StockImage]:
    """1) a mesma busca; 2) uma busca parecida; 3) fotos guardadas com descrição parecida;
    4) o banco de fotos, se ainda houver chamadas na hora."""
    normalized = normalize_query(query)
    if not normalized:
        return []
    now = datetime.now(timezone.utc)
    terms = query_terms(normalized)

    cached = db.query(StockImageSearch).filter(StockImageSearch.query == normalized).first()
    if cached and _fresh(cached, now) and (cached.image_ids or cached.provider is None):
        cached.uses = (cached.uses or 0) + 1
        cached.last_used_at = now
        return _images_by_ids(db, list(cached.image_ids or []))

    similar = _similar_search(db, terms, now)
    reused = _images_by_ids(db, list(similar.image_ids or [])) if similar else []
    if len(reused) >= minimum:
        similar.uses = (similar.uses or 0) + 1
        similar.last_used_at = now
        return reused

    described = _photos_by_description(db, terms)
    if len(described) >= max(minimum, 3):
        return described

    results: list[dict[str, Any]] = []
    provider = None
    # Unsplash primeiro, depois Pexels; em cada banco, as chaves na ordem do Admin Master.
    # Chave esgotada na hora (ou recusada) passa a vez para a próxima.
    for name, search in (("unsplash", _search_unsplash), ("pexels", _search_pexels)):
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
    if provider is None:
        # Sem chamadas na hora: o que o banco local tiver, mesmo pouco.
        return reused or described

    images = _upsert_images(db, results)
    if cached is None:
        cached = StockImageSearch(query=normalized)
        db.add(cached)
    cached.provider = provider
    cached.image_ids = [image.id for image in images]
    cached.created_at = now
    cached.last_used_at = now
    cached.uses = (cached.uses or 0) + 1
    db.flush()
    return images or reused or described


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
    provider_home = {"unsplash": "https://unsplash.com/", "pexels": "https://www.pexels.com/"}.get(image.provider, "")
    return {
        "url": url,
        "name": image.photographer or provider,
        "link": _with_utm(image.photographer_url),
        "provider": provider,
        "providerLink": _with_utm(provider_home),
    }


class _Picker:
    """Escolhe fotos sem repetir na mesma página, dentro do tempo máximo."""

    def __init__(self, db: Session, client: httpx.Client, agency_id: int | None) -> None:
        self.db, self.client, self.agency_id = db, client, agency_id
        self.used: set[int] = set()
        self.started = time.monotonic()
        self.saved_urls: set[str] = set()
        # Crédito de cada foto escolhida (url → crédito), para a seção guardar.
        self.credits: dict[str, dict[str, str]] = {}

    def credits_for(self, urls: list[str]) -> list[dict[str, str]]:
        return [self.credits[url] for url in urls if url in self.credits]

    def out_of_time(self) -> bool:
        return time.monotonic() - self.started > TIME_BUDGET_SECONDS

    def pick(self, queries: list[str], count: int = 1) -> list[str]:
        urls: list[str] = []
        # Destino no Brasil: a busca do lugar leva "Brazil" e todas preferem fotos daqui.
        prefer_brazil = bool(queries) and mentions_brazil(queries[0])
        if prefer_brazil:
            queries = [with_country(queries[0]), *queries[1:]]
        for query in queries:
            if len(urls) >= count or self.out_of_time():
                break
            found = search_stock_images(self.db, self.client, query, minimum=count + len(self.used))
            for image in rank_images(found, query, prefer_brazil=prefer_brazil):
                if len(urls) >= count or self.out_of_time():
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
        return urls

    def _add_to_library(self, url: str, image: StockImage) -> None:
        # A foto entra na biblioteca de mídia da agência, para ela reaproveitar no editor.
        if not self.agency_id or url in self.saved_urls:
            return
        self.saved_urls.add(url)
        exists = self.db.query(MediaAsset).filter(MediaAsset.agency_id == self.agency_id, MediaAsset.url == url).first()
        if not exists:
            credit = f"{image.provider.title()} - {image.photographer or 'banco de fotos'}"
            self.db.add(MediaAsset(agency_id=self.agency_id, url=url, type="image", original_file_name=credit[:255]))


def fill_section_photos(db: Session, sections: list[dict[str, Any]], agency_id: int | None = None) -> int:
    """Troca as imagens provisórias das seções da IA por fotos dos bancos gratuitos.

    Usa a "Busca de imagem" de cada seção (destino e, em seguida, a sensação), e por fim uma
    busca genérica do tipo. Devolve quantas fotos foram colocadas."""
    pending = [section for section in sections if section.get("aiImageQuery") is not None]
    if not pending or not stock_search_enabled(db):
        for section in sections:
            section.pop("aiImageQuery", None)
            for item in section.get("items") or []:
                if isinstance(item, dict):
                    item.pop("aiImageQuery", None)
        return 0
    filled = 0
    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        picker = _Picker(db, client, agency_id)
        for section in sections:
            kind = section.get("type")
            raw_query = section.pop("aiImageQuery", None)
            queries = split_queries(raw_query or "") + [FALLBACK_QUERIES.get(kind, "travel")]
            if kind in PHOTO_FIELDS and raw_query is not None:
                urls = picker.pick(queries)
                if urls:
                    for field in PHOTO_FIELDS[kind]:
                        section[field] = urls[0]
                    section["aiStockPhoto"] = True
                    section["photoCredits"] = picker.credits_for(urls[:1])
                    filled += 1
            elif kind == "story" and raw_query is not None:
                urls = picker.pick(queries)
                if urls:
                    section["images"] = urls
                    section["aiStockPhoto"] = True
                    section["photoCredits"] = picker.credits_for(urls)
                    filled += 1
            elif kind == "itinerary" and raw_query is not None:
                days = [day for day in section.get("days") or [] if isinstance(day, dict)]
                urls = picker.pick(queries, count=len(days))
                for day, url in zip(days, urls):
                    day["image"] = url
                if urls:
                    section["aiStockPhoto"] = True
                    section["photoCredits"] = picker.credits_for(urls)
                    filled += len(urls)
            if kind == "links":
                for item in section.get("items") or []:
                    if not isinstance(item, dict):
                        continue
                    item_query = item.pop("aiImageQuery", None)
                    if item.get("pageSlug"):
                        continue  # o card ligado a uma página usa a foto dela
                    item_queries = split_queries(item_query or "") or [str(item.get("title") or "")]
                    urls = picker.pick(item_queries + [FALLBACK_QUERIES["links"]])
                    if urls:
                        item["image"] = urls[0]
                        section.setdefault("photoCredits", []).extend(picker.credits_for(urls[:1]))
                        filled += 1
            if picker.out_of_time():
                logger.info("stock_photos_time_budget_reached filled=%s", filled)
                break
        for section in sections:
            section.pop("aiImageQuery", None)
            for item in section.get("items") or []:
                if isinstance(item, dict):
                    item.pop("aiImageQuery", None)
    db.commit()
    return filled
