<template>
  <V2Section type="hero" :background="textBg" :anchor-id="section.anchorId" full>
    <!-- Imersivo (padrão): foto inteira atrás do texto; no celular a foto fica quase
         quadrada no topo e o texto assenta na cor de fundo, que sobe em degradê. -->
    <div v-if="layout === 'immersive'" class="v2-hero v2-hero--imm">
      <div class="v2-hero-media" aria-hidden="true">
        <iframe v-if="video" :src="video" title="" tabindex="-1" allow="autoplay; encrypted-media"></iframe>
        <picture v-else-if="image">
          <source v-if="mobileImage" :srcset="mobileImage" media="(max-width: 640px)" />
          <img :src="image" alt="" />
        </picture>
      </div>
      <div class="v2-hero-fade" aria-hidden="true"></div>
      <div class="v2-hero-spacer" aria-hidden="true"></div>
      <div class="v2-hero-inner">
        <HeroContent v-bind="contentProps" />
      </div>
      <div v-if="logo" class="v2-hero-logo"><img :src="logo" :alt="agencyName" :style="logoStyle" /></div>
    </div>

    <div v-else-if="layout === 'classic'" class="v2-hero v2-hero--classic">
      <div class="v2-hero-media" aria-hidden="true">
        <iframe v-if="video" :src="video" title="" tabindex="-1" allow="autoplay; encrypted-media"></iframe>
        <img v-else-if="image" :src="image" alt="" />
      </div>
      <div class="v2-hero-veil" aria-hidden="true"></div>
      <div class="v2-hero-inner is-center">
        <img v-if="logo" :src="logo" :alt="agencyName" :style="logoStyle" class="v2-hero-logo-inline" />
        <HeroContent v-bind="contentProps" centered />
      </div>
    </div>

    <div v-else-if="layout === 'split'" class="v2-hero v2-hero--split">
      <div class="v2-hero-split">
        <div class="v2-hero-split-copy">
          <img v-if="logo" :src="logo" :alt="agencyName" :style="logoStyle" class="v2-hero-logo-inline" />
          <HeroContent v-bind="contentProps" on-light />
        </div>
        <div class="v2-hero-split-media">
          <img v-if="image" :src="image" :alt="title" />
        </div>
      </div>
    </div>

    <div v-else class="v2-hero v2-hero--card">
      <div class="v2-hero-media" aria-hidden="true"><img v-if="image" :src="image" alt="" /></div>
      <div class="v2-hero-card-spacer" aria-hidden="true"></div>
      <div class="v2-hero-inner">
        <div class="v2-hero-card">
          <img v-if="logo" :src="logo" :alt="agencyName" :style="logoStyle" class="v2-hero-logo-inline" />
          <HeroContent v-bind="contentProps" on-light />
        </div>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, toRef } from "vue";
