from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.product import Product, ProductAccommodationMode, ProductVariation
from app.models.rooming import RoomingAssignment, RoomingRoom
from app.models.sale import Sale, SalePassenger
from app.models.sale_item import SaleItem
from app.models.passenger_group import PassengerGroup, PassengerType
from app.schemas.rooming import (
    AutoMatchApplyResponse,
    AutoMatchNewRoomPreview,
    AutoMatchPreviewResponse,
    AutoMatchPreviewSummary,
    AutoMatchFillPreview,
    RoomAssignmentPayload,
    RoomingAccommodationOption,
    RoomingAccommodationSection,
    RoomingAlert,
    RoomingListResponse,
    RoomingPassenger,
    RoomingProductSummary,
    RoomingRoomOut,
    RoomingRoomPayload,
    RoomingStats,
)


def _sale_product_filter(product: Product) -> object:
    return or_(Sale.product_id == product.id, Sale.product_public_id == product.public_id)


def _sanitize_text(value: str | None, length: int = 120) -> str | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:length]


def _ensure_rooming_enabled(product: Product) -> None:
    if not getattr(product, "has_rooms", False):
        raise HTTPException(status_code=404, detail="Rooming nao habilitado para este produto.")


def _room_status(occupancy: int, capacity: int) -> str:
    if occupancy <= 0:
        return "empty"
    if occupancy < capacity:
        return "incomplete"
    if occupancy == capacity:
        return "complete"
    return "conflict"


@dataclass
class PassengerProfile:
    accommodation_key: str | None
    capacity_required: int | None
    is_private: bool
    consumes_capacity: bool


def _passenger_profile(passenger: SalePassenger) -> PassengerProfile:
    group = passenger.passenger_group
    sale_item = group.sale_item if group else None
    accommodation_key = None
    capacity_required = None
    is_private = False
    consumes_capacity = True
    if sale_item:
        fallback_capacity = sale_item.room_capacity or sale_item.people_count or 1
        accommodation_key = sale_item.variation_public_id or f"capacity:{fallback_capacity}"
        capacity_required = group.capacity if group and group.capacity else fallback_capacity
        is_private = sale_item.accommodation_mode == ProductAccommodationMode.private.value
    if passenger.type == PassengerType.child_free.value:
        consumes_capacity = False
    normalized_key = accommodation_key[:64] if accommodation_key else None
    return PassengerProfile(
        accommodation_key=normalized_key,
        capacity_required=capacity_required,
        is_private=is_private,
        consumes_capacity=consumes_capacity,
    )


def _serialize_passenger(passenger: SalePassenger, assigned_room_id: int | None) -> RoomingPassenger:
    sale = passenger.sale
    if not sale:
        raise HTTPException(status_code=404, detail="Venda do passageiro não encontrada.")
    group = passenger.passenger_group
    sale_item = group.sale_item if group else None
    profile = _passenger_profile(passenger)
    reference = sale.provider_charge_id or sale.product_public_id or str(sale.id)
    return RoomingPassenger(
        id=passenger.id,
        name=passenger.name or "Passageiro sem nome",
        passenger_type=passenger.type,
        sale_id=sale.id,
        sale_reference=reference,
        order_code=str(sale.id),
        passenger_group_label=group.label if group else None,
        variation_name=sale_item.variation_name if sale_item else None,
        boarding_location=passenger.boarding_location,
        assigned_room_id=assigned_room_id,
        accommodation_key=profile.accommodation_key,
        capacity_required=profile.capacity_required,
        is_private=profile.is_private,
        consumes_capacity=profile.consumes_capacity,
    )


def _serialize_room(room: RoomingRoom) -> RoomingRoomOut:
    passengers: list[RoomingPassenger] = []
    for assignment in room.assignments or []:
        if not assignment.passenger:
            continue
        passengers.append(_serialize_passenger(assignment.passenger, room.id))
    occupancy = sum(1 for passenger in passengers if passenger.consumes_capacity)
    variation_public_id = room.variation.public_id if room.variation else None
    accommodation_label = room.accommodation_label or (room.variation.name if room.variation else None)
    return RoomingRoomOut(
        id=room.id,
        name=room.name,
        accommodation_label=accommodation_label,
        accommodation_key=room.accommodation_key,
        variation_public_id=variation_public_id,
        capacity=room.capacity,
        occupancy=occupancy,
        status=_room_status(occupancy, room.capacity),
        passengers=passengers,
        locked=bool(room.locked),
        is_private=bool(room.is_private),
        origin=room.origin,
        sale_id=room.sale_id,
    )


def _room_capacity_usage(room: RoomingRoom) -> int:
    usage = 0
    for assignment in room.assignments or []:
        passenger = assignment.passenger
        if not passenger:
            continue
        profile = _passenger_profile(passenger)
        if profile.consumes_capacity:
            usage += 1
    return usage


def _room_has_space_for(room: RoomingRoom, passenger: SalePassenger) -> bool:
    profile = _passenger_profile(passenger)
    if not profile.consumes_capacity:
        return True
    return _room_capacity_usage(room) < room.capacity


