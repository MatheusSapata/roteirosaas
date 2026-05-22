<template>
  <div class="hero-proto-body">
    <aside class="tabs">
      <button v-for="tab in tabs" :key="tab.id" class="tab" :class="{ active: activeTab === tab.id }" type="button" @click="activeTab = tab.id">
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}<small>{{ tab.desc }}</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activeTab === 'text'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos do banner</h2>
            <p class="section-desc">Edite o título principal, o texto de apoio e os destaques exibidos no banner.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Título principal <span class="help" data-tip="Frase de maior destaque da seção hero.">?</span></label>
            <input v-model="local.title" />
          </div>

          <div class="field">
            <label>Texto de apoio <span class="help" data-tip="Texto complementar exibido logo abaixo do título.">?</span></label>
            <div class="rich-box">
              <RichTextEditor v-model="local.subtitle" placeholder="Conte um pouco sobre o roteiro..." />
            </div>
          </div>

          <div class="field">
            <label>Destaques <span class="help" data-tip="Digite um destaque e clique em Adicionar.">?</span></label>
            <div class="highlight-input-row">
              <input v-model="newChip" placeholder="Ex: Wi‑Fi Starlink" @keydown.enter.prevent="addChip" />
              <button class="add-btn" type="button" @click="addChip">Adicionar</button>
            </div>
            <div class="highlight-tags">
              <span v-for="(chip, index) in normalizedChips" :key="`${chip}-${index}`" class="highlight-tag">
                <span class="drag-handle">⋮⋮</span>
                {{ chip }}
                <button class="tag-remove" type="button" @click="removeChip(index)">×</button>
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'media'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Imagens do banner</h2>
            <p class="section-desc">Envie imagem para desktop, mobile e logo da agência, além da cor de escurecimento.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="list">
            <div class="media-item">
              <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="onMediaFileChange('logo', $event)" />
              <button type="button" class="media-thumb-button" @click="logoInput?.click()">
                <img v-if="previewUrl(local.logoUrl)" :src="previewUrl(local.logoUrl) || ''" alt="Logo da agência" />
                <div v-else class="media-preview">Logo</div>
              </button>
              <div class="media-info">
                <strong>Logo da agência <span class="help" data-tip="Logo exibida sobre a hero.">?</span></strong>
                <p>Logo exibida sobre o fundo principal.</p>
              </div>
              <div class="btn-row">
                <div class="logo-size-inline-wrap">
                  <div class="logo-size-inline">
                    <input v-model.number="local.logoSize" type="number" min="48" max="160" step="4" />
                    <button type="button" @click="updateLogoSize(-4)">-</button>
                    <button type="button" @click="updateLogoSize(4)">+</button>
                  </div>
                  <small class="logo-size-inline-label">Tamanho da logo</small>
                </div>
                <button type="button" @click="logoInput?.click()">{{ uploadingSlot === "logo" ? "Enviando..." : "Substituir" }}</button>
                <button type="button" class="danger" @click="clearMedia('logo')">Remover</button>
              </div>
            </div>
          </div>

          <div class="list" style="margin-top:12px;">
            <div class="media-item">
              <input ref="bgInput" type="file" accept="image/*" class="hidden" @change="onMediaFileChange('background', $event)" />
              <button type="button" class="media-thumb-button" @click="bgInput?.click()">
                <img v-if="previewUrl(local.backgroundImage)" :src="previewUrl(local.backgroundImage) || ''" alt="Imagem de fundo" />
                <div v-else class="media-preview">BG</div>
              </button>
              <div class="media-info">
                <strong>Imagem de fundo <span class="help" data-tip="Imagem principal de fundo da hero.">?</span></strong>
                <p>Versão exibida na área principal da seção.</p>
              </div>
              <div class="btn-row">
                <button type="button" @click="bgInput?.click()">{{ uploadingSlot === "background" ? "Enviando..." : "Substituir" }}</button>
                <button type="button" class="danger" @click="clearMedia('background')">Remover</button>
              </div>
            </div>
          </div>

          <div class="compact-grid" style="margin-top:12px;">
            <div class="field">
              <label>Cor de escurecimento <span class="help" data-tip="Camada para reforçar contraste dos textos.">?</span></label>
              <div class="color-input">
                <input type="color" class="color-preview" :value="colorOnly(local.gradientColor)" @input="onColorPick" />
                <input v-model="local.gradientColor" />
              </div>
            </div>
            <div class="field">
              <label>Vídeo (YouTube) <span class="help" data-tip="Link do vídeo incorporado ao layout imersivo.">?</span></label>
              <input v-model="local.videoUrl" placeholder="Link do YouTube ou iframe com src" />
            </div>
          </div>
        </div>
      </div>

      <div v-else class="section-card" :class="{ 'section-card--dropdown-open': sectionDropdownOpen }">
        <div class="section-head">
          <div>
            <h2 class="section-title">Botão de ação do banner</h2>
            <p class="section-desc">Defina o convite principal da seção e para onde o visitante será direcionado ao clicar.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Tipo de ação <span class="help" data-tip="Escolha entre link externo/WhatsApp ou âncora interna.">?</span></label>
            <div class="pill-row">
              <span class="pill" :class="{ active: local.ctaMode !== 'section' }" @click="local.ctaMode = 'link'">WhatsApp / Link externo</span>
              <span class="pill" :class="{ active: local.ctaMode === 'section' }" @click="local.ctaMode = 'section'">Ir para seção</span>
            </div>
          </div>

          <div class="compact-grid">
            <div class="field">
              <label>Texto do botão <span class="help" data-tip="Texto curto mostrado no botão.">?</span></label>
              <input v-model="local.ctaLabel" />
            </div>
            <div class="field">
              <label>Destino do clique <span class="help" data-tip="URL externa ou seção de destino.">?</span></label>
              <template v-if="local.ctaMode === 'section'">
                <div ref="sectionDropdownRef" class="section-dropdown">
                  <button type="button" class="section-dropdown-trigger" @click="toggleSectionDropdown">
                    <span>{{ selectedSectionOption?.label || "Selecione uma seção" }}</span>
                    <span class="section-dropdown-arrow">▾</span>
                  </button>
                  <div v-if="sectionDropdownOpen" class="section-dropdown-menu">
                    <button
                      v-for="opt in sectionOptions"
                      :key="opt.value"
                      type="button"
                      class="section-dropdown-item"
                      @mouseenter="hoveredSectionOption = opt"
                      @mouseleave="hoveredSectionOption = null"
                      @click="selectSectionOption(opt)"
                    >
                      {{ opt.label }}
                    </button>
                  </div>
                  <div v-if="sectionDropdownOpen && hoveredSectionOption" class="section-hover-preview">
                    <SectionHoverVisualPreview
                      :label="hoveredSectionOption.label"
                      :section="hoveredSectionOption.section"
                    />
                  </div>
                </div>
              </template>
              <template v-else>
                <input v-model="local.ctaLink" />
                <label class="inline-check"><input type="checkbox" v-model="local.ctaOpenInNewTab" /> Abrir em nova aba</label>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import type { HeroSection, PageSection } from "../../types/page";
