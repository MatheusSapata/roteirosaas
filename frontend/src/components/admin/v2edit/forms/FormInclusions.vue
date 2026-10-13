<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="inclusions" title-placeholder="O que está incluso na sua viagem" @patch="patch" />
      <EdGroup title="Seu pacote inclui" :count="countLabel(included.length)">
        <EdText :model-value="readText(modelValue.includedTitle)" label="Título da lista" placeholder="Seu pacote inclui" @update:model-value="patch({ includedTitle: writeText(modelValue.includedTitle, $event) })" />
        <EdList
          :items="included"
          :item-title="item => readText(item.title)"
          :new-item="newItem"
          add-label="Adicionar item"
          item-label="Item"
          @update:items="patch({ included: $event })"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.title)" label="Item" placeholder="Ex.: 7 pernoites em hotéis" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdText
              :model-value="readText(item.details)"
              label="Detalhes (opcional)"
              multiline
              hint="Um por linha. Aparecem como subitens, por exemplo as noites em cada cidade."
              @update:model-value="update({ details: writeText(item.details, $event) })"
            />
          </template>
        </EdList>
      </EdGroup>
      <EdGroup title="Não inclui" :count="countLabel(excluded.length)">
        <EdText :model-value="readText(modelValue.excludedTitle)" label="Título da lista" placeholder="Não inclui" @update:model-value="patch({ excludedTitle: writeText(modelValue.excludedTitle, $event) })" />
        <EdList
          :items="excluded"
          :item-title="item => readText(item.title)"
          :new-item="newItem"
          add-label="Adicionar item"
          item-label="Item"
          @update:items="patch({ excluded: $event })"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.title)" label="Item" placeholder="Ex.: Bilhete aéreo" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdText
              :model-value="readText(item.details)"
              label="Detalhes (opcional)"
              multiline
              hint="Um por linha."
              @update:model-value="update({ details: writeText(item.details, $event) })"
            />
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdAlign :value="modelValue" type="inclusions" @patch="patch" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" fallback="#FFFFFF" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { InclusionsSection } from "../../../../types/page";
import EdAlign from "../EdAlign.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdList from "../EdList.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: InclusionsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: InclusionsSection): void }>();
const { patch } = useDraft(props, emit);
const included = computed(() => props.modelValue.included || []);
const excluded = computed(() => props.modelValue.excluded || []);
const newItem = () => ({ title: "", details: "" });
const countLabel = (count: number) => `${count} ${count === 1 ? "item" : "itens"}`;
</script>
