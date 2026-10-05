<template>
  <!-- Os desenhos vêm só das listas fixas (ícones básicos e biblioteca Lucide), nunca de dados do usuário. -->
  <svg
    v-if="basic"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="basic.paths"
  ></svg>
  <component :is="libraryIcon" v-else-if="libraryIcon" />
  <span v-else-if="name && iconName" class="travel-icon-placeholder" :style="{ width: `${size}px`, height: `${size}px` }" aria-hidden="true"></span>
</template>

<script setup lang="ts">
import { computed, h, shallowRef, watch } from "vue";
import { loadIconLibrary, renderIconNodes, type IconNode } from "../../utils/iconLibrary";
import { TRAVEL_ICONS, iconValueName, type TravelIconKey } from "../../utils/travelIcons";

const props = withDefaults(defineProps<{ name?: string | null; size?: number | string; strokeWidth?: number | string }>(), {
  name: null,
  size: 18,
  strokeWidth: 2
});

// Aceita "icon:nome" ou só o nome.
const iconName = computed(() => {
  const raw = props.name || "";
  return iconValueName(raw) || (raw && !raw.includes(":") ? raw : null);
});
const basic = computed(() => {
  const key = iconName.value as TravelIconKey | null;
  return key && key in TRAVEL_ICONS ? TRAVEL_ICONS[key] : null;
});

// Fora dos básicos, carrega a biblioteca completa (uma vez só, em arquivo separado).
const nodes = shallowRef<IconNode[] | null>(null);
watch(
  iconName,
  async name => {
    nodes.value = null;
    if (!name || basic.value) return;
    const library = await loadIconLibrary();
    if (iconName.value === name) nodes.value = library[name] || null;
  },
  { immediate: true }
);
const libraryIcon = computed(() => {
  if (!nodes.value) return null;
  const children = renderIconNodes(nodes.value);
  return () =>
    h(
      "svg",
      {
        width: props.size,
        height: props.size,
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        "stroke-width": props.strokeWidth,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        "aria-hidden": "true"
      },
      children
    );
});
</script>

<style scoped>
.travel-icon-placeholder {
  display: inline-block;
}
</style>