def _assert_room_accepts_passenger(room: RoomingRoom, passenger: SalePassenger) -> None:
    profile = _passenger_profile(passenger)
    if profile.accommodation_key and profile.accommodation_key != room.accommodation_key:
        raise HTTPException(status_code=400, detail="Tipo de acomoda��ǜo incompat��vel com o quarto selecionado.")
    if room.is_private and room.sale_id and room.sale_id != passenger.sale_id:
        raise HTTPException(status_code=400, detail="Quarto privativo reservado para outro pedido.")


def _build_accommodation_catalog(
    product: Product,
    rooms: list[RoomingRoom],
) -> dict[str, RoomingAccommodationOption]:
    catalog: dict[str, RoomingAccommodationOption] = {}
    for variation in product.variations or []:
        if not getattr(variation, "has_accommodation", False):
            continue
        catalog[variation.public_id] = RoomingAccommodationOption(
            key=variation.public_id,
            label=variation.name,
            capacity=variation.room_capacity or variation.people_included or 1,
            variation_public_id=variation.public_id,
            product_room_id=None,
        )
    for template in sorted(product.rooms or [], key=lambda entry: entry.capacity):
        key = f"template:{template.id}"
        catalog[key] = RoomingAccommodationOption(
            key=key,
            label=template.name,
            capacity=template.capacity or 1,
            variation_public_id=None,
            product_room_id=template.id,
        )
    for room in rooms:
        key = room.accommodation_key
        if key in catalog:
            continue
        label = room.accommodation_label or (room.variation.name if room.variation else f"{room.capacity} pessoas")
        variation_public_id = room.variation.public_id if room.variation else None
        catalog[key] = RoomingAccommodationOption(
            key=key,
            label=label,
            capacity=room.capacity,
            variation_public_id=variation_public_id,
            product_room_id=None,
        )
    return catalog


def _fetch_rooms(product: Product, db: Session) -> list[RoomingRoom]:
    return (
        db.query(RoomingRoom)
        .options(
            joinedload(RoomingRoom.variation),
            selectinload(RoomingRoom.assignments)
            .joinedload(RoomingAssignment.passenger)
            .joinedload(SalePassenger.sale),
            selectinload(RoomingRoom.assignments)
            .joinedload(RoomingAssignment.passenger)
            .joinedload(SalePassenger.passenger_group)
            .joinedload(PassengerGroup.sale_item),
        )
        .filter(RoomingRoom.product_id == product.id)
        .order_by(RoomingRoom.created_at.asc(), RoomingRoom.id.asc())
        .all()
    )


def _fetch_passengers(product: Product, db: Session) -> list[SalePassenger]:
    return (
        db.query(SalePassenger)
        .join(Sale)
        .options(
            joinedload(SalePassenger.sale),
            joinedload(SalePassenger.passenger_group)
            .joinedload(PassengerGroup.sale_item)
            .joinedload(SaleItem.variation),
        )
        .filter(_sale_product_filter(product))
        .order_by(Sale.id.asc(), SalePassenger.id.asc())
        .all()
    )


def _passenger_requires_rooming(passenger: SalePassenger) -> bool:
    group = passenger.passenger_group
    if not group:
        return False
    sale_item = group.sale_item
    return bool(sale_item and _item_has_accommodation(sale_item))


def _rooming_passengers(product: Product, db: Session) -> list[SalePassenger]:
    passengers = _fetch_passengers(product, db)
    return [passenger for passenger in passengers if _passenger_requires_rooming(passenger)]


def _rooms_by_key(serialized_rooms: list[RoomingRoomOut]) -> dict[str, list[RoomingRoomOut]]:
    mapping: dict[str, list[RoomingRoomOut]] = defaultdict(list)
    for room in serialized_rooms:
        mapping[room.accommodation_key].append(room)
    return mapping


def _status_summary(rooms: list[RoomingRoomOut]) -> dict[str, int]:
    summary = {"empty": 0, "incomplete": 0, "complete": 0, "conflict": 0}
    for room in rooms:
        summary[room.status] = summary.get(room.status, 0) + 1
    return summary


def _build_alerts(stats: RoomingStats) -> list[RoomingAlert]:
    alerts: list[RoomingAlert] = []
    if stats.passengers_without_room:
        alerts.append(
            RoomingAlert(
                id="pending-passengers",
                message=f"{stats.passengers_without_room} passageiro(s) aguardando alocação.",
                tone="warning",
            )
        )
    if stats.rooms_incomplete:
        alerts.append(
            RoomingAlert(
                id="rooms-incomplete",
                message=f"{stats.rooms_incomplete} quarto(s) com vagas disponíveis.",
                tone="warning",
            )
        )
    if stats.rooms_conflict:
        alerts.append(
            RoomingAlert(
                id="rooms-conflict",
                message=f"{stats.rooms_conflict} quarto(s) acima da capacidade.",
                tone="danger",
            )
        )
    if not alerts:
        alerts.append(RoomingAlert(id="rooming-ok", message="Todas as alocações estão atualizadas.", tone="neutral"))
    return alerts


