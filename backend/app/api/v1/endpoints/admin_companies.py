"""Admin Master: empresas (situação, tempo desativada, uso) e o ciclo dos arquivos guardados
(arquivar material de quem saiu do ar, limpar arquivos sem uso). Ver services/media_lifecycle."""
from __future__ import annotations

import threading
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.db import session as db_session
from app.models.agency_user import AgencyUser
from app.models.media_archive import AgencyMediaArchive, MediaOrphan
from app.models.page import Page
from app.models.stats import PageVisitStats
from app.models.user import User
from app.models.user_session import UserSession
from app.services import media_lifecycle as lifecycle
from app.services.company_status import agencies_with_owner, company_status

router = APIRouter(prefix="/master/companies")


class CompanyOut(BaseModel):
    id: int
    name: str
    slug: str
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    plan: Optional[str] = None
    status: str
    status_label: str
    online: bool
    status_since: Optional[datetime] = None
    status_days: Optional[int] = None
    since_estimated: bool = False
    valid_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_access_at: Optional[datetime] = None
    pages_total: int = 0
    pages_published: int = 0
    visits_30d: int = 0
    media_stage: str = "hot"
    media_files: int = 0
    media_bytes: int = 0
    media_shared_skipped: int = 0
    media_measured_at: Optional[datetime] = None
    media_error: Optional[str] = None
    next_step: Optional[str] = None


class CompaniesResponse(BaseModel):
    items: list[CompanyOut]
    summary: dict[str, Any]


def _next_step(status_key: str, days: int | None, stage: str) -> str | None:
    if status_key != "inactive":
        return "Restaurar arquivos (voltou a assinar)" if stage in ("cool", "archive") else None
    days = days or 0
    if stage == "hot":
        wait = lifecycle.COOL_AFTER_DAYS - days
        return "Pronta para Cool" if wait <= 0 else f"Cool em {wait} dia(s)"
    if stage == "cool":
        wait = lifecycle.ARCHIVE_AFTER_DAYS - days
        return "Pronta para Archive" if wait <= 0 else f"Archive em {wait} dia(s)"
    return None


