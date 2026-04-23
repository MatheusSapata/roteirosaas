export interface PaymentBreakdown {
  base_amount_cents: number;
  gross_amount_cents: number;
  platform_fee_amount_cents: number;
  gateway_fee_estimated_cents: number;
  agency_net_amount_cents: number;
  installment_amount_cents: number;
  installments: number;
  currency: string;
  payment_method: string;
  spread_percentage: number;
}

export type SalePaymentStatus = "pending" | "processing" | "paid" | "canceled" | "refunded";

export type CheckoutChildSelection = Record<string, number>;

export interface CheckoutCartItem {
  variation_id: string;
  quantity: number;
  children?: CheckoutChildSelection;
  departure_id?: number | null;
}

export interface CheckoutCustomer {
  name: string;
  email: string;
  phone: string;
}

export interface ChildPricingRule {
  key: string;
  label: string;
  min_age: number;
  max_age: number;
  enabled: boolean;
  pricing_mode: "free" | "extra";
  extra_amount_cents: number;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
  max_quantity: number | null;
}

export interface ChildPricingRulePayload extends ChildPricingRule {}

export interface ProductVariation {
  id: number;
  public_id: string;
  name: string;
  description?: string | null;
  price_cents: number;
  currency: string;
  people_included: number;
  status: string;
  stock_mode: string;
  has_accommodation: boolean;
  accommodation_mode: "private" | "shared";
  room_capacity: number;
  slots_per_unit: number;
  total_slots?: number | null;
  available_slots?: number | null;
  reserved_slots?: number | null;
  sold_slots?: number | null;
  sort_order: number;
  child_policy_enabled: boolean;
  child_pricing_rules: ChildPricingRule[];
}

export interface ProductRoom {
  id: number;
  name: string;
  capacity: number;
  is_private: boolean;
  stock_quantity: number;
}

export interface ProductRoomPayload {
  id?: number | null;
  name: string;
  capacity: number;
  is_private: boolean;
  stock_quantity: number;
}

export interface ProductSummary {
  id: number;
  public_id: string;
  agency_id?: number | null;
  template_contract_id?: number | null;
  template_contract_name?: string | null;
  name: string;
  description?: string | null;
  status: string;
  trip_date?: string | null;
  date_is_flexible: boolean;
  total_slots: number;
  available_slots: number;
  reserved_slots: number;
  sold_slots: number;
  inventory_strategy: "manual" | "unlimited";
  allow_oversell: boolean;
  card_interest_mode: "merchant" | "customer";
  allowed_payment_methods: Array<"pix" | "credit_card" | "boleto">;
  schedule_mode: "fixed_date" | "recurring";
  timezone?: string | null;
  checkout_banner_url?: string | null;
  checkout_product_image_url?: string | null;
  variations: ProductVariation[];
  boarding_locations: string[];
  has_rooms: boolean;
  is_road_trip: boolean;
}

export interface ProductDetail extends ProductSummary {
  created_at: string;
  updated_at?: string | null;
  rooms: ProductRoom[];
}

export interface ProductListResponse {
  items: ProductSummary[];
}

export interface ProductInventoryRebuildResponse {
  scanned_products: number;
  updated_products: number;
}

export interface ProductVariationPayload {
  public_id?: string | null;
  name: string;
  description?: string | null;
  price_cents: number;
  currency: string;
  people_included: number;
  status: string;
  stock_mode: string;
  has_accommodation?: boolean;
  accommodation_mode: "private" | "shared";
  room_capacity: number;
  slots_per_unit: number;
  total_slots?: number | null;
  available_slots?: number | null;
  child_policy_enabled?: boolean;
  child_pricing_rules?: ChildPricingRulePayload[];
}

export interface ProductPayload {
  name: string;
  description?: string | null;
  status: string;
  agency_id?: number | null;
  template_contract_id?: number | null;
  trip_date?: string | null;
  date_is_flexible: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
  allow_oversell: boolean;
  card_interest_mode?: "merchant" | "customer";
  allowed_payment_methods?: Array<"pix" | "credit_card" | "boleto">;
  schedule_mode?: "fixed_date" | "recurring";
  timezone?: string | null;
  checkout_banner_url?: string | null;
  checkout_product_image_url?: string | null;
  variations: ProductVariationPayload[];
  boarding_locations: string[];
  has_rooms: boolean;
  is_road_trip: boolean;
  rooms: ProductRoomPayload[];
}