import { sectionsInjectionKey } from "./sectionsContext";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { useAgencyStore } from "../../store/useAgencyStore";
import { resolveMediaUrl, uploadImageFile } from "../../utils/media";
import { sectionLabels } from "../../utils/sectionLabels";
import SectionHoverVisualPreview from "./SectionHoverVisualPreview.vue";

type HeroTab = "text" | "media" | "button";

const props = defineProps<{ modelValue: HeroSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: HeroSection): void }>();
const injectedSections = inject(sectionsInjectionKey, null);
const agencyStore = useAgencyStore();

const HERO_LAYOUT: HeroSection["layout"] = "immersive";
const HERO_ANIMATION_DURATION = 1000;

const tabs: Array<{ id: HeroTab; icon: string; label: string; desc: string }> = [
  { id: "text", icon: "✎", label: "Textos", desc: "Conteúdo principal" },
  { id: "media", icon: "▧", label: "Mídia", desc: "Imagem e vídeo" },
  { id: "button", icon: "↗", label: "Botão", desc: "Ação do visitante" }
];

const activeTab = ref<HeroTab>("text");
const newChip = ref("");
const logoInput = ref<HTMLInputElement | null>(null);
const bgInput = ref<HTMLInputElement | null>(null);
const uploadingSlot = ref<"logo" | "background" | null>(null);
type SectionOption = { value: string; label: string; preview: string; section: PageSection };
const sectionDropdownOpen = ref(false);
const hoveredSectionOption = ref<SectionOption | null>(null);
const sectionDropdownRef = ref<HTMLElement | null>(null);

const local = reactive<HeroSection>({
  ...props.modelValue,
  layout: HERO_LAYOUT,
  logoSize: props.modelValue.logoSize ?? 64,
  logoBorderRadius: props.modelValue.logoBorderRadius ?? 0,
  chips: props.modelValue.chips ? [...props.modelValue.chips] : [],
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null,
  ctaOpenInNewTab: props.modelValue.ctaOpenInNewTab !== false,
  enableAnimation: true,
  animationDuration: HERO_ANIMATION_DURATION,
  ctaShimmer: true
});

