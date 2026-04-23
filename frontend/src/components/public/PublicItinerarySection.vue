<template>
  <section class="w-full" :style="{ background: sectionBackground }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="space-y-6">
        <div class="flex items-start justify-center">
          <div class="text-center">
            <div class="mb-2 flex justify-center">
              <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accent" />
            </div>
            <h1 class="text-3xl font-bold md:text-4xl" :style="{ color: primaryText }">{{ titleText }}</h1>
            <p v-if="subtitleText" class="text-sm" :style="{ color: mutedText }">{{ subtitleText }}</p>
          </div>
        </div>

        <!-- Timeline layout -->
        <div v-if="section.layout === 'timeline' || !section.layout" class="mt-8 flex flex-col items-center gap-4">
          <div
            v-for="(day, index) in days"
            :key="index"
            class="group w-full max-w-3xl rounded-2xl p-4 text-left transition hover:-translate-y-0.5"
            :style="dayCardStyle"
          >
            <button class="flex w-full items-center gap-[14px] text-left" @click="toggleDay(index)">
              <div
                class="mx-[4px] flex h-10 w-10 items-center justify-center rounded-full border text-sm font-semibold"
                :style="dayBadgeStyle"
              >
                {{ index + 1 }}
              </div>
              <div class="flex flex-1 flex-col justify-center">
                <p class="text-xs font-semibold uppercase tracking-wide" :style="{ color: accent }">{{ dayLabel(day, index) }}</p>
                <p class="text-[22px] font-bold leading-tight" :style="{ color: cardTitleColor }">{{ dayTitle(day, index) }}</p>
                <p class="mt-0.5 min-h-[16px] text-xs" :class="expanded[index] ? 'invisible' : ''" :style="{ color: cardHintColor }">{{ expandHint }}</p>
              </div>
              <span class="itinerary-summary-icon" :style="{ color: accent }" aria-hidden="true">
                <svg viewBox="0 0 20 20" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ 'rotate-180': expanded[index] }">
                  <path d="m6 8 4 4 4-4" />
                </svg>
              </span>
            </button>
            <transition name="itinerary-expand">
              <div v-if="expanded[index]" class="mt-2 space-y-3 overflow-hidden">
                <div
                  v-if="dayDescriptionHtml(day.description)"
                  class="text-sm leading-relaxed"
                  :style="{ color: cardBodyColor }"
                  v-html="dayDescriptionHtml(day.description)"
                ></div>
                <img
                  v-if="resolveDayImage(day.image)"
                  :src="resolveDayImage(day.image)"
                  :alt="dayImageAlt"
                  class="itinerary-expand-image block w-full rounded-2xl object-contain"
                />
              </div>
            </transition>
          </div>
        </div>

        <!-- Steps layout -->
        <div v-else-if="section.layout === 'steps'" class="space-y-6">
          <div class="relative">
            <div class="absolute left-0 right-0 top-[22px] h-0.5 bg-slate-200"></div>
            <div class="flex flex-wrap items-start justify-around gap-6">
              <button
                v-for="(day, index) in days"
                :key="'step-' + index"
                class="relative flex flex-col items-center gap-2 bg-transparent text-left"
                @click="toggleStep(index)"
              >
                <div
                class="mx-[4px] flex h-12 w-12 items-center justify-center rounded-full border-2 text-sm font-semibold"
                  :style="dayBadgeStyle"
                >
                  {{ index + 1 }}
                </div>
                <span class="rounded-full px-3 py-1 text-xs font-semibold" :style="stepChipStyle">
                  {{ dayLabel(day, index) }}
                </span>
              </button>
            </div>
          </div>
          <div v-if="activeStep !== null" class="rounded-2xl p-5" :style="dayCardStyle">
            <p class="text-xs uppercase tracking-wide" :style="{ color: cardHintColor }">{{ stepLabel }} {{ (activeStep || 0) + 1 }}</p>
            <h3 class="mt-2 text-[22px] font-bold leading-tight" :style="{ color: cardTitleColor }">{{ dayTitle(days[activeStep], activeStep || 0) }}</h3>
            <div
              v-if="dayDescriptionHtml(days[activeStep]?.description)"
              class="mt-2 text-sm leading-relaxed"
              :style="{ color: cardBodyColor }"
              v-html="dayDescriptionHtml(days[activeStep]?.description)"
            ></div>
            <img
              v-if="resolveDayImage(days[activeStep]?.image)"
              :src="resolveDayImage(days[activeStep]?.image)"
              :alt="stepImageAlt"
              class="mt-3 block w-full rounded-2xl object-contain"
            />
          </div>
        </div>

        <!-- Cards layout -->
        <div v-else-if="section.layout === 'cards'" :class="['grid gap-4', section.fullWidth ? 'md:grid-cols-3' : 'md:grid-cols-2']">
          <div
            v-for="(day, index) in days"
            :key="index"
            class="rounded-2xl p-4 transition hover:-translate-y-0.5"
            :style="dayCardStyle"
          >
            <p class="text-sm font-semibold" :style="{ color: accent }">{{ dayPrefixText }} {{ index + 1 }} • {{ dayLabel(day, index) }}</p>
            <p class="text-[22px] font-bold leading-tight" :style="{ color: cardTitleColor }">{{ dayTitle(day, index) }}</p>
            <div
              v-if="dayDescriptionHtml(day.description)"
              class="text-sm leading-relaxed"
              :style="{ color: cardBodyColor }"
              v-html="dayDescriptionHtml(day.description)"
            ></div>
            <img
              v-if="resolveDayImage(day.image)"
              :src="resolveDayImage(day.image)"
              :alt="dayImageAlt"
              class="mt-3 block w-full rounded-2xl object-contain"
            />
          </div>
        </div>

        <!-- Minimal layout -->
        <div v-else class="space-y-3">
          <div
            v-for="(day, index) in days"
            :key="index"
            class="rounded-xl p-4"
            :style="dayCardStyle"
          >
            <p class="text-sm font-semibold" :style="{ color: accent }">{{ dayPrefixText }} {{ index + 1 }} • {{ dayLabel(day, index) }}</p>
            <p class="text-[22px] font-bold leading-tight" :style="{ color: cardTitleColor }">{{ dayTitle(day, index) }}</p>
            <div
              v-if="dayDescriptionHtml(day.description)"
              class="text-sm leading-relaxed"
              :style="{ color: cardBodyColor }"
              v-html="dayDescriptionHtml(day.description)"
            ></div>
            <img
              v-if="resolveDayImage(day.image)"
              :src="resolveDayImage(day.image)"
              :alt="dayImageAlt"
              class="mt-3 block w-full rounded-2xl object-contain"
            />
          </div>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup lang="ts">
