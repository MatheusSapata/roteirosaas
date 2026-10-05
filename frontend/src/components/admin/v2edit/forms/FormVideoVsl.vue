<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Texto">
        <EdText :model-value="title" label="Título" placeholder="Assista antes de continuar" @update:model-value="title = $event" />
        <EdText :model-value="subtitle" label="Texto" placeholder="Liga o som. São 4 minutos." @update:model-value="subtitle = $event" />
      </EdGroup>
      <EdGroup title="Vídeo">
        <EdText :model-value="modelValue.videoUrl || ''" label="Link do vídeo" type="url" hint="YouTube, Vimeo ou Panda." @update:model-value="patch({ videoUrl: $event })" />
        <ImageUploadField :model-value="modelValue.thumbnailUrl || ''" label="Capa do vídeo" hint="Opcional." layout="row" @update:model-value="patch({ thumbnailUrl: $event || '' })" />
      </EdGroup>
      <EdButton
        :value="modelValue"
        :keys="{ label: 'ctaLabel', link: 'ctaLink' }"
        link-only
        placeholder="Quero minha vaga"
        @patch="changes => patch({ ...changes, ctaDestinationMode: 'external' })"
      />
      <EdGroup title="Liberação do botão" extra>
        <EdToggle
          :model-value="(modelValue.unlockAfterSeconds || 0) > 0"
          label="Liberar só no momento da oferta"
          hint="Até lá, o visitante vê apenas o vídeo."
          @update:model-value="patch({ unlockAfterSeconds: $event ? lastSeconds : 0 })"
        />
        <EdSeg
          :model-value="modelValue.unlockAction || 'reveal_page'"
          label="O que aparece"
          :options="[
            { value: 'both', label: 'Botão e página' },
            { value: 'show_button', label: 'Só o botão' },
            { value: 'reveal_page', label: 'Só a página' }
          ]"
          @update:model-value="patch({ unlockAction: $event })"
        />
        <div v-if="(modelValue.unlockAfterSeconds || 0) > 0" class="ved-pair">
          <EdText :model-value="minutes" label="Minutos" type="number" min="0" @update:model-value="setTime(Number($event) || 0, seconds)" />
          <EdText :model-value="seconds" label="Segundos" type="number" min="0" @update:model-value="setTime(minutes, Number($event) || 0)" />
        </div>
        <EdToggle :model-value="modelValue.progressBarEnabled !== false" label="Barra de progresso" @update:model-value="patch({ progressBarEnabled: $event })" />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Formato do vídeo">
        <EdSeg
          :model-value="modelValue.videoAspectRatio || 'horizontal'"
          :options="[
            { value: 'horizontal', label: 'Horizontal' },
            { value: 'vertical', label: 'Vertical' },
            { value: 'square', label: 'Quadrado' }
          ]"
          @update:model-value="patch({ videoAspectRatio: $event })"
        />
      </EdGroup>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" @change="patch" fallback="#0E1A15" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { VideoVslSection } from "../../../../types/page";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: VideoVslSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: VideoVslSection): void }>();
const { patch, text } = useDraft(props, emit);
const title = text("title");
const subtitle = text("subtitle");

const total = computed(() => Math.max(0, Math.round(props.modelValue.unlockAfterSeconds || 0)));
const minutes = computed(() => Math.floor(total.value / 60));
const seconds = computed(() => total.value % 60);
// Lembra o último tempo para religar sem perder o valor.
const lastSeconds = ref(total.value || 60);
watch(total, value => {
  if (value > 0) lastSeconds.value = value;
});
const setTime = (min: number, sec: number) => patch({ unlockAfterSeconds: Math.max(1, Math.round(min) * 60 + Math.round(sec)) });
</script>
