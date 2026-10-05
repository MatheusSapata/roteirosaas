<template>
  <V2Section type="gallery" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" />
    <div v-if="isCarousel" class="v2-gal-car v2-in v2-d2">
      <div class="v2-gal-track" :style="{ transform: `translateX(calc(-1 * ${index} * (var(--slide) + 12px)))` }">
        <figure v-for="(src, idx) in images" :key="idx" class="v2-gal-slide">
          <img :src="src" :alt="`${copy.photo} ${idx + 1}`" loading="lazy" />
        </figure>
      </div>
      <div v-if="images.length > 1" class="v2-gal-ctrl">
        <div class="v2-gal-dots" role="tablist">
          <button
            v-for="(_, idx) in images"
            :key="`d${idx}`"
            type="button"
            role="tab"
            :aria-selected="idx === index"
            :aria-label="`${copy.goTo} ${idx + 1}`"
            :class="{ 'is-on': idx === index }"
            @click="index = idx"
          ></button>
        </div>
        <span class="v2-gal-count">{{ index + 1 }} / {{ images.length }}</span>
        <button type="button" class="v2-gal-arrow" :aria-label="copy.prev" @click="go(-1)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
        </button>
        <button type="button" class="v2-gal-arrow is-next" :aria-label="copy.next" @click="go(1)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
        </button>
      </div>
    </div>
    <div v-else class="v2-gal-grid" :class="{ 'is-mosaic': isMosaic }">
      <figure v-for="(src, idx) in images" :key="idx" class="v2-gal-cell v2-in" :class="`v2-d${Math.min(idx + 2, 7)}`">
        <img :src="src" :alt="`${copy.photo} ${idx + 1}`" loading="lazy" />
      </figure>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watch } from "vue";
import type { GallerySection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { localize, useHeading } from "./useHeading";

const props = defineProps<{ section: GallerySection; previewDevice?: "desktop" | "mobile" }>();
const { label, title } = useHeading(toRef(props, "section") as never, "gallery", "");
const copy = {
  photo: localize({ pt: "Foto", es: "Foto" }),
  goTo: localize({ pt: "Ir para a foto", es: "Ir a la foto" }),
  prev: localize({ pt: "Fotos anteriores", es: "Fotos anteriores" }),
  next: localize({ pt: "Próximas fotos", es: "Siguientes fotos" })
};
// "strip" (faixa) vira o carrossel; mosaico e grade continuam.
const isCarousel = computed(() => !props.section.layout || props.section.layout === "strip");
const isMosaic = computed(() => props.section.layout === "mosaic");
const images = computed(() => (props.section.images || []).map(img => resolveMediaUrl(img) || img).filter(Boolean));
const index = ref(0);
const go = (step: number) => {
  const total = images.value.length;
  if (total) index.value = (index.value + step + total) % total;
};
watch(() => images.value.length, total => {
  if (index.value >= total) index.value = Math.max(0, total - 1);
});
</script>

<style scoped>
.v2-gal-car {
  --slide: min(100%, max(280px, calc((100% - 24px) / 3)));
  overflow: hidden;
}
.v2-gal-track {
  display: flex;
  gap: 12px;
  transition: transform 0.5s cubic-bezier(0.22, 0.8, 0.24, 1);
}
.v2-gal-slide {
  flex: 0 0 var(--slide);
  margin: 0;
  overflow: hidden;
  border-radius: 20px;
  aspect-ratio: 4 / 5;
  background: var(--v2-card);
}
.v2-gal-slide img,
.v2-gal-cell img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.v2-gal-ctrl {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
}
.v2-gal-dots {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.v2-gal-dots button {
  width: 8px;
  height: 8px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: var(--v2-line);
  cursor: pointer;
  transition: width 0.2s ease, background-color 0.2s ease;
}
.v2-gal-dots button.is-on {
  width: 24px;
  background: var(--v2-accent);
}
.v2-gal-count {
  font-size: 14px;
  font-weight: 700;
  color: var(--v2-muted);
  font-variant-numeric: tabular-nums;
}
.v2-gal-arrow {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 0;
  border-radius: 999px;
  background: var(--v2-card);
  color: var(--v2-ink);
  cursor: pointer;
}
.v2-gal-arrow.is-next {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
.v2-gal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 12px;
}
.v2-gal-cell {
  margin: 0;
  overflow: hidden;
  border-radius: 18px;
  aspect-ratio: 1;
  background: var(--v2-card);
}
.v2-gal-grid.is-mosaic {
  grid-auto-flow: dense;
}
.is-mosaic .v2-gal-cell:nth-child(5n + 1) {
  grid-row: span 2;
  aspect-ratio: auto;
}
</style>
