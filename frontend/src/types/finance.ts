export interface StripeAccountStatus {
  connected: boolean;
  account_id: string | null;
  onboarding_completed: boolean;
  charges_enabled: boolean;
  payouts_enabled: boolean;
  email: string | null;
  country: string | null;
  currency: string | null;
  requirements: string[] | null;
}

export interface CheckoutCartItem {
  variation_id: string;
  quantity: number;
}

export interface CheckoutCustomer {
  name: string;
  email: string;
  phone: string;
}

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
  total_slots?: number | null;
  available_slots?: number | null;
  reserved_slots?: number | null;
  sold_slots?: number | null;
  sort_order: number;
}

export interface ProductSummary {
  id: number;
  public_id: string;
  agency_id?: number | null;
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
  variations: ProductVariation[];
}

export interface ProductDetail extends ProductSummary {
  created_at: string;
  updated_at?: string | null;
}

export interface ProductListResponse {
  items: ProductSummary[];
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
  total_slots?: number | null;
  available_slots?: number | null;
}

export interface ProductPayload {
  name: string;
  description?: string | null;
  status: string;
  agency_id?: number | null;
  trip_date?: string | null;
  date_is_flexible: boolean;
  inventory_strategy: "manual" | "unlimited";
  total_slots: number;
  available_slots: number;
  allow_oversell: boolean;
  variations: ProductVariationPayload[];
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
  amount_cents: number;
  currency: string;
  commission_cents: number;
  stripe_fee_cents: number | null;
  net_amount_cents: number | null;
  payment_method: string | null;
  installments: number;
  payment_status: string;
  financial_status: string;
  payout_status: string;
  passenger_status: string;
  passengers_required: number;
  channel: string;
  customer_name: string | null;
  customer_email: string | null;
  customer_phone: string | null;
}

export interface Passenger {
  id: number;
  name: string;
  cpf?: string | null;
  birthdate?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  boarding_location?: string | null;
  extras?: string | null;
}

export interface SaleDetail extends SaleSummary {
  passengers: Passenger[];
  items: SaleItem[];
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

export interface CheckoutIntentResponse {
  sale_id: number;
  client_secret: string;
  passenger_token: string;
}

export interface PassengerFormResponse {
  sale_id: number;
  product_title: string;
  passengers_required: number;
  passenger_status: string;
  passengers: Passenger[];
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
  items: CheckoutCartItem[];
  customer: CheckoutCustomer;
}

export interface PaymentLinkRequest extends PosCheckoutRequest {
  expires_in_minutes?: number;
}

export interface PaymentLinkResponse {
  sale_id: number;
  token: string;
  url: string;
}

export interface SaleItem {
  id: number;
  variation_public_id?: string | null;
  variation_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  currency: string;
  people_count: number;
  status: string;
}
