<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="banner_card" title-placeholder="Conte com especialistas para montar o seu roteiro" @patch="patch" />
      <EdGroup title="Mídia">
        <ImageUploadField :model-value="modelValue.backgroundImage || ''" label="Foto de fundo" hint="Ideal 2400 × 1350 px." layout="compact" @update:model-value="patch({ backgroundImage: $event || '' })" />
      </EdGroup>
      <EdButton :value="modelValue" placeholder="Falar com especialista" @patch="patch" />
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdLayouts
          :model-value="modelValue.layout === 'card' ? 'card' : 'shade'"
          :options="[
            { value: 'shade', label: 'Com sombra', desc: 'Texto direto na foto' },
            { value: 'card', label: 'Cartão', desc: 'Texto num cartão sobre a foto' }
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
import type { BannerCardSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdLayouts from "../EdLayouts.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: BannerCardSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BannerCardSection): void }>();
const { patch } = useDraft(props, emit);
</script>
