<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="faq" title-placeholder="Perguntas frequentes" @patch="patch" />
      <EdGroup title="Perguntas" :count="`${items.length} ${items.length === 1 ? 'pergunta' : 'perguntas'}`">
        <EdList
          :items="items"
          :item-title="item => readText(item.question)"
          :new-item="() => ({ question: '', answer: '' })"
          add-label="Adicionar pergunta"
          item-label="Pergunta"
          @update:items="patch({ items: $event })"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.question)" label="Pergunta" @update:model-value="update({ question: writeText(item.question, $event) })" />
            <EdRich :model-value="readText(item.answer)" label="Resposta" @update:model-value="update({ answer: writeText(item.answer, $event) })" />
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'split' ? 'split' : 'accordion'"
          :options="[
            { value: 'accordion', label: 'Sanfona', desc: 'Uma pergunta abaixo da outra' },
            { value: 'split', label: 'Dividido', desc: 'Título ao lado das perguntas' }
          ]"
          @update:model-value="patch({ layout: $event })"
        />
        <EdAlign :value="modelValue" type="faq" @patch="patch" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { FaqSection } from "../../../../types/page";
import EdAlign from "../EdAlign.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdLayouts from "../EdLayouts.vue";
import EdList from "../EdList.vue";
import EdRich from "../EdRich.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: FaqSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FaqSection): void }>();
const { patch } = useDraft(props, emit);
const items = computed(() => props.modelValue.items || []);
</script>