export interface ProductBoardingLocationsPayload {
  locations: string[];
}

export interface InventoryAdjustmentPayload {
  total_slots?: number | null;
  available_slots?: number | null;
  note?: string | null;
}

export interface SaleSummary {
  id: number;
  created_at: string;
  product_public_id?: string | null;
  product_title: string;
  product_description?: string | null;
  page_title?: string | null;
  page_slug?: string | null;
  amount_cents: number;
  base_amount_cents: number;
  gross_amount_cents: number;
  currency: string;
  commission_cents: number;
  platform_fee_amount_cents: number;
  gateway_fee_estimated_cents: number;
  agency_net_amount_cents: number;
  installment_amount_cents: number;
  net_amount_cents: number | null;
  spread_percentage: number;
  provider: string;
  provider_charge_id?: string | null;
  provider_status: SalePaymentStatus;
  paid_at?: string | null;
  payment_method: string | null;
  installments: number;
  payment_status: SalePaymentStatus;
  financial_status: string;
  payout_status: string;
  passenger_status: string;
  passengers_required: number;
  consumed_capacity: number;
  channel: string;
  customer_name: string | null;
  customer_email: string | null;
  customer_phone: string | null;
  boarding_locations: string[];
  has_rooms: boolean;
  is_road_trip: boolean;
  requires_passengers: boolean;
  requires_rooming: boolean;
}

export type PassengerType = "adult" | "child_free" | "child_paid";

export interface Passenger {
  id: number;
  passenger_group_id?: number | null;
  passenger_index?: number | null;
  type: PassengerType;
  name: string;
  cpf?: string | null;
  birthdate?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  boarding_location?: string | null;
  extras?: string | null;
}

export interface PassengerGroup {
  id: number;
  sale_item_id: number;
  product_id?: number | null;
  product_name: string;
  package_name?: string | null;
  label: string;
  group_index: number;
  capacity: number;
  occupied_slots: number;
  status: "pending" | "partial" | "complete";
  allows_children: boolean;
  slot_types: PassengerType[];
  passengers: Passenger[];
}

export interface PassengerGroupListResponse {
  sale_id: number;
  passenger_status: string;
  passengers_required: number;
  total_capacity: number;
  groups: PassengerGroup[];
  contract_id?: number | null;
  contract_signature_link?: string | null;
  contract_signature_token?: string | null;
}

export interface AgencyBlimbooSettings {
  token?: string | null;
  has_token: boolean;
  updated_at?: string | null;
}

export interface AgencyBlimbooSettingsPayload {
  token?: string | null;
}

export interface PassengerGroupSavePayload {
  passengers: {
    passenger_index: number;
    type: PassengerType;
    name: string;
    cpf?: string | null;
    birthdate?: string | null;
    phone?: string | null;
    whatsapp?: string | null;
    boarding_location?: string | null;
    extras?: string | null;
  }[];
}

export interface SaleDetail extends SaleSummary {
  passengers: Passenger[];
  items: SaleItem[];
  passenger_groups?: PassengerGroup[] | null;
}

