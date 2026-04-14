<template>
  <span class="save-indicator" :class="stateClass">
    <span class="dot"></span>
    <span>{{ stateLabel }}</span>
    <span v-if="state === 'saved' && savedLabel" class="hint">· {{ savedLabel }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    state: "idle" | "dirty" | "saving" | "saved" | "error";
    updatedAt?: Date | null;
  }>(),
  { state: "idle", updatedAt: null },
);

const savedLabel = computed(() => {
  if (!props.updatedAt) return "";
  const delta = Math.floor((Date.now() - props.updatedAt.getTime()) / 1000);
  if (delta < 5) return "Salvo agora";
  if (delta < 60) return `Salvo ha ${delta} seg`;
  const minutes = Math.floor(delta / 60);
  if (minutes < 60) return `Salvo ha ${minutes} min`;
  return `Atualizado ${props.updatedAt.toLocaleTimeString("pt-BR")}`;
});

const stateLabel = computed(() => {
  if (props.state === "saving") return "Salvando...";
  if (props.state === "dirty") return "Alteracoes pendentes";
  if (props.state === "saved") return "Tudo sincronizado";
  if (props.state === "error") return "Erro ao salvar";
  return "Sem alteracoes pendentes";
});

const stateClass = computed(() => `is-${props.state}`);
</script>

<style scoped>
.save-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}
.hint {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: currentColor;
}
.is-saving .dot {
  color: #0ea5e9;
}
.is-dirty .dot {
  color: #f59e0b;
}
.is-saved .dot,
.is-idle .dot {
  color: #10b981;
}
.is-error .dot {
  color: #f43f5e;
}
</style>
