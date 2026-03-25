<template>
  <Teleport to="body">
    <transition name="fade">
      <div
        v-if="modelValue && form"
        class="fixed inset-0 z-[140] flex min-h-screen items-center justify-center px-4 py-6"
      >
        <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"></div>
        <div
          class="relative z-10 w-full max-w-lg rounded-[32px] border border-white/10 bg-white/95 p-6 text-slate-900 shadow-2xl backdrop-blur-sm dark:bg-slate-900/95 dark:text-white"
        >
          <button
            v-if="dismissible"
            type="button"
            class="absolute right-4 top-4 rounded-full bg-white/70 p-1 text-slate-700 shadow-sm transition hover:bg-white dark:bg-slate-800/70 dark:text-white"
            @click="handleDismiss"
          >
            <span class="sr-only">Fechar</span>
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 6l12 12M6 18L18 6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <div class="space-y-5">
            <div class="space-y-2 text-center">
              <div v-if="brandingLogo" class="flex justify-center">
                <img :src="brandingLogo" alt="Logo da agência" class="h-16 w-16 rounded-xl object-contain" />
              </div>
              <h2 class="text-2xl font-bold">{{ form.title || "Faça parte da lista" }}</h2>
              <p class="text-sm text-slate-500 dark:text-slate-300">
                {{ form.subtitle || "Preencha para continuar explorando este roteiro." }}
              </p>
            </div>

            <form class="space-y-4" @submit.prevent="handleSubmit">
              <div v-for="field in form.fields" :key="field.id" class="space-y-1">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {{ field.label }}
                  <span v-if="field.required" class="text-rose-500">*</span>
                </label>
                <input
                  v-model="formState[field.id]"
                  :placeholder="field.placeholder"
                  :type="inputType(field.type)"
                  :inputmode="inputMode(field.type)"
                  class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand focus:ring-2 focus:ring-brand/50 dark:border-white/10 dark:bg-slate-900 dark:text-white"
                />
                <p v-if="errors[field.id]" class="text-xs text-rose-500">{{ errors[field.id] }}</p>
              </div>

              <button
                type="submit"
                class="flex w-full items-center justify-center rounded-2xl px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
                :style="{ backgroundColor: form.buttonColor || '#22c55e' }"
                :disabled="loading"
              >
                {{ loading ? "Enviando..." : form.buttonLabel || "Enviar" }}
              </button>
            </form>
            <p v-if="generalError" class="text-center text-sm text-rose-500">{{ generalError }}</p>
            <p class="text-center text-xs text-slate-400">
              Seus dados são enviados para a agência responsável por esta página.
            </p>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { onUnmounted, reactive, ref, watch } from "vue";
import { submitLeadForm } from "../../services/leadCapture";
import type { LeadForm } from "../../types/leads";

const props = defineProps<{
  modelValue: boolean;
  form: LeadForm | null;
  source?: string | number | null;
  brandingLogo?: string | null;
  pageId?: number | null;
  pageSlug?: string | null;
  pageTitle?: string | null;
  pageUrl?: string | null;
  dismissible?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  submitted: [];
  dismissed: [];
}>();

const formState = reactive<Record<string, string>>({});
const errors = reactive<Record<string, string>>({});
const loading = ref(false);
const generalError = ref("");

const resetState = () => {
  Object.keys(formState).forEach(key => delete formState[key]);
  Object.keys(errors).forEach(key => delete errors[key]);
  loading.value = false;
  generalError.value = "";
};

const setupFields = () => {
  resetState();
  (props.form?.fields || []).forEach(field => {
    formState[field.id] = "";
    errors[field.id] = "";
  });
};

const validate = () => {
  let valid = true;
  (props.form?.fields || []).forEach(field => {
    const value = (formState[field.id] || "").trim();
    if (field.required && !value) {
      errors[field.id] = "Campo obrigatório";
      valid = false;
    } else {
      errors[field.id] = "";
    }
    if (field.type === "email" && value) {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;
      if (!emailPattern.test(value)) {
        errors[field.id] = "Informe um e-mail válido";
        valid = false;
      }
    }
  });
  return valid;
};

const lockScroll = (lock: boolean) => {
  if (typeof document === "undefined") return;
  document.body.style.overflow = lock ? "hidden" : "";
};

const handleSubmit = async () => {
  if (!props.form) return;
  if (!validate()) return;
  loading.value = true;
  generalError.value = "";
  try {
    await submitLeadForm(props.form.id, {
      formId: props.form.id,
      values: props.form.fields.map(field => ({
        fieldId: field.id,
        type: field.type,
        value: formState[field.id] || ""
      })),
      source: props.source ? String(props.source) : undefined,
      pageId: typeof props.pageId === "number" ? props.pageId : undefined,
      pageSlug: props.pageSlug || undefined,
      pageTitle: props.pageTitle || props.form?.title || undefined,
      pageUrl: props.pageUrl || (typeof window !== "undefined" ? window.location.href : undefined)
    });
    emit("submitted");
    finalize();
  } catch (err) {
    console.error("Erro ao enviar formulário de lead", err);
    generalError.value = "Não foi possível enviar. Tente novamente.";
  } finally {
    loading.value = false;
  }
};

const finalize = () => {
  emit("update:modelValue", false);
};

const handleDismiss = () => {
  emit("dismissed");
  emit("update:modelValue", false);
};

const inputType = (type: string) => {
  if (type === "email") return "email";
  if (type === "phone") return "tel";
  return "text";
};

const inputMode = (type: string) => {
  if (type === "phone") return "tel";
  if (type === "email") return "email";
  return "text";
};

watch(
  () => props.modelValue,
  value => {
    lockScroll(value);
    if (value) {
      setupFields();
    } else {
      resetState();
    }
  },
  { immediate: true }
);

watch(
  () => props.form,
  () => {
    if (props.modelValue) {
      setupFields();
    }
  }
);

onUnmounted(() => lockScroll(false));
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
