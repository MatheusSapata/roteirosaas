<template>
  <span class="package-status-badge" :class="toneClass">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  status: string;
}>();

const label = computed(() => (props.status === "active" ? "Ativo" : "Inativo"));
const toneClass = computed(() =>
  props.status === "active" ? "package-status-badge--active" : "package-status-badge--muted",
);
</script>

<style scoped>
.package-status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 1.85rem;
  padding: 0.26rem 0.78rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.package-status-badge--active {
  color: #0f766e;
  background: rgba(240, 253, 250, 0.95);
  border-color: rgba(45, 212, 191, 0.22);
}

.package-status-badge--muted {
  color: #475569;
  background: rgba(248, 250, 252, 0.95);
  border-color: rgba(203, 213, 225, 0.76);
}
</style>
