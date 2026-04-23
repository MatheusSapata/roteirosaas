from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.models.passenger_group import PassengerGroup
from app.models.page import Page
from app.models.sale import Sale, SalePaymentStatus
from app.models.sale_item import SalePaymentLink, SalePaymentLinkStatus
from app.schemas.finance import (
    PaymentConfirmationRequest,
    PaymentInstallmentOption,
    PaymentPricingResponse,
    PassengerFormResponse,
    PassengerInput,
    PassengerGroupListResponse,
    PassengerGroupOut,
    PassengerGroupSaveRequest,
    ProductCheckoutRequest,
    PublicCheckoutRequest,
    PublicCheckoutResponse,
    SectionProductsCheckoutRequest,
    SectionProductsPricingRequest,
    SaleDetail,
)
from app.schemas.products import ProductDetail
from app.services.agency_integrations import get_agency_blimboo_token
from app.core.config import get_settings
from app.services.finance import (
    complete_sale_payment,
    create_checkout_sale,
    create_product_checkout_sale,
    create_section_products_checkout_sale,
    _apply_departure_pricing_and_validate,
    _cart_currency,
    _cart_total_amount,
    _compute_section_discount_amount,
    _fee_mode_from_section,
    _lock_product_for_checkout,
    _resolve_cart_lines,
    _resolve_products_section,
    _section_discount_from_config,
    _section_product_ids,
    _validate_payment_method_compatibility,
    sale_flags,
    serialize_checkout_response,
    serialize_checkout_response_from_sale,
    serialize_passenger,
    serialize_sale,
    serialize_sale_item,
    update_passengers_from_payload,
    _installment_amount,
    _boarding_locations_from_sale,
    sale_requires_passengers,
)
from app.services.legal import maybe_generate_contract_for_sale
from app.services.blimboo_service import (
    ChargeBuildInput,
    ChargeCardInput,
    ChargeCustomerInput,
    PAYMENT_METHOD_TO_BLIMBOO,
    build_charge_payload,
    create_blimboo_charge,
)
from app.services.checkout_state import build_checkout_state
from app.services.payment_compatibility_service import normalize_allowed_payment_methods
from app.services.pricing_service import (
    pricing_from_sale,
    resolve_quote_total_cents as resolve_quote_total_cents_from_provider,
)
from app.services.payments.blimboo_api import BlimbooAPIClient, BlimbooAPIError
from app.services.payments.blimboo_pricing import (
    BLIMBOO_CURRENCY_MAP,
    build_fallback_credit_card_pricing,
    fetch_credit_card_pricing,
    merge_credit_card_pricing,
)
from app.services.passenger_groups import (
    ensure_passenger_groups,
    save_group_passengers,
    serialize_passenger_group,
)
from app.services.products import get_public_product, serialize_product_detail

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("/checkout/payment-intent", response_model=PublicCheckoutResponse)
def create_public_payment_intent(
    payload: PublicCheckoutRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale, charge = create_checkout_sale(
        db=db,
        page_id=payload.page_id,
        product_id=payload.product_id,
        section_id=payload.section_id,
        customer=payload.customer.model_dump(),
        source_url=payload.source_url,
        page_slug=payload.page_slug,
        agency_slug=payload.agency_slug,
    )
    return serialize_checkout_response(sale, charge)


@router.post("/products/checkout/payment-intent", response_model=PublicCheckoutResponse)
def create_product_checkout_intent(
    payload: ProductCheckoutRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale, charge = create_product_checkout_sale(
        db=db,
        product_public_id=payload.product_id,
        cart_items=payload.items,
        customer=payload.customer.model_dump(),
        channel=payload.channel or "page",
        page_id=payload.page_id,
        page_slug=payload.page_slug,
        agency_slug=payload.agency_slug,
        source_url=payload.source_url,
    )
    return serialize_checkout_response(sale, charge)


@router.post("/sections/products/checkout/payment-intent", response_model=PublicCheckoutResponse)
def create_section_products_checkout_intent(
    payload: SectionProductsCheckoutRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale, charge = create_section_products_checkout_sale(db=db, payload=payload)
    return serialize_checkout_response(sale, charge)


@router.post("/sections/products/checkout/pricing", response_model=PaymentPricingResponse)
def get_section_products_checkout_pricing(
    payload: SectionProductsPricingRequest,
    db: Session = Depends(get_db),
) -> PaymentPricingResponse:
    if not payload.products:
        raise HTTPException(status_code=400, detail="Selecione ao menos um produto.")

    page = db.query(Page).filter(Page.id == payload.page_id, Page.status == "published").first()
    if not page:
        raise HTTPException(status_code=404, detail="Pagina nao encontrada.")

    section = _resolve_products_section(page.config_json or {}, payload.section_id)
    allowed_products = set(_section_product_ids(section))
    if not allowed_products:
        raise HTTPException(status_code=400, detail="Secao sem produtos configurados.")

    product_lines = []
    all_lines = []
    selected_product_ids = [entry.product_id for entry in payload.products]
    if len(set(selected_product_ids)) != len(selected_product_ids):
        raise HTTPException(status_code=400, detail="Produto duplicado na selecao.")

    for selection in payload.products:
        if selection.product_id not in allowed_products:
            raise HTTPException(status_code=400, detail="Produto nao permitido nesta secao.")
        product = _lock_product_for_checkout(db, selection.product_id)
        if page.agency_id and product.agency_id and product.agency_id != page.agency_id:
            raise HTTPException(status_code=400, detail="Produto de outra agencia nao permitido na secao.")
        lines = _resolve_cart_lines(db, product, selection.items)
        _apply_departure_pricing_and_validate(db=db, product=product, lines=lines)
        product_lines.append((product, lines, {}))
        all_lines.extend(lines)

    if not all_lines:
        raise HTTPException(status_code=400, detail="Selecione ao menos um pacote.")

    selected_products = [entry[0] for entry in product_lines]
    compatible_methods = _validate_payment_method_compatibility(selected_products)
    if "credit_card" not in compatible_methods:
        raise HTTPException(status_code=400, detail="Cartao indisponivel para esta selecao.")

    currency = (payload.currency or "BRL").upper()
    base_amount_cents = int(payload.base_amount_cents or 0)
    if base_amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor final invalido para checkout.")

    raw_max_installments = section.get("installments") or 12
    try:
        max_installments = max(1, min(int(raw_max_installments or 12), 12))
    except (TypeError, ValueError):
        max_installments = 12

    raw_interest_mode = str(section.get("interestMode") or section.get("interest_mode") or "").strip().lower()
    if raw_interest_mode == "client":
        raw_interest_mode = "customer"
    if raw_interest_mode not in {"merchant", "customer"}:
        raw_interest_mode = "merchant"

    raw_max_no_interest = section.get("maxInstallmentsNoInterest") or section.get("max_installments_no_interest")
    try:
        max_no_interest = int(raw_max_no_interest) if raw_max_no_interest else None
    except (TypeError, ValueError):
        max_no_interest = None
    if max_no_interest is not None:
        max_no_interest = max(1, min(max_no_interest, max_installments))
        if raw_interest_mode == "merchant":
            # "Ate X sem juros" exige comparacao entre merchant/customer.
            raw_interest_mode = "customer"

    fee_mode = payload.fee_mode or _fee_mode_from_section(section)
    if fee_mode not in {"absorb", "pass_through"}:
        fee_mode = "absorb"
    if fee_mode == "pass_through":
        max_no_interest = None
    api_token = get_agency_blimboo_token(db, page.agency_id)
    logger.info(
        "public pricing request page_id=%s section_id=%s fee_mode=%s currency=%s base_amount_cents=%s max_installments=%s raw_interest_mode=%s max_no_interest=%s products=%s",
        payload.page_id,
        payload.section_id,
        fee_mode,
        currency,
        base_amount_cents,
        max_installments,
        raw_interest_mode,
        max_no_interest,
        [entry.product_id for entry in payload.products],
    )
    if fee_mode == "pass_through":
        return _build_pass_through_credit_card_pricing(
            api_token=api_token,
            currency=currency,
            base_amount_cents=base_amount_cents,
            max_installments=max_installments,
        )

    merchant_pricing = fetch_credit_card_pricing(
        api_base_url=settings.blimboo_api_base_url or "",
        api_token=api_token,
        currency=currency,
        base_amount_cents=base_amount_cents,
        interest_mode="merchant",
        max_installments=max_installments,
    )
    customer_pricing = fetch_credit_card_pricing(
        api_base_url=settings.blimboo_api_base_url or "",
        api_token=api_token,
        currency=currency,
        base_amount_cents=base_amount_cents,
        interest_mode="customer",
        max_installments=max_installments,
    )

    if raw_interest_mode == "merchant":
        effective_credit_card = merchant_pricing
    elif max_no_interest:
        effective_credit_card = merge_credit_card_pricing(
            currency=currency,
            base_amount_cents=base_amount_cents,
            merchant_pricing=merchant_pricing,
            customer_pricing=customer_pricing,
            max_installments=max_installments,
            max_installments_no_interest=max_no_interest,
        )
    else:
        effective_credit_card = customer_pricing

    if not effective_credit_card.options:
        effective_credit_card = build_fallback_credit_card_pricing(
            currency=currency,
            base_amount_cents=base_amount_cents,
            max_installments=max_installments,
        )

    logger.info(
        "public pricing response fee_mode=%s result=%s",
        fee_mode,
        effective_credit_card.model_dump(),
    )
    return effective_credit_card


@router.get("/products/{public_id}", response_model=ProductDetail)
def get_public_product_detail(
    public_id: str,
    db: Session = Depends(get_db),
) -> ProductDetail:
    product = get_public_product(public_id, db)
    return serialize_product_detail(product)


@router.get("/payment-links/{token}", response_model=SaleDetail)
def get_payment_link_details(
    token: str,
    db: Session = Depends(get_db),
) -> SaleDetail:
    sale = (
        _sale_by_payment_link_token(db, token)
    )
    summary = serialize_sale(sale)
    passengers: list = []
    passenger_groups: list[PassengerGroupOut] = []
    groups: list[PassengerGroup] = []
    if sale_requires_passengers(sale):
        groups = ensure_passenger_groups(sale, db)
        passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
        passenger_groups = [serialize_passenger_group(group) for group in groups]
    items = [serialize_sale_item(item) for item in sale.items]
    db.commit()
    return SaleDetail(
        **summary.model_dump(),
        passengers=passengers,
        items=items,
        passenger_groups=passenger_groups,
    )


def _money_to_cents(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return int((decimal_value * 100).quantize(Decimal("1")))


def _coerce_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _collect_pricing_options(payload, max_installments: int) -> list[PaymentInstallmentOption]:
    resolved: dict[int, PaymentInstallmentOption] = {}

    if isinstance(payload, dict):
        raw_prices = payload.get("prices")
        if isinstance(raw_prices, list):
            for index, raw_price in enumerate(raw_prices, start=1):
                if index > max(1, max_installments):
                    break
                total_amount = _money_to_cents(raw_price)
                if total_amount is None:
                    continue
                resolved[index] = PaymentInstallmentOption(
                    installments=index,
                    installment_amount_cents=int(round(total_amount / index)),
                    total_amount_cents=max(0, total_amount),
                    has_interest=False,
                )

    def _register(entry: dict, forced_installments: int | None = None) -> None:
        installments = forced_installments
        if installments is None:
            installments = (
                _coerce_int(entry.get("installments"))
                or _coerce_int(entry.get("installment"))
                or _coerce_int(entry.get("parcel"))
                or _coerce_int(entry.get("times"))
                or _coerce_int(entry.get("quantity"))
                or _coerce_int(entry.get("number"))
            )
        if not installments or installments < 1 or installments > max(1, max_installments):
            return

        total_amount = (
            _money_to_cents(entry.get("total_amount"))
            or _money_to_cents(entry.get("gross_amount"))
            or _money_to_cents(entry.get("amount"))
            or _money_to_cents(entry.get("total"))
            or _money_to_cents(entry.get("price"))
            or _money_to_cents(entry.get("value"))
        )
        installment_amount = (
            _money_to_cents(entry.get("installment_amount"))
            or _money_to_cents(entry.get("installment_value"))
            or _money_to_cents(entry.get("amount_per_installment"))
            or _money_to_cents(entry.get("parcel_amount"))
            or _money_to_cents(entry.get("value_per_installment"))
        )

        if total_amount is None and installment_amount is None:
            return
        if total_amount is None and installment_amount is not None:
            total_amount = installment_amount * installments
        if installment_amount is None and total_amount is not None:
            installment_amount = int(round(total_amount / max(installments, 1)))
        if total_amount is None or installment_amount is None:
            return

        resolved[installments] = PaymentInstallmentOption(
            installments=installments,
            installment_amount_cents=max(0, installment_amount),
            total_amount_cents=max(0, total_amount),
            has_interest=False,
        )

    def _walk(node) -> None:
        if isinstance(node, list):
            for item in node:
                _walk(item)
            return
        if not isinstance(node, dict):
            return

        _register(node)
        for key, value in node.items():
            forced_installments = _coerce_int(key) if isinstance(key, str) and key.isdigit() else None
            if forced_installments and isinstance(value, dict):
                _register(value, forced_installments=forced_installments)
            _walk(value)

    _walk(payload)
    return sorted(resolved.values(), key=lambda option: option.installments)


def _resolve_interest_candidates(interest_mode: str | None) -> list[int]:
    # Inference from the docs: interest_by is integer, but the enum mapping is not documented.
    normalized = (interest_mode or "").lower()
    preferred = 1 if normalized in {"customer", "client"} else 2
    alternatives = [preferred, 1 if preferred == 2 else 2]
    deduped: list[int] = []
    for candidate in alternatives:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _resolve_pricing_max_installments(sale: Sale) -> int:
    metadata = sale.metadata_json or {}
    raw_configured = metadata.get("checkout_max_installments")
    configured = 0
    if raw_configured is not None:
        try:
            configured = int(raw_configured)
        except (TypeError, ValueError):
            configured = 0
    if configured <= 0:
        configured = int(sale.installments or 0)
    if configured > 0:
        return max(1, min(configured, 12))
    if sale.channel == "page":
        configured = int(sale.installments or 0)
        if configured > 0:
            return max(1, min(configured, 12))
        return 12
    return 12


def _build_quote_based_credit_card_pricing(
    *,
    api_token: str,
    currency: str,
    base_amount_cents: int,
    max_installments: int,
    fee_mode: str,
) -> PaymentPricingResponse:
    client = BlimbooAPIClient(settings.blimboo_api_base_url or "", api_token)
    options: list[PaymentInstallmentOption] = []
    provider_payloads: list[dict[str, Any]] = []
    provider_responses: list[Any] = []

    for installments in range(1, max_installments + 1):
        quoted_total_cents: int | None = None
        quote_payload = {
            "amount": round(base_amount_cents / 100, 2),
            "currency": currency,
            "method": PAYMENT_METHOD_TO_BLIMBOO["credit_card"],
            "payment_method": "credit_card",
            "installments": installments,
        }
        provider_payloads.append(quote_payload)
        try:
            quote_response = client.quote_payment(quote_payload)
            provider_responses.append(quote_response)
            provider_payload = _extract_provider_payload(quote_response)
            quoted_total_cents = resolve_quote_total_cents_from_provider(provider_payload)
        except BlimbooAPIError as exc:
            provider_responses.append({"error": str(exc), "installments": installments})
            quoted_total_cents = None

        pricing = pricing_from_sale(base_amount_cents, quoted_total_cents, fee_mode)
        total_amount_cents = max(0, pricing.final_amount_cents)
        installment_amount_cents = int(round(total_amount_cents / max(installments, 1)))
        options.append(
            PaymentInstallmentOption(
                installments=installments,
                installment_amount_cents=installment_amount_cents,
                total_amount_cents=total_amount_cents,
                has_interest=total_amount_cents > base_amount_cents,
            )
        )

    result = PaymentPricingResponse(
        payment_method="credit_card",
        currency=currency,
        base_amount_cents=base_amount_cents,
        options=options,
    )
    logger.info(
        "public pricing quote path fee_mode=%s payloads=%s responses=%s result=%s",
        fee_mode,
        provider_payloads,
        provider_responses,
        result.model_dump(),
    )
    return result


def _build_pass_through_credit_card_pricing(
    *,
    api_token: str,
    currency: str,
    base_amount_cents: int,
    max_installments: int,
) -> PaymentPricingResponse:
    currency_code = BLIMBOO_CURRENCY_MAP.get((currency or "").upper())
    if currency_code is None:
        result = build_fallback_credit_card_pricing(
            currency=currency,
            base_amount_cents=base_amount_cents,
            max_installments=max_installments,
        )
        logger.info("public pricing pass_through fallback unsupported currency result=%s", result.model_dump())
        return result

    provider_payloads: list[dict[str, Any]] = []
    provider_responses: list[Any] = []
    best_result: PaymentPricingResponse | None = None

    client = BlimbooAPIClient(settings.blimboo_api_base_url or "", api_token)
    amount = round(base_amount_cents / 100, 2)
    for interest_by in _resolve_interest_candidates("customer"):
        payload = {
            "currency": currency_code,
            "method": PAYMENT_METHOD_TO_BLIMBOO["credit_card"],
            "interest_by": interest_by,
            "advancing_receivables": 1,
            "amount": amount,
        }
        provider_payloads.append(payload)
        try:
            response = client.get_pricing(payload)
            provider_responses.append(response)
            options = _collect_pricing_options(response, max_installments=max_installments)
            if options:
                normalized_options = [
                    PaymentInstallmentOption(
                        installments=option.installments,
                        installment_amount_cents=option.installment_amount_cents,
                        total_amount_cents=option.total_amount_cents,
                        has_interest=option.total_amount_cents > base_amount_cents,
                    )
                    for option in options
                ]
                result = PaymentPricingResponse(
                    payment_method="credit_card",
                    currency=currency,
                    base_amount_cents=base_amount_cents,
                    options=normalized_options,
                )
                if any(option.total_amount_cents > base_amount_cents for option in normalized_options):
                    logger.info(
                        "public pricing pass_through success url=%s method=POST payloads=%s responses=%s result=%s",
                        f"{client.base_url}/pricing",
                        provider_payloads,
                        provider_responses,
                        result.model_dump(),
                    )
                    return result
                if best_result is None:
                    best_result = result
        except (BlimbooAPIError, ValueError) as exc:
            provider_responses.append({"error": str(exc)})
            continue

    if best_result is not None:
        logger.info(
            "public pricing pass_through success without interest url=%s method=POST payloads=%s responses=%s result=%s",
            f"{client.base_url}/pricing",
            provider_payloads,
            provider_responses,
            best_result.model_dump(),
        )
        return best_result

    logger.info(
        "public pricing pass_through fallback url=%s method=POST payloads=%s responses=%s",
        f"{client.base_url}/pricing",
        provider_payloads,
        provider_responses,
    )
    result = build_fallback_credit_card_pricing(
        currency=currency,
        base_amount_cents=base_amount_cents,
        max_installments=max_installments,
    )
    logger.info("public pricing pass_through fallback result=%s", result.model_dump())
    return result


def _build_fallback_pricing(sale: Sale) -> PaymentPricingResponse:
    base_amount_cents = sale.gross_amount or sale.amount or 0
    max_installments = _resolve_pricing_max_installments(sale)
    options = [
        PaymentInstallmentOption(
            installments=installments,
            installment_amount_cents=int(round(base_amount_cents / installments)),
            total_amount_cents=base_amount_cents,
            has_interest=False,
        )
        for installments in range(1, max_installments + 1)
    ]
    return PaymentPricingResponse(
        payment_method="credit_card",
        currency=(sale.currency or "BRL").upper(),
        base_amount_cents=base_amount_cents,
        options=options,
    )


@router.get("/payment-links/{token}/pricing", response_model=PaymentPricingResponse)
def get_payment_link_pricing(
    token: str,
    db: Session = Depends(get_db),
) -> PaymentPricingResponse:
    sale = _sale_by_payment_link_token(db, token)
    currency = (sale.currency or "BRL").upper()
    base_amount_cents = sale.gross_amount or sale.amount or 0
    max_installments = _resolve_pricing_max_installments(sale)
    api_token = get_agency_blimboo_token(db, sale.agency_id)
    if _sale_fee_mode(sale) == "pass_through":
        return _build_pass_through_credit_card_pricing(
            api_token=api_token,
            currency=currency,
            base_amount_cents=base_amount_cents,
            max_installments=max_installments,
        )

    merchant_pricing = fetch_credit_card_pricing(
        api_base_url=settings.blimboo_api_base_url or "",
        api_token=api_token,
        currency=currency,
        base_amount_cents=base_amount_cents,
        interest_mode="merchant",
        max_installments=max_installments,
    )
    if sale.interest_mode == "merchant":
        return merchant_pricing

    customer_pricing = fetch_credit_card_pricing(
        api_base_url=settings.blimboo_api_base_url or "",
        api_token=api_token,
        currency=currency,
        base_amount_cents=base_amount_cents,
        interest_mode="customer",
        max_installments=max_installments,
    )
    if sale.max_installments_no_interest:
        return merge_credit_card_pricing(
            currency=currency,
            base_amount_cents=base_amount_cents,
            merchant_pricing=merchant_pricing,
            customer_pricing=customer_pricing,
            max_installments=max_installments,
            max_installments_no_interest=sale.max_installments_no_interest,
        )
    return customer_pricing


def _sale_by_token(db: Session, token: str) -> Sale:
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.contract), joinedload(Sale.product))
        .filter(Sale.passenger_form_token == token)
        .first()
    )
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return sale


def _ensure_sale_supports_passengers(sale: Sale) -> None:
    if not sale_requires_passengers(sale):
        raise HTTPException(status_code=404, detail="Venda nao exige passageiros.")


def _sale_by_payment_link_token(db: Session, token: str) -> Sale:
    link = (
        db.query(SalePaymentLink)
        .options(
            joinedload(SalePaymentLink.sale)
            .joinedload(Sale.contract),
            joinedload(SalePaymentLink.sale).joinedload(Sale.items),
            joinedload(SalePaymentLink.sale).joinedload(Sale.passengers),
            joinedload(SalePaymentLink.sale).joinedload(Sale.product),
        )
        .filter(SalePaymentLink.token == token)
        .first()
    )
    if not link or not link.sale:
        raise HTTPException(status_code=404, detail="Link de pagamento nao encontrado.")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        link.status = SalePaymentLinkStatus.expired.value
        db.add(link)
        db.commit()
        raise HTTPException(status_code=410, detail="Este link expirou. Solicite um novo com a agencia.")
    return link.sale


def _sale_by_id(db: Session, sale_id: int) -> Sale:
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.contract), joinedload(Sale.product))
        .filter(Sale.id == sale_id)
        .first()
    )
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return sale


