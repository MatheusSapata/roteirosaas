from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.api import deps

router = APIRouter()


def plan_limit(plan: str) -> int:
  if plan == "free":
    return 0
  if plan == "essencial":
    return 1
  if plan == "growth":
    return 3
  return 999999  # infinity


@router.get("/", response_model=list[dict])
def list_pixels(db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  pixels = db.query(models.Pixel).filter(models.Pixel.user_id == current_user.id).all()
  return [{"id": p.id, "name": p.name, "type": p.type, "value": p.value} for p in pixels]


@router.post("/", response_model=dict)
def create_pixel(payload: dict, db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  limit = plan_limit(current_user.plan)
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


@router.delete("/{pixel_id}")
def delete_pixel(pixel_id: int, db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_active_user)):
  pixel = db.query(models.Pixel).filter(models.Pixel.id == pixel_id, models.Pixel.user_id == current_user.id).first()
  if not pixel:
    raise HTTPException(status_code=404, detail="Pixel não encontrado.")
  db.delete(pixel)
  db.commit()
  return {"ok": True}
