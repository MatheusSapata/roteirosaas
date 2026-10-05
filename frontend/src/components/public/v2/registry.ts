import { defineAsyncComponent, type Component } from "vue";
import type { SectionType } from "../../../types/page";
import type { PageDesign } from "../../../utils/pageDesign";

/**
 * Seções que já têm visual novo. As que ainda não estão aqui continuam com o
 * componente antigo mesmo em páginas no visual novo.
 */
export const v2Components: Partial<Record<SectionType, Component>> = {
  hero: defineAsyncComponent(() => import("./V2Hero.vue")),
  countdown: defineAsyncComponent(() => import("./V2Countdown.vue")),
  story: defineAsyncComponent(() => import("./V2Story.vue")),
  reasons: defineAsyncComponent(() => import("./V2Reasons.vue")),
  itinerary: defineAsyncComponent(() => import("./V2Itinerary.vue")),
  gallery: defineAsyncComponent(() => import("./V2Gallery.vue")),
  photo: defineAsyncComponent(() => import("./V2Photo.vue")),
  prices: defineAsyncComponent(() => import("./V2Prices.vue")),
  testimonials: defineAsyncComponent(() => import("./V2Testimonials.vue")),
  faq: defineAsyncComponent(() => import("./V2Faq.vue")),
  links: defineAsyncComponent(() => import("./V2Links.vue")),
  cta: defineAsyncComponent(() => import("./V2Cta.vue")),
  header: defineAsyncComponent(() => import("./V2Header.vue")),
  banner_card: defineAsyncComponent(() => import("./V2BannerCard.vue")),
  featured_video: defineAsyncComponent(() => import("./V2FeaturedVideo.vue")),
  video_vsl: defineAsyncComponent(() => import("./V2VideoVsl.vue")),
  biography: defineAsyncComponent(() => import("./V2Biography.vue")),
  flight_details: defineAsyncComponent(() => import("./V2FlightDetails.vue")),
  viajeon_checkout: defineAsyncComponent(() => import("./V2ViajeonCheckout.vue")),
  internal_form: defineAsyncComponent(() => import("./V2InternalForm.vue")),
  agency_footer: defineAsyncComponent(() => import("./V2AgencyFooter.vue"))
};

export const pickSectionComponent = (
  type: SectionType,
  design: PageDesign,
  legacy: Partial<Record<SectionType, Component>>
): Component | undefined => (design === "v2" && v2Components[type]) || legacy[type];
