from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MediaAssetBase(BaseModel):
    url: str
    type: str = "image"
    original_file_name: Optional[str] = None


class MediaAssetCreate(MediaAssetBase):
    agency_id: int


class MediaAssetOut(MediaAssetBase):
    id: int
    agency_id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
