import json
import re
import unicodedata
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, aliased

from app.api.deps import get_current_superuser, get_db
from app.api.v1.endpoints.billing import set_subscription_cancelled
from app.core.config import get_settings
from app.models.cakto import CaktoOnboardingToken
from app.models.cakto import CaktoEventLog
from app.models.subscription import Subscription
from app.models.stats import PageVisitStats
from app.models.user import User
from app.models.user_tracking import UserTracking
from app.models.user_session import UserSession
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page, PageStatus
from app.schemas.admin import (
    AdminAgencyOut,
    AdminLtvCustomerRow,
    AdminLtvCustomersOut,
    AdminMetricsOut,
    AdminOnlineSession,
    AdminOnlineSessionsResponse,
    AdminPageOut,
    AdminRevenueForecastDay,
    AdminRevenueForecastEntry,
    AdminRevenueForecastOut,
    AdminUserOut,
    AdminUserPage,
    AdminUserTracking,
    TimeseriesPoint,
    SubscriptionTimeseriesPoint,
)
from app.schemas.page import PageOut
from app.services.cakto import CaktoAPIError, CaktoIntegrationService
from app.services.asaas import AsaasAPIError, AsaasClient
from app.services.ntfy import (
    NtfyService,
    NtfyServiceError,
    SubscriptionPushScenario,
    build_subscription_push_message,
)
from app.services.trial import start_trial, unpublish_all_user_pages
from app.services.viajechat_checkout_flow import mark_cancelled as mark_viajechat_cancelled

router = APIRouter()
EXCLUDED_PLAN = "teste"
ONLINE_WINDOW_MINUTES = 10
settings = get_settings()


def _extract_asaas_error_detail(exc: AsaasAPIError) -> str:
    raw = str(exc or "").strip()
    if raw and raw != "{}":
        return raw
    return "Erro sem detalhes retornado pelo Asaas."


class TrialRequest(BaseModel):
    plan: str = Field(default="infinity")
    days: int = Field(default=7, ge=1, le=30)


class PageCloneRequest(BaseModel):
    target_agency_id: int
    title: Optional[str] = None


class RefundRequest(BaseModel):
    reason: Optional[str] = None


class PushTestResponse(BaseModel):
    success: bool
    message: str | None = None


@router.post("/test-push", response_model=PushTestResponse)
def test_push_notification(admin: User = Depends(get_current_superuser)) -> PushTestResponse:
    service = NtfyService()
    try:
        service.publish(
            topic="roteiro_online_assinaturas",
            title="Teste Roteiro Online",
            message="Olá mundo",
            priority=3,
            tags=["rocket"],
        )
    except NtfyServiceError as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"success": False, "message": str(exc) or "erro"},
        )
    return PushTestResponse(success=True)


class PushSubscriptionTestRequest(BaseModel):
    scenario: SubscriptionPushScenario


class PushSubscriptionTestPayload(BaseModel):
    user_name: str
    payment_method: str
    amount: Decimal
    plan_name: str | None = None
    offer_name: str | None = None
    previous_plan_name: str | None = None
    upgraded_plan_name: str | None = None
    cancelled_item: str | None = None


