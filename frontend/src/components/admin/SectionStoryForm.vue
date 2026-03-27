<template>
  <div class="space-y-3">
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Posição da imagem</label>
        <select v-model="local.imagePosition" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="right">Direita</option>
          <option value="left">Esquerda</option>
        </select>
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título</label>
        <input v-model="local.title" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Subtítulo</label>
        <RichTextEditor v-model="local.subtitle" placeholder="Conte a história da agência..." />
      </div>
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.ctaEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Inserir botão de CTA</label>
    </div>
    <div v-if="local.ctaEnabled" class="space-y-3">
      <CtaActionPicker
        v-model:mode="local.ctaMode"
        v-model:sectionId="local.ctaSectionId"
        :current-anchor="local.anchorId"
      />
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-sm font-semibold text-slate-600">Texto do CTA</label>
          <input v-model="local.ctaLabel" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
        <div v-if="local.ctaMode !== 'section'">
          <label class="text-sm font-semibold text-slate-600">Link do CTA</label>
          <input v-model="local.ctaLink" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
        </div>
      </div>
      <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        A cor do botão segue a opção global "Cor de botões e destaques" configurada no topo do editor.
      </div>
    </div>

    <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      Animacoes de fade-in e o brilho do botao de CTA sao aplicados automaticamente nesta secao.
    </div>

    <MultiImageUploadField
      v-model="local.images"
      label="Imagens"
      hint="A primeira imagem é destacada na seção; nas thumbs, o clique alterna a principal."
    />
    <div class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
      Layout definido automaticamente: 1 imagem exibe destaque único; 2 ou mais ativam galeria.
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="text-sm font-semibold text-slate-600">Vídeos do YouTube</label>
        <button type="button" class="text-sm font-semibold text-brand" @click="addVideoField">+ Adicionar vídeo</button>
      </div>
      <p class="text-xs text-slate-500">Cole links do YouTube ou iframes; exibimos sempre antes das imagens.</p>
      <div v-if="local.videoUrls?.length" class="space-y-2">
        <div v-for="(video, index) in local.videoUrls" :key="`video-${index}`" class="flex items-center gap-2">
          <input
            v-model="local.videoUrls[index]"
            placeholder="https://www.youtube.com/watch?v=..."
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          />
          <button type="button" class="text-sm font-semibold text-rose-500" @click="removeVideoField(index)">Remover</button>
        </div>
      </div>
      <div v-else class="rounded-lg border border-dashed border-slate-200 px-3 py-2 text-xs text-slate-500">
        Nenhum vídeo adicionado ainda.
      </div>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
      <input v-model="local.backgroundColor" placeholder="#e5eef9" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
    </div>
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.borderEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ativar borda destacada (texto em card)</label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import MultiImageUploadField from "./inputs/MultiImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { StorySection } from "../../types/page";

const props = defineProps<{ modelValue: StorySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: StorySection): void }>();
const headingDefaults = getSectionHeadingDefaults("story");

const normalizeVideoList = (section: StorySection) => {
  const list = Array.isArray(section.videoUrls) ? [...section.videoUrls] : [];
  if (!list.length && typeof section.videoUrl === "string" && section.videoUrl.trim().length > 0) {
    list.push(section.videoUrl);
  }
  return list;
};

const local = reactive<StorySection>({
  type: "story",
  layout: "single",
  enabled: true,
  images: [],
  videoUrls: normalizeVideoList(props.modelValue),
  ctaEnabled: true,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  ...props.modelValue,
  enableAnimation: true,
  ctaShimmer: true,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null
});
const countValidImages = (images?: string[]) =>
  Array.isArray(images) ? images.filter(img => typeof img === "string" && img.trim().length > 0).length : 0;
const countValidVideos = (videos?: string[]) =>
  Array.isArray(videos) ? videos.filter(video => typeof video === "string" && video.trim().length > 0).length : 0;
const determineLayoutFromMedia = () => (countValidImages(local.images) + countValidVideos(local.videoUrls) > 1 ? "gallery" : "single");
const applyAutomaticLayout = () => {
  const desired = determineLayoutFromMedia();
  if (local.layout !== desired) {
    local.layout = desired;
  }
};

let syncing = false;
const syncFromProps = (value: StorySection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.images = Array.isArray(value.images) ? [...value.images] : [];
  local.videoUrls = normalizeVideoList(value);
  local.videoUrl = local.videoUrls[0] || "";
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  local.enableAnimation = true;
  local.ctaShimmer = true;
  applyAutomaticLayout();
  nextTick(() => {
    syncing = false;
  });
};

const addVideoField = () => {
  if (!Array.isArray(local.videoUrls)) {
    local.videoUrls = [];
  }
  local.videoUrls.push("");
};

const removeVideoField = (index: number) => {
  if (!Array.isArray(local.videoUrls)) return;
  local.videoUrls = local.videoUrls.filter((_, i) => i !== index);
  local.videoUrl = local.videoUrls[0] || "";
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

watch(
  () => local.videoUrls,
  () => {
    if (syncing) return;
    local.videoUrl = Array.isArray(local.videoUrls) && local.videoUrls.length ? local.videoUrls[0] : "";
    applyAutomaticLayout();
  },
  { deep: true }
);

watch(
  () => local.images,
  () => {
    if (syncing) return;
    applyAutomaticLayout();
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as StorySection);
  },
  { deep: true }
);
</script>