const normalizedChips = computed(() => (local.chips || []).map(chip => String(chip || "").trim()).filter(Boolean));

const sectionOptions = computed(() => {
  const currentAnchor = local.anchorId;
  const raw = injectedSections?.value || [];
  const sectionPreview = (section: PageSection) => {
    const anySection = section as any;
    const candidate =
      anySection?.title ||
      anySection?.subtitle ||
      anySection?.description ||
      anySection?.headingLabel ||
      anySection?.text ||
      "";
    return String(candidate || "").replace(/<[^>]*>/g, "").trim() || "Sem prévia disponível";
  };
  return raw
    .filter((section: PageSection) => !!section?.anchorId && section.anchorId !== currentAnchor)
    .map((section: PageSection, index: number) => ({
      value: section.anchorId as string,
      label: `${index + 1}. ${sectionLabels[section.type] || section.type}`,
      preview: sectionPreview(section),
      section
    }));
});
const selectedSectionOption = computed(() =>
  sectionOptions.value.find(option => option.value === local.ctaSectionId) || null
);
const toggleSectionDropdown = () => {
  sectionDropdownOpen.value = !sectionDropdownOpen.value;
  if (!sectionDropdownOpen.value) hoveredSectionOption.value = null;
};
const selectSectionOption = (option: SectionOption) => {
  local.ctaSectionId = option.value;
  sectionDropdownOpen.value = false;
  hoveredSectionOption.value = null;
};
const closeDropdownOnOutside = (event: MouseEvent) => {
  if (!sectionDropdownOpen.value) return;
  const target = event.target as Node | null;
  if (!target || !sectionDropdownRef.value) return;
  if (!sectionDropdownRef.value.contains(target)) {
    sectionDropdownOpen.value = false;
    hoveredSectionOption.value = null;
  }
};
const closeDropdownOnEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    sectionDropdownOpen.value = false;
    hoveredSectionOption.value = null;
  }
};
onMounted(() => document.addEventListener("mousedown", closeDropdownOnOutside));
onMounted(() => document.addEventListener("keydown", closeDropdownOnEscape));
onBeforeUnmount(() => document.removeEventListener("mousedown", closeDropdownOnOutside));
onBeforeUnmount(() => document.removeEventListener("keydown", closeDropdownOnEscape));

let syncing = false;
const syncFromProps = (value: HeroSection) => {
  syncing = true;
  Object.assign(local, value);
  local.logoSize = value.logoSize ?? 64;
  local.logoBorderRadius = value.logoBorderRadius ?? 0;
  local.chips = value.chips ? [...value.chips] : [];
  local.layout = HERO_LAYOUT;
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  local.ctaOpenInNewTab = value.ctaOpenInNewTab !== false;
  local.enableAnimation = true;
  local.animationDuration = HERO_ANIMATION_DURATION;
  local.ctaShimmer = true;
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

const addChip = () => {
  const value = newChip.value.trim();
  if (!value) return;
  if (!Array.isArray(local.chips)) local.chips = [];
  local.chips.push(value);
  newChip.value = "";
};

const removeChip = (index: number) => {
  if (!Array.isArray(local.chips)) return;
  local.chips.splice(index, 1);
};

const previewUrl = (value?: string | null) => resolveMediaUrl(value || "") || value || "";

const ensureAgencyId = async () => {
  if (!agencyStore.currentAgencyId) {
    await agencyStore.loadAgencies().catch(() => undefined);
  }
  return agencyStore.currentAgencyId;
};

const clearMedia = (slot: "logo" | "background") => {
  if (slot === "logo") local.logoUrl = "";
  else local.backgroundImage = "";
};

const onMediaFileChange = async (slot: "logo" | "background", event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  uploadingSlot.value = slot;
  try {
    const agencyId = await ensureAgencyId();
    if (!agencyId) return;
    const asset = await uploadImageFile(file, agencyId);
    if (slot === "logo") local.logoUrl = asset.url;
    else local.backgroundImage = asset.url;
  } catch {
    /* noop */
  } finally {
    target.value = "";
    uploadingSlot.value = null;
  }
};

const colorOnly = (value?: string) => {
  if (!value) return "#41ce5f";
  const match = value.match(/#([0-9a-fA-F]{6})/);
  return match ? `#${match[1]}` : "#41ce5f";
};

const onColorPick = (event: Event) => {
  const target = event.target as HTMLInputElement;
  local.gradientColor = target.value;
};

const updateLogoSize = (delta: number) => {
  const current = local.logoSize || 64;
  const next = Math.min(160, Math.max(48, current + delta));
  local.logoSize = next;
};

const logoRadiusMax = computed(() => Math.round((local.logoSize || 64) / 2));

watch(
  () => local.logoSize,
  () => {
    const current = local.logoBorderRadius ?? 0;
    const max = logoRadiusMax.value;
    if (current > max) local.logoBorderRadius = max;
    if (current < 0) local.logoBorderRadius = 0;
  }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as HeroSection);
  },
  { deep: true }
);
</script>

