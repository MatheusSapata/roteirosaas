from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db, require_agency_membership
from app.models.subscription import Subscription
from app.models.system_banner import BannerDismissal, BannerEvent, SystemBanner
from app.models.user import User
from app.schemas.system_banner import (
    BannerDismissIn,
    BannerEventIn,
    BannerEligibilityTestIn,
    BannerEligibilityTestOut,
    BannerStatsOut,
    EligibleBannerResponse,
    SystemBannerCreate,
    SystemBannerListItem,
    SystemBannerListResponse,
    SystemBannerOut,
    SystemBannerUpdate,
)

router = APIRouter()
admin_router = APIRouter(prefix="/admin/system-banners")


def _validate_payload(payload: SystemBannerCreate | SystemBannerUpdate) -> None:
    title = getattr(payload, "title", None)
    internal_name = getattr(payload, "internal_name", None)
    has_cta = getattr(payload, "has_cta", None)
    cta_type = getattr(payload, "cta_type", None)
    cta_label = getattr(payload, "cta_label", None)
    cta_target = getattr(payload, "cta_target", None)
    starts_at = getattr(payload, "starts_at", None)
    ends_at = getattr(payload, "ends_at", None)
    if title is not None and not str(title).strip():
        raise HTTPException(status_code=422, detail="Título é obrigatório.")
    if internal_name is not None and not str(internal_name).strip():
        raise HTTPException(status_code=422, detail="Nome interno é obrigatório.")
    if has_cta:
        if not cta_label or not str(cta_label).strip():
            raise HTTPException(status_code=422, detail="CTA label é obrigatório quando o CTA está ativo.")
        if cta_type in (None, "none"):
            raise HTTPException(status_code=422, detail="CTA type é obrigatório quando o CTA está ativo.")
        if not cta_target or not str(cta_target).strip():
            raise HTTPException(status_code=422, detail="CTA target é obrigatório quando o CTA está ativo.")
        if cta_type == "external_url" and not (
            str(cta_target).startswith("http://") or str(cta_target).startswith("https://")
        ):
            raise HTTPException(status_code=422, detail="URL externa precisa começar com http:// ou https://")
    if starts_at and ends_at and starts_at > ends_at:
        raise HTTPException(status_code=422, detail="Data inicial não pode ser maior que a data final.")


def _banner_stats(db: Session, banner_ids: list[int]) -> dict[int, dict[str, int | float]]:
    if not banner_ids:
        return {}
    rows = (
        db.query(
            BannerEvent.banner_id,
            BannerEvent.event_type,
            func.count(BannerEvent.id).label("count"),
        )
        .filter(BannerEvent.banner_id.in_(banner_ids))
        .group_by(BannerEvent.banner_id, BannerEvent.event_type)
        .all()
    )
    dismiss_rows = (
        db.query(BannerDismissal.banner_id, func.count(BannerDismissal.id).label("count"))
        .filter(BannerDismissal.banner_id.in_(banner_ids))
        .group_by(BannerDismissal.banner_id)
        .all()
    )
    stats: dict[int, dict[str, int | float]] = {
        bid: {"impressions": 0, "clicks": 0, "dismissals": 0, "ctr": 0.0} for bid in banner_ids
    }
    for row in rows:
        if row.event_type == "impression":
            stats[row.banner_id]["impressions"] = int(row.count)
        elif row.event_type == "click":
            stats[row.banner_id]["clicks"] = int(row.count)
        elif row.event_type == "dismiss":
            stats[row.banner_id]["dismissals"] = int(row.count)
    for row in dismiss_rows:
        stats[row.banner_id]["dismissals"] = max(int(stats[row.banner_id]["dismissals"]), int(row.count))
    for bid, item in stats.items():
        impressions = int(item["impressions"])
        clicks = int(item["clicks"])
        item["ctr"] = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.0
    return stats


