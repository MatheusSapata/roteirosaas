from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class AdminUserPage(BaseModel):
    id: int
    title: str
    slug: str
    status: str
    agency_slug: Optional[str] = None
    total_visits: int = 0
    total_cta_clicks: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminUserTracking(BaseModel):
    id: int
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    referrer: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    plan: str
    is_superuser: bool
    created_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    trial_plan: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    agency_id: Optional[int] = None
    agency_name: Optional[str] = None
    agency_slug: Optional[str] = None
    active_pages: Optional[int] = None
    whatsapp: Optional[str] = None
    published_pages: List[AdminUserPage] = Field(default_factory=list)
    draft_pages: List[AdminUserPage] = Field(default_factory=list)
    draft_pages_count: Optional[int] = None
    tracking: List[AdminUserTracking] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdminAgencyOut(BaseModel):
    id: int
    name: str
    slug: str
    pages_count: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminPageOut(BaseModel):
    id: int
    title: str
    status: str
    agency_name: str
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TimeseriesPoint(BaseModel):
    label: str
    value: int


class PlanCount(BaseModel):
    plan: str
    count: int


class AdminOnlineSession(BaseModel):
    session_id: str
    user_id: int
    user_name: str
    user_email: EmailStr
    user_plan: str
    ip_address: Optional[str] = None
    device_label: Optional[str] = None
    client_name: Optional[str] = None
    created_at: datetime
    last_seen_at: datetime
    active_sessions: int = 1
    last_path: Optional[str] = None


class AdminOnlineSessionsResponse(BaseModel):
    sessions: List[AdminOnlineSession]
    total_online: int
    unique_users: int
    generated_at: datetime


class AdminMetricsOut(BaseModel):
    total_users: int
    total_agencies: int
    total_pages: int
    published_pages: int
    total_revenue: float = 0.0
    plans: List[PlanCount]
    users: List[AdminUserOut]
    agencies: List[AdminAgencyOut]
    pages: List[AdminPageOut]
    new_users_last_days: int
    new_users_timeseries: List[TimeseriesPoint]
    mrr: float
