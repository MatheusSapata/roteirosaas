import json
import re
import unicodedata
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_current_superuser, get_db
from app.api.v1.endpoints.billing import PLAN_PRICING
from app.models.cakto import CaktoOnboardingToken
from app.models.subscription import Subscription
from app.models.stats import PageVisitStats
from app.models.user import User
from app.models.user_tracking import UserTracking
from app.models.revenue import RevenueTotal
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page, PageStatus
from app.schemas.admin import (
    AdminAgencyOut,
    AdminMetricsOut,
    AdminPageOut,
    AdminUserOut,
    AdminUserPage,
    AdminUserTracking,
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


def _normalize_config(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _sanitize_digits(value: Optional[str]) -> str:
    return re.sub(r"\D", "", value or "")


def _build_whatsapp_link(digits: str, title: str) -> str:
    message = f"Oi, tenho interesse no roteiro: {title or 'Roteiro'}"
    return f"https://wa.me/{digits}?text={quote(message)}"


def _replace_whatsapp_links(node: Any, new_link: str) -> Any:
    if not isinstance(node, (dict, list)):
        return node

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and "wa.me" in item:
                    value[key] = new_link
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(node)
    return node


def _slugify(value: str) -> str:
    norm = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
    return slug or f"pagina-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@router.get("/metrics", response_model=AdminMetricsOut)
def get_admin_metrics(
    days: int = Query(30, ge=1, le=365),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminMetricsOut:
    custom_range = None
    if start_date and end_date:
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="O período informado é inválido.")
        range_days = (end_date - start_date).days + 1
        if range_days > 365:
            raise HTTPException(status_code=400, detail="O período personalizado deve ter no máximo 365 dias.")
        since_dt = datetime.combine(start_date, datetime.min.time())
        until_dt = datetime.combine(end_date, datetime.max.time())
        custom_range = (since_dt, until_dt, range_days)
    elif start_date or end_date:
        raise HTTPException(status_code=400, detail="Informe data inicial e final para o período personalizado.")

    if custom_range:
        since_dt, until_dt, days = custom_range
    else:
        days = max(1, min(days, 365))
        until_dt = datetime.utcnow()
        since_dt = until_dt - timedelta(days=days)
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

    stats_by_page = {
        page_id: {
            "total_visits": visits or 0,
            "total_cta_clicks": (clicks_cta or 0) + (clicks_whatsapp or 0),
        }
        for page_id, visits, clicks_cta, clicks_whatsapp in (
            db.query(
                PageVisitStats.page_id,
                func.sum(PageVisitStats.visits).label("visits"),
                func.sum(PageVisitStats.clicks_cta).label("clicks_cta"),
                func.sum(PageVisitStats.clicks_whatsapp).label("clicks_whatsapp"),
            )
            .group_by(PageVisitStats.page_id)
            .all()
        )
    }

    pages_details = defaultdict(list)
    for page_id, title, slug, status, agency_id, agency_slug in (
        db.query(Page.id, Page.title, Page.slug, Page.status, Page.agency_id, Agency.slug)
        .join(Agency, Agency.id == Page.agency_id)
        .all()
    ):
        stats = stats_by_page.get(page_id, {"total_visits": 0, "total_cta_clicks": 0})
        pages_details[agency_id].append(
            {
                "id": page_id,
                "title": title,
                "slug": slug,
                "status": status,
                "agency_slug": agency_slug,
                **stats,
            }
        )

    # lista de usuários com validade
    Sub = aliased(Subscription)
    users_rows = (
        db.query(User, Sub.valid_until)
        .outerjoin(Sub, Sub.id == User.subscription_id)
        .all()
    )
    user_ids = [u.id for u, _ in users_rows]
    tracking_map: dict[int, list[UserTracking]] = {}
    if user_ids:
        tracking_rows = (
            db.query(UserTracking)
            .filter(UserTracking.user_id.in_(user_ids))
            .order_by(UserTracking.created_at.desc())
            .all()
        )
        for entry in tracking_rows:
            tracking_map.setdefault(entry.user_id, []).append(entry)
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
                tracking=[AdminUserTracking.model_validate(entry) for entry in tracking_map.get(u.id, [])],
            )
        )

    # timeseries novos usuários
    new_users_count = (
        db.query(func.count(User.id))
        .filter(User.created_at >= since_dt, User.created_at <= until_dt)
        .scalar()
        or 0
    )
    ts_rows = (
        db.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= since_dt, User.created_at <= until_dt)
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

    revenue_row = db.query(RevenueTotal).order_by(RevenueTotal.id.asc()).first()
    total_revenue_amount = float(revenue_row.total_amount or 0) if revenue_row else 0.0

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
        total_revenue=total_revenue_amount,
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


@router.delete("/users/{user_id}")
def delete_user_completely(
    user_id: int,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    memberships = db.query(AgencyUser).filter(AgencyUser.user_id == user_id).all()
    owner_agency_ids = {membership.agency_id for membership in memberships if (membership.role or "").lower() == "owner"}

    if owner_agency_ids:
        db.query(Agency).filter(Agency.id.in_(owner_agency_ids)).delete(synchronize_session=False)

    db.query(AgencyUser).filter(AgencyUser.user_id == user_id).delete(synchronize_session=False)
    db.query(CaktoOnboardingToken).filter(CaktoOnboardingToken.user_id == user_id).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return {"detail": "Usuário e dados associados foram removidos."}


@router.post("/pages/{page_id}/clone", response_model=PageOut)
def clone_shared_page(
    page_id: int,
    payload: PageCloneRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> PageOut:
    if not payload.target_agency_id:
        raise HTTPException(status_code=400, detail="Agência destino obrigatória")

    target_agency = db.query(Agency).filter(Agency.id == payload.target_agency_id).first()
    if not target_agency:
        raise HTTPException(status_code=404, detail="Agência destino não encontrada.")

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

    config_copy = deepcopy(page.config_json)
    config_copy = _normalize_config(config_copy)
    whatsapp_digits = _sanitize_digits(target_agency.cta_whatsapp)
    if config_copy and whatsapp_digits:
        new_link = _build_whatsapp_link(whatsapp_digits, title)
        config_copy = _replace_whatsapp_links(config_copy, new_link)

    new_page = Page(
        agency_id=payload.target_agency_id,
        template_id=page.template_id,
        title=title,
        slug=slug,
        status=PageStatus.published,
        published_at=datetime.utcnow(),
        cover_image_url=page.cover_image_url,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        config_json=config_copy or page.config_json,
    )
    db.add(new_page)
    db.commit()
    db.refresh(new_page)
    return new_page
