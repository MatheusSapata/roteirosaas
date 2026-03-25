from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.agency import Agency
from app.models.agency_social_link import AgencySocialLink
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.schemas.agency import AgencyCreate, AgencyOut, AgencyUpdate, AgencySocialLinkCreate

router = APIRouter()


def replace_social_links(agency: Agency, social_links: list[AgencySocialLinkCreate] | None) -> None:
    if social_links is None:
        return

    existing_links = {link.network: link for link in agency.social_links}
    seen_networks: set[str] = set()

    for link in social_links:
        if link.network in seen_networks:
            continue
        seen_networks.add(link.network)
        existing = existing_links.get(link.network)
        if existing:
            existing.url = link.url
        else:
            agency.social_links.append(AgencySocialLink(network=link.network, url=link.url))

    for link in list(agency.social_links):
        if link.network not in seen_networks:
            agency.social_links.remove(link)


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
        raise HTTPException(status_code=400, detail="Slug já está em uso.")

    payload = agency_in.dict(exclude={"social_links"})
    payload["name"] = normalized_name
    payload["slug"] = normalized_slug
    agency = Agency(**payload)
    replace_social_links(agency, agency_in.social_links or [])
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
    agency = require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    update_data = agency_in.dict(exclude_unset=True, exclude={"social_links"})
    social_links_data = agency_in.social_links

    if "slug" in update_data and update_data["slug"]:
        normalized_slug = update_data["slug"].strip().lower()
        existing_slug = (
            db.query(Agency)
            .filter(func.lower(Agency.slug) == normalized_slug, Agency.id != agency.id)
            .first()
        )
        if existing_slug:
            raise HTTPException(status_code=400, detail="Slug já está em uso.")
        update_data["slug"] = normalized_slug

    if "name" in update_data and update_data["name"]:
        update_data["name"] = update_data["name"].strip()

    for key, value in update_data.items():
        setattr(agency, key, value)

    replace_social_links(agency, social_links_data)
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


@router.get("/{agency_id}", response_model=AgencyOut)
def get_agency(
    agency_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> AgencyOut:
    agency = require_agency_membership(db=db, agency_id=agency_id, user_id=current_user.id)
    return agency
