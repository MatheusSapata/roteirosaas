from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Sequence

from fastapi import HTTPException
from sqlalchemy import or_, func, case
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    LegalContract,
    LegalContractSignatureStatus,
    Product,
    ProductScheduleMode,
    Sale,
    SaleItem,
    SalePassenger,
    SalePassengerStatus,
    SalePaymentStatus,
    Departure,
    PassengerGroup,
    SeatAssignment,
    SeatAssignmentActor,
    SeatAssignmentStatus,
    SeatChangeActorRole,
    SeatChangeLog,
    TripSeat,
    TripDepartureInstance,
    TripTransportConfig,
    TripVehicle,
    TripVehicleStatus,
    Vehicle,
    VehicleLayout,
    PassengerType,
)
from app.schemas.transport import (
    PassengerSeatSummary,
    SaleSeatSelectionProduct,
    SaleSeatSelectionProductsResponse,
    SeatAdminAssignmentPayload,
    SeatAssignmentPayload,
    SeatBlockPayload,
    SeatHistoryEntry,
    SeatHistoryResponse,
    SeatMapContext,
    SeatMapStats,
    SeatPostSignatureStatus,
    SeatSelectionContext,
    TripSeatOut,
    TripTransportConfigOut,
    TripTransportConfigPayload,
    TripVehicleOut,
    TripVehiclePayload,
    VehicleDeckSchema,
    VehicleDeckSummary,
    VehicleLayoutDetail,
    VehicleLayoutListResponse,
    VehicleLayoutPayload,
    VehicleLayoutSchema,
    VehicleLayoutSummary,
    VehicleListResponse,
    VehicleOut,
    VehiclePayload,
)
from app.services.agency_integrations import get_user_default_agency_id
from app.models.user import User
from app.schemas.transport import VehicleLayoutSchema as LayoutSchemaModel


SelectableSeatTypes = {"seat", "preferential"}


@dataclass
class _SeatMetrics:
    seat_count: int
    row_count: int
    column_count: int
    deck_mode: str
    deck_summaries: list[VehicleDeckSummary]


def _layout_schema_checksum(schema: dict) -> str:
    normalized = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _resolve_decks(schema: VehicleLayoutSchema) -> list[VehicleDeckSchema]:
    if schema.decks:
        return schema.decks
    if schema.rows is None or schema.cols is None:
        raise HTTPException(status_code=400, detail="Layout sem configuracao de grid.")
    return [
        VehicleDeckSchema(
            key="andar_unico",
            label="Andar unico",
            rows=schema.rows,
            cols=schema.cols,
            cells=schema.cells,
        )
    ]


def _compute_layout_metrics(schema: VehicleLayoutSchema) -> _SeatMetrics:
    decks = _resolve_decks(schema)
    deck_summaries: list[VehicleDeckSummary] = []
    seat_count = 0
    for deck in decks:
        deck_seat_count = sum(1 for cell in deck.cells if cell.type in SelectableSeatTypes)
        seat_count += deck_seat_count
        deck_summaries.append(
            VehicleDeckSummary(
                key=deck.key,
                label=deck.label,
                seat_count=deck_seat_count,
                rows=deck.rows,
                cols=deck.cols,
            )
        )
    row_count = max((deck.rows for deck in decks), default=0)
    column_count = max((deck.cols for deck in decks), default=0)
    deck_mode = "double" if len(decks) > 1 else "single"
    return _SeatMetrics(
        seat_count=seat_count,
        row_count=row_count,
        column_count=column_count,
        deck_mode=deck_mode,
        deck_summaries=deck_summaries,
    )


def _is_segmented_seat_map(product: Product, config: TripTransportConfig) -> bool:
    return (
        config.is_road_trip
        and product.schedule_mode == ProductScheduleMode.recurring.value
    )


def _departure_for_product(product_id: int, departure_id: int, db: Session) -> Departure:
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
        raise HTTPException(status_code=404, detail="Saida nao encontrada para este produto.")
    return departure


def _ensure_departure_instance(product: Product, departure: Departure, db: Session) -> TripDepartureInstance:
    instance = (
        db.query(TripDepartureInstance)
        .filter(
            TripDepartureInstance.product_id == product.id,
            TripDepartureInstance.departure_id == departure.id,
        )
        .first()
    )
    if instance:
        if instance.travel_date != departure.date or instance.departure_time != departure.time:
            instance.travel_date = departure.date
            instance.departure_time = departure.time
            db.add(instance)
            db.flush()
        return instance
    instance = TripDepartureInstance(
        product_id=product.id,
        departure_id=departure.id,
        travel_date=departure.date,
        departure_time=departure.time,
    )
    db.add(instance)
    db.flush()
    return instance


def _first_sold_departure_for_product(product_id: int, db: Session) -> Departure | None:
    return (
        db.query(Departure)
        .join(SaleItem, SaleItem.departure_id == Departure.id)
        .filter(
            Departure.product_id == product_id,
            Departure.deleted_at.is_(None),
            SaleItem.departure_id.is_not(None),
        )
        .order_by(Departure.date.asc(), Departure.time.asc(), Departure.id.asc())
        .first()
    )


def _resolve_admin_departure_instance(
    product: Product,
    *,
    departure_id: int | None,
    db: Session,
) -> TripDepartureInstance | None:
    target = _departure_for_product(product.id, departure_id, db) if departure_id else _first_sold_departure_for_product(product.id, db)
    if not target:
        return None
    return _ensure_departure_instance(product, target, db)


def _sale_departure_ids(sale: Sale, db: Session, product_id: int | None = None) -> list[int]:
    filters = [
        SaleItem.sale_id == sale.id,
        SaleItem.departure_id.is_not(None),
    ]
    if product_id is not None:
        filters.append(SaleItem.product_id == product_id)
    rows = (
        db.query(SaleItem.departure_id)
        .filter(*filters)
        .distinct()
        .all()
    )
    return [int(row.departure_id) for row in rows if row.departure_id is not None]


def _resolve_sale_transport_product(sale: Sale, db: Session) -> Product:
    return _resolve_sale_transport_product_with_hint(sale, db)


def _sale_transport_products(sale: Sale, db: Session) -> list[Product]:
    preferred_product_id = sale.product.id if sale.product and sale.product.is_road_trip else None
    sale_product_ids = [
        int(row.product_id)
        for row in (
            db.query(SaleItem.product_id)
            .filter(SaleItem.sale_id == sale.id, SaleItem.product_id.is_not(None))
            .distinct()
            .all()
        )
        if row.product_id is not None
    ]
    if preferred_product_id and preferred_product_id not in sale_product_ids:
        sale_product_ids.append(preferred_product_id)
    if not sale_product_ids:
        return []
    products = (
        db.query(Product)
        .filter(
            Product.id.in_(sale_product_ids),
            Product.is_road_trip.is_(True),
        )
        .order_by(Product.id.asc())
        .all()
    )
    return products


def _resolve_sale_transport_product_with_hint(
    sale: Sale,
    db: Session,
    product_public_id: str | None = None,
) -> Product:
    road_trip_products = _sale_transport_products(sale, db)
    if not road_trip_products:
        if sale.product:
            return sale.product
        raise HTTPException(status_code=404, detail="Produto nao encontrado para a venda.")
    if product_public_id:
        normalized = product_public_id.strip()
        match = next((product for product in road_trip_products if product.public_id == normalized), None)
        if not match:
            raise HTTPException(status_code=404, detail="Produto rodoviario nao encontrado para esta venda.")
        return match
    if len(road_trip_products) == 1:
        return road_trip_products[0]
    raise HTTPException(
        status_code=400,
        detail="Venda possui mais de uma excursao rodoviaria. Selecione uma saida especifica.",
    )


def _resolve_sale_departure_instance(
    sale: Sale,
    product: Product,
    *,
    departure_id: int | None,
    db: Session,
) -> TripDepartureInstance:
    sale_departure_ids = (
        db.query(SaleItem.departure_id)
        .filter(
            SaleItem.sale_id == sale.id,
            SaleItem.product_id == product.id,
            SaleItem.departure_id.is_not(None),
        )
        .distinct()
        .all()
    )
    departure_ids = [int(row.departure_id) for row in sale_departure_ids if row.departure_id is not None]
    if departure_id is not None:
        if departure_id not in departure_ids:
            raise HTTPException(status_code=400, detail="Saida informada nao pertence a esta venda.")
        departure = _departure_for_product(product.id, departure_id, db)
        return _ensure_departure_instance(product, departure, db)
    if len(departure_ids) == 1:
        departure = _departure_for_product(product.id, departure_ids[0], db)
        return _ensure_departure_instance(product, departure, db)
    if not departure_ids:
        raise HTTPException(status_code=400, detail="Venda sem saida valida para mapa de assentos.")
    raise HTTPException(
        status_code=400,
        detail="Venda possui mais de uma saida. Informe departure_id para escolher o mapa correto.",
    )