@admin_router.get("", response_model=SystemBannerListResponse)
def list_system_banners(
    q: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    placement: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> SystemBannerListResponse:
    query = db.query(SystemBanner).filter(SystemBanner.deleted_at.is_(None))
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(SystemBanner.internal_name.ilike(like), SystemBanner.title.ilike(like)))
    if is_active is not None:
        query = query.filter(SystemBanner.is_active == is_active)
    if placement:
        query = query.filter(SystemBanner.placement == placement)
    rows = query.order_by(SystemBanner.priority.desc(), SystemBanner.created_at.desc()).all()
    if plan:
        rows = [row for row in rows if (not row.target_plans) or (plan in set(row.target_plans))]
    ids = [row.id for row in rows]
    stats = _banner_stats(db, ids)
    items: list[SystemBannerListItem] = []
    for row in rows:
        row_stats = stats.get(row.id, {"impressions": 0, "clicks": 0, "dismissals": 0, "ctr": 0.0})
        items.append(
            SystemBannerListItem(
                **SystemBannerOut.model_validate(row).model_dump(),
                impressions=int(row_stats["impressions"]),
                clicks=int(row_stats["clicks"]),
                dismissals=int(row_stats["dismissals"]),
                ctr=float(row_stats["ctr"]),
            )
        )
    return SystemBannerListResponse(items=items, total=len(items))


