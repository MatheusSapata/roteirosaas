<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="reasons" title-placeholder="Por que viajar com a gente" @patch="patch" />
      <EdGroup title="Itens" :count="`${items.length} ${items.length === 1 ? 'item' : 'itens'}`">
        <EdList
          :items="items"
          :item-title="item => readText(item.title)"
          :new-item="() => ({ icon: '', title: '', description: '' })"
          add-label="Adicionar item"
          item-label="Item"
          @update:items="patch({ items: $event })"
        >
          <template #default="{ item, update }">
            <div class="ved-field">
              <span class="ved-label">Ícone</span>
              <TravelIconPicker :model-value="item.icon || ''" @update:model-value="update({ icon: $event })" />
            </div>
            <EdText :model-value="readText(item.title)" label="Título" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdRich :model-value="readText(item.description)" label="Texto" @update:model-value="update({ description: writeText(item.description, $event) })" />
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" fallback="#F2F4F1" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ReasonsSection } from "../../../../types/page";
import TravelIconPicker from "../../inputs/TravelIconPicker.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdList from "../EdList.vue";
import EdRich from "../EdRich.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: ReasonsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ReasonsSection): void }>();
const { patch } = useDraft(props, emit);
const items = computed(() => props.modelValue.items || []);
</script>
