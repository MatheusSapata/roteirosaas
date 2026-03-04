from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LessonVideoType(str, Enum):  # type: ignore[misc]
    file = "file"
    youtube = "youtube"
    iframe = "iframe"


class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration: Optional[str] = None
    level: Optional[str] = None
    video_type: LessonVideoType = LessonVideoType.youtube
    video_url: str
    thumbnail_url: Optional[str] = None


class LessonCreate(LessonBase):
    thumbnail_base64: Optional[str] = Field(default=None, description="Data URL base64 thumbnail")


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    level: Optional[str] = None
    video_type: Optional[LessonVideoType] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    thumbnail_base64: Optional[str] = None


class LessonOut(LessonBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
