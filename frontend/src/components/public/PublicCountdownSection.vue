<template>
  <section class="w-full" :style="{ background: barBackground }" :id="section.anchorId || undefined">
    <div v-if="layout === 'bar'" class="mx-auto w-full px-0 py-4 md:py-6 space-y-3">
      <div class="flex justify-center">
        <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
      </div>
      <div
        class="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 rounded-xl px-4 py-3 shadow-lg md:px-8"
        :style="{ background: section.backgroundColor || '#6b21a8', color: section.textColor || '#ffffff' }"
      >
        <div class="text-2xl font-extrabold tabular-nums md:text-3xl">
          {{ barTime }}
        </div>
        <div class="flex items-center gap-2 text-sm font-semibold md:text-base">
          <span class="text-lg md:text-xl">⏳</span>
          <span class="text-right">{{ section.label || "Garanta sua vaga agora mesmo!" }}</span>
        </div>
      </div>
    </div>

    <div v-else class="mx-auto flex w-full max-w-6xl flex-col items-center gap-6 px-6 py-8">
      <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
      <h3 class="text-center text-xl font-semibold" :style="{ color: section.textColor || '#ffffff' }">
        {{ section.label || "Coming soon..." }}
      </h3>
      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div
          v-for="part in timeParts"
          :key="part.label"
          class="flex flex-col items-center rounded-2xl bg-slate-900/80 px-6 py-4 text-white shadow-xl"
        >
          <div class="text-4xl font-extrabold tabular-nums">{{ part.value }}</div>
          <div class="mt-1 text-xs uppercase tracking-wide text-amber-400">{{ part.label }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import type { CountdownSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";

const props = defineProps<{ section: CountdownSection }>();
const headingDefaults = getSectionHeadingDefaults("countdown");

const layout = computed(() => props.section.layout || "bar");
const barBackground = computed(() => (layout.value === "bar" ? "#f8fafc" : props.section.backgroundColor || "#0b1324"));
const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const headingAccent = computed(() => props.section.backgroundColor || "#0ea5e9");

const barTime = ref("00:00:00");
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
  if (Number.isNaN(diff) || diff <= 0) {
    const fallback = fallbackFutureMs() - Date.now();
    const totalSecondsFallback = Math.floor(fallback / 1000);
    const fallbackDays = Math.floor(totalSecondsFallback / 86400);
    const fallbackHours = Math.floor((totalSecondsFallback % 86400) / 3600);
    const fallbackMinutes = Math.floor((totalSecondsFallback % 3600) / 60);
    const fallbackSeconds = totalSecondsFallback % 60;
    barTime.value = `${pad(Math.floor(totalSecondsFallback / 3600))}:${pad(fallbackMinutes)}:${pad(fallbackSeconds)}`;
    timeParts.value = [
      { label: "Dias", value: pad(fallbackDays) },
      { label: "Horas", value: pad(fallbackHours) },
      { label: "Minutos", value: pad(fallbackMinutes) },
      { label: "Segundos", value: pad(fallbackSeconds) }
    ];
    return;
  }
  const totalSeconds = Math.floor(diff / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const totalHours = Math.floor(totalSeconds / 3600);
  barTime.value = `${pad(totalHours)}:${pad(minutes)}:${pad(seconds)}`;
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
