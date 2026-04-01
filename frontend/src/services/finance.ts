import api from "./api";
import type {
  CheckoutIntentRequest,
  CheckoutIntentResponse,
  Passenger,
  PassengerFormResponse,
  PassengerLinkResponse,
  SaleDetail,
  SaleListResponse,
  StripeAccountStatus,
} from "../types/finance";

export const fetchStripeAccountStatus = () => api.get<StripeAccountStatus>("/finance/account");

export const createStripeOnboardingLink = () => api.post<{ url: string }>("/finance/account/connect");

export const listSales = (page = 1, pageSize = 20) =>
  api.get<SaleListResponse>("/finance/sales", { params: { page, page_size: pageSize } });

export const getSaleDetails = (saleId: number) => api.get<SaleDetail>(`/finance/sales/${saleId}`);

export const saveSalePassengers = (saleId: number, passengers: Passenger[]) =>
  api.post<SaleDetail>(`/finance/sales/${saleId}/passengers`, passengers);

export const getPassengerLink = (saleId: number) =>
  api.get<PassengerLinkResponse>(`/finance/sales/${saleId}/passenger-form-link`);

export const createPublicCheckoutIntent = (payload: CheckoutIntentRequest) =>
  api.post<CheckoutIntentResponse>("/public/finance/checkout/payment-intent", payload);

export const getPublicPassengerForm = (token: string) =>
  api.get<PassengerFormResponse>(`/public/finance/sales/${token}`);

export const submitPublicPassengers = (token: string, passengers: Passenger[]) =>
  api.post<PassengerFormResponse>(`/public/finance/sales/${token}/passengers`, passengers);
