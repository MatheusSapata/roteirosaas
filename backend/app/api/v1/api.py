from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    agencies,
    agency_domains,
    auth,
    billing,
    lead_forms,
    lessons,
    media,
    pages,
    pixels,
    public_lead_forms,
    public_pages,
    stats,
    templates,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agencies.router, prefix="/agencies", tags=["agencies"])
api_router.include_router(
    agency_domains.router,
    prefix="/agencies/me/domains",
    tags=["agency-domains"],
)
api_router.include_router(templates.router, prefix="/page-templates", tags=["page-templates"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(public_pages.router, prefix="/public/pages", tags=["public-pages"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(pixels.router, prefix="/pixels", tags=["pixels"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(lead_forms.router, prefix="/lead-forms", tags=["lead-forms"])
api_router.include_router(public_lead_forms.router, prefix="/public/lead-forms", tags=["public-lead-forms"])
