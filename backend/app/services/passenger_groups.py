from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Mapping, Sequence

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.passenger_group import PassengerGroup, PassengerGroupStatus, PassengerType
from app.models.sale import Sale, SalePassenger, SalePassengerStatus
from app.models.sale_item import SaleItem, SaleItemOccupancyStatus
from app.schemas.finance import (
    PassengerGroupOut,
    PassengerGroupPassengerInput,
    PassengerInput,
    SalePassengerOut,
)


def _trim(value: str | None, length: int) -> str | None:
    if value is None:
        return None
    return value[:length]


def _parse_birthdate(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Data de nascimento inválida.") from exc


def _unit_capacity(item: SaleItem) -> int:
    if item.occupancy and item.occupancy > 0:
        base_capacity = int(item.occupancy)
    else:
        base_capacity = max(int(item.slots_per_unit or 0), 0)
    if base_capacity <= 0:
        base_capacity = 1
    metadata = item.metadata_json or {}
    consumed_capacity = metadata.get("consumed_capacity")
    quantity = max(item.quantity or 0, 1)
    if isinstance(consumed_capacity, int) and consumed_capacity > 0:
        base = consumed_capacity // quantity
        if consumed_capacity % quantity:
            base += 1
        return max(base_capacity, base, 1)
    fallback = item.people_count or base_capacity
    if fallback <= 0:
        fallback = base_capacity
    per_unit = fallback // quantity if quantity else fallback
    if fallback % quantity:
        per_unit += 1
    return max(base_capacity, per_unit, 1)


def _slot_value(passenger: SalePassenger) -> int:
    if not passenger.name:
        return 0
    if passenger.type == PassengerType.child_free.value:
        return 0
    return 1


def _is_passenger_complete(passenger: SalePassenger) -> bool:
    return bool(passenger.name and passenger.cpf)


def _refresh_group_progress(group: PassengerGroup) -> None:
    occupied = sum(_slot_value(passenger) for passenger in group.passengers)
    group.occupied_slots = max(0, occupied)
    required_slots = len(_group_slot_types(group))
    completed_slots = sum(1 for passenger in group.passengers if _is_passenger_complete(passenger))
    if not group.passengers or completed_slots == 0:
        group.status = PassengerGroupStatus.pending.value
        return
    if group.occupied_slots >= group.capacity and completed_slots >= required_slots and all(
        _is_passenger_complete(p) for p in group.passengers
    ):
        group.status = PassengerGroupStatus.complete.value
    else:
        group.status = PassengerGroupStatus.partial.value


def _reserved_slots(item: SaleItem) -> int:
    if item.slots_reserved and item.slots_reserved > 0:
        return int(item.slots_reserved)
    metadata = item.metadata_json or {}
    consumed_capacity = metadata.get("consumed_capacity")
    if isinstance(consumed_capacity, int) and consumed_capacity > 0:
        return consumed_capacity
    if isinstance(consumed_capacity, str) and consumed_capacity.isdigit():
        return int(consumed_capacity)
    quantity = max(item.quantity or 0, 1)
    return max(0, _unit_capacity(item) * quantity)


def _sanitize_child_quantities(raw: Any) -> dict[str, int]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, int] = {}
    for key, value in raw.items():
        try:
            quantity = int(value)
        except (TypeError, ValueError):
            continue
        if quantity <= 0:
            continue
        result[str(key)] = quantity
    return result


def _distribute_child_plan(child_quantities: Mapping[str, int], quantity: int) -> list[dict[str, int]]:
    if quantity <= 0:
        return []
    plan: list[dict[str, int]] = [dict() for _ in range(quantity)]
    for key, total in child_quantities.items():
        base = total // quantity
        remainder = total % quantity
        for idx in range(quantity):
            assigned = base + (1 if idx < remainder else 0)
            if assigned <= 0:
                continue
            plan[idx][key] = assigned
    return plan


