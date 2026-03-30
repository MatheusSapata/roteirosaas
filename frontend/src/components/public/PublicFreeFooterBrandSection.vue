<template>
  <section class="w-full border-t border-slate-200 bg-white/80 py-6" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-4">
      <p :class="textAlignClass" class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">
        {{ footerText }}
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { FreeFooterBrandSection } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const props = defineProps<{ section: FreeFooterBrandSection }>();
const footerCopy = {
  default: { pt: "Página desenvolvida através do roteiroonline.com", es: "Página desarrollada a través de roteiroonline.com" }
} as const;
const localize = createLocalizer(getCurrentLanguage());
const footerText = computed(() => {
  const text = localize(props.section.text);
  return text.trim().length ? text : localize(footerCopy.default);
});

const textAlignClass = computed(() => {
  switch (props.section.align) {
    case "left":
      return "text-left";
    case "center":
      return "text-center";
    default:
      return "text-right";
  }
});
</script>
