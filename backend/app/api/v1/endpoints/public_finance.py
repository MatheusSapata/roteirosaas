from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.sale import Sale, SalePaymentStatus
from app.schemas.finance import (
    PaymentConfirmationRequest,
    PassengerFormResponse,
    PassengerInput,
    ProductCheckoutRequest,
    PublicCheckoutRequest,
    PublicCheckoutResponse,
)
from app.schemas.products import ProductDetail
from app.services.finance import (
    complete_sale_payment,
    create_checkout_sale,
    create_product_checkout_sale,
    serialize_checkout_response,
    serialize_checkout_response_from_sale,
    serialize_passenger,
    serialize_sale_item,
    update_passengers_from_payload,
    _installment_amount,
)
from app.services.products import get_public_product, serialize_product_detail

router = APIRouter()


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


def _sale_by_token(db: Session, token: str) -> Sale:
    sale = db.query(Sale).filter(Sale.passenger_form_token == token).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return sale


def _sale_by_id(db: Session, sale_id: int) -> Sale:
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return sale


def _serialize_passenger_form(sale: Sale) -> PassengerFormResponse:
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    items = [serialize_sale_item(item) for item in sale.items]
    return PassengerFormResponse(
        sale_id=sale.id,
        product_title=sale.product_title,
        product_description=sale.product_description,
        passengers_required=sale.passengers_required,
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
    )


@router.post("/sales/{sale_id}/confirm", response_model=PublicCheckoutResponse)
def confirm_sale_payment(
    sale_id: int,
    payload: PaymentConfirmationRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale = _sale_by_id(db, sale_id)
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
    return _serialize_passenger_form(sale)


@router.post("/sales/{token}/passengers", response_model=PassengerFormResponse)
def submit_passenger_form(
    token: str,
    payload: list[PassengerInput],
    db: Session = Depends(get_db),
) -> PassengerFormResponse:
    sale = _sale_by_token(db, token)
    if sale.payment_status != SalePaymentStatus.paid.value:
        raise HTTPException(status_code=400, detail="Pagamento ainda nao confirmado.")
    sale = update_passengers_from_payload(sale, payload, db)
    return _serialize_passenger_form(sale)
