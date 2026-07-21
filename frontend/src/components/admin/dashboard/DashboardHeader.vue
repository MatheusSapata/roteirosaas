<template>
  <header class="rounded-lg border border-border bg-card px-5 py-5 text-card-foreground shadow-card md:px-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm font-medium text-muted-foreground">{{ greeting }}, {{ userName }} <span class="ml-1">👋</span></p>
        <h1 class="mt-1 font-display text-2xl font-semibold tracking-tight text-foreground md:text-3xl">Central de comando da agência</h1>
        <p class="mt-1 text-sm text-muted-foreground">Veja o desempenho comercial, performance das páginas e prioridades do dia.</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="inline-flex h-9 items-center rounded-lg border border-border bg-background px-4 text-sm font-semibold text-foreground transition-colors hover:bg-accent"
          @click="$emit('newOpportunity')"
        >
          + Nova oportunidade
        </button>
        <button
          type="button"
          class="inline-flex h-9 items-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground shadow-soft transition-colors hover:bg-brand-dark"
          @click="$emit('newPage')"
        >
          + Nova página
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  greeting: string;
  userName: string;
}>();

defineEmits<{
  newPage: [];
  newOpportunity: [];
}>();
</script>
