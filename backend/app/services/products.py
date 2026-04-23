from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.agency_user import AgencyUser
from app.models.legal import LegalContractTemplate
from app.models.product import (
    Product,
    ProductInventoryEvent,
    ProductInventoryEventAction,
    ProductInventoryStrategy,
    ProductScheduleMode,
    ProductStatus,
    ProductVariation,
    ProductAccommodationMode,
    ProductVariationStatus,
    ProductVariationStockMode,
    ProductRoom,
)
from app.models.sale import Sale, SalePaymentStatus
from app.models.sale_item import SaleItem, SaleItemStatus
from app.models.user import User
from app.schemas.products import (
    InventoryAdjustmentPayload,
    ProductDetail,
    ProductInventoryRebuildResponse,
    ProductPayload,
    ProductSummary,
    ProductVariationOut,
    ProductVariationPayload,
    ProductRoomPayload,
    ProductRoomOut,
)
from app.services.package_pricing import normalize_child_pricing_rules, serialize_child_pricing_rules

DEFAULT_ALLOWED_PAYMENT_METHODS = ["pix", "credit_card", "boleto"]
VALID_ALLOWED_PAYMENT_METHODS = set(DEFAULT_ALLOWED_PAYMENT_METHODS)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _validate_schedule_settings(*, schedule_mode: str, timezone: str | None) -> tuple[str, str | None]:
    normalized_mode = (schedule_mode or ProductScheduleMode.fixed_date.value).strip().lower()
    if normalized_mode not in {entry.value for entry in ProductScheduleMode}:
        raise HTTPException(status_code=400, detail="Modo de agenda invalido.")
    normalized_timezone = _clean_text(timezone)
    if normalized_mode == ProductScheduleMode.recurring.value and not normalized_timezone:
        raise HTTPException(status_code=400, detail="Timezone e obrigatorio para produtos recorrentes.")
    return normalized_mode, normalized_timezone


def _normalize_accommodation_settings(
    *,
    mode: str | None,
    room_capacity: int | None,
    slots_per_unit: int | None,
) -> tuple[str, int, int]:
    normalized_mode = (mode or ProductAccommodationMode.private.value).strip().lower()
    valid_modes = {entry.value for entry in ProductAccommodationMode}
    if normalized_mode not in valid_modes:
        raise HTTPException(status_code=400, detail="Modo de acomoda��o invǭlido.")
    capacity = max(1, int(room_capacity or 1))
    slots = max(1, int(slots_per_unit or 1))
    if normalized_mode == ProductAccommodationMode.private.value and slots != capacity:
        raise HTTPException(status_code=400, detail="Pacotes privativos devem reservar todas as vagas do quarto.")
    if normalized_mode == ProductAccommodationMode.shared.value and slots > capacity:
        raise HTTPException(status_code=400, detail="Vagas por unidade nǜo podem exceder a capacidade do quarto.")
    return normalized_mode, capacity, slots


def _sanitize_boarding_locations(locations: list[str] | None) -> list[str]:
    if not locations:
        return []
    sanitized: list[str] = []
    seen = set()
    for location in locations:
        if not location:
            continue
        text = location.strip()
        if not text:
            continue
        normalized = text[:255]
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(normalized)
    return sanitized


def _normalize_allowed_payment_methods(raw: list[str] | None) -> list[str]:
    if not raw:
        return list(DEFAULT_ALLOWED_PAYMENT_METHODS)
    seen: set[str] = set()
    normalized: list[str] = []
    for entry in raw:
        method = str(entry or "").strip().lower()
        if method not in VALID_ALLOWED_PAYMENT_METHODS:
            continue
        if method in seen:
            continue
        seen.add(method)
        normalized.append(method)
    return normalized or list(DEFAULT_ALLOWED_PAYMENT_METHODS)


