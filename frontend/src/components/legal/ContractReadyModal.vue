<template>
  <teleport to="body">
    <transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Contrato digital</p>
              <h2 class="mt-2 text-2xl font-semibold text-slate-900">Seu contrato está pronto para assinatura</h2>
              <p class="mt-3 text-sm text-slate-500">
                Finalizamos todas as etapas necessárias. Assine o documento para concluir o processo com segurança.
              </p>
            </div>
            <button
              type="button"
              class="rounded-full p-2 text-slate-400 transition hover:bg-slate-100"
              @click="close"
            >
              <span class="sr-only">Fechar</span>
              &times;
            </button>
          </div>

          <div class="mt-6 space-y-4">
            <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
              <p class="font-medium text-slate-900">Próximo passo</p>
              <p class="mt-1 text-slate-600">
                Clique abaixo para revisar e assinar o contrato eletrônico.
              </p>
            </div>
            <div class="flex flex-wrap gap-3">
              <button
                type="button"
                class="btn-primary flex-1 justify-center"
                :disabled="!signatureLink"
                @click="openSignature"
              >
                Assinar agora
              </button>
              <button type="button" class="btn-secondary flex-1 justify-center" @click="close">
                Depois
              </button>
            </div>
            <p class="text-center text-xs text-slate-400">Você poderá acessar este link novamente pelo e-mail enviado.</p>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean;
  signatureLink?: string | null;
}>();

const emit = defineEmits<{ (e: "update:modelValue", value: boolean): void }>();

const close = () => {
  emit("update:modelValue", false);
};

const openSignature = () => {
  if (!props.signatureLink) return;
  window.open(props.signatureLink, "_blank");
  emit("update:modelValue", false);
};
</script>

<style scoped>
.btn-primary {
  @apply rounded-full bg-emerald-500 px-4 py-3 text-sm font-semibold text-white shadow transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-emerald-300;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-400 hover:text-emerald-600;
}
</style>
