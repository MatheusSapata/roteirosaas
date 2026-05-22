<template>
  <div class="story-form-shell">
    <aside class="story-form-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="story-nav-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="story-nav-icon">{{ tab.icon }}</span>
        <span>
          <strong>{{ tab.title }}</strong>
          <small>{{ tab.subtitle }}</small>
        </span>
      </button>
    </aside>

    <section class="story-form-content">
      <template v-if="activeTab === 'text'">
        <h4 class="story-form-title">Textos da seção</h4>
        <p class="story-form-subtitle">Edite a etiqueta, o título e o texto descritivo exibido ao lado das imagens.</p>

        <div class="story-field-group">
          <label class="story-label with-optional">
            <span>Etiqueta acima do título</span>
            <small>opcional</small>
            <span class="hint-dot hint-help" data-tip="Texto curto exibido acima do título principal.">?</span>
          </label>
          <input v-model="local.headingLabel" class="story-input" />
        </div>

        <div class="story-field-group">
          <label class="story-label">Título principal <span class="hint-dot hint-help" data-tip="Título de maior destaque da seção.">?</span></label>
          <input v-model="local.title" class="story-input" />
        </div>

        <div class="story-field-group">
          <label class="story-label">Descrição completa <span class="hint-dot hint-help" data-tip="Texto descritivo exibido ao lado da galeria.">?</span></label>
          <div class="story-rich-shell">
            <RichTextEditor v-model="local.subtitle" placeholder="Conte a história da agência..." />
          </div>
        </div>

        <div class="story-field-group">
          <label class="story-label">Posição do texto <span class="hint-dot hint-help" data-tip="Define em qual lado o texto aparece em relação às imagens.">?</span></label>
          <div class="story-position-grid">
            <button type="button" class="story-position-card" :class="{ active: local.imagePosition === 'right' }" @click="local.imagePosition = 'right'">
              <span class="story-position-icon">
                <span class="wf-box wf-box--media"></span>
                <span class="wf-box wf-box--text">
                  <span></span><span></span>
                </span>
              </span>
              <span>
                <strong>Texto à direita</strong>
                <small>Galeria à esquerda e texto ao lado.</small>
              </span>
            </button>
            <button type="button" class="story-position-card" :class="{ active: local.imagePosition === 'left' }" @click="local.imagePosition = 'left'">
              <span class="story-position-icon story-position-icon--reverse">
                <span class="wf-box wf-box--media"></span>
                <span class="wf-box wf-box--text">
                  <span></span><span></span>
                </span>
              </span>
              <span>
                <strong>Texto à esquerda</strong>
                <small>Texto primeiro e galeria ao lado.</small>
              </span>
            </button>
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'media'">
        <h4 class="story-form-title">Imagens e vídeos</h4>
        <p class="story-form-subtitle">Gerencie a galeria e vídeos exibidos nesta seção.</p>

        <div class="story-media-shell">
          <label class="story-label">Galeria de imagens <span class="hint-dot hint-help" data-tip="A primeira imagem é tratada como destaque.">?</span></label>
          <input
            ref="storyBulkImageInputRef"
            type="file"
            accept="image/*"
            multiple
            class="hidden"
            @change="onBulkStoryImagesSelected"
          />
          <input
            ref="storyReplaceImageInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onReplaceStoryImageSelected"
          />
          <div class="story-gallery-grid">
            <div v-for="(image, index) in local.images" :key="`story-image-${index}`" class="story-gallery-card">
              <div class="story-gallery-head">
                <span>{{ index === 0 ? "Imagem 1" : `Imagem ${index + 1}` }}</span>
                <span v-if="index === 0" class="story-gallery-badge">Destaque</span>
              </div>
              <div class="story-gallery-preview">
                <img v-if="image" :src="image" :alt="`Imagem ${index + 1}`" />
                <span v-else class="story-thumb-empty">Sem imagem</span>
              </div>
              <div class="story-gallery-actions">
                <button type="button" class="story-link-mini" @click="openImageEditor(index)">Editar</button>
                <button type="button" class="story-link-mini danger" @click="removeStoryImage(index)">Remover</button>
              </div>
            </div>
          </div>
          <button type="button" class="story-add-outline" @click="storyBulkImageInputRef?.click()">+ Adicionar imagem</button>
          <p v-if="bulkImageError" class="story-bulk-error">{{ bulkImageError }}</p>
        </div>

        <div class="story-media-shell mt-2">
          <label class="story-label">Vídeos do YouTube <span class="hint-dot hint-help" data-tip="Cole links públicos do YouTube.">?</span></label>
          <div v-if="local.videoUrls?.length" class="story-video-list">
            <div v-for="(video, index) in local.videoUrls" :key="`video-${index}`" class="story-video-row">
              <input v-model="local.videoUrls[index]" placeholder="https://www.youtube.com/watch?v=..." class="story-input" />
              <button type="button" class="story-mini-btn danger" @click="removeVideoField(index)">Remover</button>
            </div>
          </div>
          <div v-else class="story-empty">Nenhum vídeo adicionado ainda.</div>
          <button type="button" class="story-add-outline" @click="addVideoField">+ Adicionar vídeo</button>
        </div>

      </template>

      <template v-else>
        <h4 class="story-form-title">Botão da seção</h4>
        <p class="story-form-subtitle">Defina se haverá CTA e para onde o visitante será direcionado.</p>

        <label class="story-inline-check mb-2">
          <input type="checkbox" v-model="local.ctaEnabled" />
          Inserir botão de CTA
        </label>

        <div v-if="local.ctaEnabled" class="story-cta-shell story-button-panel" :class="{ 'story-cta-shell--dropdown-open': sectionDropdownOpen }">
          <div class="story-field-group">
            <label class="story-label">Tipo de ação <span class="hint-dot hint-help" data-tip="Escolha entre link externo/WhatsApp ou seção interna.">?</span></label>
            <div class="story-pill-row">
              <button type="button" class="story-pill" :class="{ active: local.ctaMode !== 'section' }" @click="local.ctaMode = 'link'">
                WhatsApp / Link externo
              </button>
              <button type="button" class="story-pill" :class="{ active: local.ctaMode === 'section' }" @click="local.ctaMode = 'section'">
                Ir para seção
              </button>
            </div>
          </div>

          <div class="story-grid-2">
            <div>
              <label class="story-label">Texto do botão <span class="hint-dot hint-help" data-tip="Texto exibido no botão de chamada.">?</span></label>
              <input v-model="local.ctaLabel" class="story-input" />
            </div>
            <div>
              <label class="story-label">Destino do clique <span class="hint-dot hint-help" data-tip="URL externa ou âncora de seção.">?</span></label>
              <template v-if="local.ctaMode === 'section'">
                <div ref="sectionDropdownRef" class="section-dropdown">
                  <button type="button" class="section-dropdown-trigger story-input" @click="toggleSectionDropdown">
                    <span>{{ selectedSectionOption?.label || 'Selecione uma seção' }}</span>
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
                    <SectionHoverVisualPreview :label="hoveredSectionOption.label" :section="hoveredSectionOption.section" />
                  </div>
                </div>
              </template>
              <template v-else>
                <input v-model="local.ctaLink" class="story-input" />
              </template>
            </div>
          </div>

          <label class="story-inline-check mt-2" v-if="local.ctaMode !== 'section'">
            <input type="checkbox" v-model="local.ctaOpenInNewTab" />
            Abrir em nova aba
          </label>
        </div>
      </template>

    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import SectionHoverVisualPreview from "./SectionHoverVisualPreview.vue";
