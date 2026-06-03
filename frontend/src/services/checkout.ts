import api from "./api";

export type CheckoutThemeMode = "light" | "dark";
export type CheckoutDiscountType = "fixed" | "percent";

export interface CheckoutAppearance {
  key: string;
  name: string;
  theme_mode: CheckoutThemeMode;
  desktop_image_url?: string | null;
  mobile_banner_url?: string | null;
  active: boolean;
}

export interface CheckoutOffer {
  key: string;
  title: string;
  footer_product_label: string;
  plan_key: string;
  billing_cycle: "monthly" | "annual";
  amount: string;
  active: boolean;
  subtitle?: string | null;
  checkout_key?: string | null;
}

export interface CheckoutCoupon {
  code: string;
  title: string;
  discount_type: CheckoutDiscountType;
  value: string;
  offer_keys: string[];
  active: boolean;
  usage_count?: number;
}

export interface CheckoutSettings {
  id: number;
  is_active: boolean;
  offers: CheckoutOffer[];
  coupons: CheckoutCoupon[];
  checkouts: CheckoutAppearance[];
  created_at: string;
  updated_at: string;
}

export interface CheckoutPublicConfig {
  theme_mode: CheckoutThemeMode;
  desktop_image_url?: string | null;
  mobile_banner_url?: string | null;
  offer: CheckoutOffer;
}

export interface CheckoutSessionPayload {
  offer_key: string;
  customer_name: string;
  customer_email: string;
  customer_document: string;
  customer_phone: string;
  customer_zipcode: string;
  coupon_code?: string | null;
  metadata?: Record<string, unknown>;
}

export interface CheckoutSession {
  token: string;
  offer_key: string;
  product_name: string;
  billing_cycle: string;
  amount: string;
  original_amount?: string | null;
  discount_amount?: string | null;
  applied_coupon_code?: string | null;
  status: string;
  payment_method?: string | null;
  pix_mode?: "automatic" | "conventional" | null;
  customer_name: string;
  customer_email: string;
  customer_document: string;
  customer_phone: string;
  customer_zipcode: string;
  pix_copy_paste?: string | null;
  pix_qr_code_base64?: string | null;
  pix_expiration_date?: string | null;
  paid_at?: string | null;
  password_defined_at?: string | null;
  user_exists: boolean;
  requires_password_setup: boolean;
  is_upgrade?: boolean;
  locked_profile_fields?: Record<string, boolean> | null;
}

export interface CheckoutCouponPreviewPayload {
  offer_key: string;
  coupon_code: string;
}

export interface CheckoutCouponPreview {
  offer_key: string;
  amount: string;
  original_amount: string;
  discount_amount: string;
  applied_coupon_code: string;
}

export interface CheckoutCardPayload {
  token: string;
  holder_name: string;
  card_number: string;
  expiry_month: string;
  expiry_year: string;
  ccv: string;
  installment_count: number;
  remote_ip?: string | null;
}

