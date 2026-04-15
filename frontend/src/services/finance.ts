import api from "./api";
import type {
  AgencyBlimbooSettings,
  AgencyBlimbooSettingsPayload,
  CheckoutIntentRequest,
  Passenger,
  PassengerFormResponse,
  PassengerGroup,
  PassengerGroupListResponse,
  PassengerGroupSavePayload,
  PassengerLinkResponse,
  PaymentPricingResponse,
  PaymentLinkRequest,
  PaymentLinkResponse,
  PaymentLinkSimulationRequest,
  PaymentLinkSimulationResponse,
  PosCheckoutRequest,
  ProductCheckoutRequest,
  ProductDetail,
  ProductListResponse,
  ProductPayload,
  ProductBoardingLocationsPayload,
  InventoryAdjustmentPayload,
  ProductInventoryRebuildResponse,
  PublicCheckoutResponse,
  SaleDetail,
  SaleListResponse,
} from "../types/finance";

export const listProducts = () => api.get<ProductListResponse>("/finance/products");

export const rebuildProductInventory = () =>
  api.post<ProductInventoryRebuildResponse>("/finance/products/rebuild-inventory");

export const getProductDetail = (publicId: string) => api.get<ProductDetail>(`/finance/products/${publicId}`);

export const getPublicProductDetail = (publicId: string) =>
  api.get<ProductDetail>(`/public/finance/products/${publicId}`);

export const createProduct = (payload: ProductPayload) => api.post<ProductDetail>("/finance/products", payload);

export const updateProduct = (publicId: string, payload: ProductPayload) =>
  api.put<ProductDetail>(`/finance/products/${publicId}`, payload);

export const updateProductBoardingLocations = (publicId: string, payload: ProductBoardingLocationsPayload) =>
  api.put<ProductDetail>(`/finance/products/${publicId}/boarding-locations`, payload);

export const deleteProduct = (publicId: string) => api.delete(`/finance/products/${publicId}`);

export const adjustProductInventory = (publicId: string, payload: InventoryAdjustmentPayload) =>
  api.post<ProductDetail>(`/finance/products/${publicId}/inventory`, payload);

export const createPosCheckout = (publicId: string, payload: PosCheckoutRequest) =>
  api.post<PublicCheckoutResponse>(`/finance/products/${publicId}/pos/checkout`, payload);

export const createProductPaymentLink = (publicId: string, payload: PaymentLinkRequest) =>
  api.post<PaymentLinkResponse>(`/finance/products/${publicId}/payment-links`, payload);

export const simulateProductPaymentLink = (publicId: string, payload: PaymentLinkSimulationRequest) =>
  api.post<PaymentLinkSimulationResponse>(`/finance/products/${publicId}/payment-links/simulation`, payload);

export const listSales = (page = 1, pageSize = 20) =>
  api.get<SaleListResponse>("/finance/sales", { params: { page, page_size: pageSize } });

export const getSaleDetails = (saleId: number) => api.get<SaleDetail>(`/finance/sales/${saleId}`);

export const saveSalePassengers = (saleId: number, passengers: Passenger[]) =>
  api.post<SaleDetail>(`/finance/sales/${saleId}/passengers`, passengers);

export const getSalePassengerGroups = (saleId: number) =>
  api.get<PassengerGroupListResponse>(`/finance/sales/${saleId}/passenger-groups`);

export const savePassengerGroupPassengers = (groupId: number, payload: PassengerGroupSavePayload) =>
  api.put<PassengerGroup>(`/finance/passenger-groups/${groupId}/passengers`, payload);

export const getPassengerLink = (saleId: number) =>
  api.get<PassengerLinkResponse>(`/finance/sales/${saleId}/passenger-form-link`);

export const createPublicCheckoutIntent = (payload: CheckoutIntentRequest) =>
  api.post<PublicCheckoutResponse>("/public/finance/checkout/payment-intent", payload);

export const createProductPublicCheckoutIntent = (payload: ProductCheckoutRequest) =>
  api.post<PublicCheckoutResponse>("/public/finance/products/checkout/payment-intent", payload);

export const getPublicPaymentLinkDetails = (token: string) =>
  api.get<SaleDetail>(`/public/finance/payment-links/${token}`);

export const getPublicPaymentLinkPricing = (token: string) =>
  api.get<PaymentPricingResponse>(`/public/finance/payment-links/${token}/pricing`);

export const confirmPublicSale = (
  saleId: number,
  payload: { payment_method: string; installments: number },
) => api.post<PublicCheckoutResponse>(`/public/finance/sales/${saleId}/confirm`, payload);

export const simulateSaleStatus = (saleId: number, status: string) =>
  api.post<SaleDetail>(`/finance/sales/${saleId}/simulate-status`, { status });

export const getPublicPassengerForm = (token: string) =>
  api.get<PassengerFormResponse>(`/public/finance/sales/${token}`);

export const submitPublicPassengers = (token: string, passengers: Passenger[]) =>
  api.post<PassengerFormResponse>(`/public/finance/sales/${token}/passengers`, passengers);

export const getPublicPassengerGroups = (token: string) =>
  api.get<PassengerGroupListResponse>(`/public/finance/sales/${token}/passenger-groups`);

export const savePublicPassengerGroup = (token: string, groupId: number, payload: PassengerGroupSavePayload) =>
  api.put<PassengerGroup>(`/public/finance/sales/${token}/passenger-groups/${groupId}`, payload);

export const getBlimbooSettings = () => api.get<AgencyBlimbooSettings>("/finance/settings/blimboo");

export const saveBlimbooSettings = (payload: AgencyBlimbooSettingsPayload) =>
  api.post<AgencyBlimbooSettings>("/finance/settings/blimboo", payload);
