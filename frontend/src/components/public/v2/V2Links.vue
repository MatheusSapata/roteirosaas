<template>
  <!-- Como na seção antiga: sem cards, a seção não aparece na página; na prévia do editor, um aviso. -->
  <V2Section v-if="items.length || previewDevice" type="links" :background="section.backgroundColor" :anchor-id="section.anchorId">
    <V2Head :label="label" :title="title" :subtitle-html="subtitleHtml" :align="headAlign" />
    <p v-if="!items.length" class="v2-links-empty">Adicione cards em Links/Roteiros. Sem cards, a seção não aparece na página.</p>
    <div v-else class="v2-links" :class="isCarousel ? 'is-carousel' : 'is-grid'" :style="layoutVars">
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
          <span class="v2-links-media"><V2Img v-if="item.image" :src="item.image" alt="" sizes="(max-width: 640px) 100vw, 420px" /></span>
          <span class="v2-links-body">
            <!-- Título e texto ocupam a mesma altura em todos os cards (a do maior). -->
            <span class="v2-links-text">
              <span class="v2-links-text-in">
                <b class="v2-links-title">{{ item.title }}</b>
                <span v-if="item.description" class="v2-links-desc">{{ item.description }}</span>
              </span>
            </span>
            <span class="v2-links-foot">
              <!-- Ícones da seção antiga: calendário em cada data e etiqueta no preço. -->
              <span v-if="item.dates" class="v2-links-meta">
                <span v-if="item.departure" class="v2-links-dt"><small><svg class="v2-links-ico" width="15" height="15" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg>{{ copy.departure }}</small><b>{{ item.departure }}</b></span>
                <span v-if="item.return" class="v2-links-dt"><small><svg class="v2-links-ico" width="15" height="15" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg>{{ copy.return }}</small><b>{{ item.return }}</b></span>
              </span>
              <span v-if="item.price" class="v2-links-price">
                <svg class="v2-links-ico v2-links-ico--tag" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.6 13.6 12 22l-9-9V4h9l8.6 8.6a.7.7 0 0 1 0 1Z" /><circle cx="8" cy="9" r="1.5" /></svg>
                <span class="v2-links-price-copy">
                  <small v-if="item.pricePrefix" class="v2-links-price-pre">{{ item.pricePrefix }}</small>
                  <span class="v2-links-price-line">
                    <b>{{ item.price }}</b>
                    <small v-if="item.priceSuffix">{{ item.priceSuffix }}</small>
                  </span>
                </span>
              </span>
              <span class="v2-btn v2-btn--block v2-links-btn">
                <span>{{ item.buttonLabel }}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
              </span>
            </span>
          </span>
        </a>
      </div>
      <button v-if="overflowing" type="button" class="v2-links-arrow is-prev" :aria-label="copy.prev" @click="slide(-1)">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
      </button>
      <button v-if="overflowing" type="button" class="v2-links-arrow is-next" :aria-label="copy.next" @click="slide(1)">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
      </button>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, toRef, watch } from "vue";
