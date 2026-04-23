<template>
  <div class="space-y-6">
    <div class="space-y-5">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.desktopImage.label }}</label>
        <p class="text-xs text-slate-500">
          {{ viewCopy.desktopImage.helper }}
        </p>
        <ImageUploadField
          v-model="local.image"
          class="mt-2"
          :hint="viewCopy.desktopImage.hint"
          :enable-crop="true"
          :crop-aspect="3"
          :editor-title="viewCopy.desktopImage.editorTitle"
        />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.mobileImage.label }}</label>
        <p class="text-xs text-slate-500">{{ viewCopy.mobileImage.helper }}</p>
        <ImageUploadField
          v-model="local.mobileImage"
          class="mt-2"
          :hint="viewCopy.mobileImage.hint"
          :enable-crop="true"
          :crop-aspect="2"
          :editor-title="viewCopy.mobileImage.editorTitle"
        />
      </div>
    </div>

    <div class="grid gap-6 md:grid-cols-2">
      <div class="space-y-5">
        <div v-if="hasImage">
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.title.label }}</label>
          <input
            v-model="local.title"
            class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold uppercase tracking-wide"
            :placeholder="viewCopy.title.placeholder"
          />
          <p class="mt-1 text-xs text-slate-500">{{ viewCopy.title.helper }}</p>
        </div>

        <div>
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.text.label }}</label>
          <RichTextEditor
            v-model="local.text"
            class="mt-2"
            :placeholder="viewCopy.text.placeholder"
          />
        </div>
      </div>

      <div class="space-y-5">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.font.titleLabel }}</label>
            <input
              v-model.number="local.titleFontSize"
              type="number"
              min="24"
              max="160"
              step="2"
              class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.font.textLabel }}</label>
            <input
              v-model.number="local.textFontSize"
              type="number"
              min="14"
              max="48"
              step="1"
              class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.titleColor }}</label>
            <div class="mt-2 flex items-center gap-3">
              <input v-model="titleColor" type="color" class="h-10 w-10 cursor-pointer rounded border border-slate-200" />
              <input
                v-model="local.titleColor"
                placeholder="#ffffff"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.textColor }}</label>
            <div class="mt-2 flex items-center gap-3">
              <input v-model="textColor" type="color" class="h-10 w-10 cursor-pointer rounded border border-slate-200" />
              <input
                v-model="local.textColor"
                placeholder="#0f172a"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>
        </div>

        <div>
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.overlay.label }}</label>
          <input
            v-model.number="overlay"
            type="range"
            min="0"
            max="0.85"
            step="0.05"
            class="mt-2 w-full"
          />
          <p class="mt-1 text-xs text-slate-500">{{ viewCopy.overlay.helper }}</p>
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
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: BiographySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BiographySection): void }>();
const t = createAdminLocalizer();

const viewCopy = {
  desktopImage: {
    label: t({ pt: "Imagem desktop", es: "Imagen desktop" }),
    helper: t({
      pt: "Opcional. O título só aparece quando houver uma imagem carregada (recomendado 1920x640px).",
      es: "Opcional. El título solo aparece cuando hay una imagen cargada (recomendado 1920x640px)."
    }),
    hint: t({ pt: "Recomendado 1920x640px", es: "Recomendado 1920x640px" }),
    editorTitle: t({ pt: "Ajuste a imagem da biografia", es: "Ajusta la imagen de la biografía" })
  },
  mobileImage: {
    label: t({ pt: "Imagem mobile (opcional)", es: "Imagen mobile (opcional)" }),
    helper: t({
      pt: "Use uma versão horizontal 2:1 para telas menores (ex.: 1600x800px).",
      es: "Usa una versión horizontal 2:1 para pantallas menores (ej.: 1600x800px)."
    }),
    hint: t({ pt: "Exibida automaticamente no mobile", es: "Se muestra automáticamente en mobile" }),
    editorTitle: t({ pt: "Ajuste a imagem mobile", es: "Ajusta la imagen mobile" })
  },
  title: {
    label: t({ pt: "Título", es: "Título" }),
    placeholder: t({ pt: "BIOGRAFIA", es: "BIOGRAFÍA" }),
    helper: t({ pt: "Use letras maiúsculas para reforçar o impacto visual.", es: "Usa mayúsculas para reforzar el impacto visual." })
  },
  text: {
    label: t({ pt: "Texto abaixo", es: "Texto debajo" }),
    placeholder: t({
      pt: "Conte a história da sua agência, bastidores e conquistas...",
      es: "Cuenta la historia de tu agencia, bastidores y logros..."
    })
  },
  font: {
    titleLabel: t({ pt: "Fonte do título (px)", es: "Fuente del título (px)" }),
    textLabel: t({ pt: "Fonte do texto (px)", es: "Fuente del texto (px)" })
  },
  colors: {
    titleColor: t({ pt: "Cor do título", es: "Color del título" }),
    textColor: t({ pt: "Cor do texto", es: "Color del texto" })
  },
  overlay: {
    label: t({ pt: "Intensidade da sobreposição", es: "Intensidad de la superposición" }),
    helper: t({ pt: "Escurece a foto para garantir que o título fique legível.", es: "Oscurece la foto para garantizar que el título sea legible." })
  }
};

const defaultBodyText =
  "Use esta seção para compartilhar a história da sua agência, bastidores e fatos que criam conexão com o visitante.";

const normalizeLegacyLocalizedText = (value: unknown, fallback: string) => {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object") return fallback;
  const record = value as Record<string, unknown>;
  const preferredKeys = ["pt", "es"];
  for (const key of preferredKeys) {
    const candidate = record[key];
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate;
    }
  }
  for (const candidate of Object.values(record)) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate;
    }
  }
  return fallback;
};

const local = reactive<BiographySection>({
  type: "biography",
  enabled: true,
  fullWidth: true,
  overlayOpacity: 0.45,
  titleColor: "#ffffff",
  textColor: "#0f172a",
  titleFontSize: 72,
  textFontSize: 18,
  ...props.modelValue,
  title: normalizeLegacyLocalizedText(props.modelValue?.title, "BIOGRAFIA"),
  text: normalizeLegacyLocalizedText(props.modelValue?.text, defaultBodyText)
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

const hasImage = computed(() => Boolean((local.image && local.image.trim()) || (local.mobileImage && local.mobileImage.trim())));

let syncing = false;
const syncFromProps = (value: BiographySection) => {
  syncing = true;
  Object.assign(local, {
    ...value,
    title: normalizeLegacyLocalizedText(value.title, "BIOGRAFIA"),
    text: normalizeLegacyLocalizedText(value.text, defaultBodyText),
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
