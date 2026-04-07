from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.product import (
    Product,
    ProductStatus,
    ProductVariation,
    ProductVariationStatus,
)
from app.models.sale import (
    Sale,
    SaleFinancialStatus,
    SalePassenger,
    SalePassengerStatus,
    SalePaymentStatus,
    SalePayoutStatus,
)
from app.models.sale_item import SaleItem, SaleItemStatus, SalePaymentLink, SalePaymentLinkStatus
from app.models.user import User
from app.schemas.finance import (
    CheckoutCartItem,
    PassengerInput,
    PaymentBreakdown,
    PaymentLinkRequest,
    PaymentLinkResponse,
    PosCheckoutRequest,
    ProductCheckoutRequest,
    PublicCheckoutResponse,
    SaleItemOut,
    SalePassengerOut,
    SaleSummary,
)
from app.services.payments import get_payment_provider
from app.services.payments.base import PaymentCharge, PaymentChargeRequest
from app.services.products import (
    reserve_inventory_for_item,
    confirm_inventory_for_sale,
    release_inventory_for_sale,
)

payment_provider = get_payment_provider()


def _localized_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("pt", "es", "en"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return text
        for _, text in value.items():
            if isinstance(text, str) and text.strip():
                return text
    return str(value)


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value)
    raise HTTPException(status_code=400, detail="Valor de preÃ§o invÃ¡lido.")


