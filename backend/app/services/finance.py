from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import get_settings
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.product import (
    Product,
    ProductAccommodationMode,
    ProductScheduleMode,
    ProductStatus,
    ProductVariation,
    ProductVariationStatus,
)
from app.models.schedule import Departure
from app.models.sale import (
    Sale,
    SaleFinancialStatus,
    SalePassengerStatus,
    SalePaymentStatus,
    SalePayoutStatus,
)
from app.models.sale_item import (
    SaleItem,
    SaleItemOccupancyStatus,
    SaleItemStatus,
    SalePaymentLink,
    SalePaymentLinkStatus,
)
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
    SectionDiscountConfig,
    SectionProductsCheckoutRequest,
    SaleItemChildBreakdown,
    SaleItemOut,
    SaleSummary,
)
from app.models.transport import TripDepartureInstance
from app.services.departures import (
    DepartureBookingService,
    DepartureCapacityService,
    DeparturePricingService,
)
from app.services.agency_integrations import get_agency_blimboo_token
from app.services.email import EmailClient
from app.services.payments import get_payment_provider
from app.services.payments.blimboo_api import BlimbooAPIError
from app.services.payments.base import PaymentCharge, PaymentChargeRequest
from app.services.package_pricing import PackageComposition, calculate_package_composition
from app.services.products import (
    confirm_inventory_for_sale,
    reserve_inventory_for_item,
    release_inventory_for_sale,
)
from app.services.passenger_groups import (
    assign_passengers_flat,
    ensure_passenger_groups,
    serialize_passenger,
    serialize_passenger_group,
)
from app.services.legal import maybe_generate_contract_for_sale
from app.services.payment_compatibility_service import (
    DEFAULT_ALLOWED_PAYMENT_METHODS,
    ensure_exact_compatibility,
    normalize_allowed_payment_methods,
)
logger = logging.getLogger(__name__)


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


def _normalize_allowed_payment_methods(raw: Any) -> list[str]:
    return normalize_allowed_payment_methods(raw)


def _product_allowed_payment_methods(product: Product | None) -> list[str]:
    if not product:
        return list(DEFAULT_ALLOWED_PAYMENT_METHODS)
    return _normalize_allowed_payment_methods(product.allowed_payment_methods)


def _fee_mode_from_section(section: dict[str, Any] | None) -> str:
    if not isinstance(section, dict):
        return "absorb"
    raw = str(
        section.get("feeMode")
        or section.get("fee_mode")
        or "absorb"
    ).strip().lower()
    return raw if raw in {"absorb", "pass_through"} else "absorb"


def _fee_mode_for_sale(sale: Sale) -> str:
    metadata = sale.metadata_json or {}
    raw = str(metadata.get("fee_mode") or "absorb").strip().lower()
    return raw if raw in {"absorb", "pass_through"} else "absorb"


def _allowed_payment_methods_for_sale(sale: Sale) -> list[str]:
    metadata = sale.metadata_json or {}
    from_metadata = _normalize_allowed_payment_methods(metadata.get("allowed_payment_methods"))
    if from_metadata:
        return from_metadata
    return _product_allowed_payment_methods(sale.product)


def _normalize_boarding_locations(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    cleaned: list[str] = []
    seen = set()
    for entry in raw:
        if not isinstance(entry, str):
            continue
        text = entry.strip()
        if not text:
            continue
        normalized = text[:255]
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)
    return cleaned


def _boarding_locations_from_sale(sale: Sale) -> list[str]:
    metadata = sale.metadata_json or {}
    locations = _normalize_boarding_locations(metadata.get("boarding_locations"))
    if locations:
        return locations
    product_metadata = sale.product.metadata_json if sale.product else None
    return _normalize_boarding_locations(product_metadata.get("boarding_locations") if product_metadata else None)


def _format_brl_amount(amount_cents: int | None) -> str:
    cents = amount_cents or 0
    amount = Decimal(cents) / Decimal("100")
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _resolve_agency_label(sale: Sale, db: Session) -> str:

    settings = get_settings()

    if sale.agency_id:

        agency = db.query(Agency).filter(Agency.id == sale.agency_id).first()

        if agency and agency.name:

            return agency.name

    return settings.app_name or "Roteiro Online"





def _resolve_customer_name(sale: Sale) -> str:

    return sale.customer_name or sale.customer_email or "cliente"





def _send_pos_checkout_email(sale: Sale, db: Session) -> None:
    if not sale.customer_email or not sale.passenger_form_token or not sale_requires_passengers(sale):
        return

    settings = get_settings()

    base_url = (settings.resolved_webapp_base_url or "").rstrip("/")

    passenger_url = f"{base_url}/passageiros/{sale.passenger_form_token}"

    agency_label = _resolve_agency_label(sale, db)

    product_label = sale.product_title or "sua compra"

    amount_label = _format_brl_amount((sale.gross_amount or sale.amount or 0))

    customer_name = _resolve_customer_name(sale)

    sale_reference = f"#{sale.id}"

    subject = f"{agency_label} - Detalhes da sua compra"

    text_body = (

        f"Ola {customer_name},\n\n"

        f"Registramos a sua compra do pacote {product_label} com a agencia {agency_label}.\n"

        f"Valor cobrado: {amount_label}\n"

        f"Venda: {sale_reference}\n\n"

        f"Acesse o link abaixo para preencher os passageiros e acompanhar a viagem:\n"

        f"{passenger_url}\n\n"

        "Se tiver duvidas basta responder este e-mail.\n"

        f"{agency_label}"

    )

    html_body = f"""

        <p>Ola {customer_name},</p>

        <p>Registramos a sua compra do pacote <strong>{product_label}</strong> com a agencia <strong>{agency_label}</strong>.</p>

        <ul style=\"padding-left:16px;color:#0f172a;\">

            <li><strong>Valor:</strong> {amount_label}</li>

            <li><strong>Venda:</strong> {sale_reference}</li>

        </ul>

        <p>Acesse o link abaixo para acompanhar a viagem e preencher os dados dos passageiros:</p>

        <p style=\"margin:24px 0;\">

            <a href=\"{passenger_url}\" style=\"background-color:#10b981;color:#fff;padding:12px 20px;border-radius:999px;font-weight:600;text-decoration:none;\">

                Abrir formulario de passageiros

            </a>

        </p>

        <p>Se preferir, copie e cole este link no navegador:</p>

        <p style=\"word-break:break-all;\"><a href=\"{passenger_url}\">{passenger_url}</a></p>

        <p>Se tiver duvidas basta responder este e-mail.</p>

        <p>{agency_label}</p>

    """

    try:

        EmailClient().send_email(

            to_email=sale.customer_email,

            subject=subject,

            html_body=html_body,

            text_body=text_body,

        ) 
    except Exception:  # pragma: no cover - envio de e-mail nao deve bloquear fluxo

        logger.exception("Falha ao enviar e-mail de confirmacao para venda POS %s", sale.id)