import { sectionsInjectionKey } from "./sectionsContext";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import { sectionLabels } from "../../utils/sectionLabels";
import { useAgencyStore } from "../../store/useAgencyStore";
import { uploadImageFile } from "../../utils/media";
import type { PageSection, StorySection } from "../../types/page";

type StoryEditorTab = "text" | "media" | "button";
type SectionOption = { value: string; label: string; preview: string; section: PageSection };

const props = defineProps<{ modelValue: StorySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: StorySection): void }>();
const headingDefaults = getSectionHeadingDefaults("story");
const injectedSections = inject(sectionsInjectionKey, null);
const agencyStore = useAgencyStore();

const tabs: Array<{ id: StoryEditorTab; title: string; subtitle: string; icon: string }> = [
  { id: "text", title: "Textos", subtitle: "Conteúdo da seção", icon: "✎" },
  { id: "media", title: "Mídia", subtitle: "Imagens e vídeos", icon: "▧" },
  { id: "button", title: "Botão", subtitle: "Chamada final", icon: "↗" }
];

const activeTab = ref<StoryEditorTab>("text");
const storyBulkImageInputRef = ref<HTMLInputElement | null>(null);
const storyReplaceImageInputRef = ref<HTMLInputElement | null>(null);
const storyReplaceImageIndex = ref<number | null>(null);
const bulkImageError = ref("");
const sectionDropdownOpen = ref(false);
const hoveredSectionOption = ref<SectionOption | null>(null);
const sectionDropdownRef = ref<HTMLElement | null>(null);