import { computed, inject, isRef, ref, watch } from "vue";
import type { ItineraryDay, ItinerarySection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { resolveMediaUrl } from "../../utils/media";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette, getRelativeLuminance, normalizeHexColor } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: ItinerarySection }>();
const localize = createLocalizer(getCurrentLanguage());
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
const headingDefaults = getSectionHeadingDefaults("itinerary");
const defaultAccent = "#41ce5f";
const itineraryCopy = {
  defaultTitle: { pt: "Dia a dia", es: "Día a día" },
  defaultSubtitle: { pt: "Visão clara do roteiro completo.", es: "Visión clara del itinerario completo." },
  dayPrefix: { pt: "Dia", es: "Día" },
  stepPrefix: { pt: "Passo", es: "Paso" },
  expandHint: { pt: "Clique para ver detalhes", es: "Haz clic para ver detalles" },
  dayImageAlt: { pt: "Imagem do dia", es: "Imagen del día" },
  stepImageAlt: { pt: "Imagem do passo", es: "Imagen del paso" }
} as const;

const accent = computed(() => props.section.ctaColor || brandingPrimary.value || defaultAccent);
const sectionBackground = computed(() => props.section.backgroundColor || "linear-gradient(180deg,#f8fafc,#fff)");
const sectionBackgroundHex = computed(() => normalizeHexColor(props.section.backgroundColor));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const sectionBackgroundIsLight = computed(() => {
  if (!sectionBackgroundHex.value) return !textPalette.value.isLight;
  return getRelativeLuminance(sectionBackgroundHex.value) > 0.7;
});
const days = computed(() => props.section.days || []);
const titleText = computed(() => {
  const text = localize(props.section.title).trim();
  return text.length ? text : localize(itineraryCopy.defaultTitle);
});
const subtitleText = computed(() => {
  const raw = props.section.subtitle;
  if (raw === null || typeof raw === "undefined") return localize(itineraryCopy.defaultSubtitle);
  const text = localize(raw).trim();
  return text;
});
const headingLabel = computed(() =>
  resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize)
);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);
const expandHint = computed(() => localize(itineraryCopy.expandHint));
const dayDescriptionHtml = (text?: any) => sanitizeHtml(localize(text));
const resolveDayImage = (image?: string) => {
  if (!image) return "";
  return resolveMediaUrl(image);
};
const expanded = ref<boolean[]>(days.value.map(() => false));
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