def _normalize_room_payloads(payload: list[ProductRoomPayload] | None) -> list[dict[str, object]]:
    if not payload:
        return []
    normalized: list[dict[str, object]] = []
    for entry in payload:
        raw = entry.model_dump() if hasattr(entry, "model_dump") else dict(entry)  # type: ignore[arg-type]
        name = _clean_text(str(raw.get("name") or "")) or "Acomodação"
        capacity = max(1, int(raw.get("capacity") or 1))
        stock_quantity = raw.get("stock_quantity") or 0
        try:
            stock = int(stock_quantity)
        except (TypeError, ValueError):
            stock = 0
        stock = max(0, stock)
        normalized.append(
            {
                "id": raw.get("id"),
                "name": name[:255],
                "capacity": capacity,
                "is_private": bool(raw.get("is_private", False)),
                "stock_quantity": stock,
            }
        )
    return normalized


def _extract_boarding_locations(product: Product) -> list[str]:
    metadata = product.metadata_json or {}
    raw = metadata.get("boarding_locations")
    if isinstance(raw, list):
        raw_list = [entry for entry in raw if isinstance(entry, str)]
        return _sanitize_boarding_locations(raw_list)
    return []


def _apply_boarding_locations(product: Product, locations: list[str]) -> None:
    metadata = dict(product.metadata_json or {})
    metadata["boarding_locations"] = locations
    product.metadata_json = metadata


def _serialize_product_room(room: ProductRoom) -> ProductRoomOut:
    return ProductRoomOut(
        id=room.id,
        name=room.name,
        capacity=room.capacity or 1,
        is_private=bool(room.is_private),
        stock_quantity=room.stock_quantity or 0,
    )


def _apply_rooms(product: Product, rooms_payload: list[ProductRoomPayload] | None) -> None:
    normalized = _normalize_room_payloads(rooms_payload)
    existing_map = {room.id: room for room in list(product.rooms or []) if room.id is not None}
    retained: set[int] = set()
    new_rooms: list[ProductRoom] = []
    for entry in normalized:
        room_id = entry.get("id")
        if room_id and room_id in existing_map:
            room = existing_map[room_id]
            room.name = entry["name"]  # type: ignore[assignment]
            room.capacity = entry["capacity"]  # type: ignore[assignment]
            room.is_private = bool(entry["is_private"])
            room.stock_quantity = entry["stock_quantity"]  # type: ignore[assignment]
            retained.add(room_id)
        else:
            new_rooms.append(
                ProductRoom(
                    name=entry["name"],  # type: ignore[arg-type]
                    capacity=entry["capacity"],  # type: ignore[arg-type]
                    is_private=bool(entry["is_private"]),
                    stock_quantity=entry["stock_quantity"],  # type: ignore[arg-type]
                )
            )
    for room_id, room in existing_map.items():
        if room_id not in retained:
            product.rooms.remove(room)
    product.rooms.extend(new_rooms)


def _normalize_child_rules_payload(rules: list[dict[str, object]] | list | None) -> list[dict[str, object]]:
    if not rules:
        return serialize_child_pricing_rules(normalize_child_pricing_rules(None))
    raw_rules: list[dict[str, object]] = []
    for rule in rules:
        if hasattr(rule, "model_dump"):
            raw_rules.append(rule.model_dump())
        elif isinstance(rule, dict):
            raw_rules.append(rule)
    return serialize_child_pricing_rules(normalize_child_pricing_rules(raw_rules))


def _ensure_owner(product: Product, user: User) -> None:
    if product.user_id != user.id:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")


def _serialize_variation(variation: ProductVariation) -> ProductVariationOut:
    child_rules = serialize_child_pricing_rules(normalize_child_pricing_rules(variation.child_pricing_rules or []))
    return ProductVariationOut(
        id=variation.id,
        public_id=variation.public_id,
        name=variation.name,
        description=variation.description,
        price_cents=variation.price_cents,
        currency=variation.currency,
        people_included=variation.people_included,
        status=variation.status,
        stock_mode=variation.stock_mode,
        has_accommodation=bool(variation.has_accommodation),
        accommodation_mode=variation.accommodation_mode or ProductAccommodationMode.private.value,
        room_capacity=variation.room_capacity or 1,
        slots_per_unit=variation.slots_per_unit or 1,
        total_slots=variation.total_slots,
        available_slots=variation.available_slots,
        reserved_slots=variation.reserved_slots,
        sold_slots=variation.sold_slots,
        sort_order=variation.sort_order,
        child_policy_enabled=variation.child_policy_enabled,
        child_pricing_rules=child_rules,
    )


