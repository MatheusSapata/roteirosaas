<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6">
        <div class="pb-4 text-center" :style="{ borderBottom: `1px solid ${accentBorder}` }">
          <div class="flex justify-center">
            <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accent" />
          </div>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Planos e opções</h2>
          <p class="text-sm text-slate-500">Escolha o formato que combina com você.</p>
        </div>

        <div class="space-y-8">
          <article
            v-for="(item, index) in section.items"
            :key="'column-' + index"
            :class="[
              'relative flex flex-col gap-4 rounded-2xl border p-5 text-center transition md:flex-row md:items-center md:justify-between md:text-left',
              item.highlight
                ? 'border-transparent text-white shadow-xl hover:-translate-y-1 hover:shadow-2xl'
                : 'border-slate-100 bg-white/95 text-slate-900 hover:-translate-y-0.5 hover:shadow-lg'
            ]"
            :style="item.highlight ? highlightCardStyle : undefined"
          >
            <div class="space-y-2 text-center md:text-left">
              <p
                v-if="item.titleLabel"
                class="text-xs uppercase tracking-[0.2em] md:mt-0"
                :class="[item.highlight ? 'text-white/80' : 'text-slate-500', 'mt-4']"
              >
                {{ item.titleLabel.toUpperCase() }}
              </p>
              <p class="text-xl font-semibold" :class="item.highlight ? 'text-white' : 'text-slate-900'">{{ item.title }}</p>
            </div>
            <div class="flex flex-col items-center gap-4 md:flex-row md:items-center md:justify-between">
              <div class="space-y-1 md:text-right">
                <p
                  v-if="item.priceLabel"
                  class="text-sm font-medium"
                  :class="item.highlight ? 'text-white/80' : 'text-slate-500'"
                >
                  {{ item.priceLabel }}
                </p>
                <p class="text-3xl font-bold" :style="{ color: item.highlight ? '#ffffff' : accent }">
                  {{ formatPrice(item.price, item.currency) }}
                </p>
                <p v-if="item.description" class="text-xs" :class="item.highlight ? 'text-white/80' : 'text-slate-500'">
                  {{ item.description }}
                </p>
              </div>
              <a
                v-if="ctaLink"
                :href="ctaLink"
                target="_blank"
                rel="noopener"
                data-track-event="cta"
                :data-track-type="ctaTrackType"
                :class="[
                  'inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold shadow-md transition w-full md:w-auto max-w-sm mx-auto md:mx-0',
                  item.highlight ? 'text-slate-900 hover:-translate-y-0.5 hover:shadow-xl' : 'text-white hover:-translate-y-0.5 hover:shadow-lg'
                ]"
                :style="{ background: item.highlight ? '#ffffff' : accent }"
              >
                Reservar
              </a>
            </div>
            <span
              v-if="item.badge"
              class="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full border px-4 py-1 text-xs font-semibold uppercase tracking-wide shadow-sm"
              :style="badgeStyle(item.highlight)"
            >
              <span aria-hidden="true">★</span>
              {{ item.badge }}
            </span>
          </article>

        </div>

        <p v-if="section.description" class="mt-6 text-sm text-slate-500 text-center md:text-left">
          {{ section.description }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CurrencyCode, PriceItem, PricesSection } from "../../types/page";
import { isWhatsappLink } from "../../utils/links";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";

const props = defineProps<{ section: PricesSection; ctaLink?: string }>();
const ctaLink = props.ctaLink || "#";

const defaultAccent = "#0ea5e9";
const headingDefaults = getSectionHeadingDefaults("prices");
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
const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const highlightShadow = computed(() => toRgba(accent.value, 0.45));
const highlightCardStyle = computed(() => ({
  background: accent.value,
  color: "#fff",
  boxShadow: `0 25px 60px -30px ${highlightShadow.value}`
}));
const badgeStyle = (highlight: boolean) =>
  highlight
    ? { background: "#ffffff", color: accent.value, borderColor: "#ffffff" }
    : { background: toRgba(accent.value, 0.12), color: accent.value, borderColor: toRgba(accent.value, 0.4) };

const currencyMap: Record<CurrencyCode, { locale: string; currency: CurrencyCode }> = {
  BRL: { locale: "pt-BR", currency: "BRL" },
  USD: { locale: "en-US", currency: "USD" },
  EUR: { locale: "de-DE", currency: "EUR" },
  ARS: { locale: "es-AR", currency: "ARS" }
};
const defaultCurrency = currencyMap.BRL;
const formatPrice = (price: number, currency?: PriceItem["currency"]) => {
  const config = currencyMap[(currency as CurrencyCode) || "BRL"] || defaultCurrency;
  try {
    return new Intl.NumberFormat(config.locale, { style: "currency", currency: config.currency }).format(price);
  } catch {
    return `R$ ${price.toLocaleString("pt-BR")}`;
  }
};
const ctaTrackType = computed(() => (isWhatsappLink(ctaLink) ? "whatsapp" : "cta"));
</script>

