from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.transport import SeatAssignmentPayload, SeatPostSignatureStatus, SeatSelectionContext
from app.services.transport import (
    get_post_sale_status,
    get_post_signature_status,
    get_public_seat_selection_context_by_sale,
    get_public_seat_selection_context,
    select_seat_for_sale,
    select_seat_for_signature,
)

router = APIRouter()


@router.get("/signatures/{token}/status", response_model=SeatPostSignatureStatus)
def post_signature_status_endpoint(token: str, db: Session = Depends(get_db)) -> SeatPostSignatureStatus:
    return get_post_signature_status(token, db)


@router.get("/sales/{token}/status", response_model=SeatPostSignatureStatus)
def post_sale_status_endpoint(token: str, db: Session = Depends(get_db)) -> SeatPostSignatureStatus:
    return get_post_sale_status(token, db)


@router.get("/signatures/{token}/seats", response_model=SeatSelectionContext)
def get_public_seat_context_endpoint(
    token: str,
    trip_vehicle_id: int | None = None,
    db: Session = Depends(get_db),
) -> SeatSelectionContext:
    return get_public_seat_selection_context(token, db, trip_vehicle_id=trip_vehicle_id)


@router.get("/sales/{token}/seats", response_model=SeatSelectionContext)
def get_public_sale_seat_context_endpoint(
    token: str,
    trip_vehicle_id: int | None = None,
    db: Session = Depends(get_db),
) -> SeatSelectionContext:
    return get_public_seat_selection_context_by_sale(token, db, trip_vehicle_id=trip_vehicle_id)


@router.post("/signatures/{token}/seats", response_model=SeatSelectionContext)
def select_public_seat_endpoint(
    token: str,
    payload: SeatAssignmentPayload,
    db: Session = Depends(get_db),
) -> SeatSelectionContext:
    return select_seat_for_signature(token, payload, db)


@router.post("/sales/{token}/seats", response_model=SeatSelectionContext)
def select_public_sale_seat_endpoint(
    token: str,
    payload: SeatAssignmentPayload,
    db: Session = Depends(get_db),
) -> SeatSelectionContext:
    return select_seat_for_sale(token, payload, db)