def _inventory_units_for_item(item: SaleItem) -> int:
    if item.slots_reserved and item.slots_reserved > 0:
        return int(item.slots_reserved)
    metadata = item.metadata_json or {}
    consumed_capacity = metadata.get("consumed_capacity")
    if isinstance(consumed_capacity, int) and consumed_capacity > 0:
        return consumed_capacity
    quantity = max(int(item.quantity or 0), 1)
    occupancy = max(int(item.occupancy or 0), 1)
    return occupancy * quantity


def _collect_inventory_counters(
    db: Session,
    product_ids: Sequence[int],
) -> tuple[dict[int, dict[str, int]], dict[int, dict[str, int]]]:
    product_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"reserved": 0, "sold": 0})
    variation_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"reserved": 0, "sold": 0})
    if not product_ids:
        return product_counts, variation_counts

    rows = (
        db.query(SaleItem, Sale.payment_status)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .filter(SaleItem.product_id.in_(product_ids))
        .all()
    )

    ignored_item_statuses = {SaleItemStatus.canceled.value, SaleItemStatus.refunded.value}
    for item, payment_status in rows:
        if not item.product_id:
            continue
        if (item.status or SaleItemStatus.pending.value) in ignored_item_statuses:
            continue

        units = _inventory_units_for_item(item)
        if units <= 0:
            continue

        bucket: str | None = None
        if payment_status == SalePaymentStatus.paid.value:
            bucket = "sold"
        elif payment_status in {SalePaymentStatus.pending.value, SalePaymentStatus.processing.value}:
            bucket = "reserved"
        if not bucket:
            continue

        product_counts[item.product_id][bucket] += units
        if item.variation_id:
            variation_counts[item.variation_id][bucket] += units

    return product_counts, variation_counts


def _apply_inventory_snapshot(
    product: Product,
    product_counts: dict[int, dict[str, int]],
    variation_counts: dict[int, dict[str, int]],
) -> bool:
    changed = False
    counters = product_counts.get(product.id, {})
    reserved = max(int(counters.get("reserved", 0)), 0)
    sold = max(int(counters.get("sold", 0)), 0)

    if product.reserved_slots != reserved:
        product.reserved_slots = reserved
        changed = True
    if product.sold_slots != sold:
        product.sold_slots = sold
        changed = True

    for variation in product.variations:
        counters = variation_counts.get(variation.id, {})
        variation_reserved = max(int(counters.get("reserved", 0)), 0)
        variation_sold = max(int(counters.get("sold", 0)), 0)

        if (variation.reserved_slots or 0) != variation_reserved:
            variation.reserved_slots = variation_reserved
            changed = True
        if (variation.sold_slots or 0) != variation_sold:
            variation.sold_slots = variation_sold
            changed = True

    return changed


def _reconcile_inventory_snapshots(products: Sequence[Product], db: Session) -> int:
    if not products:
        return 0
    product_counts, variation_counts = _collect_inventory_counters(
        db,
        [product.id for product in products if product.id is not None],
    )
    updated_products = 0
    for product in products:
        if _apply_inventory_snapshot(product, product_counts, variation_counts):
            db.add(product)
            updated_products += 1
    if updated_products:
        db.commit()
    return updated_products


def rebuild_inventory_snapshots_for_user(user: User, db: Session) -> ProductInventoryRebuildResponse:
    products = (
        db.query(Product)
        .filter(Product.user_id == user.id)
        .options(joinedload(Product.variations), joinedload(Product.template_contract), joinedload(Product.rooms))
        .all()
    )
    updated_products = _reconcile_inventory_snapshots(products, db)
    return ProductInventoryRebuildResponse(
        scanned_products=len(products),
        updated_products=updated_products,
    )


