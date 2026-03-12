<template>
  <section
    class="relative w-full"
    :class="isFullLayout ? 'px-0 pb-0' : 'px-4 py-12'"
    :id="section.anchorId || undefined"
  >
    <div v-if="imageSrc" :class="isFullLayout ? 'h-[380px] sm:h-[520px]' : 'mx-auto max-w-4xl'">
      <div
        v-if="isFullLayout"
        class="relative h-full w-full overflow-hidden"
      >
        <img
          :src="imageSrc"
          :alt="altText"
          class="h-full w-full object-cover"
        />
        <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/20 via-black/10 to-transparent"></div>
      </div>
      <div
        v-else
        class="overflow-hidden rounded-[32px] border border-white/40 bg-white shadow-2xl shadow-emerald-900/10"
      >
        <img
          :src="imageSrc"
          :alt="altText"
          class="h-full w-full object-cover"
        />
      </div>
    </div>
    <div
      v-else
      class="mx-auto max-w-3xl rounded-3xl border border-dashed border-slate-300 bg-slate-50/70 px-6 py-12 text-center text-slate-500"
    >
      Adicione uma imagem para esta seção.
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PhotoSection } from "../../types/page";
import { resolveMediaUrl } from "../../utils/media";

const props = defineProps<{ section: PhotoSection }>();

const imageSrc = computed(() => resolveMediaUrl(props.section.image) || props.section.image || "");
const altText = computed(() => props.section.altText || "Imagem ilustrativa");
const isFullLayout = computed(() => (props.section.layout || "card") === "full");
</script>
