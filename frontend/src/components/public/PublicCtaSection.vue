<template>
  <section class="w-full" :style="outerStyle" :id="section.anchorId || undefined">
    <!-- Layout simples full width -->
    <div v-if="section.layout === 'simple'" class="relative w-full">
      <div class="absolute inset-0" :style="bgImageStyle"></div>
      <div class="relative mx-auto flex min-h-[300px] w-full max-w-6xl flex-col items-center justify-center px-6 py-12 text-center" :style="{ color: textColor }">
        <div class="flex justify-center">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
        </div>
        <p class="text-2xl font-bold md:text-3xl">{{ section.label }}</p>
        <div class="mt-2 text-sm md:text-base" v-if="descriptionHtml" v-html="descriptionHtml"></div>
        <div class="mt-5 flex justify-center" v-if="ctaHasTarget">
          <a
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            data-track-event="cta"
            rel="noopener"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: buttonColor, color: buttonTextColor }"
          >
            {{ buttonLabel }}
          </a>
        </div>
      </div>
    </div>

    <!-- Demais layouts dentro de container -->
    <div v-else class="mx-auto max-w-6xl px-6 py-12">
      <div
        :class="[
          'rounded-3xl p-6 shadow-[0_16px_50px_-30px_rgba(15,23,42,0.55)]',
          highlightActive ? 'ring-1 ring-white/30 bg-transparent' : 'bg-white/90 ring-1 ring-slate-100'
        ]"
        :style="cardWrapperStyle"
      >
        <!-- Barra -->
        <div
          v-if="section.layout === 'bar' || !section.layout"
          :class="[
            'flex flex-col gap-4 rounded-2xl border px-5 py-4 shadow-lg md:flex-row md:items-center md:justify-between',
            highlightActive ? 'border-white/40 bg-transparent' : 'border-slate-100 bg-white/90'
          ]"
          :style="{ borderColor: highlightBorderColor }"
        >
          <div class="space-y-1 text-center" :style="{ color: textColor }">
            <div class="flex justify-center">
              <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
            </div>
            <p class="text-lg font-semibold" :style="{ color: textColor }">{{ section.label }}</p>
            <div class="text-sm" :style="{ color: textColor }" v-if="descriptionHtml" v-html="descriptionHtml"></div>
          </div>
          <a
            v-if="ctaHasTarget"
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            data-track-event="cta"
            rel="noopener"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: buttonColor, color: buttonTextColor }"
          >
            {{ buttonLabel }}
          </a>
        </div>

        <!-- Split -->
        <div
          v-else-if="section.layout === 'split'"
          :class="[
            'grid gap-4 rounded-2xl border p-6 shadow-xl md:grid-cols-2',
            highlightActive ? 'border-white/40 bg-transparent' : 'border-slate-100 bg-white/95'
          ]"
          :style="{ borderColor: highlightBorderColor }"
        >
          <div class="space-y-2 text-center" :style="{ color: textColor }">
            <div class="flex justify-center">
              <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
            </div>
            <p class="text-2xl font-bold" :style="{ color: textColor }">{{ section.label }}</p>
            <div class="text-sm" :style="{ color: textColor }" v-if="descriptionHtml" v-html="descriptionHtml"></div>
          </div>
          <div class="flex items-center justify-end">
          <a
            v-if="ctaHasTarget"
            :href="ctaHref"
            :data-scroll-target="ctaIsScroll ? 'true' : null"
            target="_blank"
            data-track-event="cta"
            rel="noopener"
            :data-track-type="ctaTrackType"
            class="inline-flex items-center justify-center rounded-lg px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            :style="{ background: buttonColor, color: buttonTextColor }"
          >
            {{ buttonLabel }}
          </a>
          </div>
        </div>

        <!-- Card -->
        <div
          v-else
          :class="[
            'relative overflow-hidden rounded-3xl border p-6 shadow-2xl',
            highlightActive ? 'border-white/40 bg-transparent' : 'border-slate-100 bg-white/95'
          ]"
          :style="{ borderColor: highlightBorderColor }"
        >
          <div v-if="!highlightActive" class="absolute inset-0 bg-gradient-to-br from-white via-white to-transparent"></div>
          <div class="relative space-y-3 text-center" :style="{ color: textColor }">
            <div class="flex justify-center">
              <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
            </div>
            <p class="text-2xl font-bold" :style="{ color: textColor }">{{ section.label }}</p>
            <div class="text-sm" :style="{ color: textColor }" v-if="descriptionHtml" v-html="descriptionHtml"></div>
            <a
              v-if="ctaHasTarget"
              :href="ctaHref"
              :data-scroll-target="ctaIsScroll ? 'true' : null"
              target="_blank"
              data-track-event="cta"
              rel="noopener"
              :data-track-type="ctaTrackType"
              class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
              :style="{ background: buttonColor, color: buttonTextColor }"
            >
              {{ buttonLabel }}
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import type { CtaSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";

const props = defineProps<{ section: CtaSection }>();
const headingDefaults = getSectionHeadingDefaults("cta");

const accent = computed(() => props.section.backgroundColor || "#41ce5f");
const highlightActive = computed(() => !!props.section.highlight);
const highlightColor = computed(() => props.section.highlightColor || props.section.ctaColor || accent.value);
const buttonColor = computed(() => (highlightActive.value ? "#ffffff" : props.section.ctaColor || accent.value));
const buttonTextColor = computed(() => (highlightActive.value ? "#0f172a" : "#ffffff"));
const textColor = computed(() =>
  highlightActive.value ? "#ffffff" : props.section.textColor || (props.section.layout === "simple" ? "#ffffff" : "#0f172a")
);
const outerStyle = computed(() => (props.section.layout === "simple" ? {} : { background: accentSoftBg.value }));
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.link || "#"
);
const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.link
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const headingAccent = computed(() => (highlightActive.value ? "#ffffff" : buttonColor.value));
const buttonLabel = computed(() =>
  props.section.ctaText || (props.section.layout === "simple" ? "Saiba mais" : "Falar com especialista")
);
const descriptionHtml = computed(() => sanitizeHtml(props.section.description));

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(14,165,233,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const accentBorder = computed(() => toRgba(accent.value, 0.25));
const highlightBorderColor = computed(() => (highlightActive.value ? "rgba(255,255,255,0.4)" : accentBorder.value));
const cardWrapperStyle = computed(() => (highlightActive.value ? { background: highlightColor.value } : {}));
const accentSoftBg = computed(() => props.section.backgroundColor || `linear-gradient(135deg, ${toRgba(accent.value, 0.08)}, rgba(255,255,255,0.95))`);
const backgroundImage = computed(() => resolveMediaUrl(props.section.backgroundImage));
const ctaTrackType = computed(() =>
  ctaMode.value === "section" ? "cta" : isWhatsappLink(props.section.link || undefined) ? "whatsapp" : "cta"
);
const bgImageStyle = computed(() =>
  highlightActive.value
    ? { background: highlightColor.value }
    : backgroundImage.value
      ? {
          backgroundImage: `linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0.35)), url(${backgroundImage.value})`,
          backgroundSize: "cover",
          backgroundPosition: "center"
        }
      : {
          background: props.section.backgroundColor || accent.value
        }
);
</script>