def _payment_link_url(token: str) -> str:
    settings = get_settings()
    base_url = (settings.resolved_webapp_base_url or "").rstrip("/")
    return f"{base_url}/pagamentos/{token}"


def _send_payment_link_email(sale: Sale, link: SalePaymentLink, db: Session) -> None:
    if not sale.customer_email:
        return
    payment_url = _payment_link_url(link.token)
    agency_label = _resolve_agency_label(sale, db)
    product_label = sale.product_title or "seu pacote"
    amount_label = _format_brl_amount(sale.gross_amount or sale.amount or 0)
    customer_name = _resolve_customer_name(sale)
    sale_reference = f"#{sale.id}"
    expires_label = link.expires_at.strftime("%d/%m/%Y %H:%M") if link.expires_at else ""
    expires_line = f"Valido ate: {expires_label}\n" if expires_label else ""
    subject = f"{agency_label} - Link de pagamento"
    text_body = (
        f"Ola {customer_name},\n\n"
        f"Geramos um link de pagamento para o pacote {product_label} da agencia {agency_label}.\n"
        f"Valor: {amount_label} ({sale_reference})\n"
        f"Acesse: {payment_url}\n"
        f"{expires_line}"
        "\n"
        "Caso ja tenha pago, ignore esta mensagem. Duvidas? Basta responder este e-mail.\n"
        f"{agency_label}"
    )
    expires_paragraph = f"<p>Link valido ate <strong>{expires_label}</strong>.</p>" if expires_label else ""
    html_body = f"""
        <p>Ola {customer_name},</p>
        <p>Segue o link para concluir o pagamento do pacote <strong>{product_label}</strong> com a agencia <strong>{agency_label}</strong>.</p>
        <ul style="padding-left:16px;color:#0f172a;">
            <li><strong>Valor:</strong> {amount_label}</li>
            <li><strong>Venda:</strong> {sale_reference}</li>
        </ul>
        {expires_paragraph}
        <p style="margin:24px 0;">
            <a href="{payment_url}" style="background-color:#10b981;color:#fff;padding:12px 20px;border-radius:999px;font-weight:600;text-decoration:none;">
                Abrir link de pagamento
            </a>
        </p>
        <p>Se preferir, copie e cole este link no navegador:</p>
        <p style="word-break:break-all;"><a href="{payment_url}">{payment_url}</a></p>
        <p>Qualquer duvida basta responder este e-mail.</p>
        <p>{agency_label}</p>
    """
    try:
        EmailClient().send_email(
            to_email=sale.customer_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
    except Exception:  # pragma: no cover
        logger.exception("Falha ao enviar e-mail de link de pagamento para venda %s", sale.id)

def _payment_provider_for_agency(db: Session, agency_id: int | None):
    token = get_agency_blimboo_token(db, agency_id)
    return get_payment_provider(token)

def _create_payment_charge(
    *,
    db: Session,
    agency_id: int | None,
    base_amount_cents: int,
    currency: str,
    installments: int,
    payment_method: str,
    metadata: dict[str, str | int | None] | None = None,
    defer_provider: bool = False,
) -> PaymentCharge:
    if base_amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor do pedido invǭlido.")
    if defer_provider:
        normalized_installments = max(1, installments)
        pending_reference = f"pending-{secrets.token_hex(8)}"
        return PaymentCharge(
            base_amount=base_amount_cents,
            gross_amount=base_amount_cents,
            platform_fee_amount=0,
            gateway_fee_estimated=0,
            agency_net_amount=base_amount_cents,
            spread_percentage_bps=0,
            installment_amount=int(round(base_amount_cents / normalized_installments)),
            installments=normalized_installments,
            payment_method=payment_method or "pix",
            currency=currency.upper(),
            provider="blimboo",
            provider_charge_id=pending_reference,
            provider_status=SalePaymentStatus.pending,
            metadata=metadata or {},
        )
    request = PaymentChargeRequest(
        base_amount=base_amount_cents,
        currency=currency.upper(),
        installments=max(1, installments),
        payment_method=payment_method or "credit_card",
        metadata=metadata or {},
    )
    provider = _payment_provider_for_agency(db, agency_id)
    try:
        return provider.initialize_charge(request)
    except BlimbooAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Nao foi possivel iniciar a cobranca. {exc}") from exc


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
    aggregated: dict[tuple[str, int | None], dict[str, Any]] = {}
    is_recurring = product.schedule_mode == ProductScheduleMode.recurring.value
    for item in cart_items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantidade inválida.")
        departure_id = int(item.departure_id) if item.departure_id is not None else None
        if is_recurring and departure_id is None:
            raise HTTPException(status_code=400, detail="Produto recorrente exige departure_id por item.")
        bucket = aggregated.setdefault((item.variation_id, departure_id), {"quantity": 0, "children": {}, "departure_id": departure_id})
        bucket["quantity"] += item.quantity
        children = bucket["children"]
        raw_children = item.children or []
        if isinstance(raw_children, dict):
            iterator = raw_children.items()
        else:
            iterator = ((getattr(child, "key", None), getattr(child, "quantity", 0)) for child in raw_children)
        for key, raw_qty in iterator:
            key_str = str(key or "").strip()
            if not key_str:
                continue
            try:
                qty = int(raw_qty)
            except (TypeError, ValueError):
                continue
            qty = max(0, qty)
            if qty <= 0:
                continue
            children[key_str] = children.get(key_str, 0) + qty
    if not aggregated:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma variação.")
    variation_ids = [variation_id for variation_id, _ in aggregated.keys()]
    variations = (
        db.query(ProductVariation)
        .filter(
            ProductVariation.product_id == product.id,
            ProductVariation.public_id.in_(variation_ids),
        )
        .with_for_update()
        .all()
    )
    if len(variations) != len(set(variation_ids)):
        raise HTTPException(status_code=404, detail="Variação não encontrada.")
    variation_map = {variation.public_id: variation for variation in variations}
    lines: list[ProductCartLine] = []
    for key, payload in aggregated.items():
        public_id, departure_id = key
        variation = variation_map[public_id]
        if variation.status != ProductVariationStatus.active.value:
            raise HTTPException(status_code=400, detail=f"Variação indisponível: {variation.name}.")
        quantity = payload["quantity"]
        children = payload["children"]
        composition = calculate_package_composition(
            variation=variation,
            quantity=quantity,
            child_counts=children,
        )
        lines.append(
            ProductCartLine(
                variation=variation,
                quantity=quantity,
                children=dict(children),
                composition=composition,
                departure_id=departure_id,
            )
        )
    lines.sort(key=lambda line: (line.variation.sort_order, line.departure_id or 0))
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
        total += int(line.total_amount_cents if line.total_amount_cents is not None else line.composition.total_price_cents)
    return total


def _cart_passengers(lines: Iterable[ProductCartLine]) -> int:
    passengers = 0
    for line in lines:
        passengers += line.composition.total_passengers
    return passengers


def _cart_capacity(lines: Iterable[ProductCartLine]) -> int:
    capacity = 0
    for line in lines:
        capacity += line.composition.total_capacity
    return capacity


def _line_capacity_units(line: ProductCartLine) -> int:
    return max(int(line.composition.total_capacity or 0), 0)


def _apply_departure_pricing_and_validate(
    *,
    db: Session,
    product: Product,
    lines: list[ProductCartLine],
) -> dict[int, Departure]:
    locked_departures: dict[int, Departure] = {}
    is_recurring = product.schedule_mode == ProductScheduleMode.recurring.value
    if not is_recurring:
        for line in lines:
            line.override_unit_price_cents = None
            line.total_amount_cents = line.composition.total_price_cents
        return locked_departures

    for line in lines:
        if line.departure_id is None:
            raise HTTPException(status_code=400, detail="Produto recorrente exige departure_id por item.")
        departure = locked_departures.get(line.departure_id)
        if departure is None:
            departure = DepartureBookingService.lock_for_booking(db, departure_id=line.departure_id, product_id=product.id)
            locked_departures[line.departure_id] = departure
        requested_units = _line_capacity_units(line)
        DepartureCapacityService.validate_sellable(departure=departure, requested_units=requested_units)
        override_unit_price = DeparturePricingService.resolve_price(default_price=line.variation.price_cents, departure=departure)
        line.override_unit_price_cents = int(override_unit_price)
        line.total_amount_cents = int((override_unit_price * line.quantity) + line.composition.child_extra_cents)
    return locked_departures


def _reserve_departure_capacity_for_lines(*, lines: list[ProductCartLine], departures: dict[int, Departure]) -> None:
    for line in lines:
        if line.departure_id is None:
            continue
        departure = departures.get(line.departure_id)
        if not departure:
            continue
        DepartureCapacityService.reserve(departure=departure, units=_line_capacity_units(line))


def _distribute_child_slots(child_quantities: Mapping[str, int], quantity: int) -> list[dict[str, int]]:
    if quantity <= 0:
        return []
    plan: list[dict[str, int]] = [dict() for _ in range(quantity)]
    for key, raw_total in (child_quantities or {}).items():
        try:
            total = int(raw_total)
        except (TypeError, ValueError):
            total = 0
        if total <= 0:
            continue
        base = total // quantity
        remainder = total % quantity
        for index in range(quantity):
            assigned = base + (1 if index < remainder else 0)
            if assigned <= 0:
                continue
            plan[index][str(key)] = assigned
    return plan


def _product_behavior_flags(product: Product | None) -> dict[str, bool]:
    has_rooms = bool(getattr(product, "has_rooms", False)) if product else False
    is_road_trip = bool(getattr(product, "is_road_trip", False)) if product else False
    return {
        "has_rooms": has_rooms,
        "is_road_trip": is_road_trip,
        "requires_passengers": True,
        "requires_rooming": has_rooms,
    }


def _resolve_metadata_flags(metadata: dict[str, Any] | None, defaults: dict[str, bool]) -> dict[str, bool]:
    flags = defaults.copy()
    if metadata:
        raw_flags = metadata.get("product_flags")
        if isinstance(raw_flags, dict):
            for key in ("has_rooms", "is_road_trip", "requires_passengers", "requires_rooming"):
                if key in raw_flags:
                    flags[key] = bool(raw_flags[key])
    return flags


def sale_flags(sale: Sale) -> dict[str, bool]:
    metadata = sale.metadata_json if isinstance(sale.metadata_json, dict) else None
    defaults = _product_behavior_flags(sale.product)
    flags = _resolve_metadata_flags(metadata, defaults)
    checkout_mode = str((metadata or {}).get("checkout_mode") or "").strip().lower()
    selected_products = (metadata or {}).get("selected_products")
    is_product_flow = bool(sale.product_id or sale.product_public_id)
    is_section_multi_product = checkout_mode == "section_multi_product" or (
        isinstance(selected_products, list) and len(selected_products) > 0
    )
    if is_product_flow or is_section_multi_product:
        # Regra de negocio: toda venda de produto exige lista de passageiros.
        flags["requires_passengers"] = True
    return flags


def sale_requires_passengers(sale: Sale) -> bool:
    return bool(sale_flags(sale).get("requires_passengers"))


def sale_requires_rooming(sale: Sale) -> bool:
    return bool(sale_flags(sale).get("requires_rooming"))


def _build_sale_items_from_lines(sale: Sale, product: Product, lines: Iterable[ProductCartLine]) -> list[SaleItem]:
    created: list[SaleItem] = []
    for line in lines:
        variation = line.variation
        composition = line.composition
        quantity = max(1, line.quantity)
        consumed_capacity = max(0, composition.total_capacity)
        base_unit_slots = variation.slots_per_unit or variation.people_included or 1
        unit_capacity = max(1, base_unit_slots)
        if consumed_capacity and quantity:
            base_capacity = consumed_capacity // quantity
            if consumed_capacity % quantity:
                base_capacity += 1
            unit_capacity = max(unit_capacity, base_capacity)
        slots_reserved = consumed_capacity
        room_capacity = variation.room_capacity or unit_capacity
        accommodation_mode = variation.accommodation_mode or ProductAccommodationMode.private.value
        child_quantities: dict[str, int] = {}
        for key, raw_value in (line.children or {}).items():
            try:
                value_int = int(raw_value)
            except (TypeError, ValueError):
                continue
            if value_int <= 0:
                continue
            child_quantities[str(key)] = value_int
        item = SaleItem(
            product_id=product.id,
            departure_id=line.departure_id,
            product_public_id=product.public_id,
            variation_id=variation.id,
            variation_public_id=variation.public_id,
            variation_name=variation.name,
            variation_description=variation.description,
            currency=(variation.currency or "BRL").lower(),
            unit_price=int(line.override_unit_price_cents if line.override_unit_price_cents is not None else variation.price_cents),
            quantity=line.quantity,
            subtotal_amount_cents=int(
                (line.override_unit_price_cents if line.override_unit_price_cents is not None else variation.price_cents) * line.quantity
            ),
            discount_amount_cents=int(max(line.discount_amount_cents or 0, 0)),
            total_amount_cents=int(
                (line.total_amount_cents if line.total_amount_cents is not None else composition.total_price_cents)
                - max(line.discount_amount_cents or 0, 0)
            ),
            total_price=int(
                (line.total_amount_cents if line.total_amount_cents is not None else composition.total_price_cents)
                - max(line.discount_amount_cents or 0, 0)
            ),
            people_count=composition.total_passengers,
            occupancy=unit_capacity,
            allows_children=bool(variation.child_policy_enabled),
            children_rules_snapshot=variation.child_pricing_rules,
            stock_mode=variation.stock_mode,
            accommodation_mode=accommodation_mode,
            room_capacity=room_capacity,
            slots_per_unit=base_unit_slots,
            slots_reserved=slots_reserved,
            metadata_json={
                "base_passengers": composition.base_passengers,
                "base_capacity": composition.base_capacity,
                "child_passengers": composition.child_passengers,
                "child_capacity": composition.child_capacity,
                "child_extra_amount_cents": composition.child_extra_cents,
                "child_breakdown": [child.serialize() for child in composition.child_breakdown],
                "child_quantities": child_quantities,
                "child_slots_plan": _distribute_child_slots(child_quantities, quantity),
                "child_policy_enabled": variation.child_policy_enabled,
                "consumed_capacity": composition.total_capacity,
                "accommodation_mode": accommodation_mode,
                "room_capacity": room_capacity,
                "slots_per_unit": base_unit_slots,
                "slots_reserved": slots_reserved,
                "departure_id": line.departure_id,
            },
        )
        sale.items.append(item)
        created.append(item)
    return created


def _ensure_trip_departure_instances_for_sale_items(product: Product, sale_items: Iterable[SaleItem], db: Session) -> None:
    if not product.is_road_trip or product.schedule_mode != ProductScheduleMode.recurring.value:
        return
    departure_ids = {
        int(item.departure_id)
        for item in sale_items
        if item.departure_id is not None
    }
    if not departure_ids:
        return
    departures = (
        db.query(Departure)
        .filter(
            Departure.product_id == product.id,
            Departure.id.in_(departure_ids),
            Departure.deleted_at.is_(None),
        )
        .all()
    )
    departures_by_id = {departure.id: departure for departure in departures}
    for departure_id in departure_ids:
        departure = departures_by_id.get(departure_id)
        if not departure:
            continue
        exists = (
            db.query(TripDepartureInstance.id)
            .filter(
                TripDepartureInstance.product_id == product.id,
                TripDepartureInstance.departure_id == departure.id,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            TripDepartureInstance(
                product_id=product.id,
                departure_id=departure.id,
                travel_date=departure.date,
                departure_time=departure.time,
            )
        )


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
    interest_mode_override: str | None = None,
    max_installments_no_interest_override: int | None = None,
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
    locked_departures = _apply_departure_pricing_and_validate(db=db, product=product, lines=lines)
    currency = _cart_currency(lines)
    amount_cents = _cart_total_amount(lines)
    passengers_total = _cart_passengers(lines)
    consumed_capacity = _cart_capacity(lines)
    product_flags = _product_behavior_flags(product)
    passengers_required = passengers_total if product_flags["requires_passengers"] else 0
    package_composition = [
        {
            "variation_public_id": line.variation.public_id,
            "variation_name": line.variation.name,
            "quantity": line.quantity,
            "departure_id": line.departure_id,
            "base_passengers": line.composition.base_passengers,
            "child_passengers": line.composition.child_passengers,
            "consumed_capacity": line.composition.total_capacity,
            "line_total_amount_cents": int(line.total_amount_cents if line.total_amount_cents is not None else line.composition.total_price_cents),
            "child_breakdown": [child.serialize() for child in line.composition.child_breakdown],
        }
        for line in lines
    ]

    passenger_token = secrets.token_urlsafe(24)
    passenger_status = (
        SalePassengerStatus.not_started.value if product_flags["requires_passengers"] else SalePassengerStatus.completed.value
    )
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
        "passengers_required": passengers_required,
        "consumed_capacity": consumed_capacity,
        "sale_passenger_token": passenger_token,
        "customer_name": _trim(customer.get("name"), 255),
        "customer_email": _trim(customer.get("email"), 255),
        "customer_phone": _trim(customer.get("phone"), 50),
        "description": _trim(product.name, 255),
    }
    charge = _create_payment_charge(
        db=db,
        agency_id=product.agency_id,
        base_amount_cents=amount_cents,
        currency=currency,
        installments=1,
        payment_method="credit_card",
        metadata=charge_metadata,
        defer_provider=channel == "public_page",
    )

    resolved_interest_mode = str(interest_mode_override or product.card_interest_mode or "merchant").lower()
    if resolved_interest_mode == "client":
        resolved_interest_mode = "customer"
    if resolved_interest_mode not in {"merchant", "customer"}:
        resolved_interest_mode = "merchant"
    resolved_max_no_interest = int(max_installments_no_interest_override) if max_installments_no_interest_override else None
    if resolved_max_no_interest is not None:
        resolved_max_no_interest = max(1, min(resolved_max_no_interest, 12))

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
        passenger_status=passenger_status,
        passenger_form_token=passenger_token,
        interest_mode=resolved_interest_mode,
        max_installments_no_interest=resolved_max_no_interest,
        metadata_json={
            "channel": channel,
            "source_url": source_url,
            "agency_slug": agency_slug,
            "page_id": page_id,
            "consumed_capacity": consumed_capacity,
            "fee_mode": "absorb",
            "allowed_payment_methods": _product_allowed_payment_methods(product),
            "package_composition": package_composition,
            "boarding_locations": _normalize_boarding_locations((product.metadata_json or {}).get("boarding_locations")),
            "product_flags": product_flags,
        },
        customer_name=_trim(customer.get("name"), 255),
        customer_email=_trim(customer.get("email"), 255),
        customer_phone=_trim(customer.get("phone"), 50),
        channel=channel,
    )
    _apply_charge_to_sale(sale, charge)

    built_items = _build_sale_items_from_lines(sale, product, lines)
    db.add(sale)
    db.flush()
    _ensure_trip_departure_instances_for_sale_items(product, built_items, db)

    for line, item in zip(lines, built_items):
        reserve_inventory_for_item(
            db=db,
            product=product,
            variation=line.variation,
            capacity_units=line.composition.total_capacity,
            sale=sale,
            sale_item=item,
        )
    _reserve_departure_capacity_for_lines(lines=lines, departures=locked_departures)

    db.commit()
    db.refresh(sale)
    return sale, charge


