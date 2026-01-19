<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6">
        <div class="flex items-start justify-between gap-4">
          <div class="pl-12 md:pl-14">
            <p class="text-sm uppercase tracking-wide text-slate-500">Itinerário</p>
            <h2 class="text-2xl font-bold text-slate-900">Dia a dia</h2>
            <p class="text-sm text-slate-500">Visão clara do roteiro completo.</p>
          </div>
        </div>

        <!-- Timeline layout -->
        <div v-if="section.layout === 'timeline' || !section.layout" class="relative pl-8 md:pl-10">
          <div class="absolute left-8 md:left-10 top-4 bottom-4 w-px bg-slate-200"></div>
          <div class="space-y-3">
            <div
              v-for="(day, index) in section.days"
              :key="index"
              class="group relative ml-3 flex w-full flex-col gap-3 rounded-2xl border border-slate-100 bg-white/90 p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
              :style="{ boxShadow: `0 20px 40px -30px ${accentShadow}` }"
            >
              <button
                class="flex w-full items-start gap-4 text-left"
                @click="toggleDay(index)"
              >
                <div
                  class="flex h-8 w-8 items-center justify-center rounded-full border bg-white text-xs font-semibold transition group-hover:-translate-y-0.5"
                  :style="{ borderColor: accent, color: accent }"
                >
                  {{ index + 1 }}
                </div>
                <div class="flex-1 space-y-1">
                  <p class="text-xs font-semibold uppercase tracking-wide" :style="{ color: accent }">{{ day.day }}</p>
                  <p class="text-lg font-semibold text-slate-900">{{ day.title }}</p>
                  <p v-if="!expanded[index]" class="text-xs text-slate-400">Clique para ver detalhes</p>
                </div>
                <span class="text-sm text-slate-500">{{ expanded[index] ? "−" : "+" }}</span>
              </button>
              <div v-if="expanded[index]" class="pl-12 text-sm leading-relaxed text-slate-600">
                {{ day.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- Steps layout -->
        <div v-else-if="section.layout === 'steps'" class="space-y-6">
          <div class="relative">
            <div class="absolute left-0 right-0 top-[22px] h-0.5 bg-slate-200"></div>
            <div class="flex flex-wrap items-start justify-around gap-6">
              <button
                v-for="(day, index) in section.days"
                :key="'step-' + index"
                class="relative flex flex-col items-center gap-2 bg-transparent text-left"
                @click="toggleStep(index)"
              >
                <div
                class="flex h-12 w-12 items-center justify-center rounded-full border-2 bg-white text-sm font-semibold shadow-sm transition hover:-translate-y-0.5"
                  :style="{ borderColor: accent.value, color: accent.value }"
                >
                  {{ index + 1 }}
                </div>
                <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold" :style="{ color: accent.value }">
                  {{ day.day || `Passo ${index + 1}` }}
                </span>
              </button>
            </div>
          </div>
          <div v-if="activeStep !== null" class="rounded-2xl border border-slate-100 bg-white/95 p-5 shadow-[0_20px_45px_-34px_rgba(15,23,42,0.6)]">
            <p class="text-xs uppercase tracking-wide text-slate-500">Passo {{ (activeStep || 0) + 1 }}</p>
            <h3 class="mt-2 text-lg font-semibold text-slate-900">{{ section.days[activeStep]?.title }}</h3>
            <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ section.days[activeStep]?.description }}</p>
          </div>
        </div>

        <!-- Cards layout -->
        <div v-else-if="section.layout === 'cards'" :class="['grid gap-4', section.fullWidth ? 'md:grid-cols-3' : 'md:grid-cols-2']">
          <div
            v-for="(day, index) in section.days"
            :key="index"
            class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            :style="{ borderColor: accentSoft }"
          >
            <p class="text-sm font-semibold" :style="{ color: accent }">Dia {{ index + 1 }} • {{ day.day }}</p>
            <p class="text-lg font-semibold text-slate-900">{{ day.title }}</p>
            <p class="text-sm leading-relaxed text-slate-600">{{ day.description }}</p>
          </div>
        </div>

        <!-- Minimal layout -->
        <div v-else class="space-y-3">
          <div
            v-for="(day, index) in section.days"
            :key="index"
            class="rounded-xl border border-slate-100 bg-white/90 p-4 shadow-sm"
            :style="{ borderColor: accentSoft }"
          >
            <p class="text-sm font-semibold" :style="{ color: accent }">Dia {{ index + 1 }} • {{ day.day }}</p>
            <p class="text-lg font-semibold text-slate-900">{{ day.title }}</p>
            <p class="text-sm leading-relaxed text-slate-600">{{ day.description }}</p>
          </div>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { ItinerarySection } from "../../types/page";

const props = defineProps<{ section: ItinerarySection }>();
const defaultAccent = "#0ea5e9";

const isLight = (hex?: string) => {
  if (!hex) return true;
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return true;
  const r = parseInt(full.substring(0, 2), 16) / 255;
  const g = parseInt(full.substring(2, 4), 16) / 255;
  const b = parseInt(full.substring(4, 6), 16) / 255;
  const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
  return luminance > 0.8;
};

const accent = computed(() => {
  const bg = props.section.backgroundColor;
  if (!bg || isLight(bg)) return defaultAccent;
  return bg;
});
const expanded = ref<boolean[]>([]);
const activeStep = ref<number | null>(null);

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const accentSoft = computed(() => toRgba(accent.value, 0.12));
const accentShadow = computed(() => toRgba(accent.value, 0.35));

const toggleDay = (index: number) => {
  expanded.value[index] = !expanded.value[index];
};

expanded.value = props.section.days.map(() => false);

const toggleStep = (index: number) => {
  activeStep.value = activeStep.value === index ? null : index;
};
</script>
