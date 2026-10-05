<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="internal_form" title-placeholder="Fale com um especialista" @patch="patch" />
      <EdGroup title="Formulário">
        <label class="ved-field">
          <span class="ved-label">Formulário usado</span>
          <select class="ved-select" :value="modelValue.formId || ''" @change="patch({ formId: ($event.target as HTMLSelectElement).value })">
            <option value="">{{ loading ? "Carregando…" : "Escolher formulário…" }}</option>
            <option v-for="form in forms" :key="form.id" :value="String(form.id)">{{ form.name || form.title }}</option>
          </select>
          <span class="ved-hint">Os envios viram oportunidades e usam as notificações deste formulário.</span>
        </label>
        <p v-if="!loading && !forms.length" class="ved-info">Crie um formulário para publicar esta seção.</p>
        <div class="ved-inline-actions">
          <button type="button" class="ved-inline-btn" @click="openBuilder(null)">Criar formulário</button>
          <button v-if="selectedForm" type="button" class="ved-inline-btn" @click="openBuilder(selectedForm)">Editar campos e avisos</button>
        </div>
      </EdGroup>
      <EdGroup title="Depois de enviar">
        <EdText
          :model-value="readText(modelValue.successMessage)"
          label="Mensagem"
          multiline
          placeholder="Recebemos seus dados! Em breve falamos com você."
          @update:model-value="patch({ successMessage: writeText(modelValue.successMessage, $event) })"
        />
        <EdText
          :model-value="modelValue.successDurationSeconds ?? 5"
          label="Mostrar por (segundos)"
          type="number"
          min="1"
          @update:model-value="patch({ successDurationSeconds: Math.min(30, Math.max(1, Number($event) || 5)) })"
        />
      </EdGroup>
      <LeadFormBuilderModal v-model="builderOpen" :form="builderForm" :saving="saving" @save="saveForm" />
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdSeg
          :model-value="modelValue.alignment || 'center'"
          label="Alinhamento"
          :options="[
            { value: 'left', label: 'Esquerda' },
            { value: 'center', label: 'Centro' },
            { value: 'right', label: 'Direita' }
          ]"
          @update:model-value="patch({ alignment: $event })"
        />
        <ImageUploadField
          layout="compact"
          :model-value="modelValue.backgroundType === 'image' ? modelValue.backgroundImage || '' : ''"
          label="Foto de fundo"
          hint="Opcional. Com foto, ela aparece escurecida atrás do formulário."
          @update:model-value="setPhoto"
        />
        <EdSeg
          v-if="modelValue.backgroundType === 'image'"
          :model-value="overlay"
          label="Escurecer a foto"
          :options="[
            { value: 0.25, label: 'Pouco' },
            { value: 0.45, label: 'Médio' },
            { value: 0.65, label: 'Muito' }
          ]"
          @update:model-value="patch({ overlayOpacity: $event })"
        />
      </EdGroup>
      <EdGroup v-if="modelValue.backgroundType !== 'image'" title="Fundo">
        <EdBackground :value="modelValue" auto @change="changes => patch({ ...changes, backgroundType: 'solid' })" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useLeadCaptureStore } from "../../../../store/useLeadCaptureStore";
import type { LeadForm, LeadFormPayload } from "../../../../types/leads";
import type { InternalFormSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import LeadFormBuilderModal from "../../leads/LeadFormBuilderModal.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: InternalFormSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: InternalFormSection): void }>();
const { patch } = useDraft(props, emit);

const store = useLeadCaptureStore();
const forms = computed(() => store.forms);
const loading = computed(() => store.formsLoading);
const selectedForm = computed(() => forms.value.find(form => String(form.id) === String(props.modelValue.formId)) || null);
onMounted(() => store.fetchForms().catch(() => undefined));

const builderOpen = ref(false);
const builderForm = ref<LeadForm | null>(null);
const saving = ref(false);
const openBuilder = (form: LeadForm | null) => {
  builderForm.value = form;
  builderOpen.value = true;
};
const saveForm = async ({ id, form }: { id: string | null; form: LeadFormPayload }) => {
  saving.value = true;
  try {
    const saved = id ? await store.updateForm(id, form) : await store.createForm(form);
    patch({ formId: String(saved.id) });
    builderOpen.value = false;
  } finally {
    saving.value = false;
  }
};

const setPhoto = (url: string | null) => patch(url ? { backgroundType: "image", backgroundImage: url } : { backgroundType: "solid", backgroundImage: "" });
const overlay = computed(() => {
  const value = typeof props.modelValue.overlayOpacity === "number" ? props.modelValue.overlayOpacity : 0.45;
  return [0.25, 0.45, 0.65].reduce((best, option) => (Math.abs(option - value) < Math.abs(best - value) ? option : best), 0.45);
});
</script>
