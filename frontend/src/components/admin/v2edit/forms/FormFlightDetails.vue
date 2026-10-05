<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="flight_details" title-placeholder="Detalhes do voo" @patch="patch" />
      <EdGroup title="Voos">
        <!-- Editor de trechos de sempre (busca automática e salvamento por trecho), em versão compacta. -->
        <SectionFlightDetailsForm ref="flights" compact :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)" />
      </EdGroup>
      <EdGroup title="Informações gerais">
        <EdRich :model-value="readText(modelValue.generalInfo)" label="Texto" hint="Bagagem, documentos, check-in…" @update:model-value="patch({ generalInfo: writeText(modelValue.generalInfo, $event) })" />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Trechos">
        <EdToggle :model-value="modelValue.showOutbound !== false" label="Mostrar ida" @update:model-value="patch({ showOutbound: $event })" />
        <EdToggle :model-value="modelValue.showInbound !== false" label="Mostrar volta" @update:model-value="patch({ showInbound: $event })" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { FlightDetailsSection } from "../../../../types/page";
import SectionFlightDetailsForm from "../../SectionFlightDetailsForm.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdRich from "../EdRich.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: FlightDetailsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FlightDetailsSection): void }>();
const { patch } = useDraft(props, emit);

// O editor chama isto antes de salvar a seção, para não perder um trecho em edição.
const flights = ref<InstanceType<typeof SectionFlightDetailsForm> | null>(null);
defineExpose({
  savePendingSegmentDraft: () => (flights.value as any)?.savePendingSegmentDraft?.() ?? true
});
</script>
