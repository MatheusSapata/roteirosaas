<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6 rounded-3xl bg-white/85 p-6 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.55)] ring-1 ring-slate-100">
        <div>
          <span class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-600" :style="{ background: accentSoft, color: accent }">
            <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>
            FAQ
          </span>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Perguntas frequentes</h2>
          <p class="text-sm text-slate-500">As dúvidas mais comuns sobre o roteiro.</p>
        </div>

        <!-- Accordion layout -->
        <div v-if="section.layout === 'accordion' || !section.layout" class="space-y-3">
          <details
            v-for="(item, index) in section.items"
            :key="index"
            class="group rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
            :style="{ borderColor: accentSoft }"
          >
            <summary class="cursor-pointer text-sm font-semibold text-slate-900">{{ item.question }}</summary>
            <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ item.answer }}</p>
          </details>
        </div>

        <!-- Split layout -->
        <div v-else-if="section.layout === 'split'" class="grid gap-4 md:grid-cols-2">
          <div class="space-y-3">
            <div
              v-for="(item, index) in leftItems"
              :key="'left-' + index"
              class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              :style="{ borderColor: accentSoft }"
            >
              <p class="text-sm font-semibold text-slate-900">{{ item.question }}</p>
              <p class="text-sm leading-relaxed text-slate-600">{{ item.answer }}</p>
            </div>
          </div>
          <div class="space-y-3">
            <div
              v-for="(item, index) in rightItems"
              :key="'right-' + index"
              class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              :style="{ borderColor: accentSoft }"
            >
              <p class="text-sm font-semibold text-slate-900">{{ item.question }}</p>
              <p class="text-sm leading-relaxed text-slate-600">{{ item.answer }}</p>
            </div>
          </div>
        </div>

        <!-- Compact layout -->
        <div v-else class="grid gap-3 md:grid-cols-2">
          <div
            v-for="(item, index) in section.items"
            :key="index"
            class="rounded-xl border border-slate-100 bg-white/90 p-3 shadow-sm"
            :style="{ borderColor: accentSoft }"
          >
            <p class="text-sm font-semibold text-slate-900">{{ item.question }}</p>
            <p class="text-sm leading-relaxed text-slate-600">{{ item.answer }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { FaqSection } from "../../types/page";

const props = defineProps<{ section: FaqSection }>();

const middle = computed(() => Math.ceil((props.section.items?.length || 0) / 2));
const leftItems = computed(() => props.section.items?.slice(0, middle.value) || []);
const rightItems = computed(() => props.section.items?.slice(middle.value) || []);

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
const accentSoft = computed(() => toRgba(accent.value, 0.12));
</script>
