from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class AdminUserPage(BaseModel):
    id: int
    title: str
    slug: str
    status: str
    agency_slug: Optional[str] = None

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


class AdminMetricsOut(BaseModel):
    total_users: int
    total_agencies: int
    total_pages: int
    published_pages: int
    plans: List[PlanCount]
    users: List[AdminUserOut]
    agencies: List[AdminAgencyOut]
    pages: List[AdminPageOut]
    new_users_last_days: int
    new_users_timeseries: List[TimeseriesPoint]
    mrr: float
