import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.v1.api import api_router
from app.api import cakto as cakto_api
from app.api.deps import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.services.public_page_renderer import (
    FRONTEND_DIST_DIR,
    FrontendTemplateNotReady,
    PublicPageNotAvailable,
    load_frontend_index,
    render_public_page_html,
)
from app.services.public_page_resolver import PublicPageResolverService
from app.services.subscription import schedule_expiration_job
from app.services.trial_tags import schedule_trial_tag_job

settings = get_settings()
page_resolver = PublicPageResolverService(settings)

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(cakto_api.router)
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
frontend_assets_dir = FRONTEND_DIST_DIR / "assets"
if frontend_assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_assets_dir)), name="frontend-assets")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _frontend_response(html_content: str) -> HTMLResponse:
    return HTMLResponse(html_content)


def _safe_load_frontend() -> str:
    try:
        return load_frontend_index()
    except FrontendTemplateNotReady as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _serve_public_page(
    request: Request,
    db: Session,
    agency_slug: str | None = None,
    page_slug: str | None = None,
) -> HTMLResponse:
    try:
        host_header = request.headers.get("x-forwarded-host") or request.headers.get("host")
        scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
        resolution = page_resolver.resolve(
            host_header=host_header,
            path=request.url.path,
            scheme=scheme,
            agency_slug_param=agency_slug,
            page_slug_param=page_slug,
            db=db,
        )
        host_for_url = host_header or resolution.normalized_host or request.url.netloc
        if resolution.mode == "platform_path" and settings.platform_primary_domain:
            host_for_url = settings.platform_primary_domain
        page_url = f"{resolution.scheme or 'https'}://{host_for_url}{request.url.path}"
        html = render_public_page_html(resolution.agency_slug, resolution.page_slug, page_url=page_url, db=db)
        return _frontend_response(html)
    except PublicPageNotAvailable:
        # Retorna o HTML padrao para permitir que o SPA trate o erro normalmente.
        return _frontend_response(_safe_load_frontend())
    except FrontendTemplateNotReady as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc



@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_frontend_index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    host_header = request.headers.get("x-forwarded-host") or request.headers.get("host")
    normalized_host = PublicPageResolverService._normalize_hostname(host_header)
    if normalized_host in page_resolver.platform_hosts or not normalized_host:
        return _frontend_response(_safe_load_frontend())
    return _serve_public_page(request=request, db=db)


@app.get("/admin/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def serve_admin_app(full_path: str = "") -> HTMLResponse:
    # Sempre entrega o SPA padrao; o frontend decide qual tela mostrar.
    return _frontend_response(_safe_load_frontend())


@app.get("/p/{agency_slug}", response_class=HTMLResponse, include_in_schema=False)
@app.get("/p/{agency_slug}/{page_slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_short_public_page(
    agency_slug: str,
    request: Request,
    page_slug: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _serve_public_page(request=request, db=db, agency_slug=agency_slug, page_slug=page_slug)


RESERVED_PREFIXES = {"api", "assets", "uploads", "static", "admin"}


@app.get("/{agency_slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_agency_root(
    agency_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if agency_slug in RESERVED_PREFIXES:
        raise HTTPException(status_code=404, detail="Not Found")
    return _serve_public_page(request=request, db=db, agency_slug=agency_slug, page_slug=None)


@app.get("/{agency_slug}/{page_slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_agency_page(
    agency_slug: str,
    page_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if agency_slug in RESERVED_PREFIXES:
        raise HTTPException(status_code=404, detail="Not Found")
    return _serve_public_page(request=request, db=db, agency_slug=agency_slug, page_slug=page_slug)


@app.on_event("startup")
async def start_background_jobs() -> None:
    # Evita agendar o job durante testes automatizados
    if settings.env == "test":
        return
    schedule_expiration_job(interval_minutes=60)
    schedule_trial_tag_job()
