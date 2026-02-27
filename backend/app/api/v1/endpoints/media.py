from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_user import AgencyUser
from app.models.media import MediaAsset
from app.models.user import User
from app.schemas.media import MediaAssetOut
from app.services.media_storage import media_storage

router = APIRouter()


def ensure_agency_member(db: Session, agency_id: int, user_id: int) -> None:
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this agency")


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
        raise HTTPException(status_code=404, detail="Media not found")
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == asset.agency_id, AgencyUser.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this agency")
    return asset
