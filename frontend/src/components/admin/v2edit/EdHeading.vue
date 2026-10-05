<template>
  <EdGroup title="Cabeçalho da seção">
    <EdText v-if="!noLabel" :model-value="labelValue" label="Selo" hint="Pequena etiqueta acima do título. Deixe vazio para não mostrar." placeholder="Ex.: Vantagens" @update:model-value="write(keys.label, $event)" />
    <EdText :model-value="read(keys.title)" label="Título" :placeholder="titlePlaceholder" @update:model-value="write(keys.title, $event)" />
    <EdRich v-if="!noText" :model-value="read(keys.text)" label="Texto" hint="Opcional." @update:model-value="write(keys.text, $event)" />
  </EdGroup>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { SectionType } from "../../../types/page";
import { getSectionHeadingDefaults } from "../../../utils/sectionHeadings";
import EdGroup from "./EdGroup.vue";
import EdRich from "./EdRich.vue";
import EdText from "./EdText.vue";
import { readText, writeText } from "./useDraft";

const props = withDefaults(
  defineProps<{
    value: Record<string, any>;
    /** Tipo da seção, para mostrar o selo padrão quando nada foi salvo. */
    type?: SectionType;
    keys?: { label: string; title: string; text: string };
    noLabel?: boolean;
    noText?: boolean;
    titlePlaceholder?: string;
  }>(),
  { keys: () => ({ label: "headingLabel", title: "title", text: "subtitle" }), noLabel: false, noText: false, titlePlaceholder: "" }
);
const emit = defineEmits<{ (e: "patch", value: Record<string, any>): void }>();
const read = (key: string) => readText(props.value[key]);
// Sem selo salvo, a página mostra o selo padrão da seção: o campo mostra o mesmo.
const labelValue = computed(() => {
  const saved = props.value[props.keys.label];
  if (saved !== null && saved !== undefined) return readText(saved);
  return props.type ? readText(getSectionHeadingDefaults(props.type).label) : "";
});
const write = (key: string, next: string) => emit("patch", { [key]: writeText(props.value[key], next) });
</script>
