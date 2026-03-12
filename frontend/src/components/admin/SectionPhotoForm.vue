<template>
  <div class="space-y-4">
    <div>
      <label class="text-sm font-semibold text-slate-600">Imagem</label>
      <p class="text-xs text-slate-500">Envie uma imagem em alta resolução (PNG ou JPG).</p>
      <ImageUploadField v-model="local.image" class="mt-2" />
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Layout</label>
      <div class="mt-2 grid gap-3 md:grid-cols-2">
        <label
          class="flex cursor-pointer flex-col gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition"
          :class="local.layout === 'card' ? 'border-brand bg-brand/5 text-brand' : 'border-slate-200 text-slate-600'"
        >
          <span class="flex items-center justify-between">
            <span>Card centralizado</span>
            <input type="radio" class="text-brand" value="card" v-model="local.layout" />
          </span>
          <span class="text-xs font-normal text-slate-500">A imagem fica dentro de um card com sombra.</span>
        </label>
        <label
          class="flex cursor-pointer flex-col gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition"
          :class="local.layout === 'full' ? 'border-brand bg-brand/5 text-brand' : 'border-slate-200 text-slate-600'"
        >
          <span class="flex items-center justify-between">
            <span>Tela cheia</span>
            <input type="radio" class="text-brand" value="full" v-model="local.layout" />
          </span>
          <span class="text-xs font-normal text-slate-500">A imagem ocupa a largura total, semelhante ao hero.</span>
        </label>
      </div>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">Texto alternativo (opcional)</label>
      <input
        v-model="local.altText"
        placeholder="Descreva brevemente a imagem"
        class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
      />
      <p class="mt-1 text-xs text-slate-500">IMPORTANTE para acessibilidade e SEO.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import type { PhotoSection } from "../../types/page";

const props = defineProps<{ modelValue: PhotoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PhotoSection): void }>();

const local = reactive<PhotoSection>({
  type: "photo",
  enabled: true,
  image: "",
  layout: "card",
  ...props.modelValue,
});

let syncing = false;
const syncFromProps = (value: PhotoSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "card";
  nextTick(() => {
    syncing = false;
  });
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
    emit("update:modelValue", value as PhotoSection);
  },
  { deep: true }
);
</script>
