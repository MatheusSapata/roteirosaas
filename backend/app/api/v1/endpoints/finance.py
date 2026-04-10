from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.models.passenger_group import PassengerGroup
from app.models.sale import Sale, SalePaymentStatus
from app.models.user import User
from app.schemas.finance import (
    AgencyBlimbooSettings,
    AgencyBlimbooSettingsPayload,
    PassengerGroupListResponse,
    PassengerGroupOut,
    PassengerGroupSaveRequest,
    PassengerInput,
    PassengerLinkResponse,
    PaymentLinkRequest,
    PaymentLinkResponse,
    PosCheckoutRequest,
    PublicCheckoutResponse,
    SaleDetail,
    SaleListResponse,
    SaleStatusSimulationRequest,
)
from app.schemas.products import (
    InventoryAdjustmentPayload,
    ProductDetail,
    ProductListResponse,
    ProductPayload,
    ProductBoardingLocationsPayload,
)
from app.schemas.rooming import (
    AutoMatchApplyPayload,
    AutoMatchApplyResponse,
    AutoMatchPreviewResponse,
    RoomAssignmentPayload,
    RoomingListResponse,
    RoomingRoomOut,
    RoomingRoomPayload,
    RoomingRoomUpdatePayload,
    MovePassengerPayload,
    ReplacePassengerPayload,
    SwapPassengersPayload,
)
from app.services.agency_integrations import (
    get_agency_payment_settings,
    get_user_default_agency_id,
    save_agency_blimboo_token,
)
from app.services.finance import (
    create_payment_link_sale,
    create_pos_sale,
    serialize_checkout_response,
    serialize_checkout_response_from_sale,
    serialize_sale,
    serialize_sale_item,
    simulate_sale_status,
    update_passengers_from_payload,
    sale_requires_passengers,
)
from app.services.passenger_groups import (
    ensure_passenger_groups,
    save_group_passengers,
    serialize_passenger,
    serialize_passenger_group,
)
from app.services.products import (
    adjust_inventory,
    create_product,
    delete_product as delete_product_service,
    get_product_by_public_id,
    list_products_for_user,
    serialize_product_detail,
    update_product,
    update_product_boarding_locations,
)
from app.services.rooming import (
    assign_passenger,
    apply_auto_match,
    create_room,
    get_rooming_list,
    move_passenger,
    preview_auto_match,
    replace_passenger,
    remove_passenger,
    rename_room,
    swap_passengers,
)

router = APIRouter()
settings = get_settings()


def _sale_or_404(db: Session, sale_id: int, user_id: int) -> Sale:
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.product))
        .filter(Sale.id == sale_id, Sale.user_id == user_id)
        .first()
    )
    if not sale:
        raise HTTPException(status_code=404, detail="Venda nao encontrada.")
    return sale


def _ensure_sale_supports_passengers(sale: Sale) -> None:
    if not sale_requires_passengers(sale):
        raise HTTPException(status_code=404, detail="Venda nao exige passageiros.")


def _blimboo_settings_response(record) -> AgencyBlimbooSettings:
    token = record.blimboo_api_token if record else None
    updated_at = record.updated_at if record else None
    return AgencyBlimbooSettings(token=token, has_token=bool(token), updated_at=updated_at)


@router.get("/settings/blimboo", response_model=AgencyBlimbooSettings)
def get_blimboo_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgencyBlimbooSettings:
    agency_id = get_user_default_agency_id(current_user, db)
    record = get_agency_payment_settings(db, agency_id)
    return _blimboo_settings_response(record)


