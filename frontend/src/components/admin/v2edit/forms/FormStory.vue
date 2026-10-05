<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="headingValue" type="story" title-placeholder="Sete dias entre lagos e picos" @patch="patchHeading" />
      <EdGroup title="Fotos" :count="`${images.length} de 10`">
        <MultiImageUploadField :model-value="images" label="Fotos" hint="Até 10 fotos." @update:model-value="patch({ images: $event.slice(0, 10) })" />
      </EdGroup>
      <EdButton :value="modelValue" placeholder="Ver o roteiro" @patch="patch" />
    </template>
    <template #look>
      <EdGroup title="Fotos">
        <EdSeg
          :model-value="modelValue.imagePosition === 'left' ? 'left' : 'right'"
          label="Posição das fotos"
          :options="[
            { value: 'left', label: 'Esquerda' },
            { value: 'right', label: 'Direita' }
          ]"
          @update:model-value="patch({ imagePosition: $event })"
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
import type { StorySection } from "../../../../types/page";
import MultiImageUploadField from "../../inputs/MultiImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdSeg from "../EdSeg.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: StorySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: StorySection): void }>();
const { patch } = useDraft(props, emit);
const images = computed(() => props.modelValue.images || []);
// A seção antiga guardava o selo em "badge"; o visual novo lê "headingLabel" primeiro.
const headingValue = computed(() => ({ ...props.modelValue, headingLabel: props.modelValue.headingLabel ?? props.modelValue.badge }));
const patchHeading = (changes: Record<string, any>) =>
  patch("headingLabel" in changes ? { ...changes, badge: changes.headingLabel } : changes);
</script>