def _child_plan_entry(group: PassengerGroup) -> dict[str, int]:
    item = group.sale_item
    if not item:
        return {}
    metadata = item.metadata_json or {}
    quantity = max(item.quantity or 0, 1)
    plan: list[dict[str, int]] = []
    raw_plan = metadata.get("child_slots_plan")
    if isinstance(raw_plan, list):
        for entry in raw_plan:
            if isinstance(entry, Mapping):
                sanitized = _sanitize_child_quantities(entry)
                plan.append(sanitized)
    if not plan:
        quantities = _sanitize_child_quantities(metadata.get("child_quantities"))
        plan = _distribute_child_plan(quantities, quantity)
    if not plan:
        passengers_total = int(item.people_count or 0)
        seat_capacity_total = group.capacity * quantity
        extras_total = max(0, passengers_total - seat_capacity_total)
        if extras_total > 0:
            plan = _distribute_child_plan({"__fallback_child": extras_total}, quantity)
    if not plan:
        return {}
    index = max(0, min(group.group_index - 1, len(plan) - 1))
    return plan[index] or {}


def _group_slot_types(group: PassengerGroup) -> list[str]:
    slot_types: list[str] = [PassengerType.adult.value for _ in range(max(group.capacity, 0))]
    if not group.sale_item:
        return slot_types
    rules_snapshot = group.sale_item.children_rules_snapshot or group.children_rules_snapshot or []
    rules: dict[str, Mapping[str, Any]] = {}
    for raw_rule in rules_snapshot or []:
        if isinstance(raw_rule, Mapping):
            key = str(raw_rule.get("key") or "")
            if key:
                rules[key] = raw_rule
    child_entry = _child_plan_entry(group)
    for key, quantity in child_entry.items():
        rule = rules.get(key)
        if rule:
            if not rule.get("counts_as_passenger"):
                continue
            if rule.get("counts_towards_capacity"):
                # already accounted in base capacity
                continue
            passenger_type = (
                PassengerType.child_paid.value if (rule.get("pricing_mode") == "extra") else PassengerType.child_free.value
            )
        else:
            passenger_type = PassengerType.child_free.value
        for _ in range(max(0, int(quantity))):
            slot_types.append(passenger_type)
    return slot_types


def _group_slot_limit(group: PassengerGroup) -> int:
    return len(_group_slot_types(group))


def _refresh_sale_item_occupancy(item: SaleItem) -> None:
    reserved = _reserved_slots(item)
    occupied = sum(group.occupied_slots for group in item.passenger_groups or [])
    if reserved <= 0:
        item.occupancy_status = (
            SaleItemOccupancyStatus.complete.value if occupied > 0 else SaleItemOccupancyStatus.pending.value
        )
        return
    if occupied <= 0:
        item.occupancy_status = SaleItemOccupancyStatus.pending.value
    elif occupied >= reserved:
        item.occupancy_status = SaleItemOccupancyStatus.complete.value
    else:
        item.occupancy_status = SaleItemOccupancyStatus.partial.value


def compute_sale_passenger_status(sale: Sale) -> str:
    groups = list(sale.passenger_groups or [])
    if not groups:
        passengers = list(sale.passengers or [])
        if not passengers:
            return SalePassengerStatus.not_started.value
        if sale.passengers_required and len(passengers) >= sale.passengers_required:
            if all(_is_passenger_complete(p) for p in passengers):
                return SalePassengerStatus.completed.value
        return SalePassengerStatus.partial.value

    has_pending = any(group.status == PassengerGroupStatus.pending.value for group in groups)
    all_complete = all(group.status == PassengerGroupStatus.complete.value for group in groups)
    if all_complete and groups:
        return SalePassengerStatus.completed.value
    if has_pending and not any(group.passengers for group in groups):
        return SalePassengerStatus.not_started.value
    return SalePassengerStatus.partial.value


