<template>
  <section class="status-card">
    <p class="eyebrow">{{ headline }}</p>
    <p class="status-subtitle">{{ description }}</p>

    <ul v-if="items.length" class="status-list">
      <li v-for="item in items" :key="item.id" class="status-item">
        <span class="status-icon" aria-hidden="true">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="10" cy="10" r="9" stroke-opacity="0.3" />
            <path d="M6 10.5l2.5 2.5L14 7.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <div>
          <p class="status-title">{{ item.title }}</p>
          <p v-if="item.description" class="status-description">{{ item.description }}</p>
        </div>
      </li>
    </ul>
    <p v-else class="status-empty">Ainda não há etapas concluídas para este documento.</p>

    <div v-if="footerText" class="status-footer">
      <span class="status-badge">{{ footerText }}</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
interface DocumentStatusItem {
  id: string;
  title: string;
  description?: string;
}

const props = defineProps<{
  items: DocumentStatusItem[];
  title?: string;
  description?: string;
  footerText?: string | null;
}>();

const headline = computed(() => props.title || "Status do documento");
const description = computed(
  () =>
    props.description ||
    "Este documento passou pelas etapas essenciais de validação e registro."
);
const items = computed(() => props.items || []);
const footerText = computed(() => props.footerText || null);
</script>

<style scoped>
.status-card {
  @apply rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.status-subtitle {
  @apply mt-2 text-sm text-slate-600;
}
.status-list {
  @apply mt-6 space-y-5;
}
.status-item {
  @apply flex gap-4;
}
.status-icon {
  @apply flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600;
}
.status-icon svg {
  width: 24px;
  height: 24px;
}
.status-title {
  @apply text-base font-semibold text-slate-900;
}
.status-description {
  @apply mt-1 text-sm text-slate-500;
}
.status-empty {
  @apply mt-6 rounded-2xl border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500;
}
.status-footer {
  @apply mt-6;
}
.status-badge {
  @apply inline-flex items-center rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700;
}
</style>
