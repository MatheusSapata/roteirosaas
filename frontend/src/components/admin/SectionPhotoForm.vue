<template>
  <div class="space-y-4">
    <div>
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.image.label }}</label>
      <p class="text-xs text-slate-500">{{ viewCopy.image.helper }}</p>
      <ImageUploadField v-model="local.image" class="mt-2" />
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.layout.label }}</label>
      <div class="mt-2 grid gap-3 md:grid-cols-2">
        <label
          class="flex cursor-pointer flex-col gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition"
          :class="local.layout === 'card' ? 'border-brand bg-brand/5 text-brand' : 'border-slate-200 text-slate-600'"
        >
          <span class="flex items-center justify-between">
            <span>{{ viewCopy.layout.cardLabel }}</span>
            <input type="radio" class="text-brand" value="card" v-model="local.layout" />
          </span>
          <span class="text-xs font-normal text-slate-500">{{ viewCopy.layout.cardHelper }}</span>
        </label>
        <label
          class="flex cursor-pointer flex-col gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition"
          :class="local.layout === 'full' ? 'border-brand bg-brand/5 text-brand' : 'border-slate-200 text-slate-600'"
        >
          <span class="flex items-center justify-between">
            <span>{{ viewCopy.layout.fullLabel }}</span>
            <input type="radio" class="text-brand" value="full" v-model="local.layout" />
          </span>
          <span class="text-xs font-normal text-slate-500">{{ viewCopy.layout.fullHelper }}</span>
        </label>
      </div>
    </div>

    <div v-if="local.layout === 'card'">
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.background.label }}</label>
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
          {{ viewCopy.background.useAlternate }}
        </button>
      </div>
      <p class="mt-1 text-xs text-slate-500">{{ viewCopy.background.helper }}</p>
    </div>

    <div>
      <label class="text-sm font-semibold text-slate-600">{{ viewCopy.altText.label }}</label>
      <input
        v-model="local.altText"
        :placeholder="viewCopy.altText.placeholder"
        class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
      />
      <p class="mt-1 text-xs text-slate-500">{{ viewCopy.altText.helper }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import type { PhotoSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: PhotoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PhotoSection): void }>();
const t = createAdminLocalizer();

const viewCopy = {
  image: {
    label: t({ pt: "Imagem", es: "Imagen" }),
    helper: t({ pt: "Envie uma imagem em alta resolução (PNG ou JPG).", es: "Sube una imagen en alta resolución (PNG o JPG)." })
  },
  layout: {
    label: t({ pt: "Layout", es: "Layout" }),
    cardLabel: t({ pt: "Card centralizado", es: "Card centrado" }),
    cardHelper: t({ pt: "A imagem fica dentro de um card com sombra.", es: "La imagen queda dentro de un card con sombra." }),
    fullLabel: t({ pt: "Tela cheia", es: "Pantalla completa" }),
    fullHelper: t({ pt: "A imagem ocupa a largura total, semelhante ao hero.", es: "La imagen ocupa todo el ancho, similar al hero." })
  },
  background: {
    label: t({ pt: "Cor de fundo (opcional)", es: "Color de fondo (opcional)" }),
    useAlternate: t({ pt: "Usar alternância", es: "Usar alternancia" }),
    helper: t({ pt: "Deixe em branco para seguir as cores configuradas na página.", es: "Déjalo en blanco para seguir los colores configurados en la página." })
  },
  altText: {
    label: t({ pt: "Texto alternativo (opcional)", es: "Texto alternativo (opcional)" }),
    placeholder: t({ pt: "Descreva brevemente a imagem", es: "Describe brevemente la imagen" }),
    helper: t({ pt: "Importante para acessibilidade e SEO.", es: "Importante para accesibilidad y SEO." })
  }
};

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
