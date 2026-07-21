<template>
  <div class="banner-form-shell">
    <aside class="banner-form-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="banner-nav-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="banner-nav-icon">{{ tab.icon }}</span>
        <span>
          <strong>{{ tab.title }}</strong>
          <small>{{ tab.subtitle }}</small>
        </span>
      </button>
    </aside>

    <section class="banner-form-content">
      <template v-if="activeTab === 'text'">
        <h4 class="banner-form-title">Textos do banner</h4>
        <p class="banner-form-subtitle">Edite o título principal, o texto de apoio e os destaques exibidos no banner.</p>

        <div class="banner-field-group">
          <label class="banner-label">Título principal <span class="hint-dot">?</span></label>
          <input v-model="local.title" class="banner-input" placeholder="Vamos para Treze Tílias em Setembro?!" />
        </div>

        <div class="banner-field-group">
          <label class="banner-label">Texto de apoio <span class="hint-dot">?</span></label>
          <RichTextEditor v-model="local.subtitle" placeholder="Descreva rapidamente o convite do banner." />
        </div>

        <div class="banner-field-group">
          <label class="banner-label">Destaques <span class="hint-dot">?</span></label>
          <div class="banner-highlight-row">
            <input
              v-model="newHighlight"
              class="banner-input"
              placeholder="Ex: Últimas vagas"
              @keydown.enter.prevent="addHighlight"
            />
            <button type="button" class="banner-outline-btn" @click="addHighlight">Adicionar</button>
          </div>
          <div class="banner-chip-wrap">
            <span v-for="(item, index) in local.highlights" :key="`${item}-${index}`" class="banner-chip">
              {{ item }}
              <button type="button" @click="removeHighlight(index)">×</button>
            </span>
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'images'">
        <div class="section-head">
          <div>
            <h2 class="section-title">Imagens do banner</h2>
            <p class="section-desc">Envie imagem para desktop, mobile e logo da agência, além da cor de escurecimento.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="list">
            <div class="media-item">
            <img v-if="previewUrl(local.backgroundImage)" :src="previewUrl(local.backgroundImage) || ''" alt="Imagem para desktop" />
            <div v-else class="media-fallback">Desktop</div>
            <div class="media-info">
              <strong>Imagem para desktop <span class="hint-dot">?</span></strong>
              <p>Versão exibida em telas maiores.</p>
            </div>
            <div class="btn-row">
              <input ref="desktopInput" type="file" accept="image/*" class="hidden" @change="onMediaFileChange('desktop', $event)" />
              <button type="button" @click="desktopInput?.click()">{{ uploadingSlot === "desktop" ? "Enviando..." : "Substituir" }}</button>
              <button type="button" class="danger" @click="clearMedia('desktop')">Remover</button>
            </div>
            </div>

            <div class="media-item">
            <img v-if="previewUrl(local.mobileBackgroundImage)" :src="previewUrl(local.mobileBackgroundImage) || ''" alt="Imagem para mobile" />
            <div v-else class="media-fallback">Mobile</div>
            <div class="media-info">
              <strong>Imagem para mobile <span class="hint-dot">?</span></strong>
              <p>Versão otimizada para celular.</p>
            </div>
            <div class="btn-row">
              <input ref="mobileInput" type="file" accept="image/*" class="hidden" @change="onMediaFileChange('mobile', $event)" />
              <button type="button" @click="mobileInput?.click()">{{ uploadingSlot === "mobile" ? "Enviando..." : "Substituir" }}</button>
              <button type="button" class="danger" @click="clearMedia('mobile')">Remover</button>
            </div>
            </div>

            <div class="media-item">
            <img v-if="previewUrl(local.logoImage)" :src="previewUrl(local.logoImage) || ''" alt="Logo da agência" />
            <div v-else class="media-fallback">Logo</div>
            <div class="media-info">
              <strong>Logo da agência <span class="hint-dot">?</span></strong>
              <p>Logo exibida sobre o banner.</p>
            </div>
            <div class="btn-row">
              <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="onMediaFileChange('logo', $event)" />
              <button type="button" @click="logoInput?.click()">{{ uploadingSlot === "logo" ? "Enviando..." : "Substituir" }}</button>
              <button type="button" class="danger" @click="clearMedia('logo')">Remover</button>
            </div>
            </div>
          </div>

          <div class="compact-grid" style="margin-top:12px;">
            <div class="field">
              <label>Posição da imagem <span class="hint-dot">?</span></label>
            <select v-model="local.imagePosition" class="banner-input">
              <option value="center">Centro</option>
              <option value="top">Topo</option>
              <option value="bottom">Base</option>
              <option value="left">Esquerda</option>
              <option value="right">Direita</option>
              <option value="center top">Centro superior</option>
              <option value="center bottom">Centro inferior</option>
            </select>
            </div>
            <div class="field">
              <label>Cor de escurecimento <span class="hint-dot">?</span></label>
            <div class="banner-color-row">
              <input type="color" v-model="local.gradientColor" class="banner-color" />
              <input v-model="local.gradientColor" class="banner-input" />
            </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <h4 class="banner-form-title">Botão de ação do banner</h4>
        <p class="banner-form-subtitle">Defina o convite principal da seção e para onde o visitante será direcionado ao clicar.</p>

        <div class="banner-button-content" :class="{ 'banner-button-content--dropdown-open': sectionDropdownOpen }">
        <label class="banner-check">
          <input type="checkbox" v-model="local.ctaEnabled" />
          Exibir botão de CTA
        </label>

        <template v-if="local.ctaEnabled !== false">
        <div class="banner-field-group">
          <label class="banner-label">Tipo de ação <span class="hint-dot">?</span></label>
          <div class="banner-pill-row">
            <button
              type="button"
              class="banner-pill"
              :class="{ active: local.ctaMode !== 'section' }"
              @click="local.ctaMode = 'link'"
            >
              WhatsApp / Link externo
            </button>
            <button
              type="button"
              class="banner-pill"
              :class="{ active: local.ctaMode === 'section' }"
              @click="local.ctaMode = 'section'"
            >
              Ir para seção
            </button>
          </div>
        </div>

        <div class="banner-grid-2">
          <div>
            <label class="banner-label">Texto do botão <span class="hint-dot">?</span></label>
            <input v-model="local.ctaLabel" class="banner-input" placeholder="Quero falar no WhatsApp" />
          </div>
          <div>
            <label class="banner-label">Destino do clique <span class="hint-dot">?</span></label>
            <template v-if="local.ctaMode === 'section'">
              <div ref="sectionDropdownRef" class="section-dropdown">
                <button type="button" class="section-dropdown-trigger banner-input" @click="toggleSectionDropdown">
                  <span>{{ selectedSectionOption?.label || "Selecione uma seção" }}</span>
                  <span class="section-dropdown-arrow">▾</span>
                </button>
                <div v-if="sectionDropdownOpen" class="section-dropdown-menu">
                  <button
                    v-for="option in sectionOptions"
                    :key="option.value"
                    type="button"
                    class="section-dropdown-item"
                    @mouseenter="hoveredSectionOption = option"
                    @mouseleave="hoveredSectionOption = null"
                    @click="selectSectionOption(option)"
                  >
                    {{ option.label }}
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
              <input v-model="local.ctaLink" class="banner-input" placeholder="https://wa.me/5553123456788" />
            </template>
          </div>
        </div>

        <label class="banner-check mt-2" v-if="local.ctaMode !== 'section'">
          <input type="checkbox" v-model="local.ctaOpenInNewTab" />
          Abrir em nova aba
        </label>
        </template>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import type { BannerCardSection, PageSection } from "../../types/page";