def ensure_passenger_groups(sale: Sale, db: Session) -> list[PassengerGroup]:
    if not sale.passengers_required:
        return []
    items = list(sale.items or [])
    if not items:
        return list(sale.passenger_groups or [])

    existing = {(group.sale_item_id, group.group_index): group for group in sale.passenger_groups or []}
    sort_index = 0
    for item in sorted(items, key=lambda entry: (entry.created_at or sale.created_at or 0, entry.id)):
        quantity = max(item.quantity or 0, 0)
        for idx in range(1, quantity + 1):
            sort_index += 1
            key = (item.id, idx)
            group = existing.get(key)
            if group:
                group.sort_order = sort_index
                continue
            label_base = item.variation_name or (item.product_public_id or "Pacote")
            group = PassengerGroup(
                sale_id=sale.id,
                sale_item_id=item.id,
                product_id=item.product_id,
                product_name_snapshot=label_base,
                group_index=idx,
                label=f"{label_base} {idx}",
                capacity=_unit_capacity(item),
                occupied_slots=0,
                sort_order=sort_index,
                allows_children=bool(item.allows_children),
                children_rules_snapshot=item.children_rules_snapshot,
            )
            sale.passenger_groups.append(group)
            db.add(group)

    db.flush()
    groups = sorted(sale.passenger_groups or [], key=lambda entry: (entry.sort_order, entry.id))
    for group in groups:
        _refresh_group_progress(group)
    for item in sale.items or []:
        _refresh_sale_item_occupancy(item)
        db.add(item)
    sale.passenger_status = compute_sale_passenger_status(sale)
    return groups


def serialize_passenger(passenger: SalePassenger) -> SalePassengerOut:
    return SalePassengerOut(
        id=passenger.id,
        passenger_group_id=passenger.passenger_group_id,
        passenger_index=passenger.passenger_index,
        type=passenger.type,
        name=passenger.name,
        cpf=passenger.cpf,
        birthdate=passenger.birthdate.isoformat() if passenger.birthdate else None,
        phone=passenger.phone,
        whatsapp=passenger.whatsapp,
        boarding_location=passenger.boarding_location,
        extras=passenger.extras,
    )


def serialize_passenger_group(group: PassengerGroup) -> PassengerGroupOut:
    passengers = sorted(group.passengers or [], key=lambda passenger: passenger.passenger_index or 0)
    return PassengerGroupOut(
        id=group.id,
        sale_item_id=group.sale_item_id,
        product_id=group.product_id,
        product_name=group.product_name_snapshot,
        label=group.label,
        group_index=group.group_index,
        capacity=group.capacity,
        occupied_slots=group.occupied_slots,
        status=group.status,
        allows_children=group.allows_children,
        slot_types=_group_slot_types(group),
        passengers=[serialize_passenger(passenger) for passenger in passengers],
    )


def _has_payload_data(payload: PassengerGroupPassengerInput) -> bool:
    return any(
        [
            _trim(payload.name, 1),
            _trim(payload.cpf, 1),
            _trim(payload.phone, 1),
            _trim(payload.whatsapp, 1),
            _trim(payload.boarding_location, 1),
            _trim(payload.extras, 1),
        ]
    )


