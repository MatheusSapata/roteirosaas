<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="itinerary" title-placeholder="Dia a dia da viagem" @patch="patch" />
      <EdGroup title="Datas">
        <EdText
          :model-value="modelValue.startDate || ''"
          label="Primeiro dia"
          type="date"
          hint="Vazio: usa a data de saída da Capa. Os dias seguintes contam a partir daqui; dá para escolher a data de um dia abaixo."
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
          <template #default="{ item, update, index }">
            <EdText :model-value="readText(item.title)" label="Título" placeholder="Chegada e traslado ao hotel" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdText
              :model-value="item.date || ''"
              label="Data do dia"
              type="date"
              :hint="item.date ? 'Os dias seguintes continuam a partir desta data.' : autoDateHint(index)"
              @update:model-value="update({ date: $event || undefined })"
            />
            <EdRich :model-value="readText(item.description)" label="Texto" @update:model-value="update({ description: writeText(item.description, $event) })" />
            <ImageUploadField :model-value="item.image || ''" label="Foto do dia" hint="Opcional." layout="compact" @update:model-value="update({ image: $event || '' })" />
          </template>
        </EdList>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'cards' || modelValue.layout === 'steps' ? 'cards' : modelValue.layout === 'journey' ? 'journey' : 'timeline'"
          :options="[
            { value: 'journey', label: 'Jornada', desc: 'Cartões com calendário que abrem e fecham' },
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
import { addDays, formatDayMonth, parseTripDate } from "../../../../utils/tripDates";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const { patch } = useDraft(props, emit);
const days = computed(() => props.modelValue.days || []);
const newId = () => `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
const newDay = (): ItineraryDay => ({ id: newId(), day: "", title: "", description: "", image: "" });
// O rótulo automático "Dia N" segue a posição ao reordenar; rótulos escritos à mão ficam como estão.
const isAutoLabel = (value: ItineraryDay["day"]) => !readText(value).trim() || /^(dia|día)\s*\d+$/i.test(readText(value).trim());
// Mesma conta da página: data própria do dia, senão a do dia anterior + 1, senão o início + posição.
const autoDates = computed(() => {
  const start = parseTripDate(props.modelValue.startDate);
  let previous: Date | null = null;
  return days.value.map((day, idx) => {
    const date = parseTripDate(day.date) || (previous ? addDays(previous, 1) : start ? addDays(start, idx) : null);
    previous = date;
    return date;
  });
});
const autoDateHint = (index: number) => {
  const date = autoDates.value[index];
  return date ? `Vazio: ${formatDayMonth(date)}, seguindo a sequência.` : "Vazio: segue a sequência do roteiro.";
};
const setDays = (next: ItineraryDay[]) =>
  patch({ days: next.map((day, index) => (isAutoLabel(day.day) ? { ...day, day: `Dia ${index + 1}` } : day)) });
</script>
