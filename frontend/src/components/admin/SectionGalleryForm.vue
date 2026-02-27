<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Galeria</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
    <MultiImageUploadField
      v-model="local.images"
      label="Imagens da galeria"
      hint="Envie quantas imagens quiser; a primeira define o destaque e as demais seguem o layout escolhido."
    />
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Layout</label>
        <select v-model="local.layout" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option value="mosaic">Mosaico</option>
          <option value="grid">Grade clean</option>
          <option value="strip">Faixas</option>
        </select>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">Cor de fundo</label>
        <select v-model="local.backgroundColor" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2">
          <option v-for="option in colorOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>
    <div>
      <div class="flex items-center gap-2">
        <input type="checkbox" v-model="local.fullWidth" class="h-4 w-4" />
        <label class="text-sm font-semibold text-slate-600">Ocupar largura total</label>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import MultiImageUploadField from "./inputs/MultiImageUploadField.vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { GallerySection } from "../../types/page";

const props = defineProps<{ modelValue: GallerySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: GallerySection): void }>();
const headingDefaults = getSectionHeadingDefaults("gallery");

const local = reactive<GallerySection>({
  layout: "mosaic",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  ...props.modelValue,
  images: Array.isArray(props.modelValue.images) ? [...props.modelValue.images] : []
});
let syncing = false;
const syncFromProps = (value: GallerySection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "mosaic";
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.images = Array.isArray(value.images) ? [...value.images] : [];
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
const colorOptions = [
  { label: "Branco", value: "#ffffff" },
  { label: "Cinza suave", value: "#f8fafc" },
  { label: "Azul claro", value: "#e0f2fe" },
  { label: "Marfim", value: "#fef3c7" },
  { label: "Rosa claro", value: "#fdf2f8" },
  { label: "Verde menta", value: "#ecfdf3" },
  { label: "Lilás", value: "#f5f3ff" },
  { label: "Turquesa", value: "#e0f7f7" },
  { label: "Cinza médio", value: "#e2e8f0" },
  { label: "Grafite", value: "#0f172a" }
];

watch(
  () => ({ ...local, images: [...local.images] }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as GallerySection);
  },
  { deep: true }
);
</script>