def _serialize_passenger_form(sale: Sale, db: Session) -> PassengerFormResponse:
    _ensure_sale_supports_passengers(sale)
    metadata = sale.metadata_json or {}
    consumed_capacity = metadata.get("consumed_capacity")
    if not isinstance(consumed_capacity, int):
        consumed_capacity = sale.passengers_required
    flags = sale_flags(sale)
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    items = [serialize_sale_item(item) for item in sale.items]
    groups = ensure_passenger_groups(sale, db)
    db.commit()
    passenger_groups = [serialize_passenger_group(group) for group in groups]
    contract = sale.contract
    agency = sale.agency or (sale.product.agency if sale.product else None)
    return PassengerFormResponse(
        sale_id=sale.id,
        agency_name=agency.name if agency else None,
        agency_logo_url=agency.logo_url if agency else None,
        agency_whatsapp=agency.cta_whatsapp if agency else None,
        product_title=sale.product_title,
        product_description=sale.product_description,
        passengers_required=sale.passengers_required,
        consumed_capacity=consumed_capacity,
        passenger_status=sale.passenger_status,
        payment_status=sale.payment_status,
        payout_status=sale.payout_status,
        amount_cents=sale.amount or sale.gross_amount,
        gross_amount_cents=sale.gross_amount or sale.amount,
        installment_amount_cents=_installment_amount(sale),
        installments=sale.installments,
        channel=sale.channel,
        customer_name=sale.customer_name,
        customer_email=sale.customer_email,
        customer_phone=sale.customer_phone,
        passengers=passengers,
        items=items,
        contract_id=contract.id if contract else None,
        contract_signature_link=contract.signature_link if contract else None,
        contract_signature_token=contract.signature_token if contract else None,
        groups=passenger_groups,
        boarding_locations=_boarding_locations_from_sale(sale),
        has_rooms=flags["has_rooms"],
        is_road_trip=flags["is_road_trip"],
        requires_passengers=flags["requires_passengers"],
        requires_rooming=flags["requires_rooming"],
    )


