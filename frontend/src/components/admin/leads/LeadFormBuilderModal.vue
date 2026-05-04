<template>
  <Teleport to="body">
    <transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[120] flex items-center justify-center px-3 py-3 sm:px-4 sm:py-6"
      >
        <div class="app-modal-overlay absolute inset-0"></div>
        <div class="lead-form-builder-modal relative z-10 flex max-h-[calc(100vh-1.5rem)] w-full max-w-5xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl sm:max-h-[calc(100vh-3rem)] dark:bg-[#10141f] dark:text-white">
          <div class="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-5 py-5 dark:border-white/10 dark:bg-[#0b0f1a]">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">Leads</p>
              <h2 class="text-2xl font-bold text-slate-900 dark:text-white">{{ title }}</h2>
              <p class="text-sm text-slate-500 dark:text-slate-400">Monte os campos principais em poucos cliques.</p>
            </div>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-white/20 dark:text-white dark:hover:bg-white/10"
              @click="close"
            >
              Fechar
            </button>
          </div>

          <div class="grid min-h-0 flex-1 gap-0 overflow-hidden lg:grid-cols-[1.08fr_0.92fr]">
            <div class="builder-left min-h-0 space-y-5 overflow-y-auto px-5 py-5">
              <div class="builder-section space-y-4 rounded-2xl border border-slate-100 p-4 dark:border-white/10">
                <div>
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Nome interno</label>
                  <input
                    v-model="state.name"
                    class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-[#0c1221] dark:text-white"
                    placeholder="Formulário de orçamento"
                  />
                </div>

                <div class="grid gap-4 md:grid-cols-2">
                  <div>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Título exibido</label>
                    <input
                      v-model="state.title"
                      class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/15 dark:bg-[#0f1628] dark:text-white"
                      placeholder="Quer receber o roteiro completo?"
                    />
                  </div>
                  <div>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Subtítulo</label>
                    <textarea
                      v-model="state.subtitle"
                      rows="2"
                      class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/15 dark:bg-[#0f1628] dark:text-white"
                      placeholder="Receba no WhatsApp em poucos minutos."
                    ></textarea>
                  </div>
                </div>

                <div class="grid gap-3 md:grid-cols-2">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Texto do botão</p>
                    <input
                      v-model="state.buttonLabel"
                      class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-inner dark:border-white/15 dark:bg-[#0f1628] dark:text-white"
                      placeholder="Quero receber agora"
                    />
                    <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
                      A cor seguirá automaticamente a cor de destaque da página.
                    </p>
                  </div>

                  <label class="flex h-full items-start gap-3 rounded-2xl border border-slate-100 bg-white/80 px-4 py-3 text-sm font-semibold text-slate-600 shadow-sm dark:border-white/15 dark:bg-white/5 dark:text-white">
                    <input type="checkbox" v-model="state.showLogo" class="mt-1 h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand" />
                    <span>
                      Exibir logo da agência no topo
                      <span class="block text-xs font-normal text-slate-500 dark:text-slate-400">Desmarque caso prefira um formulário sem branding.</span>
                    </span>
                  </label>
                </div>

                <div>
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Status inicial do lead</label>
                  <select
                    v-model="state.defaultStatusId"
                    class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-[#0c1221] dark:text-white"
                  >
                    <option value="">Sem status padrão</option>
                    <option v-for="status in statuses" :key="status.id" :value="String(status.id)">
                      {{ status.name }}
                    </option>
                  </select>
                  <p v-if="!statuses.length && !statusesLoading" class="mt-1 text-xs text-slate-500 dark:text-slate-300">
                    Nenhum status configurado. Use o botão "Configurações" em Oportunidades.
                  </p>
                </div>
              </div>

              <div class="space-y-4 rounded-2xl border border-slate-100 p-4 dark:border-white/10">
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p class="text-sm font-semibold text-slate-900 dark:text-white">Campos disponíveis</p>
                    <p class="text-xs text-slate-500 dark:text-slate-400">Escolha quais dados deseja coletar.</p>
                  </div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {{ state.fields.length }} selecionado(s)
                  </p>
                </div>

                <div class="grid gap-3 sm:grid-cols-2">
                  <button
                    v-for="preset in fieldPresets"
                    :key="preset.type"
                    type="button"
                    class="flex flex-col rounded-2xl border px-4 py-3 text-left transition"
                    :class="selectedTypes.includes(preset.type)
                      ? 'border-brand bg-brand/10 text-brand'
                      : 'border-dashed border-slate-200 text-slate-600 hover:border-slate-300 dark:border-white/20 dark:text-white'"
                    @click="toggleField(preset.type)"
                  >
                    <span class="text-sm font-semibold">{{ preset.label }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400">{{ preset.description }}</span>
                  </button>
                </div>

                <div v-if="state.fields.length" class="space-y-3">
                  <div
                    v-for="(field, index) in state.fields"
                    :key="field.id"
                    class="rounded-2xl border border-slate-100 p-4 shadow-sm dark:border-white/10 dark:bg-white/5"
                  >
                    <div class="flex flex-wrap items-center justify-between gap-2 text-sm">
                      <div class="font-semibold text-slate-700 dark:text-slate-200">
                        {{ index + 1 }}. {{ presetLabel(field.type) }}
                      </div>
                      <div class="flex flex-wrap items-center gap-2">
                        <button
                          class="rounded-full border border-slate-200 px-2 py-1 text-xs text-slate-500 transition hover:bg-slate-100 dark:border-white/15 dark:text-white dark:hover:bg-white/10"
                          type="button"
                          @click="moveField(index, -1)"
                          :disabled="index === 0"
                        >
                          ↑
                        </button>
                        <button
                          class="rounded-full border border-slate-200 px-2 py-1 text-xs text-slate-500 transition hover:bg-slate-100 dark:border-white/15 dark:text-white dark:hover:bg-white/10"
                          type="button"
                          @click="moveField(index, 1)"
                          :disabled="index === state.fields.length - 1"
                        >
                          ↓
                        </button>
                        <button
                          class="rounded-full border border-rose-200 px-2 py-1 text-xs text-rose-600 transition hover:bg-rose-50 dark:border-rose-400/40 dark:text-rose-200 dark:hover:bg-rose-500/10"
                          type="button"
                          @click="removeField(index)"
                        >
                          Remover
                        </button>
                      </div>
                    </div>

                    <div class="mt-3 space-y-3">
                      <div class="grid gap-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:bg-white/5 dark:text-slate-300 md:grid-cols-2">
                        <div>
                          <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Campo</p>
                          <p class="mt-1 font-medium text-slate-700 dark:text-slate-100">{{ presetLabel(field.type) }}</p>
                        </div>
                        <div>
                          <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Formato</p>
                          <p class="mt-1 font-medium text-slate-700 dark:text-slate-100">{{ formatLabel(field.type) }}</p>
                        </div>
                      </div>
                      <label class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                        <input type="checkbox" v-model="field.required" class="h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand" />
                        Campo obrigatório
                      </label>
                    </div>
                  </div>
                </div>

                <div
                  v-else
                  class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500 dark:border-white/20 dark:bg-[#141b2d] dark:text-slate-300"
                >
                  Selecione pelo menos um campo para começar.
                </div>
              </div>
            </div>

            <div class="builder-preview hidden min-h-0 overflow-y-auto border-l border-slate-100 bg-slate-50 px-5 py-5 dark:border-white/5 dark:bg-[#0b0f1a] lg:block">
              <LeadFormPreview :form="state" interactive @reorder="reorderFieldsFromPreview" />
            </div>
          </div>

          <div class="flex shrink-0 flex-col gap-4 border-t border-slate-100 bg-white px-5 py-4 text-sm md:flex-row md:items-center md:justify-between dark:border-white/10 dark:bg-[#05070f]">
            <p v-if="errorMessage" class="text-sm text-rose-500">
              {{ errorMessage }}
            </p>
            <div class="flex flex-wrap gap-3 self-end md:ml-auto md:justify-end">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-white/15 dark:text-white dark:hover:bg-white/10"
                @click="close"
              >
                Cancelar
              </button>
              <button
                type="button"
                class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="saving"
                @click="handleSubmit"
              >
                {{ saving ? "Salvando..." : editingId ? "Atualizar formulário" : "Salvar formulário" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from "vue";
import type { LeadFieldType, LeadForm, LeadFormField, LeadFormPayload } from "../../../types/leads";
import { useLeadCaptureStore } from "../../../store/useLeadCaptureStore";
import LeadFormPreview from "./LeadFormPreview.vue";

const props = defineProps<{
  modelValue: boolean;
  form?: LeadForm | null;
  saving?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  save: [{ id: string | null; form: LeadFormPayload }];
}>();

const generateId = () => `field-${Math.random().toString(36).slice(2, 9)}`;

interface FieldPreset {
  type: LeadFieldType;
  label: string;
  description: string;
  placeholder: string;
}

const fieldPresets: FieldPreset[] = [
  {
    type: "name",
    label: "Nome completo",
    description: "Ajuda a personalizar o contato com o lead.",
    placeholder: "Ex.: Ana Silva"
  },
  {
    type: "phone",
    label: "Telefone / WhatsApp",
    description: "Para responder rapidamente pelo WhatsApp.",
    placeholder: "(11) 99999-9999"
  },
  {
    type: "email",
    label: "E-mail",
    description: "Ideal para enviar materiais e cotações.",
    placeholder: "voce@email.com"
  },
  {
    type: "city",
    label: "Cidade",
    description: "Entenda a origem do lead para ofertas.",
    placeholder: "São Paulo - SP"
  },
  {
    type: "cpf",
    label: "CPF",
    description: "Permite sugerir ou vincular cliente automaticamente.",
    placeholder: "000.000.000-00"
  },
  {
    type: "birthdate",
    label: "Data de nascimento",
    description: "Ajuda a completar o cadastro do cliente.",
    placeholder: "1990-01-31"
  }
];

const leadStore = useLeadCaptureStore();
const statuses = computed(() => leadStore.statuses);
const statusesLoading = computed(() => leadStore.statusesLoading);

const state = reactive<LeadFormPayload>({
  name: "",
  title: "",
  subtitle: "",
  buttonLabel: "Enviar",
  buttonColor: "",
  showLogo: true,
  fields: [],
  defaultStatusId: null
});

const editingId = ref<string | null>(null);
const errorMessage = ref("");

const title = computed(() => (editingId.value ? "Editar formulário" : "Novo formulário"));
const selectedTypes = computed(() => state.fields.map(field => field.type));

const formatLabel = (type: LeadFieldType) => {
  const formats: Record<LeadFieldType, string> = {
    name: "Texto livre",
    phone: "Telefone / WhatsApp",
    email: "E-mail",
    city: "Cidade",
    cpf: "CPF",
    birthdate: "Data"
  };
  return formats[type] || "Texto";
};

const presetLabel = (type: LeadFieldType) => fieldPresets.find(preset => preset.type === type)?.label || type;

const createFieldFromPreset = (type: LeadFieldType, value?: Partial<LeadFormField>): LeadFormField => {
  const preset = fieldPresets.find(item => item.type === type);
  return {
    id: value?.id || generateId(),
    type,
    label: preset?.label || value?.label || type,
    placeholder: preset?.placeholder || value?.placeholder || "",
    required: value?.required !== undefined ? value.required : true
  };
};

const toggleField = (type: LeadFieldType) => {
  const index = state.fields.findIndex(field => field.type === type);
  if (index >= 0) {
    state.fields.splice(index, 1);
  } else {
    state.fields.push(createFieldFromPreset(type));
  }
};

const moveField = (index: number, direction: number) => {
  const target = index + direction;
  if (target < 0 || target >= state.fields.length) return;
  const [item] = state.fields.splice(index, 1);
  state.fields.splice(target, 0, item);
};

const reorderFieldsFromPreview = (oldIndex: number, newIndex: number) => {
  if (oldIndex === newIndex) return;
  if (oldIndex < 0 || oldIndex >= state.fields.length) return;
  if (newIndex < 0 || newIndex >= state.fields.length) newIndex = Math.max(0, Math.min(state.fields.length - 1, newIndex));
  const [item] = state.fields.splice(oldIndex, 1);
  if (!item) return;
  state.fields.splice(newIndex, 0, item);
};

const removeField = (index: number) => {
  state.fields.splice(index, 1);
};

const resetState = () => {
  state.name = "";
  state.title = "";
  state.subtitle = "";
  state.buttonLabel = "Enviar";
  state.buttonColor = "";
  state.showLogo = true;
  state.fields = [];
  state.defaultStatusId = null;
  editingId.value = null;
  errorMessage.value = "";
};

const hydrateFromForm = (form?: LeadForm | null) => {
  if (!form) {
    resetState();
    return;
  }
  state.name = form.name || "";
  state.title = form.title || "";
  state.subtitle = form.subtitle || "";
  state.buttonLabel = form.buttonLabel || "Enviar";
  state.buttonColor = "";
  state.showLogo = form.showLogo !== false;
  state.fields = (form.fields || []).map(field => createFieldFromPreset(field.type, field));
  state.defaultStatusId = form.defaultStatusId ? String(form.defaultStatusId) : null;
  editingId.value = form.id;
  errorMessage.value = "";
};

const lockScroll = (lock: boolean) => {
  if (typeof document === "undefined") return;
  document.body.style.overflow = lock ? "hidden" : "";
};

const close = () => {
  emit("update:modelValue", false);
};

const validate = () => {
  if (!state.name.trim()) {
    errorMessage.value = "Defina um nome para identificar o formulário.";
    return false;
  }
  if (!state.title.trim()) {
    errorMessage.value = "Informe o título exibido no formulário.";
    return false;
  }
  if (!state.fields.length) {
    errorMessage.value = "Selecione pelo menos um campo.";
    return false;
  }
  errorMessage.value = "";
  return true;
};

const resolveStatusPayload = () => {
  if (!state.defaultStatusId) return null;
  const parsed = Number(state.defaultStatusId);
  return Number.isNaN(parsed) ? state.defaultStatusId : parsed;
};

const buildPayload = (): LeadFormPayload => {
  const cleanButtonColor = state.buttonColor?.trim() || "";
  const payload: LeadFormPayload = {
    name: state.name.trim(),
    title: state.title.trim(),
    subtitle: state.subtitle?.trim() || "",
    buttonLabel: state.buttonLabel?.trim() || "Enviar",
    showLogo: state.showLogo !== false,
    fields: state.fields.map(field => ({
      ...field,
      label: presetLabel(field.type),
      placeholder: fieldPresets.find(preset => preset.type === field.type)?.placeholder || ""
    })),
    defaultStatusId: resolveStatusPayload()
  };

  if (cleanButtonColor) {
    payload.buttonColor = cleanButtonColor;
  }

  return payload;
};

const handleSubmit = () => {
  if (!validate()) return;
  emit("save", {
    id: editingId.value,
    form: buildPayload()
  });
};

watch(
  () => props.modelValue,
  open => {
    lockScroll(open);
    if (open) {
      leadStore.fetchStatuses().catch(() => undefined);
      hydrateFromForm(props.form || null);
    } else {
      resetState();
    }
  },
  { immediate: true }
);

watch(
  () => props.form,
  form => {
    if (props.modelValue) {
      hydrateFromForm(form || null);
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

:global(.dark-theme .lead-form-builder-modal) {
  background-color: #10141f;
}

:global(.dark-theme .lead-form-builder-modal .builder-left) {
  background-color: #0b0f1a;
}

:global(.dark-theme .lead-form-builder-modal .builder-section) {
  background-color: #11182b;
}

:global(.dark-theme .lead-form-builder-modal input),
:global(.dark-theme .lead-form-builder-modal textarea),
:global(.dark-theme .lead-form-builder-modal select) {
  background-color: #0f1524;
  border-color: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
}

:global(.dark-theme .lead-form-builder-modal .builder-left .text-slate-500) {
  color: #cbd5f5;
}

.builder-preview {
  transform: scale(0.88);
  transform-origin: top center;
}
</style>
