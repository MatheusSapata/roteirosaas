from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.sale import Sale
from app.schemas.finance import (
    PassengerFormResponse,
    PassengerInput,
    ProductCheckoutRequest,
    PublicCheckoutRequest,
    PublicCheckoutResponse,
)
from app.schemas.products import ProductDetail
from app.services.finance import (
    create_checkout_sale,
    create_product_checkout_sale,
    serialize_passenger,
    update_passengers_from_payload,
)
from app.services.products import get_public_product, serialize_product_detail

router = APIRouter()


@router.post("/checkout/payment-intent", response_model=PublicCheckoutResponse)
def create_public_payment_intent(
    payload: PublicCheckoutRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale, client_secret = create_checkout_sale(
        db=db,
        page_id=payload.page_id,
        product_id=payload.product_id,
        section_id=payload.section_id,
        customer=payload.customer.model_dump(),
        source_url=payload.source_url,
        page_slug=payload.page_slug,
        agency_slug=payload.agency_slug,
    )
    return PublicCheckoutResponse(
        sale_id=sale.id,
        client_secret=client_secret,
        passenger_token=sale.passenger_form_token,
    )


@router.post("/products/checkout/payment-intent", response_model=PublicCheckoutResponse)
def create_product_checkout_intent(
    payload: ProductCheckoutRequest,
    db: Session = Depends(get_db),
) -> PublicCheckoutResponse:
    sale, client_secret = create_product_checkout_sale(
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
    return PublicCheckoutResponse(
        sale_id=sale.id,
        client_secret=client_secret,
        passenger_token=sale.passenger_form_token,
    )


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
        raise HTTPException(status_code=404, detail="Venda não encontrada.")
    return sale


@router.get("/sales/{token}", response_model=PassengerFormResponse)
def get_passenger_form(
    token: str,
    db: Session = Depends(get_db),
) -> PassengerFormResponse:
    sale = _sale_by_token(db, token)
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    return PassengerFormResponse(
        sale_id=sale.id,
        product_title=sale.product_title,
        passengers_required=sale.passengers_required,
        passenger_status=sale.passenger_status,
        passengers=passengers,
    )


@router.post("/sales/{token}/passengers", response_model=PassengerFormResponse)
def submit_passenger_form(
    token: str,
    payload: list[PassengerInput],
    db: Session = Depends(get_db),
) -> PassengerFormResponse:
    sale = _sale_by_token(db, token)
    if sale.payment_status != "succeeded":
        raise HTTPException(status_code=400, detail="Pagamento ainda não confirmado.")
    sale = update_passengers_from_payload(sale, payload, db)
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    return PassengerFormResponse(
        sale_id=sale.id,
        product_title=sale.product_title,
        passengers_required=sale.passengers_required,
        passenger_status=sale.passenger_status,
        passengers=passengers,
    )

