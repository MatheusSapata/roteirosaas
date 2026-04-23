from __future__ import annotations

from datetime import date, datetime, time as dt_time
from typing import Literal

from pydantic import BaseModel, Field


class ScheduleTemplateWeekdayPayload(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    is_enabled: bool = True


class ScheduleTemplateTimePayload(BaseModel):
    time: str
    capacity_override: int | None = Field(default=None, ge=0)
    price_override: int | None = Field(default=None, ge=0)
    sort_order: int = 0
    is_active: bool = True


class ScheduleTemplateCalendarDateTimePayload(BaseModel):
    time: str
    capacity_override: int | None = Field(default=None, ge=0)
    price_override: int | None = Field(default=None, ge=0)
    is_active: bool = True


class ScheduleTemplateCalendarDatePayload(BaseModel):
    date: date
    is_active: bool = True
    times: list[ScheduleTemplateCalendarDateTimePayload] = Field(default_factory=list)


class ScheduleTemplatePayload(BaseModel):
    template_type: Literal["weekday", "calendar"]
    start_date: date
    end_date: date | None = None
    timezone: str
    default_capacity: int | None = Field(default=None, ge=0)
    default_price: int | None = Field(default=None, ge=0)
    generation_horizon_days: int = Field(default=90, ge=1, le=365)
    is_active: bool = True
    weekdays: list[ScheduleTemplateWeekdayPayload] = Field(default_factory=list)
    times: list[ScheduleTemplateTimePayload] = Field(default_factory=list)
    calendar_dates: list[ScheduleTemplateCalendarDatePayload] = Field(default_factory=list)


class ScheduleTemplateOut(BaseModel):
    id: int
    product_id: int
    template_type: str
    start_date: date
    end_date: date | None = None
    timezone: str
    default_capacity: int | None = None
    default_price: int | None = None
    generation_horizon_days: int
    is_active: bool
    weekdays: list[ScheduleTemplateWeekdayPayload] = Field(default_factory=list)
    times: list[ScheduleTemplateTimePayload] = Field(default_factory=list)
    calendar_dates: list[ScheduleTemplateCalendarDatePayload] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DepartureOut(BaseModel):
    id: int
    product_id: int
    schedule_template_id: int | None = None
    date: date
    time: dt_time
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str
    status: str
    capacity_total: int
    capacity_reserved: int
    capacity_sold: int
    capacity_available: int
    price_override: int | None = None
    is_manual_override: bool
    notes: str | None = None
    source_type: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DepartureListResponse(BaseModel):
    items: list[DepartureOut]


class ScheduleGenerateRequest(BaseModel):
    from_date: date | None = None
    to_date: date | None = None


class ScheduleGenerateResponse(BaseModel):
    generated: int
    updated: int
    total: int


class PublicDepartureCalendarDayOut(BaseModel):
    date: date
    day: int
    available: bool
    departures_count: int
    low_availability: bool = False
    status: str


class PublicDepartureCalendarResponse(BaseModel):
    product_id: int
    month: str
    timezone: str
    days: list[PublicDepartureCalendarDayOut]


class PublicDepartureTimeSlotOut(BaseModel):
    departure_id: int
    time: str
    available: bool
    remaining_capacity: int
    effective_price: int | None = None
    status: str
    label: str
    low_availability: bool


class PublicDepartureTimesResponse(BaseModel):
    product_id: int
    date: date
    timezone: str
    slots: list[PublicDepartureTimeSlotOut]


class PublicDepartureValidateRequest(BaseModel):
    product_id: str
    departure_id: int
    quantity: int = Field(default=1, ge=1)


class PublicDepartureValidateResponse(BaseModel):
    valid: bool
    reason: str | None = None
    final_price: int | None = None
    snapshot: DepartureOut | None = None


class ScheduleExceptionPayload(BaseModel):
    exception_type: Literal[
        "block_date",
        "block_time",
        "cancel_departure",
        "close_departure",
        "capacity_override",
        "price_override",
    ]
    schedule_template_id: int | None = None
    date: date
    time: str | None = None
    new_status: Literal["draft", "active", "full", "closed", "canceled"] | None = None
    capacity_override: int | None = Field(default=None, ge=0)
    price_override: int | None = Field(default=None, ge=0)
    reason: str | None = Field(default=None, max_length=500)


class ScheduleExceptionOut(BaseModel):
    id: int
    product_id: int
    schedule_template_id: int | None = None
    exception_type: str
    date: date
    time: dt_time | None = None
    new_status: str | None = None
    capacity_override: int | None = None
    price_override: int | None = None
    reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScheduleExceptionListResponse(BaseModel):
    items: list[ScheduleExceptionOut]