def _resolve_products_section(config: dict[str, Any], section_id: str) -> dict[str, Any]:
    sections = config.get("sections") or []
    for idx, raw_section in enumerate(sections):
        if not isinstance(raw_section, dict) or raw_section.get("type") != "products":
            continue
        candidate_id = (
            raw_section.get("id")
            or raw_section.get("section_id")
            or raw_section.get("sectionId")
            or raw_section.get("anchorId")
            or f"products-{idx}"
        )
        if str(candidate_id) == str(section_id):
            return raw_section
    raise HTTPException(status_code=404, detail="Secao de produtos nao encontrada.")


def _section_product_ids(section: dict[str, Any]) -> list[str]:
    product_ids_raw = section.get("productIds")
    product_ids: list[str] = []
    if isinstance(product_ids_raw, list):
        for entry in product_ids_raw:
            text = str(entry or "").strip()
            if text:
                product_ids.append(text)
    legacy_id = str(section.get("productId") or "").strip()
    if legacy_id and legacy_id not in product_ids:
        product_ids.append(legacy_id)
    return product_ids


def _validate_payment_method_compatibility(products: list[Product]) -> list[str]:
    groups = [_product_allowed_payment_methods(product) for product in products]
    return ensure_exact_compatibility(groups)


def _compute_section_discount_amount(
    *,
    subtotal_cents: int,
    selected_products: list[str],
    discount: SectionDiscountConfig | None,
) -> int:
    if subtotal_cents <= 0 or not discount:
        return 0
    if not discount.rule_type or not discount.discount_type or discount.discount_value is None:
        return 0
    selected_set = set(selected_products)
    eligible = False
    if discount.rule_type == "min_quantity":
        minimum = max(int(discount.min_selected_products or 0), 1)
        eligible = len(selected_set) >= minimum
    elif discount.rule_type == "exact_combination":
        required = {str(product_id).strip() for product_id in (discount.required_product_ids or []) if str(product_id).strip()}
        eligible = bool(required) and required.issubset(selected_set)
    if not eligible:
        return 0
    if discount.discount_type == "fixed":
        fixed_cents = max(int(discount.discount_value or 0), 0)
        return min(fixed_cents, subtotal_cents)
    percent = max(min(int(discount.discount_value or 0), 100), 0)
    return int(round(subtotal_cents * (percent / 100)))


