<template>
  <div :class="['template-preview', { 'template-preview--mobile': props.previewDevice === 'mobile' }]">
    <div v-if="!sections.length" class="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
      Nenhuma seção disponível neste template.
    </div>
    <template v-else v-for="(section, idx) in sections" :key="idx">
      <PublicHeroSection
        v-if="section?.enabled && section.type === 'hero'"
        :section="section"
        v-bind="sectionExtraProps(section, idx)"
      />
      <component
        v-else-if="section?.enabled"
        :is="publicComponents[section.type]"
        :section="section"
        v-bind="sectionExtraProps(section, idx)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, provide } from "vue";
import PublicHeroSection from "../public/PublicHeroSection.vue";
import PublicBannerCardSection from "../public/PublicBannerCardSection.vue";
import PublicPricesSection from "../public/PublicPricesSection.vue";
import PublicProductsSection from "../public/PublicProductsSection.vue";
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
import PublicPhotoSection from "../public/PublicPhotoSection.vue";
import PublicBiographySection from "../public/PublicBiographySection.vue";
import type { PageConfig, PageSection, SectionType } from "../../types/page";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";

const publicComponents: Record<string, unknown> = {
  hero: PublicHeroSection,
  banner_card: PublicBannerCardSection,
  prices: PublicPricesSection,
  products: PublicProductsSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  featured_video: PublicFeaturedVideoSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  free_footer_brand: PublicFreeFooterBrandSection,
  agency_footer: PublicAgencyFooterSection,
  photo: PublicPhotoSection,
  biography: PublicBiographySection
};

const sectionRequiresBranding = (type?: SectionType) => type === "hero" || type === "agency_footer";

interface Props {
  config?: PageConfig | null;
  branding?: Record<string, unknown>;
  previewDevice?: "desktop" | "mobile";
}

const props = withDefaults(defineProps<Props>(), {
  config: null,
  branding: () => ({}),
  previewDevice: "desktop"
});

provide(PUBLIC_BRANDING_KEY, computed(() => props.branding || {}));

const sections = computed<PageSection[]>(() => props.config?.sections || []);
const branding = computed(() => props.branding || {});
const previewAwareSections: SectionType[] = ["hero", "banner_card", "story", "featured_video", "reasons", "agency_footer", "biography"];
const sectionSupportsPreviewDevice = (type?: SectionType) => !!type && previewAwareSections.includes(type);
const findPrevEnabledSection = (index: number) => {
  for (let i = index - 1; i >= 0; i -= 1) {
    const candidate = sections.value[i];
    if (candidate?.enabled) return candidate;
  }
  return null;
};
const findNextEnabledSection = (index: number) => {
  for (let i = index + 1; i < sections.value.length; i += 1) {
    const candidate = sections.value[i];
    if (candidate?.enabled) return candidate;
  }
  return null;
};
const sectionExtraProps = (section?: PageSection, index?: number) => {
  const extra: Record<string, unknown> = {};
  const type = section?.type;
  if (sectionRequiresBranding(type)) {
    extra.branding = branding.value;
  }
  if (sectionSupportsPreviewDevice(type)) {
    extra.previewDevice = props.previewDevice;
  }
  if (type === "banner_card" && typeof index === "number") {
    const prev = findPrevEnabledSection(index);
    const next = findNextEnabledSection(index);
    extra.prevIsBannerCard = prev?.type === "banner_card";
    extra.nextIsBannerCard = next?.type === "banner_card";
  }
  return extra;
};
</script>

<style scoped>
.template-preview {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-bottom: 0;
}

.template-preview--mobile {
  gap: 0;
  padding-bottom: 0;
}
</style>