def _normalize_allowed_payment_methods(raw: Any) -> list[str]:
    return normalize_allowed_payment_methods(raw)


def _allowed_methods_for_sale(sale: Sale) -> list[str]:
    metadata = sale.metadata_json or {}
    metadata_methods = _normalize_allowed_payment_methods(metadata.get("allowed_payment_methods"))
    if metadata_methods:
        return metadata_methods
    if sale.product:
        return _normalize_allowed_payment_methods(getattr(sale.product, "allowed_payment_methods", None))
    return ["pix", "credit_card", "boleto"]


def _sale_fee_mode(sale: Sale) -> str:
    metadata = sale.metadata_json or {}
    value = str(metadata.get("fee_mode") or "absorb").strip().lower()
    return value if value in {"absorb", "pass_through"} else "absorb"


def _extract_provider_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        extracted: dict[str, Any] = {}
        nested_data = payload.get("data")
        if isinstance(nested_data, dict):
            extracted.update(nested_data)
        # Preserva campos de nivel raiz (ex.: boleto_url, linha_digitavel,
        # installments, links) que podem nao estar dentro de "data".
        for key, value in payload.items():
            if key == "data":
                continue
            if key not in extracted:
                extracted[key] = value
        return extracted or payload
    return {}


def _merge_provider_payload(previous: Any, current: Any) -> dict[str, Any]:
    prev = previous if isinstance(previous, dict) else {}
    curr = current if isinstance(current, dict) else {}
    merged: dict[str, Any] = dict(prev)
    for key, value in curr.items():
        if isinstance(value, dict) and isinstance(prev.get(key), dict):
            merged[key] = _merge_provider_payload(prev.get(key), value)
            continue
        merged[key] = value
    return merged


