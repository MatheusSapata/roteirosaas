"""Admin Master: fotos cadastradas à mão (qualquer site), com palavras-chave e crédito.

O assistente de IA usa estas fotos antes de buscar no Unsplash e no Pexels, sempre que as
palavras-chave aparecem na busca. A foto é baixada e guardada otimizada no nosso
armazenamento, para a página não depender do site de origem.
"""
from __future__ import annotations

import hashlib
import io
import ipaddress
import socket
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.stock_image import StockImage
from app.models.user import User
from app.services.image_optimizer import optimize_image
from app.services.media_storage import media_storage
from app.services.stock_images import MANUAL_PROVIDER, keyword_list

router = APIRouter(prefix="/master/stock-photos")

MAX_BYTES = 15 * 1024 * 1024
RAW_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class StockPhotoIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=1000)
    keywords: str = Field(..., min_length=2, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500)
    author: Optional[str] = Field(default=None, max_length=255)
    author_url: Optional[str] = Field(default=None, max_length=500)
    source_name: Optional[str] = Field(default=None, max_length=120)
    source_url: Optional[str] = Field(default=None, max_length=500)


class StockPhotoUpdate(BaseModel):
    keywords: Optional[str] = Field(default=None, min_length=2, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500)
    author: Optional[str] = Field(default=None, max_length=255)
    author_url: Optional[str] = Field(default=None, max_length=500)
    source_name: Optional[str] = Field(default=None, max_length=120)
    source_url: Optional[str] = Field(default=None, max_length=500)


class StockPhotoOut(BaseModel):
    id: int
    url: str
    original_url: str
    keywords: list[str]
    description: Optional[str]
    author: Optional[str]
    author_url: Optional[str]
    source_name: Optional[str]
    source_url: Optional[str]
    width: Optional[int]
    height: Optional[int]
    uses: int
    created_at: Optional[datetime]


def _out(image: StockImage) -> StockPhotoOut:
    return StockPhotoOut(
        id=image.id,
        url=image.stored_url or image.download_url,
        original_url=image.download_url,
        keywords=keyword_list(image.tags),
        description=image.alt,
        author=image.photographer,
        author_url=image.photographer_url,
        source_name=image.source_name,
        source_url=image.page_url,
        width=image.width,
        height=image.height,
        uses=image.uses or 0,
        created_at=image.created_at,
    )


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _link(value: str | None) -> str | None:
    value = _clean(value)
    if value and urlparse(value).scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Os links precisam começar com http:// ou https://.")
    return value


def _check_public_host(url: str) -> None:
    """Só baixa de endereços públicos (nada da rede interna do servidor)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Informe o endereço completo da imagem (http:// ou https://).")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="Não encontramos o site dessa imagem.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(status_code=400, detail="Endereço de imagem não permitido.")


def download_photo(url: str) -> tuple[str, int | None, int | None]:
    """Baixa a imagem, guarda a cópia otimizada e devolve (endereço, largura, altura)."""
    _check_public_host(url)
    headers = {"User-Agent": "RoteiroOnline/1.0 (+https://roteiroonline.com)"}
    try:
        with httpx.Client(timeout=20, follow_redirects=True, headers=headers) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
                if not content_type.startswith("image/"):
                    raise HTTPException(
                        status_code=400,
                        detail="Esse link não é de uma imagem. Abra a foto, clique com o botão direito e copie o endereço da imagem.",
                    )
                data = b""
                for chunk in response.iter_bytes():
                    data += chunk
                    if len(data) > MAX_BYTES:
                        raise HTTPException(status_code=400, detail="Imagem grande demais (máximo de 15 MB).")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Não foi possível baixar a imagem: {exc}") from exc
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Não conseguimos abrir essa imagem.") from exc
    variants = optimize_image(data)
    if variants:
        return media_storage.save_image_variants(variants), width, height
    extension = RAW_TYPES.get(content_type)
    if not extension:
        raise HTTPException(status_code=400, detail="Use uma imagem JPG, PNG ou WebP.")
    return media_storage.save(data, f"foto{extension}", content_type), width, height


def _get(db: Session, photo_id: int) -> StockImage:
    image = db.query(StockImage).filter(StockImage.id == photo_id, StockImage.provider == MANUAL_PROVIDER).first()
    if not image:
        raise HTTPException(status_code=404, detail="Foto não encontrada.")
    return image


def _keywords(value: str) -> str:
    keywords = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    if not keyword_list(", ".join(keywords)):
        raise HTTPException(status_code=400, detail="Informe ao menos uma palavra-chave.")
    return ", ".join(dict.fromkeys(keywords))[:500]


@router.get("", response_model=list[StockPhotoOut])
def list_stock_photos(
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[StockPhotoOut]:
    query = db.query(StockImage).filter(StockImage.provider == MANUAL_PROVIDER)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(StockImage.tags.ilike(like), StockImage.alt.ilike(like), StockImage.photographer.ilike(like)))
    return [_out(image) for image in query.order_by(StockImage.id.desc()).limit(500).all()]


@router.post("", response_model=StockPhotoOut)
def create_stock_photo(
    payload: StockPhotoIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> StockPhotoOut:
    url = payload.url.strip()
    provider_id = hashlib.sha1(url.encode()).hexdigest()[:40]
    if db.query(StockImage.id).filter(StockImage.provider == MANUAL_PROVIDER, StockImage.provider_id == provider_id).first():
        raise HTTPException(status_code=409, detail="Essa imagem já está cadastrada.")
    keywords = _keywords(payload.keywords)
    stored_url, width, height = download_photo(url)
    image = StockImage(
        provider=MANUAL_PROVIDER,
        provider_id=provider_id,
        download_url=url,
        stored_url=stored_url,
        tags=keywords,
        alt=_clean(payload.description),
        photographer=_clean(payload.author),
        photographer_url=_link(payload.author_url),
        source_name=_clean(payload.source_name),
        page_url=_link(payload.source_url),
        width=width,
        height=height,
        uses=0,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return _out(image)


@router.patch("/{photo_id}", response_model=StockPhotoOut)
def update_stock_photo(
    photo_id: int,
    payload: StockPhotoUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> StockPhotoOut:
    image = _get(db, photo_id)
    updates = payload.model_dump(exclude_unset=True)
    if "keywords" in updates and updates["keywords"] is not None:
        image.tags = _keywords(updates["keywords"])
    if "description" in updates:
        image.alt = _clean(updates["description"])
    if "author" in updates:
        image.photographer = _clean(updates["author"])
    if "author_url" in updates:
        image.photographer_url = _link(updates["author_url"])
    if "source_name" in updates:
        image.source_name = _clean(updates["source_name"])
    if "source_url" in updates:
        image.page_url = _link(updates["source_url"])
    db.commit()
    db.refresh(image)
    return _out(image)


@router.delete("/{photo_id}")
def delete_stock_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, str]:
    """Tira a foto do banco (a IA deixa de usar). Páginas que já usam a foto continuam com ela."""
    image = _get(db, photo_id)
    db.delete(image)
    db.commit()
    return {"detail": "Foto removida do banco."}
