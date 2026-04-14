from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.product import Product
from app.models.user import User
from app.models.transport import SeatAssignmentActor
from app.schemas.transport import (
    SeatAdminAssignmentPayload,
    SeatBlockPayload,
    SeatHistoryResponse,
    SeatMapContext,
    TripTransportConfigOut,
    TripTransportConfigPayload,
    VehicleLayoutDetail,
    VehicleLayoutListResponse,
    VehicleLayoutPayload,
    VehicleListResponse,
    VehicleOut,
    VehiclePayload,
)
from app.services.products import get_product_by_public_id
from app.services.transport import (
    assign_seat_to_passenger,
    block_trip_seat,
    create_vehicle,
    create_vehicle_layout,
    delete_vehicle,
    delete_vehicle_layout,
    duplicate_vehicle_layout,
    drop_passenger_assignment,
    get_trip_seat_map,
    get_trip_transport_config,
    get_vehicle_layout_detail,
    list_seat_history,
    list_vehicle_layouts,
    list_vehicles,
    save_trip_transport_config,
    update_vehicle,
    update_vehicle_layout,
)

router = APIRouter()


def _product(public_id: str, user: User, db: Session) -> Product:
    return get_product_by_public_id(public_id, user, db)


@router.get("/layouts", response_model=VehicleLayoutListResponse)
def list_layouts_endpoint(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> VehicleLayoutListResponse:
    return list_vehicle_layouts(user, db)


@router.post("/layouts", response_model=VehicleLayoutDetail)
def create_layout_endpoint(
    payload: VehicleLayoutPayload,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleLayoutDetail:
    return create_vehicle_layout(user, payload, db)


@router.get("/layouts/{layout_id}", response_model=VehicleLayoutDetail)
def get_layout_endpoint(
    layout_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleLayoutDetail:
    return get_vehicle_layout_detail(user, layout_id, db)


@router.put("/layouts/{layout_id}", response_model=VehicleLayoutDetail)
def update_layout_endpoint(
    layout_id: int,
    payload: VehicleLayoutPayload,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleLayoutDetail:
    return update_vehicle_layout(user, layout_id, payload, db)


@router.post("/layouts/{layout_id}/duplicate", response_model=VehicleLayoutDetail)
def duplicate_layout_endpoint(
    layout_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleLayoutDetail:
    return duplicate_vehicle_layout(user, layout_id, db)


@router.delete("/layouts/{layout_id}", status_code=204)
def delete_layout_endpoint(
    layout_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    delete_vehicle_layout(user, layout_id, db)


@router.get("/vehicles", response_model=VehicleListResponse)
def list_vehicles_endpoint(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleListResponse:
    return list_vehicles(user, db)


@router.post("/vehicles", response_model=VehicleOut)
def create_vehicle_endpoint(
    payload: VehiclePayload,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleOut:
    return create_vehicle(user, payload, db)


@router.put("/vehicles/{vehicle_id}", response_model=VehicleOut)
def update_vehicle_endpoint(
    vehicle_id: int,
    payload: VehiclePayload,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> VehicleOut:
    return update_vehicle(user, vehicle_id, payload, db)


@router.delete("/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle_endpoint(
    vehicle_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    delete_vehicle(user, vehicle_id, db)


@router.get("/products/{public_id}/transport-config", response_model=TripTransportConfigOut)
def get_transport_config_endpoint(
    public_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TripTransportConfigOut:
    product = _product(public_id, user, db)
    return get_trip_transport_config(product, db)


@router.put("/products/{public_id}/transport-config", response_model=TripTransportConfigOut)
def save_transport_config_endpoint(
    public_id: str,
    payload: TripTransportConfigPayload,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TripTransportConfigOut:
    product = _product(public_id, user, db)
    return save_trip_transport_config(product, payload, db)


@router.get("/products/{public_id}/seat-map", response_model=SeatMapContext)
def get_seat_map_endpoint(
    public_id: str,
    trip_vehicle_id: int | None = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SeatMapContext:
    product = _product(public_id, user, db)
    return get_trip_seat_map(product, db, trip_vehicle_id=trip_vehicle_id)


@router.post("/products/{public_id}/seats/assignments", response_model=SeatMapContext)
def assign_seat_endpoint(
    public_id: str,
    payload: SeatAdminAssignmentPayload,
    trip_vehicle_id: int | None = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SeatMapContext:
    product = _product(public_id, user, db)
    assign_seat_to_passenger(
        product,
        payload,
        actor=SeatAssignmentActor.admin,
        db=db,
        user=user,
        notes=payload.notes,
        status_override=payload.assignment_status,
    )
    return get_trip_seat_map(product, db, trip_vehicle_id=trip_vehicle_id)


@router.delete("/products/{public_id}/seats/passengers/{passenger_id}", status_code=204)
def remove_assignment_endpoint(
    public_id: str,
    passenger_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    product = _product(public_id, user, db)
    drop_passenger_assignment(
        product,
        passenger_id=passenger_id,
        actor=SeatAssignmentActor.admin,
        db=db,
        user=user,
        reason="Removido manualmente",
    )


@router.post("/products/{public_id}/seats/block", response_model=SeatMapContext)
def block_seat_endpoint(
    public_id: str,
    payload: SeatBlockPayload,
    trip_vehicle_id: int | None = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SeatMapContext:
    product = _product(public_id, user, db)
    block_trip_seat(product, payload, db, user=user)
    return get_trip_seat_map(product, db, trip_vehicle_id=trip_vehicle_id)


@router.get("/products/{public_id}/seat-history", response_model=SeatHistoryResponse)
def seat_history_endpoint(
    public_id: str,
    limit: int = 20,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SeatHistoryResponse:
    product = _product(public_id, user, db)
    normalized_limit = max(1, min(limit, 100))
    return list_seat_history(product, normalized_limit, db)
