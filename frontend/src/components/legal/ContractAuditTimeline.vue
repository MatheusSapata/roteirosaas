<template>
  <section class="card timeline-card">
    <div class="timeline-header">
      <div>
        <p class="eyebrow">{{ computedTitle }}</p>
        <p class="timeline-subtitle">Visão cronológica e auditável dos eventos deste documento.</p>
      </div>
      <button
        v-if="hasMore && events.length"
        type="button"
        class="timeline-button"
        :disabled="loading"
        @click="$emit('load-full-history')"
      >
        Ver histórico completo
      </button>
    </div>

    <div v-if="error" class="timeline-error">
      <p>{{ error }}</p>
    </div>
    <div v-else-if="loading && !events.length" class="timeline-loading">
      <div v-for="index in 4" :key="index" class="timeline-skeleton"></div>
    </div>
    <ul v-else-if="events.length" class="timeline-list">
      <li v-for="event in events" :key="event.id" class="timeline-item">
        <div class="timeline-marker">
          <span class="timeline-dot" />
        </div>
        <div class="timeline-content">
          <div class="timeline-row">
            <p class="timeline-title">{{ event.title }}</p>
            <span class="timeline-actor">{{ actorLabel(event.actor_type) }}</span>
          </div>
          <p v-if="event.description" class="timeline-description">{{ event.description }}</p>
          <p class="timeline-meta">
            {{ formatDateTime(event.occurred_at) }}
            <span v-if="event.is_reconstructed" class="timeline-tag">Reconstruído</span>
          </p>
        </div>
      </li>
    </ul>
    <div v-else class="timeline-empty">
      <p>Nenhum evento registrado ainda.</p>
    </div>

    <div v-if="loading && events.length" class="timeline-progress">
      Carregando histórico completo...
    </div>
    <button
      v-else-if="hasMore && events.length"
      type="button"
      class="timeline-button timeline-button--full"
      :disabled="loading"
      @click="$emit('load-full-history')"
    >
      Ver histórico completo
    </button>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { LegalContractAuditEvent } from "../../types/legal";

const props = defineProps<{
  events: LegalContractAuditEvent[];
  loading?: boolean;
  error?: string | null;
  hasMore?: boolean;
  title?: string;
}>();

defineEmits<{
  (event: "load-full-history"): void;
}>();

const computedTitle = computed(() => props.title || "Histórico do documento");

const formatDateTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const day = date.toLocaleDateString("pt-BR");
  const time = date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${day} • ${time}`;
};

const actorLabel = (value: string) => {
  switch (value) {
    case "customer":
      return "Cliente";
    case "agency":
      return "Agência";
    default:
      return "Sistema";
  }
};

const events = computed(() => props.events || []);
const hasMore = computed(() => Boolean(props.hasMore));
const loading = computed(() => Boolean(props.loading));
const error = computed(() => props.error || "");
</script>

<style scoped>
.timeline-card {
  @apply rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.timeline-header {
  @apply flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between;
}
.timeline-subtitle {
  @apply mt-1 text-sm text-slate-500;
}
.timeline-button {
  @apply rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-emerald-400 hover:text-emerald-600 disabled:opacity-60;
}
.timeline-button--full {
  @apply mt-4 w-full justify-center border-slate-300;
}
.timeline-error {
  @apply mt-4 rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-600;
}
.timeline-loading {
  @apply mt-6 space-y-3;
}
.timeline-skeleton {
  @apply h-16 rounded-2xl bg-slate-100;
  background-image: linear-gradient(90deg, rgba(15, 23, 42, 0.04), rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0.04));
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.timeline-list {
  @apply relative mt-6 space-y-6 pl-5;
}
.timeline-list::before {
  content: "";
  @apply absolute left-2 top-0 h-full w-px bg-slate-200;
}
.timeline-item {
  @apply relative flex gap-4;
}
.timeline-marker {
  @apply absolute -left-[7px] top-1 flex h-3.5 w-3.5 items-center justify-center;
}
.timeline-dot {
  @apply block h-3.5 w-3.5 rounded-full border border-emerald-200 bg-white;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
}
.timeline-content {
  @apply w-full rounded-2xl border border-slate-100 bg-slate-50/50 p-4 shadow-sm;
}
.timeline-row {
  @apply flex flex-wrap items-center justify-between gap-3;
}
.timeline-title {
  @apply text-base font-semibold text-slate-900;
}
.timeline-description {
  @apply mt-2 text-sm text-slate-600;
}
.timeline-meta {
  @apply mt-3 text-xs font-semibold uppercase tracking-[0.25em] text-slate-400;
}
.timeline-actor {
  @apply rounded-full bg-slate-900/5 px-3 py-1 text-xs font-semibold text-slate-600;
}
.timeline-tag {
  @apply ml-3 rounded-full bg-slate-900/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500;
}
.timeline-empty {
  @apply mt-6 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500;
}
.timeline-progress {
  @apply mt-4 text-center text-sm text-slate-500;
}
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