def _status_from_blimboo(payload: dict[str, Any]) -> SalePaymentStatus:
    charge = payload.get("charge") if isinstance(payload.get("charge"), dict) else {}
    raw_value = payload.get("status") or payload.get("provider_status") or charge.get("status") or "pending"
    if isinstance(raw_value, (int, float)):
        # Tabela oficial Blimboo:
        # 0 = Em aberto, 1 = Em dia, 2 = Concluido/Pago, 3 = Estornado, -1 = Cancelada.
        numeric = int(raw_value)
        if numeric == 2:
            return SalePaymentStatus.paid
        if numeric == 3:
            return SalePaymentStatus.refunded
        if numeric in {-1, 4, 5, 6}:
            return SalePaymentStatus.canceled
        if numeric == 1:
            return SalePaymentStatus.processing
        if numeric == 0:
            return SalePaymentStatus.pending
        return SalePaymentStatus.pending
    raw = str(raw_value).strip().lower()
    if raw in {"paid", "approved", "succeeded", "success", "captured"}:
        return SalePaymentStatus.paid
    if raw in {"canceled", "cancelled", "refused", "rejected", "failed", "denied"}:
        return SalePaymentStatus.canceled
    if raw in {"processing", "in_process", "pending", "waiting_payment", "awaiting_payment"}:
        return SalePaymentStatus.processing
    return SalePaymentStatus.pending