def _trip_vehicle_counts(
    product_id: int,
    db: Session,
    departure_instance_id: int | None = None,
) -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    seat_filters = [TripSeat.product_id == product_id]
    assignment_filters = [SeatAssignment.product_id == product_id]
    if departure_instance_id is None:
        seat_filters.append(TripSeat.departure_instance_id.is_(None))
        assignment_filters.append(SeatAssignment.departure_instance_id.is_(None))
    else:
        seat_filters.append(TripSeat.departure_instance_id == departure_instance_id)
        assignment_filters.append(SeatAssignment.departure_instance_id == departure_instance_id)
    seat_counts = {
        row.trip_vehicle_id: row.count
        for row in (
            db.query(TripSeat.trip_vehicle_id, func.count(TripSeat.id).label("count"))
            .filter(*seat_filters)
            .group_by(TripSeat.trip_vehicle_id)
            .all()
        )
    }
    assignment_counts = {
        row.trip_vehicle_id: row.count
        for row in (
            db.query(SeatAssignment.trip_vehicle_id, func.count(SeatAssignment.id).label("count"))
            .filter(*assignment_filters)
            .group_by(SeatAssignment.trip_vehicle_id)
            .all()
        )
    }
    blocked_counts = {
        row.trip_vehicle_id: row.count
        for row in (
            db.query(TripSeat.trip_vehicle_id, func.count(TripSeat.id).label("count"))
            .filter(
                *seat_filters,
                or_(TripSeat.is_blocked.is_(True), TripSeat.is_selectable.is_(False)),
            )
            .group_by(TripSeat.trip_vehicle_id)
            .all()
        )
    }
    return seat_counts, assignment_counts, blocked_counts


def _serialize_trip_vehicle(
    trip_vehicle: TripVehicle,
    seat_counts: dict[int, int],
    assignment_counts: dict[int, int],
    blocked_counts: dict[int, int],
) -> TripVehicleOut:
    seat_count = seat_counts.get(trip_vehicle.id, 0)
    occupied = assignment_counts.get(trip_vehicle.id, 0)
    blocked = blocked_counts.get(trip_vehicle.id, 0)
    base_capacity = trip_vehicle.capacity if trip_vehicle.capacity is not None else seat_count
    if trip_vehicle.capacity and seat_count:
        base_capacity = min(trip_vehicle.capacity, seat_count)
    elif base_capacity is None:
        base_capacity = 0
    display_capacity = base_capacity or seat_count or trip_vehicle.capacity or 0
    capacity_after_blocks = max((base_capacity or 0) - blocked, 0)
    available_by_capacity = max(capacity_after_blocks - occupied, 0)
    available_by_layout = max(seat_count - blocked - occupied, 0)
    available = min(available_by_capacity, available_by_layout)
    display_occupied = min(occupied + blocked, display_capacity) if display_capacity else occupied + blocked
    vehicle_data = _serialize_vehicle(trip_vehicle.vehicle) if trip_vehicle.vehicle else None
    layout_summary = _serialize_layout_summary(trip_vehicle.layout) if trip_vehicle.layout else None
    return TripVehicleOut(
        id=trip_vehicle.id,
        product_id=trip_vehicle.product_id,
        display_name=trip_vehicle.display_name,
        vehicle_id=trip_vehicle.vehicle_id,
        layout_id=trip_vehicle.layout_id,
        capacity=trip_vehicle.capacity,
        occupied_seats=display_occupied,
        available_seats=available,
        order_index=trip_vehicle.order_index,
        status=trip_vehicle.status,
        is_active=trip_vehicle.is_active,
        auto_activate_next=trip_vehicle.auto_activate_next,
        vehicle=vehicle_data,
        layout=layout_summary,
        seats_generated=seat_count > 0,
        created_at=trip_vehicle.created_at,
        updated_at=trip_vehicle.updated_at,
    )


def _serialize_layout_summary(layout: VehicleLayout) -> VehicleLayoutSummary:
    schema = VehicleLayoutSchema.model_validate(layout.layout_schema)
    metrics = _compute_layout_metrics(schema)
    return VehicleLayoutSummary(
        id=layout.id,
        name=layout.name,
        vehicle_type=layout.vehicle_type,
        slug=layout.slug,
        seat_count=metrics.seat_count or layout.seat_count,
        row_count=metrics.row_count or layout.row_count,
        column_count=metrics.column_count or layout.column_count,
        thumbnail_url=layout.thumbnail_url,
        is_active=layout.is_active,
        created_at=layout.created_at,
        updated_at=layout.updated_at,
        deck_mode=metrics.deck_mode,
        deck_summaries=metrics.deck_summaries,
    )


def _serialize_layout_detail(layout: VehicleLayout) -> VehicleLayoutDetail:
    schema = LayoutSchemaModel.model_validate(layout.layout_schema)
    summary = _serialize_layout_summary(layout)
    return VehicleLayoutDetail(**summary.model_dump(), layout_schema=schema)


def _agency_layout_query(db: Session, agency_id: int):
    return db.query(VehicleLayout).filter(VehicleLayout.agency_id == agency_id)


def list_vehicle_layouts(user: User, db: Session) -> VehicleLayoutListResponse:
    agency_id = get_user_default_agency_id(user, db)
    layouts = (
        _agency_layout_query(db, agency_id)
        .order_by(VehicleLayout.created_at.desc())
        .all()
    )
    return VehicleLayoutListResponse(items=[_serialize_layout_summary(layout) for layout in layouts])


def _layout_by_id(layout_id: int, agency_id: int, db: Session) -> VehicleLayout:
    layout = (
        _agency_layout_query(db, agency_id)
        .filter(VehicleLayout.id == layout_id)
        .first()
    )
    if not layout:
        raise HTTPException(status_code=404, detail="Layout nao encontrado.")
    return layout


def get_vehicle_layout_detail(user: User, layout_id: int, db: Session) -> VehicleLayoutDetail:
    agency_id = get_user_default_agency_id(user, db)
    layout = _layout_by_id(layout_id, agency_id, db)
    return _serialize_layout_detail(layout)


def create_vehicle_layout(user: User, payload: VehicleLayoutPayload, db: Session) -> VehicleLayoutDetail:
    agency_id = get_user_default_agency_id(user, db)
    schema = payload.layout_schema
    metrics = _compute_layout_metrics(schema)
    layout = VehicleLayout(
        agency_id=agency_id,
        name=payload.name.strip(),
        slug=payload.slug.strip() if payload.slug else None,
        vehicle_type=payload.vehicle_type or "custom",
        seat_count=payload.seat_count or metrics.seat_count,
        row_count=payload.row_count or metrics.row_count,
        column_count=payload.column_count or metrics.column_count,
        layout_schema=schema.model_dump(),
        thumbnail_url=payload.thumbnail_url,
        is_active=payload.is_active,
    )
    db.add(layout)
    db.commit()
    db.refresh(layout)
    return _serialize_layout_detail(layout)


def update_vehicle_layout(user: User, layout_id: int, payload: VehicleLayoutPayload, db: Session) -> VehicleLayoutDetail:
    agency_id = get_user_default_agency_id(user, db)
    layout = _layout_by_id(layout_id, agency_id, db)
    schema = payload.layout_schema
    metrics = _compute_layout_metrics(schema)
    layout.name = payload.name.strip()
    layout.slug = payload.slug.strip() if payload.slug else None
    layout.vehicle_type = payload.vehicle_type or layout.vehicle_type
    layout.seat_count = payload.seat_count or metrics.seat_count
    layout.row_count = payload.row_count or metrics.row_count
    layout.column_count = payload.column_count or metrics.column_count
    layout.layout_schema = schema.model_dump()
    layout.thumbnail_url = payload.thumbnail_url
    layout.is_active = payload.is_active
    db.add(layout)
    db.commit()
    db.refresh(layout)
    return _serialize_layout_detail(layout)


