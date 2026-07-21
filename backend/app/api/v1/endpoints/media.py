from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_user import AgencyUser
from app.models.media import MediaAsset
from app.models.user import User
from app.schemas.media import MediaAssetOut
from app.services.background_removal import (
    BackgroundRemovalUnavailable,
    InvalidBackgroundRemovalImage,
    MAX_IMAGE_BYTES,
    remove_image_background,
)
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


@router.post("/remove-background")
async def remove_media_background(
    agency_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    ensure_agency_member(db, agency_id, current_user.id)
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Envie um arquivo de imagem válido.")

    file_bytes = await file.read(MAX_IMAGE_BYTES + 1)
    try:
        result = await run_in_threadpool(remove_image_background, file_bytes)
    except InvalidBackgroundRemovalImage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BackgroundRemovalUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="A remoção de fundo está temporariamente indisponível. Tente novamente em instantes.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail="Não foi possível remover o fundo desta imagem.") from exc

    return Response(
        content=result,
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename="background-removed.png"'},
    )


@router.get("/proxy")
def proxy_media(
    url: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    raw = (url or "").strip()
    parsed = urlparse(raw)
    input_path = parsed.path.rstrip("/")

    user_assets = (
        db.query(MediaAsset)
        .join(AgencyUser, AgencyUser.agency_id == MediaAsset.agency_id)
        .filter(AgencyUser.user_id == current_user.id)
        .all()
    )

    asset: MediaAsset | None = None
    for candidate in user_assets:
        stored = (candidate.url or "").strip()
        if not stored:
            continue

        if stored == raw:
            asset = candidate
            break

        stored_parsed = urlparse(stored)
        stored_path = stored_parsed.path.rstrip("/")

        if input_path and stored_path and input_path == stored_path:
            asset = candidate
            break

        if input_path and stored.endswith(input_path):
            asset = candidate
            break

    if not asset:
        raise HTTPException(status_code=404, detail="Mídia não encontrada.")

    fetch_url = raw if parsed.scheme in {"http", "https"} else (asset.url or "").strip()
    fetch_parsed = urlparse(fetch_url)
    if fetch_parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="URL de mídia inválida.")

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            remote = client.get(fetch_url)
            remote.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Não foi possível carregar a mídia.") from exc

    content_type = remote.headers.get("content-type", "application/octet-stream")
    return Response(content=remote.content, media_type=content_type)


@router.get("/{media_id}", response_model=MediaAssetOut)
def get_media(media_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> MediaAssetOut:
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Mídia não encontrada.")
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == asset.agency_id, AgencyUser.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta agência.")
    return asset
