import type { Component } from "vue";
import { lazySection } from "../lazySection";
import type { SectionType } from "../../../types/page";
import type { PageDesign } from "../../../utils/pageDesign";
// Menu do topo e Banner Inicial abrem a página: vêm junto com ela, sem esperar outro download.
import V2Header from "./V2Header.vue";
import V2Hero from "./V2Hero.vue";

/**
 * Seções que já têm visual novo. As que ainda não estão aqui continuam com o
 * componente antigo mesmo em páginas no visual novo.
 */
export const v2Components: Partial<Record<SectionType, Component>> = {
  hero: V2Hero,
  countdown: lazySection(() => import("./V2Countdown.vue")),
  story: lazySection(() => import("./V2Story.vue")),
  reasons: lazySection(() => import("./V2Reasons.vue")),
  inclusions: lazySection(() => import("./V2Inclusions.vue")),
  itinerary: lazySection(() => import("./V2Itinerary.vue")),
  gallery: lazySection(() => import("./V2Gallery.vue")),
  photo: lazySection(() => import("./V2Photo.vue")),
  prices: lazySection(() => import("./V2Prices.vue")),
  testimonials: lazySection(() => import("./V2Testimonials.vue")),
  faq: lazySection(() => import("./V2Faq.vue")),
  links: lazySection(() => import("./V2Links.vue")),
  cta: lazySection(() => import("./V2Cta.vue")),
  header: V2Header,
  banner_card: lazySection(() => import("./V2BannerCard.vue")),
  featured_video: lazySection(() => import("./V2FeaturedVideo.vue")),
  video_vsl: lazySection(() => import("./V2VideoVsl.vue")),
  biography: lazySection(() => import("./V2Biography.vue")),
  flight_details: lazySection(() => import("./V2FlightDetails.vue")),
  viajeon_checkout: lazySection(() => import("./V2ViajeonCheckout.vue")),
  internal_form: lazySection(() => import("./V2InternalForm.vue")),
  redirect: lazySection(() => import("./V2Redirect.vue")),
  agency_footer: lazySection(() => import("./V2AgencyFooter.vue"))
};

export const pickSectionComponent = (
  type: SectionType,
  design: PageDesign,
  legacy: Partial<Record<SectionType, Component>>
): Component | undefined => (design === "v2" && v2Components[type]) || legacy[type];
