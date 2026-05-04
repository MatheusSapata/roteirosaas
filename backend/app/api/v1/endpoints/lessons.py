import base64
import mimetypes
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonOut, LessonUpdate
from app.services.lessons_defaults import DEFAULT_LESSONS
from app.services.media_storage import media_storage

router = APIRouter()

THUMBNAIL_MAX_BYTES = 5 * 1024 * 1024
DATA_URL_PATTERN = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$")


def _save_data_url_thumbnail(data_url: str) -> str:
    match = DATA_URL_PATTERN.match(data_url.strip())
    if not match:
        raise HTTPException(status_code=400, detail="Imagem inválida.")
    raw = match.group("data")
    try:
        binary = base64.b64decode(raw)
    except (base64.binascii.Error, ValueError) as exc:  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail="Imagem inválida.") from exc
    if len(binary) > THUMBNAIL_MAX_BYTES:
        raise HTTPException(status_code=400, detail="Imagem muito grande (máximo 4MB).")
    mime = match.group("mime")
    extension = mimetypes.guess_extension(mime or "") or ".png"
    filename = f"lesson-thumb{extension}"
    return media_storage.save(binary, filename, mime)


def _resolve_thumbnail(thumbnail_base64: Optional[str], thumbnail_url: Optional[str]) -> Optional[str]:
    if thumbnail_base64:
        return _save_data_url_thumbnail(thumbnail_base64)
    if thumbnail_url is not None:
        return thumbnail_url or None
    return None


def _apply_defaults(instance: Lesson, payload: LessonUpdate) -> Lesson:
    if payload.module_name is not None:
        instance.module_name = payload.module_name
    if payload.title is not None:
        instance.title = payload.title
    if payload.description is not None:
        instance.description = payload.description
    if payload.duration is not None:
        instance.duration = payload.duration
    if payload.level is not None:
        instance.level = payload.level
    if payload.video_type is not None:
        instance.video_type = payload.video_type
    if payload.video_url is not None:
        instance.video_url = payload.video_url
    if payload.thumbnail_base64 or payload.thumbnail_url is not None:
        instance.thumbnail_url = _resolve_thumbnail(payload.thumbnail_base64, payload.thumbnail_url)
    return instance


@router.get("", response_model=List[LessonOut])
def list_lessons(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> List[Lesson]:
    return db.query(Lesson).order_by(Lesson.created_at.desc()).all()


@router.post("", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> Lesson:
    lesson = Lesson(
        module_name=payload.module_name,
        title=payload.title,
        description=payload.description,
        duration=payload.duration,
        level=payload.level,
        video_type=payload.video_type,
        video_url=payload.video_url,
        thumbnail_url=_resolve_thumbnail(payload.thumbnail_base64, payload.thumbnail_url),
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.put("/{lesson_id}", response_model=LessonOut)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> Lesson:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    lesson = _apply_defaults(lesson, payload)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> None:
    deleted = db.query(Lesson).filter(Lesson.id == lesson_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    db.commit()


@router.post("/reset", response_model=List[LessonOut])
def reset_lessons(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> List[Lesson]:
    db.query(Lesson).delete()
    for lesson_data in DEFAULT_LESSONS:
        lesson = Lesson(**lesson_data)
        db.add(lesson)
    db.commit()
    return db.query(Lesson).order_by(Lesson.created_at.desc()).all()
