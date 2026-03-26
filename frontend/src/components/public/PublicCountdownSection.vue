<template>
  <section class="w-full" :style="{ background: barBackground }" :id="section.anchorId || undefined">
    <div v-if="layout === 'bar'" class="mx-auto w-full px-0 pt-5 pb-3 md:pt-7 md:pb-4 space-y-0">
      <div class="flex justify-center -mb-2">
        <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
      </div>
      <div
        class="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 rounded-xl px-4 py-3 shadow-lg md:px-8"
        :style="{ background: section.backgroundColor || '#6b21a8', color: section.textColor || '#ffffff' }"
      >
        <div class="text-2xl font-extrabold tabular-nums md:text-3xl">
          {{ barTime }}
        </div>
      <div class="flex items-center gap-2">
          <span class="text-3xl">&#9889;</span>
          <h1 class="text-3xl font-bold leading-tight md:text-4xl">
            {{ section.label || "Garanta sua vaga agora mesmo!" }}
          </h1>
        </div>
      </div>
    </div>

    <div v-else class="mx-auto flex w-full max-w-6xl flex-col items-center gap-4 px-6 pt-8 pb-6">
      <div class="-mb-2">
        <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
      </div>
      <h1 class="text-center text-3xl font-bold md:text-4xl mb-1" :style="{ color: section.textColor || '#ffffff' }">
        {{ section.label || "Coming soon..." }}
      </h1>
      <div class="mt-1 grid grid-cols-2 gap-3 md:grid-cols-4 pb-4">
        <div
          v-for="part in timeParts"
          :key="part.label"
          class="flex flex-col items-center rounded-2xl bg-slate-900/80 px-6 py-4 text-white shadow-xl"
        >
          <div class="text-4xl font-extrabold tabular-nums">{{ part.value }}</div>
          <div class="mt-1 text-xs uppercase tracking-wide text-white">
            {{ part.label }}
          </div>
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
const headingAccent = computed(() => props.section.textColor || "#ffffff");

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