const normalizeVideoList = (section: StorySection) => {
  const list = Array.isArray(section.videoUrls) ? [...section.videoUrls] : [];
  if (!list.length && typeof section.videoUrl === "string" && section.videoUrl.trim().length > 0) {
    list.push(section.videoUrl);
  }
  return list;
};

const local = reactive<StorySection>({
  type: "story",
  layout: "single",
  enabled: true,
  images: [],
  videoUrls: normalizeVideoList(props.modelValue),
  ctaEnabled: true,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  ...props.modelValue,
  enableAnimation: true,
  ctaShimmer: true,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId || null,
  ctaOpenInNewTab: props.modelValue.ctaOpenInNewTab !== false
});

const sectionOptions = computed(() => {
  const currentAnchor = local.anchorId;
  const raw = injectedSections?.value || [];
  const sectionPreview = (section: PageSection) => {
    const anySection = section as any;
    const candidate =
      anySection?.title || anySection?.subtitle || anySection?.description || anySection?.headingLabel || anySection?.text || "";
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

const countValidImages = (images?: string[]) =>
  Array.isArray(images) ? images.filter(img => typeof img === "string" && img.trim().length > 0).length : 0;

const countValidVideos = (videos?: string[]) =>
  Array.isArray(videos) ? videos.filter(video => typeof video === "string" && video.trim().length > 0).length : 0;

const determineLayoutFromMedia = () =>
  countValidImages(local.images) + countValidVideos(local.videoUrls) > 1 ? "gallery" : "single";

const applyAutomaticLayout = () => {
  const desired = determineLayoutFromMedia();
  if (local.layout !== desired) local.layout = desired;
};

let syncing = false;
const syncFromProps = (value: StorySection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.images = Array.isArray(value.images) ? [...value.images] : [];
  local.videoUrls = normalizeVideoList(value);
  local.videoUrl = local.videoUrls[0] || "";
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId || null;
  local.ctaOpenInNewTab = value.ctaOpenInNewTab !== false;
  local.enableAnimation = true;
  local.ctaShimmer = true;
  applyAutomaticLayout();
  nextTick(() => {
    syncing = false;
  });
};

const addVideoField = () => {
  if (!Array.isArray(local.videoUrls)) local.videoUrls = [];
  local.videoUrls.push("");
};

const ensureAgencyId = async () => {
  if (!agencyStore.currentAgencyId) {
    await agencyStore.loadAgencies().catch(() => undefined);
  }
  return agencyStore.currentAgencyId;
};

const onBulkStoryImagesSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files || []);
  if (!files.length) return;
  bulkImageError.value = "";
  if (!Array.isArray(local.images)) local.images = [];
  const agencyId = await ensureAgencyId();
  if (!agencyId) {
    bulkImageError.value = "Selecione ou crie uma agência antes de enviar imagens.";
    target.value = "";
    return;
  }
  let successCount = 0;
  for (const file of files) {
    try {
      const asset = await uploadImageFile(file, agencyId);
      if (asset?.url) {
        local.images.push(asset.url);
        successCount += 1;
      }
    } catch {
      bulkImageError.value = "Algumas imagens não foram enviadas. Tente novamente.";
    }
  }
  if (!successCount && !bulkImageError.value) {
    bulkImageError.value = "Não foi possível enviar as imagens selecionadas.";
  }
  target.value = "";
};

const removeStoryImage = (index: number) => {
  if (!Array.isArray(local.images)) return;
  local.images = local.images.filter((_, i) => i !== index);
};

const openImageEditor = (index: number) => {
  storyReplaceImageIndex.value = index;
  storyReplaceImageInputRef.value?.click();
};

const onReplaceStoryImageSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  target.value = "";
  if (!file || storyReplaceImageIndex.value === null) return;

  const agencyId = await ensureAgencyId();
  if (!agencyId) {
    bulkImageError.value = "Selecione ou crie uma agência antes de enviar imagens.";
    storyReplaceImageIndex.value = null;
    return;
  }

  try {
    const asset = await uploadImageFile(file, agencyId);
    if (asset?.url && Array.isArray(local.images) && storyReplaceImageIndex.value < local.images.length) {
      local.images[storyReplaceImageIndex.value] = asset.url;
    }
  } catch {
    bulkImageError.value = "Não foi possível substituir a imagem. Tente novamente.";
  } finally {
    storyReplaceImageIndex.value = null;
  }
};

