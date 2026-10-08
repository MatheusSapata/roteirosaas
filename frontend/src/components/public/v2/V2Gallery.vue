<template>
  <V2Section type="gallery" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :align="align" />
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
    <div v-else-if="isMosaic" class="v2-gal-mosaic">
      <figure v-for="(src, idx) in images" :key="idx" class="v2-gal-cell v2-in" :class="[`v2-d${Math.min(idx + 2, 7)}`, mosaicCell(idx)]">
        <img :src="src" :alt="`${copy.photo} ${idx + 1}`" loading="lazy" />
      </figure>
    </div>
    <div v-else class="v2-gal-grid v2-flow" :style="{ '--v2-cols': columns }">
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
import { balancedColumns } from "./balancedColumns";

const props = defineProps<{ section: GallerySection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, align } = useHeading(toRef(props, "section") as never, "gallery", "");
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
const columns = computed(() => balancedColumns(images.value.length));
// Mosaico em blocos de 5 fotos: uma grande (2×2) e quatro pequenas, sem buracos.
// As que sobram no fim dividem a linha: 1 ocupa a largura toda, 2 meio a meio, 3 = meia + duas.
const mosaicCell = (idx: number) => {
  const total = images.value.length;
  const blockStart = idx - (idx % 5);
  const left = total - blockStart;
  if (left >= 5) return idx % 5 === 0 ? (Math.floor(idx / 5) % 2 ? "is-big is-right" : "is-big") : "";
  const pos = idx - blockStart;
  if (left === 1) return "is-full";
  if (left === 2) return "is-half";
  if (left === 3) return pos === 0 ? "is-half is-lead" : "";
  return "";
};
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
  gap: 12px;
}
.v2-gal-cell {
  margin: 0;
  overflow: hidden;
  border-radius: 18px;
  aspect-ratio: 1;
  background: var(--v2-card);
}
/* Grade: no celular, duas fotos por linha. */
@container (max-width: 560px) {
  .v2-gal-grid > .v2-gal-cell {
    flex-basis: calc((100% - 12px) / 2);
  }
}
.v2-gal-mosaic {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: clamp(130px, 19cqi, 250px);
  grid-auto-flow: dense;
  gap: 12px;
}
.v2-gal-mosaic .v2-gal-cell {
  aspect-ratio: auto;
}
.v2-gal-mosaic .is-big {
  grid-column: span 2;
  grid-row: span 2;
}
.v2-gal-mosaic .is-big.is-right {
  grid-column: 3 / span 2;
}
.v2-gal-mosaic .is-half {
  grid-column: span 2;
}
.v2-gal-mosaic .is-full {
  grid-column: 1 / -1;
}
/* Celular: duas colunas; a foto grande ocupa a linha inteira. */
@container (max-width: 640px) {
  .v2-gal-mosaic {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: 42cqi;
  }
  .v2-gal-mosaic .is-big,
  .v2-gal-mosaic .is-big.is-right {
    grid-column: 1 / -1;
    grid-row: span 1;
  }
  .v2-gal-mosaic .is-half {
    grid-column: span 1;
  }
  .v2-gal-mosaic .is-lead {
    grid-column: 1 / -1;
  }
}
</style>
