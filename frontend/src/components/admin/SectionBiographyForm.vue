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
        <div class="rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {{ viewCopy.languageSwitcher.label }}
              </p>
              <p class="text-xs text-slate-500">{{ viewCopy.languageSwitcher.helper }}</p>
            </div>
            <div class="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 p-1">
              <button
                v-for="option in languageOptions"
                :key="option.key"
                type="button"
                class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide transition"
                :class="option.key === activeLanguage ? 'bg-brand text-white shadow-sm' : 'text-slate-500 hover:text-slate-900'"
                @click="activeLanguage = option.key"
              >
                {{ option.shortLabel }}
              </button>
            </div>
          </div>
        </div>
        <div v-if="hasImage">
          <label class="text-sm font-semibold text-slate-600">
            {{ viewCopy.title.label }}
            <span class="ml-1 text-xs font-normal uppercase tracking-wide text-slate-400">
              ({{ currentLanguageLabel }})
            </span>
          </label>
          <input
            v-model="titleInputValue"
            class="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold uppercase tracking-wide"
            :placeholder="viewCopy.title.placeholder"
          />
          <p class="mt-1 text-xs text-slate-500">{{ viewCopy.title.helper }}</p>
        </div>

        <div>
          <label class="text-sm font-semibold text-slate-600">
            {{ viewCopy.subtitle.label }}
            <span class="ml-1 text-xs font-normal uppercase tracking-wide text-slate-400">
              ({{ currentLanguageLabel }})
            </span>
          </label>
          <RichTextEditor
            :key="`biography-text-${activeLanguage}`"
            v-model="textInputValue"
            class="mt-2"
            :placeholder="viewCopy.subtitle.placeholder"
          />
        </div>
      </div>

      <div class="space-y-5">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.font.titleLabel }}</label>
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
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.font.textLabel }}</label>
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
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.titleColor }}</label>
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
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.colors.textColor }}</label>
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
          <label class="text-sm font-semibold text-slate-600">{{ viewCopy.overlay.label }}</label>
          <input
            type="range"
            min="0"
            max="0.85"
            step="0.05"
            v-model.number="overlay"
            class="mt-2 w-full"
          />
          <p class="mt-1 text-xs text-slate-500">{{ viewCopy.overlay.helper }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import type { BiographySection } from "../../types/page";
import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";
import { createTranslatable, type LocalizedString, type SupportedLanguage } from "../../utils/i18n";

const props = defineProps<{ modelValue: BiographySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BiographySection): void }>();
const t = createAdminLocalizer();
const adminLanguage = getAdminLanguage();

const languageOptions = [
  { key: "pt" as SupportedLanguage, label: t({ pt: "Português", es: "Portugués" }), shortLabel: "PT" },
  { key: "es" as SupportedLanguage, label: t({ pt: "Espanhol", es: "Español" }), shortLabel: "ES" }
] as const;

const isLocalizedRecord = (value: LocalizedString): value is Partial<Record<SupportedLanguage, string>> =>
  typeof value === "object" && value !== null;

const readLocalizedField = (value: LocalizedString, lang: SupportedLanguage) => {
  if (value === null || typeof value === "undefined") return "";
  if (typeof value === "string") {
    return lang === "pt" ? value : "";
  }
  const candidate = value[lang];
  if (typeof candidate === "string") {
    return candidate;
  }
  return "";
};

const writeLocalizedField = (current: LocalizedString, lang: SupportedLanguage, nextValue: string): LocalizedString => {
  const normalized = typeof nextValue === "string" ? nextValue : "";
  const trimmed = normalized.trim();
  if (lang === "pt" && typeof current === "string") {
    return normalized;
  }
  const record: Partial<Record<SupportedLanguage, string>> = isLocalizedRecord(current) ? { ...current } : {};
  if (typeof current === "string" && current.trim().length) {
    record.pt = current;
  }
  if (trimmed.length === 0) {
    delete record[lang];
  } else {
    record[lang] = normalized;
  }
  const keys = Object.keys(record);
  if (!keys.length) return "";
  if (keys.length === 1 && keys[0] === "pt") {
    return record.pt ?? "";
  }
  return record;
};

const ensureLanguage = (lang: SupportedLanguage): SupportedLanguage => {
  const found = languageOptions.find(option => option.key === lang);
  return found ? found.key : "pt";
};

const activeLanguage = ref<SupportedLanguage>(ensureLanguage(adminLanguage));
const currentLanguageLabel = computed(
  () => languageOptions.find(option => option.key === activeLanguage.value)?.label || languageOptions[0].label
);

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
  subtitle: {
    label: t({ pt: "Subtítulo / Texto abaixo", es: "Subtítulo / Texto debajo" }),
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
  },
  languageSwitcher: {
    label: t({ pt: "Conte�do por idioma", es: "Contenido por idioma" }),
    helper: t({ pt: "Edite os textos em Portugu�s ou Espanhol.", es: "Edita los textos en Portugués o Español." })
  }
};

const biographyDefaults = createTranslatable({
  title: { pt: "BIOGRAFIA", es: "BIOGRAFÍA" },
  text: {
    pt: "Use esta se��o para compartilhar a história da sua agência, bastidores e fatos que criam conexão com o visitante.",
    es: "Usa esta sección para compartir la historia de tu agencia, bastidores y hechos que crean conexión con el visitante."
  }
});

const local = reactive<BiographySection>({
  type: "biography",
  enabled: true,
  fullWidth: true,
  title: biographyDefaults.title,
  text: biographyDefaults.text,
  overlayOpacity: 0.45,
  titleColor: "#ffffff",
  textColor: "#0f172a",
  titleFontSize: 72,
  textFontSize: 18,
  ...props.modelValue
});

const titleInputValue = computed({
  get: () => readLocalizedField(local.title, activeLanguage.value),
  set: value => {
    local.title = writeLocalizedField(local.title, activeLanguage.value, value);
  }
});

const textInputValue = computed({
  get: () => readLocalizedField(local.text, activeLanguage.value),
  set: value => {
    local.text = writeLocalizedField(local.text, activeLanguage.value, value);
  }
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
