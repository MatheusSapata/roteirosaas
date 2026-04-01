import type { InjectionKey } from "vue";
import type { PriceItem, PricesSection } from "../types/page";

export interface PublicCheckoutPayload {
  section: PricesSection;
  item: PriceItem;
}

export interface PublicCheckoutBridge {
  startCheckout: (payload: PublicCheckoutPayload) => void;
}

export const PUBLIC_CHECKOUT_KEY: InjectionKey<PublicCheckoutBridge | null> = Symbol("public-checkout");