def duplicate_vehicle_layout(user: User, layout_id: int, db: Session) -> VehicleLayoutDetail:
    agency_id = get_user_default_agency_id(user, db)
    layout = _layout_by_id(layout_id, agency_id, db)
    clone = VehicleLayout(
        agency_id=agency_id,
        name=f"{layout.name} (copia)",
        slug=None,
        vehicle_type=layout.vehicle_type,
        seat_count=layout.seat_count,
        row_count=layout.row_count,
        column_count=layout.column_count,
        layout_schema=layout.layout_schema,
        thumbnail_url=layout.thumbnail_url,
        is_active=layout.is_active,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return _serialize_layout_detail(clone)


def delete_vehicle_layout(user: User, layout_id: int, db: Session) -> None:
    agency_id = get_user_default_agency_id(user, db)
    layout = _layout_by_id(layout_id, agency_id, db)
    usage = (
        db.query(TripTransportConfig)
        .filter(TripTransportConfig.layout_id == layout.id)
        .count()
    )
    if usage:
        raise HTTPException(
            status_code=400,
            detail="Layout associado a viagens. Remova a associacao antes de excluir.",
        )
    db.delete(layout)
    db.commit()


def _serialize_vehicle(vehicle: Vehicle) -> VehicleOut:
    return VehicleOut(
        id=vehicle.id,
        name=vehicle.name,
        plate=vehicle.plate,
        photo_url=vehicle.photo_url,
        partner_name=vehicle.partner_name,
        layout_id=vehicle.layout_id,
        is_active=vehicle.is_active,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


def list_vehicles(user: User, db: Session) -> VehicleListResponse:
    agency_id = get_user_default_agency_id(user, db)
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.agency_id == agency_id)
        .order_by(Vehicle.created_at.desc())
        .all()
    )
    return VehicleListResponse(items=[_serialize_vehicle(vehicle) for vehicle in vehicles])


def _vehicle_by_id(vehicle_id: int, agency_id: int, db: Session) -> Vehicle:
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.agency_id == agency_id, Vehicle.id == vehicle_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veiculo nao encontrado.")
    return vehicle


