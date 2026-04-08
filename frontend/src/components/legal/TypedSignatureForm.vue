<template>
  <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="space-y-3">
      <div>
        <label class="input-label">Nome completo</label>
        <input
          type="text"
          class="input"
          :value="modelValue"
          :disabled="disabled || loading"
          placeholder="Digite seu nome completo"
          @input="onInput"
          @keyup.enter="emitSubmit"
        />
        <p class="mt-1 text-xs text-slate-500">Assinamos exibindo exatamente o nome digitado acima.</p>
      </div>
      <button
        type="button"
        class="btn-primary w-full"
        :disabled="isButtonDisabled"
        @click="emitSubmit"
      >
        <span v-if="loading">Processando...</span>
        <span v-else>Assinar contrato</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    loading?: boolean;
    disabled?: boolean;
    canSubmit?: boolean;
  }>(),
  {
    modelValue: "",
    loading: false,
    disabled: false,
    canSubmit: true,
  }
);

const emit = defineEmits<{
  (event: "update:modelValue", value: string): void;
  (event: "submit"): void;
}>();

const onInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit("update:modelValue", target.value);
};

const emitSubmit = () => {
  if (isButtonDisabled.value) return;
  emit("submit");
};

const isButtonDisabled = computed(() => {
  if (props.disabled || props.loading) return true;
  if (!props.canSubmit) return true;
  return props.modelValue.trim().length < 3;
});
</script>

<style scoped>
.input {
  @apply w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none disabled:bg-slate-100;
}
.input-label {
  @apply mb-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.btn-primary {
  @apply rounded-2xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:translate-y-0 disabled:bg-emerald-300;
}
</style>
