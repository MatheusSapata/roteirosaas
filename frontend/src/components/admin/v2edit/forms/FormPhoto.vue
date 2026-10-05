<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Foto">
        <ImageUploadField :model-value="modelValue.image || ''" label="Foto" hint="Ideal 2400 × 1350 px." @update:model-value="patch({ image: $event || '' })" />
        <EdText :model-value="altText" label="Legenda" hint="Também é lida por leitores de tela." @update:model-value="altText = $event" />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'full' ? 'full' : 'card'"
          :options="[
            { value: 'card', label: 'Card', desc: 'Com margens e cantos arredondados' },
            { value: 'full', label: 'Largura total', desc: 'De ponta a ponta da tela' }
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
import type { PhotoSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdLayouts from "../EdLayouts.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: PhotoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PhotoSection): void }>();
const { patch, text } = useDraft(props, emit);
const altText = text("altText");
</script>
