<template>
<section class="w-full" :id="section.anchorId || undefined">
  <div
    class="mx-auto w-full space-y-6"
    :class="section.fullWidth ? 'max-w-none px-0 md:px-0' : 'max-w-6xl px-4 md:px-0'"
  >
      <div
        v-if="hasImage"
        class="relative bg-slate-900 shadow-2xl"
        :class="imageWrapperClass"
      >
        <img
          :src="imageUrl"
          alt="Biografia"
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
        class="mx-auto max-w-4xl leading-relaxed px-4 md:px-0"
        :style="{ color: bodyColor, fontSize: textSize }"
        v-html="textHtml"
      ></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import type { BiographySection } from "../../types/page";

const props = defineProps<{ section: BiographySection; previewDevice?: "desktop" | "mobile" }>();
const isMobileViewport = ref(false);
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
    return "w-screen relative left-1/2 right-1/2 -ml-[50vw] md:left-auto md:right-auto md:ml-0";
  }
  return "w-full rounded-[36px]";
});
const imageFitClass = computed(() => (isPreview.value ? "object-contain" : "object-cover"));
const imageHeightClass = computed(() => {
  if (usingMobileImage.value) {
    return "h-auto";
  }
  return props.section.fullWidth ? "h-[260px] sm:h-[320px] md:h-[640px]" : "h-[300px] sm:h-[360px] md:h-[480px]";
});
const imageStyle = computed(() => (usingMobileImage.value ? { aspectRatio: "2 / 1" } : {}));
const overlayColor = computed(() => {
  const value = typeof props.section.overlayOpacity === "number" ? props.section.overlayOpacity : 0.45;
  const safe = Math.min(Math.max(value, 0), 0.9);
  return `rgba(0,0,0,${safe})`;
});
const displayTitle = computed(() => (props.section.title && props.section.title.trim()) || "");
const titleColor = computed(() => props.section.titleColor || "#ffffff");
const bodyColor = computed(() => props.section.textColor || "#0f172a");
const titleSize = computed(() => {
  const base = props.section.titleFontSize ?? 72;
  const limited = isMobileView.value ? Math.min(base, 40) : base;
  return `${limited}px`;
});
const textSize = computed(() => `${props.section.textFontSize ?? 18}px`);
const textHtml = computed(() => sanitizeHtml(props.section.text || ""));
</script>
