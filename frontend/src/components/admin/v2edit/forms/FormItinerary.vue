<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="itinerary" title-placeholder="Dia a dia da viagem" @patch="patch" />
      <EdGroup title="Cronograma" :count="`${days.length} ${days.length === 1 ? 'etapa' : 'etapas'}`">
        <EdList
          :items="days"
          :item-title="(day, index) => `${index + 1}. ${readText(day.title)}`"
          :new-item="newDay"
          add-label="Adicionar etapa"
          item-label="Etapa"
          @update:items="setDays"
        >
          <template #default="{ item, update, index }">
            <EdText
              :model-value="partOf(index, 'badge')"
              label="Selo (faixa de cima)"
              placeholder="Dia 1"
              hint="Apague para o calendário ficar de uma cor só."
              @update:model-value="update({ badge: writeText(item.badge, $event) })"
            />
            <EdText
              :model-value="partOf(index, 'number')"
              label="Número grande"
              placeholder="12"
              hint="Pode ser a data ou só o número da etapa."
              @update:model-value="update({ number: writeText(item.number, $event) })"
            />
            <EdText
              :model-value="partOf(index, 'note')"
              label="Texto embaixo do número"
              placeholder="Fev"
              hint="Opcional. Apague para ficar só o número."
              @update:model-value="update({ numberNote: writeText(item.numberNote, $event) })"
            />
            <EdText
              :model-value="partOf(index, 'kicker')"
              label="Texto acima do título"
              placeholder="Quinta-feira"
              @update:model-value="update({ kicker: writeText(item.kicker, $event) })"
            />
            <EdText :model-value="readText(item.title)" label="Título" placeholder="Chegada e traslado ao hotel" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <EdRich :model-value="readText(item.description)" label="Descrição" @update:model-value="update({ description: writeText(item.description, $event) })" />
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
        <EdAlign :value="modelValue" type="itinerary" @patch="patch" />
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
import { itineraryDayParts } from "../../../../utils/itineraryDay";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const { patch } = useDraft(props, emit);
const days = computed(() => props.modelValue.days || []);
const newId = () => `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
const newDay = (): ItineraryDay => ({ id: newId(), day: "", title: "", description: "", image: "" });
// O rótulo automático "Dia N" segue a posição ao reordenar; rótulos escritos à mão ficam como estão.
const isAutoLabel = (value: ItineraryDay["day"]) => !readText(value).trim() || /^(dia|día)\s*\d+$/i.test(readText(value).trim());
// Mesma conta da página: o que nunca foi escrito mostra o valor automático, e o que foi escrito vale como está.
const parts = computed(() => itineraryDayParts(props.modelValue, undefined, "Dia", "Dia", readText));
const partOf = (index: number, key: "badge" | "number" | "note" | "kicker") => parts.value[index]?.[key] ?? "";
const setDays = (next: ItineraryDay[]) =>
  patch({ days: next.map((day, index) => (isAutoLabel(day.day) ? { ...day, day: `Dia ${index + 1}` } : day)) });
</script>
