<template>
  <V2Section type="biography" :background="section.backgroundColor" :anchor-id="section.anchorId" full>
    <header v-if="image || title" class="v2-art-cover">
      <picture v-if="image">
        <source v-if="mobileImage" :srcset="mobileImage" media="(max-width: 640px)" />
        <img :src="image" :alt="title || copy.alt" class="v2-reveal" loading="lazy" />
      </picture>
      <div class="v2-art-veil" :style="{ '--veil': veil }" aria-hidden="true"></div>
      <h2 v-if="title" class="v2-art-title v2-in">{{ title }}</h2>
    </header>
    <div v-if="bodyHtml" class="v2-art-body">
      <div class="v2-art-text v2-in v2-d2" v-html="bodyHtml"></div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { BiographySection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import { sanitizeHtml } from "../../../utils/sanitizeHtml";
import { localize, text } from "./useHeading";

const props = defineProps<{ section: BiographySection; previewDevice?: "desktop" | "mobile" }>();
const copy = { alt: localize({ pt: "Biografia", es: "Biografía" }) };
const image = computed(() => resolveMediaUrl(props.section.image) || resolveMediaUrl(props.section.mobileImage) || "");
const mobileImage = computed(() => resolveMediaUrl(props.section.mobileImage) || "");
const title = computed(() => text(props.section.title));
// O artigo aceita imagens e vídeos (YouTube/Vimeo) no meio do texto.
const bodyHtml = computed(() => {
  const raw = text(props.section.text);
  if (!raw) return "";
  const safe = sanitizeHtml(raw, { embeds: true });
  if (typeof document === "undefined") return safe;
  const box = document.createElement("div");
  box.innerHTML = safe;
  box.querySelectorAll("img").forEach(img => {
    img.setAttribute("src", resolveMediaUrl(img.getAttribute("src")) || "");
    img.setAttribute("loading", "lazy");
  });
  box.querySelectorAll("iframe").forEach(frame => {
    frame.setAttribute("loading", "lazy");
    frame.setAttribute("allow", "accelerometer; encrypted-media; gyroscope; picture-in-picture");
    frame.setAttribute("allowfullscreen", "true");
  });
  return box.innerHTML;
});
// Mesmo campo de hoje (overlayOpacity, padrão 0,45), limitado para o título continuar legível.
const veil = computed(() => {
  const value = typeof props.section.overlayOpacity === "number" ? props.section.overlayOpacity : 0.45;
  return String(Math.min(Math.max(value, 0.2), 0.85));
});
</script>

<style scoped>
.v2-art-cover {
  position: relative;
  display: grid;
  place-items: center;
  min-height: clamp(320px, 42cqi, 560px);
  overflow: hidden;
  color: #fff;
  text-align: center;
}
.v2-art-cover picture,
.v2-art-cover img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.v2-art-veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(6, 12, 9, calc(var(--veil) - 0.3)) 0%, rgba(6, 12, 9, var(--veil)) 100%);
}
.v2-art-cover:not(:has(img)) {
  background: #0b1410;
}
.v2-art-title {
  position: relative;
  max-width: 900px;
  margin: 0;
  padding: 56px clamp(20px, 5cqi, 40px);
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 700;
  font-size: clamp(32px, 5.4cqi, 68px);
  line-height: 1.02;
  letter-spacing: -0.03em;
  text-wrap: balance;
}
.v2-art-body {
  padding: clamp(40px, 6cqi, 72px) clamp(20px, 5cqi, 40px) clamp(56px, 8cqi, 96px);
}
.v2-art-text {
  max-width: 720px;
  margin: 0 auto;
  font-size: clamp(17px, 1.6cqi, 19px);
  line-height: 1.75;
}
.v2-art-text :deep(p) {
  margin: 0 0 1em;
}
.v2-art-text :deep(h2),
.v2-art-text :deep(h3),
.v2-art-text :deep(h4) {
  margin: 1.4em 0 0.5em;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: clamp(22px, 2.6cqi, 30px);
  line-height: 1.15;
  letter-spacing: -0.02em;
}
.v2-art-text :deep(ul),
.v2-art-text :deep(ol) {
  margin: 0 0 1em;
  padding-left: 1.3em;
}
.v2-art-text :deep(li::marker) {
  color: var(--v2-accent-text);
}
.v2-art-text :deep(img) {
  display: block;
  width: 100%;
  height: auto;
  margin: 1.6em 0;
  border-radius: 18px;
}
.v2-art-text :deep(iframe) {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
  margin: 1.6em 0;
  border: 0;
  border-radius: 18px;
  background: #0f1713;
}
.v2-art-text :deep(h3) {
  font-size: clamp(19px, 2cqi, 23px);
}
.v2-art-text :deep(s) {
  opacity: 0.7;
}
.v2-art-text :deep(a) {
  color: var(--v2-accent-text);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.v2-art-text :deep(blockquote) {
  margin: 1.4em 0;
  padding: 0;
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 600;
  font-size: clamp(20px, 2.4cqi, 26px);
  line-height: 1.35;
}
.v2-art-text :deep(blockquote)::before {
  content: "“";
  display: block;
  color: var(--v2-accent-text);
  font-size: 2em;
  line-height: 0.6;
}
.v2-art-text :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 1.4em 0;
  border-radius: 18px;
}
</style>
