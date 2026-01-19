<template>
  <section class="w-full border-t border-slate-200 bg-white/80 py-6" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-4">
      <p :class="textAlignClass" class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">
        {{ section.text || "Página desenvolvida através do roteiroonline.com" }}
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { FreeFooterBrandSection } from "../../types/page";

const props = defineProps<{ section: FreeFooterBrandSection }>();

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
