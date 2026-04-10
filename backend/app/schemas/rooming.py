from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RoomingStatus = Literal["empty", "incomplete", "complete", "conflict"]
AlertTone = Literal["neutral", "warning", "danger"]


class RoomingProductSummary(BaseModel):
    id: int
    public_id: str
    name: str
    trip_date: str | None = None


class RoomingPassenger(BaseModel):
    id: int
    name: str
    passenger_type: str
    sale_id: int
    sale_reference: str
    order_code: str
    passenger_group_label: str | None = None
    variation_name: str | None = None
    boarding_location: str | None = None
    assigned_room_id: int | None = None
    accommodation_key: str | None = None
    capacity_required: int | None = None
    is_private: bool = False


class RoomingRoomOut(BaseModel):
    id: int
    name: str
    accommodation_label: str | None = None
    accommodation_key: str
    variation_public_id: str | None = None
    capacity: int
    occupancy: int
    status: RoomingStatus
    passengers: list[RoomingPassenger]
    locked: bool = False
    is_private: bool = False
    origin: str | None = None
    sale_id: int | None = None
    passenger_group_id: int | None = None


class RoomingStats(BaseModel):
    total_passengers: int
    passengers_with_room: int
    passengers_without_room: int
    total_rooms: int
    rooms_complete: int
    rooms_incomplete: int
    rooms_empty: int
    rooms_conflict: int


class RoomingAccommodationSection(BaseModel):
    key: str
    label: str
    capacity: int
    variation_public_id: str | None = None
    rooms: list[RoomingRoomOut]
    status_summary: dict[str, int]


class RoomingAlert(BaseModel):
    id: str
    message: str
    tone: AlertTone


class RoomingAccommodationOption(BaseModel):
    key: str
    label: str
    capacity: int
    variation_public_id: str | None = None
    product_room_id: int | None = None


class RoomingListResponse(BaseModel):
    product: RoomingProductSummary
    stats: RoomingStats
    accommodations: list[RoomingAccommodationSection]
    pending_passengers: list[RoomingPassenger]
    alerts: list[RoomingAlert]
    options: list[RoomingAccommodationOption]


class RoomingRoomPayload(BaseModel):
    label: str | None = Field(None, max_length=120)
    accommodation_label: str | None = Field(None, max_length=120)
    variation_public_id: str | None = None
    capacity: int | None = Field(None, ge=1)
    product_room_id: int | None = None


class RoomAssignmentPayload(BaseModel):
    passenger_id: int = Field(..., gt=0)


class RoomingRoomUpdatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class AutoMatchFillPreview(BaseModel):
    room_id: int
    room_name: str
    before: int
    after: int
    capacity: int
    passengers_added: list[RoomingPassenger]


class AutoMatchNewRoomPreview(BaseModel):
    room_type_key: str
    room_label: str
    capacity: int
    passengers: list[RoomingPassenger]


class AutoMatchPreviewSummary(BaseModel):
    pending_before: int
    pending_after: int
    passengers_to_allocate: int
    rooms_to_complete: int
    rooms_to_create: int


class AutoMatchPreviewResponse(BaseModel):
    preview_token: str
    summary: AutoMatchPreviewSummary
    fills: list[AutoMatchFillPreview]
    new_rooms: list[AutoMatchNewRoomPreview]
    remaining_unassigned: list[RoomingPassenger]


class AutoMatchApplyResponse(BaseModel):
    summary: AutoMatchPreviewSummary


class AutoMatchApplyPayload(BaseModel):
    preview_token: str = Field(..., min_length=8)


class MovePassengerPayload(BaseModel):
    passenger_id: int = Field(..., gt=0)
    target_room_id: int = Field(..., gt=0)


class SwapPassengersPayload(BaseModel):
    incoming_passenger_id: int = Field(..., gt=0)
    source_room_id: int = Field(..., gt=0)
    target_room_id: int = Field(..., gt=0)
    outgoing_passenger_id: int = Field(..., gt=0)


class ReplacePassengerPayload(BaseModel):
    incoming_passenger_id: int = Field(..., gt=0)
    target_room_id: int = Field(..., gt=0)
    outgoing_passenger_id: int = Field(..., gt=0)
