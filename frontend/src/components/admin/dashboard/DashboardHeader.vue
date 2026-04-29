<template>
  <header class="rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-[0_4px_18px_rgba(15,23,42,0.05)] md:px-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm font-medium text-slate-500">{{ greeting }}, {{ userName }} <span class="ml-1">👋</span></p>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">Central de comando da agência</h1>
        <p class="mt-1 text-sm text-slate-500">Veja o desempenho comercial, performance das páginas e prioridades do dia.</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          @click="$emit('newOpportunity')"
        >
          + Nova oportunidade
        </button>
        <button
          type="button"
          class="inline-flex items-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
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
