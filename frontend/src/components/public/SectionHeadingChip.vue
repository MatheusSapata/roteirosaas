<template>
  <span
    v-if="textToShow"
    class="inline-flex w-max shrink-0 items-center justify-center rounded-full border px-4 py-1 text-[11px] font-semibold uppercase tracking-[0.3em] whitespace-nowrap"
    :style="chipStyle"
  >
    {{ textToShow.toUpperCase() }}
  </span>
</template>

<script setup lang="ts">
import { computed, inject, isRef } from "vue";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";

const props = defineProps<{
  text?: string;
  accent?: string;
  styleType?: "filled" | "outline";
}>();

const branding = inject(PUBLIC_BRANDING_KEY, null);

const brandingPrimary = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;
  if (typeof data === "object" && data) {
    const color = (data as Record<string, any>).primary_color;
    if (typeof color === "string" && color.trim()) return color.trim();
  }
  return "";
});

const accentColor = computed(() => brandingPrimary.value || props.accent?.trim() || "#0ea5e9");

const textToShow = computed(() => {
  const t = props.text?.trim();
  return t && t.length ? t : "";
});

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "").trim();
  const full =
    cleaned.length === 3
      ? cleaned.split("").map((c) => c + c).join("")
      : cleaned;

  if (!/^[0-9a-fA-F]{6}$/.test(full)) return `rgba(14,165,233,${alpha})`;

  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const chipStyle = computed(() => ({
  borderColor: toRgba(accentColor.value, 0.4),
  color: accentColor.value,
  background: toRgba(accentColor.value, 0.08),
}));
</script>
