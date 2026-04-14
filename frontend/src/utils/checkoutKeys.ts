import type { InjectionKey } from "vue";
import type { CheckoutChildSelection } from "../types/finance";

export interface ProductCheckoutItemPayload {
  variationId: string;
  name: string;
  quantity: number;
  unitAmount: number;
  currency: string;
  peopleCount: number;
  consumedCapacity: number;
  childExtraAmount: number;
  childBreakdown: ProductCheckoutChildBreakdown[];
  children: CheckoutChildSelection;
}

export interface ProductCheckoutPayload {
  productId: string;
  productName: string;
  productDescription?: string | null;
  currency: string;
  totalAmount: number;
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
