from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.models.passenger_group import PassengerGroup
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
    SaleDetail,
)
from app.schemas.products import ProductDetail
from app.services.agency_integrations import get_agency_blimboo_token
from app.core.config import get_settings
from app.services.finance import (
    complete_sale_payment,
    create_checkout_sale,
    create_product_checkout_sale,
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
from app.services.payments.blimboo_api import BlimbooAPIClient, BlimbooAPIError
from app.services.payments.blimboo_pricing import (
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

BLIMBOO_CURRENCY_MAP = {
    "BRL": 1,
}

BLIMBOO_CREDIT_CARD_METHOD = 2


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
    preferred = 2 if normalized in {"customer", "client"} else 1
    alternatives = [preferred, 1 if preferred == 2 else 2]
    deduped: list[int] = []
    for candidate in alternatives:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _resolve_pricing_max_installments(sale: Sale) -> int:
    configured = sale.installments or 0
    if sale.channel == "page" and configured > 0:
        return max(1, min(configured, 12))
    return 12


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
    return PassengerFormResponse(
        sale_id=sale.id,
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
    sale.payment_method = payload.payment_method or sale.payment_method
    sale.installments = payload.installments or sale.installments
    sale = complete_sale_payment(sale, db)
    return serialize_checkout_response_from_sale(sale)


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


