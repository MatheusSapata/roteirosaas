<template>
  <section class="rounded-lg border border-border bg-card p-5 text-card-foreground shadow-card">
    <h3 class="mb-4 font-display text-base font-semibold text-foreground">{{ title }}</h3>
    <div class="space-y-2">
      <div
        v-for="item in items"
        :key="item.label"
        class="flex items-center justify-between rounded-lg border border-border bg-muted px-3 py-2"
      >
        <span class="text-sm text-muted-foreground">{{ item.label }}</span>
        <span class="text-sm font-bold text-foreground">{{ item.value }}</span>
      </div>
      <p v-if="!items.length" class="text-sm text-muted-foreground">Sem dados.</p>
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