def create_vehicle(user: User, payload: VehiclePayload, db: Session) -> VehicleOut:
    agency_id = get_user_default_agency_id(user, db)
    vehicle = Vehicle(
        agency_id=agency_id,
        name=payload.name.strip(),
        plate=payload.plate.strip() if payload.plate else None,
        photo_url=payload.photo_url.strip() if payload.photo_url else None,
        partner_name=payload.partner_name.strip() if payload.partner_name else None,
        layout_id=payload.layout_id,
        is_active=payload.is_active,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return _serialize_vehicle(vehicle)


def update_vehicle(user: User, vehicle_id: int, payload: VehiclePayload, db: Session) -> VehicleOut:
    agency_id = get_user_default_agency_id(user, db)
    vehicle = _vehicle_by_id(vehicle_id, agency_id, db)
    vehicle.name = payload.name.strip()
    vehicle.plate = payload.plate.strip() if payload.plate else None
    vehicle.photo_url = payload.photo_url.strip() if payload.photo_url else None
    vehicle.partner_name = payload.partner_name.strip() if payload.partner_name else None
    vehicle.layout_id = payload.layout_id
    vehicle.is_active = payload.is_active
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return _serialize_vehicle(vehicle)


def delete_vehicle(user: User, vehicle_id: int, db: Session) -> None:
    agency_id = get_user_default_agency_id(user, db)
    vehicle = _vehicle_by_id(vehicle_id, agency_id, db)
    usage = (
        db.query(TripTransportConfig)
        .filter(TripTransportConfig.vehicle_id == vehicle.id)
        .count()
    )
    if usage:
        raise HTTPException(
            status_code=400,
            detail="Veiculo associado a viagens. Desvincule antes de excluir.",
        )
    db.delete(vehicle)
    db.commit()


def _ensure_trip_config(product: Product, db: Session) -> TripTransportConfig:
    config = (
        db.query(TripTransportConfig)
        .filter(TripTransportConfig.product_id == product.id)
        .first()
    )
    if not config:
        config = TripTransportConfig(product_id=product.id, is_road_trip=product.is_road_trip)
        db.add(config)
        db.flush()
    return config


def _trip_vehicle_summaries(
    product_id: int,
    db: Session,
    departure_instance_id: int | None = None,
) -> list[TripVehicleOut]:
    vehicles = (
        db.query(TripVehicle)
        .options(joinedload(TripVehicle.vehicle), joinedload(TripVehicle.layout))
        .filter(TripVehicle.product_id == product_id)
        .order_by(TripVehicle.order_index.asc(), TripVehicle.id.asc())
        .all()
    )
    seat_counts, assignment_counts, blocked_counts = _trip_vehicle_counts(
        product_id,
        db,
        departure_instance_id=departure_instance_id,
    )
    return [
        _serialize_trip_vehicle(vehicle, seat_counts, assignment_counts, blocked_counts) for vehicle in vehicles
    ]


def _resolve_active_trip_vehicle(product: Product, db: Session) -> TripVehicle | None:
    return (
        db.query(TripVehicle)
        .filter(
            TripVehicle.product_id == product.id,
            TripVehicle.is_active.is_(True),
        )
        .order_by(
            case((TripVehicle.status == TripVehicleStatus.active.value, 0), else_=1),
            TripVehicle.order_index.asc(),
            TripVehicle.id.asc(),
        )
        .first()
    )


def _trip_vehicle_snapshot(
    vehicle: TripVehicle,
    db: Session,
    departure_instance_id: int | None = None,
) -> TripVehicleOut:
    seat_counts, assignment_counts, blocked_counts = _trip_vehicle_counts(
        vehicle.product_id,
        db,
        departure_instance_id=departure_instance_id,
    )
    return _serialize_trip_vehicle(vehicle, seat_counts, assignment_counts, blocked_counts)


def _sync_trip_vehicle_statuses(product_id: int, db: Session, departure_instance_id: int | None = None) -> None:
    vehicles = (
        db.query(TripVehicle)
        .filter(TripVehicle.product_id == product_id)
        .order_by(TripVehicle.order_index.asc(), TripVehicle.id.asc())
        .all()
    )
    seat_counts, assignment_counts, blocked_counts = _trip_vehicle_counts(
        product_id,
        db,
        departure_instance_id=departure_instance_id,
    )
    activation_available = True
    active_assigned = False
    for vehicle in vehicles:
        if not vehicle.is_active:
            vehicle.status = TripVehicleStatus.inactive.value
            continue
        seat_count = seat_counts.get(vehicle.id, 0)
        blocked_count = blocked_counts.get(vehicle.id, 0)
        capacity_limit = vehicle.capacity or seat_count
        if vehicle.capacity and seat_count:
            capacity_limit = min(vehicle.capacity, seat_count)
        elif not capacity_limit:
            capacity_limit = seat_count or vehicle.capacity or 0
        capacity_limit = max(capacity_limit - blocked_count, 0)
        occupancy = assignment_counts.get(vehicle.id, 0)
        if capacity_limit <= 0:
            vehicle.status = TripVehicleStatus.inactive.value
            continue
        if occupancy >= capacity_limit:
            vehicle.status = TripVehicleStatus.full.value
            if not vehicle.auto_activate_next:
                activation_available = False
            continue
        if active_assigned or not activation_available:
            vehicle.status = TripVehicleStatus.inactive.value
            continue
        vehicle.status = TripVehicleStatus.active.value
        active_assigned = True
    db.flush()


def _apply_trip_vehicle_payloads(
    product: Product,
    config: TripTransportConfig,
    payloads: Sequence[TripVehiclePayload],
    regenerate_layout: bool,
    db: Session,
) -> None:
    if not payloads:
        raise HTTPException(status_code=400, detail="Associe ao menos um veiculo para viagens rodoviarias.")
    order_values = [item.order_index for item in payloads]
    if len(order_values) != len(set(order_values)):
        raise HTTPException(status_code=400, detail="Existem ordens de liberacao duplicadas.")
    existing = {
        vehicle.id: vehicle
        for vehicle in db.query(TripVehicle)
        .filter(TripVehicle.product_id == product.id)
        .all()
    }
    provided_active = any(item.status == TripVehicleStatus.active.value for item in payloads if item.status)
    seen_ids: list[int] = []
    primary_payload: TripVehiclePayload | None = None
    sorted_payloads = sorted(payloads, key=lambda item: (item.order_index, item.id or 0))
    for index, item in enumerate(sorted_payloads):
        trip_vehicle = existing.get(item.id) if item.id else None
        if item.id and not trip_vehicle:
            raise HTTPException(status_code=404, detail="Veiculo associado nao encontrado.")
        if not trip_vehicle:
            trip_vehicle = TripVehicle(product_id=product.id)
        previous_layout_id = trip_vehicle.layout_id
        layout = (
            db.query(VehicleLayout)
            .filter(VehicleLayout.id == item.layout_id)
            .first()
        )
        if not layout:
            raise HTTPException(status_code=404, detail="Layout de veiculo nao encontrado.")
        trip_vehicle.vehicle_id = item.vehicle_id
        trip_vehicle.layout_id = item.layout_id
        trip_vehicle.display_name = (item.display_name or layout.name).strip() if (item.display_name or layout.name) else None
        trip_vehicle.capacity = item.capacity
        trip_vehicle.order_index = item.order_index
        trip_vehicle.is_active = item.is_active
        trip_vehicle.auto_activate_next = item.auto_activate_next
        if item.status:
            trip_vehicle.status = item.status
        elif not provided_active and index == 0:
            trip_vehicle.status = TripVehicleStatus.active.value
        elif not provided_active:
            trip_vehicle.status = TripVehicleStatus.inactive.value
        db.add(trip_vehicle)
        db.flush()
        seen_ids.append(trip_vehicle.id)
        if primary_payload is None:
            primary_payload = item
        existing_seats = (
            db.query(func.count(TripSeat.id))
            .filter(TripSeat.trip_vehicle_id == trip_vehicle.id)
            .scalar()
            or 0
        )
        should_regenerate = regenerate_layout or previous_layout_id != item.layout_id or existing_seats == 0
        if should_regenerate:
            _generate_trip_vehicle_seats(product, trip_vehicle, layout, db, force=True)
    if seen_ids:
        ids_to_keep = seen_ids
        db.query(TripVehicle).filter(
            TripVehicle.product_id == product.id,
            ~TripVehicle.id.in_(ids_to_keep),
        ).delete(synchronize_session=False)
    else:
        db.query(TripVehicle).filter(TripVehicle.product_id == product.id).delete(synchronize_session=False)
    reference_payload = primary_payload or sorted_payloads[0]
    config.layout_id = reference_payload.layout_id
    config.vehicle_id = reference_payload.vehicle_id
    ref_layout = (
        db.query(VehicleLayout)
        .filter(VehicleLayout.id == reference_payload.layout_id)
        .first()
    )
    if ref_layout:
        config.layout_schema_checksum = _layout_schema_checksum(ref_layout.layout_schema)

def _serialize_trip_config(config: TripTransportConfig, seat_count: int, db: Session) -> TripTransportConfigOut:
    layout_summary = _serialize_layout_summary(config.layout) if config.layout else None
    vehicle_data = _serialize_vehicle(config.vehicle) if config.vehicle else None
    return TripTransportConfigOut(
        product_id=config.product_id,
        is_road_trip=config.is_road_trip,
        layout=layout_summary,
        vehicle=vehicle_data,
        boarding_notes=config.boarding_notes,
        seats_generated=seat_count > 0,
        seat_count=seat_count,
        updated_at=config.updated_at,
        vehicles=_trip_vehicle_summaries(config.product_id, db),
    )


def get_trip_transport_config(product: Product, db: Session) -> TripTransportConfigOut:
    config = _ensure_trip_config(product, db)
    seat_count = (
        db.query(func.count(TripSeat.id))
        .filter(TripSeat.product_id == product.id)
        .scalar()
        or 0
    )
    return _serialize_trip_config(config, seat_count, db)


def save_trip_transport_config(
    product: Product,
    payload: TripTransportConfigPayload,
    db: Session,
) -> TripTransportConfigOut:
    config = _ensure_trip_config(product, db)
    config.is_road_trip = payload.is_road_trip
    product.is_road_trip = payload.is_road_trip
    config.boarding_notes = payload.boarding_notes

    if payload.is_road_trip:
        vehicles_payload = list(payload.vehicles or [])
        if not vehicles_payload:
            if not payload.layout_id:
                raise HTTPException(status_code=400, detail="Selecione ao menos um layout para configurar o transporte.")
            layout = (
                db.query(VehicleLayout)
                .filter(VehicleLayout.id == payload.layout_id)
                .first()
            )
            if not layout:
                raise HTTPException(status_code=404, detail="Layout nao encontrado.")
            schema = VehicleLayoutSchema.model_validate(layout.layout_schema)
            metrics = _compute_layout_metrics(schema)
            fallback_capacity = metrics.seat_count or 1
            vehicles_payload = [
                TripVehiclePayload(
                    vehicle_id=payload.vehicle_id,
                    layout_id=layout.id,
                    display_name=layout.name,
                    capacity=fallback_capacity,
                    order_index=1,
                    status=TripVehicleStatus.active.value,
                    is_active=True,
                    auto_activate_next=True,
                )
            ]
        _apply_trip_vehicle_payloads(product, config, vehicles_payload, payload.regenerate_layout, db)
    else:
        config.layout_id = None
        config.boarding_notes = None
        db.query(SeatAssignment).filter(SeatAssignment.product_id == product.id).delete(synchronize_session=False)
        db.query(TripSeat).filter(TripSeat.product_id == product.id).delete(synchronize_session=False)
        db.query(TripVehicle).filter(TripVehicle.product_id == product.id).delete(synchronize_session=False)

    db.add_all([config, product])
    db.commit()
    db.refresh(config)
    seat_count = (
        db.query(func.count(TripSeat.id))
        .filter(TripSeat.product_id == product.id)
        .scalar()
        or 0
    )
    return _serialize_trip_config(config, seat_count, db)


def _generate_trip_vehicle_seats(
    product: Product,
    trip_vehicle: TripVehicle,
    layout: VehicleLayout,
    db: Session,
    force: bool = False,
    departure_instance_id: int | None = None,
) -> None:
    assignment_filters = [
        SeatAssignment.product_id == product.id,
        SeatAssignment.trip_vehicle_id == trip_vehicle.id,
    ]
    seat_filters = [
        TripSeat.product_id == product.id,
        TripSeat.trip_vehicle_id == trip_vehicle.id,
    ]
    if departure_instance_id is None:
        assignment_filters.append(SeatAssignment.departure_instance_id.is_(None))
        seat_filters.append(TripSeat.departure_instance_id.is_(None))
    else:
        assignment_filters.append(SeatAssignment.departure_instance_id == departure_instance_id)
        seat_filters.append(TripSeat.departure_instance_id == departure_instance_id)
    if not force:
        assignments_exist = (
            db.query(SeatAssignment.id)
            .filter(*assignment_filters)
            .first()
        )
        if assignments_exist:
            raise HTTPException(
                status_code=409,
                detail="Ja existem assentos atribuidos neste veiculo. Confirme a regeneracao para substituir o mapa.",
            )
    db.query(SeatAssignment).filter(*assignment_filters).delete(synchronize_session=False)
    db.query(TripSeat).filter(*seat_filters).delete(synchronize_session=False)
    schema = LayoutSchemaModel.model_validate(layout.layout_schema)
    counter = 0
    for deck_order, deck in enumerate(_resolve_decks(schema)):
        ordered_cells = sorted(deck.cells, key=lambda entry: (entry.row, entry.col))
        for cell in ordered_cells:
            if cell.type not in SelectableSeatTypes:
                continue
            counter += 1
            seat_label = str(cell.label or counter)
            seat_number = f"{trip_vehicle.id}-{seat_label}"
            meta = dict(cell.meta or {})
            deck_key = deck.key or f"deck_{deck_order}"
            meta.setdefault("deck_key", deck_key)
            meta.setdefault("deck_label", deck.label)
            meta.setdefault("deck_order", deck_order)
            trip_seat = TripSeat(
                product_id=product.id,
                departure_instance_id=departure_instance_id,
                layout_id=layout.id,
                trip_vehicle_id=trip_vehicle.id,
                seat_number=seat_number,
                seat_label=cell.label or seat_label,
                seat_type=cell.type,
                row_index=cell.row,
                col_index=cell.col,
                deck_key=deck_key,
                deck_label=deck.label,
                deck_order=deck_order,
                is_selectable=bool(cell.selectable),
                is_blocked=bool(cell.blocked),
                meta_json=meta,
            )
            db.add(trip_seat)
    db.flush()


def _sale_product_filter(product: Product):
    return or_(Sale.product_id == product.id, Sale.product_public_id == product.public_id)


def _contract_by_token(token: str, db: Session) -> LegalContract:
    normalized = (token or "").strip()
    if not normalized:
        raise HTTPException(status_code=404, detail="Assinatura nao encontrada.")
    contract = (
        db.query(LegalContract)
        .options(
            joinedload(LegalContract.sale).joinedload(Sale.product),
            joinedload(LegalContract.sale).joinedload(Sale.items),
        )
        .filter(LegalContract.signature_token == normalized)
        .first()
    )
    if not contract or not contract.sale:
        raise HTTPException(status_code=404, detail="Assinatura nao encontrada.")
    return contract


def _sale_by_passenger_token(token: str, db: Session) -> Sale:
    normalized = (token or "").strip()
    if not normalized:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.product), joinedload(Sale.items), joinedload(Sale.contract))
        .filter(Sale.passenger_form_token == normalized)
        .first()
    )
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return sale


