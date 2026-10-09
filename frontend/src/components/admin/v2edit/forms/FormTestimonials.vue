<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="testimonials" title-placeholder="Quem já foi conta" @patch="patch" />
      <EdGroup title="Depoimentos" :count="`${items.length} ${items.length === 1 ? 'relato' : 'relatos'}`">
        <EdList
          :items="items"
          :item-title="item => readText(item.name)"
          :new-item="() => ({ name: '', role: '', text: '', avatar: '' })"
          add-label="Adicionar depoimento"
          item-label="Depoimento"
          @update:items="patch({ items: $event })"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.name)" label="Nome" @update:model-value="update({ name: writeText(item.name, $event) })" />
            <EdText :model-value="readText(item.role)" label="Saída ou detalhe" placeholder="Saída de junho de 2025" @update:model-value="update({ role: writeText(item.role, $event) })" />
            <EdText :model-value="readText(item.text)" label="Depoimento" multiline @update:model-value="update({ text: writeText(item.text, $event) })" />
            <ImageUploadField :model-value="item.avatar || ''" label="Foto" hint="Opcional. Sem foto, aparecem as iniciais do nome." layout="compact" @update:model-value="update({ avatar: $event || '' })" />
          </template>
        </EdList>
      </EdGroup>
      <EdButton :value="modelValue" toggle-label="Mostrar botão abaixo dos depoimentos" placeholder="Quero viver isso também" @patch="patch" />
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'highlight' ? 'highlight' : 'cards'"
          :options="[
            { value: 'cards', label: 'Cartões', desc: 'Lado a lado' },
            { value: 'highlight', label: 'Destaque', desc: 'Um relato grande por vez' }
          ]"
          @update:model-value="patch({ layout: $event })"
        />
        <EdAlign :value="modelValue" type="testimonials" @patch="patch" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" fallback="#F2F4F1" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { TestimonialsSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdAlign from "../EdAlign.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdLayouts from "../EdLayouts.vue";
import EdList from "../EdList.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: TestimonialsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: TestimonialsSection): void }>();
const { patch } = useDraft(props, emit);
const items = computed(() => props.modelValue.items || []);
</script>
