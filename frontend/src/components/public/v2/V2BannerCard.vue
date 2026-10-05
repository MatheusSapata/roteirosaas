<template>
  <V2Section type="banner_card" :background="section.backgroundColor" :anchor-id="section.anchorId" :class="{ 'v2-bc-tight-top': prevIsBannerCard, 'v2-bc-tight-bottom': nextIsBannerCard }">
    <div class="v2-bc v2-in">
      <img v-if="image" :src="image" alt="" class="v2-bc-img v2-reveal" loading="lazy" />
      <div class="v2-bc-card">
        <span v-if="label" class="v2-eyebrow"><span aria-hidden="true"></span>{{ label }}</span>
        <h2 v-if="title" class="v2-bc-title">{{ title }}</h2>
        <div v-if="subtitleHtml" class="v2-bc-sub" v-html="subtitleHtml"></div>
        <div v-if="cta.enabled.value"><V2Button :attrs="cta.attrs.value">{{ ctaLabel }}</V2Button></div>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { BannerCardSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Button from "./V2Button.vue";
import { useCta } from "./useCta";
import { html, localize, text } from "./useHeading";

const props = defineProps<{
  section: BannerCardSection;
  previewDevice?: "desktop" | "mobile";
  prevIsBannerCard?: boolean;
  nextIsBannerCard?: boolean;
}>();
const image = computed(() => resolveMediaUrl(props.section.backgroundImage || "") || props.section.backgroundImage || "");
const label = computed(() => text(props.section.headingLabel));
const title = computed(() => text(props.section.title));
const subtitleHtml = computed(() => (text(props.section.subtitle) ? html(props.section.subtitle) : ""));
const cta = useCta(toRef(props, "section"));
const ctaLabel = computed(() => text(props.section.ctaLabel) || localize({ pt: "Falar agora", es: "Hablar ahora" }));
</script>

<style scoped>
.v2-bc {
  position: relative;
  display: flex;
  align-items: center;
  min-height: clamp(380px, 42cqi, 520px);
  overflow: hidden;
  border-radius: 28px;
  background: #0b1410;
}
.v2-bc-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.v2-bc-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  max-width: 520px;
  margin: clamp(16px, 4cqi, 48px);
  padding: clamp(24px, 4cqi, 40px);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.94);
  color: #0f1713;
  box-shadow: 0 24px 60px -24px rgba(6, 12, 9, 0.5);
}
.v2-bc-title {
  margin: 0;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 700;
  font-size: clamp(26px, 3.4cqi, 40px);
  line-height: 1.05;
  letter-spacing: -0.025em;
}
.v2-bc-sub {
  color: rgba(15, 23, 19, 0.74);
  line-height: 1.55;
}
.v2-bc-sub :deep(p) {
  margin: 0;
}
.v2-bc-card .v2-eyebrow {
  background: var(--v2-accent);
}
@container (max-width: 640px) {
  .v2-bc {
    flex-direction: column;
    align-items: stretch;
    justify-content: flex-end;
    min-height: 0;
    padding-top: 200px;
  }
  .v2-bc-img {
    height: 260px;
  }
  .v2-bc-card {
    margin: 0 12px 12px;
  }
}
.v2-bc-tight-top :deep(.v2-wrap) {
  padding-top: 8px;
}
.v2-bc-tight-bottom :deep(.v2-wrap) {
  padding-bottom: 8px;
}
</style>
