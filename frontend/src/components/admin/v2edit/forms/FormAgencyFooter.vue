<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Dados da agência">
        <p class="ved-info">Nome, descrição, contatos e redes vêm do perfil da agência, em Minha Agência.</p>
        <EdToggle :model-value="modelValue.showCadastur !== false" label="Mostrar selo do Cadastur" @update:model-value="patch({ showCadastur: $event })" />
        <EdSeg
          v-if="modelValue.showCadastur !== false"
          :model-value="modelValue.cadasturDocumentType || 'cnpj'"
          label="Documento do Cadastur"
          :options="[
            { value: 'cnpj', label: 'CNPJ' },
            { value: 'cpf', label: 'CPF' }
          ]"
          @update:model-value="patch({ cadasturDocumentType: $event })"
        />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" fallback="#0E1A15" @change="changes => patch({ ...changes, customBackground: true })" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import type { AgencyFooterSection } from "../../../../types/page";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdSeg from "../EdSeg.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: AgencyFooterSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: AgencyFooterSection): void }>();
const { patch } = useDraft(props, emit);
</script>
