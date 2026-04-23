import type { InjectionKey } from "vue";
import type { CheckoutChildSelection } from "../types/finance";

export interface ProductCheckoutItemPayload {
  productId: string;
  productName: string;
  productImageUrl?: string | null;
  variationId: string;
  name: string;
  dateLabel?: string | null;
  departureLabel?: string | null;
  quantity: number;
  unitAmount: number;
  currency: string;
  peopleCount: number;
  consumedCapacity: number;
  childExtraAmount: number;
  childBreakdown: ProductCheckoutChildBreakdown[];
  children: CheckoutChildSelection;
  departureId?: number | null;
}

export interface ProductCheckoutPayload {
  mode?: "single" | "multi";
  sectionId?: string;
  feeMode?: "absorb" | "pass_through";
  productId?: string;
  productName?: string;
  productDescription?: string | null;
  installments?: number;
  interestMode?: "merchant" | "customer";
  maxInstallmentsNoInterest?: number | null;
  allowedPaymentMethods?: Array<"pix" | "credit_card" | "boleto">;
  currency: string;
  totalAmount: number;
  subtotalAmount?: number;
  discountAmount?: number;
  discountLabel?: string | null;
  passengersRequired: number;
  consumedCapacity: number;
  items: ProductCheckoutItemPayload[];
}

export interface ProductCheckoutChildBreakdown {
  key: string;
  label: string;
  quantity: number;
  unitAmount: number;
  totalAmount: number;
}

export interface PublicProductCheckoutBridge {
  startCheckout: (payload: ProductCheckoutPayload) => void;
}

export const PUBLIC_PRODUCT_CHECKOUT_KEY: InjectionKey<PublicProductCheckoutBridge | null> = Symbol(
  "public-product-checkout"
);