def serialize_product(product: Product) -> ProductSummary:
    return ProductSummary(
        id=product.id,
        public_id=product.public_id,
        agency_id=product.agency_id,
        template_contract_id=product.template_contract_id,
        template_contract_name=product.template_contract.name if product.template_contract else None,
        name=product.name,
        description=product.description,
        status=product.status,
        trip_date=product.trip_date,
        date_is_flexible=product.date_is_flexible,
        total_slots=product.total_slots,
        available_slots=product.available_slots,
        reserved_slots=product.reserved_slots,
        sold_slots=product.sold_slots,
        inventory_strategy=product.inventory_strategy,
        allow_oversell=product.allow_oversell,
        card_interest_mode=product.card_interest_mode or "merchant",
        allowed_payment_methods=_normalize_allowed_payment_methods(product.allowed_payment_methods),
        checkout_banner_url=_clean_text(product.checkout_banner_url),
        checkout_product_image_url=_clean_text(product.checkout_product_image_url),
        schedule_mode=product.schedule_mode or ProductScheduleMode.fixed_date.value,
        timezone=_clean_text(product.timezone),
        variations=[_serialize_variation(variation) for variation in sorted(product.variations, key=lambda v: v.sort_order)],
        boarding_locations=_extract_boarding_locations(product),
        has_rooms=bool(product.has_rooms),
        is_road_trip=bool(product.is_road_trip),
    )


def serialize_product_detail(product: Product) -> ProductDetail:
    summary = serialize_product(product)
    return ProductDetail(
        **summary.model_dump(),
        created_at=product.created_at,
        updated_at=product.updated_at,
        rooms=[_serialize_product_room(room) for room in sorted(product.rooms or [], key=lambda r: (r.capacity, r.name.lower()))],
    )


def list_products_for_user(user: User, db: Session) -> list[ProductSummary]:
    products = (
        db.query(Product)
        .filter(Product.user_id == user.id)
        .options(joinedload(Product.variations), joinedload(Product.template_contract), joinedload(Product.rooms))
        .order_by(Product.created_at.desc())
        .all()
    )
    _reconcile_inventory_snapshots(products, db)
    return [serialize_product(record) for record in products]


def _resolve_agency_id(payload: ProductPayload, user: User, db: Session) -> int | None:
    if payload.agency_id:
        membership = (
            db.query(AgencyUser)
            .filter(AgencyUser.user_id == user.id, AgencyUser.agency_id == payload.agency_id)
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="Agência inválida para este usuário.")
        return payload.agency_id

    membership = db.query(AgencyUser).filter(AgencyUser.user_id == user.id).order_by(AgencyUser.role.asc()).first()
    return membership.agency_id if membership else None


