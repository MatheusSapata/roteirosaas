<template>
  <div class="space-y-3">
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Destaque</label>
        <input v-model="local.badge" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Layout</label>
        <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="single">Imagem única + texto</option>
          <option value="gallery">Texto + galeria com thumbs</option>
        </select>
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
        <input v-model="local.subtitle" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.ctaEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Inserir botČœo de CTA</label>
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
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="text-sm font-semibold text-slate-600">Cor do botão (CTA)</label>
          <div class="mt-1 flex items-center gap-2">
            <input type="color" v-model="local.ctaColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
            <input v-model="local.ctaColor" placeholder="#0ea5e9" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>
        </div>
      </div>
    </div>

    <MultiImageUploadField
      v-model="local.images"
      label="Imagens"
      hint="A primeira imagem é destacada na seção; nas thumbs, o clique alterna a principal."
    />

    <div>
      <label class="text-sm font-semibold text-slate-600">Vídeo (YouTube opcional)</label>
      <input v-model="local.videoUrl" placeholder="Link ou iframe do YouTube" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
      <p class="mt-1 text-xs text-slate-500">Se preencher, substitui a imagem principal pelo vídeo.</p>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
      <input v-model="local.backgroundColor" placeholder="#e5eef9" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ativar seção</label>
    </div>
    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="local.borderEnabled" class="h-4 w-4" />
      <label class="text-sm font-semibold text-slate-600">Ativar borda destacada (texto em card)</label>
    </div>
    <div v-if="local.borderEnabled">
      <label class="text-sm font-semibold text-slate-600">Cor da borda</label>
      <div class="mt-1 flex items-center gap-2">
        <input type="color" v-model="local.borderColor" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
        <input v-model="local.borderColor" placeholder="#0ea5e9" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
      </div>
      <p class="mt-1 text-xs text-slate-500">Usa por padrão a cor do CTA, mas pode ser personalizada.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import MultiImageUploadField from "./inputs/MultiImageUploadField.vue";
import CtaActionPicker from "./inputs/CtaActionPicker.vue";
import type { StorySection } from "../../types/page";

const props = defineProps<{ modelValue: StorySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: StorySection): void }>();

const local = reactive<StorySection>({
  type: "story",
  layout: "single",
  enabled: true,
  images: [],
  ctaEnabled: true,
  ...props.modelValue,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null
});
let syncing = false;
const syncFromProps = (value: StorySection) => {
  syncing = true;
  Object.assign(local, value);
  local.images = Array.isArray(value.images) ? [...value.images] : [];
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  syncing = false;
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
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as StorySection);
  },
  { deep: true }
);
</script>