import { sectionsInjectionKey } from "./sectionsContext";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { useAgencyStore } from "../../store/useAgencyStore";
import { resolveMediaUrl, uploadImageFile } from "../../utils/media";
import { sectionLabels } from "../../utils/sectionLabels";
import SectionHoverVisualPreview from "./SectionHoverVisualPreview.vue";

type BannerEditorTab = "text" | "images" | "button";

type BannerCardSectionExtended = BannerCardSection & {
  highlights?: string[];
  mobileBackgroundImage?: string;
  logoImage?: string;
  imagePosition?: "center" | "left" | "right" | "top" | "bottom";
};
type SectionOption = { value: string; label: string; preview: string; section: PageSection };

const props = defineProps<{ modelValue: BannerCardSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: BannerCardSection): void }>();

const activeTab = ref<BannerEditorTab>("text");
const newHighlight = ref("");
const injectedSections = inject(sectionsInjectionKey, null);
const agencyStore = useAgencyStore();
const desktopInput = ref<HTMLInputElement | null>(null);
const mobileInput = ref<HTMLInputElement | null>(null);
const logoInput = ref<HTMLInputElement | null>(null);
const uploadingSlot = ref<"desktop" | "mobile" | "logo" | null>(null);
const sectionDropdownOpen = ref(false);
const hoveredSectionOption = ref<SectionOption | null>(null);
const sectionDropdownRef = ref<HTMLElement | null>(null);