<style scoped>
.hero-proto-body {
  --editor-tab-icon-size: 22px;
  --editor-tab-icon-font: 12px;
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 0;
  background: #f8faf9;
}

.tabs {
  padding: 16px 12px 16px 12px;
  border-right: 0;
  background: #fff;
  overflow-y: auto;
}

.tabs::-webkit-scrollbar,
.editor::-webkit-scrollbar,
.content-area::-webkit-scrollbar { width: 6px; }

.tabs::-webkit-scrollbar-thumb,
.editor::-webkit-scrollbar-thumb,
.content-area::-webkit-scrollbar-thumb {
  background: #dfe8e2;
  border-radius: 999px;
}

.tab {
  width: 100%;
  border: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 9px;
  border-radius: 14px;
  background: #eef3ef;
  color: #172132;
  font-weight: 700;
  margin-bottom: 6px;
  cursor: pointer;
  text-align: left;
}

.tab.active {
  background: #35d467;
  color: #073417;
}

.tab-icon {
  width: var(--editor-tab-icon-size);
  height: var(--editor-tab-icon-size);
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.62);
  font-size: var(--editor-tab-icon-font);
  flex: 0 0 auto;
}

.tab small {
  display: block;
  margin-top: -1px;
  color: inherit;
  opacity: .58;
  font-size: 9px;
  line-height: 1;
  font-weight: 600;
}


.editor {
  padding: 10px 14px;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  background: #f4f7f5;
}

.section-card {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #edf3ef;
}

.section-title {
  margin: 0 0 5px;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -.02em;
}

.section-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: #75867b;
}

.content-area {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}

.compact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.field { margin-bottom: 10px; }

label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #748379;
  font-weight: 800;
  margin-bottom: 6px;
}

.help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 1px solid #d8e3dc;
  color: #9aaaa0;
  font-size: 9px;
  font-weight: 900;
  cursor: help;
  margin-left: 2px;
}

.help:hover::after {
  content: attr(data-tip);
  position: absolute;
  transform: translateY(-140%);
  width: 230px;
  padding: 9px 10px;
  border-radius: 10px;
  background: #07111f;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
  text-transform: none;
  letter-spacing: 0;
  z-index: 10;
  box-shadow: 0 10px 24px rgba(7,17,31,.2);
}

input, select {
  width: 100%;
  height: 40px;
  border: 1px solid #dfe8e2;
  background: #fff;
  color: #172132;
  border-radius: 10px;
  padding: 0 11px;
  font-size: 14px;
}

.rich-box {
  border: 1px solid #dfe8e2;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.rich-box :deep(.ql-toolbar.ql-snow) {
  border: 0 !important;
  border-bottom: 1px solid #e6eee8 !important;
  background: #fbfdfc;
  padding: 4px 8px;
}

.rich-box :deep(.ql-toolbar .ql-formats) {
  margin-right: 8px;
}

.rich-box :deep(.ql-toolbar button) {
  width: 18px;
  height: 18px;
  padding: 2px;
}

.rich-box :deep(.ql-container.ql-snow) {
  border: 0 !important;
}

.rich-box :deep(.ql-editor) {
  min-height: 88px;
}

.inline-check {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64746a;
  font-size: 13px;
  font-weight: 800;
  margin-top: 8px;
  text-transform: none;
  letter-spacing: 0;
}

.inline-check input {
  width: 16px;
  height: 16px;
  min-height: 0;
  padding: 0;
  accent-color: #35d467;
}

.highlight-input-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.add-btn {
  height: 40px;
  padding: 0 14px;
  background: #f8fbf9;
  color: #173b25;
  border: 1px dashed #dfe8e2;
  border-radius: 8px;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 850;
}

.highlight-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 10px;
  border: 1px solid #dfe8e2;
  border-radius: 12px;
  background: #fff;
  min-height: 56px;
}

.highlight-tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 100%;
  padding: 5px 8px;
  border: 1px solid #dfe8e2;
  background: #f8fbf9;
  border-radius: 999px;
  color: #173b25;
  font-size: 11px;
  font-weight: 700;
}

