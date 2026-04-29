<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_4px_18px_rgba(15,23,42,0.05)]">
    <h3 class="mb-4 text-base font-bold text-slate-900">{{ title }}</h3>
    <div class="space-y-2">
      <div
        v-for="item in items"
        :key="item.label"
        class="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2"
      >
        <span class="text-sm text-slate-700">{{ item.label }}</span>
        <span class="text-sm font-bold text-slate-900">{{ item.value }}</span>
      </div>
      <p v-if="!items.length" class="text-sm text-slate-500">Sem dados.</p>
    </div>
  </section>
</template>

<script setup lang="ts">
type PipelineItem = {
  label: string;
  value: number | string;
};

defineProps<{
  title: string;
  items: PipelineItem[];
}>();
</script>