import type { LinksSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import V2Section from "./V2Section.vue";
import V2Img from "./V2Img.vue";
import V2Head from "./V2Head.vue";
import { localize, text, useHeading } from "./useHeading";

const props = defineProps<{ section: LinksSection; previewDevice?: "desktop" | "mobile" }>();
const { label, title, subtitleHtml, align: headAlign } = useHeading(toRef(props, "section"), "links");
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

// As setas aparecem só quando os cards não cabem (computador com 5+, tablet com 3+);
// no celular o carrossel desliza com o dedo.
const track = ref<HTMLElement | null>(null);
const overflowing = ref(false);
// Título + texto ficam com a altura do maior da mesma linha: datas, preço e
// botão começam na mesma altura em todos os cards. No celular em grade (um card
// por linha) cada card fica com a própria altura.
const equalizeText = () => {
  const el = track.value;
  if (!el) return;
  const boxes = Array.from(el.querySelectorAll<HTMLElement>(".v2-links-text"));
  const rows = new Map<number, HTMLElement[]>();
  boxes.forEach(box => {
    const top = Math.round((box.closest(".v2-links-card") as HTMLElement | null)?.offsetTop ?? 0);
    rows.set(top, [...(rows.get(top) || []), box]);
  });
  rows.forEach(row => {
    const tallest = Math.max(...row.map(box => (box.firstElementChild as HTMLElement | null)?.offsetHeight || 0));
    row.forEach(box => {
      box.style.minHeight = row.length > 1 ? `${tallest}px` : "";
    });
  });
};
const measure = () => {
  const el = track.value;
  overflowing.value = isCarousel.value && !!el && el.scrollWidth > el.clientWidth + 4;
  equalizeText();
};
let resizeObserver: ResizeObserver | null = null;
onMounted(() => {
  measure();
  // A largura dos cards e o carregamento da fonte mudam a altura do texto.
  if (typeof ResizeObserver !== "undefined" && track.value) {
    resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(track.value);
  }
  if (typeof document !== "undefined") document.fonts?.ready.then(measure);
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
.v2-links-empty {
  margin: 0 auto;
  max-width: 520px;
  padding: 18px 20px;
  border: 1px dashed var(--v2-line);
  border-radius: 16px;
  color: var(--v2-muted);
  text-align: center;
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
/* A rolagem lateral recorta o que passa da lista: a folga em cima e embaixo
   (compensada pela margem negativa) deixa caber a subida do card e a sombra do
   hover, que desce ~42px. Nas laterais não há folga, para não aparecer uma tira
   dos cards vizinhos. Os cards continuam no mesmo lugar. */
.is-carousel .v2-links-track {
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding: 8px 0 48px;
  margin: -8px 0 -48px;
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
/* Setas nas laterais, fora dos cards (os cards não encolhem). Usam a folga ao
   lado da lista, até 64px; em telas sem folga encostam na borda do card. */
.v2-links-arrow {
  position: absolute;
  z-index: 2;
  top: 50%;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: var(--v2-card);
  color: var(--v2-ink);
  box-shadow: 0 10px 28px -10px rgba(6, 12, 9, 0.4), 0 0 0 1px rgba(6, 12, 9, 0.06);
  cursor: pointer;
  transform: translateY(-50%);
  transition: transform 0.2s ease, background-color 0.2s ease, color 0.2s ease;
  --v2-links-arrow-out: min(64px, calc((100cqi - 100%) / 2 - 2px));
}
.v2-links-arrow.is-prev {
  left: calc(-1 * var(--v2-links-arrow-out));
}
.v2-links-arrow.is-next {
  right: calc(-1 * var(--v2-links-arrow-out));
}
.v2-links-arrow:hover {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  transform: translateY(-50%) scale(1.06);
}
.v2-links-arrow:focus-visible {
  outline: 2px solid var(--v2-accent);
  outline-offset: 2px;
}
/* Tablet: 2 por vez. */
@container (max-width: 1023px) {
  .v2-links-card {
    flex-basis: calc((100% - var(--v2-links-gap)) / 2);
  }
}
/* Celular: no carrossel, um card e a ponta do próximo (desliza com o dedo, sem
   setas); na grade, um embaixo do outro. */
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
  .v2-links-arrow {
    display: none;
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
  /* O card vira referência de largura para o preço se ajustar em cards estreitos. */
  container: v2-link-card / inline-size;
}
.v2-links-text {
  display: block;
}
.v2-links-text-in {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
/* Datas, preço e botão ficam juntos na base do card. */
.v2-links-foot {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
}
.v2-links-title {
  font-size: 19px;
  line-height: 1.25;
}
.v2-links-desc {
  color: var(--v2-muted);
  line-height: 1.5;
}
/* Ida e volta lado a lado; sem espaço para as duas, uma desce para baixo da outra. */
.v2-links-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(84px, 1fr));
  gap: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--v2-soft);
}
.v2-links-dt {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.v2-links-dt:only-child {
  grid-column: 1 / -1;
}
.v2-links-dt small {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--v2-muted);
}
.v2-links-dt b {
  font-size: 15px;
  white-space: nowrap;
}
/* Mesmos ícones e traço da seção antiga: contorno fino, sem fundo. */
.v2-links-ico {
  flex: 0 0 auto;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  color: var(--v2-ink);
  opacity: 0.8;
}
/* Preço no mesmo desenho das datas: "a partir de" pequeno em cima e, embaixo, o
   valor com "por pessoa" ao lado. "Por pessoa" desce inteiro quando não cabe,
   nunca quebrado no meio. */
.v2-links-price {
  display: flex;
  align-items: center;
  gap: 10px;
}
.v2-links-price-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.v2-links-price-pre {
  font-size: 12.5px;
  line-height: 1.2;
  color: var(--v2-muted);
}
.v2-links-price-line {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 6px;
  line-height: 1.15;
}
/* Valor e etiqueta na cor de destaque da página (na versão legível sobre o fundo do card). */
.v2-links-price-line b {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 22px;
  white-space: nowrap;
  color: var(--v2-accent-text);
}
.v2-links-ico--tag {
  color: var(--v2-accent-text);
  opacity: 1;
}
.v2-links-price-line small {
  font-size: 14px;
  color: var(--v2-muted);
}
/* Card estreito (computador pequeno com 4 por linha): o valor diminui um pouco
   para caber com "por pessoa" na mesma linha, sem tirar o ícone. */
@container v2-link-card (max-width: 220px) {
  .v2-links-price-line b {
    font-size: 19px;
  }
  .v2-links-price-line small {
    font-size: 13px;
  }
}
.v2-links-btn {
  --v2-btn-h: 48px;
  padding: 10px 20px;
}
.v2-links-meta + .v2-links-btn,
.v2-links-price + .v2-links-btn {
  margin-top: 4px;
}
</style>
