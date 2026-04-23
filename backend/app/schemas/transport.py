from __future__ import annotations

from datetime import datetime, date
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class VehicleLayoutCellSchema(BaseModel):
    row: int
    col: int
    type: str
    label: str | None = None
    selectable: bool = True
    blocked: bool = False
    meta: dict[str, Any] | None = None


class VehicleDeckSchema(BaseModel):
    key: str
    label: str
    rows: int = Field(ge=1)
    cols: int = Field(ge=1)
    cells: list[VehicleLayoutCellSchema] = Field(default_factory=list)

    @validator("cells", each_item=True)
    def _validate_deck_cell(cls, cell: VehicleLayoutCellSchema, values: dict[str, Any]) -> VehicleLayoutCellSchema:
        rows = values.get("rows")
        cols = values.get("cols")
        if rows is not None and (cell.row < 0 or cell.row >= rows):
            raise ValueError("Cell row outside deck bounds")
        if cols is not None and (cell.col < 0 or cell.col >= cols):
            raise ValueError("Cell column outside deck bounds")
        return cell


class VehicleLayoutSchema(BaseModel):
    rows: int | None = Field(default=None, ge=1)
    cols: int | None = Field(default=None, ge=1)
    cells: list[VehicleLayoutCellSchema] = Field(default_factory=list)
    decks: list[VehicleDeckSchema] | None = None

    @validator("cells", each_item=True)
    def _validate_single_deck_cell(cls, cell: VehicleLayoutCellSchema, values: dict[str, Any]) -> VehicleLayoutCellSchema:
        if values.get("decks"):
            return cell
        rows = values.get("rows")
        cols = values.get("cols")
        if rows is None or cols is None:
            raise ValueError("rows and cols are required for single deck layouts")
        if cell.row < 0 or cell.row >= rows:
            raise ValueError("Cell row outside layout bounds")
        if cell.col < 0 or cell.col >= cols:
            raise ValueError("Cell column outside layout bounds")
        return cell


class VehicleLayoutPayload(BaseModel):
    name: str
    vehicle_type: str = "custom"
    slug: str | None = None
    seat_count: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    thumbnail_url: str | None = None
    is_active: bool = True
    layout_schema: VehicleLayoutSchema


class VehicleLayoutSummary(BaseModel):
    id: int
    name: str
    vehicle_type: str
    slug: str | None = None
    seat_count: int
    row_count: int
    column_count: int
    thumbnail_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    deck_mode: Literal["single", "double"] = "single"
    deck_summaries: list["VehicleDeckSummary"] = Field(default_factory=list)


class VehicleLayoutDetail(VehicleLayoutSummary):
    layout_schema: VehicleLayoutSchema


class VehicleLayoutListResponse(BaseModel):
    items: list[VehicleLayoutSummary]


class VehiclePayload(BaseModel):
    name: str
    plate: str | None = None
    photo_url: str | None = None
    partner_name: str | None = None
    layout_id: int | None = None
    is_active: bool = True


class VehicleOut(VehiclePayload):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


class VehicleListResponse(BaseModel):
    items: list[VehicleOut]


class SeatPostSignatureStatus(BaseModel):
    sale_id: int
    contract_id: int | None = None
    product_id: int
    signature_status: str | None = None
    is_road_trip: bool
    has_layout: bool
    seats_generated: bool
    payment_confirmed: bool
    passengers_completed: bool
    can_select_seats: bool
    seats_selected: bool
    message: str | None = None


class SaleSeatSelectionProduct(BaseModel):
    product_id: int
    product_public_id: str
    product_name: str


class SaleSeatSelectionProductsResponse(BaseModel):
    sale_id: int
    items: list[SaleSeatSelectionProduct] = Field(default_factory=list)


class TripVehiclePayload(BaseModel):
    id: int | None = None
    vehicle_id: int | None = None
    layout_id: int
    display_name: str | None = None
    capacity: int = Field(gt=0)
    order_index: int = Field(ge=1)
    status: Literal["inactive", "active", "full"] | None = None
    is_active: bool = True
    auto_activate_next: bool = True


