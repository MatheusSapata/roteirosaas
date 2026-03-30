<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6">
        <div class="text-center">
          <div class="flex justify-center">
            <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accent" />
          </div>
          <h1 class="mt-3 text-3xl font-bold md:text-4xl" :style="{ color: primaryText }">{{ title }}</h1>
          <p v-if="subtitle" class="text-sm" :style="{ color: mutedText }">{{ subtitle }}</p>
        </div>

        <!-- Accordion layout -->
        <div v-if="section.layout === 'accordion' || !section.layout" class="space-y-3">
          <details
            v-for="(item, index) in section.items || []"
            :key="index"
            class="group rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
            :style="{ borderColor: accentSoft }"
          >
            <summary class="cursor-pointer text-sm font-semibold text-slate-900">{{ questionText(item) }}</summary>
            <div class="mt-2 text-sm leading-relaxed text-slate-600 faq-answer" v-html="formatAnswer(item.answer)"></div>
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
              <p class="text-sm font-semibold text-slate-900">{{ questionText(item) }}</p>
              <div class="text-sm leading-relaxed text-slate-600 faq-answer" v-html="formatAnswer(item.answer)"></div>
            </div>
          </div>
          <div class="space-y-3">
            <div
              v-for="(item, index) in rightItems"
              :key="'right-' + index"
              class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              :style="{ borderColor: accentSoft }"
            >
              <p class="text-sm font-semibold text-slate-900">{{ questionText(item) }}</p>
              <div class="text-sm leading-relaxed text-slate-600 faq-answer" v-html="formatAnswer(item.answer)"></div>
            </div>
          </div>
        </div>

        <!-- Compact layout -->
        <div v-else class="grid gap-3 md:grid-cols-2">
          <div
            v-for="(item, index) in section.items || []"
            :key="index"
            class="rounded-xl border border-slate-100 bg-white/90 p-3 shadow-sm"
            :style="{ borderColor: accentSoft }"
          >
            <p class="text-sm font-semibold text-slate-900">{{ questionText(item) }}</p>
            <div class="text-sm leading-relaxed text-slate-600 faq-answer" v-html="formatAnswer(item.answer)"></div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject, isRef } from "vue";
import type { FaqItem, FaqSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette } from "../../utils/colorContrast";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: FaqSection }>();
const headingDefaults = getSectionHeadingDefaults("faq");
const defaultTitle = { pt: "Perguntas frequentes", es: "Preguntas frecuentes" };
const defaultSubtitle = { pt: "As dúvidas mais comuns sobre o roteiro.", es: "Las dudas más comunes sobre el itinerario." };
const branding = inject(PUBLIC_BRANDING_KEY, null);
const currentLanguage = getCurrentLanguage();
const localize = createLocalizer(currentLanguage);

const brandingPrimary = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;
  if (typeof data === "object" && data) {
    const color = (data as Record<string, any>).primary_color;
    if (typeof color === "string" && color.trim()) return color.trim();
  }
  return "";
});

const middle = computed(() => Math.ceil((props.section.items?.length || 0) / 2));
const leftItems = computed(() => props.section.items?.slice(0, middle.value) || []);
const rightItems = computed(() => props.section.items?.slice(middle.value) || []);

const defaultAccent = "#41ce5f";
const isLight = (hex?: string) => {
  if (!hex) return true;
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return true;
  const r = parseInt(full.substring(0, 2), 16) / 255;
  const g = parseInt(full.substring(2, 4), 16) / 255;
  const b = parseInt(full.substring(4, 6), 16) / 255;
  const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
  return luminance > 0.85;
};

const accent = computed(() => props.section.ctaColor?.trim() || brandingPrimary.value || defaultAccent);
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
const headingLabel = computed(() => {
  const override = localize(props.section.headingLabel);
  if (override.trim().length) return override;
  const fallback = headingDefaults.label;
  return typeof fallback === "string" ? fallback : localize(fallback);
});
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const title = computed(() => {
  const text = localize(props.section.title);
  return text.trim().length ? text : localize(defaultTitle);
});
const subtitle = computed(() => {
  const text = localize(props.section.subtitle);
  return text.trim().length ? text : localize(defaultSubtitle);
});
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);

const formatAnswer = (value?: any) => {
  const sanitized = sanitizeHtml(localize(value));
  return sanitized || "";
};
const questionText = (item: FaqItem) => localize(item.question);
</script>