_PUSH_SUBSCRIPTION_TEST_DATA: dict[SubscriptionPushScenario, PushSubscriptionTestPayload] = {
    SubscriptionPushScenario.NEW: PushSubscriptionTestPayload(
        user_name="Ana Teste",
        payment_method="PIX",
        amount=Decimal("197.00"),
        plan_name="Plano Essencial",
        offer_name="Oferta Essencial Mensal",
    ),
    SubscriptionPushScenario.RENEWED: PushSubscriptionTestPayload(
        user_name="Bruno Teste",
        payment_method="Cartão de crédito",
        amount=Decimal("297.00"),
        plan_name="Plano Infinity",
        offer_name="Oferta Infinity Anual",
    ),
    SubscriptionPushScenario.CANCELLED: PushSubscriptionTestPayload(
        user_name="Carla Teste",
        payment_method="Boleto",
        amount=Decimal("297.00"),
        plan_name="Plano Growth",
        offer_name="Oferta Growth Mensal",
        cancelled_item="Assinatura mensal do Plano Growth",
    ),
    SubscriptionPushScenario.UPGRADED: PushSubscriptionTestPayload(
        user_name="Daniel Teste",
        payment_method="Cartão de crédito",
        amount=Decimal("149.90"),
        previous_plan_name="Plano Essencial",
        upgraded_plan_name="Plano Growth",
    ),
    SubscriptionPushScenario.TEST: PushSubscriptionTestPayload(
        user_name="Usuário de teste",
        payment_method="PIX",
        amount=Decimal("0.00"),
        plan_name="Teste manual",
        offer_name="Oferta de teste",
    ),
}


def _test_push_tags_for_scenario(tags: list[str], scenario: SubscriptionPushScenario) -> list[str]:
    if scenario == SubscriptionPushScenario.CANCELLED:
        return ["skull", *[tag for tag in tags if tag != "rocket"]]
    return tags


@router.post("/test-push/subscription", response_model=PushTestResponse)
def test_push_subscription_notification(
    payload: PushSubscriptionTestRequest,
    admin: User = Depends(get_current_superuser),
) -> PushTestResponse:
    test_data = _PUSH_SUBSCRIPTION_TEST_DATA[payload.scenario]
    title, message, tags = build_subscription_push_message(
        scenario=payload.scenario,
        user_name=test_data.user_name,
        payment_method=test_data.payment_method,
        amount=test_data.amount,
        plan_name=test_data.plan_name,
        offer_name=test_data.offer_name,
        previous_plan_name=test_data.previous_plan_name,
        upgraded_plan_name=test_data.upgraded_plan_name,
        cancelled_item=test_data.cancelled_item,
    )
    tags = _test_push_tags_for_scenario(tags, payload.scenario)
    service = NtfyService()
    try:
        service.publish(
            topic="roteiro_online_assinaturas",
            title=title,
            message=message,
            priority=3,
            tags=tags,
        )
    except NtfyServiceError as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"success": False, "message": str(exc) or "erro"},
        )
    return PushTestResponse(success=True)


@router.post("/test-push/subscription/all", response_model=PushTestResponse)
def test_push_subscription_notifications_all(
    admin: User = Depends(get_current_superuser),
) -> PushTestResponse:
    service = NtfyService()
    for scenario, test_data in _PUSH_SUBSCRIPTION_TEST_DATA.items():
        title, message, tags = build_subscription_push_message(
            scenario=scenario,
            user_name=test_data.user_name,
            payment_method=test_data.payment_method,
        amount=test_data.amount,
        plan_name=test_data.plan_name,
        offer_name=test_data.offer_name,
        previous_plan_name=test_data.previous_plan_name,
        upgraded_plan_name=test_data.upgraded_plan_name,
        cancelled_item=test_data.cancelled_item,
    )
        tags = _test_push_tags_for_scenario(tags, scenario)
        service.publish(
            topic="roteiro_online_assinaturas",
            title=title,
            message=message,
            priority=3,
            tags=tags,
        )
    return PushTestResponse(success=True)


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
    digits = re.sub(r"\D", "", value or "")
    digits = digits.lstrip("0")
    if not digits:
        return ""
    if digits.startswith("55"):
        return digits
    if len(digits) in (10, 11):
        return f"55{digits}"
    return digits


def _build_whatsapp_link(digits: str, title: str) -> str:
    normalized = _sanitize_digits(digits)
    if not normalized:
        return ""
    message = f"Oi, tenho interesse no roteiro: {title or 'Roteiro'}"
    return f"https://wa.me/{normalized}?text={quote(message)}"


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


