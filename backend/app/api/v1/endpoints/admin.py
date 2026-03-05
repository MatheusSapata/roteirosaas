import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_current_superuser, get_db
from app.api.v1.endpoints.billing import PLAN_PRICING
from app.models.subscription import Subscription
from app.models.user import User
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page, PageStatus
from app.schemas.admin import (
    AdminAgencyOut,
    AdminMetricsOut,
    AdminPageOut,
    AdminUserOut,
    AdminUserPage,
    TimeseriesPoint,
)
from app.schemas.page import PageOut
from app.services.trial import start_trial

router = APIRouter()
EXCLUDED_PLAN = "teste"


class TrialRequest(BaseModel):
    plan: str = Field(default="infinity")
    days: int = Field(default=7, ge=1, le=30)


class PageCloneRequest(BaseModel):
    target_agency_id: int
    title: Optional[str] = None


def _slugify(value: str) -> str:
    norm = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
    return slug or f"pagina-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@router.get("/metrics", response_model=AdminMetricsOut)
def get_admin_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminMetricsOut:
    days = max(1, min(days, 365))
    plan_not_test = or_(User.plan.is_(None), func.lower(User.plan) != EXCLUDED_PLAN)
    total_users = db.query(func.count(User.id)).filter(plan_not_test).scalar() or 0
    total_agencies = db.query(func.count(Agency.id)).scalar() or 0
    total_pages = db.query(func.count(Page.id)).scalar() or 0
    published_pages = (
        db.query(func.count(Page.id))
        .filter(Page.status == PageStatus.published)
        .scalar()
        or 0
    )

    # planos
    plan_counts = (
        db.query(User.plan, User.trial_plan, func.count(User.id))
        .group_by(User.plan, User.trial_plan)
        .all()
    )
    plans = []
    for plan, trial_plan, count in plan_counts:
        base = plan.title()
        label = f"{base} (trial)" if trial_plan else base
        plans.append({"plan": label, "count": count})

    # agências relacionadas aos usuários
    agency_links = (
        db.query(AgencyUser.user_id, Agency.id, Agency.name, Agency.slug)
        .join(Agency, Agency.id == AgencyUser.agency_id)
        .order_by(AgencyUser.user_id, Agency.created_at)
        .all()
    )
    agency_by_user: dict[int, tuple[int, str, str]] = {}
    for user_id, agency_id, agency_name, agency_slug in agency_links:
        agency_by_user.setdefault(user_id, (agency_id, agency_name, agency_slug))

    pages_by_agency_count = {
        agency_id: count
        for agency_id, count in (
            db.query(Page.agency_id, func.count(Page.id))
            .filter(Page.status == PageStatus.published)
            .group_by(Page.agency_id)
            .all()
        )
        if agency_id is not None
    }

    pages_details = defaultdict(list)
    for page_id, title, slug, status, agency_id, agency_slug in (
        db.query(Page.id, Page.title, Page.slug, Page.status, Page.agency_id, Agency.slug)
        .join(Agency, Agency.id == Page.agency_id)
        .all()
    ):
        pages_details[agency_id].append(
            {
                "id": page_id,
                "title": title,
                "slug": slug,
                "status": status,
                "agency_slug": agency_slug,
            }
        )

    # lista de usuários com validade
    Sub = aliased(Subscription)
    users_rows = (
        db.query(User, Sub.valid_until)
        .outerjoin(Sub, Sub.id == User.subscription_id)
        .all()
    )
    users: List[AdminUserOut] = []
    for u, valid_until in users_rows:
        agency_info = agency_by_user.get(u.id)
        agency_id = agency_info[0] if agency_info else None
        agency_name = agency_info[1] if agency_info else None
        agency_slug = agency_info[2] if agency_info else None
        pages_for_agency = pages_details.get(agency_id, []) if agency_id else []
        user_published_pages = [
            AdminUserPage(**page)
            for page in pages_for_agency
            if page.get("status") == PageStatus.published
        ]
        user_draft_pages = [
            AdminUserPage(**page)
            for page in pages_for_agency
            if page.get("status") == PageStatus.draft
        ]
        users.append(
            AdminUserOut(
                id=u.id,
                name=u.name,
                email=u.email,
                plan=u.plan,
                is_superuser=u.is_superuser,
                created_at=u.created_at,
                valid_until=valid_until,
                trial_plan=u.trial_plan,
                trial_ends_at=u.trial_ends_at,
                agency_id=agency_id,
                agency_name=agency_name,
                agency_slug=agency_slug,
                active_pages=pages_by_agency_count.get(agency_id, 0) if agency_id else 0,
                whatsapp=u.whatsapp,
                published_pages=user_published_pages,
                draft_pages=user_draft_pages,
                draft_pages_count=len(user_draft_pages),
            )
        )

    # timeseries novos usuários
    since = datetime.utcnow() - timedelta(days=days)
    new_users_count = db.query(func.count(User.id)).filter(User.created_at >= since).scalar() or 0
    ts_rows = (
        db.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )
    timeseries = [TimeseriesPoint(label=str(d), value=c) for d, c in ts_rows]

    # MRR: soma dos preços mensais dos planos ativos (exceto free)
    def get_monthly_price(plan_key: Optional[str], cycle_key: Optional[str]) -> float:
        if not plan_key:
            return 0.0
        plan_info = PLAN_PRICING.get(plan_key)
        if not plan_info:
            return 0.0
        cycle = (cycle_key or "monthly").lower()
        cycle_info = plan_info.get(cycle)
        if not cycle_info:
            return 0.0
        price = float(cycle_info.get("price", 0.0))
        return price / 12.0 if cycle == "annual" else price

    mrr = 0.0
    active_subs = (
        db.query(Subscription)
        .filter(Subscription.status == "active")
        .all()
    )
    for sub in active_subs:
        if (sub.plan or "").lower() == EXCLUDED_PLAN:
            continue
        mrr += get_monthly_price(sub.plan, sub.billing_cycle)

    recent_agencies_rows = (
        db.query(Agency, func.count(Page.id).label("pages_count"))
        .outerjoin(Page, Page.agency_id == Agency.id)
        .group_by(Agency.id)
        .order_by(Agency.created_at.desc())
        .limit(6)
        .all()
    )
    agencies = [
        AdminAgencyOut(
            id=agency.id,
            name=agency.name,
            slug=agency.slug,
            created_at=agency.created_at,
            pages_count=pages_count or 0,
        )
        for agency, pages_count in recent_agencies_rows
    ]

    recent_pages_rows = (
        db.query(Page, Agency.name)
        .join(Agency, Agency.id == Page.agency_id)
        .order_by(Page.created_at.desc())
        .limit(8)
        .all()
    )
    pages_overview = [
        AdminPageOut(
            id=page.id,
            title=page.title,
            status=page.status,
            agency_name=agency_name,
            created_at=page.created_at,
            published_at=page.published_at,
        )
        for page, agency_name in recent_pages_rows
    ]

    return AdminMetricsOut(
        total_users=total_users,
        total_agencies=total_agencies,
        total_pages=total_pages,
        published_pages=published_pages,
        plans=plans,
        users=users,
        agencies=agencies,
        pages=pages_overview,
        new_users_last_days=new_users_count,
        new_users_timeseries=timeseries,
        mrr=mrr,
    )