import type { HeroSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import { normalizeYoutubeEmbedUrl } from "../../../utils/video";
import V2Section from "./V2Section.vue";
import { useCta } from "./useCta";
import { html, localize, text } from "./useHeading";
import { contrast, WHITE_TEXT_MIN_CONTRAST } from "./useSectionTone";

const props = defineProps<{
  section: HeroSection;
  branding?: Record<string, any>;
  previewDevice?: "desktop" | "mobile";
  hideLogo?: boolean;
}>();

const layout = computed(() => props.section.layout || "immersive");
const textBg = computed(() => (props.section.gradientColor || "").trim() || "#0B1410");
const title = computed(() => text(props.section.title));
const subtitleHtml = computed(() => (text(props.section.subtitle) ? html(props.section.subtitle) : ""));
const chips = computed(() => (props.section.chips || []).map(chip => text(chip)).filter(Boolean));
const image = computed(() => resolveMediaUrl(props.section.backgroundImage) || "");
const mobileImage = computed(() => resolveMediaUrl(props.section.mobileBackgroundImage) || "");
const video = computed(() => {
  const embed = normalizeYoutubeEmbedUrl(props.section.videoUrl);
  if (!embed) return "";
  const id = embed.split("/").pop()?.split("?")[0] || "";
  const join = embed.includes("?") ? "&" : "?";
  return `${embed}${join}autoplay=1&mute=1&loop=1&controls=0&playsinline=1&playlist=${id}`;
});
const agencyName = computed(() => String(props.branding?.agency_name || ""));
// Logo só quando a página não tem Menu do topo (o PublicPageView avisa com hideLogo).
const logo = computed(() => (props.hideLogo ? "" : resolveMediaUrl(props.section.logoUrl) || resolveMediaUrl(props.branding?.logo_url) || ""));
const logoStyle = computed(() => ({
  height: `${Math.max(32, Math.min(props.section.logoSize ?? 56, 120))}px`,
  borderRadius: `${props.section.logoBorderRadius ?? 0}px`
}));
const cta = useCta(toRef(props, "section"));
const ctaLabel = computed(() => text(props.section.ctaLabel) || localize({ pt: "Quero falar agora", es: "Quiero hablar ahora" }));
const darkText = computed(() => contrast("#FFFFFF", textBg.value) < WHITE_TEXT_MIN_CONTRAST);

const contentProps = computed(() => ({
  title: title.value,
  subtitleHtml: subtitleHtml.value,
  chips: chips.value,
  ctaEnabled: cta.enabled.value,
  ctaAttrs: cta.attrs.value,
  ctaLabel: ctaLabel.value,
  darkText: darkText.value
}));

const HeroContent = defineComponent({
  name: "V2HeroContent",
  props: {
    title: { type: String, default: "" },
    subtitleHtml: { type: String, default: "" },
    chips: { type: Array as () => string[], default: () => [] },
    ctaEnabled: Boolean,
    ctaAttrs: { type: Object, default: () => ({}) },
    ctaLabel: { type: String, default: "" },
    darkText: Boolean,
    centered: Boolean,
    onLight: Boolean
  },
  setup(p) {
    const check = () =>
      h("svg", { width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2.6, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, [h("path", { d: "m5 12 5 5 9-10" })]);
    const arrow = () =>
      h("svg", { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2.2, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, [h("path", { d: "M5 12h14M13 6l6 6-6 6" })]);
    return () =>
      h("div", { class: ["v2-hero-content", { "is-center": p.centered, "on-light": p.onLight, "dark-text": p.darkText && !p.onLight }] }, [
        p.chips.length
          ? h(
              "ul",
              { class: "v2-hero-chips v2-in", "aria-label": localize({ pt: "Destaques da viagem", es: "Destacados del viaje" }) },
              p.chips.map(chip => h("li", [h("span", { class: "v2-hero-chip-ico" }, [check()]), chip]))
            )
          : null,
        p.title ? h("h1", { class: "v2-hero-title v2-in v2-d1" }, p.title) : null,
        p.subtitleHtml ? h("div", { class: "v2-hero-sub v2-in v2-d2", innerHTML: p.subtitleHtml }) : null,
        p.ctaEnabled ? h("div", { class: "v2-in v2-d3" }, [h("a", { class: "v2-btn v2-hero-btn", ...p.ctaAttrs }, [h("span", p.ctaLabel), arrow()])]) : null
      ]);
  }
});
</script>

<style>
.v2-hero {
  position: relative;
  overflow: hidden;
  color: #fff;
}
.v2-hero-media {
  position: absolute;
  inset: 0;
}
.v2-hero-media img,
.v2-hero-media picture,
.v2-hero-media iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
  object-fit: cover;
}
.v2-hero-media iframe {
  pointer-events: none;
  transform: scale(1.35);
}
.v2-hero-inner {
  position: relative;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 clamp(20px, 5cqi, 40px) clamp(32px, 6cqi, 72px);
}
.v2-hero--imm {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: min(92vh, 860px);
}
.v2-hero--imm .v2-hero-media,
.v2-hero--imm .v2-hero-fade {
  bottom: auto;
  height: min(100%, 112cqi);
}
.v2-hero-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--v2-bg) 18%, transparent) 0%,
    transparent 22%,
    transparent 40%,
    color-mix(in srgb, var(--v2-bg) 78%, transparent) 70%,
    var(--v2-bg) 94%
  );
}
.v2-hero-spacer {
  position: relative;
  height: min(calc(112cqi - 150px), 340px);
}
.v2-hero-logo {
  position: absolute;
  top: clamp(16px, 3cqi, 28px);
  left: 0;
  right: 0;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 clamp(20px, 5cqi, 40px);
}
.v2-hero-logo img,
.v2-hero-logo-inline {
  display: block;
  width: auto;
  max-width: 220px;
  object-fit: contain;
}
.v2-hero-logo img {
  filter: drop-shadow(0 1px 10px rgba(0, 0, 0, 0.35));
}
.v2-hero-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 820px;
  color: var(--v2-ink);
}
.v2-hero--imm .v2-hero-content,
.v2-hero--classic .v2-hero-content {
  color: #fff;
}
.v2-hero--imm .v2-hero-content.dark-text {
  color: #0f1713;
}
.v2-hero-content.is-center {
  align-items: center;
  margin: 0 auto;
  text-align: center;
}
.v2-hero-content.on-light {
  color: #0f1713;
}
.v2-hero-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.is-center .v2-hero-chips {
  justify-content: center;
}
.v2-hero-chips li {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px 5px 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(10px);
  font-size: 14px;
  font-weight: 650;
  line-height: 1.2;
}
.dark-text .v2-hero-chips li,
.on-light .v2-hero-chips li {
  background: rgba(15, 23, 19, 0.06);
  border-color: transparent;
}
.v2-hero-chip-ico {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-hero-title {
  margin: 0;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 700;
  font-size: clamp(36px, 6cqi, 76px);
  line-height: 0.98;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.v2-hero-sub {
  max-width: 640px;
  font-size: clamp(17px, 1.8cqi, 20px);
  line-height: 1.5;
  opacity: 0.88;
}
.v2-hero-sub p {
  margin: 0;
}
.v2-hero-btn {
  min-height: 56px;
  padding: 0 28px;
  font-size: 17px;
}
.v2-hero--classic {
  display: grid;
  place-items: center;
  min-height: clamp(560px, 56cqi, 760px);
}
.v2-hero-veil {
  position: absolute;
  inset: 0;
  background: rgba(6, 12, 9, 0.5);
}
.v2-hero--classic .v2-hero-inner {
  padding-top: 72px;
  padding-bottom: 72px;
}
.v2-hero-inner.is-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.v2-hero--split {
  background: color-mix(in srgb, var(--v2-accent) 10%, #fbfcfa);
  color: #0f1713;
}
.v2-hero-split {
  display: flex;
  flex-wrap: wrap-reverse;
  align-items: center;
  gap: clamp(24px, 5cqi, 64px);
  max-width: 1240px;
  margin: 0 auto;
  padding: clamp(16px, 4cqi, 48px) clamp(16px, 5cqi, 40px);
}
.v2-hero-split-copy {
  flex: 1 1 420px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.v2-hero-split-media {
  flex: 1 1 420px;
  min-width: 0;
}
@container (max-width: 640px) {
  .v2-hero--imm {
    min-height: 0;
  }
}
.v2-hero-split-media img {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 5;
  max-height: 680px;
  object-fit: cover;
  border-radius: 28px;
}
.v2-hero--card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: clamp(560px, 56cqi, 740px);
}
.v2-hero-card-spacer {
  position: relative;
  height: min(340px, max(0px, calc(900px - 100cqi)));
}
.v2-hero--card .v2-hero-inner {
  padding-top: 24px;
  padding-bottom: 40px;
}
.v2-hero-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 520px;
  padding: clamp(24px, 4cqi, 40px);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 24px 60px -24px rgba(6, 12, 9, 0.5);
}
.v2-hero--card .v2-hero-title,
.v2-hero--split .v2-hero-title {
  font-size: clamp(32px, 4.6cqi, 60px);
}
</style>
