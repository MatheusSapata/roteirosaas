<template>
  <!-- Os caminhos vêm só da lista fixa em utils/travelIcons.ts, nunca de dados do usuário. -->
  <svg
    v-if="icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="icon.paths"
  ></svg>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { TRAVEL_ICONS, travelIconKey, type TravelIconKey } from "../../utils/travelIcons";

const props = withDefaults(defineProps<{ name?: string | null; size?: number | string; strokeWidth?: number | string }>(), {
  name: null,
  size: 18,
  strokeWidth: 2
});
const icon = computed(() => {
  const raw = props.name || "";
  const key = (travelIconKey(raw) || (raw in TRAVEL_ICONS ? raw : null)) as TravelIconKey | null;
  return key ? TRAVEL_ICONS[key] : null;
});
</script>