def _passenger_records(
    product: Product,
    db: Session,
    departure_id: int | None = None,
) -> list[SalePassenger]:
    section_sale_group_ids = (
        db.query(PassengerGroup.id)
        .join(SaleItem, SaleItem.id == PassengerGroup.sale_item_id)
        .filter(SaleItem.product_id == product.id)
        .subquery()
    )
    query = (
        db.query(SalePassenger)
        .join(Sale, Sale.id == SalePassenger.sale_id)
        .options(
            joinedload(SalePassenger.sale),
            joinedload(SalePassenger.passenger_group).joinedload(PassengerGroup.sale_item),
        )
        .filter(
            or_(
                _sale_product_filter(product),
                SalePassenger.passenger_group_id.in_(section_sale_group_ids),
            ),
            SalePassenger.type != PassengerType.child_free.value,
        )
    )
    if departure_id is not None:
        query = (
            query.join(PassengerGroup, PassengerGroup.id == SalePassenger.passenger_group_id)
            .join(SaleItem, SaleItem.id == PassengerGroup.sale_item_id)
            .filter(SaleItem.departure_id == departure_id)
        )
    return query.all()


def _trip_seat_records(
    product: Product,
    db: Session,
    trip_vehicle_id: int | None = None,
    departure_instance_id: int | None = None,
) -> list[TripSeat]:
    query = (
        db.query(TripSeat)
        .filter(TripSeat.product_id == product.id)
        .options(
            selectinload(TripSeat.assignments)
            .joinedload(SeatAssignment.passenger)
            .joinedload(SalePassenger.sale)
        )
        .order_by(TripSeat.row_index.asc(), TripSeat.col_index.asc())
    )
    if departure_instance_id is None:
        query = query.filter(TripSeat.departure_instance_id.is_(None))
    else:
        query = query.filter(TripSeat.departure_instance_id == departure_instance_id)
    if trip_vehicle_id:
        query = query.filter(TripSeat.trip_vehicle_id == trip_vehicle_id)
    return query.all()


def _passenger_assignment_map(
    product_id: int,
    db: Session,
    departure_instance_id: int | None = None,
) -> dict[int, TripSeat]:
    filters = [SeatAssignment.product_id == product_id]
    if departure_instance_id is None:
        filters.append(SeatAssignment.departure_instance_id.is_(None))
    else:
        filters.append(SeatAssignment.departure_instance_id == departure_instance_id)
    assignments = (
        db.query(SeatAssignment)
        .options(
            joinedload(SeatAssignment.seat)
        )
        .filter(*filters)
        .all()
    )
    mapping: dict[int, TripSeat] = {}
    for entry in assignments:
        if entry.seat:
            mapping[entry.passenger_id] = entry.seat
    return mapping


def _serialize_trip_seat(seat: TripSeat, current_sale_id: int | None = None) -> TripSeatOut:
    assignment = seat.assignments[0] if seat.assignments else None
    passenger = assignment.passenger if assignment else None
    passenger_name = passenger.name if passenger else None
    meta = seat.meta_json or {}
    deck_key = seat.deck_key or meta.get("deck_key")
    deck_label = seat.deck_label or meta.get("deck_label")
    deck_order = seat.deck_order if seat.deck_order is not None else meta.get("deck_order")
    return TripSeatOut(
        id=seat.id,
        trip_vehicle_id=seat.trip_vehicle_id,
        seat_number=seat.seat_number,
        seat_label=seat.seat_label,
        seat_type=seat.seat_type,
        row_index=seat.row_index,
        col_index=seat.col_index,
        is_selectable=seat.is_selectable,
        is_blocked=seat.is_blocked,
        is_occupied=bool(assignment),
        occupied_by_passenger_id=passenger.id if passenger else None,
        occupied_by_passenger_name=passenger_name,
        occupied_by_sale_id=assignment.sale_id if assignment else None,
        occupied_by_current_sale=bool(assignment and assignment.sale_id == current_sale_id),
        deck_key=deck_key,
        deck_label=deck_label,
        deck_order=deck_order,
    )


def _passenger_summary(passenger: SalePassenger, assignments: dict[int, TripSeat]) -> PassengerSeatSummary:
    seat = assignments.get(passenger.id)
    seat_label = seat.seat_label if seat else None
    seat_number = seat.seat_number if seat else None
    status = "assigned" if seat else "unassigned"
    return PassengerSeatSummary(
        id=passenger.id,
        sale_id=passenger.sale_id,
        name=passenger.name or "Passageiro",
        seat_id=seat.id if seat else None,
        seat_number=seat_number,
        seat_label=seat_label,
        status=status,  # type: ignore[arg-type]
    )


def _seat_stats(seats: Iterable[TripSeat], passengers: Iterable[PassengerSeatSummary]) -> SeatMapStats:
    seats_list = list(seats)
    passengers_list = list(passengers)
    total = len(seats_list)
    blocked = sum(1 for seat in seats_list if seat.is_blocked or not seat.is_selectable)
    occupied = sum(1 for seat in seats_list if seat.assignments or seat.is_blocked or not seat.is_selectable)
    available = max(total - blocked - occupied, 0)
    assigned_passengers = sum(1 for passenger in passengers_list if passenger.status == "assigned")
    pending_passengers = max(len(passengers_list) - assigned_passengers, 0)
    return SeatMapStats(
        total_seats=total,
        available_seats=available,
        occupied_seats=occupied,
        blocked_seats=blocked,
        assigned_passengers=assigned_passengers,
        pending_passengers=pending_passengers,
    )


def _departure_time_str(departure: Departure | None) -> str | None:
    if not departure:
        return None
    return departure.time.strftime("%H:%M")