@router.post("/users/{user_id}/grant-trial", response_model=AdminUserOut)
def grant_trial(
    user_id: int,
    payload: TrialRequest,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> AdminUserOut:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    start_trial(user, payload.plan, payload.days)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/pages/{page_id}/clone", response_model=PageOut)
def clone_shared_page(
    page_id: int,
    payload: PageCloneRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> PageOut:
    if not payload.target_agency_id:
        raise HTTPException(status_code=400, detail="Agência destino obrigatória")

    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == payload.target_agency_id, AgencyUser.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Você não participa da agência selecionada.")

    page = (
        db.query(Page)
        .join(Agency, Agency.id == Page.agency_id)
        .filter(Page.id == page_id, Page.status == PageStatus.published)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Página publicada não encontrada.")

    title = (payload.title or page.title or "Página importada").strip()
    slug_base = _slugify(title)
    slug = slug_base
    suffix = 1
    while (
        db.query(Page)
        .filter(Page.agency_id == payload.target_agency_id, Page.slug == slug)
        .first()
        is not None
    ):
        suffix += 1
        slug = f"{slug_base}-{suffix}"

    new_page = Page(
        agency_id=payload.target_agency_id,
        template_id=page.template_id,
        title=title,
        slug=slug,
        status=PageStatus.draft,
        cover_image_url=page.cover_image_url,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        config_json=page.config_json,
    )
    db.add(new_page)
    db.commit()
    db.refresh(new_page)
    return new_page
