<template>
  <div class="lead-form-preview rounded-2xl border border-slate-200 bg-slate-50 p-5 shadow-inner dark:border-white/10 dark:bg-white/5">
    <div class="flex flex-col items-center text-center">
      <div v-if="agencyLogo && displayLogo" class="mb-4 flex justify-center">
        <img :src="agencyLogo" alt="Logo da agência" class="h-20 w-20 rounded-2xl object-contain" />
      </div>
      <h3 class="mt-2 text-xl font-bold text-slate-900 dark:text-white">
        {{ form.title?.trim() || "Título do formulário" }}
      </h3>
      <p class="mt-1 max-h-24 overflow-hidden text-ellipsis break-words text-center text-sm text-slate-500 dark:text-slate-400">
        {{ form.subtitle?.trim() || "Subtítulo inspirador para convencer o visitante a deixar os dados." }}
      </p>
    </div>

    <template v-if="visibleFields.length">
      <div ref="fieldsContainer" class="mt-5 space-y-3">
        <div
          v-for="(field, idx) in visibleFields"
          :key="field.id || field.type"
          class="space-y-1 cursor-move"
          :data-preview-field="interactive ? idx : null"
        >
          <label class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
            {{ field.label || presetLabels[field.type] }}
          </label>
          <input
            :type="inputType(field.type)"
            :inputmode="inputMode(field.type)"
            :placeholder="field.placeholder || presetPlaceholders[field.type]"
            disabled
            class="w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-500 shadow-inner dark:border-white/10 dark:bg-black/30 dark:text-slate-200"
          />
        </div>
      </div>
    </template>

    <button
      v-if="showButton"
      class="mt-6 w-full rounded-2xl px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:brightness-95"
      :style="buttonStyle"
      type="button"
      disabled
    >
      {{ buttonLabel }}
    </button>
    <p class="mt-3 text-center text-xs text-slate-400 dark:text-slate-500">Pré-visualização estática.</p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import Sortable, { SortableEvent } from "sortablejs";
import { useAgencyStore } from "../../../store/useAgencyStore";
import type { LeadForm, LeadFormField, LeadFieldType } from "../../../types/leads";

const props = defineProps<{
  form: Partial<LeadForm>;
  interactive?: boolean;
}>();

const emit = defineEmits<{
  reorder: [oldIndex: number, newIndex: number];
}>();

const agencyStore = useAgencyStore();
const { agencies, currentAgencyId } = storeToRefs(agencyStore);

const currentAgency = computed(() => agencies.value.find(agency => agency.id === currentAgencyId.value) || agencies.value[0] || null);
const agencyLogo = computed(() => currentAgency.value?.logo_url || "");
const displayLogo = computed(() => props.form.showLogo !== false);

const presetLabels: Record<string, string> = {
  name: "Nome completo",
  phone: "Telefone / WhatsApp",
  email: "E-mail",
  city: "Cidade",
  cpf: "CPF",
  birthdate: "Data de nascimento"
};

const presetPlaceholders: Record<string, string> = {
  name: "Seu nome",
  phone: "(11) 99999-9999",
  email: "voce@email.com",
  city: "São Paulo - SP",
  cpf: "000.000.000-00",
  birthdate: "1990-01-31"
};

const inputType = (type: LeadFieldType) => {
  if (type === "email") return "email";
  if (type === "birthdate") return "date";
  return "text";
};

const inputMode = (type: LeadFieldType) => {
  if (type === "phone" || type === "cpf") return "numeric";
  if (type === "email") return "email";
  return "text";
};

const visibleFields = computed<LeadFormField[]>(() => (props.form.fields || []).filter(Boolean));

const showButton = computed(() => !!visibleFields.value.length || Boolean((props.form.buttonLabel || "").trim()));
const buttonLabel = computed(() => props.form.buttonLabel?.trim() || "Enviar");
const buttonStyle = computed(() => ({
  backgroundColor: props.form.buttonColor || "#3CC96C",
  border: `1px solid ${props.form.buttonColor || "#3CC96C"}`
}));

const fieldsContainer = ref<HTMLElement | null>(null);
let sortable: Sortable | null = null;

const destroySortable = () => {
  if (sortable) {
    sortable.destroy();
    sortable = null;
  }
};

const setupSortable = () => {
  if (!props.interactive || visibleFields.value.length <= 1 || !fieldsContainer.value) {
    destroySortable();
    return;
  }
  destroySortable();
  sortable = Sortable.create(fieldsContainer.value, {
    animation: 180,
    draggable: "[data-preview-field]",
    ghostClass: "preview-field-ghost",
    dragClass: "preview-field-dragging",
    onEnd(evt: SortableEvent) {
      if (typeof evt.oldIndex !== "number" || typeof evt.newIndex !== "number") return;
      if (evt.oldIndex === evt.newIndex) return;
      emit("reorder", evt.oldIndex, evt.newIndex);
    }
  });
};

onMounted(setupSortable);
onBeforeUnmount(destroySortable);

watch(
  () => [props.interactive, visibleFields.value.length],
  () => setupSortable()
);
</script>

<style scoped>
.lead-form-preview {
  min-height: 240px;
}

.preview-field-ghost {
  opacity: 0.5;
}

.preview-field-dragging {
  cursor: grabbing !important;
}
</style>
