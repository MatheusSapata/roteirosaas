<template>
  <section ref="root" :id="anchorId || undefined" class="v2-sec" :class="[`v2-sec--${type}`, { 'v2-sec--flush': flush, 'v2-armed': armed, 'v2-on': shown }]" :style="vars">
    <div class="v2-wrap" :class="{ 'v2-wrap--full': full }">
      <slot :tone="tone" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useSectionTone } from "./useSectionTone";
import { useEntrance } from "./useEntrance";
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

// Animação de entrada (useEntrance): também nas seções da primeira tela, como o Banner.
const root = ref<HTMLElement | null>(null);
const { armed, shown } = useEntrance(root);
</script>