const tabs: Array<{ id: BannerEditorTab; title: string; subtitle: string; icon: string }> = [
  { id: "text", title: "Textos", subtitle: "Chamada principal", icon: "✎" },
  { id: "images", title: "Imagens", subtitle: "Visual do banner", icon: "▧" },
  { id: "button", title: "Botão", subtitle: "Ação do visitante", icon: "↗" }
];

const ensureColor = (value: string | undefined, fallback: string) => (value && value.trim() ? value : fallback);

const local = reactive<BannerCardSectionExtended>({
  ...(props.modelValue as BannerCardSectionExtended),
  enabled: props.modelValue.enabled ?? true,
  title: props.modelValue.title || "Conte com especialistas para transformar o seu roteiro.",
  subtitle: props.modelValue.subtitle || "",
  ctaLabel: props.modelValue.ctaLabel || "Quero saber mais",
  ctaLink: props.modelValue.ctaLink || "https://wa.me/",
  ctaColor: ensureColor(props.modelValue.ctaColor, "#41ce5f"),
  gradientColor: ensureColor(props.modelValue.gradientColor, "#0b0f19"),
  backgroundColor: ensureColor(props.modelValue.backgroundColor, "#020617"),
  cardBackground: ensureColor(props.modelValue.cardBackground, "rgba(5,6,15,0.88)"),
  cardBorderColor: ensureColor(props.modelValue.cardBorderColor, "rgba(255,255,255,0.25)"),
  textColor: ensureColor(props.modelValue.textColor, "rgba(255,255,255,0.85)"),
  ctaEnabled: props.modelValue.ctaEnabled !== false,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null,
  ctaOpenInNewTab: props.modelValue.ctaOpenInNewTab !== false,
  highlights: Array.isArray((props.modelValue as any).highlights) ? [...(props.modelValue as any).highlights] : [],
  mobileBackgroundImage: (props.modelValue as any).mobileBackgroundImage || "",
  logoImage: (props.modelValue as any).logoImage || "",
  imagePosition: ((props.modelValue as any).imagePosition as BannerCardSectionExtended["imagePosition"]) || "center"
});

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

const addHighlight = () => {
  const value = newHighlight.value.trim();
  if (!value) return;
  if (!Array.isArray(local.highlights)) local.highlights = [];
  local.highlights.push(value);
  newHighlight.value = "";
};

const removeHighlight = (index: number) => {
  if (!Array.isArray(local.highlights)) return;
  local.highlights.splice(index, 1);
};

const previewUrl = (value?: string | null) => resolveMediaUrl(value || "") || value || "";

const ensureAgencyId = async () => {
  if (!agencyStore.currentAgencyId) {
    await agencyStore.loadAgencies().catch(() => undefined);
  }
  return agencyStore.currentAgencyId;
};

const assignMediaValue = (slot: "desktop" | "mobile" | "logo", value: string) => {
  if (slot === "desktop") local.backgroundImage = value;
  else if (slot === "mobile") local.mobileBackgroundImage = value;
  else local.logoImage = value;
};

const clearMedia = (slot: "desktop" | "mobile" | "logo") => {
  assignMediaValue(slot, "");
};

const onMediaFileChange = async (slot: "desktop" | "mobile" | "logo", event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  uploadingSlot.value = slot;
  try {
    const agencyId = await ensureAgencyId();
    if (!agencyId) return;
    const asset = await uploadImageFile(file, agencyId);
    assignMediaValue(slot, asset.url);
  } catch {
    /* noop */
  } finally {
    target.value = "";
    uploadingSlot.value = null;
  }
};