def _resolve_provider_charge_id(payload: dict[str, Any], sale_id: int) -> str:
    charge = payload.get("charge") if isinstance(payload.get("charge"), dict) else {}
    for key in ("id", "charge_id", "provider_charge_id", "transaction_id", "reference"):
        value = payload.get(key)
        if value:
            return str(value)
    for key in ("uuid", "id", "charge_id", "reference"):
        value = charge.get(key)
        if value:
            return str(value)
    return f"sale-{sale_id}-{uuid4().hex[:12]}"


def _resolve_quote_total_cents(payload: dict[str, Any]) -> int | None:
    return resolve_quote_total_cents_from_provider(payload)


def _update_sale_status_without_completion(sale: Sale, status: SalePaymentStatus, db: Session) -> None:
    sale.provider_status = status.value
    sale.payment_status = status.value
    if status in {SalePaymentStatus.processing, SalePaymentStatus.pending}:
        sale.financial_status = "pending"
        sale.payout_status = "pending"
        sale.paid_at = None
    db.add(sale)
    db.commit()
    db.refresh(sale)


def _status_message(status: SalePaymentStatus) -> str:
    if status == SalePaymentStatus.paid:
        return "Pagamento aprovado."
    if status == SalePaymentStatus.canceled:
        return "Pagamento recusado."
    return "Pagamento pendente."


