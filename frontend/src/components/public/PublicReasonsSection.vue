<template>
  <section class="w-full" :style="{ background: section.backgroundColor || 'linear-gradient(180deg,#f8fafc,#fff)' }" :id="section.anchorId || undefined">
    <div class="mx-auto max-w-6xl px-6 py-12">
      <div class="text-center">
        <div class="flex justify-center">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="headingAccent" />
        </div>
        <h2 class="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">{{ section.title }}</h2>
        <p v-if="section.subtitle" class="mt-2 text-base leading-relaxed text-slate-600 md:text-lg">{{ section.subtitle }}</p>
      </div>

      <div v-if="isMobilePreview" class="mt-8 flex flex-col gap-4">
        <article
          v-for="(item, idx) in limitedItems"
          :key="'mobile-' + idx"
          class="flex w-full flex-col rounded-2xl bg-white/95 p-4 text-center shadow-[0_16px_40px_-28px_rgba(15,23,42,0.6)] ring-1 ring-slate-100"
        >
          <ReasonCard :item="item" />
        </article>
      </div>

      <div v-else class="mt-8 flex flex-col items-center gap-5">
        <div
          v-for="(row, rowIndex) in desktopRows"
          :key="'row-' + rowIndex"
          class="flex w-full flex-wrap justify-center gap-4"
        >
          <article
            v-for="(item, idx) in row"
            :key="'card-' + rowIndex + '-' + idx"
            class="flex w-full max-w-[260px] flex-col rounded-2xl bg-white/95 p-4 text-center shadow-[0_16px_40px_-28px_rgba(15,23,42,0.6)] ring-1 ring-slate-100"
          >
            <ReasonCard :item="item" />
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from "vue";
import type { ReasonsSection, ReasonItem } from "../../types/page";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";

const props = defineProps<{ section: ReasonsSection; previewDevice?: "desktop" | "mobile" }>();
const headingDefaults = getSectionHeadingDefaults("reasons");
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const headingLabel = computed(() => props.section.headingLabel ?? headingDefaults.label);
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const headingAccent = "#0ea5e9";
const MAX_ITEMS = 8;

const limitedItems = computed(() => (props.section.items || []).slice(0, MAX_ITEMS));

const desktopRows = computed(() => {
  const items = limitedItems.value;
  const total = items.length;
  if (!total) return [];
  if (total <= 4) return [items];
  const firstRowCount = Math.min(4, Math.ceil(total / 2));
  const first = items.slice(0, firstRowCount);
  const second = items.slice(firstRowCount);
  return [first, second];
});

const ReasonCard = defineComponent({
  props: {
    item: {
      type: Object as () => ReasonItem,
      required: true
    }
  },
  setup(componentProps) {
    return () =>
      h("div", { class: "reason-card-content" }, [
        h("div", { class: "mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 text-2xl" }, [
          h("span", componentProps.item.icon || "⭐")
        ]),
        h("h3", { class: "mt-3 text-lg font-semibold text-slate-900" }, componentProps.item.title),
        h("p", { class: "mt-2 text-sm leading-relaxed text-slate-600" }, componentProps.item.description)
      ]);
  }
});
</script>
