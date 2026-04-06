from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.models.sale import Sale
from app.models.user import User
from app.schemas.finance import (
    PassengerInput,
    PassengerLinkResponse,
    PaymentLinkRequest,
    PaymentLinkResponse,
    PosCheckoutRequest,
    PublicCheckoutResponse,
    SaleDetail,
    SaleListResponse,
    StripeAccountStatus,
    StripeOnboardingLinkResponse,
)
from app.schemas.products import (
    InventoryAdjustmentPayload,
    ProductDetail,
    ProductListResponse,
    ProductPayload,
)
from app.services.finance import (
    apply_payment_intent_update,
    create_onboarding_link,
    create_payment_link_sale,
    create_pos_sale,
    fetch_stripe_account_status,
    handle_payout_event,
    mark_sale_payment_failed,
    serialize_passenger,
    serialize_sale,
    serialize_sale_item,
    sync_account_status,
    update_passengers_from_payload,
)
from app.services.products import (
    adjust_inventory,
    create_product,
    delete_product as delete_product_service,
    get_product_by_public_id,
    list_products_for_user,
    serialize_product_detail,
    update_product,
)

router = APIRouter()
settings = get_settings()


def _finance_dashboard_url() -> str:
    base = settings.resolved_webapp_base_url
    return f"{base}/admin/financeiro"


def _sale_or_404(db: Session, sale_id: int, user_id: int) -> Sale:
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.user_id == user_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")
    return sale


@router.get("/account", response_model=StripeAccountStatus)
def get_stripe_account_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> StripeAccountStatus:
    record = fetch_stripe_account_status(current_user, db)
    requirements = []
    if record and isinstance(record.requirements, dict):
        for key in ("currently_due", "past_due"):
            pending = record.requirements.get(key) or []
            requirements.extend(pending)
    return StripeAccountStatus(
        connected=bool(current_user.stripe_account_id),
        account_id=current_user.stripe_account_id,
        onboarding_completed=bool(current_user.stripe_onboarding_completed),
        charges_enabled=bool(current_user.stripe_charges_enabled),
        payouts_enabled=bool(current_user.stripe_payouts_enabled),
        email=record.email if record else current_user.email,
        country=record.country if record else None,
        currency=record.default_currency if record else None,
        requirements=requirements or None,
    )