const removeVideoField = (index: number) => {
  if (!Array.isArray(local.videoUrls)) return;
  local.videoUrls = local.videoUrls.filter((_, i) => i !== index);
  local.videoUrl = local.videoUrls[0] || "";
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
  () => local.videoUrls,
  () => {
    if (syncing) return;
    local.videoUrl = Array.isArray(local.videoUrls) && local.videoUrls.length ? local.videoUrls[0] : "";
    applyAutomaticLayout();
  },
  { deep: true }
);

watch(
  () => local.images,
  () => {
    if (syncing) return;
    applyAutomaticLayout();
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as StorySection);
  },
  { deep: true }
);
</script>

<style scoped>
.story-form-shell {
  --editor-tab-icon-size: 22px;
  --editor-tab-icon-font: 12px;
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 56vh;
}

.story-form-nav {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
}

.story-nav-item {
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

.story-nav-item.active {
  background: #34c759;
  border-color: #34c759;
}

.story-nav-icon {
  width: var(--editor-tab-icon-size);
  height: var(--editor-tab-icon-size);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--editor-tab-icon-font);
}

.story-nav-item strong {
  display: block;
  font-size: 16px;
  line-height: 0.95;
  font-weight: 700;
}

.story-nav-item small {
  display: block;
  font-size: 10px;
  color: #64748b;
  margin-top: 0;
  font-weight: 600;
}

.story-form-content {
  background: #f4f7f5;
  padding: 10px 14px;
  overflow-y: auto;
}

.story-form-title {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 2px;
}

.story-form-subtitle {
  margin-top: 0;
  color: #607284;
  font-size: 12px;
}

.story-field-group {
  margin-top: 10px;
}

.story-label.with-optional {
  justify-content: flex-start;
  gap: 6px;
}

.story-label.with-optional small {
  margin-left: auto;
  text-transform: none;
  letter-spacing: 0;
  font-size: 12px;
  color: #93a29a;
  font-weight: 700;
}