def save_group_passengers(
    group: PassengerGroup,
    payload: Sequence[PassengerGroupPassengerInput],
    db: Session,
) -> PassengerGroup:
    if not payload and not group.passengers:
        _refresh_group_progress(group)
        if group.sale_item:
            _refresh_sale_item_occupancy(group.sale_item)
            db.add(group.sale_item)
        group.sale.passenger_status = compute_sale_passenger_status(group.sale)
        db.add(group.sale)
        db.add(group)
        db.flush()
        return group

    index_set = set()
    existing = {passenger.passenger_index: passenger for passenger in group.passengers}
    new_passengers: list[SalePassenger] = []
    slot_types = _group_slot_types(group)
    slot_limit = len(slot_types)

    for entry in payload:
        if entry.passenger_index < 1 or entry.passenger_index > slot_limit:
            raise HTTPException(status_code=400, detail="Índice do passageiro fora da capacidade do grupo.")
        if entry.passenger_index in index_set:
            raise HTTPException(status_code=400, detail="Cada posição do grupo deve ser única.")
        index_set.add(entry.passenger_index)
        data_present = _has_payload_data(entry)
        passenger = existing.get(entry.passenger_index)
        if not data_present:
            if passenger:
                db.delete(passenger)
            continue
        if not passenger:
            passenger = SalePassenger(
                sale_id=group.sale_id,
                passenger_group_id=group.id,
                passenger_index=entry.passenger_index,
            )
            new_passengers.append(passenger)
        default_type = slot_types[entry.passenger_index - 1] if entry.passenger_index - 1 < len(slot_types) else PassengerType.adult.value
        passenger.type = entry.type or default_type
        passenger.name = _trim(entry.name, 255) or ""
        passenger.cpf = _trim(entry.cpf, 20)
        passenger.birthdate = _parse_birthdate(entry.birthdate)
        passenger.phone = _trim(entry.phone, 50)
        passenger.whatsapp = _trim(entry.whatsapp, 50)
        passenger.boarding_location = _trim(entry.boarding_location, 255)
        passenger.extras = _trim(entry.extras, 1000)
        db.add(passenger)

    for passenger in new_passengers:
        group.passengers.append(passenger)

    for passenger in list(group.passengers):
        if passenger.passenger_index not in index_set and passenger not in new_passengers:
            group.passengers.remove(passenger)
            db.delete(passenger)

    _refresh_group_progress(group)
    sale = group.sale
    if group.sale_item:
        _refresh_sale_item_occupancy(group.sale_item)
        db.add(group.sale_item)
    sale.passenger_status = compute_sale_passenger_status(sale)
    db.add(group)
    db.add(sale)
    db.flush()
    return group


def assign_passengers_flat(sale: Sale, passenger_payload: Iterable[PassengerInput], db: Session) -> Sale:
    groups = ensure_passenger_groups(sale, db)
    flat_payload = list(passenger_payload)
    if not groups:
        sale.passengers.clear()
        for payload in flat_payload:
            passenger = SalePassenger(
                sale_id=sale.id,
                name=_trim(payload.name, 255) or "",
                cpf=_trim(payload.cpf, 20),
                birthdate=_parse_birthdate(payload.birthdate),
                phone=_trim(payload.phone, 50),
                whatsapp=_trim(payload.whatsapp, 50),
                boarding_location=_trim(payload.boarding_location, 255),
                extras=_trim(payload.extras, 1000),
            )
            sale.passengers.append(passenger)
        sale.passenger_status = compute_sale_passenger_status(sale)
        db.add(sale)
        db.flush()
        return sale

    total_slots = sum(len(_group_slot_types(group)) for group in groups)
    if len(flat_payload) > total_slots:
        raise HTTPException(status_code=400, detail="Quantidade de passageiros excede a capacidade dos grupos.")

    offset = 0
    for group in groups:
        slot_types = _group_slot_types(group)
        subset = flat_payload[offset : offset + len(slot_types)]
        offset += len(subset)
        group_payload = [
            PassengerGroupPassengerInput(
                passenger_index=index + 1,
                type=slot_types[index] if index < len(slot_types) else PassengerType.adult.value,
                name=entry.name,
                cpf=entry.cpf,
                birthdate=entry.birthdate,
                phone=entry.phone,
                whatsapp=entry.whatsapp,
                boarding_location=entry.boarding_location,
                extras=entry.extras,
            )
            for index, entry in enumerate(subset)
        ]
        save_group_passengers(group, group_payload, db)

    sale.passenger_status = compute_sale_passenger_status(sale)
    db.add(sale)
    db.flush()
    return sale
