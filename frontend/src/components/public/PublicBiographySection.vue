<template>
  <section class="w-full" :id="section.anchorId || undefined">
    <div class="mx-auto w-full space-y-6" :class="[section.fullWidth ? 'max-w-none px-0' : 'max-w-6xl']">
      <div
        v-if="hasImage"
        class="relative w-full overflow-hidden bg-slate-900 shadow-2xl"
      >
        <img :src="imageUrl" alt="Biografia" class="h-[280px] w-full object-cover md:h-[420px]" />
        <div class="absolute inset-0" :style="{ backgroundColor: overlayColor }"></div>
        <div class="absolute inset-0 flex items-center justify-center px-6 text-center">
          <h1
            class="text-4xl font-black uppercase tracking-[0.2em] drop-shadow-2xl md:text-6xl"
            :style="{ color: titleColor, fontSize: titleSize }"
          >
            {{ section.title || "Biografia" }}
          </h1>
        </div>
      </div>

      <div
        class="mx-auto max-w-4xl leading-relaxed"
        :style="{ color: bodyColor, fontSize: textSize }"
        v-html="textHtml"
      ></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import type { BiographySection } from "../../types/page";

const props = defineProps<{ section: BiographySection; previewDevice?: "desktop" | "mobile" }>();

const hasImage = computed(() => !!(props.section.image || "").trim());
const imageUrl = computed(() => (hasImage.value ? resolveMediaUrl(props.section.image as string) : ""));
const overlayColor = computed(() => {
  const value = typeof props.section.overlayOpacity === "number" ? props.section.overlayOpacity : 0.45;
  const safe = Math.min(Math.max(value, 0), 0.9);
  return `rgba(0,0,0,${safe})`;
});
const titleColor = computed(() => props.section.titleColor || "#ffffff");
const bodyColor = computed(() => props.section.textColor || "#0f172a");
const titleSize = computed(() => `${props.section.titleFontSize ?? 72}px`);
const textSize = computed(() => `${props.section.textFontSize ?? 18}px`);
const textHtml = computed(() => sanitizeHtml(props.section.text || ""));
</script>