@router.post("/sales/{sale_id}/confirm", response_model=PublicCheckoutResponse)
def confirm_sale_payment(
    sale_id: int,
    payload: PaymentConfirmationRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale = _sale_by_id(db, sale_id)
    if payload.customer:
        sale.customer_name = payload.customer.name
        sale.customer_email = payload.customer.email
        sale.customer_phone = payload.customer.phone
    allowed_methods = _allowed_methods_for_sale(sale)
    fee_mode = _sale_fee_mode(sale)
    state = build_checkout_state(
        sale=sale,
        payment_method=payload.payment_method or sale.payment_method or "pix",
        installments=payload.installments or sale.installments or 1,
        fee_mode=fee_mode,
        allowed_payment_methods=allowed_methods,
    )
    if state.payment_method == "credit_card":
        max_installments = _resolve_pricing_max_installments(sale)
        if state.installments > max_installments:
            raise HTTPException(status_code=400, detail=f"Parcelamento maximo permitido: {max_installments}x.")

    if not str(sale.customer_name or "").strip() or not str(sale.customer_email or "").strip() or not str(sale.customer_phone or "").strip():
        raise HTTPException(status_code=400, detail="Revise os dados obrigatorios do pagamento.")
    payer_passport = str(payload.payer_passport or payload.payer_document or "").strip()
    payer_nationality = str(payload.payer_nationality or "").strip().upper()
    if not payer_passport or not payer_nationality:
        raise HTTPException(status_code=400, detail="Revise os dados obrigatorios do pagamento.")

    api_token = get_agency_blimboo_token(db, sale.agency_id)
    if not api_token:
        raise HTTPException(status_code=400, detail="Token da Blimboo nao configurado para este usuario.")
    if not settings.blimboo_api_base_url:
        raise HTTPException(status_code=500, detail="Base URL da Blimboo nao configurada.")

    client = BlimbooAPIClient(settings.blimboo_api_base_url or "", api_token)
    quote_payload: dict[str, Any] | None = None
    quoted_total_cents: int | None = None
    selected_total_cents = int(payload.total_amount_cents or 0)
    if selected_total_cents > 0 and selected_total_cents >= state.base_amount_cents:
        quoted_total_cents = selected_total_cents
    if state.fee_mode == "pass_through":
        try:
            method_code = PAYMENT_METHOD_TO_BLIMBOO[state.payment_method]
            quote_response = client.quote_payment(
                {
                    "amount": round(state.base_amount_cents / 100, 2),
                    "currency": state.currency,
                    "method": method_code,
                    "payment_method": state.payment_method,
                    "installments": state.installments,
                }
            )
            quote_payload = _extract_provider_payload(quote_response)
            quote_total = _resolve_quote_total_cents(quote_payload)
            if quote_total and quote_total > 0:
                quoted_total_cents = quote_total
        except BlimbooAPIError:
            if not quoted_total_cents:
                quoted_total_cents = None

    pricing_mode = "pass_through" if quoted_total_cents and quoted_total_cents > 0 else state.fee_mode
    pricing = pricing_from_sale(state.base_amount_cents, quoted_total_cents, pricing_mode)
    order_id = f"sale-{sale.id}-{uuid4().hex[:8]}"
    charge_payload = build_charge_payload(
        ChargeBuildInput(
            payment_method=state.payment_method,
            installments=state.installments,
            currency=state.currency,
            amount_cents=pricing.final_amount_cents,
            description=sale.product_title or f"Venda #{sale.id}",
            customer=ChargeCustomerInput(
                name=str(sale.customer_name or "").strip(),
                email=str(sale.customer_email or "").strip(),
                phone_number=str(sale.customer_phone or "").strip(),
                nationality=payer_nationality,
                passport=payer_passport,
            ),
            order_id=order_id,
            metadata={
                "sale_id": sale.id,
                "agency_id": sale.agency_id,
                "fee_mode": state.fee_mode,
                "base_amount_cents": pricing.base_amount_cents,
                "final_amount_cents": pricing.final_amount_cents,
            },
            card=(
                ChargeCardInput(
                    holder_name=str(payload.card_holder_name or "").strip(),
                    number=str(payload.card_number or "").strip(),
                    exp_month=int(payload.card_exp_month or 0),
                    exp_year=int(payload.card_exp_year or 0),
                    cvv=str(payload.card_cvv or "").strip(),
                )
                if state.payment_method == "credit_card"
                else None
            ),
        )
    )
    provider_payload = create_blimboo_charge(client, charge_payload)

    provider_status = _status_from_blimboo(provider_payload)
    provider_charge_id = _resolve_provider_charge_id(provider_payload, sale.id)

    sale.provider = "blimboo"
    sale.provider_charge_id = provider_charge_id
    sale.payment_method = state.payment_method
    sale.installments = state.installments
    sale.currency = state.currency.lower()
    sale.base_amount = pricing.base_amount_cents
    sale.gross_amount = pricing.final_amount_cents
    sale.amount = pricing.final_amount_cents
    sale.gateway_fee_estimated = pricing.fee_amount_cents
    sale.agency_net_amount = pricing.base_amount_cents if state.fee_mode == "pass_through" else max(0, pricing.final_amount_cents - pricing.fee_amount_cents)
    provider_metadata = dict(sale.provider_metadata or {})
    provider_metadata["installment_amount"] = int(round(pricing.final_amount_cents / max(1, state.installments)))
    provider_metadata["last_provider_payload"] = provider_payload
    provider_metadata["last_provider_request"] = charge_payload
    provider_metadata["last_provider_quote"] = quote_payload
    sale.provider_metadata = provider_metadata
    db.add(sale)
    db.flush()

    if provider_status == SalePaymentStatus.paid:
        sale = complete_sale_payment(sale, db)
        response = serialize_checkout_response_from_sale(sale)
        response.message = "Pagamento aprovado."
        return response

    _update_sale_status_without_completion(sale, provider_status, db)
    response = serialize_checkout_response_from_sale(sale)
    if provider_status == SalePaymentStatus.canceled:
        response.message = "Pagamento recusado."
    elif provider_status == SalePaymentStatus.processing:
        response.message = "Pagamento pendente."
    else:
        response.message = "Pagamento pendente."
    return response


@router.get("/sales/{sale_id}/status", response_model=PublicCheckoutResponse)
def get_sale_payment_status(
    sale_id: int,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale = _sale_by_id(db, sale_id)

    terminal_statuses = {
        SalePaymentStatus.paid.value,
        SalePaymentStatus.canceled.value,
        SalePaymentStatus.refunded.value,
    }
    if sale.payment_status in terminal_statuses:
        response = serialize_checkout_response_from_sale(sale)
        response.message = _status_message(SalePaymentStatus(sale.payment_status))
        return response

    if sale.provider != "blimboo" or not sale.provider_charge_id:
        response = serialize_checkout_response_from_sale(sale)
        response.message = "Pagamento pendente."
        return response

    api_token = get_agency_blimboo_token(db, sale.agency_id)
    if not api_token or not settings.blimboo_api_base_url:
        response = serialize_checkout_response_from_sale(sale)
        response.message = "Pagamento pendente."
        return response

    client = BlimbooAPIClient(settings.blimboo_api_base_url or "", api_token)
    try:
        raw_payload = client.get_charge(sale.provider_charge_id)
        provider_payload = _extract_provider_payload(raw_payload)
    except BlimbooAPIError:
        response = serialize_checkout_response_from_sale(sale)
        response.message = "Pagamento pendente."
        return response

    provider_status = _status_from_blimboo(provider_payload)
    resolved_charge_id = _resolve_provider_charge_id(provider_payload, sale.id)
    if resolved_charge_id:
        sale.provider_charge_id = resolved_charge_id
    metadata = dict(sale.provider_metadata or {})
    metadata["last_provider_payload"] = _merge_provider_payload(
        metadata.get("last_provider_payload"),
        provider_payload,
    )
    metadata["last_provider_status_check_at"] = datetime.now(timezone.utc).isoformat()
    sale.provider_metadata = metadata
    db.add(sale)
    db.flush()

    if provider_status == SalePaymentStatus.paid:
        sale = complete_sale_payment(sale, db)
    else:
        _update_sale_status_without_completion(sale, provider_status, db)

    response = serialize_checkout_response_from_sale(sale)
    response.message = _status_message(provider_status)
    return response


@router.get("/sales/{token}", response_model=PassengerFormResponse)
def get_passenger_form(
    token: str,
    db: Session = Depends(get_db),
) -> PassengerFormResponse:
    sale = _sale_by_token(db, token)
    return _serialize_passenger_form(sale, db)


@router.post("/sales/{token}/passengers", response_model=PassengerFormResponse)
def submit_passenger_form(
    token: str,
    payload: list[PassengerInput],
    db: Session = Depends(get_db),
) -> PassengerFormResponse:
    sale = _sale_by_token(db, token)
    if sale.payment_status != SalePaymentStatus.paid.value:
        raise HTTPException(status_code=400, detail="Pagamento ainda nao confirmado.")
    _ensure_sale_supports_passengers(sale)
    sale = update_passengers_from_payload(sale, payload, db)
    return _serialize_passenger_form(sale, db)


@router.get("/sales/{token}/passenger-groups", response_model=PassengerGroupListResponse)
def get_public_passenger_groups(
    token: str,
    db: Session = Depends(get_db),
) -> PassengerGroupListResponse:
    sale = _sale_by_token(db, token)
    _ensure_sale_supports_passengers(sale)
    groups = ensure_passenger_groups(sale, db)
    db.commit()
    serialized = [serialize_passenger_group(group) for group in groups]
    total_capacity = sum(group.capacity for group in groups)
    contract = sale.contract
    return PassengerGroupListResponse(
        sale_id=sale.id,
        passenger_status=sale.passenger_status,
        passengers_required=sale.passengers_required,
        total_capacity=total_capacity,
        groups=serialized,
        contract_id=contract.id if contract else None,
        contract_signature_link=contract.signature_link if contract else None,
        contract_signature_token=contract.signature_token if contract else None,
    )


@router.put(
    "/sales/{token}/passenger-groups/{group_id}",
    response_model=PassengerGroupOut,
)
def save_public_passenger_group(
    token: str,
    group_id: int,
    payload: PassengerGroupSaveRequest,
    db: Session = Depends(get_db),
) -> PassengerGroupOut:
    sale = _sale_by_token(db, token)
    _ensure_sale_supports_passengers(sale)
    groups = ensure_passenger_groups(sale, db)
    group = next((entry for entry in groups if entry.id == group_id), None)
    if not group:
        group = (
            db.query(PassengerGroup)
            .filter(PassengerGroup.sale_id == sale.id, PassengerGroup.id == group_id)
            .first()
        )
    if not group:
        raise HTTPException(status_code=404, detail="Grupo de passageiros nao encontrado.")
    updated_group = save_group_passengers(group, payload.passengers, db)
    db.commit()
    db.refresh(updated_group)
    sale = updated_group.sale
    maybe_generate_contract_for_sale(sale, db)
    db.refresh(sale)
    return serialize_passenger_group(updated_group)


