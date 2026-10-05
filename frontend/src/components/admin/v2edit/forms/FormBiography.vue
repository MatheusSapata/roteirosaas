<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Capa">
        <ImageUploadField :model-value="modelValue.image || ''" label="Foto do computador" hint="Ideal 2400 × 1000 px." @update:model-value="patch({ image: $event || '' })" />
        <ImageUploadField :model-value="modelValue.mobileImage || ''" label="Foto do celular" hint="Opcional. Sem ela, usa a do computador." layout="row" @update:model-value="patch({ mobileImage: $event || '' })" />
        <EdText :model-value="title" label="Título" placeholder="Como montamos um roteiro" @update:model-value="title = $event" />
      </EdGroup>
      <EdGroup title="Texto">
        <EdRich :model-value="body" label="Texto formatado" hint="Negrito, itálico, listas e links. Alguns clientes usam como um post de blog." @update:model-value="body = $event" />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Capa">
        <EdSeg
          :model-value="overlay"
          label="Escurecer a foto"
          :options="[
            { value: 0.25, label: 'Pouco' },
            { value: 0.45, label: 'Médio' },
            { value: 0.65, label: 'Muito' }
          ]"
          @update:model-value="patch({ overlayOpacity: $event })"
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
import type { BiographySection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdRich from "../EdRich.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: BiographySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BiographySection): void }>();
const { patch, text } = useDraft(props, emit);
const title = text("title");
const body = text("text");
// Arredonda para a opção mais próxima, já que páginas antigas podem ter outro valor.
const overlay = computed(() => {
  const value = typeof props.modelValue.overlayOpacity === "number" ? props.modelValue.overlayOpacity : 0.45;
  return [0.25, 0.45, 0.65].reduce((best, option) => (Math.abs(option - value) < Math.abs(best - value) ? option : best), 0.45);
});
</script>
