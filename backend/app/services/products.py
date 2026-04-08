from __future__ import annotations

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
    ProductStatus,
    ProductVariation,
    ProductVariationStatus,
    ProductVariationStockMode,
)
from app.models.sale import Sale
from app.models.sale_item import SaleItem, SaleItemStatus
from app.models.user import User
from app.schemas.products import (
    InventoryAdjustmentPayload,
    ProductDetail,
    ProductPayload,
    ProductSummary,
    ProductVariationOut,
    ProductVariationPayload,
)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _ensure_owner(product: Product, user: User) -> None:
    if product.user_id != user.id:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")


def _serialize_variation(variation: ProductVariation) -> ProductVariationOut:
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
        total_slots=variation.total_slots,
        available_slots=variation.available_slots,
        reserved_slots=variation.reserved_slots,
        sold_slots=variation.sold_slots,
        sort_order=variation.sort_order,
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
        variations=[_serialize_variation(variation) for variation in sorted(product.variations, key=lambda v: v.sort_order)],
    )


def serialize_product_detail(product: Product) -> ProductDetail:
    summary = serialize_product(product)
    return ProductDetail(
        **summary.model_dump(),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def list_products_for_user(user: User, db: Session) -> list[ProductSummary]:
    products = (
        db.query(Product)
        .filter(Product.user_id == user.id)
        .options(joinedload(Product.variations), joinedload(Product.template_contract))
        .order_by(Product.created_at.desc())
        .all()
    )
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
        record.sort_order = index

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
    )
    db.add(product)
    db.flush()
    _sync_variations(product, payload.variations)
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
    return product


def update_product(product: Product, payload: ProductPayload, user: User, db: Session) -> Product:
    _ensure_owner(product, user)
    product.name = payload.name.strip()
    product.description = _clean_text(payload.description)
    product.status = payload.status
    product.trip_date = payload.trip_date
    product.date_is_flexible = payload.date_is_flexible
    product.inventory_strategy = payload.inventory_strategy
    product.total_slots = payload.total_slots
    product.available_slots = min(payload.available_slots, payload.total_slots)
    product.allow_oversell = payload.allow_oversell
    product.template_contract_id = _resolve_template_contract_id(payload.template_contract_id, user, db)
    _sync_variations(product, payload.variations)
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
        .options(joinedload(Product.variations))
        .filter(Product.public_id == public_id, Product.status == ProductStatus.active.value)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return product


def reserve_inventory_for_item(
    *,
    db: Session,
    product: Product,
    variation: ProductVariation | None,
    quantity: int,
    sale: Sale,
    sale_item: SaleItem,
) -> None:
    if quantity <= 0:
        return

    reserved_product = 0
    reserved_variant = 0

    if product.inventory_strategy == ProductInventoryStrategy.manual.value and not product.allow_oversell:
        if product.available_slots < quantity:
            raise HTTPException(status_code=400, detail="Sem vagas suficientes para o produto.")
        before = product.available_slots
        product.available_slots -= quantity
        product.reserved_slots += quantity
        reserved_product = quantity
        db.add(
            ProductInventoryEvent(
                product=product,
                action=ProductInventoryEventAction.reserve.value,
                quantity=quantity,
                available_before=before,
                available_after=product.available_slots,
                sale=sale,
                sale_item=sale_item,
            )
        )
    else:
        product.reserved_slots += quantity

    if variation:
        variation.reserved_slots = (variation.reserved_slots or 0) + quantity
        if variation.stock_mode == ProductVariationStockMode.variant.value:
            available_now = variation.available_slots or 0
            if available_now < quantity:
                raise HTTPException(status_code=400, detail=f"Sem vagas suficientes em {variation.name}.")
            before = available_now
            variation.available_slots = available_now - quantity
            reserved_variant = quantity
            db.add(
                ProductInventoryEvent(
                    product=product,
                    variation=variation,
                    action=ProductInventoryEventAction.reserve.value,
                    quantity=quantity,
                    available_before=before,
                    available_after=variation.available_slots,
                    sale=sale,
                    sale_item=sale_item,
                )
            )

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
