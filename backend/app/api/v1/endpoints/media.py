import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_user import AgencyUser
from app.models.media import MediaAsset
from app.models.user import User
from app.schemas.media import MediaAssetOut

router = APIRouter()
UPLOAD_DIR = "uploads"


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
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1]
    file_id = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    url = f"/{UPLOAD_DIR}/{file_id}"
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
