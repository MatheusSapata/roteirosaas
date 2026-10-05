<template>
  <section ref="root" :id="anchorId || undefined" class="v2-sec" :class="[`v2-sec--${type}`, { 'v2-sec--flush': flush, 'v2-armed': armed, 'v2-on': shown }]" :style="vars">
    <div class="v2-wrap" :class="{ 'v2-wrap--full': full }">
      <slot :tone="tone" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useSectionTone } from "./useSectionTone";
import "./v2.css";

const props = withDefaults(
  defineProps<{
    type: string;
    background?: string | null;
    fallbackBackground?: string;
    anchorId?: string;
    flush?: boolean;
    full?: boolean;
  }>(),
  { background: null, fallbackBackground: "#FFFFFF", anchorId: undefined, flush: false, full: false }
);

const { tone, vars } = useSectionTone(computed(() => props.background), props.fallbackBackground);

// Animação de entrada: arma a seção só com JS e IntersectionObserver disponíveis,
// para o conteúdo nunca ficar invisível; dispara uma vez, com 15% visível.
const root = ref<HTMLElement | null>(null);
const armed = ref(false);
const shown = ref(false);
let observer: IntersectionObserver | null = null;

onMounted(() => {
  if (typeof window === "undefined" || !("IntersectionObserver" in window) || !root.value) return;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  const rect = root.value.getBoundingClientRect();
  if (rect.top < window.innerHeight && rect.bottom > 0) return;
  armed.value = true;
  observer = new IntersectionObserver(
    entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        shown.value = true;
        observer?.disconnect();
      }
    },
    { threshold: 0.15 }
  );
  observer.observe(root.value);
});

onBeforeUnmount(() => observer?.disconnect());
</script>
