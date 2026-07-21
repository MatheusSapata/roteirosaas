<template>
  <div class="bio-form-shell">
    <aside class="bio-form-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="bio-nav-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="bio-nav-icon">{{ tab.icon }}</span>
        <span>
          <strong>{{ tab.title }}</strong>
          <small>{{ tab.subtitle }}</small>
        </span>
      </button>
    </aside>

    <section class="bio-form-content">
      <template v-if="activeTab === 'text'">
        <h4 class="bio-form-title">Textos da seção</h4>
        <p class="bio-form-subtitle">Edite título, descrição e estilo do conteúdo da biografia.</p>

        <div v-if="hasImage" class="bio-field-group">
          <label class="bio-label">Título principal <span class="hint-dot hint-help" data-tip="Título exibido sobre o bloco de biografia.">?</span></label>
          <input
            v-model="local.title"
            class="bio-input bio-input-uppercase"
            :placeholder="viewCopy.title.placeholder"
          />
          <p class="bio-hint">{{ viewCopy.title.helper }}</p>
        </div>

        <div class="bio-field-group">
          <label class="bio-label">Descrição completa <span class="hint-dot hint-help" data-tip="Texto descritivo principal da biografia.">?</span></label>
          <div class="bio-rich-shell">
            <RichTextEditor v-model="local.text" :placeholder="viewCopy.text.placeholder" />
          </div>
        </div>

        <div class="bio-grid-3 bio-grid-3--align-end">
          <div class="bio-field-group">
            <label class="bio-label">{{ viewCopy.font.titleLabel }}</label>
            <div class="bio-stepper-inline">
              <input
                v-model.number="local.titleFontSize"
                type="number"
                min="24"
                max="160"
                step="2"
                class="bio-stepper-input"
              />
              <button type="button" class="bio-stepper-btn" @click="updateTitleSize(-2)">-</button>
              <button type="button" class="bio-stepper-btn" @click="updateTitleSize(2)">+</button>
            </div>
          </div>
          <div class="bio-field-group">
            <label class="bio-label">{{ viewCopy.colors.titleColor }}</label>
            <div class="bio-color-row">
              <input v-model="titleColor" type="color" class="bio-color-picker" />
              <input v-model="local.titleColor" placeholder="#ffffff" class="bio-input bio-input-mono" />
            </div>
          </div>
          <div class="bio-field-group">
            <label class="bio-label">{{ viewCopy.overlay.label }}</label>
            <input
              v-model.number="overlay"
              type="range"
              min="0"
              max="0.85"
              step="0.05"
              class="bio-range"
            />
            <p class="bio-hint">Regula a sobreposição da imagem.</p>
          </div>
        </div>
      </template>

      <template v-else>
        <h4 class="bio-form-title">Mídia da biografia</h4>
        <p class="bio-form-subtitle">Gerencie as imagens exibidas no desktop e no mobile.</p>

        <div class="bio-field-group">
          <label class="bio-label">{{ viewCopy.desktopImage.label }} <span class="hint-dot hint-help" :data-tip="viewCopy.desktopImage.helper">?</span></label>
          <ImageUploadField
            v-model="local.image"
            :hint="viewCopy.desktopImage.hint"
            :enable-crop="true"
            :crop-aspect="3"
            :editor-title="viewCopy.desktopImage.editorTitle"
          />
        </div>

        <div class="bio-field-group">
          <label class="bio-label">{{ viewCopy.mobileImage.label }} <span class="hint-dot hint-help" :data-tip="viewCopy.mobileImage.helper">?</span></label>
          <ImageUploadField
            v-model="local.mobileImage"
            :hint="viewCopy.mobileImage.hint"
            :enable-crop="true"
            :crop-aspect="2"
            :editor-title="viewCopy.mobileImage.editorTitle"
          />
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import type { BiographySection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

type BiographyTab = "text" | "media";
const tabs: Array<{ id: BiographyTab; title: string; subtitle: string; icon: string }> = [
  { id: "text", title: "Textos", subtitle: "Conteúdo da seção", icon: "✎" },
  { id: "media", title: "Mídia", subtitle: "Imagens", icon: "▧" }
];

const props = defineProps<{ modelValue: BiographySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BiographySection): void }>();
const t = createAdminLocalizer();
const activeTab = ref<BiographyTab>("text");

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
    placeholder: t({ pt: "BIOGRAFIA", es: "BIOGRAFÍA" }),
    helper: t({ pt: "Use letras maiúsculas para reforçar o impacto visual.", es: "Usa mayúsculas para reforzar el impacto visual." })
  },
  text: {
    placeholder: t({
      pt: "Conte a história da sua agência, bastidores e conquistas...",
      es: "Cuenta la historia de tu agencia, bastidores y logros..."
    })
  },
  font: {
    titleLabel: t({ pt: "Tamanho do título", es: "Tamaño del título" })
  },
  colors: {
    titleColor: t({ pt: "Cor do título", es: "Color del título" })
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
  for (const key of ["pt", "es"]) {
    const candidate = record[key];
    if (typeof candidate === "string" && candidate.trim()) return candidate;
  }
  for (const candidate of Object.values(record)) {
    if (typeof candidate === "string" && candidate.trim()) return candidate;
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

const updateTitleSize = (delta: number) => {
  const current = typeof local.titleFontSize === "number" ? local.titleFontSize : 72;
  local.titleFontSize = clampNumber(current + delta, 72, 24, 160);
};

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
  if (!present) local.title = "";
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

<style scoped>
.bio-form-shell {
  --editor-tab-icon-size: 22px;
  --editor-tab-icon-font: 12px;
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 56vh;
}

.bio-form-nav {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
}

.bio-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #d8dfda;
  border-radius: 14px;
  padding: 6px 9px;
  background: #eef2ef;
  color: #0f172a;
  text-align: left;
}

.bio-nav-item.active {
  background: #34c759;
  border-color: #34c759;
}

.bio-nav-icon {
  width: var(--editor-tab-icon-size);
  height: var(--editor-tab-icon-size);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--editor-tab-icon-font);
}

