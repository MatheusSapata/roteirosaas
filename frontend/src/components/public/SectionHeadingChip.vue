<template>
  <span v-if="textToShow" class="heading-chip-wrapper">
    <span
      class="heading-chip mb-3 inline-flex w-auto max-w-full shrink-0 items-center justify-center rounded-full border px-4 py-1 text-[11px] font-semibold uppercase tracking-[0.3em] whitespace-normal md:whitespace-nowrap break-words"
      :style="chipStyle"
    >
      {{ textToShow.toUpperCase() }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed, inject, isRef } from "vue";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { createLocalizer, getCurrentLanguage, type LocalizedString } from "../../utils/i18n";

const props = defineProps<{
  text?: LocalizedString;
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

const accentColor = computed(() => props.accent?.trim() || brandingPrimary.value || "#41ce5f");
const localize = createLocalizer(getCurrentLanguage());
const textToShow = computed(() => {
  const localized = localize(props.text);
  return localized.trim();
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

<style scoped>
.heading-chip-wrapper {
  display: inline-flex;
  max-width: 100%;
}

.heading-chip {
  flex-wrap: nowrap;
}

@media (max-width: 640px) {
  .heading-chip-wrapper {
    width: 100%;
    justify-content: center;
  }

  .heading-chip {
    flex-wrap: wrap;
    white-space: normal;
    word-break: break-word;
    max-width: 100%;
    text-align: center;
  }
}
</style>
