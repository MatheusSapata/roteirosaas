from datetime import date

from pydantic import BaseModel, ConfigDict


class PageVisitStatsBase(BaseModel):
    page_id: int
    date: date
    visits: int = 0
    clicks_whatsapp: int = 0
    clicks_cta: int = 0


class PageVisitStatsCreate(PageVisitStatsBase):
    pass


class PageVisitStatsOut(PageVisitStatsBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StatsTrend(BaseModel):
    pages: float | None = None
    integrations: float | None = None
    visits: float | None = None
    whatsapp: float | None = None


class StatsSeriesItem(BaseModel):
    label: str
    visits: int
    clicks: int
    conversions: int


class StatsOverviewOut(BaseModel):
    visits: int
    whatsapp: int
    cta: int
    trend: StatsTrend | None = None
    timeseries: list[StatsSeriesItem]


class PageStatsSummaryOut(BaseModel):
    page_id: int
    visits: int
    clicks_cta: int
    clicks_whatsapp: int
