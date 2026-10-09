<template>
  <EdSeg
    v-if="canAlign"
    :model-value="current"
    label="Alinhamento"
    :options="[
      { value: 'left', label: 'Esquerda' },
      { value: 'center', label: 'Centro' }
    ]"
    :hint="hint"
    @update:model-value="emit('patch', { headingAlign: $event })"
  />
</template>

<script setup lang="ts">
// Um controle só por seção: o alinhamento vale para o computador e o celular, e o texto
// não tem alinhamento próprio (o editor de texto do editor novo não mostra esse botão).
import { computed } from "vue";
import type { SectionType } from "../../../types/page";
import { alignAppliesToItems, resolveHeadingAlign, supportsHeadingAlign } from "../../../utils/sectionHeadings";
import EdSeg from "./EdSeg.vue";

const props = defineProps<{ value: Record<string, any>; type: SectionType }>();
const emit = defineEmits<{ (e: "patch", value: Record<string, any>): void }>();
const canAlign = computed(() => supportsHeadingAlign(props.type));
const current = computed(() => resolveHeadingAlign(props.type, props.value.headingAlign));
const hint = computed(() =>
  alignAppliesToItems(props.type)
    ? "Cabeçalho e itens (ícone, título e texto). Vale para o computador e o celular."
    : "Selo, título e texto do cabeçalho. Vale para o computador e o celular."
);
</script>
