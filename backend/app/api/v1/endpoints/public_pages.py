from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.api.v1.endpoints.pages import apply_free_footer, normalize_config, resolve_agency_plan
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.schemas.page import PublicPageOut

router = APIRouter()


def sanitize_digits(value: str | None) -> str:
    return "".join(filter(str.isdigit, value or ""))


def build_map_query(address: dict[str, str | None]) -> str:
    parts = [
        address.get("street"),
        address.get("number"),
        address.get("complement"),
        address.get("neighborhood"),
        address.get("city"),
        address.get("state"),
        address.get("zipcode"),
    ]
    return ", ".join(part.strip() for part in parts if part and part.strip())


def build_agency_profile(agency: Agency) -> dict[str, object]:
    membership = None
    for rel in agency.users or []:
        if rel.role == "owner" and rel.user:
            membership = rel
            break
    if membership is None:
        membership = next((rel for rel in agency.users or [] if rel.user), None)
    owner = membership.user if membership else None

    address = {
        "street": owner.address_street if owner else None,
        "number": owner.address_number if owner else None,
        "complement": owner.address_complement if owner else None,
        "neighborhood": owner.address_neighborhood if owner else None,
        "city": owner.address_city if owner else None,
        "state": owner.address_state if owner else None,
        "zipcode": owner.address_zipcode if owner else None,
    }
    address_text = build_map_query(address)
    map_embed_url = f"https://www.google.com/maps?q={quote_plus(address_text)}&output=embed" if address_text else None
    cnpj_digits = sanitize_digits(owner.cnpj if owner else None)
    contact_phone = agency.cta_whatsapp or (owner.whatsapp if owner else None)

    return {
        "name": agency.name,
        "cnpj": owner.cnpj if owner else None,
        "cnpj_digits": cnpj_digits or None,
        "email": owner.email if owner else None,
        "phone": contact_phone,
        "social_links": [{"network": link.network, "url": link.url} for link in agency.social_links or []],
        "address": address,
        "address_text": address_text or None,
        "map_query": address_text or None,
        "map_embed_url": map_embed_url,
        "cadastur_url": f"https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/{cnpj_digits}"
        if cnpj_digits
        else None,
    }


def serialize_public_page(page: Page, agency_slug: str, db: Session) -> PublicPageOut:
    plan = resolve_agency_plan(db, page.agency_id)
    config = apply_free_footer(normalize_config(page.config_json), plan) or {}
    branding = {
        "agency_name": page.agency.name,
        "logo_url": page.agency.logo_url,
        "primary_color": page.agency.primary_color,
        "secondary_color": page.agency.secondary_color,
        "agency_profile": build_agency_profile(page.agency),
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


def base_page_query(db: Session):
    return (
        db.query(Page)
        .join(Page.agency)
        .options(
            selectinload(Page.agency)
            .selectinload(Agency.users)
            .selectinload(AgencyUser.user),
            selectinload(Page.agency).selectinload(Agency.social_links),
        )
    )


@router.get("/by-slug/{agency_slug}/{page_slug}", response_model=PublicPageOut)
def get_public_page(agency_slug: str, page_slug: str, db: Session = Depends(get_db)) -> PublicPageOut:
    normalized_agency_slug = agency_slug.lower()
    normalized_page_slug = page_slug.lower()
    page = (
        base_page_query(db)
        .filter(
            func.lower(Page.slug) == normalized_page_slug,
            Page.status == "published",
            Page.agency.has(func.lower(Agency.slug) == normalized_agency_slug),
        )
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Pǭgina nǜo encontrada ou nǜo publicada.")
    return serialize_public_page(page, agency_slug, db)


@router.get("/default/{agency_slug}", response_model=PublicPageOut)
def get_default_public_page(agency_slug: str, db: Session = Depends(get_db)) -> PublicPageOut:
    normalized_slug = agency_slug.lower()
    agency = db.query(Agency).filter(func.lower(Agency.slug) == normalized_slug).first()
    if not agency or not agency.default_page_id:
        raise HTTPException(status_code=404, detail="Pǭgina padrǜo nǜo configurada.")
    page = (
        base_page_query(db)
        .filter(Page.id == agency.default_page_id, Page.status == "published")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Pǭgina padrǜo nǜo encontrada ou nǜo publicada.")
    return serialize_public_page(page, agency_slug, db)
