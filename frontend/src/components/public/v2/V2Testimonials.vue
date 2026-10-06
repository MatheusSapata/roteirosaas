<template>
  <V2Section type="testimonials" :background="section.backgroundColor" fallback-background="#F2F4F1" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" />
    <div v-if="isHighlight && items.length" class="v2-tm-hl">
      <figure class="v2-tm-main v2-in">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path :d="quotePath" /><path :d="quotePath2" /></svg>
        <blockquote>{{ items[0].text }}</blockquote>
        <figcaption><b>{{ items[0].name }}</b><span v-if="items[0].role">{{ items[0].role }}</span></figcaption>
      </figure>
      <div v-if="items.length > 1" class="v2-tm-side">
        <figure v-for="(item, idx) in items.slice(1)" :key="idx" class="v2-card v2-tm-small v2-in" :class="`v2-d${Math.min(idx + 2, 7)}`">
          <blockquote>“{{ item.text }}”</blockquote>
          <figcaption><b>{{ item.name }}</b><span v-if="item.role"> · {{ item.role }}</span></figcaption>
        </figure>
      </div>
    </div>
    <div v-else class="v2-tm-grid">
      <figure v-for="(item, idx) in items" :key="idx" class="v2-card v2-tm-card v2-in" :class="`v2-d${Math.min(idx + 3, 7)}`">
        <div class="v2-tm-top">
          <span class="v2-tm-stars" aria-label="5 de 5 estrelas">★★★★★</span>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path :d="quotePath" /><path :d="quotePath2" /></svg>
        </div>
        <blockquote>“{{ item.text }}”</blockquote>
        <figcaption>
          <img v-if="item.avatar" :src="item.avatar" alt="" class="v2-tm-avatar" />
          <span v-else class="v2-tm-avatar v2-tm-initials" aria-hidden="true">{{ item.initials }}</span>
          <span class="v2-tm-who"><b>{{ item.name }}</b><span v-if="item.role">{{ item.role }}</span></span>
        </figcaption>
      </figure>
    </div>
    <div v-if="cta.enabled.value" class="v2-actions">
      <V2Button :attrs="cta.attrs.value">{{ ctaLabel }}</V2Button>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import type { TestimonialsSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import V2Button from "./V2Button.vue";
import { useCta } from "./useCta";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: TestimonialsSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml } = useHeading(toRef(props, "section"), "testimonials", { pt: "Depoimentos", es: "Testimonios" });
const isHighlight = computed(() => props.section.layout === "highlight");
const quotePath = "M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z";
const quotePath2 = "M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z";
const items = computed(() =>
  (props.section.items || []).map(item => {
    const name = text(item.name);
    return {
      name,
      text: text(item.text),
      role: text(item.role),
      avatar: resolveMediaUrl(item.avatar) || item.avatar || "",
      initials: name.split(/\s+/).filter(Boolean).slice(0, 2).map(p => p[0]?.toUpperCase()).join("")
    };
  })
);
const cta = useCta(toRef(props, "section"));
const ctaLabel = computed(() => text(props.section.ctaLabel) || localize({ pt: "Falar com especialista", es: "Hablar con un especialista" }));
</script>

<style scoped>
.v2-tm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
  gap: 16px;
}
.v2-tm-card {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 26px;
  border-radius: 24px;
}
.v2-tm-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--v2-accent-text);
}
.v2-tm-stars {
  color: #e0a526;
  font-size: 18px;
  letter-spacing: 2px;
}
blockquote {
  margin: 0;
  white-space: pre-line;
  font-size: 17px;
  line-height: 1.6;
}
figcaption {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: auto;
}
.v2-tm-avatar {
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  border-radius: 999px;
  object-fit: cover;
}
.v2-tm-initials {
  display: grid;
  place-items: center;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  font-weight: 700;
}
.v2-tm-who {
  display: flex;
  flex-direction: column;
}
.v2-tm-who span {
  font-size: 14px;
  color: var(--v2-muted);
}
.v2-tm-hl {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.v2-tm-main {
  flex: 3 1 440px;
  min-width: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: clamp(28px, 4cqi, 44px);
  border-radius: 28px;
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-tm-main svg {
  opacity: 0.9;
}
.v2-tm-main blockquote {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-weight: 600;
  font-size: clamp(22px, 2.6cqi, 30px);
  line-height: 1.3;
}
.v2-tm-main figcaption {
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}
.v2-tm-side {
  flex: 2 1 300px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.v2-tm-small {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 22px;
  border-radius: 24px;
}
.v2-tm-small blockquote {
  font-size: 16px;
}
.v2-tm-small figcaption {
  font-size: 14px;
  display: block;
}
</style>