@admin_router.post("", response_model=SystemBannerOut, status_code=status.HTTP_201_CREATED)
def create_system_banner(
    payload: SystemBannerCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> SystemBannerOut:
    _validate_payload(payload)
    banner = SystemBanner(**payload.model_dump(), created_by_user_id=current_user.id, updated_by_user_id=current_user.id)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


@admin_router.get("/{banner_id}", response_model=SystemBannerOut)
def get_system_banner(
    banner_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> SystemBannerOut:
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    return banner


@admin_router.patch("/{banner_id}", response_model=SystemBannerOut)
def update_system_banner(
    banner_id: int,
    payload: SystemBannerUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> SystemBannerOut:
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    _validate_payload(payload)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(banner, key, value)
    banner.updated_by_user_id = current_user.id
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


@admin_router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_banner(
    banner_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> None:
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    banner.deleted_at = datetime.now(timezone.utc)
    banner.updated_by_user_id = current_user.id
    db.add(banner)
    db.commit()


@admin_router.post("/{banner_id}/duplicate", response_model=SystemBannerOut)
def duplicate_system_banner(
    banner_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> SystemBannerOut:
    source = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not source:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    payload = SystemBannerOut.model_validate(source).model_dump()
    payload.pop("id", None)
    payload["internal_name"] = f"{source.internal_name} (cópia)"
    payload["is_active"] = False
    payload["created_by_user_id"] = current_user.id
    payload["updated_by_user_id"] = current_user.id
    copy = SystemBanner(**payload)
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


@admin_router.post("/{banner_id}/toggle-active", response_model=SystemBannerOut)
def toggle_system_banner_active(
    banner_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> SystemBannerOut:
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    banner.is_active = not bool(banner.is_active)
    banner.updated_by_user_id = current_user.id
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


@admin_router.get("/{banner_id}/stats", response_model=BannerStatsOut)
def get_system_banner_stats(
    banner_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> BannerStatsOut:
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    stats = _banner_stats(db, [banner_id]).get(banner_id, {"impressions": 0, "clicks": 0, "dismissals": 0, "ctr": 0.0})
    return BannerStatsOut(
        banner_id=banner_id,
        impressions=int(stats["impressions"]),
        clicks=int(stats["clicks"]),
        dismissals=int(stats["dismissals"]),
        ctr=float(stats["ctr"]),
    )


def _is_dismissed(db: Session, banner_id: int, agency_id: int | None, user_id: int | None, now: datetime) -> bool:
    query = db.query(BannerDismissal).filter(BannerDismissal.banner_id == banner_id)
    if agency_id is not None:
        query = query.filter(or_(BannerDismissal.agency_id == agency_id, BannerDismissal.agency_id.is_(None)))
    if user_id is not None:
        query = query.filter(or_(BannerDismissal.user_id == user_id, BannerDismissal.user_id.is_(None)))
    dismissals = query.order_by(BannerDismissal.dismissed_at.desc()).all()
    for d in dismissals:
        if d.permanent:
            return True
        if d.expires_at and d.expires_at > now:
            return True
    return False


def _is_eligible_plan(banner: SystemBanner, user_plan: str | None) -> bool:
    if not banner.target_plans:
        return True
    if not user_plan:
        return False
    return user_plan in banner.target_plans


def _eligible_banners_query(db: Session, placement: str, now: datetime):
    return db.query(SystemBanner).filter(
        SystemBanner.deleted_at.is_(None),
        SystemBanner.is_active.is_(True),
        or_(SystemBanner.placement == placement, SystemBanner.placement == "global"),
        or_(SystemBanner.starts_at.is_(None), SystemBanner.starts_at <= now),
        or_(SystemBanner.ends_at.is_(None), SystemBanner.ends_at >= now),
    )


def _evaluate_banner_for_context(
    db: Session,
    banner: SystemBanner,
    now: datetime,
    *,
    placement: str,
    plan: str | None,
    subscription_status: str | None,
    agency_id: int | None,
    role: str | None,
    user_id: int | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    eligible = True

    if not bool(banner.is_active):
        eligible = False
        reasons.append("Banner inativo.")

    if banner.deleted_at is not None:
        eligible = False
        reasons.append("Banner removido.")

    if banner.placement not in {placement, "global"}:
        eligible = False
        reasons.append("Placement incompatível.")

    if banner.starts_at and banner.starts_at > now:
        eligible = False
        reasons.append("Ainda não iniciou.")

    if banner.ends_at and banner.ends_at < now:
        eligible = False
        reasons.append("Já expirou.")

    if not _is_eligible_plan(banner, plan):
        eligible = False
        reasons.append("Plano não elegível.")

    if banner.target_subscription_statuses and subscription_status not in set(banner.target_subscription_statuses):
        eligible = False
        reasons.append("Status de assinatura não elegível.")

    if banner.target_agency_ids and agency_id not in set(banner.target_agency_ids):
        eligible = False
        reasons.append("Agência não elegível.")

    if banner.target_user_roles and role not in set(banner.target_user_roles):
        eligible = False
        reasons.append("Perfil de usuário não elegível.")

    if user_id is not None:
        if _is_dismissed(db, banner.id, agency_id, user_id, now):
            eligible = False
            reasons.append("Banner está oculto por dismiss ativo.")

        if banner.hide_after_click:
            clicked = (
                db.query(BannerEvent.id)
                .filter(
                    BannerEvent.banner_id == banner.id,
                    BannerEvent.event_type == "click",
                    or_(BannerEvent.user_id == user_id, BannerEvent.user_id.is_(None)),
                    or_(BannerEvent.agency_id == agency_id, BannerEvent.agency_id.is_(None)),
                )
                .first()
            )
            if clicked:
                eligible = False
                reasons.append("Banner oculto após clique.")

        if banner.max_views_per_user:
            user_impressions = (
                db.query(func.count(BannerEvent.id))
                .filter(
                    BannerEvent.banner_id == banner.id,
                    BannerEvent.event_type == "impression",
                    BannerEvent.user_id == user_id,
                )
                .scalar()
            )
            if int(user_impressions or 0) >= banner.max_views_per_user:
                eligible = False
                reasons.append("Limite de visualizações por usuário atingido.")

    if agency_id is not None and banner.max_views_per_agency:
        agency_impressions = (
            db.query(func.count(BannerEvent.id))
            .filter(
                BannerEvent.banner_id == banner.id,
                BannerEvent.event_type == "impression",
                BannerEvent.agency_id == agency_id,
            )
            .scalar()
        )
        if int(agency_impressions or 0) >= banner.max_views_per_agency:
            eligible = False
            reasons.append("Limite de visualizações por agência atingido.")

    return eligible, reasons


@router.get("/eligible", response_model=EligibleBannerResponse)
def get_eligible_banner(
    placement: str = Query(default="dashboard"),
    agency_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> EligibleBannerResponse:
    if agency_id is not None:
        require_agency_membership(db, agency_id, current_user.id)
    now = datetime.now(timezone.utc)
    subscription_status = db.query(Subscription.status).filter(Subscription.user_id == current_user.id).scalar()
    candidates = (
        _eligible_banners_query(db, placement, now)
        .order_by(SystemBanner.priority.desc(), SystemBanner.created_at.desc())
        .all()
    )
    for banner in candidates:
        role = "admin_master" if current_user.is_superuser else "agency_admin"
        eligible, _ = _evaluate_banner_for_context(
            db,
            banner,
            now,
            placement=placement,
            plan=current_user.plan,
            subscription_status=subscription_status,
            agency_id=agency_id,
            role=role,
            user_id=current_user.id,
        )
        if not eligible:
            continue
        return EligibleBannerResponse(banner=banner)
    return EligibleBannerResponse(banner=None)


@admin_router.post("/test-eligibility", response_model=BannerEligibilityTestOut)
def test_system_banner_eligibility(
    payload: BannerEligibilityTestIn,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> BannerEligibilityTestOut:
    now = datetime.now(timezone.utc)
    role = payload.context.role or ("admin_master" if current_user.is_superuser else "agency_admin")
    banner = SystemBanner(**payload.model_dump(exclude={"context"}))
    banner.id = 0
    eligible, reasons = _evaluate_banner_for_context(
        db,
        banner,
        now,
        placement=payload.context.placement,
        plan=payload.context.plan or current_user.plan,
        subscription_status=payload.context.subscription_status,
        agency_id=payload.context.agency_id,
        role=role,
        user_id=None,
    )
    if eligible:
        reasons.append("Banner elegível para o contexto informado.")
    return BannerEligibilityTestOut(eligible=eligible, reasons=reasons)


@router.post("/{banner_id}/impression", status_code=status.HTTP_204_NO_CONTENT)
def track_banner_impression(
    banner_id: int,
    payload: BannerEventIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    if payload.agency_id is not None:
        require_agency_membership(db, payload.agency_id, current_user.id)
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    event = BannerEvent(
        banner_id=banner_id,
        agency_id=payload.agency_id,
        user_id=current_user.id,
        event_type="impression",
        event_metadata=payload.metadata,
    )
    db.add(event)
    db.commit()


@router.post("/{banner_id}/click", status_code=status.HTTP_204_NO_CONTENT)
def track_banner_click(
    banner_id: int,
    payload: BannerEventIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    if payload.agency_id is not None:
        require_agency_membership(db, payload.agency_id, current_user.id)
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    event = BannerEvent(
        banner_id=banner_id,
        agency_id=payload.agency_id,
        user_id=current_user.id,
        event_type="click",
        event_metadata=payload.metadata,
    )
    db.add(event)
    db.commit()


@router.post("/{banner_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_banner(
    banner_id: int,
    payload: BannerDismissIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    if payload.agency_id is not None:
        require_agency_membership(db, payload.agency_id, current_user.id)
    banner = db.query(SystemBanner).filter(SystemBanner.id == banner_id, SystemBanner.deleted_at.is_(None)).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado.")
    mode = payload.mode or banner.dismiss_behavior or "hide_forever"
    days = payload.dismiss_duration_days if payload.dismiss_duration_days is not None else banner.dismiss_duration_days
    now = datetime.now(timezone.utc)
    permanent = mode == "hide_forever"
    expires_at = None
    if mode == "hide_for_days":
        if not days or days <= 0:
            days = 7
        expires_at = now + timedelta(days=days)
    dismissal = BannerDismissal(
        banner_id=banner_id,
        agency_id=payload.agency_id,
        user_id=current_user.id,
        permanent=permanent,
        expires_at=expires_at,
    )
    db.add(dismissal)
    db.add(
        BannerEvent(
            banner_id=banner_id,
            agency_id=payload.agency_id,
            user_id=current_user.id,
            event_type="dismiss",
            event_metadata={"mode": mode, "days": days},
        )
    )
    db.commit()