@router.get("", response_model=CompaniesResponse)
def list_companies(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> CompaniesResponse:
    now = datetime.now(timezone.utc)
    pages = {
        agency_id: (int(total or 0), int(published or 0))
        for agency_id, total, published in db.query(
            Page.agency_id, func.count(Page.id), func.count(Page.id).filter(Page.status == "published")
        ).group_by(Page.agency_id)
    }
    visits = dict(
        db.query(Page.agency_id, func.coalesce(func.sum(PageVisitStats.visits), 0))
        .join(PageVisitStats, PageVisitStats.page_id == Page.id)
        .filter(PageVisitStats.date >= date.today() - timedelta(days=30))
        .group_by(Page.agency_id)
        .all()
    )
    last_access = dict(
        db.query(AgencyUser.agency_id, func.max(UserSession.last_seen_at))
        .join(UserSession, UserSession.user_id == AgencyUser.user_id)
        .group_by(AgencyUser.agency_id)
        .all()
    )
    archives = {record.agency_id: record for record in db.query(AgencyMediaArchive).all()}
    items: list[CompanyOut] = []
    for agency, owner in agencies_with_owner(db):
        status = company_status(owner, now)
        record = archives.get(agency.id)
        stage = record.stage if record else "hot"
        subscription = owner.subscription if owner else None
        total, published = pages.get(agency.id, (0, 0))
        items.append(CompanyOut(
            id=agency.id,
            name=agency.name,
            slug=agency.slug,
            owner_name=owner.name if owner else None,
            owner_email=owner.email if owner else None,
            plan=(owner.plan if owner else None),
            status=status.key,
            status_label=status.label,
            online=status.online,
            status_since=status.since,
            status_days=status.days,
            since_estimated=status.estimated,
            valid_until=subscription.valid_until if subscription else None,
            created_at=agency.created_at,
            last_access_at=last_access.get(agency.id),
            pages_total=total,
            pages_published=published,
            visits_30d=int(visits.get(agency.id) or 0),
            media_stage=stage,
            media_files=record.files_count if record else 0,
            media_bytes=int(record.total_bytes or 0) if record else 0,
            media_shared_skipped=record.shared_skipped if record else 0,
            media_measured_at=record.measured_at if record else None,
            media_error=record.last_error if record else None,
            next_step=_next_step(status.key, status.days, stage),
        ))
    counts: dict[str, int] = {}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
    inactive = [item for item in items if item.status == "inactive"]
    summary = {
        "counts": counts,
        "total": len(items),
        "inactive_over_30": sum(1 for item in inactive if (item.status_days or 0) >= 30),
        "inactive_bytes": sum(item.media_bytes for item in inactive if item.media_stage in ("hot", "restoring")),
        "archived_bytes": sum(item.media_bytes for item in items if item.media_stage in ("cool", "archive")),
        "automation": lifecycle.automation_enabled(),
        "rules": {
            "cool_after_days": lifecycle.COOL_AFTER_DAYS,
            "archive_after_days": lifecycle.ARCHIVE_AFTER_DAYS,
            "orphan_grace_days": lifecycle.ORPHAN_GRACE_DAYS,
        },
    }
    items.sort(key=lambda item: (item.status != "inactive", -(item.status_days or 0), item.name.lower()))
    return CompaniesResponse(items=items, summary=summary)


@router.get("/storage")
def storage_status(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    analysis = lifecycle.analysis
    orphans = db.query(MediaOrphan).all()
    ready = [orphan for orphan in orphans if lifecycle.orphan_ready(orphan)]
    return {
        "status": analysis.status,
        "started_at": analysis.started_at,
        "finished_at": analysis.finished_at,
        "error": analysis.error,
        "summary": analysis.summary,
        "orphans": {
            "groups": len(orphans),
            "bytes": sum(orphan.total_bytes or 0 for orphan in orphans),
            "ready_groups": len(ready),
            "ready_bytes": sum(orphan.total_bytes or 0 for orphan in ready),
            "oldest_seen_at": min((orphan.first_seen_at for orphan in orphans), default=None),
        },
    }


@router.post("/storage/analyze")
def start_analysis(_: User = Depends(get_current_superuser)) -> dict[str, str]:
    if lifecycle.analysis.status == "running":
        return {"status": "running"}
    threading.Thread(target=lifecycle.run_analysis, args=(db_session.SessionLocal,), daemon=True).start()
    return {"status": "running"}


class ConfirmIn(BaseModel):
    confirm: str = ""


def _run(action, *args, **kwargs) -> dict[str, Any]:
    try:
        record = action(*args, **kwargs)
    except lifecycle.LifecycleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "stage": record.stage,
        "files": record.files_count,
        "bytes": int(record.total_bytes or 0),
        "shared_skipped": record.shared_skipped,
        "error": record.last_error,
    }


@router.post("/{agency_id}/media/cool")
def media_to_cool(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    return _run(lifecycle.move_agency_media, db, agency_id, "Cool")


@router.post("/{agency_id}/media/archive")
def media_to_archive(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    # Margem de segurança: Archive (indisponível) só depois do prazo do Cool.
    return _run(lifecycle.move_agency_media, db, agency_id, "Archive", min_days=lifecycle.COOL_AFTER_DAYS)


@router.post("/{agency_id}/media/restore")
def media_restore(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> dict[str, Any]:
    return _run(lifecycle.restore_agency_media, db, agency_id)


@router.post("/{agency_id}/media/delete")
def media_delete(
    agency_id: int, payload: ConfirmIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)
) -> dict[str, Any]:
    agency = next((agency for agency, _owner in agencies_with_owner(db) if agency.id == agency_id), None)
    if agency is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    if payload.confirm.strip().lower() != agency.slug.lower():
        raise HTTPException(status_code=400, detail=f'Para confirmar, digite o identificador da empresa: "{agency.slug}".')
    return _run(lifecycle.delete_agency_media, db, agency_id)


@router.post("/orphans/delete-ready")
def orphans_delete_ready(
    payload: ConfirmIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)
) -> dict[str, int]:
    if payload.confirm.strip().upper() != "EXCLUIR":
        raise HTTPException(status_code=400, detail='Para confirmar, digite "EXCLUIR".')
    if lifecycle.analysis.status == "running":
        raise HTTPException(status_code=409, detail="Espere a análise terminar.")
    return lifecycle.delete_ready_orphans(db)
