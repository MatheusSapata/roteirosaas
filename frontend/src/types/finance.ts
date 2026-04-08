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
  template_contract_id?: number | null;
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

export interface PublicCheckoutResponse {
  sale_id: number;
  checkout_reference: string;
  passenger_token: string;
  provider: string;
  provider_status: SalePaymentStatus;
  breakdown: PaymentBreakdown;
}

export interface PassengerFormResponse {
  sale_id: number;
  product_title: string;
  product_description?: string | null;
  passengers_required: number;
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
