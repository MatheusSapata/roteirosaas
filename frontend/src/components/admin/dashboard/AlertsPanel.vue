<template>
  <section class="rounded-lg border border-border bg-card p-5 text-card-foreground shadow-card">
    <h3 class="mb-4 font-display text-base font-semibold text-foreground">Alertas inteligentes</h3>
    <div class="grid gap-3 md:grid-cols-3">
      <article
        v-for="alert in alerts"
        :key="alert.title"
        class="rounded-lg border px-4 py-3"
        :class="alert.tone === 'warning' ? 'border-border bg-status-warning text-status-warning-foreground' : alert.tone === 'danger' ? 'border-border bg-status-danger text-status-danger-foreground' : 'border-border bg-status-neutral text-status-neutral-foreground'"
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
