<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="rounded-3xl bg-white/85 p-6 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.55)] ring-1 ring-slate-100">
        <div class="flex flex-wrap items-center justify-between gap-3 pb-4" :style="{ borderBottom: `1px solid ${accentBorder}` }">
          <div>
            <span class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-600" :style="{ background: accentSoft, color: accent }">
              <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>
              Investimento
            </span>
            <h2 class="mt-3 text-2xl font-bold text-slate-900">Planos e opções</h2>
            <p class="text-sm text-slate-500">Escolha o formato que combina com você.</p>
          </div>
        </div>

        <!-- Layout cards -->
        <div v-if="section.layout === 'cards' || !section.layout" :class="['mt-5 grid gap-4', section.fullWidth ? 'md:grid-cols-3' : 'md:grid-cols-2']">
          <article
            v-for="(item, index) in section.items"
            :key="'card-' + index"
            class="relative overflow-hidden rounded-2xl border border-slate-100 bg-white p-5 shadow-lg transition hover:-translate-y-1 hover:shadow-xl"
          >
            <div class="absolute inset-x-0 top-0 h-1" :style="{ background: accent }"></div>
            <p class="text-lg font-semibold text-slate-900">{{ item.title }}</p>
            <p class="mt-2 text-3xl font-bold" :style="{ color: accent }">R$ {{ item.price.toLocaleString('pt-BR') }}</p>
            <p class="mt-2 text-sm text-slate-600">{{ item.description }}</p>
            <div class="mt-4 space-y-2 text-sm text-slate-600">
              <div class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full" :style="{ background: accent }"></span>Suporte dedicado
              </div>
              <div class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full" :style="{ background: accentSoft }"></span>Pagamento facilitado
              </div>
            </div>
            <a
              v-if="ctaLink"
              :href="ctaLink"
              target="_blank"
              rel="noopener"
              data-track-event="cta"
              :data-track-type="ctaTrackType"
              class="mt-4 inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:shadow-lg"
              :style="{ background: buttonColor }"
            >
              Falar com consultor
            </a>
          </article>
        </div>

        <!-- Layout colunas -->
        <div v-else-if="section.layout === 'columns'" class="mt-6 space-y-4">
          <article
            v-for="(item, index) in section.items"
            :key="'column-' + index"
            class="flex flex-col gap-4 rounded-2xl border border-slate-100 bg-white/95 p-5 shadow-md transition hover:-translate-y-0.5 hover:shadow-lg md:flex-row md:items-center md:justify-between"
          >
            <div class="space-y-1">
              <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Pacote</p>
              <p class="text-xl font-semibold text-slate-900">{{ item.title }}</p>
              <p class="text-sm text-slate-600">{{ item.description }}</p>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <p class="text-sm text-slate-500">Investimento</p>
                <p class="text-3xl font-bold" :style="{ color: accent }">R$ {{ item.price.toLocaleString('pt-BR') }}</p>
              </div>
              <a
                v-if="ctaLink"
                :href="ctaLink"
                target="_blank"
                rel="noopener"
                data-track-event="cta"
                :data-track-type="ctaTrackType"
                class="inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
                :style="{ background: accent }"
              >
                Reservar
              </a>
          </div>
          </article>
        </div>

        <!-- Layout destaque -->
        <div v-else class="mt-6 space-y-4">
          <article
            v-if="section.items[0]"
            class="relative overflow-hidden rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl transition"
          >
            <div class="absolute inset-x-0 top-0 h-1.5" :style="{ background: accent }"></div>
            <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Recomendado</p>
                <p class="text-2xl font-bold text-slate-900">{{ section.items[0].title }}</p>
                <p class="text-sm text-slate-600">{{ section.items[0].description }}</p>
              </div>
              <div class="flex items-center gap-4">
                <p class="text-4xl font-bold" :style="{ color: accent }">R$ {{ section.items[0].price.toLocaleString('pt-BR') }}</p>
                <a
                  v-if="ctaLink"
                  :href="ctaLink"
                  target="_blank"
                  rel="noopener"
                  data-track-event="cta"
                  :data-track-type="ctaTrackType"
                  class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
                  :style="{ background: buttonColor }"
                >
                  Falar agora
                </a>
              </div>
            </div>
          </article>
          <div class="grid gap-3 md:grid-cols-2">
            <article
              v-for="(item, index) in section.items.slice(1)"
              :key="'highlight-' + index"
              class="rounded-2xl border border-slate-100 bg-white/95 p-4 shadow-md"
            >
              <p class="text-base font-semibold text-slate-900">{{ item.title }}</p>
              <p class="text-2xl font-bold" :style="{ color: accent }">R$ {{ item.price.toLocaleString('pt-BR') }}</p>
              <p class="text-sm text-slate-600">{{ item.description }}</p>
            </article>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PricesSection } from "../../types/page";
import { isWhatsappLink } from "../../utils/links";

const props = defineProps<{ section: PricesSection; ctaLink?: string }>();
const ctaLink = props.ctaLink || "#";

const defaultAccent = "#0ea5e9";
const buttonColor = computed(() => props.section.ctaColor || defaultAccent);
const accent = computed(() => buttonColor.value);
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
const ctaTrackType = computed(() => (isWhatsappLink(ctaLink) ? "whatsapp" : "cta"));
</script>
