"""Admin Master: fotos cadastradas à mão (qualquer site), com palavras-chave e crédito.

O assistente de IA usa estas fotos antes de buscar no Unsplash e no Pexels, sempre que as
palavras-chave aparecem na busca. A foto é baixada e guardada otimizada no nosso
armazenamento, para a página não depender do site de origem.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.stock_image import StockImage
from app.models.user import User
from app.db import session as db_session
from app.services.curated_photos import (
    MAX_IMAGE_BYTES,
    Credits,
    PhotoError,
    direct_download_url,
    download,
    get_job,
    new_job,
    run_link_import,
    save_curated_photo,
)
from app.services.stock_images import MANUAL_PROVIDER, keyword_list

router = APIRouter(prefix="/master/stock-photos")



class StockPhotoIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=1000)
    keywords: str = Field(..., min_length=2, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500)
    author: Optional[str] = Field(default=None, max_length=255)
    author_url: Optional[str] = Field(default=None, max_length=500)
    source_name: Optional[str] = Field(default=None, max_length=120)
    source_url: Optional[str] = Field(default=None, max_length=500)


class ImportLinkIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=1000)
    keywords: str = Field(..., min_length=2, max_length=500)
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


def download_photo(url: str) -> bytes:
    """Baixa a imagem do endereço (só endereços públicos, até 30 MB)."""
    try:
        data, content_type = download(direct_download_url(url), MAX_IMAGE_BYTES)
    except PhotoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Não foi possível baixar a imagem: {exc}") from exc
    if content_type and not content_type.startswith("image/") and content_type != "application/octet-stream":
        raise HTTPException(
            status_code=400,
            detail="Esse link não é de uma imagem. Abra a foto, clique com o botão direito e copie o endereço da imagem.",
        )
    return data


def _credits(payload: "StockPhotoIn | ImportLinkIn") -> Credits:
    return Credits(
        description=_clean(getattr(payload, "description", None)),
        author=_clean(payload.author),
        author_url=_link(payload.author_url),
        source_name=_clean(payload.source_name),
        source_url=_link(payload.source_url),
    )


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
    _keywords(payload.keywords)
    credits = _credits(payload)
    data = download_photo(url)
    try:
        image = save_curated_photo(db, data, keywords=payload.keywords, credits=credits, origin=url)
    except PhotoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if image is None:
        raise HTTPException(status_code=409, detail="Essa imagem já está cadastrada.")
    return _out(image)


@router.post("/upload", response_model=StockPhotoOut)
async def upload_stock_photo(
    file: UploadFile = File(...),
    keywords: str = Form(..., min_length=2, max_length=500),
    path: str = Form(default="", max_length=500),
    author: str = Form(default="", max_length=255),
    author_url: str = Form(default="", max_length=500),
    source_name: str = Form(default="", max_length=120),
    source_url: str = Form(default="", max_length=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> StockPhotoOut:
    """Uma foto enviada do computador. O painel manda uma por vez (lotes e pastas), com o
    caminho relativo para o nome do arquivo e as pastas virarem contexto."""
    _keywords(keywords)
    data = await file.read(MAX_IMAGE_BYTES + 1)
    credits = Credits(
        author=_clean(author), author_url=_link(author_url), source_name=_clean(source_name), source_url=_link(source_url)
    )
    name = path or file.filename or "foto.jpg"
    try:
        image = save_curated_photo(db, data, keywords=keywords, credits=credits, origin=f"upload:{name}", path=name)
    except PhotoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if image is None:
        raise HTTPException(status_code=409, detail="Essa imagem já está cadastrada.")
    return _out(image)


@router.post("/import-link")
def import_stock_photos_from_link(
    payload: ImportLinkIn,
    background: BackgroundTasks,
    _: User = Depends(get_current_superuser),
) -> dict:
    """Link do Dropbox (pasta ou foto) ou de um .zip: baixa e cadastra em segundo plano."""
    url = payload.url.strip()
    if urlparse(url).scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Cole o link completo (https://...).")
    _keywords(payload.keywords)
    job = new_job()
    background.add_task(run_link_import, job, db_session.SessionLocal, url, payload.keywords, _credits(payload))
    return job.as_dict()


@router.get("/import-link/{job_id}")
def stock_photo_import_status(job_id: str, _: User = Depends(get_current_superuser)) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Importação não encontrada (o servidor pode ter reiniciado).")
    return job.as_dict()


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
