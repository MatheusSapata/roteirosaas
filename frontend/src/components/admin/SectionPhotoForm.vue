<template>
  <div class="photo-proto-body">
    <aside class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab"
        :class="{ active: activeTab === tab.id }"
        type="button"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon" v-html="tab.icon"></span>
        <span>{{ tab.label }}<small>{{ tab.desc }}</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activeTab === 'media'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Foto destacada</h2>
            <p class="section-desc">Envie a imagem principal da seção em alta resolução.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Imagem <span class="help" data-tip="Imagem principal exibida na seção.">?</span></label>
            <div class="list">
              <div class="media-item">
                <input ref="imageInput" type="file" accept="image/*" class="hidden" @change="onImageFileChange" />
                <button type="button" class="media-thumb-button" @click="imageInput?.click()">
                  <img v-if="previewUrl(local.image)" :src="previewUrl(local.image) || ''" alt="Imagem destacada" />
                  <div v-else class="media-preview">IMG</div>
                </button>
                <div class="media-info">
                  <strong>Imagem destacada <span class="help" data-tip="Imagem principal da seção foto destacada.">?</span></strong>
                  <p>Versão exibida na área principal da seção.</p>
                </div>
                <div class="btn-row">
                  <button type="button" @click="imageInput?.click()">
                    {{ uploadingImage ? "Enviando..." : (local.image ? "Substituir" : "Adicionar") }}
                  </button>
                  <button v-if="local.image" type="button" class="danger" @click="clearImage">Remover</button>
                </div>
              </div>
            </div>
            <p v-if="uploadError" class="field-hint field-hint--error">{{ uploadError }}</p>
          </div>

          <div class="field">
            <label>Texto alternativo <span class="help" data-tip="Descrição para acessibilidade e SEO.">?</span></label>
            <input v-model="local.altText" :placeholder="viewCopy.altText.placeholder" />
            <p class="field-hint">{{ viewCopy.altText.helper }}</p>
          </div>
 
          <div class="field">
            <label>Tipo de layout <span class="help" data-tip="Card centralizado ou largura total.">?</span></label>
            <div class="layout-grid">
              <button
                type="button"
                class="layout-option"
                :class="local.layout === 'card' ? 'active' : ''"
                @click="local.layout = 'card'"
              >
                <span class="layout-row layout-row--icon">
                  <span class="layout-svg-preview layout-svg-preview--card" aria-hidden="true">
                    <svg viewBox="0 0 64 44" xmlns="http://www.w3.org/2000/svg">
                      <rect x="0" y="0" width="64" height="44" rx="8" fill="#d7dde6" />
                      <rect x="16" y="12" width="32" height="20" rx="4" fill="none" stroke="#4b5563" stroke-width="2.2" />
                      <rect x="20" y="16" width="24" height="12" rx="3" fill="#6b7280" opacity="0.45" />
                    </svg>
                  </span>
                  <span class="layout-copy">
                    <strong class="layout-title-right">{{ viewCopy.layout.cardLabel }}</strong>
                    <small>{{ viewCopy.layout.cardHelper }}</small>
                  </span>
                </span>
              </button>
              <button
                type="button"
                class="layout-option"
                :class="local.layout === 'full' ? 'active' : ''"
                @click="local.layout = 'full'"
              >
                <span class="layout-row layout-row--icon">
                  <span class="layout-svg-preview layout-svg-preview--full" aria-hidden="true">
                    <svg viewBox="0 0 64 44" xmlns="http://www.w3.org/2000/svg">
                      <rect x="0" y="0" width="64" height="10" fill="currentColor" opacity="0.18" />
                      <rect x="0" y="34" width="64" height="10" fill="currentColor" opacity="0.18" />
                      <rect x="0" y="10" width="64" height="24" fill="currentColor" opacity="0.45" />
                      <rect x="9" y="18" width="46" height="8" rx="2.5" fill="currentColor" opacity="0.3" />
                    </svg>
                  </span>
                  <span class="layout-copy">
                    <strong class="layout-title-right">{{ viewCopy.layout.fullLabel }}</strong>
                    <small>{{ viewCopy.layout.fullHelper }}</small>
                  </span>
                </span>
              </button>
            </div>
          </div>

          <div v-if="local.layout === 'card'" class="field">
            <label>Cor de fundo <span class="help" data-tip="Cor de fundo do bloco quando usar layout card.">?</span></label>
            <div class="color-row">
              <input type="color" v-model="colorPickerValue" class="color-picker" />
              <input v-model="customBackground" placeholder="#f4f7ff" class="mono-input" />
              <button type="button" class="ghost-btn" @click="customBackground = ''">Usar automática</button>
            </div>
            <p class="field-hint">{{ viewCopy.background.helper }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import type { PhotoSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { resolveMediaUrl, uploadImageFile } from "../../utils/media";
import { useAgencyStore } from "../../store/useAgencyStore";
import { adminTabIcons } from "../../utils/adminTabIcons";

type PhotoTab = "media";

const props = defineProps<{ modelValue: PhotoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PhotoSection): void }>();
const t = createAdminLocalizer();
const agencyStore = useAgencyStore();
const imageInput = ref<HTMLInputElement | null>(null);
const uploadingImage = ref(false);
const uploadError = ref("");

const tabs: Array<{ id: PhotoTab; icon: string; label: string; desc: string }> = [
  { id: "media", icon: adminTabIcons.media, label: "Mídia", desc: "Imagem e layout" }
];

const activeTab = ref<PhotoTab>("media");

const viewCopy = {
  layout: {
    cardLabel: t({ pt: "Card centralizado", es: "Card centrado" }),
    cardHelper: t({ pt: "A imagem fica dentro de um card com sombra.", es: "La imagen queda dentro de un card con sombra." }),
    fullLabel: t({ pt: "Tela cheia", es: "Pantalla completa" }),
    fullHelper: t({ pt: "A imagem ocupa a largura total, semelhante ao hero.", es: "La imagen ocupa todo el ancho, similar al hero." })
  },
  background: {
    helper: t({ pt: "Deixe em branco para seguir as cores configuradas na página.", es: "Déjalo en blanco para seguir los colores configurados en la página." })
  },
  altText: {
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
  backgroundColor: props.modelValue.backgroundColor
});

let syncing = false;
const customBackground = ref(props.modelValue.backgroundColor || "");
const colorPickerValue = computed({
  get: () => customBackground.value || "#f4f7ff",
  set: value => {
    customBackground.value = value;
  }
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

const previewUrl = (value?: string | null) => resolveMediaUrl(value);

const ensureAgencyId = async () => {
  if (!agencyStore.currentAgencyId) {
    await agencyStore.loadAgencies().catch(() => undefined);
  }
  return agencyStore.currentAgencyId;
};

const onImageFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const agencyId = await ensureAgencyId();
  if (!agencyId) {
    uploadError.value = "Selecione ou crie uma agência antes de enviar imagens.";
    input.value = "";
    return;
  }
  uploadingImage.value = true;
  uploadError.value = "";
  try {
    const asset = await uploadImageFile(file, agencyId);
    local.image = asset.url;
  } catch {
    uploadError.value = "Não foi possível enviar a imagem. Tente novamente.";
  } finally {
    uploadingImage.value = false;
    input.value = "";
  }
};

const clearImage = () => {
  local.image = "";
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

<style scoped>
.photo-proto-body {
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 56vh;
}

.tabs {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
}

.tab {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #d8dfda;
  border-radius: 14px;
  padding: 7px 9px;
  background: #eef2ef;
  color: #0f172a;
  text-align: left;
}

.tab.active {
  background: #34c759;
  border-color: #34c759;
}

.tab-icon {
  width: 22px;
  height: 22px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.tab > span {
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.15;
}

.tab > span small {
  font-size: 12px;
  font-weight: 600;
  color: rgba(15, 23, 42, 0.55);
}

.tab.active > span small {
  color: rgba(7, 82, 36, 0.78);
}

.editor {
  padding: 0;
  background: #edf1ef;
}

.section-card {
  background: transparent;
  border: 0;
  min-height: 100%;
}

.section-head {
  padding: 14px 16px 10px;
  border-bottom: 1px solid #dde5e1;
}

.section-title {
  margin: 0;
  font-size: 18px;
  line-height: 1.15;
  color: #0f172a;
  font-weight: 800;
}

.section-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6a7e74;
}

.content-area {
  padding: 12px 14px;
  display: grid;
  gap: 10px;
}

.field {
  display: grid;
  gap: 6px;
}

.field label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 800;
  color: #6a7e74;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.help {
  width: 16px;
  height: 16px;
  border: 1px solid #cdd8d2;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #8ca198;
  position: relative;
  cursor: help;
  background: #eef4f1;
  text-transform: none;
}

.help:hover::after {
  content: attr(data-tip);
  position: absolute;
  left: 22px;
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  padding: 6px 8px;
  background: #0f172a;
  color: #fff;
  font-size: 11px;
  border-radius: 8px;
  z-index: 20;
  text-transform: none;
  letter-spacing: 0;
}

input {
  width: 100%;
  border: 1px solid #cad7d1;
  border-radius: 12px;
  background: #fff;
  font-size: 16px;
  line-height: 1.25;
  padding: 9px 12px;
  color: #1f2937;
}

input:focus {
  outline: none;
  border-color: #9cb5aa;
  box-shadow: 0 0 0 2px rgba(52, 199, 89, 0.15);
}

.field-hint {
  margin: 0;
  font-size: 11px;
  color: #7d9087;
}

.field-hint--error {
  color: #dc2626;
}

.list {
  display: grid;
  gap: 8px;
}

.media-item {
  display: grid;
  grid-template-columns: 86px 1fr auto;
  gap: 12px;
  align-items: center;
  border: 1px solid #dfe8e2;
  background: #fff;
  border-radius: 12px;
  padding: 8px;
}

.media-thumb-button {
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
}

.media-thumb-button img {
  width: 86px;
  height: 58px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
}

.media-preview {
  width: 86px;
  height: 58px;
  border-radius: 8px;
  background: #e3ebe6;
  display: grid;
  place-items: center;
  color: #7d8d83;
  font-size: 12px;
  font-weight: 700;
}

.media-info strong {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 3px;
  font-size: 13px;
}

.media-info p {
  margin: 0;
  color: #7d8d83;
  font-size: 12px;
  line-height: 1.35;
}

.btn-row {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  align-items: center;
}

.btn-row button {
  border: 1px solid #dfe8e2;
  border-radius: 8px;
  padding: 7px 10px;
  min-height: 32px;
  background: #fff;
  color: #223228;
  font-size: 12px;
  font-weight: 700;
}

.btn-row button.danger {
  background: #fff1f1;
  color: #e13c3c;
  border-color: #ffd4d4;
}

.layout-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.layout-option {
  border: 1px solid #cad7d1;
  border-radius: 14px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 2px;
  background: #fff;
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.layout-option.active {
  border-color: #34c759;
  background: #ecfdf2;
}

.layout-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  align-items: center;
  column-gap: 14px;
}

.layout-row--icon {
  justify-content: flex-start;
}

.layout-svg-preview {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0f172a;
}

.layout-svg-preview svg {
  width: 52px;
  height: 36px;
}

.layout-svg-preview--card {
  width: 72px;
  min-width: 72px;
  height: 54px;
  border-radius: 12px;
  background: transparent;
}

.layout-svg-preview--full {
  width: 72px;
  min-width: 72px;
  height: 54px;
  border-radius: 8px;
  background: transparent;
}

.layout-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.layout-title-right {
  font-size: 12px;
  color: #12212f;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.layout-copy small {
  font-size: 12px;
  color: #6f857a;
  font-weight: 700;
  line-height: 1.25;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.color-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.color-picker {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid #cad7d1;
  padding: 2px;
}

.mono-input {
  flex: 1;
  min-width: 180px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.ghost-btn {
  border: 1px solid #cad7d1;
  border-radius: 999px;
  background: #fff;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  padding: 8px 12px;
}

@media (max-width: 900px) {
  .photo-proto-body {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .tabs {
    border-right: 0;
    border-bottom: 0;
    padding: 8px 8px 8px 16px;
    margin-bottom: 8px;
    flex-direction: row;
  }

  .tab {
    flex: 1;
    min-width: 0;
  }

  .tab > span {
    font-size: 14px;
  }

  .tab > span small {
    display: none;
  }

  .editor {
    padding: 0;
  }

  .section-title {
    font-size: 18px;
  }

  .section-desc {
    font-size: 14px;
  }

  .field label {
    font-size: 12px;
  }

  input {
    font-size: 16px;
  }

  .layout-grid {
    grid-template-columns: 1fr;
  }

  .media-item {
    grid-template-columns: 70px 1fr;
  }

  .media-item .btn-row {
    grid-column: 2 / span 1;
    justify-content: flex-start;
  }
}
</style>