export interface CheckoutTrackPayload {
  event_name: string;
  step?: string | null;
  status?: string | null;
  payment_method?: string | null;
  duration_ms?: number | null;
  error_message?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface CheckoutTrackingItem {
  id: number;
  token: string;
  offer_key: string;
  customer_name: string;
  customer_email: string;
  customer_document?: string | null;
  customer_phone: string;
  customer_zipcode: string;
  payment_method_selected?: string | null;
  signed_at?: string | null;
  password_defined_at?: string | null;
  created_at: string;
  updated_at: string;
  events_count: number;
  success_events_count: number;
  error_events_count: number;
  last_event_name?: string | null;
  last_event_at?: string | null;
  last_ip_address?: string | null;
  last_ip_city?: string | null;
  last_ip_region?: string | null;
  last_ip_country?: string | null;
  total_time_seconds?: number | null;
  sessions_count?: number;
}

export interface CheckoutTrackingEventItem {
  id: number;
  token: string;
  offer_key: string;
  event_name: string;
  step?: string | null;
  status?: string | null;
  payment_method?: string | null;
  duration_ms?: number | null;
  error_message?: string | null;
  ip_address?: string | null;
  ip_country?: string | null;
  ip_region?: string | null;
  ip_city?: string | null;
  created_at: string;
}

export interface CheckoutTrackingDocumentDetail {
  customer_document: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  sessions_count: number;
  events_count: number;
  error_events_count: number;
  signed_count: number;
  password_defined_count: number;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  events: CheckoutTrackingEventItem[];
}

export interface CheckoutOfferReportItem {
  offer_key: string;
  offer_title: string;
  checkout_key?: string | null;
  is_active: boolean;
  signed_count: number;
  upgrade_count: number;
  direct_count: number;
  total_count: number;
  last_signed_at?: string | null;
}

export const getAdminCheckoutSettings = async () => {
  const response = await api.get<CheckoutSettings>("/admin/checkout-settings");
  return response.data;
};

export const saveAdminCheckoutSettings = async (payload: Omit<CheckoutSettings, "id" | "created_at" | "updated_at">) => {
  const response = await api.put<CheckoutSettings>("/admin/checkout-settings", payload);
  return response.data;
};

export const getCheckoutConfig = async (offerKey: string) => {
  const response = await api.get<CheckoutPublicConfig>(`/checkout/public/config/${offerKey}`);
  return response.data;
};

export const createCheckoutSession = async (payload: CheckoutSessionPayload) => {
  const response = await api.post<CheckoutSession>("/checkout/public/session", payload);
  return response.data;
};

export const createUpgradeCheckoutSession = async (offerKey: string, couponCode?: string | null) => {
  const response = await api.post<CheckoutSession>("/checkout/public/session/upgrade", {
    offer_key: offerKey,
    coupon_code: couponCode || null,
  });
  return response.data;
};

export const updateUpgradeCheckoutSessionDetails = async (
  token: string,
  payload: Pick<
    CheckoutSessionPayload,
    "customer_name" | "customer_email" | "customer_document" | "customer_phone" | "customer_zipcode"
  >
) => {
  const response = await api.put<CheckoutSession>(`/checkout/public/session/${encodeURIComponent(token)}/upgrade-details`, payload);
  return response.data;
};

export const previewCheckoutCoupon = async (payload: CheckoutCouponPreviewPayload) => {
  const response = await api.post<CheckoutCouponPreview>("/checkout/public/coupon-preview", payload);
  return response.data;
};

export const getCheckoutSession = async (token: string) => {
  const response = await api.get<CheckoutSession>(`/checkout/public/session/${token}`);
  return response.data;
};

export const refreshCheckoutSession = async (token: string) => {
  const response = await api.post<CheckoutSession>(`/checkout/public/session/${token}/refresh`);
  return response.data;
};

export const startPixCheckout = async (token: string) => {
  const response = await api.post<CheckoutSession>(`/checkout/public/session/${token}/pix`);
  return response.data;
};

export const startCardCheckout = async (token: string, payload: CheckoutCardPayload) => {
  const response = await api.post<CheckoutSession>(`/checkout/public/session/${token}/card`, payload);
  return response.data;
};

export const finishCheckoutPassword = async (token: string, password: string) => {
  const response = await api.post<{ detail: string; email: string }>(`/checkout/public/session/${token}/password`, {
    token,
    password,
  });
  return response.data;
};

export const trackCheckoutEvent = async (token: string, payload: CheckoutTrackPayload) => {
  await api.post<{ ok: boolean }>(`/checkout/public/session/${token}/track`, payload);
};

export const getAdminCheckoutTracking = async (offerKey?: string, limit = 200) => {
  const response = await api.get<CheckoutTrackingItem[]>("/admin/checkout-settings/tracking", {
    params: { offer_key: offerKey || undefined, limit },
  });
  return response.data;
};

export const getAdminCheckoutTrackingDocument = async (customerDocument: string, offerKey?: string) => {
  const response = await api.get<CheckoutTrackingDocumentDetail>(`/admin/checkout-settings/tracking/document/${encodeURIComponent(customerDocument)}`, {
    params: { offer_key: offerKey || undefined },
  });
  return response.data;
};

export const getAdminCheckoutOfferReports = async (params?: { startDate?: string | null; endDate?: string | null }) => {
  const response = await api.get<CheckoutOfferReportItem[]>("/admin/checkout-settings/reports/offers", {
    params: {
      start_date: params?.startDate || undefined,
      end_date: params?.endDate || undefined,
    },
  });
  return response.data;
};