class TripTransportConfigPayload(BaseModel):
    is_road_trip: bool
    layout_id: int | None = None
    vehicle_id: int | None = None
    boarding_notes: str | None = None
    regenerate_layout: bool = False
    vehicles: list[TripVehiclePayload] | None = None


class TripTransportConfigOut(BaseModel):
    product_id: int
    is_road_trip: bool
    layout: VehicleLayoutSummary | None = None
    vehicle: VehicleOut | None = None
    boarding_notes: str | None = None
    seats_generated: bool
    seat_count: int
    updated_at: datetime | None = None
    vehicles: list[TripVehicleOut] = Field(default_factory=list)


class TripSeatOut(BaseModel):
    id: int
    trip_vehicle_id: int
    seat_number: str
    seat_label: str | None = None
    seat_type: str
    row_index: int
    col_index: int
    is_selectable: bool
    is_blocked: bool
    is_occupied: bool
    occupied_by_passenger_id: int | None = None
    occupied_by_passenger_name: str | None = None
    occupied_by_sale_id: int | None = None
    occupied_by_current_sale: bool = False
    deck_key: str | None = None
    deck_label: str | None = None
    deck_order: int | None = None


class PassengerSeatSummary(BaseModel):
    id: int
    sale_id: int
    name: str
    seat_id: int | None = None
    seat_number: str | None = None
    seat_label: str | None = None
    status: Literal["unassigned", "assigned"]


class SeatMapStats(BaseModel):
    total_seats: int
    available_seats: int
    occupied_seats: int
    blocked_seats: int
    assigned_passengers: int
    pending_passengers: int


class SeatMapContext(BaseModel):
    product_id: int
    product_name: str
    product_public_id: str | None = None
    trip_date: date | None = None
    departure_instance_id: int | None = None
    departure_id: int | None = None
    departure_date: date | None = None
    departure_time: str | None = None
    trip_vehicle: TripVehicleOut | None = None
    vehicles: list[TripVehicleOut] = Field(default_factory=list)
    layout: VehicleLayoutDetail | None = None
    seats: list[TripSeatOut]
    passengers: list[PassengerSeatSummary]
    stats: SeatMapStats
    boarding_notes: str | None = None
    can_assign: bool = True


class SeatSelectionContext(SeatMapContext):
    sale_id: int
    sale_reference: str | None = None
    can_submit: bool = True
    message: str | None = None
    preference_notice: str | None = None


class SeatAssignmentPayload(BaseModel):
    passenger_id: int
    seat_id: int


class SeatAdminAssignmentPayload(SeatAssignmentPayload):
    notes: str | None = None
    assignment_status: str | None = None


class SeatBlockPayload(BaseModel):
    seat_id: int
    is_blocked: bool
    reason: str | None = None


class SeatHistoryEntry(BaseModel):
    id: int
    passenger_id: int | None = None
    passenger_name: str | None = None
    sale_id: int | None = None
    old_seat_label: str | None = None
    new_seat_label: str | None = None
    changed_by_role: str
    changed_by_user_id: int | None = None
    reason: str | None = None
    created_at: datetime


class SeatHistoryResponse(BaseModel):
    items: list[SeatHistoryEntry]
    has_more: bool


class VehicleDeckSummary(BaseModel):
    key: str
    label: str
    seat_count: int
    rows: int
    cols: int


class TripVehicleOut(BaseModel):
    id: int
    product_id: int
    display_name: str | None = None
    vehicle_id: int | None = None
    layout_id: int | None = None
    capacity: int
    occupied_seats: int
    available_seats: int
    order_index: int
    status: Literal["inactive", "active", "full"]
    is_active: bool
    auto_activate_next: bool
    vehicle: VehicleOut | None = None
    layout: VehicleLayoutSummary | None = None
    seats_generated: bool
    created_at: datetime
    updated_at: datetime | None = None


class TripVehicleListResponse(BaseModel):
    items: list[TripVehicleOut]


VehicleLayoutSummary.model_rebuild()
VehicleLayoutDetail.model_rebuild()
TripTransportConfigOut.model_rebuild()
TripVehicleOut.model_rebuild()
