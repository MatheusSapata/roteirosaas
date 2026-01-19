<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="rounded-3xl bg-white/80 p-6 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.55)] ring-1 ring-slate-100">
        <div class="flex flex-wrap items-center justify-between gap-3 pb-4" :style="{ borderBottom: `1px solid ${accentBorder}` }">
          <div>
            <span class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-600" :style="{ background: accentSoft, color: accent }">
              <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>
              Galeria
            </span>
            <h2 class="mt-3 text-2xl font-bold text-slate-900">Explore o destino</h2>
            <p class="text-sm text-slate-500">Imagens reais para sentir o clima da viagem.</p>
          </div>
        </div>

        <!-- Layout mosaico -->
        <div v-if="section.layout === 'mosaic' || !section.layout" class="mt-5 grid gap-4 md:grid-cols-3">
          <div v-if="resolvedImages[0]" class="group relative overflow-hidden rounded-2xl ring-1 ring-slate-100 shadow-lg md:col-span-2">
            <img :src="resolvedImages[0]" class="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
            <div class="absolute inset-0 bg-gradient-to-t from-slate-900/40 via-transparent to-transparent opacity-0 transition group-hover:opacity-100"></div>
          </div>
          <div class="grid gap-4">
            <div
              v-for="(img, index) in resolvedImages.slice(1, 3)"
              :key="index"
              class="group relative overflow-hidden rounded-2xl ring-1 ring-slate-100 shadow-lg"
            >
              <img :src="img" class="h-40 w-full object-cover transition duration-500 group-hover:scale-105" />
              <div class="absolute inset-0 bg-gradient-to-t from-slate-900/35 via-transparent to-transparent opacity-0 transition group-hover:opacity-100"></div>
            </div>
          </div>
          <div v-if="resolvedImages.length > 3" class="grid gap-3 md:col-span-3 md:grid-cols-4">
            <div
              v-for="(img, index) in resolvedImages.slice(3)"
              :key="'thumb-' + index"
              class="group relative overflow-hidden rounded-xl ring-1 ring-slate-100 shadow-sm"
            >
              <img :src="img" class="h-32 w-full object-cover transition duration-300 group-hover:scale-105" />
              <div class="absolute inset-0 bg-slate-900/10 opacity-0 transition group-hover:opacity-100"></div>
            </div>
          </div>
        </div>

        <!-- Layout grade -->
        <div v-else-if="section.layout === 'grid'" :class="['mt-5 grid gap-4', section.fullWidth ? 'sm:grid-cols-2 lg:grid-cols-4' : 'sm:grid-cols-2 lg:grid-cols-3']">
          <div
            v-for="(img, index) in resolvedImages"
            :key="'grid-' + index"
            class="group relative overflow-hidden rounded-2xl ring-1 ring-slate-100 shadow-lg transition hover:-translate-y-0.5"
          >
            <img :src="img" class="h-48 w-full object-cover transition duration-300 group-hover:scale-105" />
            <div class="absolute inset-0 bg-gradient-to-t from-slate-900/50 via-transparent to-transparent opacity-0 transition group-hover:opacity-100"></div>
          </div>
        </div>

        <!-- Layout faixa -->
        <div v-else class="mt-5 space-y-3">
          <div class="flex gap-3 overflow-x-auto pb-2">
            <div
              v-for="(img, index) in resolvedImages"
              :key="'strip-' + index"
              class="group relative h-48 min-w-[260px] overflow-hidden rounded-2xl ring-1 ring-slate-100 shadow-md"
            >
              <img :src="img" class="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
              <div class="absolute inset-0 bg-gradient-to-t from-slate-900/40 via-transparent to-transparent opacity-0 transition group-hover:opacity-100"></div>
            </div>
          </div>
          <p class="text-xs text-slate-500" :style="{ color: accent }">Passe para o lado para ver mais fotos</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import type { GallerySection } from "../../types/page";

const props = defineProps<{ section: GallerySection }>();

const accent = computed(() => props.section.backgroundColor || "#0ea5e9");
const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const accentSoft = computed(() => toRgba(accent.value, 0.1));
const accentBorder = computed(() => toRgba(accent.value, 0.25));
const resolvedImages = computed(() =>
  (props.section.images || [])
    .map(img => resolveMediaUrl(img) || img)
    .filter(Boolean)
);
</script>
