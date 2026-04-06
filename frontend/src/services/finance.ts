import api from "./api";
import type {
  CheckoutIntentRequest,
  CheckoutIntentResponse,
  Passenger,
  PassengerFormResponse,
  PassengerLinkResponse,
  PaymentLinkRequest,
  PaymentLinkResponse,
  PosCheckoutRequest,
  ProductCheckoutRequest,
  ProductDetail,
  ProductListResponse,
  ProductPayload,
  InventoryAdjustmentPayload,
  SaleDetail,
  SaleListResponse,
  StripeAccountStatus,
} from "../types/finance";

export const fetchStripeAccountStatus = () => api.get<StripeAccountStatus>("/finance/account");

export const createStripeOnboardingLink = () => api.post<{ url: string }>("/finance/account/connect");

export const listProducts = () => api.get<ProductListResponse>("/finance/products");

export const getProductDetail = (publicId: string) => api.get<ProductDetail>(`/finance/products/${publicId}`);

export const getPublicProductDetail = (publicId: string) =>
  api.get<ProductDetail>(`/public/finance/products/${publicId}`);

export const createProduct = (payload: ProductPayload) => api.post<ProductDetail>("/finance/products", payload);

export const updateProduct = (publicId: string, payload: ProductPayload) =>
  api.put<ProductDetail>(`/finance/products/${publicId}`, payload);

export const deleteProduct = (publicId: string) => api.delete(`/finance/products/${publicId}`);

export const adjustProductInventory = (publicId: string, payload: InventoryAdjustmentPayload) =>
  api.post<ProductDetail>(`/finance/products/${publicId}/inventory`, payload);

export const createPosCheckout = (publicId: string, payload: PosCheckoutRequest) =>
  api.post<CheckoutIntentResponse>(`/finance/products/${publicId}/pos/checkout`, payload);

export const createProductPaymentLink = (publicId: string, payload: PaymentLinkRequest) =>
  api.post<PaymentLinkResponse>(`/finance/products/${publicId}/payment-links`, payload);

export const listSales = (page = 1, pageSize = 20) =>
  api.get<SaleListResponse>("/finance/sales", { params: { page, page_size: pageSize } });

export const getSaleDetails = (saleId: number) => api.get<SaleDetail>(`/finance/sales/${saleId}`);

export const saveSalePassengers = (saleId: number, passengers: Passenger[]) =>
  api.post<SaleDetail>(`/finance/sales/${saleId}/passengers`, passengers);

export const getPassengerLink = (saleId: number) =>
  api.get<PassengerLinkResponse>(`/finance/sales/${saleId}/passenger-form-link`);

export const createPublicCheckoutIntent = (payload: CheckoutIntentRequest) =>
  api.post<CheckoutIntentResponse>("/public/finance/checkout/payment-intent", payload);

export const createProductPublicCheckoutIntent = (payload: ProductCheckoutRequest) =>
  api.post<CheckoutIntentResponse>("/public/finance/products/checkout/payment-intent", payload);

export const getPublicPassengerForm = (token: string) =>
  api.get<PassengerFormResponse>(`/public/finance/sales/${token}`);

export const submitPublicPassengers = (token: string, passengers: Passenger[]) =>
  api.post<PassengerFormResponse>(`/public/finance/sales/${token}/passengers`, passengers);
