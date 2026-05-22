<template>
  <div class="hover-visual-preview">
    <div class="hover-visual-preview__title">{{ label }}</div>
    <div class="hover-visual-preview__frame">
      <div class="hover-visual-preview__scaled">
        <PublicHeroSection
          v-if="section.type === 'hero'"
          :section="section as any"
          :branding="{}"
          previewDevice="desktop"
        />
        <component
          v-else
          :is="resolvedComponent"
          :section="section as any"
          previewDevice="desktop"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PageSection } from "../../types/page";
import PublicHeroSection from "../public/PublicHeroSection.vue";
import PublicBannerCardSection from "../public/PublicBannerCardSection.vue";
import PublicPricesSection from "../public/PublicPricesSection.vue";
import PublicItinerarySection from "../public/PublicItinerarySection.vue";
import PublicFaqSection from "../public/PublicFaqSection.vue";
import PublicTestimonialsSection from "../public/PublicTestimonialsSection.vue";
import PublicFeaturedVideoSection from "../public/PublicFeaturedVideoSection.vue";
import PublicCtaSection from "../public/PublicCtaSection.vue";
import PublicStorySection from "../public/PublicStorySection.vue";
import PublicReasonsSection from "../public/PublicReasonsSection.vue";
import PublicCountdownSection from "../public/PublicCountdownSection.vue";
import PublicFreeFooterBrandSection from "../public/PublicFreeFooterBrandSection.vue";
import PublicAgencyFooterSection from "../public/PublicAgencyFooterSection.vue";
import PublicFlightDetailsSection from "../public/PublicFlightDetailsSection.vue";
import PublicPhotoSection from "../public/PublicPhotoSection.vue";
import PublicBiographySection from "../public/PublicBiographySection.vue";

const props = defineProps<{
  label: string;
  section: PageSection;
}>();

const componentMap: Record<string, unknown> = {
  hero: PublicHeroSection,
  banner_card: PublicBannerCardSection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  featured_video: PublicFeaturedVideoSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  flight_details: PublicFlightDetailsSection,
  free_footer_brand: PublicFreeFooterBrandSection,
  agency_footer: PublicAgencyFooterSection,
  photo: PublicPhotoSection,
  biography: PublicBiographySection
};

const resolvedComponent = computed(() => componentMap[props.section.type] || PublicBannerCardSection);
</script>

<style scoped>
.hover-visual-preview__title {
  font-size: 13px;
  font-weight: 700;
  color: #102018;
  margin-bottom: 8px;
}

.hover-visual-preview__frame {
  position: relative;
  width: 100%;
  height: 180px;
  border: 1px solid #d8e4dc;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.hover-visual-preview__scaled {
  width: 960px;
  transform: scale(0.26);
  transform-origin: top left;
}
</style>
