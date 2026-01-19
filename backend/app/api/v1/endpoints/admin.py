from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_current_superuser, get_db
from app.api.v1.endpoints.billing import PLAN_PRICING
from app.models.subscription import Subscription
from app.models.user import User
from app.models.agency import Agency
from app.models.page import Page
from app.schemas.admin import (
    AdminAgencyOut,
    AdminMetricsOut,
    AdminPageOut,
    AdminUserOut,
    TimeseriesPoint,
)
from app.services.trial import start_trial

router = APIRouter()


class TrialRequest(BaseModel):
    plan: str = Field(default="infinity")
    days: int = Field(default=7, ge=1, le=30)


@router.get("/metrics", response_model=AdminMetricsOut)
def get_admin_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminMetricsOut:
    days = max(1, min(days, 365))
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_agencies = db.query(func.count(Agency.id)).scalar() or 0
    total_pages = db.query(func.count(Page.id)).scalar() or 0
    published_pages = db.query(func.count(Page.id)).filter(Page.status == "published").scalar() or 0

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

    # lista de usuários com validade
    Sub = aliased(Subscription)
    users_rows = (
        db.query(User, Sub.valid_until)
        .outerjoin(Sub, Sub.id == User.subscription_id)
        .all()
    )
    users: List[AdminUserOut] = [
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
        )
        for u, valid_until in users_rows
    ]

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
    plan_price_map = {k: v["price"] for k, v in PLAN_PRICING.items()}
    mrr = 0.0
    active_subs = (
        db.query(Subscription)
        .filter(Subscription.status == "active")
        .all()
    )
    for sub in active_subs:
        price = plan_price_map.get(sub.plan, 0.0)
        mrr += price

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
    pages = [
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
        pages=pages,
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