def _resolve_template_contract_id(template_id: int | None, user: User, db: Session) -> int | None:
    if not template_id:
        return None
    template = (
        db.query(LegalContractTemplate)
        .filter(LegalContractTemplate.id == template_id, LegalContractTemplate.user_id == user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=400, detail="Template jurídico inválido.")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template jurídico inativo.")
    return template.id


def _sync_variations(product: Product, payload: Sequence[ProductVariationPayload]) -> None:
    existing = {variation.public_id: variation for variation in product.variations}
    kept: set[str] = set()

    for index, variation_payload in enumerate(payload):
        record = existing.get(variation_payload.public_id) if variation_payload.public_id else None
        if record is None:
            record = ProductVariation(product=product)
            product.variations.append(record)

        record.name = variation_payload.name.strip()
        record.description = _clean_text(variation_payload.description)
        record.price_cents = variation_payload.price_cents
        record.currency = variation_payload.currency.upper()
        record.people_included = variation_payload.people_included
        record.status = variation_payload.status
        record.stock_mode = variation_payload.stock_mode
        record.has_accommodation = bool(variation_payload.has_accommodation)
        (
            record.accommodation_mode,
            record.room_capacity,
            record.slots_per_unit,
        ) = _normalize_accommodation_settings(
            mode=variation_payload.accommodation_mode,
            room_capacity=variation_payload.room_capacity,
            slots_per_unit=variation_payload.slots_per_unit,
        )
        if not record.has_accommodation:
            record.accommodation_mode = ProductAccommodationMode.private.value
            record.room_capacity = 1
            record.slots_per_unit = 1
        record.sort_order = index
        record.child_policy_enabled = variation_payload.child_policy_enabled
        record.child_pricing_rules = _normalize_child_rules_payload(variation_payload.child_pricing_rules)

        if variation_payload.stock_mode == ProductVariationStockMode.variant.value:
            record.total_slots = variation_payload.total_slots or 0
            if variation_payload.available_slots is not None:
                record.available_slots = min(variation_payload.available_slots, record.total_slots)
            elif record.available_slots is None:
                record.available_slots = record.total_slots
        else:
            record.total_slots = None
            record.available_slots = None

        kept.add(record.public_id)

    for variation in list(product.variations):
        if variation.public_id not in kept:
            product.variations.remove(variation)


def create_product(payload: ProductPayload, user: User, db: Session) -> Product:
    agency_id = _resolve_agency_id(payload, user, db)
    schedule_mode, timezone = _validate_schedule_settings(schedule_mode=payload.schedule_mode, timezone=payload.timezone)
    product = Product(
        user_id=user.id,
        agency_id=agency_id,
        template_contract_id=_resolve_template_contract_id(payload.template_contract_id, user, db),
        name=payload.name.strip(),
        description=_clean_text(payload.description),
        status=payload.status,
        trip_date=payload.trip_date,
        date_is_flexible=payload.date_is_flexible,
        inventory_strategy=payload.inventory_strategy,
        total_slots=payload.total_slots,
        available_slots=min(payload.available_slots, payload.total_slots),
        allow_oversell=payload.allow_oversell,
        is_road_trip=bool(payload.is_road_trip),
        card_interest_mode=payload.card_interest_mode or "merchant",
        allowed_payment_methods=_normalize_allowed_payment_methods(payload.allowed_payment_methods),
        checkout_banner_url=_clean_text(payload.checkout_banner_url),
        checkout_product_image_url=_clean_text(payload.checkout_product_image_url),
        schedule_mode=schedule_mode,
        timezone=timezone,
    )
    _apply_boarding_locations(product, _sanitize_boarding_locations(payload.boarding_locations))
    db.add(product)
    db.flush()
    _sync_variations(product, payload.variations)
    product.has_rooms = any(variation.has_accommodation for variation in product.variations)
    if not product.has_rooms:
        product.rooms = []
    if product.has_rooms and payload.rooms:
        _apply_rooms(product, payload.rooms)
    else:
        product.rooms = []
    db.commit()
    db.refresh(product)
    return product


def get_product_by_public_id(public_id: str, user: User, db: Session) -> Product:
    product = (
        db.query(Product)
        .filter(Product.public_id == public_id, Product.user_id == user.id)
        .options(joinedload(Product.variations), joinedload(Product.template_contract))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    _reconcile_inventory_snapshots([product], db)
    return product


def update_product(product: Product, payload: ProductPayload, user: User, db: Session) -> Product:
    _ensure_owner(product, user)
    schedule_mode, timezone = _validate_schedule_settings(schedule_mode=payload.schedule_mode, timezone=payload.timezone)
    product.name = payload.name.strip()
    product.description = _clean_text(payload.description)
    product.status = payload.status
    product.trip_date = payload.trip_date
    product.date_is_flexible = payload.date_is_flexible
    product.inventory_strategy = payload.inventory_strategy
    product.total_slots = payload.total_slots
    product.available_slots = min(payload.available_slots, payload.total_slots)
    product.allow_oversell = payload.allow_oversell
    product.is_road_trip = bool(payload.is_road_trip)
    if payload.card_interest_mode is not None:
        product.card_interest_mode = payload.card_interest_mode
    product.allowed_payment_methods = _normalize_allowed_payment_methods(payload.allowed_payment_methods)
    product.checkout_banner_url = _clean_text(payload.checkout_banner_url)
    product.checkout_product_image_url = _clean_text(payload.checkout_product_image_url)
    product.schedule_mode = schedule_mode
    product.timezone = timezone
    product.template_contract_id = _resolve_template_contract_id(payload.template_contract_id, user, db)
    _apply_boarding_locations(product, _sanitize_boarding_locations(payload.boarding_locations))
    _sync_variations(product, payload.variations)
    product.has_rooms = any(variation.has_accommodation for variation in product.variations)
    if product.has_rooms and payload.rooms:
        _apply_rooms(product, payload.rooms)
    else:
        for room in list(product.rooms or []):
            product.rooms.remove(room)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(public_id: str, user: User, db: Session) -> None:
    product = (
        db.query(Product)
        .filter(Product.public_id == public_id)
        .options(joinedload(Product.variations))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    _ensure_owner(product, user)
    db.delete(product)
    db.commit()


def update_product_boarding_locations(product: Product, locations: list[str], user: User, db: Session) -> Product:
    _ensure_owner(product, user)
    sanitized = _sanitize_boarding_locations(locations)
    _apply_boarding_locations(product, sanitized)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def adjust_inventory(product: Product, payload: InventoryAdjustmentPayload, user: User, db: Session) -> Product:
    _ensure_owner(product, user)
    changed = False
    if payload.total_slots is not None:
        if payload.total_slots < 0:
            raise HTTPException(status_code=400, detail="Total de vagas inválido.")
        product.total_slots = payload.total_slots
        if product.available_slots > product.total_slots:
            product.available_slots = product.total_slots
        changed = True

    if payload.available_slots is not None:
        if payload.available_slots < 0:
            raise HTTPException(status_code=400, detail="Vagas disponíveis inválidas.")
        if payload.available_slots > product.total_slots and not product.allow_oversell:
            raise HTTPException(status_code=400, detail="Vagas disponíveis não podem exceder o total.")
        product.available_slots = payload.available_slots
        changed = True

    if changed:
        event = ProductInventoryEvent(
            product=product,
            action=ProductInventoryEventAction.manual_available.value,
            quantity=payload.available_slots or product.available_slots,
            available_before=None,
            available_after=product.available_slots,
            context={"user_id": user.id, "note": payload.note},
        )
        db.add(event)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_public_product(public_id: str, db: Session) -> Product:
    product = (
        db.query(Product)
        .options(joinedload(Product.variations), joinedload(Product.rooms))
        .filter(Product.public_id == public_id, Product.status == ProductStatus.active.value)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    _reconcile_inventory_snapshots([product], db)
    return product


def reserve_inventory_for_item(
    *,
    db: Session,
    product: Product,
    variation: ProductVariation | None,
    capacity_units: int,
    sale: Sale,
    sale_item: SaleItem,
) -> None:
    if capacity_units <= 0:
        return

    reserved_product = 0
    reserved_variant = 0

    if product.inventory_strategy == ProductInventoryStrategy.manual.value and not product.allow_oversell:
        if product.available_slots < capacity_units:
            raise HTTPException(status_code=400, detail="Sem vagas suficientes para o produto.")
        before = product.available_slots
        product.available_slots -= capacity_units
        product.reserved_slots += capacity_units
        reserved_product = capacity_units
        db.add(
            ProductInventoryEvent(
                product=product,
                action=ProductInventoryEventAction.reserve.value,
                quantity=capacity_units,
                available_before=before,
                available_after=product.available_slots,
                sale=sale,
                sale_item=sale_item,
            )
        )
    else:
        product.reserved_slots += capacity_units

    if variation:
        variation.reserved_slots = (variation.reserved_slots or 0) + capacity_units
        if variation.stock_mode == ProductVariationStockMode.variant.value:
            available_now = variation.available_slots or 0
            if available_now < capacity_units:
                raise HTTPException(status_code=400, detail="Sem vagas suficientes para a variação.")
            variation.available_slots = available_now - capacity_units
            variation.reserved_slots = (variation.reserved_slots or 0) + capacity_units
            reserved_variant = capacity_units

    sale_item.reserved_from_product = reserved_product
    sale_item.reserved_from_variant = reserved_variant
    db.add(product)
    if variation:
        db.add(variation)
    db.add(sale_item)


def _load_sale_with_items(db: Session, sale_id: int) -> Sale | None:
    return (
        db.query(Sale)
        .options(
            joinedload(Sale.items).joinedload(SaleItem.product),
            joinedload(Sale.items).joinedload(SaleItem.variation),
        )
        .filter(Sale.id == sale_id)
        .first()
    )


def confirm_inventory_for_sale(sale: Sale, db: Session) -> None:
    current_sale = _load_sale_with_items(db, sale.id)
    if not current_sale:
        return
    for item in current_sale.items:
        if item.status != SaleItemStatus.pending.value:
            continue
        if item.reserved_from_product and item.product:
            item.product.reserved_slots = max(item.product.reserved_slots - item.reserved_from_product, 0)
            item.product.sold_slots += item.reserved_from_product
            db.add(
                ProductInventoryEvent(
                    product=item.product,
                    action=ProductInventoryEventAction.confirm.value,
                    quantity=item.reserved_from_product,
                    available_before=None,
                    available_after=item.product.available_slots,
                    sale=current_sale,
                    sale_item=item,
                )
            )
        if item.reserved_from_variant and item.variation:
            item.variation.reserved_slots = max((item.variation.reserved_slots or 0) - item.reserved_from_variant, 0)
            item.variation.sold_slots = (item.variation.sold_slots or 0) + item.reserved_from_variant
            db.add(
                ProductInventoryEvent(
                    product=item.product or current_sale.product,
                    variation=item.variation,
                    action=ProductInventoryEventAction.confirm.value,
                    quantity=item.reserved_from_variant,
                    available_before=None,
                    available_after=item.variation.available_slots,
                    sale=current_sale,
                    sale_item=item,
                )
            )
        item.status = SaleItemStatus.confirmed.value
        db.add(item)
    db.commit()


def release_inventory_for_sale(sale: Sale, db: Session, *, mark_canceled: bool = True) -> None:
    current_sale = _load_sale_with_items(db, sale.id)
    if not current_sale:
        return
    for item in current_sale.items:
        if item.status != SaleItemStatus.pending.value:
            continue
        if item.reserved_from_product and item.product:
            item.product.available_slots += item.reserved_from_product
            item.product.reserved_slots = max(item.product.reserved_slots - item.reserved_from_product, 0)
            db.add(
                ProductInventoryEvent(
                    product=item.product,
                    action=ProductInventoryEventAction.release.value,
                    quantity=item.reserved_from_product,
                    available_before=None,
                    available_after=item.product.available_slots,
                    sale=current_sale,
                    sale_item=item,
                )
            )
        if item.reserved_from_variant and item.variation:
            if item.variation.stock_mode == ProductVariationStockMode.variant.value:
                item.variation.available_slots = (item.variation.available_slots or 0) + item.reserved_from_variant
            item.variation.reserved_slots = max((item.variation.reserved_slots or 0) - item.reserved_from_variant, 0)
            db.add(
                ProductInventoryEvent(
                    product=item.product or current_sale.product,
                    variation=item.variation,
                    action=ProductInventoryEventAction.release.value,
                    quantity=item.reserved_from_variant,
                    available_before=None,
                    available_after=item.variation.available_slots,
                    sale=current_sale,
                    sale_item=item,
                )
            )
        if mark_canceled:
            item.status = SaleItemStatus.canceled.value
        db.add(item)
    db.commit()