def _payload_nested(data: Any, *keys: str) -> Any:
    current = data
    for key in keys:
        if current is None:
            return None
        if isinstance(current, list):
            current = current[0] if current else None
        if current is None:
            return None
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = "".join(ch for ch in text.replace(",", ".") if ch.isdigit() or ch in {".", "-"})
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


def _extract_cakto_amount(payload: dict[str, Any]) -> Decimal:
    candidates: list[Any] = []

    def push(value: Any) -> None:
        if value is not None:
            candidates.append(value)

    primary = payload.get("data")
    if isinstance(primary, list):
        primary = primary[0] if primary else None

    order = None
    if isinstance(primary, dict):
        if primary.get("id") and primary.get("status"):
            order = primary
        elif isinstance(primary.get("order"), dict):
            order = primary.get("order")

    if isinstance(order, dict):
        push(order.get("amount"))
        push(order.get("amount_paid"))
        push(order.get("netAmount"))
        push(order.get("net_amount"))
        push(order.get("price"))
        push(order.get("baseAmount"))
        push(order.get("base_amount"))

    push(_payload_nested(payload, "data", "order", "amount"))
    push(_payload_nested(payload, "data", "order", "amount_paid"))
    push(_payload_nested(payload, "data", "order", "netAmount"))
    push(_payload_nested(payload, "data", "order", "net_amount"))
    push(_payload_nested(payload, "data", "subscription", "amount"))
    push(_payload_nested(payload, "data", "subscription", "currentPeriod", "amount"))
    push(_payload_nested(payload, "data", "subscription", "current_period", "amount"))

    for candidate in candidates:
        decimal_value = _to_decimal(candidate)
        if decimal_value is not None and decimal_value > 0:
            return decimal_value
    return Decimal("0")