export interface SaleListResponse {
  items: SaleSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface PassengerLinkResponse {
  token: string;
  url: string;
}

export interface CheckoutIntentRequest {
  page_id: number;
  product_id: string;
  section_id?: string | null;
  page_slug?: string | null;
  agency_slug?: string | null;
  source_url?: string | null;
  customer: {
    name: string;
    email: string;
    phone: string;
  };
}

export interface PublicCheckoutResponse {
  sale_id: number;
  checkout_reference: string;
  passenger_token?: string | null;
  provider: string;
  provider_status: SalePaymentStatus;
  breakdown: PaymentBreakdown;
  allowed_payment_methods?: Array<"pix" | "credit_card" | "boleto">;
  fee_mode?: "absorb" | "pass_through";
  provider_payload?: Record<string, unknown> | null;
  message?: string | null;
}

export interface SalePaymentMethodAvailabilityResponse {
  sale_id: number;
  allowed_payment_methods: Array<"pix" | "credit_card" | "boleto">;
  fee_mode: "absorb" | "pass_through";
}

export interface PassengerFormResponse {
  sale_id: number;
  agency_name?: string | null;
  agency_logo_url?: string | null;
  agency_whatsapp?: string | null;
  product_title: string;
  product_description?: string | null;
  passengers_required: number;
  consumed_capacity: number;
  passenger_status: string;
  payment_status: SalePaymentStatus;
  payout_status: string;
  amount_cents: number;
  gross_amount_cents: number;
  installment_amount_cents: number;
  installments: number;
  channel: string;
  customer_name?: string | null;
  customer_email?: string | null;
  customer_phone?: string | null;
  passengers: Passenger[];
  items: SaleItem[];
  contract_id?: number | null;
  contract_signature_link?: string | null;
  contract_signature_token?: string | null;
  groups: PassengerGroup[];
  boarding_locations: string[];
  has_rooms: boolean;
  is_road_trip: boolean;
  requires_passengers: boolean;
  requires_rooming: boolean;
}

export interface ProductCheckoutRequest {
  product_id: string;
  items: CheckoutCartItem[];
  customer: CheckoutCustomer;
  page_id?: number | null;
  page_slug?: string | null;
  agency_slug?: string | null;
  source_url?: string | null;
  channel?: string;
}

export interface PosCheckoutRequest {
  product_id: string;
  items: CheckoutCartItem[];
  customer: CheckoutCustomer;
  channel?: string;
}

export interface PaymentLinkRequest extends PosCheckoutRequest {
  expires_in_minutes?: number;
  interest_mode?: "merchant" | "customer";
  max_installments_no_interest?: number;
}

export interface PaymentLinkResponse {
  sale_id: number;
  token: string;
  url: string;
}

export interface PaymentInstallmentOption {
  installments: number;
  installment_amount_cents: number;
  total_amount_cents: number;
  has_interest: boolean;
}

export interface PaymentPricingResponse {
  payment_method: string;
  currency: string;
  base_amount_cents: number;
  options?: PaymentInstallmentOption[];
  prices?: Array<number | string>;
}

export interface PaymentMethodSummary {
  payment_method: string;
  currency: string;
  base_amount_cents: number;
  total_amount_cents: number;
  gateway_fee_estimated_cents: number;
  agency_net_amount_cents: number;
  installment_amount_cents: number;
  installments: number;
}

export interface PaymentLinkSimulationRequest {
  product_id: string;
  items: CheckoutCartItem[];
  customer?: CheckoutCustomer;
  channel?: string;
  interest_mode?: "merchant" | "customer";
  max_installments_no_interest?: number;
}

export interface PaymentLinkSimulationResponse {
  currency: string;
  base_amount_cents: number;
  pix: PaymentMethodSummary;
  boleto: PaymentMethodSummary;
  merchant_credit_card: PaymentPricingResponse;
  customer_credit_card: PaymentPricingResponse;
  effective_credit_card: PaymentPricingResponse;
  max_installments_no_interest?: number | null;
}

export interface SaleItem {
  id: number;
  product_id?: number | null;
  product_name?: string | null;
  product_image_url?: string | null;
  departure_id?: number | null;
  departure_date?: string | null;
  departure_time?: string | null;
  variation_public_id?: string | null;
  variation_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  currency: string;
  people_count: number;
  consumed_capacity: number;
  accommodation_mode: "private" | "shared";
  room_capacity: number;
  slots_per_unit: number;
  slots_reserved: number;
  occupancy_status: "pending_assignment" | "partial" | "complete";
  child_extra_amount_cents: number;
  child_breakdown: SaleItemChildBreakdown[];
  subtotal_amount_cents: number;
  discount_amount_cents: number;
  total_amount_cents: number;
  status: string;
}

export interface ScheduleTemplateWeekdayPayload {
  weekday: number;
  is_enabled: boolean;
}

export interface ScheduleTemplateTimePayload {
  time: string;
  capacity_override?: number | null;
  price_override?: number | null;
  sort_order: number;
  is_active: boolean;
}

export interface ScheduleTemplateCalendarDateTimePayload {
  time: string;
  capacity_override?: number | null;
  price_override?: number | null;
  is_active: boolean;
}

export interface ScheduleTemplateCalendarDatePayload {
  date: string;
  is_active: boolean;
  times: ScheduleTemplateCalendarDateTimePayload[];
}

export interface ScheduleTemplatePayload {
  template_type: "weekday" | "calendar";
  start_date: string;
  end_date?: string | null;
  timezone: string;
  default_capacity?: number | null;
  default_price?: number | null;
  generation_horizon_days: number;
  is_active: boolean;
  weekdays: ScheduleTemplateWeekdayPayload[];
  times: ScheduleTemplateTimePayload[];
  calendar_dates: ScheduleTemplateCalendarDatePayload[];
}

export interface ScheduleTemplate extends ScheduleTemplatePayload {
  id: number;
  product_id: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DepartureSummary {
  id: number;
  product_id: number;
  schedule_template_id?: number | null;
  date: string;
  time: string;
  starts_at: string;
  ends_at?: string | null;
  timezone: string;
  status: "draft" | "active" | "full" | "closed" | "canceled";
  capacity_total: number;
  capacity_reserved: number;
  capacity_sold: number;
  capacity_available: number;
  price_override?: number | null;
  is_manual_override: boolean;
  notes?: string | null;
  source_type?: string | null;
}

export interface DepartureListResponse {
  items: DepartureSummary[];
}

export interface ScheduleGenerateResponse {
  generated: number;
  updated: number;
  total: number;
}

export interface ScheduleExceptionPayload {
  exception_type: "block_date" | "block_time" | "cancel_departure" | "close_departure" | "capacity_override" | "price_override";
  schedule_template_id?: number | null;
  date: string;
  time?: string | null;
  new_status?: "draft" | "active" | "full" | "closed" | "canceled" | null;
  capacity_override?: number | null;
  price_override?: number | null;
  reason?: string | null;
}

export interface ScheduleException extends ScheduleExceptionPayload {
  id: number;
  product_id: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ScheduleExceptionListResponse {
  items: ScheduleException[];
}

export interface PublicDepartureCalendarDay {
  date: string;
  day: number;
  available: boolean;
  departures_count: number;
  low_availability: boolean;
  status: string;
}

export interface PublicDepartureCalendarResponse {
  product_id: number;
  month: string;
  timezone: string;
  days: PublicDepartureCalendarDay[];
}

export interface PublicDepartureTimeSlot {
  departure_id: number;
  time: string;
  available: boolean;
  remaining_capacity: number;
  effective_price?: number | null;
  status: string;
  label: string;
  low_availability: boolean;
}

export interface PublicDepartureTimesResponse {
  product_id: number;
  date: string;
  timezone: string;
  slots: PublicDepartureTimeSlot[];
}

export interface PublicDepartureValidateResponse {
  valid: boolean;
  reason?: string | null;
  final_price?: number | null;
  snapshot?: DepartureSummary | null;
}

export interface SectionDiscountConfig {
  rule_type?: "min_quantity" | "exact_combination" | null;
  min_selected_products?: number | null;
  required_product_ids?: string[];
  discount_type?: "fixed" | "percentage" | null;
  discount_value?: number | null;
}

export interface SectionProductSelection {
  product_id: string;
  items: CheckoutCartItem[];
}

export interface SectionProductsCheckoutRequest {
  page_id: number;
  section_id: string;
  customer: CheckoutCustomer;
  products: SectionProductSelection[];
  discount?: SectionDiscountConfig | null;
  page_slug?: string | null;
  agency_slug?: string | null;
  source_url?: string | null;
  channel?: string;
}

export interface SectionProductsPricingRequest {
  page_id: number;
  section_id: string;
  fee_mode?: "absorb" | "pass_through";
  products: SectionProductSelection[];
  base_amount_cents: number;
  currency: string;
  discount?: SectionDiscountConfig | null;
  page_slug?: string | null;
  agency_slug?: string | null;
  source_url?: string | null;
  channel?: string;
}

export interface SaleItemChildBreakdown {
  key: string;
  label: string;
  quantity: number;
  unit_amount_cents: number;
  total_amount_cents: number;
  counts_towards_capacity: boolean;
  counts_as_passenger: boolean;
}
