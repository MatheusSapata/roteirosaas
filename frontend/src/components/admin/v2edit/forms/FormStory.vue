<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="headingValue" type="story" title-placeholder="Sete dias entre lagos e picos" @patch="patchHeading" />
      <EdGroup title="Fotos" :count="`${images.length} de 10`">
        <MultiImageUploadField :model-value="images" label="Fotos" hint="Até 10 fotos." @update:model-value="patch({ images: $event.slice(0, 10) })" />
      </EdGroup>
      <EdGroup title="Vídeos" :count="`${videos.length} de ${MAX_VIDEOS}`">
        <p class="ved-hint">Links do YouTube ou do Vimeo. Os vídeos aparecem antes das fotos, na ordem da lista.</p>
        <EdList
          :items="videos"
          :item-title="(item, index) => videoTitle(item.url, index)"
          :new-item="() => ({ url: '' })"
          add-label="Adicionar vídeo"
          item-label="Vídeo"
          :max="MAX_VIDEOS"
          @update:items="saveVideos"
        >
          <template #default="{ item, update }">
            <EdText :model-value="item.url" label="Link do vídeo" type="url" placeholder="https://youtube.com/watch?v=…" @update:model-value="update({ url: $event })" />
            <p v-if="item.url.trim() && !toVideoEmbedUrl(item.url)" class="ved-info ved-warn">Este link não é do YouTube nem do Vimeo e não vai aparecer na página.</p>
          </template>
        </EdList>
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
import EdList from "../EdList.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";
import { extractYoutubeId, toVideoEmbedUrl } from "../../../../utils/video";

const props = defineProps<{ modelValue: StorySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: StorySection): void }>();
const { patch } = useDraft(props, emit);
const images = computed(() => props.modelValue.images || []);

// Vídeos: a lista fica em "videoUrls"; seções antigas podem ter só "videoUrl" (um vídeo).
// Ao salvar, o "videoUrl" é zerado para o vídeo antigo não voltar depois de removido.
const MAX_VIDEOS = 10;
const videos = computed(() => {
  const list = Array.isArray(props.modelValue.videoUrls) ? props.modelValue.videoUrls.filter(url => typeof url === "string") : [];
  const legacy = (props.modelValue.videoUrl || "").trim();
  if (legacy && !list.some(url => url.trim() === legacy)) list.unshift(legacy);
  return list.map(url => ({ url }));
});
const saveVideos = (items: { url: string }[]) => patch({ videoUrls: items.map(item => item.url), videoUrl: "" });
const videoTitle = (url: string, index: number) => {
  const raw = (url || "").trim();
  if (!raw) return "";
  if (extractYoutubeId(raw)) return `YouTube · vídeo ${index + 1}`;
  if (/vimeo\.com/i.test(raw)) return `Vimeo · vídeo ${index + 1}`;
  return `Link inválido · vídeo ${index + 1}`;
};
// A seção antiga guardava o selo em "badge"; o visual novo lê "headingLabel" primeiro.
const headingValue = computed(() => ({ ...props.modelValue, headingLabel: props.modelValue.headingLabel ?? props.modelValue.badge }));
const patchHeading = (changes: Record<string, any>) =>
  patch("headingLabel" in changes ? { ...changes, badge: changes.headingLabel } : changes);
</script>
