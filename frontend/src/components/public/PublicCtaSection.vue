<template>
  <section class="w-full" :id="section.anchorId || undefined">
    <div class="relative w-full">
      <div class="absolute inset-0" :style="bgImageStyle"></div>

      <div
        class="relative mx-auto flex min-h-[300px] w-full max-w-6xl flex-col items-center justify-center px-6 py-12 text-center"
        :style="{ color: textColor }"
      >
        <div class="flex justify-center">
          <SectionHeadingChip
            :text="headingLabel"
            :styleType="headingStyle"
            :accent="headingAccent"
          />
        </div>

        <p class="text-2xl font-bold md:text-3xl" :style="{ color: titleColor }">
          {{ section.label }}
        </p>

        <div
          v-if="descriptionHtml"
          class="mt-2 text-sm md:text-base"
          :style="{ color: descriptionColor }"
          v-html="descriptionHtml"
        ></div>

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
  </section>
</template>

<script setup lang="ts">
import { computed, inject, isRef } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import type { CtaSection } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";

const props = defineProps<{ section: CtaSection }>();
const headingDefaults = getSectionHeadingDefaults("cta");

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

const normalizeColor = (value?: string | null) =>
  typeof value === "string" ? value.trim() : "";

const sectionBackground = computed(
  () => normalizeColor(props.section.backgroundColor) || brandingPrimary.value || "#41ce5f"
);

const highlightActive = computed(() => !!props.section.highlight);

const highlightColor = computed(
  () =>
    normalizeColor(props.section.highlightColor) ||
    normalizeColor(props.section.ctaColor) ||
    sectionBackground.value
);

const backgroundImage = computed(() => resolveMediaUrl(props.section.backgroundImage));

const useImageBackground = computed(() => !highlightActive.value && !!backgroundImage.value);

/**
 * Cor sólida REAL usada no CTA.
 * Se o destaque estiver ativo, vale o highlightColor.
 * Senão, vale o backgroundColor/cor principal.
 */
const renderedSolidBackground = computed(() =>
  highlightActive.value ? highlightColor.value : sectionBackground.value
);

const parseHexColor = (color?: string | null) => {
  if (!color || typeof color !== "string") return null;

  const normalized = color.trim();
  if (!normalized.startsWith("#")) return null;

  const hex = normalized.slice(1);
  const full = hex.length === 3 ? hex.split("").map((c) => c + c).join("") : hex;

  if (full.length !== 6) return null;

  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);

  if ([r, g, b].some((value) => Number.isNaN(value))) return null;

  return { r, g, b };
};

const getLuminance = (color?: string | null) => {
  const rgb = parseHexColor(color);
  if (!rgb) return null;

  return (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
};

const getContrastTextColor = (color?: string | null) => {
  const luminance = getLuminance(color);
  if (luminance === null) return "#ffffff";
  return luminance > 0.6 ? "#111827" : "#ffffff";
};

const baseTextColor = computed(() => {
  if (useImageBackground.value) return "#ffffff";
  return props.section.textColor || getContrastTextColor(renderedSolidBackground.value);
});

/**
 * TÍTULO sempre segue a luminância real do fundo renderizado.
 * Não depende de props.section.textColor.
 */
const titleColor = computed(() => {
  if (useImageBackground.value) return "#ffffff";
  return getContrastTextColor(renderedSolidBackground.value);
});

const textColor = computed(() => baseTextColor.value);

const descriptionColor = computed(() => {
  if (useImageBackground.value) return "rgba(255,255,255,0.86)";

  const luminance = getLuminance(renderedSolidBackground.value);

  if (luminance === null) return "rgba(255,255,255,0.82)";

  return luminance > 0.6 ? "rgba(15,23,42,0.72)" : "rgba(255,255,255,0.82)";
});

const ctaMode = computed(() => props.section.ctaMode || "link");

const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId
    ? `#${props.section.ctaSectionId}`
    : props.section.link || "#"
);

const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.link
);

const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);

const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);

const headingAccent = computed(() => {
  if (useImageBackground.value) return "rgba(255,255,255,0.92)";

  const luminance = getLuminance(renderedSolidBackground.value);

  if (luminance === null) return "#0f172a";

  return luminance > 0.6 ? "#0f172a" : "rgba(255,255,255,0.92)";
});

const buttonColor = computed(() => "#ffffff");
const buttonTextColor = computed(() => "#0f172a");

const buttonLabel = computed(() => props.section.ctaText || "Saiba mais");
const descriptionHtml = computed(() => sanitizeHtml(props.section.description));

const ctaTrackType = computed(() =>
  ctaMode.value === "section"
    ? "cta"
    : isWhatsappLink(props.section.link || undefined)
      ? "whatsapp"
      : "cta"
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
          background: sectionBackground.value
        }
);
</script>