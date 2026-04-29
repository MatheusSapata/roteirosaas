<template>
  <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_18px_rgba(15,23,42,0.05)] transition hover:-translate-y-0.5 hover:shadow-[0_10px_24px_rgba(15,23,42,0.08)]">
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ title }}</p>
        <p class="mt-2 text-2xl font-bold tracking-tight text-slate-900">{{ value }}</p>
        <p v-if="subtitle" class="mt-1 text-xs text-slate-500">{{ subtitle }}</p>
      </div>
      <span class="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
        <slot name="icon" />
      </span>
    </div>
    <p v-if="delta" class="mt-3 text-xs font-semibold" :class="delta.startsWith('-') ? 'text-rose-600' : 'text-emerald-600'">
      {{ delta }}
    </p>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  value: string;
  subtitle?: string;
  delta?: string;
}>();
</script>
