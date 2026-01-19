<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="text-center">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Por que escolher</p>
        <h2 class="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">{{ section.title }}</h2>
        <p v-if="section.subtitle" class="mt-2 text-base leading-relaxed text-slate-600 md:text-lg">{{ section.subtitle }}</p>
      </div>

      <div
        class="mt-8 grid grid-cols-2 gap-4 md:grid-cols-2 lg:grid-cols-4"
        :class="isMobilePreview ? '!grid-cols-2 !gap-4' : ''"
      >
        <article
          v-for="(item, idx) in section.items"
          :key="idx"
          class="flex h-full flex-col rounded-2xl bg-white/95 p-4 text-center shadow-[0_16px_40px_-28px_rgba(15,23,42,0.6)] ring-1 ring-slate-100"
        >
          <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 text-2xl">
            <span>{{ item.icon || "⭐" }}</span>
          </div>
          <h3 class="mt-3 text-lg font-semibold text-slate-900">{{ item.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ item.description }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ReasonsSection } from "../../types/page";

const props = defineProps<{ section: ReasonsSection; previewDevice?: "desktop" | "mobile" }>();
const isMobilePreview = computed(() => props.previewDevice === "mobile");
</script>
