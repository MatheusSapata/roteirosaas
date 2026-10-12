<template>
  <!-- Uma seção da página, com o mesmo componente do site, adaptada ao tamanho do post. -->
  <div class="sx" :class="{ 'sx-no-cta': !data.ctaEnabled }" :style="rootStyle">
    <div class="sx-stage" :style="stageStyle">
      <div ref="inner" class="sx-inner public-page">
        <component :is="component" v-if="component" :section="section" v-bind="extraProps" preview-device="mobile" />
      </div>
    </div>
    <div class="sx-pager" aria-hidden="true">
      <span class="sx-dots"><i v-for="dot in total" :key="dot" :class="{ on: dot === index + 1 }"></i></span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * A seção é desenhada numa largura de celular (o visual novo usa medidas relativas à largura
 * da seção) e depois ampliada até ocupar o post; seção alta encolhe para caber inteira.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import type { PageSection } from "../../types/page";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { PAGE_DESIGN_KEY } from "../public/v2/designContext";
import { PHOTO_CREDITS_KEY, buildPhotoCredits } from "../public/v2/photoCredits";
import { v2Components } from "../public/v2/registry";
import { STATIC_RENDER_KEY } from "../public/v2/useEntrance";
import { FORMAT_SIZES, effectiveColors, readableOn, type CreativeData, type CreativeFormat } from "./creativeData";

const props = defineProps<{
  section: PageSection;
  allSections: PageSection[];
  format: CreativeFormat;
  data: CreativeData;
  branding: Record<string, unknown>;
  accent: string;
  tripStartDate?: string;
  index: number;
  total: number;
  /** Não usados aqui (mesma interface dos outros slides). */
  photo?: string;
  photos?: string[];
  slide?: unknown;
  showLogo?: boolean;
}>();

provide(STATIC_RENDER_KEY, true);
provide(PAGE_DESIGN_KEY, computed(() => ({ accent: props.accent })));
provide(PUBLIC_BRANDING_KEY, computed(() => props.branding));
provide(PHOTO_CREDITS_KEY, computed(() => buildPhotoCredits(props.allSections)));

const size = computed(() => FORMAT_SIZES[props.format]);
// Largura "de celular" em que a seção é desenhada antes de ampliar.
const virtualWidth = computed(() => (props.format === "story" ? 430 : 520));
const component = computed(() => v2Components[props.section.type]);
const extraProps = computed(() => {
  const extra: Record<string, unknown> = {};
  if (props.section.type === "hero" || props.section.type === "agency_footer") extra.branding = props.branding;
  if (props.section.type === "hero") extra.hideLogo = false;
  if (props.section.type === "itinerary") extra.tripStartDate = props.tripStartDate || "";
  if (props.section.type === "agency_footer" || props.section.type === "header") extra.logoUrl = props.data.logoUrl;
  return extra;
});

const inner = ref<HTMLElement | null>(null);
const contentHeight = ref(800);
const background = ref("#ffffff");
let observer: ResizeObserver | null = null;

const measure = () => {
  const element = inner.value;
  if (!element) return;
  contentHeight.value = Math.max(1, element.scrollHeight);
  const first = element.firstElementChild as HTMLElement | null;
  const color = first ? getComputedStyle(first).backgroundColor : "";
  background.value = color && color !== "rgba(0, 0, 0, 0)" && color !== "transparent" ? color : "#ffffff";
};

const pagerInk = computed(() => {
  const match = background.value.match(/\d+(\.\d+)?/g);
  if (!match) return "#111827";
  const [r, g, b] = match.slice(0, 3).map(Number);
  return (r * 299 + g * 587 + b * 114) / 1000 > 150 ? "#111827" : "#ffffff";
});
const scale = computed(() => Math.min(size.value.width / virtualWidth.value, size.value.height / contentHeight.value));
const stageStyle = computed(() => {
  const width = virtualWidth.value * scale.value;
  const height = contentHeight.value * scale.value;
  return {
    width: `${virtualWidth.value}px`,
    left: `${Math.round((size.value.width - width) / 2)}px`,
    top: `${Math.round((size.value.height - height) / 2)}px`,
    transform: `scale(${scale.value})`
  };
});
const rootStyle = computed(() => {
  const colors = effectiveColors(props.data);
  return {
    width: `${size.value.width}px`,
    height: `${size.value.height}px`,
    background: background.value,
    // Pontinhos na cor que aparece sobre o fundo da seção (sem cápsula atrás).
    "--ink": pagerInk.value,
    "--c2": colors.secondary,
    "--on2": readableOn(colors.secondary)
  };
});

onMounted(() => {
  measure();
  if (inner.value && "ResizeObserver" in window) {
    observer = new ResizeObserver(() => measure());
    observer.observe(inner.value);
  }
});
watch(
  () => props.section,
  () => nextTick(measure),
  { deep: true }
);
onBeforeUnmount(() => observer?.disconnect());
</script>

<style scoped>
.sx {
  position: relative;
  overflow: hidden;
}
.sx-stage {
  position: absolute;
  transform-origin: top left;
}
.sx-inner {
  width: 100%;
  pointer-events: none;
}
/* A arte não é clicável: os botões da seção só aparecem com o botão ligado no passo "Botão". */
.sx-no-cta :deep(.v2-btn) {
  display: none !important;
}
/* Base discreta: só os pontinhos, centralizados, sem cápsula de fundo nem seta. */
.sx-pager {
  position: absolute;
  right: 0;
  bottom: 34px;
  left: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: var(--ink);
}
.sx-dots {
  display: flex;
  gap: 10px;
}
.sx-dots i {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.3;
}
.sx-dots i.on {
  width: 34px;
  opacity: 0.85;
}
</style>