def get_trip_seat_map(
    product: Product,
    db: Session,
    trip_vehicle_id: int | None = None,
    departure_id: int | None = None,
) -> SeatMapContext:
    config = _ensure_trip_config(product, db)
    segmented = _is_segmented_seat_map(product, config)
    departure_instance = _resolve_admin_departure_instance(product, departure_id=departure_id, db=db) if segmented else None
    departure = departure_instance.departure if departure_instance else None
    departure_instance_id = departure_instance.id if departure_instance else None
    if config.is_road_trip:
        _sync_trip_vehicle_statuses(
            product.id,
            db,
            departure_instance_id=departure_instance_id if segmented else None,
        )
    target_vehicle = None
    layout = None
    seats: list[TripSeat] = []
    vehicle_options: list[TripVehicleOut] = []
    if config.is_road_trip:
        vehicle_query = db.query(TripVehicle).filter(TripVehicle.product_id == product.id)
        if trip_vehicle_id:
            target_vehicle = vehicle_query.filter(TripVehicle.id == trip_vehicle_id).first()
        if not target_vehicle:
            target_vehicle = _resolve_active_trip_vehicle(product, db) or vehicle_query.order_by(
                TripVehicle.order_index.asc(), TripVehicle.id.asc()
            ).first()
        if target_vehicle:
            layout = _serialize_layout_detail(target_vehicle.layout) if target_vehicle.layout else None
            if segmented and departure_instance and layout and not _trip_seat_records(
                product,
                db,
                trip_vehicle_id=target_vehicle.id,
                departure_instance_id=departure_instance_id,
            ):
                _generate_trip_vehicle_seats(
                    product,
                    target_vehicle,
                    target_vehicle.layout,
                    db,
                    force=True,
                    departure_instance_id=departure_instance_id,
                )
                db.commit()
            seats = _trip_seat_records(
                product,
                db,
                trip_vehicle_id=target_vehicle.id,
                departure_instance_id=departure_instance_id if segmented else None,
            )
        vehicle_options = _trip_vehicle_summaries(
            product.id,
            db,
            departure_instance_id=departure_instance_id if segmented else None,
        )
    else:
        layout = _serialize_layout_detail(config.layout) if config.layout else None
        seats = _trip_seat_records(product, db, departure_instance_id=None)
        vehicle_options = []
    passengers = _passenger_records(product, db, departure_id=departure.id if departure else None)
    assignment_map = _passenger_assignment_map(
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    passenger_items = [_passenger_summary(passenger, assignment_map) for passenger in passengers]
    stats = _seat_stats(seats, passenger_items)
    trip_vehicle_summary = (
        _trip_vehicle_snapshot(
            target_vehicle,
            db,
            departure_instance_id=departure_instance_id if segmented else None,
        )
        if target_vehicle
        else None
    )
    return SeatMapContext(
        product_id=product.id,
        product_name=product.name,
        product_public_id=product.public_id,
        trip_date=product.trip_date,
        departure_instance_id=departure_instance_id,
        departure_id=departure.id if departure else None,
        departure_date=departure.date if departure else None,
        departure_time=_departure_time_str(departure),
        trip_vehicle=trip_vehicle_summary,
        vehicles=vehicle_options,
        layout=layout,
        seats=[_serialize_trip_seat(seat) for seat in seats],
        passengers=passenger_items,
        stats=stats,
        boarding_notes=config.boarding_notes,
        can_assign=config.is_road_trip and bool(layout),
    )


def _seat_selection_status_for_sale(
    sale: Sale,
    contract: LegalContract | None,
    db: Session,
) -> SeatPostSignatureStatus:
    if not sale:
        raise HTTPException(status_code=404, detail="Venda ou produto nao encontrado.")
    product = _resolve_sale_transport_product(sale, db)
    config = _ensure_trip_config(product, db)
    segmented = _is_segmented_seat_map(product, config)
    departure_instance = None
    if segmented:
        try:
            departure_instance = _resolve_sale_departure_instance(sale, product, departure_id=None, db=db)
        except HTTPException:
            departure_instance = None
    departure_instance_id = departure_instance.id if departure_instance else None
    if config.is_road_trip:
        _sync_trip_vehicle_statuses(
            product.id,
            db,
            departure_instance_id=departure_instance_id if segmented else None,
        )
    seat_filters = [TripSeat.product_id == product.id]
    assignment_filters = [SeatAssignment.sale_id == sale.id]
    if segmented:
        if departure_instance_id is not None:
            seat_filters.append(TripSeat.departure_instance_id == departure_instance_id)
            assignment_filters.append(SeatAssignment.departure_instance_id == departure_instance_id)
        else:
            seat_filters.append(TripSeat.departure_instance_id.is_not(None))
            assignment_filters.append(SeatAssignment.departure_instance_id.is_not(None))
    else:
        seat_filters.append(TripSeat.departure_instance_id.is_(None))
        assignment_filters.append(SeatAssignment.departure_instance_id.is_(None))
    seats_generated = (
        db.query(TripSeat.id)
        .filter(*seat_filters)
        .first()
        is not None
    )
    active_vehicle = _resolve_active_trip_vehicle(product, db) if config.is_road_trip else None
    active_vehicle_seats_generated = False
    if active_vehicle:
        active_vehicle_filters = [TripSeat.trip_vehicle_id == active_vehicle.id]
        if segmented:
            if departure_instance_id is not None:
                active_vehicle_filters.append(TripSeat.departure_instance_id == departure_instance_id)
            else:
                active_vehicle_filters.append(TripSeat.departure_instance_id.is_not(None))
        else:
            active_vehicle_filters.append(TripSeat.departure_instance_id.is_(None))
        active_vehicle_seats_generated = (
            db.query(TripSeat.id)
            .filter(*active_vehicle_filters)
            .first()
            is not None
        )
    payment_confirmed = sale.payment_status == SalePaymentStatus.paid.value
    passengers_completed = sale.passenger_status == SalePassengerStatus.completed.value
    seats_selected = (
        db.query(SeatAssignment.id)
        .filter(*assignment_filters)
        .count()
        > 0
    )
    requires_signature = contract is not None
    signature_signed = (
        contract.signature_status == LegalContractSignatureStatus.signed.value if contract else True
    )
    can_select = (
        signature_signed
        and payment_confirmed
        and passengers_completed
        and config.is_road_trip
        and seats_generated
        and bool(active_vehicle)
        and active_vehicle_seats_generated
    )
    message = None
    if not config.is_road_trip:
        message = "Assentos nao estao disponiveis para esta excursao."
    elif not seats_generated:
        message = "Mapa de assentos ainda nao foi configurado pela agencia."
    elif not active_vehicle:
        message = "Os assentos serao liberados assim que o proximo veiculo estiver ativo."
    elif not active_vehicle_seats_generated:
        message = "O veiculo atual ainda nao possui mapa liberado."
    elif not passengers_completed:
        message = "Finalize o cadastro dos passageiros para escolher os assentos."
    elif not payment_confirmed:
        message = "Pagamento ainda nao confirmado."
    elif requires_signature and not signature_signed:
        message = "Assinatura ainda nao foi concluida."
    return SeatPostSignatureStatus(
        sale_id=sale.id,
        contract_id=contract.id if contract else None,
        product_id=product.id,
        signature_status=contract.signature_status if contract else None,
        is_road_trip=config.is_road_trip,
        has_layout=bool((active_vehicle and active_vehicle.layout_id) or config.layout_id),
        seats_generated=seats_generated,
        payment_confirmed=payment_confirmed,
        passengers_completed=passengers_completed,
        can_select_seats=can_select,
        seats_selected=seats_selected,
        message=message,
    )


def get_post_signature_status(token: str, db: Session) -> SeatPostSignatureStatus:
    contract = _contract_by_token(token, db)
    return _seat_selection_status_for_sale(contract.sale, contract, db)


def get_post_sale_status(token: str, db: Session) -> SeatPostSignatureStatus:
    sale = _sale_by_passenger_token(token, db)
    return _seat_selection_status_for_sale(sale, sale.contract, db)


def list_sale_seat_selection_products(token: str, db: Session) -> SaleSeatSelectionProductsResponse:
    sale = _sale_by_passenger_token(token, db)
    products = _sale_transport_products(sale, db)
    return SaleSeatSelectionProductsResponse(
        sale_id=sale.id,
        items=[
            SaleSeatSelectionProduct(
                product_id=product.id,
                product_public_id=product.public_id,
                product_name=product.name,
            )
            for product in products
            if product.public_id
        ],
    )


def get_public_seat_selection_context(
    token: str,
    db: Session,
    trip_vehicle_id: int | None = None,
    departure_id: int | None = None,
) -> SeatSelectionContext:
    contract = _contract_by_token(token, db)
    sale = contract.sale
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return get_seat_selection_context(sale, db, trip_vehicle_id=trip_vehicle_id, departure_id=departure_id)


def get_public_seat_selection_context_by_sale(
    token: str,
    db: Session,
    trip_vehicle_id: int | None = None,
    departure_id: int | None = None,
    product_public_id: str | None = None,
) -> SeatSelectionContext:
    sale = _sale_by_passenger_token(token, db)
    return get_seat_selection_context(
        sale,
        db,
        trip_vehicle_id=trip_vehicle_id,
        departure_id=departure_id,
        product_public_id=product_public_id,
    )


def select_seat_for_signature(
    token: str,
    payload: SeatAssignmentPayload,
    db: Session,
    departure_id: int | None = None,
) -> SeatSelectionContext:
    contract = _contract_by_token(token, db)
    sale = contract.sale
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    _ensure_sale_ready_for_selection(sale, db)
    product = _resolve_sale_transport_product(sale, db)
    assignment = assign_seat_to_passenger(
        product,
        payload,
        actor=SeatAssignmentActor.customer,
        db=db,
        expected_sale_id=sale.id,
    )
    return get_seat_selection_context(
        sale,
        db,
        trip_vehicle_id=assignment.trip_vehicle_id,
        departure_id=departure_id,
    )


def select_seat_for_sale(
    token: str,
    payload: SeatAssignmentPayload,
    db: Session,
    departure_id: int | None = None,
    product_public_id: str | None = None,
) -> SeatSelectionContext:
    sale = _sale_by_passenger_token(token, db)
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    _ensure_sale_ready_for_selection(sale, db)
    product = _resolve_sale_transport_product_with_hint(sale, db, product_public_id=product_public_id)
    assignment = assign_seat_to_passenger(
        product,
        payload,
        actor=SeatAssignmentActor.customer,
        db=db,
        expected_sale_id=sale.id,
    )
    return get_seat_selection_context(
        sale,
        db,
        trip_vehicle_id=assignment.trip_vehicle_id,
        departure_id=departure_id,
        product_public_id=product.public_id,
    )


def _ensure_sale_ready_for_selection(sale: Sale, db: Session) -> None:
    if sale.payment_status != SalePaymentStatus.paid.value:
        raise HTTPException(status_code=400, detail="Pagamento ainda nao confirmado.")
    if sale.passenger_status != SalePassengerStatus.completed.value:
        raise HTTPException(status_code=400, detail="Preencha todos os passageiros antes de definir assentos.")
    contract = sale.contract or (
        db.query(LegalContract)
        .filter(LegalContract.sale_id == sale.id)
        .first()
    )
    if contract and contract.signature_status != "signed":
        raise HTTPException(status_code=400, detail="Contrato nao esta assinado.")


def get_seat_selection_context(
    sale: Sale,
    db: Session,
    trip_vehicle_id: int | None = None,
    departure_id: int | None = None,
    product_public_id: str | None = None,
) -> SeatSelectionContext:
    _ensure_sale_ready_for_selection(sale, db)
    product = _resolve_sale_transport_product_with_hint(sale, db, product_public_id=product_public_id)
    config = _ensure_trip_config(product, db)
    if not config.is_road_trip:
        raise HTTPException(status_code=404, detail="Assentos indisponiveis para esta excursao.")
    segmented = _is_segmented_seat_map(product, config)
    departure_instance = _resolve_sale_departure_instance(sale, product, departure_id=departure_id, db=db) if segmented else None
    departure_instance_id = departure_instance.id if departure_instance else None
    departure = departure_instance.departure if departure_instance else None
    _sync_trip_vehicle_statuses(
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    vehicle_query = db.query(TripVehicle).filter(TripVehicle.product_id == product.id)
    active_vehicle = None
    if trip_vehicle_id:
        active_vehicle = vehicle_query.filter(TripVehicle.id == trip_vehicle_id).first()
    if not active_vehicle:
        active_vehicle = _resolve_active_trip_vehicle(product, db)
    if not active_vehicle:
        raise HTTPException(status_code=409, detail="Nenhum veiculo disponivel para selecao no momento.")
    if not active_vehicle.is_active or active_vehicle.status != TripVehicleStatus.active.value:
        raise HTTPException(status_code=409, detail="Veiculo informado ainda nao esta liberado para selecao.")
    if segmented and departure_instance and active_vehicle.layout and not _trip_seat_records(
        product,
        db,
        trip_vehicle_id=active_vehicle.id,
        departure_instance_id=departure_instance_id,
    ):
        _generate_trip_vehicle_seats(
            product,
            active_vehicle,
            active_vehicle.layout,
            db,
            force=True,
            departure_instance_id=departure_instance_id,
        )
        db.commit()
    seats = _trip_seat_records(
        product,
        db,
        trip_vehicle_id=active_vehicle.id,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    if not seats:
        raise HTTPException(status_code=409, detail="Mapa de assentos nao foi configurado para este veiculo.")
    layout = _serialize_layout_detail(active_vehicle.layout) if active_vehicle.layout else None
    passengers_query = (
        db.query(SalePassenger)
        .options(joinedload(SalePassenger.passenger_group).joinedload(PassengerGroup.sale_item))
        .filter(
            SalePassenger.sale_id == sale.id,
            SalePassenger.type != PassengerType.child_free.value,
        )
    )
    if segmented and departure is not None:
        passengers_query = (
            passengers_query.join(PassengerGroup, PassengerGroup.id == SalePassenger.passenger_group_id)
            .join(SaleItem, SaleItem.id == PassengerGroup.sale_item_id)
            .filter(SaleItem.departure_id == departure.id)
        )
    passengers = passengers_query.all()
    assignment_map = _passenger_assignment_map(
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    passenger_items = [_passenger_summary(passenger, assignment_map) for passenger in passengers]
    stats = _seat_stats(seats, passenger_items)
    reference = sale.provider_charge_id or sale.product_public_id or str(sale.id)
    vehicle_options = [
        vehicle
        for vehicle in _trip_vehicle_summaries(
            product.id,
            db,
            departure_instance_id=departure_instance_id if segmented else None,
        )
        if vehicle.is_active and vehicle.status == TripVehicleStatus.active.value
    ]
    return SeatSelectionContext(
        product_id=product.id,
        product_name=product.name,
        product_public_id=product.public_id,
        trip_date=product.trip_date,
        departure_instance_id=departure_instance_id,
        departure_id=departure.id if departure else None,
        departure_date=departure.date if departure else None,
        departure_time=_departure_time_str(departure),
        trip_vehicle=_trip_vehicle_snapshot(
            active_vehicle,
            db,
            departure_instance_id=departure_instance_id if segmented else None,
        ),
        vehicles=vehicle_options,
        layout=layout,
        seats=[_serialize_trip_seat(seat, current_sale_id=sale.id) for seat in seats],
        passengers=passenger_items,
        stats=stats,
        sale_id=sale.id,
        sale_reference=reference,
        boarding_notes=config.boarding_notes,
        can_assign=True,
        can_submit=True,
        message=None,
        preference_notice="Os assentos escolhidos podem sofrer ajustes operacionais pela agencia.",
    )


def _resolve_passenger_departure_id(passenger: SalePassenger, product: Product, db: Session) -> int | None:
    group = passenger.passenger_group
    if group and group.sale_item and group.sale_item.departure_id:
        return int(group.sale_item.departure_id)
    sale = passenger.sale
    if not sale:
        return None
    departure_ids = _sale_departure_ids(sale, db, product_id=product.id)
    if len(departure_ids) == 1:
        return departure_ids[0]
    if product.schedule_mode == ProductScheduleMode.recurring.value:
        raise HTTPException(status_code=400, detail="Passageiro sem saida definida para mapa de assentos.")
    return None


def _resolve_passenger_departure_instance(
    passenger: SalePassenger,
    product: Product,
    config: TripTransportConfig,
    db: Session,
) -> TripDepartureInstance | None:
    if not _is_segmented_seat_map(product, config):
        return None
    departure_id = _resolve_passenger_departure_id(passenger, product, db)
    if departure_id is None:
        return None
    departure = _departure_for_product(product.id, departure_id, db)
    return _ensure_departure_instance(product, departure, db)


def _assignment_for_passenger(
    passenger_id: int,
    product_id: int,
    db: Session,
    departure_instance_id: int | None = None,
) -> SeatAssignment | None:
    query = db.query(SeatAssignment).filter(
        SeatAssignment.passenger_id == passenger_id,
        SeatAssignment.product_id == product_id,
    )
    if departure_instance_id is None:
        query = query.filter(SeatAssignment.departure_instance_id.is_(None))
    else:
        query = query.filter(SeatAssignment.departure_instance_id == departure_instance_id)
    return query.first()


def _seat_by_id(
    seat_id: int,
    product_id: int,
    db: Session,
    departure_instance_id: int | None = None,
) -> TripSeat:
    query = db.query(TripSeat).filter(
        TripSeat.id == seat_id,
        TripSeat.product_id == product_id,
    )
    if departure_instance_id is not None:
        query = query.filter(TripSeat.departure_instance_id == departure_instance_id)
    seat = query.first()
    if not seat:
        raise HTTPException(status_code=404, detail="Assento nao encontrado.")
    return seat


def _passenger_by_id(passenger_id: int, product: Product, db: Session, expected_sale_id: int | None = None) -> SalePassenger:
    passenger = (
        db.query(SalePassenger)
        .options(
            joinedload(SalePassenger.sale),
            joinedload(SalePassenger.passenger_group).joinedload(PassengerGroup.sale_item),
        )
        .filter(SalePassenger.id == passenger_id)
        .first()
    )
    if not passenger:
        raise HTTPException(status_code=404, detail="Passageiro nao encontrado.")
    sale = passenger.sale
    group = passenger.passenger_group
    group_product_id = group.product_id if group else None
    group_item_product_id = group.sale_item.product_id if group and group.sale_item else None
    belongs_to_product = bool(
        sale
        and (
            sale.product_id == product.id
            or sale.product_public_id == product.public_id
            or group_product_id == product.id
            or group_item_product_id == product.id
        )
    )
    if not belongs_to_product:
        raise HTTPException(status_code=404, detail="Passageiro nao pertence a esta viagem.")
    if expected_sale_id and sale.id != expected_sale_id:
        raise HTTPException(status_code=404, detail="Passageiro nao pertence a este pedido.")
    if passenger.type == PassengerType.child_free.value:
        raise HTTPException(status_code=400, detail="Passageiro sem assento proprio.")
    return passenger


def _log_seat_change(
    product_id: int,
    passenger: SalePassenger | None,
    sale_id: int | None,
    old_seat_id: int | None,
    new_seat_id: int | None,
    role: SeatChangeActorRole | str,
    user_id: int | None,
    reason: str | None,
    db: Session,
    trip_vehicle_id: int | None = None,
    departure_instance_id: int | None = None,
) -> None:
    log = SeatChangeLog(
        product_id=product_id,
        departure_instance_id=departure_instance_id,
        passenger_id=passenger.id if passenger else None,
        sale_id=sale_id,
        old_seat_id=old_seat_id,
        new_seat_id=new_seat_id,
        changed_by_user_id=user_id,
        changed_by_role=role.value if isinstance(role, SeatChangeActorRole) else role,
        reason=reason,
        trip_vehicle_id=trip_vehicle_id,
    )
    db.add(log)


def assign_seat_to_passenger(
    product: Product,
    payload: SeatAssignmentPayload,
    actor: SeatAssignmentActor,
    db: Session,
    user: User | None = None,
    notes: str | None = None,
    status_override: str | None = None,
    expected_sale_id: int | None = None,
) -> SeatAssignment:
    config = _ensure_trip_config(product, db)
    segmented = _is_segmented_seat_map(product, config)
    passenger = _passenger_by_id(payload.passenger_id, product, db, expected_sale_id=expected_sale_id)
    departure_instance = _resolve_passenger_departure_instance(passenger, product, config, db) if segmented else None
    departure_instance_id = departure_instance.id if departure_instance else None
    seat = _seat_by_id(payload.seat_id, product.id, db, departure_instance_id=departure_instance_id if segmented else None)
    if segmented and seat.departure_instance_id != departure_instance_id:
        raise HTTPException(status_code=400, detail="Assento informado pertence a outra saida.")
    if not seat.is_selectable or seat.is_blocked:
        raise HTTPException(status_code=400, detail="Assento indisponivel para selecao.")
    existing_assignment = _assignment_for_passenger(
        passenger.id,
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    if existing_assignment and existing_assignment.seat_id == seat.id:
        return existing_assignment
    occupant = seat.assignments[0] if seat.assignments else None
    if occupant and occupant.passenger_id != passenger.id:
        raise HTTPException(status_code=409, detail="Assento ja atribuido a outro passageiro.")
    if existing_assignment:
        db.delete(existing_assignment)
        _log_seat_change(
            product.id,
            passenger,
            passenger.sale_id,
            existing_assignment.seat_id,
            None,
            SeatChangeActorRole(actor.value),
            user.id if user else None,
            "Liberado para nova selecao",
            db,
            trip_vehicle_id=existing_assignment.trip_vehicle_id if existing_assignment else None,
            departure_instance_id=departure_instance_id if segmented else None,
        )
    assignment = SeatAssignment(
        product_id=product.id,
        departure_instance_id=departure_instance_id if segmented else None,
        seat_id=seat.id,
        passenger_id=passenger.id,
        sale_id=passenger.sale_id,
        trip_vehicle_id=seat.trip_vehicle_id,
        assigned_by=actor.value,
        assignment_status=status_override or SeatAssignmentStatus.selected_by_customer.value,
        notes=notes,
    )
    db.add(assignment)
    _log_seat_change(
        product.id,
        passenger,
        passenger.sale_id,
        existing_assignment.seat_id if existing_assignment else None,
        seat.id,
        SeatChangeActorRole(actor.value),
        user.id if user else None,
        notes,
        db,
        trip_vehicle_id=seat.trip_vehicle_id,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    db.flush()
    _sync_trip_vehicle_statuses(
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def drop_passenger_assignment(
    product: Product,
    passenger_id: int,
    actor: SeatAssignmentActor,
    db: Session,
    user: User | None = None,
    reason: str | None = None,
    expected_sale_id: int | None = None,
) -> None:
    config = _ensure_trip_config(product, db)
    segmented = _is_segmented_seat_map(product, config)
    passenger = _passenger_by_id(passenger_id, product, db, expected_sale_id=expected_sale_id)
    departure_instance = _resolve_passenger_departure_instance(passenger, product, config, db) if segmented else None
    departure_instance_id = departure_instance.id if departure_instance else None
    assignment = _assignment_for_passenger(
        passenger.id,
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    if not assignment:
        return
    old_seat_id = assignment.seat_id
    db.delete(assignment)
    _log_seat_change(
        product.id,
        passenger,
        passenger.sale_id,
        old_seat_id,
        None,
        SeatChangeActorRole(actor.value),
        user.id if user else None,
        reason or "Removido",
        db,
        trip_vehicle_id=assignment.trip_vehicle_id,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    db.flush()
    _sync_trip_vehicle_statuses(
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    db.commit()


def block_trip_seat(
    product: Product,
    payload: SeatBlockPayload,
    db: Session,
    user: User | None = None,
    departure_id: int | None = None,
) -> TripSeatOut:
    config = _ensure_trip_config(product, db)
    segmented = _is_segmented_seat_map(product, config)
    departure_instance = _resolve_admin_departure_instance(product, departure_id=departure_id, db=db) if segmented else None
    departure_instance_id = departure_instance.id if departure_instance else None
    seat = _seat_by_id(payload.seat_id, product.id, db, departure_instance_id=departure_instance_id if segmented else None)
    seat.is_blocked = payload.is_blocked
    db.add(seat)
    _log_seat_change(
        product.id,
        None,
        None,
        seat.id if payload.is_blocked else None,
        None if payload.is_blocked else seat.id,
        SeatChangeActorRole.admin,
        user.id if user else None,
        payload.reason,
        db,
        trip_vehicle_id=seat.trip_vehicle_id,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    _sync_trip_vehicle_statuses(
        product.id,
        db,
        departure_instance_id=departure_instance_id if segmented else None,
    )
    db.commit()
    db.refresh(seat)
    return _serialize_trip_seat(seat)


def list_seat_history(
    product: Product,
    limit: int,
    db: Session,
    departure_id: int | None = None,
) -> SeatHistoryResponse:
    config = _ensure_trip_config(product, db)
    segmented = _is_segmented_seat_map(product, config)
    departure_instance = _resolve_admin_departure_instance(product, departure_id=departure_id, db=db) if segmented else None
    departure_instance_id = departure_instance.id if departure_instance else None
    filters = [SeatChangeLog.product_id == product.id]
    if segmented:
        if departure_instance_id is None:
            filters.append(SeatChangeLog.departure_instance_id.is_not(None))
        else:
            filters.append(SeatChangeLog.departure_instance_id == departure_instance_id)
    else:
        filters.append(SeatChangeLog.departure_instance_id.is_(None))
    query = (
        db.query(SeatChangeLog)
        .options(
            joinedload(SeatChangeLog.passenger),
            joinedload(SeatChangeLog.old_seat),
            joinedload(SeatChangeLog.new_seat),
        )
        .filter(*filters)
        .order_by(SeatChangeLog.created_at.desc())
    )
    items = query.limit(limit + 1).all()
    has_more = len(items) > limit
    serialized = []
    for entry in items[:limit]:
        passenger_name = entry.passenger.name if entry.passenger else None
        serialized.append(
            SeatHistoryEntry(
                id=entry.id,
                passenger_id=entry.passenger_id,
                passenger_name=passenger_name,
                sale_id=entry.sale_id,
                old_seat_label=entry.old_seat.seat_label if entry.old_seat else None,
                new_seat_label=entry.new_seat.seat_label if entry.new_seat else None,
                changed_by_role=entry.changed_by_role,
                changed_by_user_id=entry.changed_by_user_id,
                reason=entry.reason,
                created_at=entry.created_at,
            )
        )
    return SeatHistoryResponse(items=serialized, has_more=has_more)