def _to_cents(value: Decimal) -> int:
    cents = (value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def _create_payment_charge(
    *,
    base_amount_cents: int,
    currency: str,
    installments: int,
    payment_method: str,
    metadata: dict[str, str | int | None] | None = None,
) -> PaymentCharge:
    if base_amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor do pedido invǭlido.")
    request = PaymentChargeRequest(
        base_amount=base_amount_cents,
        currency=currency.upper(),
        installments=max(1, installments),
        payment_method=payment_method or "credit_card",
        metadata=metadata or {},
    )
    return payment_provider.initialize_charge(request)


def _apply_charge_to_sale(sale: Sale, charge: PaymentCharge) -> None:
    sale.provider = charge.provider
    sale.provider_charge_id = charge.provider_charge_id
    sale.provider_status = charge.provider_status.value
    sale.payment_status = charge.provider_status.value
    sale.payment_method = charge.payment_method
    sale.installments = charge.installments
    sale.currency = charge.currency
    sale.base_amount = charge.base_amount
    sale.gross_amount = charge.gross_amount
    sale.platform_fee_amount = charge.platform_fee_amount
    sale.gateway_fee_estimated = charge.gateway_fee_estimated
    sale.agency_net_amount = charge.agency_net_amount
    sale.spread_percentage = charge.spread_percentage_bps
    sale.amount = charge.gross_amount
    sale.commission_amount = charge.platform_fee_amount
    sale.stripe_application_fee_amount = charge.platform_fee_amount
    sale.net_amount = charge.agency_net_amount
    metadata = dict(sale.provider_metadata or {})
    metadata["installment_amount"] = charge.installment_amount
    sale.provider_metadata = metadata


def _installment_amount(sale: Sale) -> int:
    if sale.provider_metadata and "installment_amount" in sale.provider_metadata:
        try:
            return int(sale.provider_metadata["installment_amount"])
        except (ValueError, TypeError):
            pass
    if sale.gross_amount and sale.installments:
        return int(sale.gross_amount / max(1, sale.installments))
    return 0


def _find_price_item(config: dict[str, Any], product_id: str, section_hint: str | None = None) -> CheckoutPriceResolution:
    sections = config.get("sections") or []
    for idx, raw_section in enumerate(sections):
        if not isinstance(raw_section, dict) or raw_section.get("type") != "prices":
            continue
        section_id = (
            raw_section.get("id")
            or raw_section.get("section_id")
            or raw_section.get("sectionId")
            or raw_section.get("anchorId")
            or f"prices-{idx}"
        )
        if section_hint and section_hint != section_id:
            continue
        for item_idx, raw_item in enumerate(raw_section.get("items") or []):
            if not isinstance(raw_item, dict):
                continue
            checkout_config = raw_item.get("checkout") or {}
            candidate_product_id = checkout_config.get("productId") or raw_item.get("productId")
            if candidate_product_id == product_id:
                price_value = _to_decimal(raw_item.get("price"))
                passengers_required = checkout_config.get("passengersRequired") or checkout_config.get("passengers_required") or 0
                installments = checkout_config.get("installments") or 1
                interest_mode = checkout_config.get("interestMode") or checkout_config.get("interest_mode") or "merchant"
                max_no_interest = checkout_config.get("maxInstallmentsNoInterest") or checkout_config.get(
                    "max_installments_no_interest"
                )
                currency = (raw_item.get("currency") or "BRL").upper()
                return CheckoutPriceResolution(
                    section_id=str(section_id),
                    section_index=idx,
                    item_index=item_idx,
                    product_id=product_id,
                    title=_localized_value(raw_item.get("title")),
                    description=_localized_value(raw_item.get("description")),
                    price_decimal=price_value,
                    currency=currency,
                    passengers_required=int(passengers_required or 0),
                    installments=int(installments or 1),
                    interest_mode=str(interest_mode or "merchant"),
                    max_installments_no_interest=int(max_no_interest) if max_no_interest else None,
                    raw_section=raw_section,
                    raw_item=raw_item,
                    checkout_config=checkout_config,
                )
    raise HTTPException(status_code=404, detail="Produto nÃ£o encontrado no configurador da pÃ¡gina.")




def _lock_product_for_checkout(db: Session, public_id: str) -> Product:
    product = (
        db.query(Product)
        .filter(Product.public_id == public_id)
        .options(selectinload(Product.variations), selectinload(Product.user))
        .with_for_update(of=Product)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    if product.status != ProductStatus.active.value:
        raise HTTPException(status_code=400, detail="Produto inativo.")
    return product


def _resolve_cart_lines(
    db: Session,
    product: Product,
    cart_items: Iterable[CheckoutCartItem],
) -> list[ProductCartLine]:
    aggregated: dict[str, int] = {}
    for item in cart_items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantidade inválida.")
        aggregated[item.variation_id] = aggregated.get(item.variation_id, 0) + item.quantity
    if not aggregated:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma variação.")
    variations = (
        db.query(ProductVariation)
        .filter(
            ProductVariation.product_id == product.id,
            ProductVariation.public_id.in_(aggregated.keys()),
        )
        .with_for_update()
        .all()
    )
    if len(variations) != len(aggregated):
        raise HTTPException(status_code=404, detail="Variação não encontrada.")
    variation_map = {variation.public_id: variation for variation in variations}
    lines: list[ProductCartLine] = []
    for public_id, quantity in aggregated.items():
        variation = variation_map[public_id]
        if variation.status != ProductVariationStatus.active.value:
            raise HTTPException(status_code=400, detail=f"Variação indisponível: {variation.name}.")
        lines.append(ProductCartLine(variation=variation, quantity=quantity))
    lines.sort(key=lambda line: line.variation.sort_order)
    return lines


def _cart_currency(lines: Iterable[ProductCartLine]) -> str:
    currencies = {(line.variation.currency or "BRL").upper() for line in lines}
    if not currencies:
        return "BRL"
    if len(currencies) > 1:
        raise HTTPException(status_code=400, detail="Todas as variações devem usar a mesma moeda.")
    return currencies.pop()


def _cart_total_amount(lines: Iterable[ProductCartLine]) -> int:
    total = 0
    for line in lines:
        total += line.variation.price_cents * line.quantity
    return total


def _cart_passengers(lines: Iterable[ProductCartLine]) -> int:
    passengers = 0
    for line in lines:
        passengers += (line.variation.people_included or 1) * line.quantity
    return passengers


def _build_sale_items_from_lines(sale: Sale, product: Product, lines: Iterable[ProductCartLine]) -> None:
    for line in lines:
        variation = line.variation
        item = SaleItem(
            product_id=product.id,
            product_public_id=product.public_id,
            variation_id=variation.id,
            variation_public_id=variation.public_id,
            variation_name=variation.name,
            variation_description=variation.description,
            currency=(variation.currency or "BRL").lower(),
            unit_price=variation.price_cents,
            quantity=line.quantity,
            total_price=variation.price_cents * line.quantity,
            people_count=(variation.people_included or 1) * line.quantity,
            stock_mode=variation.stock_mode,
        )
        sale.items.append(item)
def _trim(value: str | None, length: int) -> str | None:
    if value is None:
        return None
    return value[:length]


def _pick_agency_owner(db: Session, agency_id: int) -> User:
    membership = (
        db.query(AgencyUser)
        .options(joinedload(AgencyUser.user))
        .filter(AgencyUser.agency_id == agency_id)
        .order_by(AgencyUser.role.desc())
        .all()
    )
    for rel in membership:
        if rel.role == "owner" and rel.user:
            return rel.user
    for rel in membership:
        if rel.user:
            return rel.user
    raise HTTPException(status_code=400, detail="AgÃªncia sem usuÃ¡rio responsÃ¡vel.")


def create_product_checkout_sale(
    *,
    db: Session,
    product_public_id: str,
    cart_items: list[CheckoutCartItem],
    customer: dict[str, str],
    channel: str,
    page_id: int | None = None,
    page_slug: str | None = None,
    agency_slug: str | None = None,
    source_url: str | None = None,
    acting_user: User | None = None,
) -> tuple[Sale, PaymentCharge]:
    product = _lock_product_for_checkout(db, product_public_id)
    owner = product.user
    if not owner:
        raise HTTPException(status_code=400, detail="Produto sem responsavel.")
    if acting_user and acting_user.id != owner.id:
        raise HTTPException(status_code=403, detail="Acesso negado ao produto.")
    if channel not in {"page", "public_page", "pos", "link"}:
        raise HTTPException(status_code=400, detail="Canal invalido.")

    lines = _resolve_cart_lines(db, product, cart_items)
    currency = _cart_currency(lines)
    amount_cents = _cart_total_amount(lines)
    passengers_required = _cart_passengers(lines)

    passenger_token = secrets.token_urlsafe(24)
    page_title_snapshot: str | None = None
    if page_id:
        page_ref = db.query(Page).filter(Page.id == page_id).first()
        if page_ref and page_ref.title:
            page_title_snapshot = _trim(page_ref.title, 255)
    charge_metadata = {
        "product_public_id": product.public_id,
        "channel": channel,
        "agency_id": product.agency_id,
        "page_id": page_id,
        "page_slug": page_slug,
        "agency_slug": agency_slug,
        "sale_passenger_token": passenger_token,
    }
    charge = _create_payment_charge(
        base_amount_cents=amount_cents,
        currency=currency,
        installments=1,
        payment_method="credit_card",
        metadata=charge_metadata,
    )

    sale = Sale(
        user_id=owner.id,
        agency_id=product.agency_id,
        page_id=page_id,
        page_slug=page_slug,
        page_title=page_title_snapshot,
        product_id=product.id,
        product_public_id=product.public_id,
        product_title=_trim(product.name, 255) or "",
        product_description=_trim(product.description, 500),
        currency=currency.lower(),
        passengers_required=passengers_required,
        passenger_form_token=passenger_token,
        interest_mode="merchant",
        metadata_json={
            "channel": channel,
            "source_url": source_url,
            "agency_slug": agency_slug,
            "page_id": page_id,
        },
        customer_name=_trim(customer.get("name"), 255),
        customer_email=_trim(customer.get("email"), 255),
        customer_phone=_trim(customer.get("phone"), 50),
        channel=channel,
    )
    _apply_charge_to_sale(sale, charge)

    _build_sale_items_from_lines(sale, product, lines)
    db.add(sale)
    db.flush()

    for item in sale.items:
        reserve_inventory_for_item(
            db=db,
            product=product,
            variation=item.variation,
            quantity=item.quantity,
            sale=sale,
            sale_item=item,
        )

    db.commit()
    db.refresh(sale)
    return sale, charge
def create_pos_sale(
    *,
    db: Session,
    product_public_id: str,
    payload: PosCheckoutRequest,
    current_user: User,
) -> tuple[Sale, PaymentCharge]:
    sale, charge = create_product_checkout_sale(
        db=db,
        product_public_id=product_public_id,
        cart_items=payload.items,
        customer=payload.customer.model_dump(),
        channel="pos",
        acting_user=current_user,
    )
    return sale, charge


def create_payment_link_sale(
    *,
    db: Session,
    product_public_id: str,
    payload: PaymentLinkRequest,
    current_user: User,
    expires_in_minutes: int | None = None,
) -> SalePaymentLink:
    sale, _charge = create_product_checkout_sale(
        db=db,
        product_public_id=product_public_id,
        cart_items=payload.items,
        customer=payload.customer.model_dump(),
        channel="link",
        acting_user=current_user,
    )
    expiration_minutes = expires_in_minutes or payload.expires_in_minutes or 60
    link = SalePaymentLink(
        sale_id=sale.id,
        created_by_user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=expiration_minutes),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def create_checkout_sale(
    *,
    db: Session,
    page_id: int,
    product_id: str,
    section_id: str | None,
    customer: dict[str, str],
    source_url: str | None = None,
    page_slug: str | None = None,
    agency_slug: str | None = None,
) -> tuple[Sale, PaymentCharge]:
    page = (
        db.query(Page)
        .options(joinedload(Page.agency).joinedload(Page.agency.users).joinedload(AgencyUser.user))
        .filter(Page.id == page_id, Page.status == "published")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Pagina nao encontrada.")
    config = page.config_json or {}
    resolution = _find_price_item(config, product_id, section_id)
    if resolution.currency != "BRL":
        raise HTTPException(status_code=400, detail="Apenas valores em BRL sao aceitos.")
    owner = _pick_agency_owner(db, page.agency_id)

    amount_cents = _to_cents(resolution.price_decimal)
    passenger_token = secrets.token_urlsafe(24)
    metadata_raw = {
        "sale_passenger_token": passenger_token,
        "page_id": page.id,
        "page_slug": page.slug,
        "agency_id": page.agency_id,
        "agency_slug": agency_slug or (page.agency.slug if page.agency else None),
        "product_id": product_id,
        "section_id": resolution.section_id,
        "user_id": owner.id,
        "page_url": source_url,
    }
    metadata = {key: str(value) for key, value in metadata_raw.items() if value is not None}
    charge = _create_payment_charge(
        base_amount_cents=amount_cents,
        currency="BRL",
        installments=max(1, resolution.installments),
        payment_method="credit_card",
        metadata=metadata,
    )

    sale = Sale(
        user_id=owner.id,
        agency_id=page.agency_id,
        page_id=page.id,
        page_slug=page.slug,
        page_title=_trim(page.title, 255),
        section_id=resolution.section_id,
        price_item_id=product_id,
        product_title=_trim(resolution.title, 255) or "",
        product_description=_trim(resolution.description, 500),
        currency="brl",
        passengers_required=resolution.passengers_required,
        passenger_form_token=passenger_token,
        installments=resolution.installments,
        interest_mode=resolution.interest_mode,
        max_installments_no_interest=resolution.max_installments_no_interest,
        metadata_json={
            "checkout": resolution.checkout_config,
            "page_slug": page_slug or page.slug,
            "page_url": source_url,
        },
        customer_name=_trim(customer.get("name"), 255),
        customer_email=_trim(customer.get("email"), 255),
        customer_phone=_trim(customer.get("phone"), 50),
        channel="page",
    )
    _apply_charge_to_sale(sale, charge)

    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale, charge
def serialize_sale(sale: Sale) -> SaleSummary:
    gross_amount = sale.gross_amount or sale.amount
    base_amount = sale.base_amount or sale.amount
    platform_fee = sale.platform_fee_amount or sale.commission_amount
    gateway_fee = sale.gateway_fee_estimated or (sale.stripe_fee_amount or 0)
    agency_net = sale.agency_net_amount or sale.net_amount or 0
    installment_amount = _installment_amount(sale)
    spread_percent = (sale.spread_percentage or 0) / 100
    return SaleSummary(
        id=sale.id,
        created_at=sale.created_at,
        product_public_id=sale.product_public_id,
        product_title=sale.product_title,
        product_description=sale.product_description,
        page_title=sale.page_title,
        page_slug=sale.page_slug,
        amount_cents=gross_amount,
        base_amount_cents=base_amount,
        gross_amount_cents=gross_amount,
        currency=sale.currency,
        commission_cents=platform_fee,
        platform_fee_amount_cents=platform_fee,
        gateway_fee_estimated_cents=gateway_fee,
        agency_net_amount_cents=agency_net,
        installment_amount_cents=installment_amount,
        net_amount_cents=agency_net,
        spread_percentage=spread_percent,
        provider=sale.provider,
        provider_charge_id=sale.provider_charge_id,
        provider_status=sale.provider_status,
        paid_at=sale.paid_at,
        payment_method=sale.payment_method,
        installments=sale.installments,
        payment_status=sale.payment_status,
        financial_status=sale.financial_status,
        payout_status=sale.payout_status,
        passenger_status=sale.passenger_status,
        passengers_required=sale.passengers_required,
        channel=sale.channel,
        customer_name=sale.customer_name,
        customer_email=sale.customer_email,
        customer_phone=sale.customer_phone,
    )


def serialize_checkout_breakdown(charge: PaymentCharge) -> PaymentBreakdown:
    return PaymentBreakdown(
        base_amount_cents=charge.base_amount,
        gross_amount_cents=charge.gross_amount,
        platform_fee_amount_cents=charge.platform_fee_amount,
        gateway_fee_estimated_cents=charge.gateway_fee_estimated,
        agency_net_amount_cents=charge.agency_net_amount,
        installment_amount_cents=charge.installment_amount,
        installments=charge.installments,
        currency=charge.currency,
        payment_method=charge.payment_method,
        spread_percentage=charge.spread_percentage_bps / 100,
    )


def serialize_checkout_response(sale: Sale, charge: PaymentCharge | None = None) -> PublicCheckoutResponse:
    if charge:
        breakdown = serialize_checkout_breakdown(charge)
        return PublicCheckoutResponse(
            sale_id=sale.id,
            checkout_reference=charge.provider_charge_id,
            passenger_token=sale.passenger_form_token,
            provider=charge.provider,
            provider_status=charge.provider_status.value,
            breakdown=breakdown,
        )
    return serialize_checkout_response_from_sale(sale)


def serialize_checkout_response_from_sale(sale: Sale) -> PublicCheckoutResponse:
    breakdown = PaymentBreakdown(
        base_amount_cents=sale.base_amount,
        gross_amount_cents=sale.gross_amount or sale.amount,
        platform_fee_amount_cents=sale.platform_fee_amount or sale.commission_amount,
        gateway_fee_estimated_cents=sale.gateway_fee_estimated or (sale.stripe_fee_amount or 0),
        agency_net_amount_cents=sale.agency_net_amount or (sale.net_amount or 0),
        installment_amount_cents=_installment_amount(sale),
        installments=sale.installments,
        currency=sale.currency,
        payment_method=sale.payment_method or "credit_card",
        spread_percentage=(sale.spread_percentage or 0) / 100,
    )
    return PublicCheckoutResponse(
        sale_id=sale.id,
        checkout_reference=sale.provider_charge_id,
        passenger_token=sale.passenger_form_token,
        provider=sale.provider,
        provider_status=sale.payment_status,
        breakdown=breakdown,
    )


def serialize_sale_item(item: SaleItem) -> SaleItemOut:
    return SaleItemOut(
        id=item.id,
        variation_public_id=item.variation_public_id,
        variation_name=item.variation_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        total_price=item.total_price,
        currency=item.currency,
        people_count=item.people_count,
        status=item.status,
    )


def serialize_passenger(passenger: SalePassenger) -> SalePassengerOut:
    return SalePassengerOut(
        id=passenger.id,
        name=passenger.name,
        cpf=passenger.cpf,
        birthdate=passenger.birthdate.isoformat() if passenger.birthdate else None,
        phone=passenger.phone,
        whatsapp=passenger.whatsapp,
        boarding_location=passenger.boarding_location,
        extras=passenger.extras,
    )


def update_passengers_from_payload(sale: Sale, passenger_payload: Iterable[PassengerInput], db: Session) -> Sale:
    sale.passengers.clear()
    db.flush()
    for payload in passenger_payload:
        birthdate_value = None
        if payload.birthdate:
            try:
                birthdate_value = date.fromisoformat(payload.birthdate)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Data de nascimento invÃ¡lida.") from exc
        passenger = SalePassenger(
            sale_id=sale.id,
            name=_trim(payload.name, 255) or "",
            cpf=_trim(payload.cpf, 20),
            birthdate=birthdate_value,
            phone=_trim(payload.phone, 50),
            whatsapp=_trim(payload.whatsapp, 50),
            boarding_location=_trim(payload.boarding_location, 255),
            extras=_trim(payload.extras, 1000),
        )
        sale.passengers.append(passenger)
    sale.passenger_status = compute_passenger_status(sale)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def compute_passenger_status(sale: Sale) -> str:
    if not sale.passengers:
        return SalePassengerStatus.not_started.value
    if sale.passengers_required and len(sale.passengers) >= sale.passengers_required:
        has_missing = any(not passenger.name or not passenger.cpf for passenger in sale.passengers)
        if not has_missing:
            return SalePassengerStatus.completed.value
    return SalePassengerStatus.partial.value


def _set_sale_payment_status(sale: Sale, status: SalePaymentStatus, db: Session) -> Sale:
    if sale.payment_status == status.value:
        return sale
    sale.payment_status = status.value
    sale.provider_status = status.value
    if status == SalePaymentStatus.paid:
        sale.financial_status = SaleFinancialStatus.finalized.value
        sale.payout_status = SalePayoutStatus.available.value
        sale.paid_at = datetime.utcnow()
        confirm_inventory_for_sale(sale, db)
    elif status in {SalePaymentStatus.canceled, SalePaymentStatus.refunded}:
        release_inventory_for_sale(sale, db)
        if status == SalePaymentStatus.refunded:
            sale.financial_status = SaleFinancialStatus.finalized.value
        else:
            sale.financial_status = SaleFinancialStatus.pending.value
        sale.payout_status = SalePayoutStatus.pending.value
        sale.paid_at = None
    else:
        sale.financial_status = SaleFinancialStatus.pending.value
        sale.payout_status = SalePayoutStatus.pending.value
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def complete_sale_payment(sale: Sale, db: Session) -> Sale:
    return _set_sale_payment_status(sale, SalePaymentStatus.paid, db)


def simulate_sale_status(sale: Sale, status: SalePaymentStatus, db: Session) -> Sale:
    return _set_sale_payment_status(sale, status, db)


@dataclass
class CheckoutPriceResolution:
    section_id: str
    section_index: int
    item_index: int
    product_id: str
    title: str
    description: str
    price_decimal: Decimal
    currency: str
    passengers_required: int
    installments: int
    interest_mode: str
    max_installments_no_interest: int | None
    raw_section: dict[str, Any]
    raw_item: dict[str, Any]
    checkout_config: dict[str, Any]


@dataclass
class ProductCartLine:
    variation: ProductVariation
    quantity: int