const accentShadow = computed(() => toRgba(accent.value, 0.35));
const neutralShadow = "0 18px 38px -28px rgba(15,23,42,0.28)";
const darkCardBorder = computed(() => `1px solid ${toRgba(accent.value, 0.42)}`);
const darkCardShadow = computed(() => `0 22px 46px -30px ${accentShadow.value}`);
const dayCardStyle = computed(() => ({
  background: sectionBackgroundIsLight.value ? "#ffffff" : "rgba(255,255,255,0.10)",
  border: sectionBackgroundIsLight.value ? "none" : darkCardBorder.value,
  boxShadow: sectionBackgroundIsLight.value ? neutralShadow : darkCardShadow.value
}));
const dayBadgeStyle = computed(() => ({
  borderColor: accent.value,
  color: sectionBackgroundIsLight.value ? accent.value : sectionBackgroundHex.value || "#1e3a8a",
  background: sectionBackgroundIsLight.value ? "rgba(255,255,255,0.72)" : accent.value,
  boxShadow: sectionBackgroundIsLight.value ? "none" : `0 10px 24px -18px ${accentShadow.value}`
}));
const stepChipStyle = computed(() => ({
  color: accent.value,
  border: sectionBackgroundIsLight.value ? "none" : `1px solid ${toRgba(accent.value, 0.32)}`,
  background: sectionBackgroundIsLight.value ? "rgba(255,255,255,0.68)" : toRgba(accent.value, 0.1),
  boxShadow: sectionBackgroundIsLight.value ? "0 10px 24px -22px rgba(15,23,42,0.2)" : `0 12px 28px -24px ${accentShadow.value}`
}));
const cardTitleColor = computed(() => (sectionBackgroundIsLight.value ? "#0f172a" : "#f8fafc"));
const cardBodyColor = computed(() => (sectionBackgroundIsLight.value ? "#475569" : "rgba(241,245,249,0.82)"));
const cardHintColor = computed(() => (sectionBackgroundIsLight.value ? "#94a3b8" : "rgba(241,245,249,0.6)"));
const dayImageAlt = computed(() => localize(itineraryCopy.dayImageAlt));
const stepImageAlt = computed(() => localize(itineraryCopy.stepImageAlt));
const dayPrefixText = computed(() => localize(itineraryCopy.dayPrefix));
const stepPrefixText = computed(() => localize(itineraryCopy.stepPrefix));
const stepLabel = computed(() => stepPrefixText.value);

const dayLabel = (day: ItineraryDay | undefined, index: number) => {
  const label = localize(day?.day).trim();
  if (label.length) return label;
  return `${dayPrefixText.value} ${index + 1}`;
};

const dayTitle = (day: ItineraryDay | undefined, index: number) => {
  const title = localize(day?.title).trim();
  if (title.length) return title;
  return `${dayPrefixText.value} ${index + 1}`;
};
const toggleDay = (index: number) => {
  expanded.value[index] = !expanded.value[index];
};

watch(
  days,
  newDays => {
    expanded.value = newDays.map(() => false);
    activeStep.value = null;
  },
  { deep: true }
);

const toggleStep = (index: number) => {
  activeStep.value = activeStep.value === index ? null : index;
};
</script>

<style scoped>
.itinerary-summary-icon {
  display: inline-flex;
  flex-shrink: 0;
}

.itinerary-summary-icon svg {
  transition: transform 0.28s ease;
}

.itinerary-expand-enter-active,
.itinerary-expand-leave-active {
  transition: max-height 1.5s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.55s ease, margin-top 1.5s cubic-bezier(0.22, 1, 0.36, 1);
  overflow: hidden;
}

.itinerary-expand-enter-from,
.itinerary-expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.itinerary-expand-enter-to,
.itinerary-expand-leave-from {
  max-height: 1200px;
  opacity: 1;
}

.itinerary-expand-image {
  transition: opacity 0.8s ease 0.2s, transform 0.8s ease 0.2s;
}

.itinerary-expand-enter-from .itinerary-expand-image,
.itinerary-expand-leave-to .itinerary-expand-image {
  opacity: 0;
  transform: translateY(10px) scale(0.985);
}

.itinerary-expand-enter-to .itinerary-expand-image,
.itinerary-expand-leave-from .itinerary-expand-image {
  opacity: 1;
  transform: translateY(0) scale(1);
}
</style>