let syncing = false;
const syncFromProps = (value: BannerCardSection) => {
  syncing = true;
  const extended = value as BannerCardSectionExtended;
  Object.assign(local, extended);
  local.enabled = value.enabled ?? true;
  local.title = value.title || "Conte com especialistas para transformar o seu roteiro.";
  local.subtitle = value.subtitle || "";
  local.ctaLabel = value.ctaLabel || "Quero saber mais";
  local.ctaLink = value.ctaLink || "https://wa.me/";
  local.ctaColor = ensureColor(value.ctaColor, "#41ce5f");
  local.gradientColor = ensureColor(value.gradientColor, "#0b0f19");
  local.backgroundColor = ensureColor(value.backgroundColor, "#020617");
  local.cardBackground = ensureColor(value.cardBackground, "rgba(5,6,15,0.88)");
  local.cardBorderColor = ensureColor(value.cardBorderColor, "rgba(255,255,255,0.25)");
  local.textColor = ensureColor(value.textColor, "rgba(255,255,255,0.85)");
  local.ctaEnabled = value.ctaEnabled !== false;
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  local.ctaOpenInNewTab = value.ctaOpenInNewTab !== false;
  local.highlights = Array.isArray((extended as any).highlights) ? [...((extended as any).highlights as string[])] : [];
  local.mobileBackgroundImage = (extended as any).mobileBackgroundImage || "";
  local.logoImage = (extended as any).logoImage || "";
  local.imagePosition = (extended as any).imagePosition || "center";
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
    emit("update:modelValue", value as BannerCardSection);
  },
  { deep: true }
);
</script>

<style scoped>
.banner-form-shell {
  --editor-tab-icon-size: 22px;
  --editor-tab-icon-font: 12px;
  display: grid;
  grid-template-columns: 178px minmax(0, 1fr);
  gap: 0;
  height: 100%;
  min-height: 56vh;
}

.banner-form-nav {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
}

.banner-nav-item {
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

.banner-nav-item.active {
  background: #34c759;
  border-color: #34c759;
}

.banner-nav-icon {
  width: var(--editor-tab-icon-size);
  height: var(--editor-tab-icon-size);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--editor-tab-icon-font);
}

.banner-nav-item strong {
  display: block;
  font-size: 15px;
  line-height: 1.15;
  font-weight: 700;
}

.banner-nav-item small {
  display: block;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
  margin-top: 0;
  font-weight: 600;
}

.banner-form-content {
  padding: 10px 14px;
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
  font-weight: 950;
  letter-spacing: -0.02em;
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

.field {
  margin-bottom: 10px;
}

.banner-form-title {
  font-size: 16px;
  line-height: 1.1;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
}

.banner-form-subtitle {
  margin-top: 2px;
  color: #607284;
  font-size: 12px;
}

.banner-field-group {
  margin-top: 14px;
}

.banner-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5f7380;
  font-size: 11px;
  font-weight: 800;
  margin-bottom: 6px;
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

.banner-input {
  width: 100%;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  padding: 9px 12px;
  font-size: 14px;
  line-height: 1.2;
  background: #fff;
}

.banner-highlight-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.banner-outline-btn {
  border: 1px dashed #c9d4ce;
  border-radius: 10px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 700;
}

.banner-chip-wrap {
  margin-top: 8px;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  min-height: 56px;
  padding: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.banner-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  border: 1px solid #cad5cf;
  background: #f1f5f2;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
}

.banner-chip button {
  color: #ef4444;
  font-weight: 700;
}

.banner-grid-2 {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.banner-media-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.media-item img {
  width: 86px;
  height: 58px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
}

.media-fallback {
  width: 86px;
  height: 58px;
  border-radius: 8px;
  background: #e3ebe6;
  color: #6b7f74;
  font-size: 11px;
  font-weight: 800;
  display: grid;
  place-items: center;
}

.media-info {
  min-width: 0;
}

.media-info strong {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 3px;
  font-size: 13px;
  font-weight: 700;
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
  align-items: center;
}

.btn-row button {
  border: 1px solid #dfe8e2;
  border-radius: 8px;
  padding: 7px 10px;
  background: #fff;
  color: #223228;
  font-size: 12px;
  font-weight: 850;
}

.btn-row button.danger {
  background: #fff1f1;
  color: #e13c3c;
  border-color: #ffd4d4;
}

.banner-color-row {
  display: grid;
  grid-template-columns: 46px 1fr;
  gap: 8px;
}

.banner-color {
  width: 46px;
  height: 40px;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  appearance: none;
  -webkit-appearance: none;
}

.banner-color::-webkit-color-swatch-wrapper {
  padding: 0;
}

.banner-color::-webkit-color-swatch {
  border: 0;
  border-radius: 8px;
}

.banner-pill-row {
  display: flex;
  gap: 8px;
}

.banner-pill {
  border-radius: 999px;
  border: 1px solid #c9d4ce;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 700;
  background: #fff;
}

.banner-pill.active {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--primary-foreground);
}

.banner-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #4d6a60;
  font-size: 11px;
  line-height: 1.1;
  font-weight: 800;
}