.story-rich-shell {
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.story-rich-shell :deep(.ql-toolbar.ql-snow) {
  border: 0 !important;
  border-bottom: 1px solid #e6eee8 !important;
  background: #fbfdfc;
  padding: 4px 8px;
}

.story-rich-shell :deep(.ql-container.ql-snow) {
  border: 0 !important;
}

.story-rich-shell :deep(.ql-editor) {
  min-height: 110px;
}

.story-rich-shell :deep(.ql-toolbar .ql-formats) {
  margin-right: 8px;
}

.story-rich-shell :deep(.ql-toolbar button) {
  width: 18px;
  height: 18px;
  padding: 2px;
}

.story-position-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.story-position-card {
  border: 1px solid #cfdad3;
  border-radius: 14px;
  background: #fff;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
}

.story-position-card.active {
  border-color: #36c65a;
  background: #eefaf1;
}

.story-position-icon {
  width: 40px;
  height: 30px;
  border-radius: 8px;
  background: #e7efea;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px;
}

.story-position-icon--reverse {
  flex-direction: row-reverse;
}

.wf-box {
  border-radius: 4px;
  background: #9eb0a6;
}

.wf-box--media {
  width: 16px;
  height: 18px;
}

.wf-box--text {
  width: 12px;
  height: 18px;
  background: #c5d3cc;
  display: grid;
  align-content: center;
  gap: 2px;
  padding: 2px;
}

.wf-box--text span {
  display: block;
  height: 2px;
  border-radius: 2px;
  background: #8ca094;
}

.story-position-card strong {
  display: block;
  font-size: 13px;
  color: #112017;
}

.story-position-card small {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: #647d70;
}

.story-label {
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
  background: #07111f;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0;
  text-transform: none;
  z-index: 30;
  box-shadow: 0 10px 24px rgba(7,17,31,.22);
}

.story-input {
  width: 100%;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  padding: 10px 12px;
  background: #fff;
}

.story-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.story-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #4d6a60;
  font-weight: 800;
}

.story-box {
  margin-top: 10px;
  border: 1px solid #dfe8e2;
  border-radius: 12px;
  background: #fff;
  padding: 10px;
}

.story-media-shell {
  margin-top: 10px;
}

.story-gallery-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.story-gallery-card {
  border: 1px solid #cad6cf;
  border-radius: 12px;
  background: #f8fbf9;
  padding: 8px;
}

.story-gallery-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.story-gallery-head span {
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  color: #556b60;
}

.story-gallery-badge {
  font-size: 10px !important;
  border-radius: 999px;
  padding: 2px 6px;
  background: #ddf6e2;
  color: #11823a !important;
}

.story-gallery-preview {
  height: 76px;
  border-radius: 10px;
  border: 1px solid #d6e2db;
  background: #eef4f0;
  overflow: hidden;
}

.story-gallery-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.story-gallery-actions {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.story-link-mini {
  border: 0;
  background: transparent;
  font-size: 12px;
  font-weight: 700;
  color: #0f1f14;
}

.story-link-mini.danger {
  color: #ef4444;
}

.story-add-outline {
  margin-top: 10px;
  width: 100%;
  border: 1px dashed #cad6cf;
  border-radius: 10px;
  padding: 8px 12px;
  background: transparent;
  font-size: 12px;
  font-weight: 700;
  color: #123623;
}

.story-bulk-error {
  margin: 6px 2px 0;
  font-size: 12px;
  color: #dc2626;
}

.story-box-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.story-link-btn {
  border: 1px dashed #c9d4ce;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #1c2a22;
}

.story-note {
  margin: 6px 0 0;
  color: #7d8d83;
  font-size: 12px;
}

.story-empty {
  margin-top: 8px;
  border: 1px dashed #dfe8e2;
  border-radius: 10px;
  padding: 8px;
  font-size: 12px;
  color: #7d8d83;
}

.story-video-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.story-video-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
}

