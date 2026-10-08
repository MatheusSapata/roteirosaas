<template>
  <V2Section type="links" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" :align="headAlign" />
    <div class="v2-links" :class="isCarousel ? 'is-carousel' : 'is-grid'" :style="layoutVars">
      <div ref="track" class="v2-links-track">
        <a
          v-for="(item, idx) in items"
          :key="item.key"
          :href="item.url"
          :target="item.newTab ? '_blank' : '_self'"
          rel="noopener noreferrer"
          class="v2-card v2-link-card v2-links-card v2-in"
          :class="`v2-d${Math.min(idx + 3, 7)}`"
        >
          <span class="v2-links-media"><img v-if="item.image" :src="item.image" alt="" loading="lazy" /></span>
          <span class="v2-links-body">
            <b class="v2-links-title">{{ item.title }}</b>
            <span v-if="item.description" class="v2-links-desc">{{ item.description }}</span>
            <span v-if="item.dates" class="v2-links-meta">
              <span class="v2-links-ico" aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="3" /><path d="M16 2v4M8 2v4M3 10h18" /></svg></span>
              <span v-if="item.departure" class="v2-links-dt"><small>{{ copy.departure }}</small><b>{{ item.departure }}</b></span>
              <span v-if="item.return" class="v2-links-dt"><small>{{ copy.return }}</small><b>{{ item.return }}</b></span>
            </span>
            <span v-if="item.price" class="v2-links-price">
              <span class="v2-links-ico" aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z" /><circle cx="7.5" cy="7.5" r=".5" fill="currentColor" /></svg></span>
              <small v-if="item.pricePrefix">{{ item.pricePrefix }}</small>
              <b>{{ item.price }}</b>
              <small v-if="item.priceSuffix">{{ item.priceSuffix }}</small>
            </span>
            <span class="v2-btn v2-btn--block v2-links-btn">
              <span>{{ item.buttonLabel }}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
            </span>
          </span>
        </a>
      </div>
      <div v-if="overflowing" class="v2-links-ctrl">
        <button type="button" class="v2-links-arrow" :aria-label="copy.prev" @click="slide(-1)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
        </button>
        <button type="button" class="v2-links-arrow is-next" :aria-label="copy.next" @click="slide(1)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
        </button>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, toRef, watch } from "vue";
import type { LinksSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Head from "./V2Head.vue";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: LinksSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml, align: headAlign } = useHeading(toRef(props, "section"), "links", "");
const copy = {
  departure: localize({ pt: "Ida", es: "Ida" }),
  return: localize({ pt: "Volta", es: "Vuelta" }),
  open: localize({ pt: "Ver roteiro", es: "Ver itinerario" }),
  prev: localize({ pt: "Roteiros anteriores", es: "Itinerarios anteriores" }),
  next: localize({ pt: "Próximos roteiros", es: "Próximos itinerarios" })
};
const formatDate = (value?: string) => {
  if (!value) return "";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) return `${match[3]}/${match[2]}/${match[1]}`;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString("pt-BR");
};
const items = computed(() =>
  (props.section.items || [])
    .filter(item => item?.url)
    .map((item, idx) => {
      const showDates = item.showDates === true && !!(item.departureDate || item.returnDate);
      const prefix = text(item.pricePrefix);
      const suffix = text(item.priceSuffix);
      const showPrice = item.showPrice === true && !!(prefix || item.priceValue || suffix);
      return {
        key: item.id || `${item.url}-${idx}`,
        url: item.url,
        newTab: item.openInNewTab !== false,
        image: resolveMediaUrl(item.image) || "",
        title: text(item.title),
        description: text(item.description),
        dates: showDates,
        departure: showDates ? formatDate(item.departureDate) : "",
        return: showDates ? formatDate(item.returnDate) : "",
        price: showPrice ? item.priceValue || "" : "",
        pricePrefix: showPrice ? prefix : "",
        priceSuffix: showPrice ? suffix : "",
        buttonLabel: text(item.buttonLabel) || copy.open
      };
    })
);
// Como na seção antiga: até 4 cards lado a lado; a partir do 5º, o carrossel
// desliza com setas. Com o carrossel desligado, os cards quebram em linhas
// centralizadas (3 ou 4 por linha). Com 1 ou 2 cards, eles não esticam.
const isCarousel = computed(() => props.section.carouselEnabled !== false);
const layoutVars = computed(() => {
  const count = items.value.length;
  let columns = count <= 3 ? 3 : 4;
  if (!isCarousel.value && (count === 5 || count === 6)) columns = 3;
  return { "--v2-links-cols": String(columns) };
});

