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
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.media_archive import AgencyMediaArchive, MediaOrphan
from app.models.page import Page, PageStatus
from app.models.stats import PageVisitStats
from app.models.user import User
from app.models.user_session import UserSession
from app.models.user_tracking import UserTracking
from app.services import media_lifecycle as lifecycle
from app.services.company_status import FREE_ACCESS_DAYS, agency_owner, agencies_with_owner, company_status

router = APIRouter(prefix="/master/companies")


class CompanyOut(BaseModel):
    id: int
    name: str
    slug: str
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_whatsapp: Optional[str] = None
    owner_is_superuser: bool = False
    plan: Optional[str] = None
    status: str
    status_label: str
    online: bool
    status_since: Optional[datetime] = None
    status_days: Optional[int] = None
    since_estimated: bool = False
    # Até quando vale o acesso atual (fim do teste, prazo do gratuito ou fim do período pago).
    access_until: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    trial_plan: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    subscription_provider: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_asaas_subscription_id: Optional[str] = None
    subscription_cakto_order_id: Optional[str] = None
    subscription_cakto_subscription_code: Optional[str] = None
    billing_cycle: Optional[str] = None
    payment_method: Optional[str] = None
    mrr_amount: float = 0
    failed_attempts: int = 0
    members_count: int = 0
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
            owner_id=owner.id if owner else None,
            owner_name=owner.name if owner else None,
            owner_email=owner.email if owner else None,
            owner_whatsapp=owner.whatsapp if owner else None,
            owner_is_superuser=bool(owner and owner.is_superuser),
            plan=(owner.plan if owner else None),
            status=status.key,
            status_label=status.label,
            online=status.online,
            status_since=status.since,
            status_days=status.days,
            since_estimated=status.estimated,
            access_until=status.ends,
            valid_until=subscription.valid_until if subscription else None,
            trial_plan=owner.trial_plan if owner else None,
            trial_ends_at=owner.trial_ends_at if owner else None,
            subscription_provider=subscription.provider if subscription else None,
            subscription_status=subscription.status if subscription else None,
            subscription_asaas_subscription_id=subscription.asaas_subscription_id if subscription else None,
            subscription_cakto_order_id=subscription.cakto_order_id if subscription else None,
            subscription_cakto_subscription_code=subscription.cakto_subscription_code if subscription else None,
            billing_cycle=subscription.billing_cycle if subscription else None,
            payment_method=subscription.payment_method_type if subscription else None,
            mrr_amount=float(subscription.mrr_amount or 0) if subscription else 0,
            failed_attempts=int(subscription.failed_attempts or 0) if subscription else 0,
            members_count=sum(1 for rel in agency.users or [] if rel.user and not rel.hidden_from_team),
            # Cadastro = criação da conta do dono (a agência pode nascer só no pagamento).
            created_at=(owner.created_at if owner and owner.created_at else agency.created_at),
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
            "free_access_days": FREE_ACCESS_DAYS,
        },
    }
    # Contas criadas por último primeiro.
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    items.sort(key=lambda item: (_aware(item.created_at) or oldest, item.id), reverse=True)
    return CompaniesResponse(items=items, summary=summary)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


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


class CompanyMemberOut(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    is_owner: bool
    last_access_at: Optional[datetime] = None


class CompanyPageOut(BaseModel):
    id: int
    title: str
    slug: str
    status: str
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    visits: int = 0
    clicks: int = 0


class CompanyTrackingOut(BaseModel):
    id: int
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    referrer: Optional[str] = None
    created_at: Optional[datetime] = None


class CompanyDetailOut(BaseModel):
    id: int
    slug: str
    members: list[CompanyMemberOut]
    pages: list[CompanyPageOut]
    tracking: list[CompanyTrackingOut]


@router.get("/{agency_id}", response_model=CompanyDetailOut)
def company_detail(agency_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> CompanyDetailOut:
    """Equipe, páginas (com visitas e cliques) e origem do cadastro do dono de uma empresa."""
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if agency is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    owner = agency_owner(agency)
    # Admins globais entram escondidos em todas as empresas: não são da equipe.
    memberships = [rel for rel in agency.users or [] if rel.user and not rel.hidden_from_team]
    last_seen = dict(
        db.query(UserSession.user_id, func.max(UserSession.last_seen_at))
        .filter(UserSession.user_id.in_([rel.user_id for rel in memberships] or [0]))
        .group_by(UserSession.user_id)
        .all()
    )
    members = sorted(
        (
            CompanyMemberOut(
                user_id=rel.user.id,
                name=rel.user.name,
                email=rel.user.email,
                role=(rel.role or "").lower(),
                is_owner=bool(owner and owner.id == rel.user.id),
                last_access_at=last_seen.get(rel.user.id),
            )
            for rel in memberships
        ),
        key=lambda member: (not member.is_owner, member.name.lower()),
    )
    stats = {
        page_id: (int(visits or 0), int(cta or 0) + int(whatsapp or 0))
        for page_id, visits, cta, whatsapp in db.query(
            PageVisitStats.page_id,
            func.sum(PageVisitStats.visits),
            func.sum(PageVisitStats.clicks_cta),
            func.sum(PageVisitStats.clicks_whatsapp),
        )
        .join(Page, Page.id == PageVisitStats.page_id)
        .filter(Page.agency_id == agency_id)
        .group_by(PageVisitStats.page_id)
    }
    pages = [
        CompanyPageOut(
            id=page.id,
            title=page.title,
            slug=page.slug,
            status=page.status.value if isinstance(page.status, PageStatus) else str(page.status or ""),
            published_at=page.published_at,
            updated_at=page.updated_at,
            visits=stats.get(page.id, (0, 0))[0],
            clicks=stats.get(page.id, (0, 0))[1],
        )
        for page in db.query(Page).filter(Page.agency_id == agency_id).order_by(Page.updated_at.desc().nullslast(), Page.id.desc())
    ]
    tracking = (
        [
            CompanyTrackingOut.model_validate(entry, from_attributes=True)
            for entry in db.query(UserTracking).filter(UserTracking.user_id == owner.id).order_by(UserTracking.created_at.desc())
        ]
        if owner
        else []
    )
    return CompanyDetailOut(id=agency.id, slug=agency.slug, members=members, pages=pages, tracking=tracking)