@router.post("/settings/blimboo", response_model=AgencyBlimbooSettings)
def save_blimboo_settings(
    payload: AgencyBlimbooSettingsPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgencyBlimbooSettings:
    agency_id = get_user_default_agency_id(current_user, db)
    record = save_agency_blimboo_token(db, agency_id, payload.token or "")
    return _blimboo_settings_response(record)


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


@router.put("/products/{public_id}/boarding-locations", response_model=ProductDetail)
def set_product_boarding_locations(
    public_id: str,
    payload: ProductBoardingLocationsPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProductDetail:
    product = get_product_by_public_id(public_id, current_user, db)
    product = update_product_boarding_locations(product, payload.locations, current_user, db)
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
        raise HTTPException(status_code=400, detail="Produto invÃ¡lido.")
    sale, charge = create_pos_sale(
        db=db,
        product_public_id=public_id,
        payload=payload,
        current_user=current_user,
    )
    return serialize_checkout_response(sale, charge)


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
    query = (
        db.query(Sale)
        .options(joinedload(Sale.product))
        .filter(Sale.user_id == current_user.id)
        .order_by(Sale.created_at.desc())
    )
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
    passengers: list = []
    passenger_groups: list[PassengerGroupOut] = []
    groups: list[PassengerGroup] = []
    if sale_requires_passengers(sale):
        groups = ensure_passenger_groups(sale, db)
        passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
        passenger_groups = [serialize_passenger_group(group) for group in groups]
    items = [serialize_sale_item(item) for item in sale.items]
    return SaleDetail(
        **summary.model_dump(),
        passengers=passengers,
        items=items,
        passenger_groups=passenger_groups,
    )


@router.post("/sales/{sale_id}/passengers", response_model=SaleDetail)
def save_sale_passengers(
    sale_id: int,
    payload: list[PassengerInput],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SaleDetail:
    sale = _sale_or_404(db, sale_id, current_user.id)
    _ensure_sale_supports_passengers(sale)
    sale = update_passengers_from_payload(sale, payload, db)
    summary = serialize_sale(sale)
    groups = ensure_passenger_groups(sale, db)
    passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
    items = [serialize_sale_item(item) for item in sale.items]
    passenger_groups = [serialize_passenger_group(group) for group in groups]
    return SaleDetail(
        **summary.model_dump(),
        passengers=passengers,
        items=items,
        passenger_groups=passenger_groups,
    )


@router.post("/sales/{sale_id}/simulate-status", response_model=SaleDetail)
def simulate_sale_status_endpoint(
    sale_id: int,
    payload: SaleStatusSimulationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SaleDetail:
    sale = _sale_or_404(db, sale_id, current_user.id)
    try:
        target_status = SalePaymentStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Status invǭlido.") from exc
    sale = simulate_sale_status(sale, target_status, db)
    summary = serialize_sale(sale)
    passengers: list = []
    passenger_groups: list[PassengerGroupOut] = []
    if sale_requires_passengers(sale):
        groups = ensure_passenger_groups(sale, db)
        passengers = [serialize_passenger(passenger) for passenger in sale.passengers]
        passenger_groups = [serialize_passenger_group(group) for group in groups]
    else:
        groups = []
    items = [serialize_sale_item(item) for item in sale.items]
    return SaleDetail(
        **summary.model_dump(),
        passengers=passengers,
        items=items,
        passenger_groups=passenger_groups,
    )


@router.get("/sales/{sale_id}/passenger-form-link", response_model=PassengerLinkResponse)
def get_passenger_form_link(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PassengerLinkResponse:
    sale = _sale_or_404(db, sale_id, current_user.id)
    _ensure_sale_supports_passengers(sale)
    token = sale.passenger_form_token
    url = f"{settings.resolved_webapp_base_url}/passageiros/{token}"
    return PassengerLinkResponse(token=token, url=url)


@router.get("/sales/{sale_id}/passenger-groups", response_model=PassengerGroupListResponse)
def get_sale_passenger_groups(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PassengerGroupListResponse:
    sale = _sale_or_404(db, sale_id, current_user.id)
    _ensure_sale_supports_passengers(sale)
    groups = ensure_passenger_groups(sale, db)
    db.commit()
    db.refresh(sale)
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


@router.put("/passenger-groups/{group_id}/passengers", response_model=PassengerGroupOut)
def save_passenger_group_passengers(
    group_id: int,
    payload: PassengerGroupSaveRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PassengerGroupOut:
    group = (
        db.query(PassengerGroup)
        .join(Sale, PassengerGroup.sale_id == Sale.id)
        .filter(PassengerGroup.id == group_id, Sale.user_id == current_user.id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Grupo de passageiros nao encontrado.")
    sale = group.sale
    if not sale:
        raise HTTPException(status_code=404, detail="Venda associada ao grupo nao encontrada.")
    _ensure_sale_supports_passengers(sale)
    updated_group = save_group_passengers(group, payload.passengers, db)
    db.commit()
    db.refresh(updated_group)
    return serialize_passenger_group(updated_group)



@router.get("/products/{public_id}/rooming-list", response_model=RoomingListResponse)
def get_rooming_list_endpoint(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RoomingListResponse:
    product = get_product_by_public_id(public_id, current_user, db)
    return get_rooming_list(product, db)


@router.post("/products/{public_id}/rooming-list/rooms", response_model=RoomingRoomOut)
def create_room_endpoint(
    public_id: str,
    payload: RoomingRoomPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RoomingRoomOut:
    product = get_product_by_public_id(public_id, current_user, db)
    return create_room(product, payload, db)


@router.post(
    "/products/{public_id}/rooming-list/rooms/{room_id}/assignments",
    response_model=RoomingRoomOut,
)
def assign_passenger_to_room_endpoint(
    public_id: str,
    room_id: int,
    payload: RoomAssignmentPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RoomingRoomOut:
    product = get_product_by_public_id(public_id, current_user, db)
    return assign_passenger(product, room_id, payload, db)


@router.delete(
    "/products/{public_id}/rooming-list/rooms/{room_id}/assignments/{passenger_id}",
    response_model=RoomingRoomOut,
)
def remove_passenger_from_room_endpoint(
    public_id: str,
    room_id: int,
    passenger_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RoomingRoomOut:
    product = get_product_by_public_id(public_id, current_user, db)
    return remove_passenger(product, room_id, passenger_id, db)


@router.patch(
    "/products/{public_id}/rooming-list/rooms/{room_id}",
    response_model=RoomingRoomOut,
)
def rename_room_endpoint(
    public_id: str,
    room_id: int,
    payload: RoomingRoomUpdatePayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RoomingRoomOut:
    product = get_product_by_public_id(public_id, current_user, db)
    return rename_room(product, room_id, payload.name, db)


@router.post(
    "/products/{public_id}/rooming-list/auto-match/preview",
    response_model=AutoMatchPreviewResponse,
)
def preview_auto_match_endpoint(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AutoMatchPreviewResponse:
    product = get_product_by_public_id(public_id, current_user, db)
    return preview_auto_match(product, db)


@router.post(
    "/products/{public_id}/rooming-list/auto-match/apply",
    response_model=AutoMatchApplyResponse,
)
def apply_auto_match_endpoint(
    public_id: str,
    payload: AutoMatchApplyPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AutoMatchApplyResponse:
    product = get_product_by_public_id(public_id, current_user, db)
    return apply_auto_match(product, payload.preview_token, db)


@router.post(
    "/products/{public_id}/rooming-list/move-passenger",
    response_model=RoomingRoomOut,
)
def move_passenger_endpoint(
    public_id: str,
    payload: MovePassengerPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RoomingRoomOut:
    product = get_product_by_public_id(public_id, current_user, db)
    return move_passenger(product, payload.passenger_id, payload.target_room_id, db)


@router.post("/products/{public_id}/rooming-list/swap-passengers", status_code=204)
def swap_passengers_endpoint(
    public_id: str,
    payload: SwapPassengersPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    product = get_product_by_public_id(public_id, current_user, db)
    swap_passengers(
        product,
        incoming_passenger_id=payload.incoming_passenger_id,
        source_room_id=payload.source_room_id,
        target_room_id=payload.target_room_id,
        outgoing_passenger_id=payload.outgoing_passenger_id,
        db=db,
    )
    return Response(status_code=204)


@router.post("/products/{public_id}/rooming-list/replace-passenger", status_code=204)
def replace_passenger_endpoint(
    public_id: str,
    payload: ReplacePassengerPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    product = get_product_by_public_id(public_id, current_user, db)
    replace_passenger(
        product,
        incoming_passenger_id=payload.incoming_passenger_id,
        target_room_id=payload.target_room_id,
        outgoing_passenger_id=payload.outgoing_passenger_id,
        db=db,
    )
    return Response(status_code=204)