.banner-button-content--dropdown-open,
.banner-button-content--dropdown-open .content-area {
  overflow: visible !important;
}

.section-dropdown {
  position: relative;
}

.section-dropdown-trigger {
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
  border: 1px solid #c9d4ce;
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

.banner-form-shell,
.banner-form-content {
  background: var(--background);
  color: var(--foreground);
}

.banner-form-nav {
  border-color: var(--border);
  background: var(--card);
}

.banner-nav-item {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.banner-nav-item.active {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
}

.banner-nav-item small,
.banner-form-subtitle,
.section-desc,
.media-info p {
  color: var(--muted-foreground);
}

.banner-form-title,
.section-title,
.media-info strong {
  color: var(--foreground);
}

.section-head {
  border-color: color-mix(in srgb, var(--border) 62%, transparent);
}

.banner-input,
.section-dropdown-trigger {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}

.banner-outline-btn,
.btn-row button,
.banner-pill {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.banner-outline-btn:hover,
.btn-row button:hover,
.banner-pill:hover {
  border-color: color-mix(in srgb, var(--primary) 38%, var(--border));
  background: var(--accent);
}

.banner-chip-wrap,
.media-item {
  border-color: var(--border);
  background: var(--card);
}

.banner-chip,
.media-fallback {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}

.btn-row button.danger {
  border-color: color-mix(in srgb, var(--destructive) 35%, var(--border));
  background: color-mix(in srgb, var(--destructive) 10%, var(--card));
  color: var(--destructive);
}

.btn-row button.danger:hover {
  border-color: color-mix(in srgb, var(--destructive) 55%, var(--border));
  background: color-mix(in srgb, var(--destructive) 18%, var(--card));
}

.banner-pill.active {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
}

.section-dropdown-menu,
.section-hover-preview {
  border-color: var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

.section-dropdown-item,
.section-hover-preview strong {
  color: var(--popover-foreground);
}

.section-dropdown-item:hover {
  background: var(--accent);
  color: var(--accent-foreground);
}

.section-hover-preview p {
  color: var(--muted-foreground);
}

@media (max-width: 900px) {
  .banner-form-shell {
    grid-template-columns: 1fr;
    min-height: 100%;
    height: 100%;
    align-content: start;
    grid-auto-rows: min-content;
    background: var(--background);
  }

  .banner-form-nav {
    border-right: 0;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    align-items: stretch;
    gap: 8px;
    overflow-x: hidden;
    padding: 8px 8px 0 16px;
    margin-bottom: 12px;
    background: var(--card);
  }

  .banner-nav-item {
    min-width: 0;
    flex: 0 0 calc((100% - 16px) / 3);
    width: calc((100% - 16px) / 3);
    height: 40px;
    min-height: 40px;
    justify-content: flex-start;
    padding: 0 10px;
    border-radius: 13px;
    gap: 8px;
  }

  .banner-nav-item > span:last-child {
    display: inline-flex;
    font-size: 12px;
    line-height: 1.1;
    align-items: center;
  }

  .banner-nav-item > span:last-child small {
    display: none;
  }

  .banner-form-content {
    background: #edf1ef;
    padding: 0 10px 10px;
    margin-top: 4px;
  }

  .banner-grid-2,
  .compact-grid {
    grid-template-columns: 1fr;
  }

  .btn-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>