.drag-handle {
  color: #9aaaa0;
  cursor: grab;
  font-weight: 950;
  line-height: 1;
}

.tag-remove {
  width: 16px;
  height: 16px;
  border: 0;
  border-radius: 999px;
  padding: 0;
  display: grid;
  place-items: center;
  color: #e13c3c;
  background: #ffe8e8;
  font-size: 11px;
  line-height: 1;
}

.tag-remove:hover { background: #ffd6d6; }

.pill-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  border: 1px solid #dfe8e2;
  background: #fff;
  border-radius: 12px;
  padding: 8px 11px;
  color: #516358;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.pill.active {
  background: #07111f;
  color: #fff;
  border-color: #07111f;
}

.list {
  display: flex;
  flex-direction: column;
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

.logo-size-inline-wrap {
  display: inline-flex;
  flex-direction: column;
  gap: 0;
  margin-right: 6px;
  align-self: center;
  position: relative;
  padding-bottom: 12px;
}

.logo-size-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.logo-size-inline input {
  width: 56px;
  height: 30px;
  min-height: 30px;
  padding: 0 6px;
  font-size: 13px;
}

.logo-size-inline button {
  min-width: 26px;
  height: 30px;
  min-height: 30px;
  padding: 0;
}

.logo-size-inline-label {
  position: absolute;
  left: 0;
  bottom: -1px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #74867a;
  line-height: 1;
  white-space: nowrap;
}

.color-input {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 8px;
  align-items: center;
}

.color-preview {
  width: 44px;
  height: 40px;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  appearance: none;
  -webkit-appearance: none;
}

.color-preview::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-preview::-webkit-color-swatch {
  border: 0;
  border-radius: 8px;
}

.section-dropdown {
  position: relative;
}

.section-dropdown-trigger {
  width: 100%;
  height: 40px;
  border: 1px solid #dfe8e2;
  background: #fff;
  color: #172132;
  border-radius: 10px;
  padding: 0 11px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  text-align: left;
}

.section-dropdown-arrow {
  color: #7b8e83;
  font-size: 14px;
}

.section-dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 40;
  width: 100%;
  max-height: 260px;
  overflow-y: auto;
  border: 1px solid #dfe8e2;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(12, 24, 18, 0.14);
}

.section-dropdown-item {
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  padding: 8px 11px;
  color: #1c2a22;
  font-size: 14px;
}

.section-dropdown-item:hover {
  background: #eef6f1;
}

.section-hover-preview {
  position: absolute;
  top: 0;
  right: calc(100% + 8px);
  width: 260px;
  border: 1px solid #d8e4dc;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(8, 19, 14, 0.16);
  padding: 10px 11px;
  z-index: 41;
}

.section-hover-preview strong {
  display: block;
  font-size: 13px;
  color: #102018;
  margin-bottom: 4px;
}

.section-hover-preview p {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: #5f7167;
}

.section-card--dropdown-open,
.section-card--dropdown-open .content-area {
  overflow: visible !important;
}

@media (max-width: 800px) {
  .hero-proto-body { grid-template-columns: 1fr; grid-template-rows: auto 1fr; }
  .tabs { display: flex; gap: 8px; overflow-x: auto; border-right: 0; border-bottom: 0; padding-left: 16px; padding-right: 8px; margin-bottom: 8px; }
  .tab { min-width: 96px; min-height: 38px; margin-bottom: 0; padding: 8px 7px; }
  .tab > span:last-child { display: inline; font-size: 12px; line-height: 1.1; }
  .tab > span:last-child small { display: none; }
  .compact-grid { grid-template-columns: 1fr; }
  .media-item { grid-template-columns: 70px 1fr; }
  .media-item .btn-row {
    grid-column: 1 / -1;
    width: 100%;
    justify-content: flex-start;
    flex-wrap: nowrap;
    gap: 4px;
    margin-top: 2px;
  }
  .media-item .btn-row > button {
    height: 28px;
    padding: 0 8px;
    font-size: 11px;
  }
  .logo-size-inline-wrap {
    width: auto;
    margin-right: 6px;
    padding-bottom: 0;
    flex: 0 0 auto;
  }
  .logo-size-inline-label {
    position: static;
    margin-top: 2px;
    font-size: 9px;
  }
  .logo-size-inline {
    gap: 4px;
  }
  .logo-size-inline input {
    width: 48px;
    height: 28px;
    min-height: 28px;
    font-size: 12px;
  }
  .logo-size-inline button {
    min-width: 24px;
    height: 28px;
    min-height: 28px;
  }
}
</style>
