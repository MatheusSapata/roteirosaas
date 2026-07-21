<template>
  <article class="rounded-lg border border-border bg-card p-4 text-card-foreground shadow-card transition hover:-translate-y-0.5 hover:shadow-elegant">
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{{ title }}</p>
        <p class="mt-2 font-display text-2xl font-semibold tracking-tight text-foreground">{{ value }}</p>
        <p v-if="subtitle" class="mt-1 text-xs text-muted-foreground">{{ subtitle }}</p>
      </div>
      <span class="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        <slot name="icon" />
      </span>
    </div>
    <p v-if="delta" class="mt-3 text-xs font-semibold" :class="delta.startsWith('-') ? 'text-status-danger-foreground' : 'text-status-success-foreground'">
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
