<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="featured_video" title-placeholder="A viagem em 2 minutos" @patch="patch" />
      <EdGroup title="Vídeo">
        <EdText :model-value="modelValue.videoUrl || ''" label="Link do vídeo" type="url" hint="YouTube ou Vimeo." placeholder="https://youtube.com/watch?v=…" @update:model-value="patch({ videoUrl: $event })" />
      </EdGroup>
      <EdButton :value="modelValue" placeholder="Falar com um especialista" @patch="patch" />
    </template>
    <template #look>
      <EdGroup title="Layout">
        <EdAlign :value="modelValue" type="featured_video" @patch="patch" />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import type { FeaturedVideoSection } from "../../../../types/page";
import EdAlign from "../EdAlign.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdHeading from "../EdHeading.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: FeaturedVideoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FeaturedVideoSection): void }>();
const { patch } = useDraft(props, emit);
</script>