def get_rooming_list(product: Product, db: Session) -> RoomingListResponse:
    _ensure_rooming_enabled(product)
    _ensure_private_rooms(product, db)
    rooms = _fetch_rooms(product, db)
    serialized_rooms = [_serialize_room(room) for room in rooms]
    passengers = _rooming_passengers(product, db)
    assignment_map = {
        assignment.passenger_id: room.id
        for room in rooms
        for assignment in room.assignments
        if assignment.passenger_id
    }
    pending_passengers = [
        _serialize_passenger(passenger, assignment_map.get(passenger.id)) for passenger in passengers if passenger.id
    ]
    assigned_count = sum(1 for passenger in pending_passengers if passenger.assigned_room_id)
    unassigned = [p for p in pending_passengers if not p.assigned_room_id]

    stats = RoomingStats(
        total_passengers=len(pending_passengers),
        passengers_with_room=assigned_count,
        passengers_without_room=len(unassigned),
        total_rooms=len(serialized_rooms),
        rooms_complete=sum(1 for room in serialized_rooms if room.status == "complete"),
        rooms_incomplete=sum(1 for room in serialized_rooms if room.status == "incomplete"),
        rooms_empty=sum(1 for room in serialized_rooms if room.status == "empty"),
        rooms_conflict=sum(1 for room in serialized_rooms if room.status == "conflict"),
    )

    catalog = _build_accommodation_catalog(product, rooms)
    rooms_map = _rooms_by_key(serialized_rooms)
    sections: list[RoomingAccommodationSection] = []
    for key, option in sorted(
        catalog.items(),
        key=lambda entry: (entry[1].capacity, entry[1].label.lower()),
    ):
        section_rooms = rooms_map.get(key, [])
        sections.append(
            RoomingAccommodationSection(
                key=key,
                label=option.label,
                capacity=option.capacity,
                variation_public_id=option.variation_public_id,
                rooms=section_rooms,
                status_summary=_status_summary(section_rooms),
            )
        )

    product_summary = RoomingProductSummary(
        id=product.id,
        public_id=product.public_id,
        name=product.name,
        trip_date=product.trip_date.isoformat() if product.trip_date else None,
    )

    options = sorted(catalog.values(), key=lambda option: (option.capacity, option.label.lower()))
    return RoomingListResponse(
        product=product_summary,
        stats=stats,
        accommodations=sections,
        pending_passengers=unassigned,
        alerts=_build_alerts(stats),
        options=options,
    )


def _find_variation(product: Product, public_id: str) -> ProductVariation | None:
    for variation in product.variations or []:
        if variation.public_id == public_id:
            return variation
    return None


def _next_room_name(product: Product, accommodation_key: str, label: str, db: Session) -> str:
    count = (
        db.query(RoomingRoom)
        .filter(RoomingRoom.product_id == product.id, RoomingRoom.accommodation_key == accommodation_key)
        .count()
    )
    return f"{label} #{count + 1}"


def create_room(product: Product, payload: RoomingRoomPayload, db: Session) -> RoomingRoomOut:
    _ensure_rooming_enabled(product)
    variation = None
    label = _sanitize_text(payload.accommodation_label) if payload.accommodation_label else None
    capacity = payload.capacity or 0
    template = None
    if payload.product_room_id:
        template = next((entry for entry in product.rooms or [] if entry.id == payload.product_room_id), None)
        if not template:
            raise HTTPException(status_code=404, detail="Configuração de quarto não encontrada.")
        capacity = template.capacity or 1
        label = label or template.name
    if payload.variation_public_id:
        variation = _find_variation(product, payload.variation_public_id)
        if not variation:
            raise HTTPException(status_code=404, detail="Tipo de acomodação não encontrado.")
        capacity = variation.room_capacity or variation.people_included or 1
        label = label or variation.name
    if capacity <= 0:
        raise HTTPException(status_code=400, detail="Capacidade do quarto inválida.")
    label = label or f"{capacity} pessoas"
    if variation:
        accommodation_key = variation.public_id
    elif template:
        accommodation_key = f"template:{template.id}"
    else:
        accommodation_key = f"capacity:{capacity}"
    name = _sanitize_text(payload.label) or _next_room_name(product, accommodation_key, label, db)
    room = RoomingRoom(
        product_id=product.id,
        variation_id=variation.id if variation else None,
        name=name,
        accommodation_label=label,
        accommodation_key=accommodation_key[:64],
        capacity=capacity,
        is_private=bool(template.is_private) if template else False,
        locked=False,
        origin=None,
    )
    metadata: dict[str, object] = dict(room.metadata_json or {})
    if template:
        metadata["product_room_id"] = template.id
    room.metadata_json = metadata or None
    db.add(room)
    db.commit()
    return _serialize_room(_load_room_with_assignments(product.id, room.id, db))


