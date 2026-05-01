from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.services.team import get_agency_plan

router = APIRouter()


def _ensure_pixels_write_access(current_user: models.User) -> None:
  if getattr(current_user, "is_superuser", False):
    return
  role = (current_user.role or "member").lower()
  if role == "viewer":
    raise HTTPException(status_code=403, detail="Seu perfil permite apenas visualizar integrações.")


def plan_limit(plan: str) -> int:
  normalized = (plan or "free").strip().lower()
  if normalized == "free":
    return 0
  if normalized in {"trial", "essencial", "professional", "profissional"}:
    return 999999
  if normalized in {"agency", "growth", "agencia"}:
    return 3
  if normalized in {"scale", "infinity", "escala", "test", "teste"}:
    return 999999
  if normalized == "essencial":
    return 1
  return 0


def _resolve_user_agency_plan(db: Session, current_user: models.User) -> str:
  agency_id = current_user.primary_agency_id
  if not agency_id:
    membership = (
      db.query(models.AgencyUser)
      .filter(models.AgencyUser.user_id == current_user.id)
      .order_by(models.AgencyUser.id.asc())
      .first()
    )
    if membership:
      agency_id = membership.agency_id
  if not agency_id:
    return (current_user.plan or "free")
  return get_agency_plan(db, agency_id)


@router.get("/", response_model=list[dict])
def list_pixels(db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  pixels = db.query(models.Pixel).filter(models.Pixel.user_id == current_user.id).all()
  return [{"id": p.id, "name": p.name, "type": p.type, "value": p.value} for p in pixels]


@router.post("/", response_model=dict)
def create_pixel(payload: dict, db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  _ensure_pixels_write_access(current_user)
  limit = plan_limit(_resolve_user_agency_plan(db, current_user))
  count = db.query(models.Pixel).filter(models.Pixel.user_id == current_user.id).count()
  if count >= limit:
    raise HTTPException(status_code=400, detail="Limite de pixels atingido para o plano atual.")
  name = payload.get("name")
  ptype = payload.get("type")
  value = payload.get("value")
  if not name or not ptype or not value:
    raise HTTPException(status_code=400, detail="Campos obrigatórios ausentes.")
  if ptype not in ("meta", "ga"):
    raise HTTPException(status_code=400, detail="Tipo inválido.")
  pixel = models.Pixel(user_id=current_user.id, name=name, type=ptype, value=value)
  db.add(pixel)
  db.commit()
  db.refresh(pixel)
  return {"id": pixel.id, "name": pixel.name, "type": pixel.type, "value": pixel.value}


@router.put("/{pixel_id}", response_model=dict)
def update_pixel(pixel_id: int, payload: dict, db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  _ensure_pixels_write_access(current_user)
  pixel = db.query(models.Pixel).filter(models.Pixel.id == pixel_id, models.Pixel.user_id == current_user.id).first()
  if not pixel:
    raise HTTPException(status_code=404, detail="Pixel não encontrado.")

  name = (payload.get("name") or "").strip()
  ptype = payload.get("type")
  value = (payload.get("value") or "").strip()
  if not name or not ptype or not value:
    raise HTTPException(status_code=400, detail="Campos obrigatórios ausentes.")
  if ptype not in ("meta", "ga"):
    raise HTTPException(status_code=400, detail="Tipo inválido.")

  pixel.name = name
  pixel.type = ptype
  pixel.value = value
  db.add(pixel)
  db.commit()
  db.refresh(pixel)
  return {"id": pixel.id, "name": pixel.name, "type": pixel.type, "value": pixel.value}


@router.delete("/{pixel_id}")
def delete_pixel(pixel_id: int, db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  _ensure_pixels_write_access(current_user)
  pixel = db.query(models.Pixel).filter(models.Pixel.id == pixel_id, models.Pixel.user_id == current_user.id).first()
  if not pixel:
    raise HTTPException(status_code=404, detail="Pixel não encontrado.")
  db.delete(pixel)
  db.commit()
  return {"ok": True}
