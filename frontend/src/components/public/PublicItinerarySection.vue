<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
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
            class="group w-full max-w-3xl rounded-2xl border border-slate-100 bg-white/90 p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
            :style="{ boxShadow: `0 20px 40px -30px ${accentShadow}` }"
          >
            <button class="flex w-full items-center gap-3 text-left" @click="toggleDay(index)">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-full border bg-white text-sm font-semibold transition group-hover:-translate-y-0.5"
                :style="{ borderColor: accent, color: accent }"
              >
                {{ index + 1 }}
              </div>
              <div class="flex-1">
                <p class="text-xs font-semibold uppercase tracking-wide" :style="{ color: accent }">{{ dayLabel(day, index) }}</p>
                <p class="text-lg font-semibold text-slate-900">{{ dayTitle(day, index) }}</p>
                <p v-if="!expanded[index]" class="text-xs text-slate-400 mt-0.5">{{ expandHint }}</p>
              </div>
              <span class="text-sm text-slate-500">{{ expanded[index] ? collapseSymbol : expandSymbol }}</span>
            </button>
            <div v-if="expanded[index]" class="mt-2 space-y-3">
              <div
                v-if="dayDescriptionHtml(day.description)"
                class="text-sm leading-relaxed text-slate-600"
                v-html="dayDescriptionHtml(day.description)"
              ></div>
              <img
                v-if="resolveDayImage(day.image)"
                :src="resolveDayImage(day.image)"
                :alt="dayImageAlt"
                class="h-80 w-full rounded-2xl object-cover"
              />
            </div>
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
                class="flex h-12 w-12 items-center justify-center rounded-full border-2 bg-white text-sm font-semibold shadow-sm transition hover:-translate-y-0.5"
                  :style="{ borderColor: accent.value, color: accent.value }"
                >
                  {{ index + 1 }}
                </div>
                <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold" :style="{ color: accent.value }">
                  {{ dayLabel(day, index) }}
                </span>
              </button>
            </div>
          </div>
          <div v-if="activeStep !== null" class="rounded-2xl border border-slate-100 bg-white/95 p-5 shadow-[0_20px_45px_-34px_rgba(15,23,42,0.6)]">
            <p class="text-xs uppercase tracking-wide text-slate-500">{{ stepLabel }} {{ (activeStep || 0) + 1 }}</p>
            <h3 class="mt-2 text-lg font-semibold text-slate-900">{{ dayTitle(days[activeStep], activeStep || 0) }}</h3>
            <div
              v-if="dayDescriptionHtml(days[activeStep]?.description)"
              class="mt-2 text-sm leading-relaxed text-slate-600"
              v-html="dayDescriptionHtml(days[activeStep]?.description)"
            ></div>
            <img
              v-if="resolveDayImage(days[activeStep]?.image)"
              :src="resolveDayImage(days[activeStep]?.image)"
              :alt="stepImageAlt"
              class="mt-3 h-96 w-full rounded-2xl object-cover"
            />
          </div>
        </div>

        <!-- Cards layout -->
        <div v-else-if="section.layout === 'cards'" :class="['grid gap-4', section.fullWidth ? 'md:grid-cols-3' : 'md:grid-cols-2']">
          <div
            v-for="(day, index) in days"
            :key="index"
            class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            :style="{ borderColor: accentSoft }"
          >
            <p class="text-sm font-semibold" :style="{ color: accent }">{{ dayPrefixText }} {{ index + 1 }} • {{ dayLabel(day, index) }}</p>
            <p class="text-lg font-semibold text-slate-900">{{ dayTitle(day, index) }}</p>
            <div
              v-if="dayDescriptionHtml(day.description)"
              class="text-sm leading-relaxed text-slate-600"
              v-html="dayDescriptionHtml(day.description)"
            ></div>
            <img
              v-if="resolveDayImage(day.image)"
              :src="resolveDayImage(day.image)"
              :alt="dayImageAlt"
              class="mt-3 h-72 w-full rounded-2xl object-cover"
            />
          </div>
        </div>

        <!-- Minimal layout -->
        <div v-else class="space-y-3">
          <div
            v-for="(day, index) in days"
            :key="index"
            class="rounded-xl border border-slate-100 bg-white/90 p-4 shadow-sm"
            :style="{ borderColor: accentSoft }"
          >
            <p class="text-sm font-semibold" :style="{ color: accent }">{{ dayPrefixText }} {{ index + 1 }} • {{ dayLabel(day, index) }}</p>
            <p class="text-lg font-semibold text-slate-900">{{ dayTitle(day, index) }}</p>
            <div
              v-if="dayDescriptionHtml(day.description)"
              class="text-sm leading-relaxed text-slate-600"
              v-html="dayDescriptionHtml(day.description)"
            ></div>
            <img
              v-if="resolveDayImage(day.image)"
              :src="resolveDayImage(day.image)"
              :alt="dayImageAlt"
              class="mt-3 h-72 w-full rounded-2xl object-cover"
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
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { resolveMediaUrl } from "../../utils/media";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";
import { deriveTextPalette } from "../../utils/colorContrast";
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

const accent = computed(() => props.section.ctaColor || brandingPrimary.value || defaultAccent);
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
const headingLabel = computed(() => {
  const custom = localize(props.section.headingLabel).trim();
  if (custom.length) return custom;
  return headingDefaults.label;
});
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
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

const accentSoft = computed(() => toRgba(accent.value, 0.12));
const accentShadow = computed(() => toRgba(accent.value, 0.35));
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
const collapseSymbol = "−";
const expandSymbol = "+";

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