def _extract_customer_email(payload: dict[str, Any]) -> str | None:
    candidates = [
        _payload_nested(payload, "data", "order", "customer", "email"),
        _payload_nested(payload, "data", "customer", "email"),
        _payload_nested(payload, "customer", "email"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return None


def _extract_customer_name(payload: dict[str, Any]) -> str | None:
    candidates = [
        _payload_nested(payload, "data", "order", "customer", "name"),
        _payload_nested(payload, "data", "customer", "name"),
        _payload_nested(payload, "customer", "name"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_next_due_datetime(payload: dict[str, Any]) -> datetime | None:
    candidates = [
        _payload_nested(payload, "data", "subscription", "nextDueDate"),
        _payload_nested(payload, "data", "subscription", "next_due_date"),
        _payload_nested(payload, "subscription", "nextDueDate"),
        _payload_nested(payload, "subscription", "next_due_date"),
        _payload_nested(payload, "data", "order", "nextDueDate"),
        _payload_nested(payload, "data", "order", "next_due_date"),
    ]
    for value in candidates:
        if not value:
            continue
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            iso_text = text.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(iso_text)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                    try:
                        parsed_date = datetime.strptime(text, fmt)
                        return parsed_date.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
    return None


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
        db.query(User, Sub)
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
    for u, sub in users_rows:
        valid_until = sub.valid_until if sub else None
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
                is_active=u.is_active,
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
                subscription_provider=sub.provider if sub else None,
                subscription_status=sub.status if sub else None,
                subscription_asaas_subscription_id=sub.asaas_subscription_id if sub else None,
                subscription_cakto_order_id=sub.cakto_order_id if sub else None,
                subscription_cakto_subscription_code=sub.cakto_subscription_code if sub else None,
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

    # timeseries de assinaturas (novas, renovadas, canceladas) + churn diario
    sub_created_rows = (
        db.query(func.date(Subscription.created_at), func.count(Subscription.id))
        .filter(Subscription.created_at >= since_dt, Subscription.created_at <= until_dt)
        .group_by(func.date(Subscription.created_at))
        .all()
    )
    new_by_day = {str(day): int(count or 0) for day, count in sub_created_rows}

    cakto_event_rows = (
        db.query(func.date(CaktoEventLog.processed_at), CaktoEventLog.event_type, func.count(CaktoEventLog.id))
        .filter(
            CaktoEventLog.processed_at.isnot(None),
            CaktoEventLog.processed_at >= since_dt,
            CaktoEventLog.processed_at <= until_dt,
        )
        .group_by(func.date(CaktoEventLog.processed_at), CaktoEventLog.event_type)
        .all()
    )
    renewed_by_day: dict[str, int] = defaultdict(int)
    cancelled_by_day: dict[str, int] = defaultdict(int)
    for day, event_type, count in cakto_event_rows:
        normalized_type = (event_type or "").strip().lower()
        day_key = str(day)
        if normalized_type == "subscription_renewed":
            renewed_by_day[day_key] += int(count or 0)
        elif normalized_type in {"subscription_canceled", "subscription_cancelled"}:
            cancelled_by_day[day_key] += int(count or 0)

    day_cursor = since_dt.date()
    day_end = until_dt.date()
    subscriptions_timeseries: list[SubscriptionTimeseriesPoint] = []
    while day_cursor <= day_end:
        day_key = day_cursor.isoformat()
        new_count = int(new_by_day.get(day_key, 0))
        renewed_count = int(renewed_by_day.get(day_key, 0))
        cancelled_count = int(cancelled_by_day.get(day_key, 0))
        base = new_count + renewed_count
        churn_rate = (cancelled_count / base * 100.0) if base > 0 else 0.0
        subscriptions_timeseries.append(
            SubscriptionTimeseriesPoint(
                label=day_key,
                new_subscriptions=new_count,
                renewed_subscriptions=renewed_count,
                cancelled_subscriptions=cancelled_count,
                churn_rate=round(churn_rate, 2),
            )
        )
        day_cursor += timedelta(days=1)

    # churn mensal SaaS (mês corrente): cancelamentos do mês / base ativa no início do mês
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    monthly_churn_base = (
        db.query(func.count(Subscription.id))
        .filter(
            Subscription.created_at < month_start,
            Subscription.plan.isnot(None),
            func.lower(Subscription.plan).notin_(["free", EXCLUDED_PLAN]),
            Subscription.status.in_(("active", "cancelled")),
        )
        .scalar()
        or 0
    )

    monthly_churn_cancelled = (
        db.query(func.count(CaktoEventLog.id))
        .filter(
            CaktoEventLog.processed_at.isnot(None),
            CaktoEventLog.processed_at >= month_start,
            CaktoEventLog.processed_at < next_month_start,
            func.lower(CaktoEventLog.event_type).in_(["subscription_canceled", "subscription_cancelled"]),
        )
        .scalar()
        or 0
    )

    monthly_churn_rate = (
        round(float(monthly_churn_cancelled) / float(monthly_churn_base) * 100.0, 2)
        if monthly_churn_base > 0
        else 0.0
    )

    mrr = (
        db.query(func.coalesce(func.sum(Subscription.mrr_amount), 0))
        .filter(Subscription.status == "active")
        .filter(or_(Subscription.plan.is_(None), func.lower(Subscription.plan) != EXCLUDED_PLAN))
        .scalar()
        or 0
    )
    mrr = float(mrr)

    cakto_revenue_events = (
        db.query(CaktoEventLog.payload)
        .filter(
            func.lower(CaktoEventLog.event_type).in_(
                ["purchase_approved", "subscription_renewed"]
            ),
            CaktoEventLog.status == "processed",
        )
        .all()
    )
    total_revenue_decimal = Decimal("0")
    for (payload,) in cakto_revenue_events:
        if isinstance(payload, dict):
            total_revenue_decimal += _extract_cakto_amount(payload)
    total_revenue_amount = float(total_revenue_decimal)

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
        subscriptions_timeseries=subscriptions_timeseries,
        monthly_churn_rate=monthly_churn_rate,
        monthly_churn_cancelled=int(monthly_churn_cancelled),
        monthly_churn_base=int(monthly_churn_base),
        mrr=mrr,
        total_revenue=total_revenue_amount,
    )


@router.get("/agencies/search", response_model=list[AdminAgencyOut])
def search_admin_agencies(
    q: str | None = Query(None, description="Nome ou slug da agência"),
    limit: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[AdminAgencyOut]:
    normalized = (q or "").strip().lower()
    query = (
        db.query(Agency, func.count(Page.id).label("pages_count"))
        .outerjoin(Page, Page.agency_id == Agency.id)
        .group_by(Agency.id)
    )
    if normalized:
        pattern = f"%{normalized}%"
        query = query.filter(
            or_(
                func.lower(Agency.name).like(pattern),
                func.lower(Agency.slug).like(pattern),
            )
        )
    result_rows = (
        query.order_by(func.lower(Agency.name))
        .limit(limit)
        .all()
    )
    return [
        AdminAgencyOut(
            id=agency.id,
            name=agency.name,
            slug=agency.slug,
            created_at=agency.created_at,
            pages_count=pages_count or 0,
        )
        for agency, pages_count in result_rows
    ]


@router.get("/revenue-forecast", response_model=AdminRevenueForecastOut)
def get_admin_revenue_forecast(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminRevenueForecastOut:

    now_utc = datetime.now(timezone.utc)
    start_day = now_utc.date()
    end_day = start_day + timedelta(days=days - 1)

    rows = (
        db.query(Subscription, User)
        .join(User, User.id == Subscription.user_id)
        .filter(func.lower(Subscription.provider).in_(("cakto", "asaas")))
        .filter(func.lower(Subscription.status) == "active")
        .filter(Subscription.valid_until.isnot(None))
        .filter(Subscription.mrr_amount > 0)
        .all()
    )

    by_day: dict[date, list[AdminRevenueForecastEntry]] = defaultdict(list)
    total_mrr = Decimal("0")
    total_count = 0
    for subscription, user in rows:
        valid_until = subscription.valid_until
        if not valid_until:
            continue
        amount_decimal = subscription.mrr_amount or Decimal("0")
        amount_float = float(amount_decimal)
        expected_on = valid_until + timedelta(days=1)
        expected_day = expected_on.date()
        if expected_day < start_day or expected_day > end_day:
            continue

        entry = AdminRevenueForecastEntry(
            subscription_id=subscription.id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            plan=subscription.plan or user.plan or "free",
            provider=subscription.provider or "",
            valid_until=valid_until,
            expected_on=expected_on,
            mrr_amount=amount_float,
        )
        by_day[expected_day].append(entry)
        total_mrr += amount_decimal
        total_count += 1

    forecast_days: list[AdminRevenueForecastDay] = []
    cursor = start_day
    while cursor <= end_day:
        entries = by_day.get(cursor, [])
        day_total = float(sum((Decimal(str(item.mrr_amount)) for item in entries), Decimal("0")))
        forecast_days.append(
            AdminRevenueForecastDay(
                date=datetime.combine(cursor, datetime.min.time(), tzinfo=timezone.utc),
                total_mrr=day_total,
                subscriptions_count=len(entries),
                entries=sorted(entries, key=lambda item: item.user_name.lower()),
            )
        )
        cursor += timedelta(days=1)

    return AdminRevenueForecastOut(
        start_date=datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc),
        end_date=datetime.combine(end_day, datetime.max.time(), tzinfo=timezone.utc),
        days=days,
        total_mrr=float(total_mrr),
        subscriptions_count=total_count,
        forecast_days=forecast_days,
    )


@router.get("/ltv-customers", response_model=AdminLtvCustomersOut)
def get_admin_ltv_customers(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminLtvCustomersOut:
    event_rows = (
        db.query(CaktoEventLog)
        .filter(CaktoEventLog.event_type.isnot(None))
        .order_by(CaktoEventLog.created_at.asc())
        .all()
    )

    trackable_types = {
        "purchase_approved",
        "subscription_created",
        "subscription_renewed",
        "subscription_canceled",
        "subscription_cancelled",
        "subscription_renewal_refused",
    }
    revenue_types = {"purchase_approved", "subscription_renewed"}
    active_types = {"purchase_approved", "subscription_created", "subscription_renewed"}
    cancelled_types = {"subscription_canceled", "subscription_cancelled", "subscription_renewal_refused"}

    by_email: dict[str, dict[str, Any]] = {}
    for row in event_rows:
        event_type = (row.event_type or "").strip().lower()
        if event_type not in trackable_types:
            continue

        payload = row.payload if isinstance(row.payload, dict) else {}
        email = _extract_customer_email(payload)
        if not email:
            continue

        occurred_at = row.processed_at or row.created_at or datetime.utcnow()
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        item = by_email.setdefault(
            email,
            {
                "email": email,
                "name": _extract_customer_name(payload),
                "entered_at": occurred_at,
                "is_active": False,
                "renewals_count": 0,
                "total_revenue": Decimal("0"),
                "cancelled_at": None,
                "next_renewal_at": None,
                "last_event_type": event_type,
                "last_event_at": occurred_at,
            },
        )

        if not item.get("name"):
            item["name"] = _extract_customer_name(payload)

        if occurred_at < item["entered_at"]:
            item["entered_at"] = occurred_at

        if occurred_at >= item["last_event_at"]:
            item["last_event_at"] = occurred_at
            item["last_event_type"] = event_type

        if event_type in revenue_types:
            item["total_revenue"] += _extract_cakto_amount(payload)
        if event_type == "subscription_renewed":
            item["renewals_count"] += 1
        if event_type in active_types:
            item["is_active"] = True
        if event_type in cancelled_types:
            item["is_active"] = False
            item["cancelled_at"] = occurred_at

        next_due = _extract_next_due_datetime(payload)
        if next_due and (item["next_renewal_at"] is None or next_due > item["next_renewal_at"]):
            item["next_renewal_at"] = next_due

    customers = [
        AdminLtvCustomerRow(
            email=data["email"],
            name=data["name"],
            entered_at=data["entered_at"],
            is_active=bool(data["is_active"]),
            renewals_count=int(data["renewals_count"]),
            total_revenue=float(data["total_revenue"]),
            cancelled_at=data["cancelled_at"],
            next_renewal_at=data["next_renewal_at"],
            last_event_type=data["last_event_type"],
            last_event_at=data["last_event_at"],
        )
        for data in by_email.values()
    ]
    customers.sort(key=lambda item: (item.total_revenue, item.renewals_count), reverse=True)

    total_revenue = float(sum((Decimal(str(item.total_revenue)) for item in customers), Decimal("0")))
    active_count = sum(1 for item in customers if item.is_active)
    cancelled_count = sum(1 for item in customers if item.cancelled_at is not None and not item.is_active)

    return AdminLtvCustomersOut(
        total_customers=len(customers),
        active_customers=active_count,
        cancelled_customers=cancelled_count,
        total_revenue=total_revenue,
        customers=customers,
    )


@router.get("/online-sessions", response_model=AdminOnlineSessionsResponse)
def get_online_sessions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminOnlineSessionsResponse:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=ONLINE_WINDOW_MINUTES)
    session_rows = (
        db.query(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .filter(
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
            UserSession.last_seen_at >= cutoff,
        )
        .order_by(UserSession.last_seen_at.desc())
        .all()
    )
    aggregated: dict[int, dict[str, Any]] = {}
    for session, user in session_rows:
        entry = aggregated.get(user.id)
        if not entry:
            entry = {"user": user, "latest": session, "count": 0}
            aggregated[user.id] = entry
        entry["count"] += 1
        latest = entry["latest"]
        if (
            not latest.last_seen_at
            or (session.last_seen_at and session.last_seen_at > latest.last_seen_at)
        ):
            entry["latest"] = session

    sessions = [
        AdminOnlineSession(
            session_id=data["latest"].id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            user_plan=user.plan,
            ip_address=data["latest"].ip_address,
            device_label=data["latest"].device_label,
            client_name=data["latest"].client_name,
            created_at=data["latest"].created_at,
            last_seen_at=data["latest"].last_seen_at,
            active_sessions=data["count"],
            last_path=data["latest"].last_path,
        )
        for user_id, data in aggregated.items()
        for user in [data["user"]]
    ]
    sessions.sort(key=lambda item: item.last_seen_at or now, reverse=True)
    unique_users = len(aggregated)
    return AdminOnlineSessionsResponse(
        sessions=sessions,
        total_online=len(session_rows),
        unique_users=unique_users,
        generated_at=now,
    )


@router.post("/online-sessions/{session_id}/revoke")
def revoke_online_session(
    session_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser),
) -> dict[str, str]:
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session or session.revoked_at:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou já encerrada.")
    session.revoked_at = datetime.now(timezone.utc)
    session.revoked_by_user_id = admin.id
    db.add(session)
    db.commit()
    return {"detail": "Sessão encerrada com sucesso."}


@router.post("/online-sessions/user/{user_id}/revoke")
def revoke_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser),
) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .all()
    )
    if not sessions:
        raise HTTPException(status_code=404, detail="Nenhuma sessão ativa encontrada para este usuário.")
    for session in sessions:
        session.revoked_at = now
        session.revoked_by_user_id = admin.id
        db.add(session)
    db.commit()
    return {"detail": f"{len(sessions)} sessão(ões) encerradas para este usuário."}


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


@router.post("/users/{user_id}/refund")
def refund_user_subscription(
    user_id: int,
    payload: RefundRequest,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    subscription = user.subscription
    if not subscription or (subscription.provider or "").lower() != "cakto":
        raise HTTPException(status_code=400, detail="Usuário não possui assinatura ativa via Cakto.")
    if not subscription.cakto_order_id:
        raise HTTPException(status_code=400, detail="Pedido Cakto não encontrado para este usuário.")

    service = CaktoIntegrationService(db)
    try:
        service.request_order_refund(order_id=subscription.cakto_order_id, reason=payload.reason)
    except CaktoAPIError as exc:  # noqa: BLE001
        raw_detail = exc.args[0] if exc.args else "Erro ao solicitar reembolso."
        if isinstance(raw_detail, dict):
            detail = raw_detail.get("detail") or raw_detail.get("message") or str(raw_detail)
        else:
            detail = str(raw_detail)
        raise HTTPException(status_code=502, detail=detail) from exc

    set_subscription_cancelled(subscription)
    user.plan = "free"
    user.is_active = False
    unpublish_all_user_pages(user, db)
    db.add_all([user, subscription])
    db.commit()
    try:
        mark_viajechat_cancelled(
            name=user.name or "",
            email=user.email or "",
            phone=user.whatsapp or "",
        )
    except Exception:  # noqa: BLE001
        pass
    db.refresh(user)
    return {"detail": "Reembolso solicitado e usuário bloqueado."}


@router.post("/users/{user_id}/asaas-cancel-immediate")
def admin_cancel_asaas_immediately(
    user_id: int,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    subscription = user.subscription
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")
    if (subscription.provider or "").lower() != "asaas":
        raise HTTPException(status_code=400, detail="Operação disponível apenas para assinaturas Asaas.")
    if not subscription.asaas_subscription_id:
        raise HTTPException(status_code=400, detail="ID de assinatura Asaas não encontrado.")

    if not settings.asaas_api_key:
        raise HTTPException(status_code=500, detail="Asaas não configurado no servidor.")
    client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
    sub_id = subscription.asaas_subscription_id
    remote_status_before = ""
    try:
        remote_before = client.get_subscription(sub_id)
        remote_status_before = str((remote_before or {}).get("status") or "").strip().upper()
    except AsaasAPIError:
        remote_status_before = ""

    if remote_status_before not in {"INACTIVE", "CANCELLED", "DELETED"}:
        try:
            client.cancel_subscription(sub_id)
        except AsaasAPIError as exc:  # noqa: BLE001
            delete_detail = _extract_asaas_error_detail(exc)
            update_detail = ""
            get_detail = ""
            try:
                client.update_subscription(sub_id, {"status": "INACTIVE"})
            except AsaasAPIError as upd_exc:  # noqa: BLE001
                update_detail = _extract_asaas_error_detail(upd_exc)

            try:
                remote_after = client.get_subscription(sub_id)
                remote_status_after = str((remote_after or {}).get("status") or "").strip().upper()
            except AsaasAPIError as get_exc:  # noqa: BLE001
                remote_status_after = ""
                get_detail = _extract_asaas_error_detail(get_exc)

            if remote_status_after not in {"INACTIVE", "CANCELLED", "DELETED"}:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"Erro ao cancelar assinatura no Asaas ({sub_id}). "
                        f"delete={delete_detail}; update={update_detail or 'n/a'}; "
                        f"get={get_detail or 'ok'}; status_before={remote_status_before or 'n/a'}; "
                        f"status_after={remote_status_after or 'n/a'}; base_url={settings.asaas_base_url}"
                    ),
                ) from exc

    # Keep account and published pages intact; only subscription becomes inactive.
    subscription.status = "inactive"
    subscription.valid_until = None
    subscription.failed_attempts = 3
    subscription.asaas_subscription_id = None
    subscription.asaas_payment_link_id = None
    subscription.external_reference = None
    subscription.mrr_amount = 0
    user.is_active = True
    db.add_all([user, subscription])
    db.commit()
    try:
        mark_viajechat_cancelled(
            name=user.name or "",
            email=user.email or "",
            phone=user.whatsapp or "",
        )
    except Exception:  # noqa: BLE001
        pass
    return {"detail": "Assinatura cancelada imediatamente e usuário mantido com acesso bloqueado para reativação."}


@router.post("/users/{user_id}/asaas-cancel-at-period-end")
def admin_schedule_asaas_cancel_at_period_end(
    user_id: int,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    subscription = user.subscription
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")
    if (subscription.provider or "").lower() != "asaas":
        raise HTTPException(status_code=400, detail="Operação disponível apenas para assinaturas Asaas.")
    if not subscription.asaas_subscription_id:
        raise HTTPException(status_code=400, detail="ID de assinatura Asaas não encontrado.")
    if not subscription.valid_until:
        raise HTTPException(status_code=400, detail="Não foi possível determinar a validade atual da assinatura.")

    subscription.status = "cancel_at_period_end"
    subscription.external_reference = None
    db.add(subscription)
    db.commit()
    return {"detail": "Cancelamento programado para o fim da validade atual da assinatura."}


@router.post("/users/{user_id}/asaas-cancel-scheduled-cancellation")
def admin_cancel_scheduled_asaas_cancellation(
    user_id: int,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    subscription = user.subscription
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")
    if (subscription.provider or "").lower() != "asaas":
        raise HTTPException(status_code=400, detail="Operação disponível apenas para assinaturas Asaas.")
    if (subscription.status or "").lower() != "cancel_at_period_end":
        raise HTTPException(status_code=400, detail="Não há cancelamento programado para desfazer.")

    subscription.status = "active"
    db.add(subscription)
    db.commit()
    return {"detail": "Cancelamento programado removido com sucesso."}


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

