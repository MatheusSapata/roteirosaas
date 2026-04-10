import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_user import AgencyUser
from app.models.media import MediaAsset
from app.models.user import User
from app.schemas.media import MediaAssetOut, MediaProxyResponse
from app.services.media_storage import media_storage

router = APIRouter()


def ensure_agency_member(db: Session, agency_id: int, user_id: int) -> None:
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta agência.")


@router.post("/upload", response_model=MediaAssetOut)
async def upload_media(
    agency_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MediaAssetOut:
    ensure_agency_member(db, agency_id, current_user.id)
    file_bytes = await file.read()
    url = media_storage.save(file_bytes, file.filename or "upload", getattr(file, "content_type", None))
    asset = MediaAsset(agency_id=agency_id, url=url, type="image", original_file_name=file.filename)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{media_id}", response_model=MediaAssetOut)
def get_media(media_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> MediaAssetOut:
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Mídia não encontrada.")
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == asset.agency_id, AgencyUser.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta agência.")
    return asset


async def _fetch_remote_bytes(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        if response.status_code >= 400:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    content_type = response.headers.get("content-type") or "application/octet-stream"
    return response.content, content_type


def _fetch_local_bytes(url: str) -> tuple[bytes, str]:
    parsed = urlparse(url)
    path = parsed.path if parsed.scheme else url
    if not path.startswith("/uploads/"):
        raise HTTPException(status_code=400, detail="Caminho de mídia inválido.")
    relative_path = path.split("/uploads/", 1)[1]
    file_path = media_storage.local_dir / Path(relative_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    data = file_path.read_bytes()
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return data, content_type


@router.get("/proxy/logo", response_model=MediaProxyResponse)
async def proxy_logo(url: str = Query(..., min_length=1)) -> MediaProxyResponse:
    if not url:
        raise HTTPException(status_code=400, detail="URL obrigatória.")

    if media_storage.is_remote:
        base_url = media_storage.base_url
        if not base_url or not url.startswith(base_url):
            raise HTTPException(status_code=400, detail="URL fora do escopo permitido.")
        data, content_type = await _fetch_remote_bytes(url)
    else:
        data, content_type = _fetch_local_bytes(url)

    encoded = base64.b64encode(data).decode("utf-8")
    data_url = f"data:{content_type};base64,{encoded}"
    return MediaProxyResponse(data_url=data_url)
