<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="itinerary" title-placeholder="Dia a dia da viagem" @patch="patch" />
      <EdGroup title="Datas">
        <EdText
          :model-value="modelValue.startDate || ''"
          label="Primeiro dia"
          type="date"
          hint="Vazio: usa a data de saída da Capa. As datas de cada dia são calculadas."
          @update:model-value="patch({ startDate: $event })"
        />
      </EdGroup>
      <EdGroup title="Dias" :count="`${days.length} ${days.length === 1 ? 'dia' : 'dias'}`">
        <EdList
          :items="days"
          :item-title="(day, index) => `${index + 1}. ${readText(day.title)}`"
          :new-item="newDay"
          add-label="Adicionar dia"
          item-label="Dia"
          @update:items="setDays"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.title)" label="Título" placeholder="Chegada e traslado ao hotel" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdRich :model-value="readText(item.description)" label="Texto" @update:model-value="update({ description: writeText(item.description, $event) })" />
            <ImageUploadField :model-value="item.image || ''" label="Foto do dia" hint="Opcional." layout="row" @update:model-value="update({ image: $event || '' })" />
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'cards' || modelValue.layout === 'steps' ? 'cards' : 'timeline'"
          :options="[
            { value: 'timeline', label: 'Linha do tempo', desc: 'Dias que abrem e fecham' },
            { value: 'cards', label: 'Cartões', desc: 'Um cartão com foto por dia' }
          ]"
          @update:model-value="patch({ layout: $event })"
        />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ItineraryDay, ItinerarySection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdLayouts from "../EdLayouts.vue";
import EdList from "../EdList.vue";
import EdRich from "../EdRich.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const { patch } = useDraft(props, emit);
const days = computed(() => props.modelValue.days || []);
const newId = () => `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
const newDay = (): ItineraryDay => ({ id: newId(), day: "", title: "", description: "", image: "" });
// O rótulo automático "Dia N" segue a posição ao reordenar; rótulos escritos à mão ficam como estão.
const isAutoLabel = (value: ItineraryDay["day"]) => !readText(value).trim() || /^(dia|día)\s*\d+$/i.test(readText(value).trim());
const setDays = (next: ItineraryDay[]) =>
  patch({ days: next.map((day, index) => (isAutoLabel(day.day) ? { ...day, day: `Dia ${index + 1}` } : day)) });
</script>
