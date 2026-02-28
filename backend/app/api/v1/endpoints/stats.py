from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.stats import PageVisitStats
from app.models.user import User
from app.schemas.stats import PageStatsSummaryOut, PageVisitStatsOut, StatsOverviewOut, StatsSeriesItem, StatsTrend

router = APIRouter()


def get_or_create_stats(db: Session, page_id: int, ref_date: date) -> PageVisitStats:
    stats = (
        db.query(PageVisitStats)
        .filter(PageVisitStats.page_id == page_id, PageVisitStats.date == ref_date)
        .first()
    )
    if stats:
        return stats
    stats = PageVisitStats(page_id=page_id, date=ref_date, visits=0, clicks_whatsapp=0, clicks_cta=0)
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


def ensure_agency_member(db: Session, agency_id: int, user_id: int) -> None:
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this agency")


def ensure_published_page(db: Session, page_id: int) -> Page:
    page = db.query(Page).filter(Page.id == page_id, Page.status == "published").first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found or not published")
    return page


@router.post("/{page_id}/track-visit", response_model=PageVisitStatsOut)
def track_visit(page_id: int, db: Session = Depends(get_db)) -> PageVisitStatsOut:
    ensure_published_page(db, page_id)
    stats = get_or_create_stats(db, page_id, date.today())
    stats.visits += 1
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


@router.post("/{page_id}/track-whatsapp-click", response_model=PageVisitStatsOut)
def track_whatsapp_click(page_id: int, db: Session = Depends(get_db)) -> PageVisitStatsOut:
    ensure_published_page(db, page_id)
    stats = get_or_create_stats(db, page_id, date.today())
    stats.clicks_whatsapp += 1
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


@router.post("/{page_id}/track-cta", response_model=PageVisitStatsOut)
def track_cta_click(page_id: int, db: Session = Depends(get_db)) -> PageVisitStatsOut:
    ensure_published_page(db, page_id)
    stats = get_or_create_stats(db, page_id, date.today())
    stats.clicks_cta += 1
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


def summarize(rows: list[PageVisitStats]) -> dict[str, int]:
    visits = sum(row.visits for row in rows)
    whatsapp = sum(row.clicks_whatsapp for row in rows)
    cta = sum(row.clicks_cta for row in rows)
    return {"visits": visits, "whatsapp": whatsapp, "cta": cta}


def percentage_change(current: int, previous: int) -> float | None:
    if previous <= 0:
        return None
    delta = ((current - previous) / previous) * 100
    return round(delta, 1)


@router.get("/overview", response_model=StatsOverviewOut)
def stats_overview(
    agency_id: int = Query(...),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> StatsOverviewOut:
    ensure_agency_member(db, agency_id, current_user.id)
    days = max(1, min(days, 90))
    today = date.today()
    since = today - timedelta(days=days - 1)
    prev_since = since - timedelta(days=days)

    base_query = (
        db.query(PageVisitStats)
        .join(Page, Page.id == PageVisitStats.page_id)
        .filter(Page.agency_id == agency_id, Page.status == "published")
    )

    current_rows = base_query.filter(PageVisitStats.date >= since).all()
    previous_rows = base_query.filter(PageVisitStats.date >= prev_since, PageVisitStats.date < since).all()

    totals = summarize(current_rows)
    prev_totals = summarize(previous_rows)

    series_map: dict[date, dict[str, int]] = defaultdict(lambda: {"visits": 0, "whatsapp": 0, "cta": 0})
    for offset in range(days):
        day = since + timedelta(days=offset)
        _ = series_map[day]  # prime keys
    for row in current_rows:
        if row.date not in series_map:
            series_map[row.date] = {"visits": 0, "whatsapp": 0, "cta": 0}
        series_map[row.date]["visits"] += row.visits
        series_map[row.date]["whatsapp"] += row.clicks_whatsapp
        series_map[row.date]["cta"] += row.clicks_cta

    timeseries = [
        StatsSeriesItem(
            label=day.strftime("%d/%m"),
            visits=data["visits"],
            clicks=data["whatsapp"] + data["cta"],
            conversions=data["cta"],
        )
        for day, data in sorted(series_map.items(), key=lambda item: item[0])
    ]

    trend = StatsTrend(
        pages=None,
        integrations=None,
        visits=percentage_change(totals["visits"], prev_totals["visits"]),
        whatsapp=percentage_change(totals["whatsapp"], prev_totals["whatsapp"]),
    )

    return StatsOverviewOut(
        visits=totals["visits"],
        whatsapp=totals["whatsapp"],
        cta=totals["cta"],
        trend=trend,
        timeseries=timeseries,
    )


@router.get("/pages", response_model=list[PageStatsSummaryOut])
def stats_per_page(
    agency_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[PageStatsSummaryOut]:
    ensure_agency_member(db, agency_id, current_user.id)
    rows = (
        db.query(
            PageVisitStats.page_id,
            func.coalesce(func.sum(PageVisitStats.visits), 0).label("visits"),
            func.coalesce(func.sum(PageVisitStats.clicks_cta), 0).label("clicks_cta"),
            func.coalesce(func.sum(PageVisitStats.clicks_whatsapp), 0).label("clicks_whatsapp"),
        )
        .join(Page, Page.id == PageVisitStats.page_id)
        .filter(Page.agency_id == agency_id)
        .group_by(PageVisitStats.page_id)
        .all()
    )
    return [
        PageStatsSummaryOut(
            page_id=row.page_id,
            visits=row.visits or 0,
            clicks_cta=row.clicks_cta or 0,
            clicks_whatsapp=row.clicks_whatsapp or 0,
        )
        for row in rows
    ]
