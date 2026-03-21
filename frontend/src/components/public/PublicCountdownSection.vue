<template>
  <section class="w-full" :style="{ background: sectionBackground }" :id="section.anchorId || undefined">
    <div class="mx-auto flex w-full max-w-6xl flex-col items-center gap-6 px-6 py-8">
      <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />

      <h1 class="text-center text-2xl font-semibold md:text-3xl" :style="{ color: titleColor }">
        {{ section.label || "Coming soon..." }}
      </h1>

      <p
        v-if="section.subtitle"
        class="max-w-3xl text-center text-sm md:text-base"
        :style="{ color: subtitleColor }"
      >
        {{ section.subtitle }}
      </p>

      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div
          v-for="part in timeParts"
          :key="part.label"
          class="flex flex-col items-center rounded-2xl bg-slate-900/80 px-6 py-4 text-white shadow-xl"
        >
          <div class="text-4xl font-extrabold tabular-nums">{{ part.value }}</div>
          <div class="mt-1 text-xs uppercase tracking-wide" :style="{ color: partLabelColor }">
            {{ part.label }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject, isRef, onBeforeUnmount, onMounted, ref } from "vue";
import type { CountdownSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";

const props = defineProps<{ section: CountdownSection }>();
const headingDefaults = getSectionHeadingDefaults("countdown");

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

const normalizeColor = (value?: string | null) => (typeof value === "string" ? value.trim() : "");

const sectionBackground = computed(
  () => normalizeColor(props.section.backgroundColor) || brandingPrimary.value || "#0b1324"
);

const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);

const parseHexColor = (color?: string | null) => {
  if (!color || typeof color !== "string") return null;

  const normalized = color.trim();
  if (!normalized.startsWith("#")) return null;

  const hex = normalized.slice(1);
  const full = hex.length === 3 ? hex.split("").map((c) => c + c).join("") : hex;

  if (full.length !== 6) return null;

  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);

  if ([r, g, b].some((value) => Number.isNaN(value))) return null;

  return { r, g, b };
};

const getLuminance = (color?: string | null) => {
  const rgb = parseHexColor(color);
  if (!rgb) return null;

  return (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
};

const getContrastTextColor = (color?: string) => {
  const luminance = getLuminance(color);
  if (luminance === null) return "#ffffff";
  return luminance > 0.6 ? "#111827" : "#ffffff";
};

const baseTextColor = computed(() => props.section.textColor || getContrastTextColor(sectionBackground.value));

const titleColor = computed(() => getContrastTextColor(sectionBackground.value));

const subtitleColor = computed(() => {
  const luminance = getLuminance(sectionBackground.value);

  if (luminance === null) {
    return "rgba(255,255,255,0.82)";
  }

  return luminance > 0.6 ? "rgba(15,23,42,0.72)" : "rgba(255,255,255,0.82)";
});

/**
 * Regra de luminância no heading:
 * fundo claro -> heading escuro
 * fundo escuro -> heading claro
 */
const headingAccent = computed(() => {
  const luminance = getLuminance(sectionBackground.value);

  if (luminance === null) {
    return "#0f172a";
  }

  return luminance > 0.6 ? "#0f172a" : "rgba(255,255,255,0.92)";
});

/**
 * Os labels "DIAS / HORAS..." ficam dentro de cards escuros,
 * então a cor deles deve contrastar com o card, não com o fundo da seção.
 */
const partLabelColor = computed(() => "rgba(255,255,255,0.68)");

const timeParts = ref([
  { label: "Dias", value: "00" },
  { label: "Horas", value: "00" },
  { label: "Minutos", value: "00" },
  { label: "Segundos", value: "00" }
]);

let timer: number | undefined;

const fallbackFutureMs = () => Date.now() + 3 * 24 * 60 * 60 * 1000;

const targetMs = computed(() => {
  const raw = props.section.targetDate;
  if (!raw) return fallbackFutureMs();

  const normalized = raw.includes("T") ? raw : raw.replace(" ", "T");
  const parsed = Date.parse(normalized);

  if (Number.isNaN(parsed)) return fallbackFutureMs();
  if (parsed <= Date.now()) return fallbackFutureMs();

  return parsed;
});

const pad = (n: number) => n.toString().padStart(2, "0");

const tick = () => {
  const diff = targetMs.value - Date.now();
  const targetDiff = Number.isNaN(diff) || diff <= 0 ? fallbackFutureMs() - Date.now() : diff;
  const totalSeconds = Math.max(0, Math.floor(targetDiff / 1000));

  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  timeParts.value = [
    { label: "Dias", value: pad(days) },
    { label: "Horas", value: pad(hours) },
    { label: "Minutos", value: pad(minutes) },
    { label: "Segundos", value: pad(seconds) }
  ];
};

onMounted(() => {
  tick();
  timer = window.setInterval(tick, 1000);
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
});
</script>