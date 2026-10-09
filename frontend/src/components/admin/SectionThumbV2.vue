<template>
  <span ref="rootRef" class="stv" :class="`stv--${type}`" :style="{ paddingTop: `${offsetTop}px` }" aria-hidden="true">
    <span v-if="visible && width" ref="stageRef" class="stv-stage" :style="{ width: `${BASE_WIDTH}px`, transform: `scale(${width / BASE_WIDTH})`, '--stv-video': `url(${videoPoster})` }" inert>
      <span class="stv-page public-tokens preview-light">
        <component :is="component" v-if="component && sample" :section="sample" preview-device="desktop" v-bind="extraProps" />
        <component :is="heroComponent" v-if="type === 'header' && heroComponent && heroSample" :section="heroSample" preview-device="desktop" hide-logo />
      </span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { SAMPLE_PHOTOS } from "../../utils/sectionSamplesV2";
import type { SectionType } from "../../types/page";
import { buildSectionSampleV2, SAMPLE_BRANDING } from "../../utils/sectionSamplesV2";
import { v2Components } from "../public/v2/registry";

/**
 * Miniatura do seletor de seções: a própria seção do visual novo, com conteúdo de exemplo,
 * desenhada na largura de um computador e reduzida para caber no cartão.
 */
const props = defineProps<{ type: SectionType }>();
const BASE_WIDTH = 960;
const videoPoster = SAMPLE_PHOTOS.praia.replace("w=1600", "w=900");

const component = computed(() => v2Components[props.type]);
const sample = computed(() => buildSectionSampleV2(props.type));
// O Menu do topo sozinho é uma faixa fina: a miniatura mostra ele sobre uma capa.
const heroComponent = computed(() => (props.type === "header" ? v2Components.hero : undefined));
const heroSample = computed(() => (props.type === "header" ? buildSectionSampleV2("hero") : null));
const extraProps = computed<Record<string, unknown>>(() => {
  if (props.type === "hero") return { branding: SAMPLE_BRANDING, hideLogo: true };
  if (props.type === "agency_footer") return { branding: SAMPLE_BRANDING };
  if (props.type === "header") return { agencyName: SAMPLE_BRANDING.agency_name };
  return {};
});

const rootRef = ref<HTMLElement | null>(null);
const stageRef = ref<HTMLElement | null>(null);
const width = ref(0);
// Seções mais baixas que o cartão ficam no meio dele; as altas começam do topo.
const offsetTop = ref(0);
let stageObserver: ResizeObserver | null = null;
const centerStage = () => {
  const root = rootRef.value;
  const stage = stageRef.value;
  if (!root || !stage) return;
  offsetTop.value = Math.max(0, Math.round((root.getBoundingClientRect().height - stage.getBoundingClientRect().height) / 2));
};
watch(stageRef, stage => {
  stageObserver?.disconnect();
  if (!stage || typeof ResizeObserver === "undefined") return;
  stageObserver = new ResizeObserver(centerStage);
  stageObserver.observe(stage);
});
const visible = ref(false);
let resizeObserver: ResizeObserver | null = null;
let intersectionObserver: IntersectionObserver | null = null;

onMounted(() => {
  const el = rootRef.value;
  if (!el) return;
  width.value = el.clientWidth;
  if (typeof ResizeObserver !== "undefined") {
    resizeObserver = new ResizeObserver(entries => {
      width.value = Math.round(entries[0]?.contentRect.width || 0);
      centerStage();
    });
    resizeObserver.observe(el);
  }
  // Só desenha quando o cartão aparece na lista: as fotos de exemplo carregam aos poucos.
  if (typeof IntersectionObserver === "undefined") {
    visible.value = true;
    return;
  }
  intersectionObserver = new IntersectionObserver(
    entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        visible.value = true;
        intersectionObserver?.disconnect();
      }
    },
    { rootMargin: "200px" }
  );
  intersectionObserver.observe(el);
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  intersectionObserver?.disconnect();
  stageObserver?.disconnect();
});
</script>

<style scoped>
.stv {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: #f2f4f1;
  pointer-events: none;
}
/* Reduzida com transform, não com zoom: o Safari não deixa o zoom levar a letra abaixo de
   ~9px, e na miniatura (1/8 do tamanho) o texto ficava gigante e empilhado. */
.stv-stage {
  display: block;
  flex-shrink: 0;
  transform-origin: 0 0;
}
.stv-page {
  display: block;
  background: #fff;
  --page-zoom: 1;
}
/* Na miniatura tudo aparece de uma vez, sem a animação de entrada da página. */
.stv :deep(.v2-in),
.stv :deep(.v2-reveal) {
  opacity: 1 !important;
  transform: none !important;
  animation: none !important;
}
.stv :deep(iframe) {
  display: none;
}
/* Vídeo sem link: a miniatura mostra uma foto com o botão de play no lugar do aviso. */
.stv :deep(.v2-fv-empty),
.stv--video_vsl :deep(.v2-vsl .rounded-3xl) {
  position: relative;
  aspect-ratio: 16 / 9;
  padding: 0;
  overflow: hidden;
  border-radius: 24px;
  background: var(--stv-video) center / cover;
  font-size: 0;
}
.stv :deep(.v2-fv-empty)::after,
.stv--video_vsl :deep(.v2-vsl .rounded-3xl)::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 96px;
  height: 96px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='m9 6 10 6-10 6z' fill='%230f1713'/%3E%3C/svg%3E") center / 44px no-repeat;
  transform: translate(-50%, -50%);
  box-shadow: 0 18px 40px -16px rgba(6, 12, 9, 0.6);
}
</style>
