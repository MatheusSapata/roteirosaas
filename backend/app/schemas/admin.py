from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict


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
