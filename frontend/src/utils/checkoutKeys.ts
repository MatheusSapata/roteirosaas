import type { InjectionKey } from "vue";

export interface ProductCheckoutItemPayload {
  variationId: string;
  name: string;
  quantity: number;
  unitAmount: number;
  currency: string;
  peopleCount: number;
}

export interface ProductCheckoutPayload {
  productId: string;
  productName: string;
  productDescription?: string | null;
  currency: string;
  totalAmount: number;
  passengersRequired: number;
  items: ProductCheckoutItemPayload[];
}

export interface PublicProductCheckoutBridge {
  startCheckout: (payload: ProductCheckoutPayload) => void;
}

export const PUBLIC_PRODUCT_CHECKOUT_KEY: InjectionKey<PublicProductCheckoutBridge | null> = Symbol(
  "public-product-checkout"
);