@router.post("/account/connect", response_model=StripeOnboardingLinkResponse)
def create_stripe_onboarding_link(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> StripeOnboardingLinkResponse:
    base_url = _finance_dashboard_url()
    url = create_onboarding_link(
        current_user,
        db,
        refresh_url=f"{base_url}?status=refresh",
        return_url=base_url,
    )
    return StripeOnboardingLinkResponse(url=url)


@router.get("/products", response_model=ProductListResponse)
def list_products_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    items = list_products_for_user(current_user, db)
    return ProductListResponse(items=items)


@router.post("/products", response_model=ProductDetail)
def create_product_endpoint(
    payload: ProductPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProductDetail:
    product = create_product(payload, current_user, db)
    return serialize_product_detail(product)


@router.get("/products/{public_id}", response_model=ProductDetail)
def get_product_endpoint(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProductDetail:
    product = get_product_by_public_id(public_id, current_user, db)
    return serialize_product_detail(product)


@router.put("/products/{public_id}", response_model=ProductDetail)
def update_product_endpoint(
    public_id: str,
    payload: ProductPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProductDetail:
    product = get_product_by_public_id(public_id, current_user, db)
    product = update_product(product, payload, current_user, db)
    return serialize_product_detail(product)


@router.delete("/products/{public_id}", status_code=204)
def delete_product_endpoint(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_product_service(public_id, current_user, db)
    return Response(status_code=204)


@router.post("/products/{public_id}/inventory", response_model=ProductDetail)
def adjust_inventory_endpoint(
    public_id: str,
    payload: InventoryAdjustmentPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProductDetail:
    product = get_product_by_public_id(public_id, current_user, db)
    product = adjust_inventory(product, payload, current_user, db)
    return serialize_product_detail(product)


@router.post("/products/{public_id}/pos/checkout", response_model=PublicCheckoutResponse)
def create_pos_checkout_endpoint(
    public_id: str,
    payload: PosCheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    if payload.product_id and payload.product_id != public_id:
        raise HTTPException(status_code=400, detail="Produto inválido.")
    sale, client_secret = create_pos_sale(
        db=db,
        product_public_id=public_id,
        payload=payload,
        current_user=current_user,
    )
    return PublicCheckoutResponse(
        sale_id=sale.id,
        client_secret=client_secret,
        passenger_token=sale.passenger_form_token,
    )


@router.post("/products/{public_id}/payment-links", response_model=PaymentLinkResponse)
def create_payment_link_endpoint(
    public_id: str,
    payload: PaymentLinkRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PaymentLinkResponse:
    link = create_payment_link_sale(
        db=db,
        product_public_id=public_id,
        payload=payload,
        current_user=current_user,
    )
    base_url = settings.resolved_webapp_base_url.rstrip("/")
    url = f"{base_url}/pagamentos/{link.token}"
    return PaymentLinkResponse(sale_id=link.sale_id, token=link.token, url=url)


@router.get("/sales", response_model=SaleListResponse)
def list_sales(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SaleListResponse:
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, 100))
    query = db.query(Sale).filter(Sale.user_id == current_user.id).order_by(Sale.created_at.desc())
    total = query.count()
    sales = query.offset((safe_page - 1) * safe_page_size).limit(safe_page_size).all()
    return SaleListResponse(
        items=[serialize_sale(sale) for sale in sales],
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )


@router.get("/sales/{sale_id}", response_model=SaleDetail)
def get_sale_details(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SaleDetail:
    sale = _sale_or_404(db, sale_id, current_user.id)
    summary = serialize_sale(sale)
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    items = [serialize_sale_item(item) for item in sale.items]
    return SaleDetail(**summary.model_dump(), passengers=passengers, items=items)


@router.post("/sales/{sale_id}/passengers", response_model=SaleDetail)
def save_sale_passengers(
    sale_id: int,
    payload: list[PassengerInput],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SaleDetail:
    sale = _sale_or_404(db, sale_id, current_user.id)
    sale = update_passengers_from_payload(sale, payload, db)
    summary = serialize_sale(sale)
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    items = [serialize_sale_item(item) for item in sale.items]
    return SaleDetail(**summary.model_dump(), passengers=passengers, items=items)


@router.get("/sales/{sale_id}/passenger-form-link", response_model=PassengerLinkResponse)
def get_passenger_form_link(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PassengerLinkResponse:
    sale = _sale_or_404(db, sale_id, current_user.id)
    token = sale.passenger_form_token
    url = f"{settings.resolved_webapp_base_url}/passageiros/{token}"
    return PassengerLinkResponse(token=token, url=url)


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_connect_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    webhook_secret = settings.stripe_connect_webhook_secret or settings.stripe_webhook_secret
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook não configurado.")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except ValueError as exc:  # pragma: no cover - validation
        raise HTTPException(status_code=400, detail="Payload inválido.") from exc
    except stripe.error.SignatureVerificationError as exc:  # pragma: no cover - validation
        raise HTTPException(status_code=400, detail="Assinatura inválida.") from exc

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})
    account_id = event.get("account")

    if event_type == "payment_intent.succeeded":
        payment_intent_id = data_object.get("id")
        if payment_intent_id:
            sale = db.query(Sale).filter(Sale.stripe_payment_intent_id == payment_intent_id).first()
            if sale:
                apply_payment_intent_update(sale, data_object, stripe_account=account_id, db=db)
    elif event_type == "payment_intent.payment_failed":
        payment_intent_id = data_object.get("id")
        if payment_intent_id:
            sale = db.query(Sale).filter(Sale.stripe_payment_intent_id == payment_intent_id).first()
            if sale:
                mark_sale_payment_failed(sale, db)
    elif event_type == "account.updated":
        account_identifier = data_object.get("id")
        if account_identifier:
            user = db.query(User).filter(User.stripe_account_id == account_identifier).first()
            if user:
                sync_account_status(user, data_object, db)
    elif event_type in {"payout.paid", "payout.failed"}:
        payout_id = data_object.get("id")
        if payout_id and account_id:
            status = "paid" if event_type == "payout.paid" else "failed"
            handle_payout_event(db=db, stripe_account=account_id, payout_id=payout_id, status=status)

    return {"received": True}
