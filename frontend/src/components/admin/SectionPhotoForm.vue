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

    <div v-if="local.layout === 'card'">
      <label class="text-sm font-semibold text-slate-600">Cor de fundo (opcional)</label>
      <div class="mt-2 flex flex-wrap items-center gap-3">
        <input
          type="color"
          v-model="colorPickerValue"
          class="h-10 w-10 cursor-pointer rounded border border-slate-200 bg-white"
        />
        <input
          v-model="customBackground"
          placeholder="#f4f7ff"
          class="w-full flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
        />
        <button
          type="button"
          class="rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          @click="customBackground = ''"
        >
          Usar alternância
        </button>
      </div>
      <p class="mt-1 text-xs text-slate-500">Deixe em branco para seguir as cores configuradas na página.</p>
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
import { computed, nextTick, reactive, ref, watch } from "vue";
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
  backgroundColor: props.modelValue.backgroundColor,
});

let syncing = false;
const customBackground = ref(props.modelValue.backgroundColor || "");
const colorPickerValue = computed({
  get: () => customBackground.value || "#f4f7ff",
  set: value => {
    customBackground.value = value;
  },
});

const syncFromProps = (value: PhotoSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "card";
  customBackground.value = value.backgroundColor || "";
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
  () => customBackground.value,
  value => {
    if (syncing) return;
    const sanitized = value.trim();
    local.backgroundColor = sanitized ? sanitized : undefined;
  }
);

watch(
  () => local.layout,
  layout => {
    if (layout === "full") {
      customBackground.value = "";
      local.backgroundColor = undefined;
    }
  }
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