def _section_discount_from_config(section: dict[str, Any]) -> SectionDiscountConfig | None:
    raw = section.get("discount")
    if not isinstance(raw, dict):
        return None
    try:
        return SectionDiscountConfig(
            rule_type=raw.get("ruleType"),
            min_selected_products=raw.get("minSelectedProducts"),
            required_product_ids=raw.get("requiredProductIds") or [],
            discount_type=raw.get("discountType"),
            discount_value=raw.get("discountValue"),
        )
    except Exception:
        return None


def _distribute_discount(lines: list[ProductCartLine], discount_total_cents: int) -> None:
    if discount_total_cents <= 0 or not lines:
        return
    gross_totals = [max(int(line.total_amount_cents or line.composition.total_price_cents), 0) for line in lines]
    subtotal = sum(gross_totals)
    if subtotal <= 0:
        return
    remaining = min(discount_total_cents, subtotal)
    for idx, line in enumerate(lines):
        if remaining <= 0:
            break
        base = gross_totals[idx]
        if base <= 0:
            continue
        if idx == len(lines) - 1:
            applied = min(remaining, base)
        else:
            proportional = int(round(discount_total_cents * (base / subtotal)))
            applied = min(max(proportional, 0), base, remaining)
        line.discount_amount_cents = applied
        remaining -= applied


