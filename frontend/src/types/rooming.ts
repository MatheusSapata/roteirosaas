export type RoomingStatus = "empty" | "incomplete" | "complete" | "conflict";
export type RoomingAlertTone = "neutral" | "warning" | "danger";

export interface RoomingPassenger {
  id: number;
  name: string;
  passenger_type: string;
  sale_id: number;
  sale_reference: string;
  order_code: string;
  passenger_group_label?: string | null;
  variation_name?: string | null;
  boarding_location?: string | null;
  assigned_room_id?: number | null;
  accommodation_key?: string | null;
  capacity_required?: number | null;
  is_private?: boolean;
  consumes_capacity?: boolean;
}

export interface RoomingRoom {
  id: number;
  name: string;
  accommodation_label?: string | null;
  accommodation_key: string;
  variation_public_id?: string | null;
  capacity: number;
  occupancy: number;
  status: RoomingStatus;
  passengers: RoomingPassenger[];
  locked: boolean;
  is_private: boolean;
  origin?: string | null;
  sale_id?: number | null;
  passenger_group_id?: number | null;
}

export interface RoomingStats {
  total_passengers: number;
  passengers_with_room: number;
  passengers_without_room: number;
  total_rooms: number;
  rooms_complete: number;
  rooms_incomplete: number;
  rooms_empty: number;
  rooms_conflict: number;
}

export interface RoomingAccommodationSection {
  key: string;
  label: string;
  capacity: number;
  variation_public_id?: string | null;
  rooms: RoomingRoom[];
  status_summary: Record<RoomingStatus, number>;
}

export interface RoomingAlert {
  id: string;
  message: string;
  tone: RoomingAlertTone;
}

export interface RoomingAccommodationOption {
  key: string;
  label: string;
  capacity: number;
  variation_public_id?: string | null;
  product_room_id?: number | null;
}

export interface RoomingProductSummary {
  id: number;
  public_id: string;
  name: string;
  trip_date?: string | null;
}

export interface RoomingListResponse {
  product: RoomingProductSummary;
  stats: RoomingStats;
  accommodations: RoomingAccommodationSection[];
  pending_passengers: RoomingPassenger[];
  alerts: RoomingAlert[];
  options: RoomingAccommodationOption[];
}

export interface CreateRoomPayload {
  label?: string | null;
  accommodation_label?: string | null;
  variation_public_id?: string | null;
  capacity?: number | null;
  product_room_id?: number | null;
}

export interface AutoMatchPreviewSummary {
  pending_before: number;
  pending_after: number;
  passengers_to_allocate: number;
  rooms_to_complete: number;
  rooms_to_create: number;
}

export interface AutoMatchFillPreview {
  room_id: number;
  room_name: string;
  before: number;
  after: number;
  capacity: number;
  passengers_added: RoomingPassenger[];
}

export interface AutoMatchNewRoomPreview {
  room_type_key: string;
  room_label: string;
  capacity: number;
  passengers: RoomingPassenger[];
}

export interface AutoMatchPreviewResponse {
  preview_token: string;
  summary: AutoMatchPreviewSummary;
  fills: AutoMatchFillPreview[];
  new_rooms: AutoMatchNewRoomPreview[];
  remaining_unassigned: RoomingPassenger[];
}

export interface AutoMatchApplyResponse {
  summary: AutoMatchPreviewSummary;
}

export interface AutoMatchApplyPayload {
  preview_token: string;
}

export interface MovePassengerPayload {
  passenger_id: number;
  target_room_id: number;
}

export interface SwapPassengersPayload {
  incoming_passenger_id: number;
  source_room_id: number;
  target_room_id: number;
  outgoing_passenger_id: number;
}

export interface ReplacePassengerPayload {
  incoming_passenger_id: number;
  target_room_id: number;
  outgoing_passenger_id: number;
}
