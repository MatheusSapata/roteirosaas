export interface VehicleLayoutCellSchema {
  row: number;
  col: number;
  type: string;
  label?: string | null;
  selectable?: boolean;
  blocked?: boolean;
  meta?: Record<string, unknown> | null;
}

export interface VehicleDeckSchema {
  key: string;
  label: string;
  rows: number;
  cols: number;
  cells: VehicleLayoutCellSchema[];
}

export interface VehicleLayoutSchema {
  rows?: number | null;
  cols?: number | null;
  cells: VehicleLayoutCellSchema[];
  decks?: VehicleDeckSchema[] | null;
}

export interface VehicleLayoutSummary {
  id: number;
  name: string;
  vehicle_type: string;
  slug?: string | null;
  seat_count: number;
  row_count: number;
  column_count: number;
  thumbnail_url?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
  deck_mode: "single" | "double";
  deck_summaries: VehicleDeckSummary[];
}

export interface VehicleLayoutDetail extends VehicleLayoutSummary {
  layout_schema: VehicleLayoutSchema;
}

export interface VehicleDeckSummary {
  key: string;
  label: string;
  seat_count: number;
  rows: number;
  cols: number;
}

export interface VehicleLayoutListResponse {
  items: VehicleLayoutSummary[];
}

export interface VehicleLayoutPayload {
  name: string;
  vehicle_type: string;
  slug?: string | null;
  seat_count?: number | null;
  row_count?: number | null;
  column_count?: number | null;
  thumbnail_url?: string | null;
  is_active: boolean;
  layout_schema: VehicleLayoutSchema;
}

export interface VehiclePayload {
  name: string;
  plate?: string | null;
  photo_url?: string | null;
  partner_name?: string | null;
  layout_id?: number | null;
  is_active: boolean;
}

export interface VehicleOut extends VehiclePayload {
  id: number;
  created_at: string;
  updated_at?: string | null;
}

export interface VehicleListResponse {
  items: VehicleOut[];
}

export interface SeatPostSignatureStatus {
  sale_id: number;
  contract_id?: number | null;
  product_id: number;
  signature_status?: string | null;
  is_road_trip: boolean;
  has_layout: boolean;
  seats_generated: boolean;
  payment_confirmed: boolean;
  passengers_completed: boolean;
  can_select_seats: boolean;
  seats_selected: boolean;
  message?: string | null;
}

export type TripVehicleStatus = "inactive" | "active" | "full";

export interface TripVehicleSummary {
  id: number;
  product_id: number;
  display_name?: string | null;
  vehicle_id?: number | null;
  layout_id?: number | null;
  capacity: number;
  occupied_seats: number;
  available_seats: number;
  order_index: number;
  status: TripVehicleStatus;
  is_active: boolean;
  auto_activate_next: boolean;
  vehicle?: VehicleOut | null;
  layout?: VehicleLayoutSummary | null;
  seats_generated: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface TripVehicleInput {
  id?: number | null;
  vehicle_id?: number | null;
  layout_id: number;
  display_name?: string | null;
  capacity: number;
  order_index: number;
  status?: TripVehicleStatus | null;
  is_active: boolean;
  auto_activate_next: boolean;
}

export interface TripSeatOut {
  id: number;
  trip_vehicle_id: number;
  seat_number: string;
  seat_label?: string | null;
  seat_type: string;
  row_index: number;
  col_index: number;
  is_selectable: boolean;
  is_blocked: boolean;
  is_occupied: boolean;
  occupied_by_passenger_id?: number | null;
  occupied_by_passenger_name?: string | null;
  occupied_by_sale_id?: number | null;
  occupied_by_current_sale: boolean;
  deck_key?: string | null;
  deck_label?: string | null;
  deck_order?: number | null;
}

export interface PassengerSeatSummary {
  id: number;
  sale_id: number;
  name: string;
  seat_id?: number | null;
  seat_number?: string | null;
  seat_label?: string | null;
  status: "unassigned" | "assigned";
}

export interface SeatMapStats {
  total_seats: number;
  available_seats: number;
  occupied_seats: number;
  blocked_seats: number;
  assigned_passengers: number;
  pending_passengers: number;
}

export interface TripTransportConfigOut {
  product_id: number;
  is_road_trip: boolean;
  layout?: VehicleLayoutSummary | null;
  vehicle?: VehicleOut | null;
  boarding_notes?: string | null;
  seats_generated: boolean;
  seat_count: number;
  updated_at?: string | null;
  vehicles: TripVehicleSummary[];
}

export interface TripTransportConfigPayload {
  is_road_trip: boolean;
  layout_id?: number | null;
  vehicle_id?: number | null;
  boarding_notes?: string | null;
  regenerate_layout?: boolean;
  vehicles?: TripVehicleInput[] | null;
}

export interface SeatMapContext {
  product_id: number;
  product_name: string;
  product_public_id?: string | null;
  trip_date?: string | null;
  trip_vehicle?: TripVehicleSummary | null;
  vehicles: TripVehicleSummary[];
  layout?: VehicleLayoutDetail | null;
  seats: TripSeatOut[];
  passengers: PassengerSeatSummary[];
  stats: SeatMapStats;
  boarding_notes?: string | null;
  can_assign: boolean;
}

export interface SeatSelectionContext extends SeatMapContext {
  sale_id: number;
  sale_reference?: string | null;
  can_submit: boolean;
  message?: string | null;
  preference_notice?: string | null;
}

export interface SeatAssignmentPayload {
  passenger_id: number;
  seat_id: number;
}

export interface SeatAdminAssignmentPayload extends SeatAssignmentPayload {
  notes?: string | null;
  assignment_status?: string | null;
}

export interface SeatBlockPayload {
  seat_id: number;
  is_blocked: boolean;
  reason?: string | null;
}

export interface SeatHistoryEntry {
  id: number;
  passenger_id?: number | null;
  passenger_name?: string | null;
  sale_id?: number | null;
  old_seat_label?: string | null;
  new_seat_label?: string | null;
  changed_by_role: string;
  changed_by_user_id?: number | null;
  reason?: string | null;
  created_at: string;
}

export interface SeatHistoryResponse {
  items: SeatHistoryEntry[];
  has_more: boolean;
}
