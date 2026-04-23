from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.product import Product, ProductScheduleMode
from app.models.schedule import (
    Departure,
    DepartureSourceType,
    DepartureStatus,
    ScheduleException,
    ScheduleExceptionType,
    ScheduleTemplate,
    ScheduleTemplateCalendarDate,
    ScheduleTemplateCalendarDateTime,
    ScheduleTemplateTime,
    ScheduleTemplateType,
    ScheduleTemplateWeekday,
)
from app.schemas.schedule import (
    DepartureOut,
    PublicDepartureCalendarDayOut,
    PublicDepartureTimeSlotOut,
    ScheduleExceptionOut,
    ScheduleExceptionPayload,
    ScheduleTemplateCalendarDatePayload,
    ScheduleTemplateOut,
    ScheduleTemplatePayload,
    ScheduleTemplateTimePayload,
    ScheduleTemplateWeekdayPayload,
)


SELLABLE_STATUSES = {DepartureStatus.active.value}


def _clean_timezone(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _parse_time(value: str) -> time:
    raw = (value or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Horario invalido.")
    try:
        if len(raw) == 5:
            return datetime.strptime(raw, "%H:%M").time()
        return datetime.strptime(raw, "%H:%M:%S").time()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Horario invalido.") from exc


def _compose_start_datetime(day: date, hour: time, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    return datetime.combine(day, hour).replace(tzinfo=tz)


def _serialize_weekdays(template: ScheduleTemplate) -> list[ScheduleTemplateWeekdayPayload]:
    return [
        ScheduleTemplateWeekdayPayload(weekday=int(entry.weekday), is_enabled=bool(entry.is_enabled))
        for entry in sorted(template.weekdays or [], key=lambda row: row.weekday)
    ]


def _serialize_times(template: ScheduleTemplate) -> list[ScheduleTemplateTimePayload]:
    return [
        ScheduleTemplateTimePayload(
            time=entry.time.strftime("%H:%M"),
            capacity_override=entry.capacity_override,
            price_override=entry.price_override,
            sort_order=entry.sort_order,
            is_active=bool(entry.is_active),
        )
        for entry in sorted(template.times or [], key=lambda row: (row.sort_order, row.time))
    ]


def _serialize_calendar_dates(template: ScheduleTemplate) -> list[ScheduleTemplateCalendarDatePayload]:
    payload: list[ScheduleTemplateCalendarDatePayload] = []
    for calendar_date in sorted(template.calendar_dates or [], key=lambda row: row.date):
        payload.append(
            ScheduleTemplateCalendarDatePayload(
                date=calendar_date.date,
                is_active=bool(calendar_date.is_active),
                times=[
                    {
                        "time": date_time.time.strftime("%H:%M"),
                        "capacity_override": date_time.capacity_override,
                        "price_override": date_time.price_override,
                        "is_active": bool(date_time.is_active),
                    }
                    for date_time in sorted(calendar_date.times or [], key=lambda row: row.time)
                ],
            )
        )
    return payload


def serialize_template(template: ScheduleTemplate) -> ScheduleTemplateOut:
    return ScheduleTemplateOut(
        id=template.id,
        product_id=template.product_id,
        template_type=template.template_type,
        start_date=template.start_date,
        end_date=template.end_date,
        timezone=template.timezone,
        default_capacity=template.default_capacity,
        default_price=template.default_price,
        generation_horizon_days=template.generation_horizon_days,
        is_active=bool(template.is_active),
        weekdays=_serialize_weekdays(template),
        times=_serialize_times(template),
        calendar_dates=_serialize_calendar_dates(template),
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def serialize_departure(departure: Departure) -> DepartureOut:
    return DepartureOut(
        id=departure.id,
        product_id=departure.product_id,
        schedule_template_id=departure.schedule_template_id,
        date=departure.date,
        time=departure.time,
        starts_at=departure.starts_at,
        ends_at=departure.ends_at,
        timezone=departure.timezone,
        status=departure.status,
        capacity_total=int(departure.capacity_total or 0),
        capacity_reserved=int(departure.capacity_reserved or 0),
        capacity_sold=int(departure.capacity_sold or 0),
        capacity_available=departure.capacity_available,
        price_override=departure.price_override,
        is_manual_override=bool(departure.is_manual_override),
        notes=departure.notes,
        source_type=departure.source_type,
        created_at=departure.created_at,
        updated_at=departure.updated_at,
    )


def serialize_exception(exception: ScheduleException) -> ScheduleExceptionOut:
    return ScheduleExceptionOut(
        id=exception.id,
        product_id=exception.product_id,
        schedule_template_id=exception.schedule_template_id,
        exception_type=exception.exception_type,
        date=exception.date,
        time=exception.time,
        new_status=exception.new_status,
        capacity_override=exception.capacity_override,
        price_override=exception.price_override,
        reason=exception.reason,
        created_at=exception.created_at,
        updated_at=exception.updated_at,
    )


def _validate_template_payload(payload: ScheduleTemplatePayload, product: Product) -> None:
    if payload.template_type == ScheduleTemplateType.weekday.value:
        if not payload.weekdays:
            raise HTTPException(status_code=400, detail="Selecione ao menos um dia da semana.")
        if not payload.times:
            raise HTTPException(status_code=400, detail="Adicione ao menos um horario.")
    if payload.template_type == ScheduleTemplateType.calendar.value and not payload.calendar_dates:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma data no calendario.")
    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="Data final invalida.")
    if payload.default_capacity is not None and payload.default_capacity < 0:
        raise HTTPException(status_code=400, detail="Capacidade padrao invalida.")
    if payload.default_price is not None and payload.default_price < 0:
        raise HTTPException(status_code=400, detail="Preco padrao invalido.")
    if product.schedule_mode != ProductScheduleMode.recurring.value:
        raise HTTPException(status_code=400, detail="Template de agenda disponivel apenas para produtos recorrentes.")


def _active_template_query(db: Session, product_id: int):
    return (
        db.query(ScheduleTemplate)
        .filter(
            ScheduleTemplate.product_id == product_id,
            ScheduleTemplate.deleted_at.is_(None),
        )
    )


def list_templates(*, db: Session, product_id: int) -> list[ScheduleTemplate]:
    return _active_template_query(db, product_id).order_by(ScheduleTemplate.created_at.desc()).all()


def create_template(*, db: Session, product: Product, payload: ScheduleTemplatePayload) -> ScheduleTemplate:
    _validate_template_payload(payload, product)
    template = ScheduleTemplate(
        product_id=product.id,
        template_type=payload.template_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        timezone=payload.timezone,
        default_capacity=payload.default_capacity,
        default_price=payload.default_price,
        generation_horizon_days=payload.generation_horizon_days,
        is_active=payload.is_active,
    )
    db.add(template)
    db.flush()
    _replace_template_relations(template, payload)
    db.commit()
    db.refresh(template)
    return template


def update_template(*, db: Session, template: ScheduleTemplate, payload: ScheduleTemplatePayload, product: Product) -> ScheduleTemplate:
    _validate_template_payload(payload, product)
    template.template_type = payload.template_type
    template.start_date = payload.start_date
    template.end_date = payload.end_date
    template.timezone = payload.timezone
    template.default_capacity = payload.default_capacity
    template.default_price = payload.default_price
    template.generation_horizon_days = payload.generation_horizon_days
    template.is_active = payload.is_active
    _replace_template_relations(template, payload)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def soft_delete_template(*, db: Session, template: ScheduleTemplate) -> None:
    template.deleted_at = datetime.utcnow()
    db.add(template)
    db.commit()


def _replace_template_relations(template: ScheduleTemplate, payload: ScheduleTemplatePayload) -> None:
    template.weekdays = []
    template.times = []
    template.calendar_dates = []

    if payload.template_type == ScheduleTemplateType.weekday.value:
        for entry in payload.weekdays:
            template.weekdays.append(
                ScheduleTemplateWeekday(
                    weekday=int(entry.weekday),
                    is_enabled=bool(entry.is_enabled),
                )
            )
        for entry in payload.times:
            template.times.append(
                ScheduleTemplateTime(
                    time=_parse_time(entry.time),
                    capacity_override=entry.capacity_override,
                    price_override=entry.price_override,
                    sort_order=entry.sort_order,
                    is_active=entry.is_active,
                )
            )
        return

    for date_payload in payload.calendar_dates:
        calendar_date_model = ScheduleTemplateCalendarDate(
            date=date_payload.date,
            is_active=date_payload.is_active,
        )
        for time_payload in date_payload.times:
            calendar_date_model.times.append(
                ScheduleTemplateCalendarDateTime(
                    time=_parse_time(time_payload.time),
                    capacity_override=time_payload.capacity_override,
                    price_override=time_payload.price_override,
                    is_active=time_payload.is_active,
                )
            )
        template.calendar_dates.append(calendar_date_model)


def _active_exceptions(db: Session, *, product_id: int, from_date: date, to_date: date) -> list[ScheduleException]:
    return (
        db.query(ScheduleException)
        .filter(
            ScheduleException.product_id == product_id,
            ScheduleException.deleted_at.is_(None),
            ScheduleException.date >= from_date,
            ScheduleException.date <= to_date,
        )
        .all()
    )


def list_exceptions(*, db: Session, product_id: int) -> list[ScheduleException]:
    return (
        db.query(ScheduleException)
        .filter(
            ScheduleException.product_id == product_id,
            ScheduleException.deleted_at.is_(None),
        )
        .order_by(ScheduleException.date.asc(), ScheduleException.time.asc().nullsfirst())
        .all()
    )


def create_exception(*, db: Session, product: Product, payload: ScheduleExceptionPayload) -> ScheduleException:
    if product.schedule_mode != ProductScheduleMode.recurring.value:
        raise HTTPException(status_code=400, detail="Excecoes disponiveis apenas para produtos recorrentes.")
    exception = ScheduleException(
        product_id=product.id,
        schedule_template_id=payload.schedule_template_id,
        exception_type=payload.exception_type,
        date=payload.date,
        time=_parse_time(payload.time) if payload.time else None,
        new_status=payload.new_status,
        capacity_override=payload.capacity_override,
        price_override=payload.price_override,
        reason=payload.reason,
    )
    db.add(exception)
    db.commit()
    db.refresh(exception)
    return exception


def update_exception(*, db: Session, exception: ScheduleException, payload: ScheduleExceptionPayload) -> ScheduleException:
    exception.schedule_template_id = payload.schedule_template_id
    exception.exception_type = payload.exception_type
    exception.date = payload.date
    exception.time = _parse_time(payload.time) if payload.time else None
    exception.new_status = payload.new_status
    exception.capacity_override = payload.capacity_override
    exception.price_override = payload.price_override
    exception.reason = payload.reason
    db.add(exception)
    db.commit()
    db.refresh(exception)
    return exception


def soft_delete_exception(*, db: Session, exception: ScheduleException) -> None:
    exception.deleted_at = datetime.utcnow()
    db.add(exception)
    db.commit()


def soft_delete_departure(*, db: Session, departure: Departure) -> None:
    departure.deleted_at = datetime.utcnow()
    db.add(departure)
    db.commit()


@dataclass
class GenerationResult:
    generated: int = 0
    updated: int = 0
    total: int = 0


class ScheduleGenerationService:
    @staticmethod
    def generate_for_product(
        *,
        db: Session,
        product: Product,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> GenerationResult:
        if product.schedule_mode != ProductScheduleMode.recurring.value:
            return GenerationResult()
        timezone = _clean_timezone(product.timezone)
        if not timezone:
            raise HTTPException(status_code=400, detail="Timezone e obrigatorio para produtos recorrentes.")

        templates = (
            db.query(ScheduleTemplate)
            .filter(
                ScheduleTemplate.product_id == product.id,
                ScheduleTemplate.deleted_at.is_(None),
                ScheduleTemplate.is_active.is_(True),
            )
            .all()
        )
        if not templates:
            return GenerationResult()

        today = date.today()
        start = from_date or today
        if to_date:
            end = to_date
        else:
            horizon = max(int(max((template.generation_horizon_days or 90) for template in templates)), 1)
            end = start + timedelta(days=horizon)
        if end < start:
            raise HTTPException(status_code=400, detail="Intervalo de geracao invalido.")

        existing = (
            db.query(Departure)
            .filter(
                Departure.product_id == product.id,
                Departure.deleted_at.is_(None),
                Departure.date >= start,
                Departure.date <= end,
            )
            .all()
        )
        by_slot: dict[tuple[int | None, date, time], Departure] = {
            (entry.schedule_template_id, entry.date, entry.time): entry for entry in existing
        }
        exceptions = _active_exceptions(db, product_id=product.id, from_date=start, to_date=end)
        result = GenerationResult()

        for template in templates:
            slots = ScheduleGenerationService._build_slots(template=template, start=start, end=end)
            for slot_date, slot_time, cap_override, price_override in slots:
                resolved = ScheduleGenerationService._resolve_with_exceptions(
                    slot_date=slot_date,
                    slot_time=slot_time,
                    base_capacity=cap_override if cap_override is not None else template.default_capacity,
                    base_price=price_override if price_override is not None else template.default_price,
                    exceptions=exceptions,
                )
                if not resolved["allowed"]:
                    continue
                capacity_total = int(resolved["capacity"] or 0)
                if capacity_total <= 0:
                    continue
                status = resolved["status"] or DepartureStatus.active.value
                key = (template.id, slot_date, slot_time)
                departure = by_slot.get(key)
                starts_at = _compose_start_datetime(slot_date, slot_time, timezone)
                if departure:
                    result.updated += 1
                else:
                    departure = Departure(
                        product_id=product.id,
                        schedule_template_id=template.id,
                        date=slot_date,
                        time=slot_time,
                        starts_at=starts_at,
                        timezone=timezone,
                        source_type=DepartureSourceType.template.value,
                    )
                    db.add(departure)
                    by_slot[key] = departure
                    result.generated += 1
                departure.schedule_template_id = template.id
                departure.starts_at = starts_at
                departure.timezone = timezone
                departure.status = status
                departure.capacity_total = capacity_total
                departure.price_override = resolved["price"]
                departure.source_type = DepartureSourceType.template.value

        db.commit()
        result.total = result.generated + result.updated
        return result

    @staticmethod
    def _build_slots(
        *,
        template: ScheduleTemplate,
        start: date,
        end: date,
    ) -> list[tuple[date, time, int | None, int | None]]:
        slots: list[tuple[date, time, int | None, int | None]] = []
        start_window = max(start, template.start_date)
        end_window = min(end, template.end_date) if template.end_date else end
        if end_window < start_window:
            return slots

        if template.template_type == ScheduleTemplateType.weekday.value:
            enabled = {int(entry.weekday) for entry in (template.weekdays or []) if entry.is_enabled}
            times = [entry for entry in (template.times or []) if entry.is_active]
            if not enabled or not times:
                return slots
            cursor = start_window
            while cursor <= end_window:
                if cursor.weekday() in enabled:
                    for time_entry in sorted(times, key=lambda row: (row.sort_order, row.time)):
                        slots.append((cursor, time_entry.time, time_entry.capacity_override, time_entry.price_override))
                cursor += timedelta(days=1)
            return slots

        for calendar_date in sorted(template.calendar_dates or [], key=lambda row: row.date):
            if not calendar_date.is_active:
                continue
            if calendar_date.date < start_window or calendar_date.date > end_window:
                continue
            for date_time in sorted(calendar_date.times or [], key=lambda row: row.time):
                if not date_time.is_active:
                    continue
                slots.append((calendar_date.date, date_time.time, date_time.capacity_override, date_time.price_override))
        return slots

    @staticmethod
    def _resolve_with_exceptions(
        *,
        slot_date: date,
        slot_time: time,
        base_capacity: int | None,
        base_price: int | None,
        exceptions: list[ScheduleException],
    ) -> dict[str, object]:
        allowed = True
        status: str | None = DepartureStatus.active.value
        capacity = base_capacity
        price = base_price
        for exception in exceptions:
            if exception.date != slot_date:
                continue
            if exception.time and exception.time != slot_time:
                continue
            if exception.exception_type in {
                ScheduleExceptionType.block_date.value,
                ScheduleExceptionType.block_time.value,
                ScheduleExceptionType.cancel_departure.value,
            }:
                allowed = False
                break
            if exception.exception_type == ScheduleExceptionType.close_departure.value:
                status = DepartureStatus.closed.value
            if exception.exception_type == ScheduleExceptionType.capacity_override.value and exception.capacity_override is not None:
                capacity = int(exception.capacity_override)
            if exception.exception_type == ScheduleExceptionType.price_override.value and exception.price_override is not None:
                price = int(exception.price_override)
        return {"allowed": allowed, "status": status, "capacity": capacity, "price": price}


class DepartureAvailabilityService:
    @staticmethod
    def list_departures_for_date(*, db: Session, product_id: int, target_date: date) -> list[Departure]:
        return (
            db.query(Departure)
            .filter(
                Departure.product_id == product_id,
                Departure.deleted_at.is_(None),
                Departure.date == target_date,
            )
            .order_by(Departure.time.asc())
            .all()
        )

    @staticmethod
    def list_departures_in_range(*, db: Session, product_id: int, from_date: date, to_date: date) -> list[Departure]:
        return (
            db.query(Departure)
            .filter(
                Departure.product_id == product_id,
                Departure.deleted_at.is_(None),
                Departure.date >= from_date,
                Departure.date <= to_date,
            )
            .order_by(Departure.date.asc(), Departure.time.asc())
            .all()
        )

    @staticmethod
    def build_calendar(
        *,
        db: Session,
        product_id: int,
        month_start: date,
        month_end: date,
    ) -> list[PublicDepartureCalendarDayOut]:
        departures = DepartureAvailabilityService.list_departures_in_range(
            db=db,
            product_id=product_id,
            from_date=month_start,
            to_date=month_end,
        )
        buckets: dict[date, list[Departure]] = {}
        for departure in departures:
            buckets.setdefault(departure.date, []).append(departure)
        days: list[PublicDepartureCalendarDayOut] = []
        for day, entries in sorted(buckets.items(), key=lambda item: item[0]):
            sellable = [entry for entry in entries if entry.status in SELLABLE_STATUSES and entry.capacity_available > 0]
            remaining = sum(entry.capacity_available for entry in sellable)
            days.append(
                PublicDepartureCalendarDayOut(
                    date=day,
                    day=day.day,
                    available=bool(sellable),
                    departures_count=len(entries),
                    low_availability=remaining > 0 and remaining <= 5,
                    status=DepartureStatus.active.value if sellable else (entries[0].status if entries else DepartureStatus.closed.value),
                )
            )
        return days

    @staticmethod
    def build_time_slots(*, departures: list[Departure]) -> list[PublicDepartureTimeSlotOut]:
        slots: list[PublicDepartureTimeSlotOut] = []
        for departure in departures:
            available = departure.status in SELLABLE_STATUSES and departure.capacity_available > 0
            slots.append(
                PublicDepartureTimeSlotOut(
                    departure_id=departure.id,
                    time=departure.time.strftime("%H:%M"),
                    available=available,
                    remaining_capacity=departure.capacity_available,
                    effective_price=departure.price_override,
                    status=departure.status,
                    label=f"{departure.time.strftime('%H:%M')} ({departure.capacity_available} vagas)",
                    low_availability=available and departure.capacity_available <= 5,
                )
            )
        return slots


class DepartureCapacityService:
    @staticmethod
    def validate_sellable(*, departure: Departure, requested_units: int) -> None:
        units = max(int(requested_units or 0), 1)
        if departure.status != DepartureStatus.active.value:
            raise HTTPException(status_code=400, detail="Saida indisponivel para venda.")
        if departure.capacity_available < units:
            raise HTTPException(status_code=400, detail="Sem capacidade disponivel para esta saida.")

    @staticmethod
    def reserve(*, departure: Departure, units: int) -> None:
        units = max(int(units or 0), 0)
        if units <= 0:
            return
        DepartureCapacityService.validate_sellable(departure=departure, requested_units=units)
        departure.capacity_reserved = max(int(departure.capacity_reserved or 0) + units, 0)
        if departure.capacity_available <= 0 and departure.status == DepartureStatus.active.value:
            departure.status = DepartureStatus.full.value

    @staticmethod
    def confirm(*, departure: Departure, units: int) -> None:
        units = max(int(units or 0), 0)
        if units <= 0:
            return
        departure.capacity_reserved = max(int(departure.capacity_reserved or 0) - units, 0)
        departure.capacity_sold = max(int(departure.capacity_sold or 0) + units, 0)
        if departure.capacity_available <= 0 and departure.status == DepartureStatus.active.value:
            departure.status = DepartureStatus.full.value
        elif departure.status == DepartureStatus.full.value and departure.capacity_available > 0:
            departure.status = DepartureStatus.active.value

    @staticmethod
    def release_reserved(*, departure: Departure, units: int) -> None:
        units = max(int(units or 0), 0)
        if units <= 0:
            return
        departure.capacity_reserved = max(int(departure.capacity_reserved or 0) - units, 0)
        if departure.status == DepartureStatus.full.value and departure.capacity_available > 0:
            departure.status = DepartureStatus.active.value


class DeparturePricingService:
    @staticmethod
    def resolve_price(*, default_price: int, departure: Departure | None = None) -> int:
        if departure and departure.price_override is not None:
            return int(departure.price_override)
        return int(default_price)


class DepartureBookingService:
    @staticmethod
    def lock_for_booking(db: Session, *, departure_id: int, product_id: int | None = None) -> Departure:
        query = db.query(Departure).filter(Departure.id == departure_id, Departure.deleted_at.is_(None)).with_for_update(of=Departure)
        if product_id is not None:
            query = query.filter(Departure.product_id == product_id)
        departure = query.first()
        if not departure:
            raise HTTPException(status_code=404, detail="Saida nao encontrada.")
        return departure
