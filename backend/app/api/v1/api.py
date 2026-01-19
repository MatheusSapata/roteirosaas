from fastapi import APIRouter

from app.api.v1.endpoints import auth, agencies, templates, pages, media, stats, public_pages, billing, pixels, admin

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agencies.router, prefix="/agencies", tags=["agencies"])
api_router.include_router(templates.router, prefix="/page-templates", tags=["page-templates"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(public_pages.router, prefix="/public/pages", tags=["public-pages"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(pixels.router, prefix="/pixels", tags=["pixels"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
