<template>
  <section class="w-full" :style="{ background: sectionBackground }" :id="section.anchorId || undefined">
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
        <div v-if="section.layout === 'accordion' || !section.layout" class="mx-auto max-w-3xl space-y-3">
          <details
            v-for="(item, index) in section.items || []"
            :key="index"
            class="group rounded-2xl p-4 transition hover:-translate-y-0.5"
            :style="faqCardStyle"
          >
            <summary class="faq-summary cursor-pointer" :style="{ color: faqQuestionColor }">
              <span class="flex min-w-0 items-center gap-3">
                <span class="mx-[4px] h-2 w-2 flex-shrink-0 rounded-full" :style="{ background: accent }"></span>
                <span class="min-w-0 text-[20px] font-semibold leading-tight">{{ questionText(item) }}</span>
              </span>
              <span class="faq-summary-icon" :style="{ color: accent }" aria-hidden="true">
                <svg viewBox="0 0 20 20" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m6 8 4 4 4-4" />
                </svg>
              </span>
            </summary>
            <div class="mt-2 text-sm leading-relaxed faq-answer" :style="{ color: faqAnswerColor }" v-html="formatAnswer(item.answer)"></div>
          </details>
        </div>

        <!-- Split layout -->
        <div v-else-if="section.layout === 'split'" class="grid gap-4 md:grid-cols-2">
          <div class="space-y-3">
            <div
              v-for="(item, index) in leftItems"
              :key="'left-' + index"
              class="rounded-2xl p-4"
              :style="faqCardStyle"
            >
              <p class="text-[20px] font-semibold leading-tight" :style="{ color: faqQuestionColor }">{{ questionText(item) }}</p>
              <div class="text-sm leading-relaxed faq-answer" :style="{ color: faqAnswerColor }" v-html="formatAnswer(item.answer)"></div>
            </div>
          </div>
          <div class="space-y-3">
            <div
              v-for="(item, index) in rightItems"
              :key="'right-' + index"
              class="rounded-2xl p-4"
              :style="faqCardStyle"
            >
              <p class="text-[20px] font-semibold leading-tight" :style="{ color: faqQuestionColor }">{{ questionText(item) }}</p>
              <div class="text-sm leading-relaxed faq-answer" :style="{ color: faqAnswerColor }" v-html="formatAnswer(item.answer)"></div>
            </div>
          </div>
        </div>

        <!-- Compact layout -->
        <div v-else class="grid gap-3 md:grid-cols-2">
          <div
            v-for="(item, index) in section.items || []"
            :key="index"
            class="rounded-xl p-3"
            :style="faqCardStyle"
          >
            <p class="text-[20px] font-semibold leading-tight" :style="{ color: faqQuestionColor }">{{ questionText(item) }}</p>
            <div class="text-sm leading-relaxed faq-answer" :style="{ color: faqAnswerColor }" v-html="formatAnswer(item.answer)"></div>
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
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette, getRelativeLuminance, normalizeHexColor } from "../../utils/colorContrast";
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
const brandingThemeAccent = computed(() => {
  if (!branding) return "";
  const data = isRef(branding) ? branding.value : branding;
  if (typeof data === "object" && data) {
    const theme = (data as Record<string, any>).theme;
    const color = theme && typeof theme.ctaDefaultColor === "string" ? theme.ctaDefaultColor : "";
    if (typeof color === "string" && color.trim()) return color.trim();
  }
  return "";
});

const middle = computed(() => Math.ceil((props.section.items?.length || 0) / 2));
const leftItems = computed(() => props.section.items?.slice(0, middle.value) || []);
const rightItems = computed(() => props.section.items?.slice(middle.value) || []);

const defaultAccent = "#41ce5f";
const accent = computed(() => brandingThemeAccent.value || brandingPrimary.value || props.section.ctaColor?.trim() || defaultAccent);
const sectionBackground = computed(() => props.section.backgroundColor || "linear-gradient(180deg,#f8fafc,#fff)");
const sectionBackgroundHex = computed(() => normalizeHexColor(props.section.backgroundColor));
const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const headingLabel = computed(() =>
  resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize)
);
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
const sectionBackgroundIsLight = computed(() => {
  if (!sectionBackgroundHex.value) return !textPalette.value.isLight;
  return getRelativeLuminance(sectionBackgroundHex.value) > 0.7;
});
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
const neutralShadow = "0 18px 38px -28px rgba(15,23,42,0.28)";
const darkCardBorder = computed(() => `1px solid ${toRgba(accent.value, 0.42)}`);
const accentShadow = computed(() => toRgba(accent.value, 0.35));
const faqCardStyle = computed(() => ({
  background: sectionBackgroundIsLight.value ? "#ffffff" : "rgba(255,255,255,0.10)",
  border: sectionBackgroundIsLight.value ? "none" : darkCardBorder.value,
  boxShadow: sectionBackgroundIsLight.value ? neutralShadow : `0 22px 46px -30px ${accentShadow.value}`
}));
const faqQuestionColor = computed(() => (sectionBackgroundIsLight.value ? "#0f172a" : "#f8fafc"));
const faqAnswerColor = computed(() => (sectionBackgroundIsLight.value ? "#475569" : "rgba(241,245,249,0.82)"));

const formatAnswer = (value?: any) => {
  const sanitized = sanitizeHtml(localize(value));
  return sanitized || "";
};
const questionText = (item: FaqItem) => localize(item.question);
</script>

<style scoped>
.faq-answer {
  overflow: hidden;
}

.faq-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

details > summary {
  list-style: none;
}

details > summary::-webkit-details-marker {
  display: none;
}

.faq-summary-icon {
  display: inline-flex;
  flex-shrink: 0;
  transition: transform 0.28s ease;
}

details[open] .faq-summary-icon {
  transform: rotate(180deg);
}

details[open] .faq-answer {
  animation: faq-expand 0.42s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes faq-expand {
  0% {
    opacity: 0;
    transform: translateY(-6px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>




