from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from app.models.agency_user import AgencyUser
from app.models.page import Page, PageStatus
from app.models.user import User
from app.services.plans import plan_limits


def start_trial(user: User, plan: str, duration_days: int = 7) -> None:
    now = datetime.now(timezone.utc)
    user.trial_original_plan = user.plan
    user.trial_plan = plan
    user.plan = plan
    user.trial_started_at = now
    user.trial_ends_at = now + timedelta(days=duration_days)
    user.trial_ack_start = False
    user.trial_ack_end = False


def _enforce_published_limits(user: User, db: Session) -> None:
    plan = user.plan or "free"
    max_published, _ = plan_limits(plan)
    if max_published is None:
        return
    memberships = (
        db.query(AgencyUser)
        .filter(AgencyUser.user_id == user.id, AgencyUser.role == "owner")
        .all()
    )
    agency_ids = [m.agency_id for m in memberships]
    if not agency_ids:
        return
    for agency_id in agency_ids:
        published_pages = (
            db.query(Page)
            .filter(Page.agency_id == agency_id, Page.status == PageStatus.published)
            .order_by(Page.published_at.asc(), Page.id.asc())
            .all()
        )
        if len(published_pages) <= max_published:
            continue
        for page in published_pages[max_published:]:
            page.status = PageStatus.draft
            page.published_at = None


def end_trial(user: User, db: Optional[Session] = None, keep_plan: Optional[str] = None) -> None:
    user.plan = keep_plan or user.trial_original_plan or "free"
    user.trial_plan = None
    user.trial_started_at = None
    user.trial_ends_at = None
    user.trial_ack_start = True
    user.trial_ack_end = False
    if db is not None:
        _enforce_published_limits(user, db)


def sync_trial_status(user: User, db: Session) -> None:
    if not user.trial_plan or not user.trial_started_at:
        return
    if not user.trial_ends_at:
        return
    now = datetime.now(timezone.utc)
    if now > user.trial_ends_at:
        end_trial(user, db)
        db.add(user)
        db.commit()
        db.refresh(user)
