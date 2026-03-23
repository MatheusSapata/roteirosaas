<template>
  <div class="space-y-6">
    <div>
      <label class="text-sm font-semibold text-slate-600">Imagem de fundo</label>
      <p class="text-xs text-slate-500">
        Opcional. O título só aparece quando houver uma imagem carregada (recomendado 1920x640px).
      </p>
      <ImageUploadField
        v-model="local.image"
        class="mt-2"
        hint="Recomendado 1920x640px"
        :enable-crop="true"
        :crop-aspect="3"
        editor-title="Ajuste a imagem da biografia"
      />
    </div>

    <div class="grid gap-6 md:grid-cols-2">
      <div class="space-y-5">
        <div v-if="hasImage">
          <label class="text-sm font-semibold text-slate-600">Título</label>
          <input
            v-model="local.title"
            class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold uppercase tracking-wide"
            placeholder="BIOGRAFIA"
          />
          <p class="mt-1 text-xs text-slate-500">Use letras maiúsculas para reforçar o impacto visual.</p>
        </div>

        <div>
          <label class="text-sm font-semibold text-slate-600">Subtítulo / Texto abaixo</label>
          <RichTextEditor
            v-model="local.text"
            class="mt-2"
            placeholder="Conte a história da sua agência, bastidores e conquistas..."
          />
        </div>
      </div>

      <div class="space-y-5">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">Fonte do título (px)</label>
            <input
              type="number"
              min="24"
              max="160"
              step="2"
              v-model.number="local.titleFontSize"
              class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Fonte do texto (px)</label>
            <input
              type="number"
              min="14"
              max="48"
              step="1"
              v-model.number="local.textFontSize"
              class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">Cor do título</label>
            <div class="mt-2 flex items-center gap-3">
              <input type="color" v-model="titleColor" class="h-10 w-10 cursor-pointer rounded border border-slate-200" />
              <input
                v-model="local.titleColor"
                placeholder="#ffffff"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Cor do texto</label>
            <div class="mt-2 flex items-center gap-3">
              <input type="color" v-model="textColor" class="h-10 w-10 cursor-pointer rounded border border-slate-200" />
              <input
                v-model="local.textColor"
                placeholder="#0f172a"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>
        </div>

        <div>
          <label class="text-sm font-semibold text-slate-600">Intensidade da sobreposição</label>
          <input
            type="range"
            min="0"
            max="0.85"
            step="0.05"
            v-model.number="overlay"
            class="mt-2 w-full"
          />
          <p class="mt-1 text-xs text-slate-500">Escurece a foto para garantir que o título fique legível.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import type { BiographySection } from "../../types/page";

const props = defineProps<{ modelValue: BiographySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BiographySection): void }>();

const local = reactive<BiographySection>({
  type: "biography",
  enabled: true,
  fullWidth: true,
  title: "BIOGRAFIA",
  text:
    "Use esta seção para compartilhar a história da sua agência, bastidores e fatos que criam conexão com o visitante.",
  overlayOpacity: 0.45,
  titleColor: "#ffffff",
  textColor: "#0f172a",
  titleFontSize: 72,
  textFontSize: 18,
  ...props.modelValue
});

const clampNumber = (value: number | undefined, fallback: number, min: number, max: number) => {
  if (typeof value !== "number" || Number.isNaN(value)) return fallback;
  return Math.min(Math.max(value, min), max);
};

const titleColor = computed({
  get: () => local.titleColor || "#ffffff",
  set: value => (local.titleColor = value)
});

const textColor = computed({
  get: () => local.textColor || "#0f172a",
  set: value => (local.textColor = value)
});

const overlay = computed({
  get: () => local.overlayOpacity ?? 0.45,
  set: value => {
    const clamped = Math.min(Math.max(typeof value === "number" ? value : 0.45, 0), 0.85);
    local.overlayOpacity = clamped;
  }
});

const hasImage = computed(() => !!(local.image || "").trim());

let syncing = false;
const syncFromProps = (value: BiographySection) => {
  syncing = true;
  Object.assign(local, {
    ...value,
    overlayOpacity: typeof value.overlayOpacity === "number" ? value.overlayOpacity : 0.45,
    fullWidth: value.fullWidth ?? true,
    titleFontSize: clampNumber(value.titleFontSize, 72, 24, 160),
    textFontSize: clampNumber(value.textFontSize, 18, 14, 48)
  });
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

watch(hasImage, present => {
  if (!present) {
    local.title = "";
  }
});

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    value.titleFontSize = clampNumber(value.titleFontSize, 72, 24, 160);
    value.textFontSize = clampNumber(value.textFontSize, 18, 14, 48);
    emit("update:modelValue", value as BiographySection);
  },
  { deep: true }
);
</script>
