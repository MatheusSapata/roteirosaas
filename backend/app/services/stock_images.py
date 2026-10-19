"""Fotos para as seções criadas pelo assistente de IA.

Busca, nesta ordem:
1) fotos cadastradas no Admin Master (banco próprio), quando as palavras-chave estão na busca;
2) os bancos gratuitos Pixabay, Unsplash e Pexels, nessa ordem, com as chaves do Admin Master
   dentro do limite por hora de cada uma (quando uma esgota, a próxima assume).
Toda busca vai ao banco na hora: não há busca guardada (a mesma busca devolvia sempre as mesmas
fotos). As buscas de uma página saem ao mesmo tempo, e a foto já baixada antes é reaproveitada.

Depois a IA olha as candidatas de cada seção (photo_choice) e escolhe as que mostram o que a
seção pede. Vaga sem fotos (ou com poucas), ou em que a IA recusou todas, ganha buscas novas
sugeridas pela IA (da mais refinada para a mais ampla) e tenta de novo; por último, a busca
genérica do tipo da seção. Sem fotos cadastradas nem chaves, nada é buscado e as seções ficam com
a imagem provisória.
"""
from __future__ import annotations

import logging
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.media import MediaAsset
from app.services.agency_photos import AGENCY_PROVIDER, AgencyPhotos, load_agency_photos, section_photos
from app.models.stock_image import StockImage
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
from app.services.photo_choice import PhotoSlot, choose_photos, refine_queries

logger = logging.getLogger(__name__)

# Fotos cadastradas à mão no Admin Master (qualquer site, com palavras-chave e crédito).
MANUAL_PROVIDER = "manual"
PER_PAGE = 30  # máximo por chamada
STOPWORDS = frozenset(
    "a an and at by de da das do dos e em for in na nas no nos of on or para por the to with com um uma".split()
)
REQUEST_TIMEOUT = 8.0
# Tempo máximo para preparar as fotos de uma estrutura (buscas, ajustes da IA, escolha e
# download); o que faltar fica com a imagem provisória. Novas buscas só até SEARCH_SECONDS, cada
# escolha da IA até CHOICE_SECONDS e cada pedido de buscas novas até REFINE_SECONDS.
TIME_BUDGET_SECONDS = 40.0
SEARCH_SECONDS = 24.0
CHOICE_SECONDS = 14.0
REFINE_SECONDS = 7.0
# Buscas ao mesmo tempo nos bancos e downloads ao mesmo tempo.
PARALLEL_SEARCHES = 6
PARALLEL_DOWNLOADS = 6
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


def _searchers() -> dict[str, Callable[..., list[dict[str, Any]]]]:
    # Lido na hora (e não guardado no módulo) para os testes poderem trocar a busca de um banco.
    return {"pixabay": _search_pixabay, "unsplash": _search_unsplash, "pexels": _search_pexels}


# Pixabay primeiro, depois Unsplash e Pexels (as fotos cadastradas já vieram antes).
PROVIDER_ORDER = ("pixabay", "unsplash", "pexels")


def _key_plan(db: Session, allowed: set[str]) -> list[tuple[str, list[ImageKey]]]:
    """Bancos ligados com chamada sobrando na hora, cada um com as chaves na ordem do Admin Master."""
    plan = []
    for name in PROVIDER_ORDER:
        if name not in allowed:
            continue
        keys = available_image_keys(db, name)
        if keys:
            plan.append((name, keys))
    return plan


def _live_search(client: httpx.Client, plan: list[tuple[str, list[ImageKey]]], query: str) -> tuple[str | None, list[dict[str, Any]], list[tuple[ImageKey, Any]]]:
    """Uma busca nos bancos, sem tocar no banco de dados (roda em paralelo com as outras).
    Chave recusada passa a vez à próxima; banco sem resultado passa a vez ao próximo banco.
    Devolve o banco que achou, os resultados e as chamadas feitas (para contar no limite)."""
    calls: list[tuple[ImageKey, Any]] = []
    searchers = _searchers()
    for name, keys in plan:
        for key in keys:
            try:
                results = searchers[name](client, key.plain_key, query, record=lambda response, key=key: calls.append((key, response)))
            except Exception as exc:  # pragma: no cover - rede/limite do provedor
                logger.warning("stock_search_failed key=%s query=%r error=%s", key.ident, query, exc)
                continue
            if results:
                return name, results, calls
            break
    return None, [], calls