def _load_room_with_assignments(product_id: int, room_id: int, db: Session) -> RoomingRoom:
    room = (
        db.query(RoomingRoom)
        .options(
            joinedload(RoomingRoom.variation),
            selectinload(RoomingRoom.assignments)
            .joinedload(RoomingAssignment.passenger)
            .joinedload(SalePassenger.sale),
            selectinload(RoomingRoom.assignments)
            .joinedload(RoomingAssignment.passenger)
            .joinedload(SalePassenger.passenger_group)
            .joinedload(PassengerGroup.sale_item),
        )
        .filter(RoomingRoom.id == room_id, RoomingRoom.product_id == product_id)
        .first()
    )
    if not room:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")
    return room


def assign_passenger(
    product: Product,
    room_id: int,
    payload: RoomAssignmentPayload,
    db: Session,
) -> RoomingRoomOut:
    _ensure_rooming_enabled(product)
    room = _load_room_with_assignments(product.id, room_id, db)
    if room.locked:
        raise HTTPException(status_code=400, detail="Este quarto estǭ bloqueado para altera��ǜes.")
    passenger = (
        db.query(SalePassenger)
        .join(Sale)
        .filter(SalePassenger.id == payload.passenger_id, _sale_product_filter(product))
        .first()
    )
    if not passenger:
        raise HTTPException(status_code=404, detail="Passageiro não encontrado para este produto.")
    if not _room_has_space_for(room, passenger):
        raise HTTPException(status_code=400, detail="Capacidade máxima do quarto atingida.")
    existing_assignment = (
        db.query(RoomingAssignment)
        .join(RoomingRoom, RoomingAssignment.room_id == RoomingRoom.id)
        .filter(RoomingAssignment.passenger_id == passenger.id, RoomingRoom.product_id == product.id)
        .first()
    )
    if existing_assignment:
        if existing_assignment.room_id == room.id:
            return _serialize_room(room)
        db.delete(existing_assignment)
        db.flush()
    db.add(RoomingAssignment(room_id=room.id, passenger_id=passenger.id))
    db.commit()
    return _serialize_room(_load_room_with_assignments(product.id, room.id, db))


def remove_passenger(product: Product, room_id: int, passenger_id: int, db: Session) -> RoomingRoomOut:
    _ensure_rooming_enabled(product)
    room = _load_room_with_assignments(product.id, room_id, db)
    if room.locked:
        raise HTTPException(status_code=400, detail="Este quarto estǭ bloqueado para altera��ǜes.")
    assignment = next((entry for entry in room.assignments if entry.passenger_id == passenger_id), None)
    if not assignment:
        assignment = (
            db.query(RoomingAssignment)
            .join(RoomingRoom, RoomingAssignment.room_id == RoomingRoom.id)
            .filter(
                RoomingAssignment.passenger_id == passenger_id,
                RoomingAssignment.room_id == room.id,
                RoomingRoom.product_id == product.id,
            )
            .first()
        )
    if not assignment:
        raise HTTPException(status_code=404, detail="Passageiro não está alocado neste quarto.")
    db.delete(assignment)
    db.commit()
    return _serialize_room(_load_room_with_assignments(product.id, room.id, db))


def rename_room(product: Product, room_id: int, name: str, db: Session) -> RoomingRoomOut:
    _ensure_rooming_enabled(product)
    room = _load_room_with_assignments(product.id, room_id, db)
    new_name = _sanitize_text(name, 120)
    if not new_name:
        raise HTTPException(status_code=400, detail="Nome do quarto inválido.")
    room.name = new_name
    metadata = dict(room.metadata_json or {})
    metadata["custom_name"] = new_name
    room.metadata_json = metadata
    db.add(room)
    db.commit()
    return _serialize_room(_load_room_with_assignments(product.id, room.id, db))


def preview_auto_match(product: Product, db: Session) -> AutoMatchPreviewResponse:
    _ensure_rooming_enabled(product)
    plan = _build_auto_match_plan(product, db)
    return AutoMatchPreviewResponse(
        preview_token=plan.preview_token,
        summary=plan.summary(),
        fills=[
            AutoMatchFillPreview(
                room_id=fill.room.id,
                room_name=fill.room.name,
                before=len(fill.room.assignments or []),
                after=len(fill.room.assignments or []) + len(fill.passengers),
                capacity=fill.room.capacity,
                passengers_added=[info.serialized for info in fill.passengers],
            )
            for fill in plan.fills
        ],
        new_rooms=[
            AutoMatchNewRoomPreview(
                room_type_key=new_room.accommodation_key,
                room_label=new_room.display_label,
                capacity=new_room.capacity,
                passengers=[info.serialized for info in new_room.passengers],
            )
            for new_room in plan.new_rooms
        ],
        remaining_unassigned=[info.serialized for info in plan.remaining],
    )


