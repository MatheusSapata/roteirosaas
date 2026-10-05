<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Texto">
        <EdText :model-value="label" label="Texto principal" placeholder="Garanta sua vaga com 10% de desconto" @update:model-value="label = $event" />
      </EdGroup>
      <EdGroup title="Prazo">
        <EdSeg
          :model-value="mode"
          label="Tipo de contagem"
          :options="[
            { value: 'fixed', label: 'Data fixa' },
            { value: 'session', label: 'Por visitante' }
          ]"
          @update:model-value="patch({ countdownMode: $event })"
        />
        <EdText v-if="mode === 'fixed'" :model-value="modelValue.targetDate || ''" label="Termina em" type="datetime-local" @update:model-value="patch({ targetDate: $event })" />
        <div v-else class="ved-pair">
          <EdText :model-value="modelValue.sessionDuration ?? 15" label="Duração" type="number" min="1" @update:model-value="patch({ sessionDuration: Math.max(1, Number($event) || 1) })" />
          <label class="ved-field">
            <span class="ved-label">Unidade</span>
            <select class="ved-select" :value="modelValue.sessionUnit || 'minutes'" @change="patch({ sessionUnit: ($event.target as HTMLSelectElement).value })">
              <option value="minutes">Minutos</option>
              <option value="hours">Horas</option>
              <option value="days">Dias</option>
            </select>
          </label>
        </div>
        <p class="ved-info">
          {{ mode === "fixed" ? "Quando o prazo acaba, a seção some da página." : "Cada visitante vê o prazo começar quando abre a página." }}
        </p>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'bar' ? 'bar' : 'flip'"
          :options="[
            { value: 'flip', label: 'Cartões', desc: 'Números grandes em cartões' },
            { value: 'bar', label: 'Barra', desc: 'Faixa fina com o prazo' }
          ]"
          @update:model-value="patch({ layout: $event })"
        />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" @change="patch" :fallback="design.accent" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CountdownSection } from "../../../../types/page";
import { usePageDesignContext } from "../../../public/v2/designContext";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdLayouts from "../EdLayouts.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: CountdownSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CountdownSection): void }>();
const { patch, text } = useDraft(props, emit);
const label = text("label");
const mode = computed(() => props.modelValue.countdownMode || "fixed");
const design = usePageDesignContext();
</script>
