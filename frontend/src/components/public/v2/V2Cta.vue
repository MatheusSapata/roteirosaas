<template>
  <V2Section v-if="!isCard" type="cta" :background="design.accent" :anchor-id="section.anchorId" flush>
    <div class="v2-cta-band v2-in">
      <div class="v2-cta-copy">
        <span v-if="eyebrow" class="v2-cta-eyebrow">{{ eyebrow }}</span>
        <h2 class="v2-title" :style="titleScaleStyle(title)">{{ title }}</h2>
        <div v-if="descriptionHtml" class="v2-lead" v-html="descriptionHtml"></div>
      </div>
      <a v-if="cta.enabled.value" class="v2-btn v2-cta-btn" v-bind="cta.attrs.value">
        <span>{{ buttonLabel }}</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      </a>
    </div>
  </V2Section>
  <V2Section v-else type="cta" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <div class="v2-cta-card v2-in">
      <img v-if="image" :src="image" alt="" class="v2-cta-img v2-reveal" />
      <div class="v2-cta-card-copy">
        <span v-if="eyebrow" class="v2-eyebrow"><span aria-hidden="true"></span>{{ eyebrow }}</span>
        <h2 class="v2-title" :style="titleScaleStyle(title)">{{ title }}</h2>
        <div v-if="descriptionHtml" class="v2-lead" v-html="descriptionHtml"></div>
        <div v-if="cta.enabled.value"><V2Button :attrs="cta.attrs.value">{{ buttonLabel }}</V2Button></div>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CtaSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../../utils/sectionHeadings";
import V2Section from "./V2Section.vue";
import V2Button from "./V2Button.vue";
import { useCta } from "./useCta";
import { usePageDesignContext } from "./designContext";
import { html, localize, text } from "./useHeading";
import { titleScaleStyle } from "./useCopyFit";

const props = defineProps<{ section: CtaSection; previewDevice?: "desktop" | "mobile" }>();
const design = usePageDesignContext();
const isCard = computed(() => props.section.layout === "split" || props.section.layout === "card");
const headingDefault = getSectionHeadingDefaults("cta").label;
const eyebrow = computed(() => {
  const value = resolveHeadingLabel(props.section.headingLabel, "", localize);
  return value === headingDefault ? "" : value;
});
const title = computed(() => text(props.section.label));
const descriptionHtml = computed(() => (text(props.section.description) ? html(props.section.description) : ""));
const image = computed(() => resolveMediaUrl(props.section.backgroundImage) || "");
const buttonLabel = computed(
  () => text(props.section.ctaText) || localize(props.section.layout === "simple" ? { pt: "Saiba mais", es: "Ver más" } : { pt: "Falar com especialista", es: "Hablar con un especialista" })
);
const cta = useCta(
  computed(() => ({
    ctaEnabled: props.section.ctaEnabled,
    ctaMode: props.section.ctaMode,
    ctaLink: props.section.link,
    ctaSectionId: props.section.ctaSectionId,
    ctaOpenInNewTab: props.section.ctaOpenInNewTab
  }))
);
</script>

<style scoped>
.v2-cta-band {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 20px 40px;
}
.v2-cta-copy {
  flex: 1 1 420px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.v2-cta-copy .v2-title {
  font-size: max(22px, calc(clamp(26px, 3.4cqi, 40px) * var(--v2-title-scale, 1)));
}
.v2-cta-copy .v2-lead {
  color: var(--v2-muted);
}
.v2-cta-eyebrow {
  font-size: 14px;
  font-weight: 700;
  opacity: 0.85;
}
.v2-cta-btn {
  --v2-btn-h: 56px;
  background: #0f1713;
  color: #fff;
  font-size: 17px;
}
.v2-cta-card {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  overflow: hidden;
  border-radius: 28px;
  background: var(--v2-card);
}
.v2-cta-img {
  flex: 1 1 360px;
  min-width: 0;
  min-height: 260px;
  object-fit: cover;
}
.v2-cta-card-copy {
  flex: 1 1 420px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 16px;
  padding: clamp(28px, 4cqi, 52px);
}
</style>