def apply_auto_match(product: Product, preview_token: str, db: Session) -> AutoMatchApplyResponse:
    _ensure_rooming_enabled(product)
    plan = _build_auto_match_plan(product, db)
    if plan.preview_token != preview_token:
        raise HTTPException(
            status_code=409,
            detail="A rooming list mudou desde a prévia. Gere uma nova simulação antes de aplicar.",
        )
    if not plan.fills and not plan.new_rooms:
        return AutoMatchApplyResponse(summary=plan.summary())
    for fill in plan.fills:
        room = _load_room_with_assignments(product.id, fill.room.id, db)
        for info in fill.passengers:
            _clear_existing_assignment(product.id, info.passenger.id, db, allow_locked=False)
            db.add(RoomingAssignment(room_id=room.id, passenger_id=info.passenger.id))
    for new_room in plan.new_rooms:
        label = new_room.label or f"{new_room.capacity} pessoas"
        name = _next_room_name(product, new_room.accommodation_key, label, db)
        room = RoomingRoom(
            product_id=product.id,
            variation_id=new_room.variation_id,
            name=name[:120],
            accommodation_label=label,
            accommodation_key=new_room.accommodation_key[:64],
            capacity=new_room.capacity,
            is_private=False,
            locked=False,
            origin="auto_shared",
        )
        db.add(room)
        db.flush()
        for info in new_room.passengers:
            _clear_existing_assignment(product.id, info.passenger.id, db, allow_locked=False)
            db.add(RoomingAssignment(room_id=room.id, passenger_id=info.passenger.id))
    db.commit()
    return AutoMatchApplyResponse(summary=plan.summary())


@dataclass
class PrivateRoomTarget:
    sale: Sale
    group: PassengerGroup | None
    item: SaleItem
    passengers: list[SalePassenger]
    capacity: int
    label: str
    accommodation_key: str


@dataclass
class PassengerMatchInfo:
    passenger: SalePassenger
    serialized: RoomingPassenger
    accommodation_key: str
    capacity: int
    variation_id: int | None
    label: str


@dataclass
class AutoMatchFillPlan:
    room: RoomingRoom
    passengers: list[PassengerMatchInfo]


@dataclass
class AutoMatchNewRoomPlan:
    accommodation_key: str
    capacity: int
    variation_id: int | None
    label: str
    display_label: str
    passengers: list[PassengerMatchInfo]


@dataclass
class AutoMatchPlan:
    preview_token: str
    fills: list[AutoMatchFillPlan]
    new_rooms: list[AutoMatchNewRoomPlan]
    remaining: list[PassengerMatchInfo]
    pending_total: int

    def summary(self) -> AutoMatchPreviewSummary:
        allocated = sum(len(fill.passengers) for fill in self.fills) + sum(
            len(room.passengers) for room in self.new_rooms
        )
        pending_after = max(0, self.pending_total - allocated)
        return AutoMatchPreviewSummary(
            pending_before=self.pending_total,
            pending_after=pending_after,
            passengers_to_allocate=allocated,
            rooms_to_complete=sum(1 for fill in self.fills if fill.passengers),
            rooms_to_create=len(self.new_rooms),
        )


def _ensure_private_rooms(product: Product, db: Session) -> None:
    sales = (
        db.query(Sale)
        .options(
            selectinload(Sale.items).selectinload(SaleItem.variation),
            selectinload(Sale.passengers),
            selectinload(Sale.passenger_groups)
            .selectinload(PassengerGroup.passengers),
            selectinload(Sale.passenger_groups)
            .selectinload(PassengerGroup.sale_item),
        )
        .filter(_sale_product_filter(product))
        .all()
    )
    rooms = (
        db.query(RoomingRoom)
        .filter(RoomingRoom.product_id == product.id, RoomingRoom.is_private.is_(True))
        .all()
    )
    room_map: dict[tuple[int | None, int | None], RoomingRoom] = {
        (room.sale_id, room.passenger_group_id): room for room in rooms
    }
    changed = False
    target_keys: set[tuple[int | None, int | None]] = set()
    for sale in sales:
        targets = _private_targets_for_sale(sale)
        if not targets:
            continue
        for target in targets:
            key = (sale.id, target.group.id if target.group else None)
            target_keys.add(key)
            room = room_map.get(key)
            if not room:
                room = _create_private_room(product, target, db)
                room_map[key] = room
                changed = True
            if _update_private_room(room, target, db):
                changed = True
            if _sync_room_passengers(room, target.passengers, db):
                changed = True
    for room_key, room in list(room_map.items()):
        if room.origin == "auto_privativo" and room_key not in target_keys:
            db.query(RoomingAssignment).filter(RoomingAssignment.room_id == room.id).delete(synchronize_session=False)
            db.delete(room)
            changed = True
    if changed:
        db.commit()


def _load_rooming_state(product: Product, db: Session) -> tuple[list[RoomingRoom], list[SalePassenger], dict[int, RoomingPassenger]]:
    rooms = _fetch_rooms(product, db)
    passengers = _rooming_passengers(product, db)
    assignment_map = {
        assignment.passenger_id: room.id
        for room in rooms
        for assignment in room.assignments
        if assignment.passenger_id
    }
    serialized_map: dict[int, RoomingPassenger] = {}
    for passenger in passengers:
        serialized_map[passenger.id] = _serialize_passenger(passenger, assignment_map.get(passenger.id))
    return rooms, passengers, serialized_map


