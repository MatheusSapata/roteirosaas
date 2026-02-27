from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.schemas.agency import AgencyCreate, AgencyOut, AgencyUpdate

router = APIRouter()


def ensure_membership(db: Session, agency_id: int, user_id: int) -> Agency:
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    membership = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this agency")
    return agency


@router.get("/me", response_model=list[AgencyOut])
def get_my_agencies(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> list[AgencyOut]:
    memberships = db.query(AgencyUser).filter(AgencyUser.user_id == current_user.id).all()
    agency_ids = [m.agency_id for m in memberships]
    agencies = db.query(Agency).filter(Agency.id.in_(agency_ids)).all() if agency_ids else []
    return agencies


@router.post("", response_model=AgencyOut)
def create_agency(agency_in: AgencyCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> AgencyOut:
    normalized_name = agency_in.name.strip()
    normalized_slug = agency_in.slug.strip().lower()

    existing_slug = db.query(Agency).filter(func.lower(Agency.slug) == normalized_slug).first()
    if existing_slug:
        raise HTTPException(status_code=400, detail="Slug já está em uso")

    existing_name = db.query(Agency).filter(func.lower(Agency.name) == normalized_name.lower()).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Nome de agência já está em uso")

    payload = agency_in.dict()
    payload["name"] = normalized_name
    payload["slug"] = normalized_slug
    agency = Agency(**payload)
    db.add(agency)
    db.commit()
    db.refresh(agency)
    membership = AgencyUser(agency_id=agency.id, user_id=current_user.id, role="owner")
    db.add(membership)
    db.commit()
    return agency


@router.put("/{agency_id}", response_model=AgencyOut)
def update_agency(
    agency_id: int,
    agency_in: AgencyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgencyOut:
    agency = ensure_membership(db, agency_id, current_user.id)
    update_data = agency_in.dict(exclude_unset=True)

    if "slug" in update_data and update_data["slug"]:
        normalized_slug = update_data["slug"].strip().lower()
        existing_slug = (
            db.query(Agency)
            .filter(func.lower(Agency.slug) == normalized_slug, Agency.id != agency.id)
            .first()
        )
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug já está em uso")
        update_data["slug"] = normalized_slug

    if "name" in update_data and update_data["name"]:
        normalized_name = update_data["name"].strip()
        existing_name = (
            db.query(Agency)
            .filter(func.lower(Agency.name) == normalized_name.lower(), Agency.id != agency.id)
            .first()
        )
        if existing_name:
            raise HTTPException(status_code=400, detail="Nome de agência já está em uso")
        update_data["name"] = normalized_name

    for key, value in update_data.items():
        setattr(agency, key, value)
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


@router.get("/{agency_id}", response_model=AgencyOut)
def get_agency(
    agency_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> AgencyOut:
    agency = ensure_membership(db, agency_id, current_user.id)
    return agency
