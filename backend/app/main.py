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
from app.services.subscription import schedule_expiration_job
from app.services.trial_tags import schedule_trial_tag_job

settings = get_settings()

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
    agency_slug: str,
    page_slug: str | None,
    request: Request,
    db: Session,
) -> HTMLResponse:
    try:
        html = render_public_page_html(agency_slug, page_slug, page_url=str(request.url), db=db)
        return _frontend_response(html)
    except PublicPageNotAvailable:
        # Retorna o HTML padrão para permitir que o SPA trate o erro normalmente.
        return _frontend_response(_safe_load_frontend())
    except FrontendTemplateNotReady as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_frontend_index() -> HTMLResponse:
    return _frontend_response(_safe_load_frontend())


@app.get("/p/{agency_slug}", response_class=HTMLResponse, include_in_schema=False)
@app.get("/p/{agency_slug}/{page_slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_short_public_page(
    agency_slug: str,
    request: Request,
    page_slug: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return _serve_public_page(agency_slug, page_slug, request, db)


RESERVED_PREFIXES = {"api", "assets", "uploads", "static"}


@app.get("/{agency_slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_agency_root(
    agency_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if agency_slug in RESERVED_PREFIXES:
        raise HTTPException(status_code=404, detail="Not Found")
    return _serve_public_page(agency_slug, None, request, db)


@app.get("/{agency_slug}/{page_slug}", response_class=HTMLResponse, include_in_schema=False)
def serve_agency_page(
    agency_slug: str,
    page_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if agency_slug in RESERVED_PREFIXES:
        raise HTTPException(status_code=404, detail="Not Found")
    return _serve_public_page(agency_slug, page_slug, request, db)


@app.on_event("startup")
async def start_background_jobs() -> None:
    # Evita agendar o job durante testes automatizados
    if settings.env == "test":
        return
    schedule_expiration_job(interval_minutes=60)
    schedule_trial_tag_job()