.story-mini-btn {
  border: 1px solid #dfe8e2;
  border-radius: 8px;
  padding: 7px 10px;
  background: #fff;
  color: #223228;
  font-size: 12px;
  font-weight: 700;
}

.story-mini-btn.danger {
  background: #fff1f1;
  color: #e13c3c;
  border-color: #ffd4d4;
}

.story-cta-shell--dropdown-open,
.story-cta-shell--dropdown-open .story-form-content {
  overflow: visible !important;
}

.story-field-group {
  margin-bottom: 10px;
}

.story-pill-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.story-pill {
  border-radius: 12px;
  border: 1px solid #dfe8e2;
  padding: 8px 11px;
  color: #516358;
  font-size: 12px;
  font-weight: 700;
  background: #fff;
}

.story-pill.active {
  background: #07111f;
  border-color: #07111f;
  color: #fff;
}

.story-inline-check {
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

.story-inline-check input {
  width: 16px;
  height: 16px;
  min-height: 0;
  padding: 0;
  accent-color: #35d467;
}

.story-button-panel .story-label {
  font-size: 11px;
  letter-spacing: .06em;
}

.story-button-panel .story-input,
.story-button-panel .section-dropdown-trigger {
  height: 40px;
  border: 1px solid #dfe8e2;
  border-radius: 10px;
  padding: 0 11px;
  font-size: 14px;
}

.story-thumb-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(150px,1fr)); gap: 10px; margin-top: 8px; }
.story-thumb-card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px; background: #fff; text-align: left; display: flex; flex-direction: column; gap: 8px; }
.story-thumb-head { display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: #64748b; }
.story-thumb-main { font-size: 10px; padding: 2px 6px; border-radius: 999px; background: #dcfce7; color: #166534; }
.story-thumb-preview { height: 86px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.story-thumb-preview img { width: 100%; height: 100%; object-fit: cover; }
.story-thumb-empty { font-size: 11px; color: #94a3b8; }
.story-thumb-actions { display: flex; justify-content: space-between; align-items: center; gap: 8px; }

.story-modal-overlay { position: fixed; inset: 0; z-index: 70; background: rgba(15,23,42,.45); display: flex; align-items: center; justify-content: center; padding: 16px; }
.story-modal { width: min(980px,100%); max-height: 86vh; overflow: auto; background: #fff; border-radius: 20px; padding: 16px; }
.story-modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.story-modal-title { font-size: 18px; font-weight: 700; color: #0f172a; }
.story-modal-close { font-size: 14px; font-weight: 600; color: #64748b; }

.section-dropdown { position: relative; }
.section-dropdown-trigger {
  width: 100%;
  height: 40px;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  background: #fff;
  color: #172132;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  text-align: left;
  font-size: 14px;
}
.section-dropdown-arrow { color: #7b8e83; font-size: 14px; }
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
.section-dropdown-item:hover { background: #eef6f1; }
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

@media (max-width: 900px) {
  .story-form-shell {
    grid-template-columns: 1fr;
    min-height: 100%;
    height: 100%;
    align-content: start;
    grid-auto-rows: min-content;
  }

  .story-form-nav {
    border-right: 0;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 8px;
    overflow-x: hidden;
    padding: 8px 8px 0 16px;
    margin-bottom: 8px;
    background: #fff;
  }

  .story-nav-item {
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

  .story-nav-item > span:last-child {
    display: inline-flex;
    font-size: 12px;
    line-height: 1.1;
    align-items: center;
  }

  .story-nav-item > span:last-child small {
    display: none;
  }

  .story-form-content {
    padding-top: 0;
    margin-top: 0;
  }

  .story-grid-2,
  .story-gallery-grid,
  .story-position-grid,
  .story-video-row {
    grid-template-columns: 1fr;
  }
}
</style>
