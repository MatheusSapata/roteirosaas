"""Fotos de bancos gratuitos (Pexels e Unsplash) para as seções criadas pelo assistente de IA.

Cada busca e cada foto ficam guardadas (stock_image_searches / stock_images): os mesmos
termos não consultam o banco de novo e uma foto já usada não é baixada outra vez.
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
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.media import MediaAsset
from app.models.stock_image import StockImage, StockImageSearch
from app.services.image_optimizer import optimize_image
from app.services.media_storage import media_storage

logger = logging.getLogger(__name__)

SEARCH_TTL = timedelta(days=30)
PER_PAGE = 12
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


def split_queries(value: str) -> list[str]:
    """ "Gramado Brazil street | casal tomando vinho" → buscas em ordem de preferência."""
    return [part.strip() for part in re.split(r"\s*(?:\||;| ou | or )\s*", value or "") if part.strip()][:3]


def stock_search_enabled() -> bool:
    settings = get_settings()
    return bool(settings.pexels_api_key or settings.unsplash_access_key)


def _search_pexels(client: httpx.Client, key: str, query: str) -> list[dict[str, Any]]:
    response = client.get(
        "https://api.pexels.com/v1/search",
        params={"query": query, "per_page": PER_PAGE, "orientation": "landscape"},
        headers={"Authorization": key},
    )
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


def _search_unsplash(client: httpx.Client, key: str, query: str) -> list[dict[str, Any]]:
    response = client.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": PER_PAGE, "orientation": "landscape", "content_filter": "high"},
        headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"},
    )
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
            "alt": (photo.get("alt_description") or "")[:500],
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
        if data["provider"] == "unsplash" and not image.stored_url:
            image.stored_url = data.get("stored_url")
        images.append(image)
    return images


def search_stock_images(db: Session, client: httpx.Client, query: str) -> list[StockImage]:
    """Fotos para os termos, do banco de buscas quando já feita há menos de 30 dias."""
    normalized = normalize_query(query)
    if not normalized:
        return []
    now = datetime.now(timezone.utc)
    cached = db.query(StockImageSearch).filter(StockImageSearch.query == normalized).first()
    if cached and cached.created_at and cached.created_at.replace(tzinfo=cached.created_at.tzinfo or timezone.utc) > now - SEARCH_TTL:
        cached.uses = (cached.uses or 0) + 1
        cached.last_used_at = now
        ids = list(cached.image_ids or [])
        by_id = {image.id: image for image in db.query(StockImage).filter(StockImage.id.in_(ids)).all()} if ids else {}
        return [by_id[image_id] for image_id in ids if image_id in by_id]

    settings = get_settings()
    results: list[dict[str, Any]] = []
    provider = None
    for name, key, search in (
        ("pexels", settings.pexels_api_key, _search_pexels),
        ("unsplash", settings.unsplash_access_key, _search_unsplash),
    ):
        if not key:
            continue
        try:
            results = search(client, key, query)
        except Exception as exc:  # pragma: no cover - rede/limite do provedor
            logger.warning("stock_search_failed provider=%s query=%r error=%s", name, query, exc)
            continue
        if results:
            provider = name
            break

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
    return images


def materialize(db: Session, client: httpx.Client, image: StockImage) -> str | None:
    """Endereço da foto para a página: baixa e guarda a cópia otimizada só na primeira vez."""
    if image.provider == "unsplash":
        try:
            client.get(image.download_url, headers={"Authorization": f"Client-ID {get_settings().unsplash_access_key}"})
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


class _Picker:
    """Escolhe fotos sem repetir na mesma página, dentro do tempo máximo."""

    def __init__(self, db: Session, client: httpx.Client, agency_id: int | None) -> None:
        self.db, self.client, self.agency_id = db, client, agency_id
        self.used: set[int] = set()
        self.started = time.monotonic()
        self.saved_urls: set[str] = set()

    def out_of_time(self) -> bool:
        return time.monotonic() - self.started > TIME_BUDGET_SECONDS

    def pick(self, queries: list[str], count: int = 1) -> list[str]:
        urls: list[str] = []
        for query in queries:
            if len(urls) >= count or self.out_of_time():
                break
            for image in search_stock_images(self.db, self.client, query):
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
    if not pending or not stock_search_enabled():
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
                    filled += 1
            elif kind == "story" and raw_query is not None:
                urls = picker.pick(queries)
                if urls:
                    section["images"] = urls
                    section["aiStockPhoto"] = True
                    filled += 1
            elif kind == "itinerary" and raw_query is not None:
                days = [day for day in section.get("days") or [] if isinstance(day, dict)]
                urls = picker.pick(queries, count=len(days))
                for day, url in zip(days, urls):
                    day["image"] = url
                if urls:
                    section["aiStockPhoto"] = True
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
