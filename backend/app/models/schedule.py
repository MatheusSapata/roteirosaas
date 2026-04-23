from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DepartureStatus(str, Enum):  # type: ignore[misc]
    draft = "draft"
    active = "active"
    full = "full"
    closed = "closed"
    canceled = "canceled"


class DepartureSourceType(str, Enum):  # type: ignore[misc]
    template = "template"
    manual = "manual"
    exception = "exception"


class ScheduleTemplateType(str, Enum):  # type: ignore[misc]
    weekday = "weekday"
    calendar = "calendar"


class ScheduleExceptionType(str, Enum):  # type: ignore[misc]
    block_date = "block_date"
    block_time = "block_time"
    cancel_departure = "cancel_departure"
    close_departure = "close_departure"
    capacity_override = "capacity_override"
    price_override = "price_override"


class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    template_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    timezone = Column(String(64), nullable=False)
    default_capacity = Column(Integer, nullable=True)
    default_price = Column(Integer, nullable=True)
    generation_horizon_days = Column(Integer, nullable=False, default=90)
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="schedule_templates")
    weekdays = relationship("ScheduleTemplateWeekday", back_populates="schedule_template", cascade="all, delete-orphan")
    times = relationship("ScheduleTemplateTime", back_populates="schedule_template", cascade="all, delete-orphan")
    calendar_dates = relationship(
        "ScheduleTemplateCalendarDate",
        back_populates="schedule_template",
        cascade="all, delete-orphan",
    )
    departures = relationship("Departure", back_populates="schedule_template")


class ScheduleTemplateWeekday(Base):
    __tablename__ = "schedule_template_weekdays"
    __table_args__ = (UniqueConstraint("schedule_template_id", "weekday", name="uq_schedule_template_weekday"),)

    id = Column(Integer, primary_key=True, index=True)
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)

    schedule_template = relationship("ScheduleTemplate", back_populates="weekdays")


class ScheduleTemplateTime(Base):
    __tablename__ = "schedule_template_times"
    __table_args__ = (UniqueConstraint("schedule_template_id", "time", name="uq_schedule_template_time"),)

    id = Column(Integer, primary_key=True, index=True)
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    time = Column(Time, nullable=False)
    capacity_override = Column(Integer, nullable=True)
    price_override = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    schedule_template = relationship("ScheduleTemplate", back_populates="times")


class ScheduleTemplateCalendarDate(Base):
    __tablename__ = "schedule_template_calendar_dates"
    __table_args__ = (UniqueConstraint("schedule_template_id", "date", name="uq_schedule_template_calendar_date"),)

    id = Column(Integer, primary_key=True, index=True)
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    schedule_template = relationship("ScheduleTemplate", back_populates="calendar_dates")
    times = relationship(
        "ScheduleTemplateCalendarDateTime",
        back_populates="calendar_date",
        cascade="all, delete-orphan",
    )


class ScheduleTemplateCalendarDateTime(Base):
    __tablename__ = "schedule_template_calendar_date_times"
    __table_args__ = (UniqueConstraint("calendar_date_id", "time", name="uq_schedule_template_calendar_date_time"),)

    id = Column(Integer, primary_key=True, index=True)
    calendar_date_id = Column(Integer, ForeignKey("schedule_template_calendar_dates.id", ondelete="CASCADE"), nullable=False, index=True)
    time = Column(Time, nullable=False)
    capacity_override = Column(Integer, nullable=True)
    price_override = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    calendar_date = relationship("ScheduleTemplateCalendarDate", back_populates="times")


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    exception_type = Column(String(40), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)
    new_status = Column(String(20), nullable=True)
    capacity_override = Column(Integer, nullable=True)
    price_override = Column(Integer, nullable=True)
    reason = Column(String(500), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="schedule_exceptions")
    schedule_template = relationship("ScheduleTemplate")


class Departure(Base):
    __tablename__ = "departures"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default=DepartureStatus.draft.value)
    capacity_total = Column(Integer, nullable=False)
    capacity_reserved = Column(Integer, nullable=False, default=0)
    capacity_sold = Column(Integer, nullable=False, default=0)
    price_override = Column(Integer, nullable=True)
    is_manual_override = Column(Boolean, nullable=False, default=False)
    notes = Column(String(500), nullable=True)
    source_type = Column(String(30), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="departures")
    schedule_template = relationship("ScheduleTemplate", back_populates="departures")
    sale_items = relationship("SaleItem", back_populates="departure")

    @property
    def capacity_available(self) -> int:
        available = int(self.capacity_total or 0) - int(self.capacity_reserved or 0) - int(self.capacity_sold or 0)
        return max(available, 0)