def _generate_snapshot_token(rooms: list[RoomingRoom], pending_infos: list[PassengerMatchInfo]) -> str:
    payload = {
        "rooms": [
            {
                "id": room.id,
                "occupancy": _room_capacity_usage(room),
                "updated_at": room.updated_at.isoformat() if room.updated_at else None,
                "locked": bool(room.locked),
            }
            for room in rooms
        ],
        "pending": sorted(info.passenger.id for info in pending_infos if info.passenger.id),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _build_auto_match_plan(product: Product, db: Session) -> AutoMatchPlan:
    rooms, passengers, serialized_map = _load_rooming_state(product, db)
    shared_pending: list[PassengerMatchInfo] = []
    for passenger in passengers:
        serialized = serialized_map[passenger.id]
        if serialized.assigned_room_id:
            continue
        if serialized.is_private or not serialized.accommodation_key:
            continue
        if not serialized.consumes_capacity:
            continue
        capacity = serialized.capacity_required or 1
        if capacity <= 0:
            capacity = 1
        variation_id = None
        label = serialized.variation_name or serialized.passenger_group_label or f"{capacity} pessoas"
        group = passenger.passenger_group
        sale_item = group.sale_item if group else None
        if sale_item:
            variation_id = sale_item.variation_id
            if not label:
                label = sale_item.variation_name or label
        shared_pending.append(
            PassengerMatchInfo(
                passenger=passenger,
                serialized=serialized,
                accommodation_key=serialized.accommodation_key,
                capacity=capacity,
                variation_id=variation_id,
                label=label,
            )
        )
    pending_total = len(shared_pending)
    rooms_by_key: dict[str, list[RoomingRoom]] = defaultdict(list)
    for room in rooms:
        if room.is_private or room.locked:
            continue
        rooms_by_key[room.accommodation_key].append(room)
    passengers_by_key: dict[str, list[PassengerMatchInfo]] = defaultdict(list)
    for info in shared_pending:
        passengers_by_key[info.accommodation_key].append(info)
    fills: list[AutoMatchFillPlan] = []
    new_rooms: list[AutoMatchNewRoomPlan] = []
    remaining: list[PassengerMatchInfo] = []
    for key, original_list in passengers_by_key.items():
        passengers_list = list(original_list)
        passengers_list.sort(key=lambda info: info.passenger.id)
        rooms_for_key = sorted(
            rooms_by_key.get(key, []),
            key=lambda room: _room_capacity_usage(room),
            reverse=True,
        )
        for room in rooms_for_key:
            available = room.capacity - _room_capacity_usage(room)
            if available <= 0 or not passengers_list:
                continue
            selected = passengers_list[:available]
            passengers_list = passengers_list[available:]
            fills.append(AutoMatchFillPlan(room=room, passengers=selected))
        if not passengers_list:
            continue
        capacity = passengers_list[0].capacity
        if capacity <= 0:
            capacity = 1
        while len(passengers_list) >= capacity:
            chunk = passengers_list[:capacity]
            passengers_list = passengers_list[capacity:]
            base_label = chunk[0].label or f"{capacity} pessoas"
            display_label = f"Quarto {base_label}"
            new_rooms.append(
                AutoMatchNewRoomPlan(
                    accommodation_key=key,
                    capacity=capacity,
                    variation_id=chunk[0].variation_id,
                    label=base_label,
                    display_label=display_label,
                    passengers=chunk,
                )
            )
        if passengers_list:
            chunk = passengers_list[:]
            passengers_list = []
            base_label = chunk[0].label or f"{capacity} pessoas"
            display_label = f"Quarto {base_label}"
            if len(chunk) < capacity:
                display_label = f"{display_label} (incompleto)"
            new_rooms.append(
                AutoMatchNewRoomPlan(
                    accommodation_key=key,
                    capacity=capacity,
                    variation_id=chunk[0].variation_id,
                    label=base_label,
                    display_label=display_label,
                    passengers=chunk,
                )
            )
        remaining.extend(passengers_list)
    preview_token = _generate_snapshot_token(rooms, shared_pending)
    return AutoMatchPlan(
        preview_token=preview_token,
        fills=[fill for fill in fills if fill.passengers],
        new_rooms=new_rooms,
        remaining=remaining,
        pending_total=pending_total,
    )


def _private_targets_for_sale(sale: Sale) -> list[PrivateRoomTarget]:
    private_groups: list[PrivateRoomTarget] = []
    for group in sale.passenger_groups or []:
        item = group.sale_item
        if (
            not item
            or item.accommodation_mode != ProductAccommodationMode.private.value
            or not _item_has_accommodation(item)
        ):
            continue
        passengers = list(group.passengers or [])
        if not passengers:
            continue
        capacity = group.capacity or len(passengers) or 1
        label = group.label or item.variation_name or "Privativo"
        key = item.variation_public_id or f"group:{group.id}"
        private_groups.append(
            PrivateRoomTarget(
                sale=sale,
                group=group,
                item=item,
                passengers=passengers,
                capacity=capacity,
                label=label,
                accommodation_key=key,
            )
        )
    if private_groups:
        return private_groups
    base_item = _select_private_sale_item(sale)
    if not base_item:
        return []
    passengers = list(sale.passengers or [])
    if not passengers:
        return []
    capacity = _resolve_capacity(base_item, len(passengers))
    label = base_item.variation_name or "Privativo"
    key = base_item.variation_public_id or f"sale:{sale.id}"
    return [
        PrivateRoomTarget(
            sale=sale,
            group=None,
            item=base_item,
            passengers=passengers,
            capacity=capacity,
            label=label,
            accommodation_key=key,
        )
    ]


def _select_private_sale_item(sale: Sale) -> SaleItem | None:
    for item in sale.items or []:
        if (
            item.accommodation_mode == ProductAccommodationMode.private.value
            and _item_has_accommodation(item)
        ):
            return item
    return None


def _item_has_accommodation(item: SaleItem) -> bool:
    variation = getattr(item, "variation", None)
    if variation is not None:
        return bool(getattr(variation, "has_accommodation", False))
    return bool(getattr(item, "product_room_id", None))


def _create_private_room(product: Product, target: PrivateRoomTarget, db: Session) -> RoomingRoom:
    label = target.label
    key = target.accommodation_key
    name = f"{label} · Pedido #{target.sale.id}"
    room = RoomingRoom(
        product_id=product.id,
        variation_id=target.item.variation_id,
        sale_id=target.sale.id,
        passenger_group_id=target.group.id if target.group else None,
        name=name[:120],
        accommodation_label=label,
        accommodation_key=key[:64],
        capacity=target.capacity,
        is_private=True,
        locked=True,
        origin="auto_privativo",
    )
    db.add(room)
    db.flush()
    return room


def _update_private_room(room: RoomingRoom, target: PrivateRoomTarget, db: Session) -> bool:
    updated = False
    capacity = target.capacity
    label = target.label
    key = target.accommodation_key
    metadata = dict(room.metadata_json or {})
    custom_name = metadata.get("custom_name")
    expected_name = custom_name or (f"{label} · Pedido #{room.sale_id}" if room.sale_id else room.name)
    if room.passenger_group_id != (target.group.id if target.group else None):
        room.passenger_group_id = target.group.id if target.group else None
        updated = True
    if room.capacity != capacity:
        room.capacity = capacity
        updated = True
    if room.accommodation_label != label:
        room.accommodation_label = label
        updated = True
    if room.accommodation_key != key[:64]:
        room.accommodation_key = key[:64]
        updated = True
    if not custom_name and room.name != (expected_name[:120] if expected_name else room.name):
        room.name = (expected_name or room.name)[:120]
        updated = True
    if room.variation_id != target.item.variation_id:
        room.variation_id = target.item.variation_id
        updated = True
    if not room.is_private:
        room.is_private = True
        updated = True
    if not room.locked:
        room.locked = True
        updated = True
    if room.origin != "auto_privativo":
        room.origin = "auto_privativo"
        updated = True
    if metadata != (room.metadata_json or {}):
        room.metadata_json = metadata
        updated = True
    if updated:
        db.add(room)
    return updated


def _sync_room_passengers(room: RoomingRoom, passengers: list[SalePassenger], db: Session) -> bool:
    passenger_ids = {passenger.id for passenger in passengers if passenger.id}
    existing_assignments = {
        row[0]
        for row in db.query(RoomingAssignment.passenger_id).filter(RoomingAssignment.room_id == room.id).all()
    }
    changed = False
    to_remove = existing_assignments - passenger_ids
    if to_remove:
        db.query(RoomingAssignment).filter(
            RoomingAssignment.room_id == room.id,
            RoomingAssignment.passenger_id.in_(list(to_remove)),
        ).delete(synchronize_session=False)
        changed = True
        existing_assignments -= to_remove
    if not passenger_ids and existing_assignments:
        db.query(RoomingAssignment).filter(RoomingAssignment.room_id == room.id).delete(synchronize_session=False)
        return True
    for passenger in passengers:
        if not passenger.id or passenger.id in existing_assignments:
            continue
        db.query(RoomingAssignment).filter(
            RoomingAssignment.passenger_id == passenger.id,
            RoomingAssignment.room_id != room.id,
        ).delete(synchronize_session=False)
        db.add(RoomingAssignment(room_id=room.id, passenger_id=passenger.id))
        existing_assignments.add(passenger.id)
        changed = True
    return changed


def _resolve_capacity(item, fallback: int) -> int:
    for candidate in (
        item.room_capacity,
        getattr(item, "people_count", None),
        getattr(item, "slots_reserved", None),
    ):
        if isinstance(candidate, int) and candidate > 0:
            return candidate
    return max(1, fallback)


def _load_passenger_for_product(product: Product, passenger_id: int, db: Session) -> SalePassenger:
    passenger = (
        db.query(SalePassenger)
        .join(Sale)
        .filter(SalePassenger.id == passenger_id, _sale_product_filter(product))
        .options(
            joinedload(SalePassenger.sale),
            joinedload(SalePassenger.passenger_group).joinedload(PassengerGroup.sale_item),
        )
        .first()
    )
    if not passenger:
        raise HTTPException(status_code=404, detail="Passageiro não encontrado.")
    return passenger


def _clear_existing_assignment(product_id: int, passenger_id: int, db: Session, *, allow_locked: bool) -> None:
    assignment = (
        db.query(RoomingAssignment)
        .join(RoomingRoom)
        .filter(RoomingAssignment.passenger_id == passenger_id, RoomingRoom.product_id == product_id)
        .first()
    )
    if assignment:
        if assignment.room.locked and not allow_locked:
            raise HTTPException(status_code=400, detail="Não é possível remover o passageiro do quarto atual.")
        db.delete(assignment)


def move_passenger(product: Product, passenger_id: int, target_room_id: int, db: Session) -> RoomingRoomOut:
    _ensure_rooming_enabled(product)
    passenger = _load_passenger_for_product(product, passenger_id, db)
    room = _load_room_with_assignments(product.id, target_room_id, db)
    if room.locked:
        raise HTTPException(status_code=400, detail="Este quarto está bloqueado para alterações.")
    _assert_room_accepts_passenger(room, passenger)
    if not _room_has_space_for(room, passenger):
        raise HTTPException(status_code=400, detail="Quarto cheio. Utilize a troca de passageiros.")
    _clear_existing_assignment(product.id, passenger.id, db, allow_locked=False)
    db.add(RoomingAssignment(room_id=room.id, passenger_id=passenger.id))
    db.commit()
    return _serialize_room(_load_room_with_assignments(product.id, room.id, db))



def swap_passengers(
    product: Product,
    incoming_passenger_id: int,
    source_room_id: int,
    target_room_id: int,
    outgoing_passenger_id: int,
    db: Session,
) -> None:
    _ensure_rooming_enabled(product)
    if incoming_passenger_id == outgoing_passenger_id:
        raise HTTPException(status_code=400, detail="Selecione passageiros diferentes para a troca.")
    if source_room_id == target_room_id:
        raise HTTPException(status_code=400, detail="Selecione quartos de origem e destino diferentes.")
    incoming = _load_passenger_for_product(product, incoming_passenger_id, db)
    outgoing = _load_passenger_for_product(product, outgoing_passenger_id, db)
    target_room = _load_room_with_assignments(product.id, target_room_id, db)
    source_room = _load_room_with_assignments(product.id, source_room_id, db)
    if target_room.locked:
        raise HTTPException(status_code=400, detail="Este quarto está bloqueado para alterações.")
    if source_room.locked:
        raise HTTPException(status_code=400, detail="Não é possível remover o passageiro do quarto de origem.")
    occupancy = _room_capacity_usage(target_room)
    if occupancy < target_room.capacity:
        raise HTTPException(status_code=400, detail="Quarto possui vagas livres. Faça a alocação normal.")
    outgoing_assignment = next((a for a in target_room.assignments if a.passenger_id == outgoing_passenger_id), None)
    if not outgoing_assignment:
        raise HTTPException(status_code=400, detail="Passageiro escolhido não está neste quarto.")
    source_assignment = next((a for a in source_room.assignments if a.passenger_id == incoming_passenger_id), None)
    if not source_assignment:
        raise HTTPException(status_code=400, detail="Passageiro informado não está no quarto de origem.")
    _assert_room_accepts_passenger(target_room, incoming)
    _assert_room_accepts_passenger(source_room, outgoing)
    db.delete(source_assignment)
    db.delete(outgoing_assignment)
    db.add(RoomingAssignment(room_id=target_room.id, passenger_id=incoming_passenger_id))
    db.add(RoomingAssignment(room_id=source_room.id, passenger_id=outgoing_passenger_id))
    db.commit()


def replace_passenger(
    product: Product,
    incoming_passenger_id: int,
    target_room_id: int,
    outgoing_passenger_id: int,
    db: Session,
) -> None:
    _ensure_rooming_enabled(product)
    if incoming_passenger_id == outgoing_passenger_id:
        raise HTTPException(status_code=400, detail="Selecione passageiros diferentes para a troca.")
    incoming = _load_passenger_for_product(product, incoming_passenger_id, db)
    outgoing = _load_passenger_for_product(product, outgoing_passenger_id, db)
    target_room = _load_room_with_assignments(product.id, target_room_id, db)
    if target_room.locked:
        raise HTTPException(status_code=400, detail="Este quarto está bloqueado para alterações.")
    occupancy = _room_capacity_usage(target_room)
    if occupancy < target_room.capacity:
        raise HTTPException(status_code=400, detail="Quarto possui vagas livres. Faça a alocação normal.")
    outgoing_assignment = next((a for a in target_room.assignments if a.passenger_id == outgoing_passenger_id), None)
    if not outgoing_assignment:
        raise HTTPException(status_code=400, detail="Passageiro escolhido não está neste quarto.")
    existing_assignment = (
        db.query(RoomingAssignment)
        .join(RoomingRoom)
        .filter(RoomingAssignment.passenger_id == incoming_passenger_id, RoomingRoom.product_id == product.id)
        .first()
    )
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Este passageiro já está alocado em um quarto. Utilize a troca.")
    _assert_room_accepts_passenger(target_room, incoming)
    db.delete(outgoing_assignment)
    db.add(RoomingAssignment(room_id=target_room.id, passenger_id=incoming_passenger_id))
    db.commit()