class _BankSearch:
    """Buscas de uma página: saem ao mesmo tempo e a mesma busca não vai duas vezes ao banco.
    Vale só durante o preparo da página (nada fica guardado para a próxima)."""

    def __init__(self, db: Session, client: httpx.Client) -> None:
        self.db, self.client = db, client
        self.allowed = active_providers(db)
        self.results: dict[str, list[StockImage]] = {}

    def run(self, requests: Iterable[tuple[str, int]]) -> None:
        """requests: (busca, fotos que a vaga leva). As cadastradas à mão vêm primeiro; se
        bastarem, a busca nem vai aos bancos."""
        pending: list[str] = []
        for query, minimum in requests:
            normalized = normalize_query(query)
            if not normalized or normalized in self.results or query in pending:
                continue
            curated = _curated_matches(self.db, query_terms(normalized))
            self.results[normalized] = curated
            if len(curated) < minimum:
                pending.append(query)
        if not pending:
            return
        plan = _key_plan(self.db, self.allowed)
        if not plan:
            return
        with ThreadPoolExecutor(max_workers=min(PARALLEL_SEARCHES, len(pending))) as pool:
            outcomes = list(pool.map(lambda query: (query, _live_search(self.client, plan, query)), pending))
        for query, (provider, found, calls) in outcomes:
            for key, response in calls:
                record_image_call(self.db, key, response)
            images = [image for image in _upsert_images(self.db, found) if image.provider in self.allowed] if provider else []
            normalized = normalize_query(query)
            curated = self.results.get(normalized, [])
            self.results[normalized] = curated + [image for image in images if image not in curated]
        self.db.flush()

    def get(self, query: str) -> list[StockImage]:
        return self.results.get(normalize_query(query), [])


def search_stock_images(db: Session, client: httpx.Client, query: str, *, minimum: int = 1) -> list[StockImage]:
    """Fotos para os termos: as cadastradas à mão no Admin Master primeiro (se bastarem, nem
    consulta o resto) e depois os bancos ao vivo."""
    bank = _BankSearch(db, client)
    bank.run([(query, minimum)])
    return bank.get(query)


def _needs_download(image: StockImage) -> bool:
    """Foto que precisa ser baixada e guardada (Pixabay e Pexels na primeira vez)."""
    return image.provider not in (MANUAL_PROVIDER, "unsplash") and not image.stored_url


def prepare_download(client: httpx.Client, url: str) -> tuple[bytes, dict[int, bytes] | None] | None:
    """Baixa e otimiza uma foto, sem tocar no banco de dados (roda em paralelo com as outras)."""
    try:
        response = client.get(url)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - rede
        logger.warning("stock_download_failed url=%s error=%s", url[:120], exc)
        return None
    return response.content, optimize_image(response.content)


def store_prepared(db: Session, image: StockImage, prepared: tuple[bytes, dict[int, bytes] | None]) -> str:
    content, variants = prepared
    url = media_storage.save_image_variants(variants) if variants else media_storage.save(content, "foto.jpg", "image/jpeg")
    image.stored_url = url
    db.flush()
    return url


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
    prepared = prepare_download(client, image.download_url)
    return store_prepared(db, image, prepared) if prepared else None


UTM = "utm_source=roteiro_online&utm_medium=referral"


def _with_utm(link: str | None) -> str:
    if not link:
        return ""
    return f"{link}{'&' if '?' in link else '?'}{UTM}"