def create_section_products_checkout_sale(
    *,
    db: Session,
    payload: SectionProductsCheckoutRequest,
) -> tuple[Sale, PaymentCharge]:
    if not payload.products:
        raise HTTPException(status_code=400, detail="Selecione ao menos um produto.")

    page = (
        db.query(Page)
        .options(joinedload(Page.agency).joinedload(Agency.users).joinedload(AgencyUser.user))
        .filter(Page.id == payload.page_id, Page.status == "published")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Pagina nao encontrada.")

    section = _resolve_products_section(page.config_json or {}, payload.section_id)
    allowed_products = set(_section_product_ids(section))
    if not allowed_products:
        raise HTTPException(status_code=400, detail="Secao sem produtos configurados.")

    owner = _pick_agency_owner(db, page.agency_id)
    selected_product_ids = [entry.product_id for entry in payload.products]
    if not selected_product_ids:
        raise HTTPException(status_code=400, detail="Selecione ao menos um produto.")
    if len(set(selected_product_ids)) != len(selected_product_ids):
        raise HTTPException(status_code=400, detail="Produto duplicado na selecao.")
    for product_id in selected_product_ids:
        if product_id not in allowed_products:
            raise HTTPException(status_code=400, detail="Produto nao permitido nesta secao.")

    product_lines: list[tuple[Product, list[ProductCartLine], dict[int, Departure]]] = []
    all_lines: list[ProductCartLine] = []
    for selection in payload.products:
        product = _lock_product_for_checkout(db, selection.product_id)
        if page.agency_id and product.agency_id and product.agency_id != page.agency_id:
            raise HTTPException(status_code=400, detail="Produto de outra agencia nao permitido na secao.")
        lines = _resolve_cart_lines(db, product, selection.items)
        locked_departures = _apply_departure_pricing_and_validate(db=db, product=product, lines=lines)
        product_lines.append((product, lines, locked_departures))
        all_lines.extend(lines)

    selected_products = [entry[0] for entry in product_lines]
    compatible_methods = _validate_payment_method_compatibility(selected_products)
    fee_mode = _fee_mode_from_section(section)
    raw_max_installments = section.get("installments") or 12
    try:
        checkout_max_installments = max(1, min(int(raw_max_installments or 12), 12))
    except (TypeError, ValueError):
        checkout_max_installments = 12
    raw_interest_mode = str(section.get("interestMode") or section.get("interest_mode") or "").strip().lower()
    if raw_interest_mode == "client":
        raw_interest_mode = "customer"
    if raw_interest_mode not in {"merchant", "customer"}:
        raw_interest_mode = "merchant"
    raw_max_no_interest = section.get("maxInstallmentsNoInterest") or section.get("max_installments_no_interest")
    try:
        checkout_max_no_interest = int(raw_max_no_interest) if raw_max_no_interest else None
    except (TypeError, ValueError):
        checkout_max_no_interest = None
    if checkout_max_no_interest is not None:
        checkout_max_no_interest = max(1, min(checkout_max_no_interest, checkout_max_installments))
    if fee_mode == "pass_through":
        checkout_max_no_interest = None

    aggregated_flags = {
        "has_rooms": any(bool(product.has_rooms) for product, _, _ in product_lines),
        "is_road_trip": any(bool(product.is_road_trip) for product, _, _ in product_lines),
        "requires_passengers": True,
        "requires_rooming": any(bool(product.has_rooms) for product, _, _ in product_lines),
    }

    currencies = _cart_currency(all_lines)
    subtotal_cents = _cart_total_amount(all_lines)
    total_passengers = _cart_passengers(all_lines)
    total_capacity = _cart_capacity(all_lines)
    effective_discount = payload.discount or _section_discount_from_config(section)
    discount_cents = _compute_section_discount_amount(
        subtotal_cents=subtotal_cents,
        selected_products=selected_product_ids,
        discount=effective_discount,
    )
    _distribute_discount(all_lines, discount_cents)
    amount_cents = max(subtotal_cents - discount_cents, 0)
    if amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor final invalido para checkout.")

    passenger_token = secrets.token_urlsafe(24)
    charge_metadata = {
        "section_id": payload.section_id,
        "page_id": page.id,
        "channel": payload.channel or "public_page",
        "agency_id": page.agency_id,
        "agency_slug": payload.agency_slug or (page.agency.slug if page.agency else None),
        "sale_passenger_token": passenger_token,
        "consumed_capacity": total_capacity,
        "customer_name": _trim(payload.customer.name, 255),
        "customer_email": _trim(payload.customer.email, 255),
        "customer_phone": _trim(payload.customer.phone, 50),
        "description": _trim(str(section.get("title") or "Checkout multi-produto"), 255),
    }
    charge = _create_payment_charge(
        db=db,
        agency_id=page.agency_id,
        base_amount_cents=amount_cents,
        currency=currencies,
        installments=1,
        payment_method="credit_card",
        metadata=charge_metadata,
        defer_provider=(payload.channel or "public_page") == "public_page",
    )

    sale = Sale(
        user_id=owner.id,
        agency_id=page.agency_id,
        page_id=page.id,
        page_slug=page.slug,
        page_title=_trim(page.title, 255),
        section_id=payload.section_id,
        product_id=None,
        product_public_id=None,
        product_title=_trim(str(section.get("title") or "Checkout multi-produto"), 255) or "Checkout multi-produto",
        product_description=_trim(str(section.get("subtitle") or "Compra com multiplos itens"), 500),
        currency=currencies.lower(),
        passengers_required=total_passengers,
        passenger_status=SalePassengerStatus.not_started.value,
        passenger_form_token=passenger_token,
        interest_mode=raw_interest_mode,
        max_installments_no_interest=checkout_max_no_interest,
        metadata_json={
            "channel": payload.channel or "public_page",
            "source_url": payload.source_url,
            "agency_slug": payload.agency_slug,
            "page_id": page.id,
            "consumed_capacity": total_capacity,
            "checkout_mode": "section_multi_product",
            "fee_mode": fee_mode,
            "allowed_payment_methods": compatible_methods,
            "selected_products": selected_product_ids,
            "subtotal_cents": subtotal_cents,
            "discount_cents": discount_cents,
            "discount_config": effective_discount.model_dump() if effective_discount else None,
            "checkout_max_installments": checkout_max_installments,
            "checkout_interest_mode": raw_interest_mode,
            "checkout_max_installments_no_interest": checkout_max_no_interest,
            "product_flags": aggregated_flags,
        },
        customer_name=_trim(payload.customer.name, 255),
        customer_email=_trim(payload.customer.email, 255),
        customer_phone=_trim(payload.customer.phone, 50),
        channel=payload.channel or "public_page",
    )
    _apply_charge_to_sale(sale, charge)
    db.add(sale)
    db.flush()

    for product, lines, departures in product_lines:
        built_items = _build_sale_items_from_lines(sale, product, lines)
        _ensure_trip_departure_instances_for_sale_items(product, built_items, db)
        for line, item in zip(lines, built_items):
            reserve_inventory_for_item(
                db=db,
                product=product,
                variation=line.variation,
                capacity_units=line.composition.total_capacity,
                sale=sale,
                sale_item=item,
            )
        _reserve_departure_capacity_for_lines(lines=lines, departures=departures)

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
    provider = _payment_provider_for_agency(db, sale.agency_id)
    updated_charge = provider.update_status(charge, SalePaymentStatus.paid)
    sale = _set_sale_payment_status(sale, SalePaymentStatus.paid, db)
    _send_pos_checkout_email(sale, db)
    return sale, updated_charge


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
        interest_mode_override=payload.interest_mode,
        max_installments_no_interest_override=payload.max_installments_no_interest,
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
    _send_payment_link_email(sale, link, db)
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
        .options(joinedload(Page.agency).joinedload(Agency.users).joinedload(AgencyUser.user))
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
        "customer_name": _trim(customer.get("name"), 255),
        "customer_email": _trim(customer.get("email"), 255),
        "customer_phone": _trim(customer.get("phone"), 50),
        "description": _trim(resolution.title, 255),
    }
    metadata = {key: str(value) for key, value in metadata_raw.items() if value is not None}
    charge = _create_payment_charge(
        db=db,
        agency_id=page.agency_id,
        base_amount_cents=amount_cents,
        currency="BRL",
        installments=max(1, resolution.installments),
        payment_method="credit_card",
        metadata=metadata,
        defer_provider=True,
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
    metadata = sale.metadata_json or {}
    flags = sale_flags(sale)
    consumed_capacity = metadata.get("consumed_capacity")
    if not isinstance(consumed_capacity, int):
        consumed_capacity = sale.passengers_required
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
        consumed_capacity=consumed_capacity,
        channel=sale.channel,
        customer_name=sale.customer_name,
        customer_email=sale.customer_email,
        customer_phone=sale.customer_phone,
        boarding_locations=_boarding_locations_from_sale(sale),
        has_rooms=flags["has_rooms"],
        is_road_trip=flags["is_road_trip"],
        requires_passengers=flags["requires_passengers"],
        requires_rooming=flags["requires_rooming"],
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
    allowed_methods = _allowed_payment_methods_for_sale(sale)
    fee_mode = _fee_mode_for_sale(sale)
    if charge:
        breakdown = serialize_checkout_breakdown(charge)
        passenger_token = sale.passenger_form_token if sale_requires_passengers(sale) else None
        return PublicCheckoutResponse(
            sale_id=sale.id,
            checkout_reference=charge.provider_charge_id,
            passenger_token=passenger_token,
            provider=charge.provider,
            provider_status=charge.provider_status.value,
            breakdown=breakdown,
            allowed_payment_methods=allowed_methods,
            fee_mode=fee_mode,            
        )
    return serialize_checkout_response_from_sale(sale)


def serialize_checkout_response_from_sale(sale: Sale) -> PublicCheckoutResponse:
    allowed_methods = _allowed_payment_methods_for_sale(sale)
    fee_mode = _fee_mode_for_sale(sale)
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
    passenger_token = sale.passenger_form_token if sale_requires_passengers(sale) else None
    return PublicCheckoutResponse(
        sale_id=sale.id,
        checkout_reference=sale.provider_charge_id,
        passenger_token=passenger_token,
        provider=sale.provider,
        provider_status=sale.payment_status,
        breakdown=breakdown,
        allowed_payment_methods=allowed_methods,
        fee_mode=fee_mode,
        provider_payload=(sale.provider_metadata or {}).get("last_provider_payload"),
    )


def serialize_sale_item(item: SaleItem) -> SaleItemOut:
    metadata = item.metadata_json or {}
    departure_date = item.departure.date.isoformat() if item.departure and item.departure.date else None
    departure_time = item.departure.time.strftime("%H:%M") if item.departure and item.departure.time else None
    breakdown_payload = metadata.get("child_breakdown") or []
    breakdown: list[SaleItemChildBreakdown] = []
    for entry in breakdown_payload:
        try:
            breakdown.append(
                SaleItemChildBreakdown(
                    key=str(entry.get("key", "")),
                    label=str(entry.get("label", "")),
                    quantity=int(entry.get("quantity") or 0),
                    unit_amount_cents=int(entry.get("unit_amount_cents") or 0),
                    total_amount_cents=int(entry.get("total_amount_cents") or 0),
                    counts_towards_capacity=bool(entry.get("counts_towards_capacity")),
                    counts_as_passenger=bool(entry.get("counts_as_passenger", True)),
                )
            )
        except (ValueError, TypeError):
            continue
    consumed_capacity = metadata.get("consumed_capacity")
    if not isinstance(consumed_capacity, int):
        consumed_capacity = item.people_count
    slots_reserved = item.slots_reserved or metadata.get("slots_reserved")
    if not isinstance(slots_reserved, int):
        slots_reserved = consumed_capacity
    room_capacity = item.room_capacity or metadata.get("room_capacity") or item.occupancy
    if not isinstance(room_capacity, int):
        room_capacity = item.occupancy or consumed_capacity
    slots_per_unit = item.slots_per_unit or metadata.get("slots_per_unit") or item.occupancy
    if not isinstance(slots_per_unit, int):
        slots_per_unit = item.occupancy or consumed_capacity
    accommodation_mode = item.accommodation_mode or metadata.get("accommodation_mode")
    if not isinstance(accommodation_mode, str) or not accommodation_mode:
        accommodation_mode = ProductAccommodationMode.private.value
    occupancy_status = item.occupancy_status or SaleItemOccupancyStatus.pending.value
    child_extra_amount = metadata.get("child_extra_amount_cents")
    if not isinstance(child_extra_amount, int):
        child_extra_amount = 0
    return SaleItemOut(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name if item.product else None,
        product_image_url=item.product.checkout_product_image_url if item.product else None,
        departure_id=item.departure_id,
        departure_date=departure_date,
        departure_time=departure_time,
        variation_public_id=item.variation_public_id,
        variation_name=item.variation_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        total_price=item.total_price,
        currency=item.currency,
        people_count=item.people_count,
        consumed_capacity=consumed_capacity,
        accommodation_mode=accommodation_mode,
        room_capacity=room_capacity,
        slots_per_unit=slots_per_unit,
        slots_reserved=slots_reserved,
        occupancy_status=occupancy_status,
        child_extra_amount_cents=child_extra_amount,
        child_breakdown=breakdown,
        subtotal_amount_cents=item.subtotal_amount_cents or item.total_price or 0,
        discount_amount_cents=item.discount_amount_cents or 0,
        total_amount_cents=item.total_amount_cents or item.total_price or 0,
        status=item.status,
    )


def update_passengers_from_payload(sale: Sale, passenger_payload: Iterable[PassengerInput], db: Session) -> Sale:
    if not sale_requires_passengers(sale):
        raise HTTPException(status_code=400, detail="Venda nao exige passageiros.")
    sale = assign_passengers_flat(sale, passenger_payload, db)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    maybe_generate_contract_for_sale(sale, db)
    db.refresh(sale)
    return sale


def _sale_item_capacity_units(item: SaleItem) -> int:
    metadata = item.metadata_json or {}
    consumed_capacity = metadata.get("consumed_capacity")
    if isinstance(consumed_capacity, int) and consumed_capacity > 0:
        return consumed_capacity
    if item.slots_reserved and item.slots_reserved > 0:
        return int(item.slots_reserved)
    return max(int(item.people_count or 0), 0)


def _sync_departure_capacity_for_sale(*, sale: Sale, db: Session, action: str) -> None:
    if action not in {"confirm", "release_reserved"}:
        return
    for item in sale.items or []:
        if not item.departure_id:
            continue
        departure = DepartureBookingService.lock_for_booking(db, departure_id=item.departure_id, product_id=item.product_id)
        units = _sale_item_capacity_units(item)
        if action == "confirm":
            DepartureCapacityService.confirm(departure=departure, units=units)
        else:
            DepartureCapacityService.release_reserved(departure=departure, units=units)
        db.add(departure)


def _set_sale_payment_status(sale: Sale, status: SalePaymentStatus, db: Session) -> Sale:
    if sale.payment_status == status.value:
        return sale
    sale.payment_status = status.value
    sale.provider_status = status.value
    if status == SalePaymentStatus.paid:
        sale.financial_status = SaleFinancialStatus.finalized.value
        sale.payout_status = SalePayoutStatus.available.value
        sale.paid_at = datetime.utcnow()
        _sync_departure_capacity_for_sale(sale=sale, db=db, action="confirm")
        confirm_inventory_for_sale(sale, db)
    elif status in {SalePaymentStatus.canceled, SalePaymentStatus.refunded}:
        _sync_departure_capacity_for_sale(sale=sale, db=db, action="release_reserved")
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
    if sale.payment_status == SalePaymentStatus.paid.value:
        maybe_generate_contract_for_sale(sale, db)
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
    children: dict[str, int]
    composition: PackageComposition
    departure_id: int | None = None
    override_unit_price_cents: int | None = None
    total_amount_cents: int | None = None
    discount_amount_cents: int = 0




