<template>
<section class="w-full" :id="section.anchorId || undefined" :style="sectionStyle">
  <div
    class="mx-auto w-full space-y-6 pb-[30px]"
    :class="section.fullWidth ? 'max-w-none px-0 md:px-0' : 'max-w-6xl px-4 md:px-0'"
  >
      <div
        v-if="hasImage"
        class="relative bg-slate-900"
        :class="imageWrapperClass"
      >
        <img
          :src="imageUrl"
          :alt="imageAltText"
          :class="[imageHeightClass, 'w-full', imageFitClass]"
          :style="imageStyle"
        />
      <div class="absolute inset-0" :style="{ backgroundColor: overlayColor }"></div>
      <div class="absolute inset-0 flex items-center justify-center px-6 text-center">
        <h1
          v-if="displayTitle"
          class="text-center text-4xl font-black uppercase tracking-[0.2em] leading-none drop-shadow-2xl md:text-6xl"
          :style="{ color: titleColor, fontSize: titleSize }"
        >
          {{ displayTitle }}
        </h1>
        </div>
      </div>

      <div
        class="mx-auto max-w-4xl px-6 text-base leading-relaxed md:px-6 md:text-lg"
        :style="bodyTextStyle"
        v-html="textHtml"
      ></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { getReadableTextColor, getRelativeLuminance, normalizeHexColor } from "../../utils/colorContrast";
import type { BiographySection } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: BiographySection; previewDevice?: "desktop" | "mobile" }>();
const isMobileViewport = ref(false);
const localize = createLocalizer(getCurrentLanguage());
const biographyCopy = {
  defaultAlt: { pt: "Biografia", es: "Biografía" }
} as const;
const detectViewport = () => {
  if (typeof window === "undefined") return;
  isMobileViewport.value = window.innerWidth <= 640;
};
onMounted(() => {
  detectViewport();
  if (typeof window !== "undefined") {
    window.addEventListener("resize", detectViewport);
  }
});
onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", detectViewport);
  }
});

const isPreview = computed(() => Boolean(props.previewDevice));
const isMobilePreviewDevice = computed(() => props.previewDevice === "mobile");
const isMobileView = computed(() => isMobileViewport.value || isMobilePreviewDevice.value);
const hasImage = computed(() =>
  Boolean(
    (props.section.image && (props.section.image as string).trim()) ||
      (props.section.mobileImage && (props.section.mobileImage as string).trim())
  )
);
const desktopImageUrl = computed(() =>
  props.section.image && String(props.section.image).trim() ? resolveMediaUrl(props.section.image as string) : ""
);
const mobileImageUrl = computed(() =>
  props.section.mobileImage && String(props.section.mobileImage).trim()
    ? resolveMediaUrl(props.section.mobileImage as string)
    : ""
);
const imageUrl = computed(() => {
  if (isMobileView.value && mobileImageUrl.value) {
    return mobileImageUrl.value;
  }
  return desktopImageUrl.value || mobileImageUrl.value || "";
});
const usingMobileImage = computed(() => Boolean(mobileImageUrl.value && imageUrl.value === mobileImageUrl.value));
const imageWrapperClass = computed(() => {
  if (props.section.fullWidth && !isPreview.value) {
    return "w-full";
  }
  return "w-full";
});
const imageFitClass = computed(() => "object-cover");
const imageHeightClass = computed(() => {
  if (usingMobileImage.value) {
    return "h-auto";
  }
  return props.section.fullWidth ? "h-[260px] sm:h-[320px] md:h-[480px]" : "h-[300px] sm:h-[360px] md:h-[480px]";
});
const imageStyle = computed(() => (usingMobileImage.value ? { aspectRatio: "2 / 1" } : {}));
const overlayColor = computed(() => {
  const value = typeof props.section.overlayOpacity === "number" ? props.section.overlayOpacity : 0.45;
  const safe = Math.min(Math.max(value, 0), 0.9);
  return `rgba(0,0,0,${safe})`;
});
const displayTitle = computed(() => localize(props.section.title).trim());
const titleColor = computed(() => props.section.titleColor || "#ffffff");
const DEFAULT_BODY_TEXT_COLOR = "#0f172a";
const sectionStyle = computed(() => {
  if (!props.section.backgroundColor) return undefined;
  return { backgroundColor: props.section.backgroundColor };
});
const normalizedBackgroundColor = computed(() => normalizeHexColor(props.section.backgroundColor));
const rawBodyColor = computed(() => (typeof props.section.textColor === "string" ? props.section.textColor.trim() : ""));
const normalizedBodyColor = computed(() => normalizeHexColor(rawBodyColor.value));
const contrastRatio = (a: number, b: number) => {
  const light = Math.max(a, b);
  const dark = Math.min(a, b);
  return (light + 0.05) / (dark + 0.05);
};
const bodyColor = computed(() => {
  if (!normalizedBackgroundColor.value) {
    return rawBodyColor.value || DEFAULT_BODY_TEXT_COLOR;
  }

  const readable = getReadableTextColor(normalizedBackgroundColor.value);
  if (!rawBodyColor.value) return readable;
  if (!normalizedBodyColor.value) return rawBodyColor.value;

  const ratio = contrastRatio(
    getRelativeLuminance(normalizedBodyColor.value),
    getRelativeLuminance(normalizedBackgroundColor.value)
  );
  if (normalizedBodyColor.value === DEFAULT_BODY_TEXT_COLOR || ratio < 4.5) {
    return readable;
  }
  return rawBodyColor.value;
});
const bodyTextStyle = computed(() => {
  const configuredSize = props.section.textFontSize;
  const style: Record<string, string> = { color: bodyColor.value };
  if (typeof configuredSize === "number" && configuredSize !== 18) {
    style.fontSize = `${configuredSize}px`;
  }
  return style;
});
const titleSize = computed(() => {
  const base = props.section.titleFontSize ?? 72;
  const limited = isMobileView.value ? Math.min(base, 40) : base;
  return `${limited}px`;
});
const textHtml = computed(() => sanitizeHtml(localize(props.section.text)));
const imageAltText = computed(() => {
  const customAlt = localize(props.section.title).trim();
  if (customAlt.length) return customAlt;
  return localize(biographyCopy.defaultAlt);
});
</script>