def credit_for(image: StockImage, url: str) -> dict[str, str] | None:
    """Crédito mostrado na página: "Foto: Nome (Unsplash)", com links pedidos pelo banco.
    Foto cadastrada à mão sem autor nem fonte não leva crédito. Foto da própria agência leva o
    crédito que já tinha na outra página (foto de banco) ou nenhum (foto dela)."""
    if image.provider == AGENCY_PROVIDER:
        return dict(image.credit) if getattr(image, "credit", None) else None
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
    # Buscas da IA (o lugar, depois a sensação) e a busca genérica do tipo da seção.
    queries: list[str] = field(default_factory=list)
    fallback: str = ""
    prefer_brazil: bool = False
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
        # Fotos já baixadas e otimizadas (em paralelo), à espera de serem guardadas.
        self.prepared: dict[int, tuple[bytes, dict[int, bytes] | None]] = {}
        # Crédito de cada foto escolhida (url → crédito), para a seção guardar.
        self.credits: dict[str, dict[str, str]] = {}
        urls = [url for url in dict.fromkeys(exclude_urls) if isinstance(url, str) and url.startswith(("http", "/"))][:200]
        # Fotos que já estão na página: "troca a foto" não devolve a mesma.
        self.excluded: set[int] = set()
        self.excluded_urls: set[str] = set(urls)
        # Endereços já colocados (a foto da agência pode ser a mesma de um banco) e, das fotos da
        # própria agência, de onde cada uma veio (para o editor avisar).
        self.used_urls: set[str] = set()
        self.origins: dict[str, str] = {}
        if urls:
            rows = db.query(StockImage.id).filter(or_(StockImage.stored_url.in_(urls), StockImage.download_url.in_(urls))).all()
            self.excluded = {image_id for (image_id,) in rows}

    def credits_for(self, urls: list[str]) -> list[dict[str, str]]:
        return [self.credits[url] for url in urls if url in self.credits]

    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def out_of_time(self) -> bool:
        return self.elapsed() > TIME_BUDGET_SECONDS

    def budget(self, slot: _Slot) -> int:
        return min(MAX_CANDIDATES, slot.count + EXTRA_CANDIDATES)

    def needs_more(self, slot: _Slot) -> bool:
        """Poucas opções para a IA escolher (ou nenhuma): vale pedir buscas novas."""
        return len(slot.candidates) < min(self.budget(slot), slot.count + 2)

    def choice_timeout(self) -> float:
        return min(CHOICE_SECONDS, TIME_BUDGET_SECONDS - self.elapsed() - 6)

    def gather(self, slot: _Slot, bank: _BankSearch, queries: list[str]) -> None:
        """Junta à vaga as candidatas das buscas, na ordem: as melhores da primeira e, se houver
        mais de uma busca, espaço para a segunda trazer outra opção."""
        budget = self.budget(slot)
        seen = {image.id for image in slot.candidates} | {image.id for image in slot.rejected}
        for position, query in enumerate(queries):
            if len(slot.candidates) >= budget:
                break
            if query not in slot.tried:
                slot.tried.append(query)
            room = budget - len(slot.candidates) - (2 if position == 0 and len(queries) > 1 else 0)
            for image in rank_images(bank.get(query), query, prefer_brazil=slot.prefer_brazil):
                if room <= 0:
                    break
                if image.id in seen or image.id in self.excluded or image.id in self.used:
                    continue
                seen.add(image.id)
                slot.candidates.append(image)
                room -= 1

    def add_agency(self, slot: _Slot, agency: AgencyPhotos) -> None:
        """Fotos da própria agência (outras páginas e PDFs) que combinam com a vaga entram na frente
        das dos bancos."""
        if not agency.photos:
            return
        text = " ".join([slot.context, *slot.queries])
        taken = {image.id for image in slot.candidates}
        found = [
            photo
            for photo in agency.match(text, skip_urls=self.excluded_urls | self.used_urls, limit=max(3, slot.count))
            if photo.id not in taken
        ]
        slot.candidates[:0] = found

    def refine(self, bank: _BankSearch, slots: list[_Slot]) -> None:
        """Vagas sem fotos (ou com poucas): a IA sugere buscas novas, da mais refinada para a mais
        ampla, e elas saem ao mesmo tempo."""
        if not slots or self.elapsed() > SEARCH_SECONDS:
            return
        suggestions = refine_queries(self.db, slots, timeout=min(REFINE_SECONDS, SEARCH_SECONDS - self.elapsed()))
        if not suggestions:
            return
        queries = {
            slot.key: [with_country(query) if slot.prefer_brazil else query for query in suggestions.get(slot.key, [])]
            for slot in slots
        }
        bank.run((query, slot.count) for slot in slots for query in queries[slot.key])
        for slot in slots:
            if queries[slot.key]:
                self.gather(slot, bank, queries[slot.key])

    def retry_refused(self, bank: _BankSearch, slots: list[_Slot]) -> dict[str, list[StockImage]] | None:
        """A IA recusou todas as candidatas: buscas novas (contando o que foi recusado) e outra
        escolha. Devolve a nova escolha ({} se nada mudou; None se a IA não respondeu)."""
        if not slots or self.elapsed() > SEARCH_SECONDS:
            return {}
        for slot in slots:
            slot.rejected.extend(slot.candidates)
            slot.candidates = []
        self.refine(bank, slots)
        retry = [slot for slot in slots if slot.candidates]
        for slot in slots:
            if not slot.candidates:
                # Nada novo: volta às recusadas (a troca pedida ainda usa o ranking delas).
                slot.candidates, slot.rejected = slot.rejected, []
        if not retry:
            return {}
        return choose_photos(self.db, self.client, retry, timeout=self.choice_timeout())

    def prefetch(self, plans: list[tuple[_Slot, list[StockImage]]]) -> None:
        """Baixa ao mesmo tempo as fotos que vão para a página (as escolhidas e uma reserva por vaga)."""
        targets: dict[int, str] = {}
        for slot, ordered in plans:
            for image in [image for image in ordered if image.id not in self.used][: slot.count + 1]:
                if _needs_download(image) and image.id not in self.prepared:
                    targets[image.id] = image.download_url
        if not targets or self.out_of_time():
            return
        with ThreadPoolExecutor(max_workers=min(PARALLEL_DOWNLOADS, len(targets))) as pool:
            results = list(pool.map(lambda item: (item[0], prepare_download(self.client, item[1])), targets.items()))
        self.prepared.update({image_id: prepared for image_id, prepared in results if prepared})

    def _url_for(self, image: StockImage) -> str | None:
        if image.provider == AGENCY_PROVIDER:
            return image.stored_url  # já está guardada (página ou PDF da agência)
        prepared = self.prepared.pop(image.id, None)
        if prepared and _needs_download(image):
            return store_prepared(self.db, image, prepared)
        return materialize(self.db, self.client, image)

    def place(self, slot: _Slot, ordered: list[StockImage]) -> int:
        urls: list[str] = []
        for image in ordered:
            if len(urls) >= slot.count or self.out_of_time():
                break
            if image.id in self.used:
                continue
            url = self._url_for(image)
            if not url or url in self.used_urls:
                continue
            self.used.add(image.id)
            self.used_urls.add(url)
            image.uses = (image.uses or 0) + 1
            urls.append(url)
            credit = credit_for(image, url)
            if credit:
                self.credits[url] = credit
            if image.provider == AGENCY_PROVIDER:
                self.origins[url] = image.origin  # já é da agência: não volta para a biblioteca
            else:
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
        queries = split_queries(raw_query or "")
        # Destino brasileiro: a primeira busca leva "Brazil" e as fotos daqui sobem no ranking.
        prefer_brazil = bool(queries) and mentions_brazil(queries[0])
        if prefer_brazil:
            queries[0] = with_country(queries[0])
        slots.append(_Slot(key=f"V{len(slots) + 1}", context=f"{context} · busca: {raw_query or fallback}",
                           count=count, queries=queries, fallback=fallback, prefer_brazil=prefer_brazil,
                           assign=assign, swap=swap))

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
    exclude_page_id: int | None = None,
) -> int:
    """Troca as imagens provisórias das seções da IA por fotos da própria agência e dos bancos.

    Para cada vaga junta candidatas: as fotos da agência que combinam (das outras páginas dela e
    dos PDFs que ela mandou) e as da "Busca de imagem" (o lugar e, em seguida, a sensação); com
    poucas, a IA sugere buscas novas e, por último, entra a busca genérica do tipo. A IA olha as
    candidatas e escolhe (recusou todas: outra rodada de buscas); sem a IA, vale o ranking.
    exclude_urls: fotos que já estão na página (a troca não devolve a mesma); exclude_page_id: a
    página que está sendo editada (as fotos dela não contam como "de outra página"). A seção com
    foto da agência ganha "aiPhotoOrigins" ({foto: de onde veio}), para o editor avisar. Devolve quantas
    fotos foram colocadas."""
    has_queries = any(
        section.get("aiImageQuery") is not None
        or any(isinstance(item, dict) and item.get("aiImageQuery") is not None for item in section.get("items") or [])
        or (section.get("type") == "links" and not section.get("aiReplaces"))
        for section in sections
    )
    if not has_queries:
        clear_photo_queries(sections)
        return 0
    agency = load_agency_photos(db, agency_id, exclude_page_id=exclude_page_id)
    if not stock_search_enabled(db) and not agency.photos:
        clear_photo_queries(sections)
        return 0
    filled = 0
    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        picker = _Picker(db, client, agency_id, exclude_urls)
        # Fotos que a resposta já trouxe (ex.: do PDF enviado, em "Imagem:") não se repetem nas vagas.
        picker.used_urls.update(url for section in sections for url, _, _ in section_photos(section))
        slots = _photo_slots(sections)
        bank = _BankSearch(db, client)
        # 1) As buscas da IA de todas as vagas ao mesmo tempo (o lugar e a sensação); as fotos da
        #    própria agência que combinam vão na frente.
        bank.run((query, slot.count) for slot in slots for query in slot.queries)
        for slot in slots:
            picker.gather(slot, bank, slot.queries)
            picker.add_agency(slot, agency)
        # 2) Vaga sem fotos ou com poucas: a IA sugere buscas mais refinadas (ou mais amplas).
        if ai_choice:
            picker.refine(bank, [slot for slot in slots if picker.needs_more(slot)])
        # 3) Ainda faltando: a busca genérica do tipo da seção.
        short = [slot for slot in slots if len(slot.candidates) <= slot.count and slot.fallback]
        bank.run((slot.fallback, slot.count) for slot in short)
        for slot in short:
            picker.gather(slot, bank, [slot.fallback])
        # 4) A IA escolhe olhando as fotos; 5) vaga em que ela recusou todas ganha outra rodada.
        choice = None
        if ai_choice:
            choice = choose_photos(db, client, slots, timeout=picker.choice_timeout())
            refused = [slot for slot in slots if choice is not None and slot.key in choice and not choice[slot.key] and slot.candidates]
            if refused:
                second = picker.retry_refused(bank, refused)
                for slot in refused:
                    if second is None:
                        choice.pop(slot.key, None)  # sem a IA na segunda rodada: vale o ranking das novas
                    elif slot.key in second:
                        choice[slot.key] = second[slot.key]
        plans: list[tuple[_Slot, list[StockImage]]] = []
        for slot in slots:
            if choice is not None and slot.key in choice and (choice[slot.key] or not slot.swap):
                picked = choice[slot.key]
                # A IA escolheu menos fotos que o carrossel ou o roteiro pedem: completa com o ranking.
                rest = [image for image in slot.candidates if image not in picked] if picked and slot.count > 1 else []
                plans.append((slot, picked + rest))
            else:
                # Sem a escolha da IA, ou troca pedida em que a IA recusou todas: vale o ranking (o
                # usuário pediu outra foto; ficar com a mesma parece que nada aconteceu).
                plans.append((slot, slot.candidates))
        # 6) Coloca as fotos: os downloads saem ao mesmo tempo.
        picker.prefetch(plans)
        for slot, ordered in plans:
            if picker.out_of_time():
                logger.info("stock_photos_time_budget_reached filled=%s", filled)
                break
            filled += picker.place(slot, ordered)
        clear_photo_queries(sections)
        if picker.origins:
            for section in sections:
                origins = {url: picker.origins[url] for url, _, _ in section_photos(section) if url in picker.origins}
                if origins:
                    section["aiPhotoOrigins"] = origins
    db.commit()
    return filled
