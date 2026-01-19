from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.endpoints.pages import apply_free_footer, normalize_config, resolve_agency_plan
from app.models.agency import Agency
from app.models.page import Page
from app.schemas.page import PublicPageOut

router = APIRouter()


def serialize_public_page(page: Page, agency_slug: str, db: Session) -> PublicPageOut:
    plan = resolve_agency_plan(db, page.agency_id)
    config = apply_free_footer(normalize_config(page.config_json), plan) or {}
    branding = {
        "agency_name": page.agency.name,
        "logo_url": page.agency.logo_url,
        "primary_color": page.agency.primary_color,
        "secondary_color": page.agency.secondary_color,
    }
    return PublicPageOut(
        id=page.id,
        title=page.title,
        slug=page.slug,
        agency_slug=agency_slug,
        cover_image_url=page.cover_image_url,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        config=config,
        branding=branding,
    )


@router.get("/by-slug/{agency_slug}/{page_slug}", response_model=PublicPageOut)
def get_public_page(agency_slug: str, page_slug: str, db: Session = Depends(get_db)) -> PublicPageOut:
    normalized_agency_slug = agency_slug.lower()
    normalized_page_slug = page_slug.lower()
    page = (
        db.query(Page)
        .join(Page.agency)
        .filter(
            func.lower(Page.slug) == normalized_page_slug,
            Page.status == "published",
            Page.agency.has(func.lower(Agency.slug) == normalized_agency_slug)
        )
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Page not found or not published")
    return serialize_public_page(page, agency_slug, db)


@router.get("/default/{agency_slug}", response_model=PublicPageOut)
def get_default_public_page(agency_slug: str, db: Session = Depends(get_db)) -> PublicPageOut:
    normalized_slug = agency_slug.lower()
    agency = db.query(Agency).filter(func.lower(Agency.slug) == normalized_slug).first()
    if not agency or not agency.default_page_id:
        raise HTTPException(status_code=404, detail="Default page not configured")
    page = (
        db.query(Page)
        .filter(Page.id == agency.default_page_id, Page.status == "published")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Default page not found or unpublished")
    return serialize_public_page(page, agency_slug, db)
