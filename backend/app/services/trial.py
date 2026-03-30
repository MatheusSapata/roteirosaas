from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.agency import Agency
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
    user.trial_warn_3days_ack = False
    user.trial_warn_1day_ack = False
    user.trial_blocked = False


def _enforce_published_limits(user: User, db: Session, unpublish_all: bool = False) -> None:
    plan = user.plan or "free"
    max_pages, _ = plan_limits(plan)
    if max_pages is None and not unpublish_all:
        return
    memberships = (
        db.query(AgencyUser)
        .filter(AgencyUser.user_id == user.id, AgencyUser.role == "owner")
        .all()
    )
    agency_ids = [m.agency_id for m in memberships]
    if not agency_ids:
        return
    agencies_to_reset: set[int] = set()
    for agency_id in agency_ids:
        published_pages = (
            db.query(Page)
            .filter(Page.agency_id == agency_id, Page.status == PageStatus.published)
            .order_by(Page.published_at.asc(), Page.id.asc())
            .all()
        )
        if not published_pages:
            continue
        if not unpublish_all and max_pages is not None and len(published_pages) <= max_pages:
            continue
        pages_to_draft = published_pages if unpublish_all or max_pages is None else published_pages[max_pages:]
        if not pages_to_draft:
            continue
        agencies_to_reset.add(agency_id)
        for page in pages_to_draft:
            page.status = PageStatus.draft
            page.published_at = None
    if agencies_to_reset:
        db.query(Agency).filter(Agency.id.in_(agencies_to_reset)).update({Agency.default_page_id: None}, synchronize_session=False)


def end_trial(user: User, db: Optional[Session] = None, keep_plan: Optional[str] = None) -> None:
    if not keep_plan:
        sub_plan = None
        if hasattr(user, "subscription") and user.subscription:
            sub_plan = user.subscription.plan
        if sub_plan and sub_plan != "free":
            keep_plan = sub_plan

    if keep_plan:
        final_plan = keep_plan
        user.plan = final_plan
        user.trial_plan = None
        user.trial_started_at = None
        user.trial_ends_at = None
        user.trial_ack_start = True
        user.trial_ack_end = True
        user.trial_warn_3days_ack = True
        user.trial_warn_1day_ack = True
        user.trial_blocked = False
    else:
        user.trial_blocked = True
        user.trial_ack_end = False
        user.trial_warn_3days_ack = True
        user.trial_warn_1day_ack = True
        if db is not None:
            _enforce_published_limits(user, db, unpublish_all=True)


def unpublish_all_user_pages(user: User, db: Session) -> None:
    """
    Força todas as páginas publicadas das agências do usuário a virarem rascunho.
    """
    _enforce_published_limits(user, db, unpublish_all=True)


def sync_trial_status(user: User, db: Session) -> None:
    if not user.trial_plan or not user.trial_started_at or user.trial_blocked:
        return
    if not user.trial_ends_at:
        return
    now = datetime.now(timezone.utc)
    if now > user.trial_ends_at:
        end_trial(user, db)
        db.add(user)
        db.commit()
        db.refresh(user)