// As setas aparecem só quando os cards não cabem (computador com 5+, tablet com 3+, celular com 2+).
const track = ref<HTMLElement | null>(null);
const overflowing = ref(false);
const measure = () => {
  const el = track.value;
  overflowing.value = isCarousel.value && !!el && el.scrollWidth > el.clientWidth + 4;
};
let resizeObserver: ResizeObserver | null = null;
onMounted(() => {
  measure();
  if (typeof ResizeObserver !== "undefined" && track.value) {
    resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(track.value);
  }
});
onBeforeUnmount(() => resizeObserver?.disconnect());
watch([items, isCarousel], () => nextTick(measure));

// Avança um card por clique; no fim volta ao começo (e vice-versa), como na seção antiga.
const slide = (direction: number) => {
  const el = track.value;
  if (!el) return;
  const card = el.querySelector<HTMLElement>(".v2-links-card");
  const step = (card?.offsetWidth || el.clientWidth * 0.8) + 16;
  const max = el.scrollWidth - el.clientWidth;
  if (direction < 0 && el.scrollLeft <= 4) return el.scrollTo({ left: max, behavior: "smooth" });
  if (direction > 0 && el.scrollLeft >= max - 4) return el.scrollTo({ left: 0, behavior: "smooth" });
  el.scrollBy({ left: direction * step, behavior: "smooth" });
};
</script>

<style scoped>
.v2-links {
  position: relative;
  --v2-links-gap: 16px;
}
.v2-links-track {
  display: flex;
  gap: var(--v2-links-gap);
}
.v2-links-card {
  flex: 0 0 calc((100% - (var(--v2-links-cols) - 1) * var(--v2-links-gap)) / var(--v2-links-cols));
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 24px;
  color: inherit;
  text-decoration: none;
}
/* Carrossel: rola de lado sem barra; com poucos cards, o grupo fica centralizado
   (margens automáticas não atrapalham quando a lista transborda). */
.is-carousel .v2-links-track {
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding: 4px 2px 8px;
  margin: -4px -2px -8px;
}
.is-carousel .v2-links-track::-webkit-scrollbar {
  display: none;
}
.is-carousel .v2-links-card {
  scroll-snap-align: start;
}
.is-carousel .v2-links-card:first-child {
  margin-left: auto;
}
.is-carousel .v2-links-card:last-child {
  margin-right: auto;
}
.is-grid .v2-links-track {
  flex-wrap: wrap;
  justify-content: center;
}
/* Setas no mesmo padrão do carrossel da galeria: embaixo, à direita. */
.v2-links-ctrl {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
}
.v2-links-arrow {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: var(--v2-card);
  color: var(--v2-ink);
  cursor: pointer;
  transition: transform 0.2s ease;
}
.v2-links-arrow:hover {
  transform: scale(1.06);
}
.v2-links-arrow:focus-visible {
  outline: 2px solid var(--v2-accent);
  outline-offset: 2px;
}
.v2-links-arrow.is-next {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
}
/* Tablet: 2 por vez. */
@container (max-width: 1023px) {
  .v2-links-card {
    flex-basis: calc((100% - var(--v2-links-gap)) / 2);
  }
}
/* Celular: no carrossel, um card e a ponta do próximo (desliza com o dedo);
   na grade, um embaixo do outro. */
@container (max-width: 640px) {
  .is-carousel .v2-links-card {
    flex-basis: 84%;
  }
  .is-carousel .v2-links-card:only-child {
    flex-basis: 100%;
  }
  .is-grid .v2-links-card {
    flex-basis: 100%;
  }
}
.v2-links-media {
  display: block;
  overflow: hidden;
  aspect-ratio: 16 / 11;
  background: var(--v2-soft);
}
.v2-links-media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.v2-links-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px 22px 22px;
}
.v2-links-title {
  font-size: 19px;
  line-height: 1.25;
}
.v2-links-desc {
  color: var(--v2-muted);
  line-height: 1.5;
}
.v2-links-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--v2-soft);
}
.v2-links-dt {
  display: flex;
  flex-direction: column;
}
.v2-links-dt small {
  font-size: 12px;
  color: var(--v2-muted);
}
.v2-links-ico {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--v2-accent-soft);
  color: var(--v2-accent-text);
}
.v2-links-price {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.v2-links-price small {
  font-size: 14px;
  color: var(--v2-muted);
}
.v2-links-price b {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 22px;
}
.v2-links-btn {
  margin-top: auto;
  min-height: 48px;
}
.v2-links-meta + .v2-links-btn,
.v2-links-price + .v2-links-btn {
  margin-top: 4px;
}
</style>
