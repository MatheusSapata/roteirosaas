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

export interface SaleSummary {
  id: number;
  created_at: string;
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
