from __future__ import annotations

from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.product import ProductScheduleMode
from app.models.schedule import Departure, ScheduleException, ScheduleTemplate
from app.models.user import User
from app.schemas.schedule import (
    DepartureListResponse,
    PublicDepartureCalendarResponse,
    PublicDepartureTimesResponse,
    PublicDepartureValidateRequest,
    PublicDepartureValidateResponse,
    ScheduleExceptionListResponse,
    ScheduleExceptionOut,
    ScheduleExceptionPayload,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
    ScheduleTemplateOut,
    ScheduleTemplatePayload,
)
from app.services.departures import (
    DepartureAvailabilityService,
    DepartureBookingService,
    DepartureCapacityService,
    DeparturePricingService,
    ScheduleGenerationService,
    create_exception,
    create_template,
    list_exceptions,
    list_templates,
    serialize_departure,
    serialize_exception,
    serialize_template,
    soft_delete_departure,
    soft_delete_exception,
    soft_delete_template,
    update_exception,
    update_template,
)
from app.services.products import get_product_by_public_id, get_public_product

router = APIRouter()


def _template_or_404(*, db: Session, product_id: int, template_id: int) -> ScheduleTemplate:
    template = (
        db.query(ScheduleTemplate)
        .filter(
            ScheduleTemplate.id == template_id,
            ScheduleTemplate.product_id == product_id,
            ScheduleTemplate.deleted_at.is_(None),
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template nao encontrado.")
    return template


def _exception_or_404(*, db: Session, product_id: int, exception_id: int) -> ScheduleException:
    record = (
        db.query(ScheduleException)
        .filter(
            ScheduleException.id == exception_id,
            ScheduleException.product_id == product_id,
            ScheduleException.deleted_at.is_(None),
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Excecao nao encontrada.")
    return record


def _departure_or_404(*, db: Session, product_id: int, departure_id: int) -> Departure:
    departure = (
        db.query(Departure)
        .filter(
            Departure.id == departure_id,
            Departure.product_id == product_id,
            Departure.deleted_at.is_(None),
        )
        .first()
    )
    if not departure:
        raise HTTPException(status_code=404, detail="Saida nao encontrada.")
    return departure


@router.get("/products/{public_id}/schedule/templates", response_model=list[ScheduleTemplateOut])
def list_schedule_templates(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ScheduleTemplateOut]:
    product = get_product_by_public_id(public_id, current_user, db)
    templates = list_templates(db=db, product_id=product.id)
    return [serialize_template(template) for template in templates]


@router.post("/products/{public_id}/schedule/templates", response_model=ScheduleTemplateOut)
def create_schedule_template(
    public_id: str,
    payload: ScheduleTemplatePayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScheduleTemplateOut:
    product = get_product_by_public_id(public_id, current_user, db)
    template = create_template(db=db, product=product, payload=payload)
    return serialize_template(template)


@router.put("/products/{public_id}/schedule/templates/{template_id}", response_model=ScheduleTemplateOut)
def update_schedule_template(
    public_id: str,
    template_id: int,
    payload: ScheduleTemplatePayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScheduleTemplateOut:
    product = get_product_by_public_id(public_id, current_user, db)
    template = _template_or_404(db=db, product_id=product.id, template_id=template_id)
    updated = update_template(db=db, template=template, payload=payload, product=product)
    return serialize_template(updated)


@router.delete("/products/{public_id}/schedule/templates/{template_id}", status_code=204)
def delete_schedule_template(
    public_id: str,
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    product = get_product_by_public_id(public_id, current_user, db)
    template = _template_or_404(db=db, product_id=product.id, template_id=template_id)
    soft_delete_template(db=db, template=template)
    return Response(status_code=204)


@router.post("/products/{public_id}/schedule/generate", response_model=ScheduleGenerateResponse)
def generate_schedule_departures(
    public_id: str,
    payload: ScheduleGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScheduleGenerateResponse:
    product = get_product_by_public_id(public_id, current_user, db)
    result = ScheduleGenerationService.generate_for_product(
        db=db,
        product=product,
        from_date=payload.from_date,
        to_date=payload.to_date,
    )
    return ScheduleGenerateResponse(generated=result.generated, updated=result.updated, total=result.total)


@router.get("/products/{public_id}/schedule/departures", response_model=DepartureListResponse)
def list_product_departures(
    public_id: str,
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DepartureListResponse:
    product = get_product_by_public_id(public_id, current_user, db)
    departures = DepartureAvailabilityService.list_departures_in_range(
        db=db,
        product_id=product.id,
        from_date=from_date,
        to_date=to_date,
    )
    return DepartureListResponse(items=[serialize_departure(departure) for departure in departures])


@router.delete("/products/{public_id}/schedule/departures/{departure_id}", status_code=204)
def delete_product_departure(
    public_id: str,
    departure_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    product = get_product_by_public_id(public_id, current_user, db)
    departure = _departure_or_404(db=db, product_id=product.id, departure_id=departure_id)
    soft_delete_departure(db=db, departure=departure)
    return Response(status_code=204)


@router.get("/products/{public_id}/schedule/exceptions", response_model=ScheduleExceptionListResponse)
def list_schedule_exceptions(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScheduleExceptionListResponse:
    product = get_product_by_public_id(public_id, current_user, db)
    items = list_exceptions(db=db, product_id=product.id)
    return ScheduleExceptionListResponse(items=[serialize_exception(item) for item in items])


@router.post("/products/{public_id}/schedule/exceptions", response_model=ScheduleExceptionOut)
def create_schedule_exception(
    public_id: str,
    payload: ScheduleExceptionPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScheduleExceptionOut:
    product = get_product_by_public_id(public_id, current_user, db)
    record = create_exception(db=db, product=product, payload=payload)
    return serialize_exception(record)


@router.put("/products/{public_id}/schedule/exceptions/{exception_id}", response_model=ScheduleExceptionOut)
def update_schedule_exception(
    public_id: str,
    exception_id: int,
    payload: ScheduleExceptionPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ScheduleExceptionOut:
    product = get_product_by_public_id(public_id, current_user, db)
    record = _exception_or_404(db=db, product_id=product.id, exception_id=exception_id)
    updated = update_exception(db=db, exception=record, payload=payload)
    return serialize_exception(updated)


@router.delete("/products/{public_id}/schedule/exceptions/{exception_id}", status_code=204)
def delete_schedule_exception(
    public_id: str,
    exception_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    product = get_product_by_public_id(public_id, current_user, db)
    record = _exception_or_404(db=db, product_id=product.id, exception_id=exception_id)
    soft_delete_exception(db=db, exception=record)
    return Response(status_code=204)


@router.get("/products/{public_id}/schedule/calendar", response_model=PublicDepartureCalendarResponse)
def get_public_departure_calendar(
    public_id: str,
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> PublicDepartureCalendarResponse:
    product = get_public_product(public_id, db)
    if product.schedule_mode != ProductScheduleMode.recurring.value:
        raise HTTPException(status_code=400, detail="Produto nao utiliza agenda recorrente.")
    year, month_number = month.split("-")
    year_int = int(year)
    month_int = int(month_number)
    start = date(year_int, month_int, 1)
    end = date(year_int, month_int, monthrange(year_int, month_int)[1])
    days = DepartureAvailabilityService.build_calendar(
        db=db,
        product_id=product.id,
        month_start=start,
        month_end=end,
    )
    return PublicDepartureCalendarResponse(
        product_id=product.id,
        month=month,
        timezone=product.timezone or "",
        days=days,
    )


@router.get("/products/{public_id}/schedule/times", response_model=PublicDepartureTimesResponse)
def get_public_departure_times(
    public_id: str,
    target_date: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
) -> PublicDepartureTimesResponse:
    product = get_public_product(public_id, db)
    if product.schedule_mode != ProductScheduleMode.recurring.value:
        raise HTTPException(status_code=400, detail="Produto nao utiliza agenda recorrente.")
    departures = DepartureAvailabilityService.list_departures_for_date(
        db=db,
        product_id=product.id,
        target_date=target_date,
    )
    return PublicDepartureTimesResponse(
        product_id=product.id,
        date=target_date,
        timezone=product.timezone or "",
        slots=DepartureAvailabilityService.build_time_slots(departures=departures),
    )


@router.post("/products/{public_id}/schedule/validate", response_model=PublicDepartureValidateResponse)
def validate_public_departure(
    public_id: str,
    payload: PublicDepartureValidateRequest,
    db: Session = Depends(get_db),
) -> PublicDepartureValidateResponse:
    product = get_public_product(public_id, db)
    if payload.product_id != public_id:
        raise HTTPException(status_code=400, detail="Produto da validacao invalido.")
    departure = DepartureBookingService.lock_for_booking(db, departure_id=payload.departure_id, product_id=product.id)
    try:
        DepartureCapacityService.validate_sellable(departure=departure, requested_units=payload.quantity)
    except HTTPException as exc:
        return PublicDepartureValidateResponse(valid=False, reason=exc.detail, final_price=None, snapshot=serialize_departure(departure))
    base_price = 0
    if product.variations:
        first_active = next((variation for variation in product.variations if variation.status == "active"), product.variations[0])
        base_price = int(first_active.price_cents or 0)
    final_price = DeparturePricingService.resolve_price(default_price=base_price, departure=departure)
    return PublicDepartureValidateResponse(
        valid=True,
        reason=None,
        final_price=final_price,
        snapshot=serialize_departure(departure),
    )
