<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Texto">
        <EdText :model-value="label" label="Título" placeholder="Restam 6 vagas para junho" @update:model-value="label = $event" />
        <EdRich :model-value="description" label="Texto" hint="Opcional." @update:model-value="description = $event" />
      </EdGroup>
      <EdButton
        :value="modelValue"
        :keys="{ enabled: 'ctaEnabled', label: 'ctaText', mode: 'ctaMode', link: 'link', section: 'ctaSectionId' }"
        placeholder="Reservar pelo WhatsApp"
        @patch="patch"
      />
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="isCard ? 'card' : 'bar'"
          :options="[
            { value: 'bar', label: 'Faixa', desc: 'Texto e botão numa faixa' },
            { value: 'card', label: 'Cartão com foto', desc: 'Foto de fundo e texto por cima' }
          ]"
          @update:model-value="patch({ layout: $event })"
        />
        <ImageUploadField v-if="isCard" :model-value="modelValue.backgroundImage || ''" label="Foto do cartão" @update:model-value="patch({ backgroundImage: $event || '' })" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CtaSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdLayouts from "../EdLayouts.vue";
import EdRich from "../EdRich.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: CtaSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CtaSection): void }>();
const { patch, text } = useDraft(props, emit);
const label = text("label");
const description = text("description");
const isCard = computed(() => props.modelValue.layout === "card" || props.modelValue.layout === "split");
</script>
