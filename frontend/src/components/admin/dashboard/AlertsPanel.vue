<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_4px_18px_rgba(15,23,42,0.05)]">
    <h3 class="mb-4 text-base font-bold text-slate-900">Alertas inteligentes</h3>
    <div class="grid gap-3 md:grid-cols-3">
      <article
        v-for="alert in alerts"
        :key="alert.title"
        class="rounded-xl border px-4 py-3"
        :class="alert.tone === 'warning' ? 'border-amber-200 bg-amber-50 text-amber-900' : alert.tone === 'danger' ? 'border-rose-200 bg-rose-50 text-rose-900' : 'border-slate-200 bg-slate-50 text-slate-900'"
      >
        <p class="text-xs font-semibold uppercase tracking-wide opacity-70">{{ alert.title }}</p>
        <p class="mt-1 text-xl font-bold">{{ alert.value }}</p>
        <p class="mt-1 text-xs opacity-80">{{ alert.description }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
type AlertItem = {
  title: string;
  value: string;
  description: string;
  tone?: "neutral" | "warning" | "danger";
};

defineProps<{
  alerts: AlertItem[];
}>();
</script>