.bio-nav-item strong {
  display: block;
  font-size: 16px;
  line-height: 0.95;
  font-weight: 700;
}

.bio-nav-item small {
  display: block;
  margin-top: 0;
  font-size: 10px;
  color: #64748b;
  font-weight: 600;
}

.bio-form-content {
  background: #f4f7f5;
  padding: 10px 14px;
  overflow-y: auto;
}

.bio-form-title {
  margin: 0 0 2px;
  font-size: 16px;
  color: #0f172a;
  font-weight: 800;
}

.bio-form-subtitle {
  margin: 0;
  font-size: 12px;
  color: #607284;
}

.bio-field-group {
  margin-top: 10px;
}

.bio-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5f7380;
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 6px;
}

.bio-input {
  width: 100%;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  padding: 10px 12px;
  background: #fff;
}

.bio-input-uppercase {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.bio-input-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.bio-stepper-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.bio-stepper-input {
  width: 112px;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  padding: 9px 12px;
  background: #fff;
  font-size: 16px;
}

.bio-stepper-btn {
  width: 30px;
  height: 30px;
  border: 1px solid #c9d4ce;
  border-radius: 10px;
  background: #f7faf8;
  color: #1f2937;
  font-weight: 700;
  line-height: 1;
}

.bio-hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #7d9087;
}

.bio-rich-shell {
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.bio-rich-shell :deep(.ql-toolbar.ql-snow) {
  border: 0 !important;
  border-bottom: 1px solid #e6eee8 !important;
  background: #fbfdfc;
  padding: 4px 8px;
}

.bio-rich-shell :deep(.ql-container.ql-snow) {
  border: 0 !important;
}

.bio-rich-shell :deep(.ql-editor) {
  min-height: 150px;
}

.bio-rich-shell :deep(.ql-toolbar .ql-formats) {
  margin-right: 8px;
}

.bio-rich-shell :deep(.ql-toolbar button) {
  width: 18px;
  height: 18px;
  padding: 2px;
}

.bio-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.bio-grid-2--align-end {
  align-items: end;
}

.bio-grid-3 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.2fr);
  gap: 10px;
}

.bio-grid-3--align-end {
  align-items: end;
}

.bio-grid-3--align-end > .bio-field-group:nth-child(2) {
  margin-left: -14px;
}

.bio-color-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bio-color-picker {
  width: 38px;
  min-width: 38px;
  height: 38px;
  border: 1px solid #c9d4ce;
  border-radius: 10px;
  padding: 2px;
}

.bio-range {
  width: 100%;
}

:deep(.bio-field-group .flex.flex-1.flex-col.rounded-xl.border.border-slate-200.p-3) {
  padding: 10px;
}

:deep(.bio-field-group .mb-3 > .flex.max-h-\[320px\].min-h-\[220px\].w-full.items-center.justify-center.overflow-hidden.rounded-lg.border.border-slate-200.bg-slate-50) {
  max-height: 150px !important;
  min-height: 120px !important;
}

:deep(.bio-field-group .image-upload-preview) {
  max-height: 150px !important;
  min-height: 120px !important;
  object-fit: cover;
}

.hint-dot {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 1px solid #c9d4ce;
  color: #8aa0ae;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.hint-help {
  position: relative;
  cursor: help;
}

.hint-help:hover::after {
  content: attr(data-tip);
  position: absolute;
  left: 50%;
  bottom: 22px;
  transform: translateX(-50%);
  width: 220px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--popover);
  color: var(--popover-foreground);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0;
  text-transform: none;
  z-index: 30;
  box-shadow: 0 10px 24px rgba(7, 17, 31, 0.22);
}

.bio-form-shell,
.bio-form-content {
  background: var(--background);
  color: var(--foreground);
}

.bio-form-nav {
  border-color: var(--border);
  background: var(--card);
}

.bio-nav-item {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.bio-nav-item.active {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
}

.bio-nav-item small,
.bio-form-subtitle,
.bio-hint {
  color: var(--muted-foreground);
}

.bio-form-title {
  color: var(--foreground);
}

.bio-input,
.bio-stepper-input {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}

.bio-stepper-btn {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.bio-stepper-btn:hover {
  border-color: color-mix(in srgb, var(--primary) 38%, var(--border));
  background: var(--accent);
}

.bio-rich-shell,
.bio-rich-shell :deep(.ql-container.ql-snow),
.bio-rich-shell :deep(.ql-editor) {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}

.bio-rich-shell :deep(.ql-toolbar.ql-snow) {
  border-color: var(--input) !important;
  background: var(--muted);
}

.bio-color-picker {
  border-color: var(--input);
  background: var(--card);
}

.hint-help:hover::after {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

@media (max-width: 900px) {
  .bio-form-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .bio-form-nav {
    border-right: 0;
    border-bottom: 0;
    padding: 8px 8px 8px 16px;
    margin-bottom: 8px;
    flex-direction: row;
    gap: 8px;
  }

  .bio-nav-item {
    flex: 1;
    min-width: 0;
    padding: 7px 8px;
  }

  .bio-nav-item strong {
    font-size: 14px;
  }

  .bio-nav-item small {
    font-size: 11px;
  }

  .bio-form-content {
    padding: 10px;
  }

  .bio-grid-2 {
    grid-template-columns: 1fr;
  }

  .bio-grid-3 {
    grid-template-columns: 1fr;
  }
}
</style>
