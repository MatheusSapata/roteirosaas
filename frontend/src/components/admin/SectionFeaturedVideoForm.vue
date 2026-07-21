<template>
  <div class="featured-video-proto-body">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: activePanel === 'text' }" @click="activePanel = 'text'">
        <span class="tab-icon" v-html="adminTabIcons.text"></span>
        <span>Textos<small>Título e descrição</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'video' }" @click="activePanel = 'video'">
        <span class="tab-icon" v-html="adminTabIcons.media"></span>
        <span>Vídeo<small>Link principal</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'button' }" @click="activePanel = 'button'">
        <span class="tab-icon" v-html="adminTabIcons.button"></span>
        <span>Botão<small>Ação do visitante</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activePanel === 'text'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure o título e o texto de apoio que acompanham o vídeo.</p>
          </div>
        </div>
        <div class="content-area">
          <div class="field">
            <label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido acima do título.">?</span></label>
            <input v-model="local.headingLabel" />
          </div>
          <div class="field">
            <label>Título principal <span class="help" data-tip="Título principal da seção de vídeo.">?</span></label>
            <input v-model="local.title" :placeholder="viewCopy.fields.titlePlaceholder" />
          </div>
          <div class="field">
            <label>Subtítulo <span class="help" data-tip="Texto complementar abaixo do título.">?</span></label>
            <RichTextEditor v-model="local.subtitle" :placeholder="viewCopy.fields.subtitlePlaceholder" />
          </div>
        </div>
      </div>

      <div v-else-if="activePanel === 'video'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Vídeo em destaque</h2>
            <p class="section-desc">Informe o link público do vídeo incorporado.</p>
          </div>
        </div>
        <div class="content-area">
          <div class="field">
            <label>Vídeo (YouTube ou iframe) <span class="help" data-tip="Aceita URL do YouTube/Vimeo ou código iframe.">?</span></label>
            <input v-model="local.videoUrl" :placeholder="viewCopy.fields.videoPlaceholder" />
            <p class="field-hint">{{ viewCopy.fields.videoHelper }}</p>
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Botão da seção</h2>
            <p class="section-desc">Defina se haverá CTA e para onde o visitante será direcionado.</p>
          </div>
        </div>
        <div class="content-area">
          <label class="inline-check"><input type="checkbox" v-model="local.ctaEnabled" /> Mostrar botão de CTA</label>

          <div v-if="local.ctaEnabled" class="cta-box">
            <div class="field">
              <label>Tipo de ação <span class="help" data-tip="Escolha entre link externo/WhatsApp ou seção interna.">?</span></label>
              <div class="pill-row">
                <button type="button" class="pill" :class="{ active: local.ctaMode !== 'section' }" @click="setCtaMode('link')">
                  WhatsApp / Link externo
                </button>
                <button type="button" class="pill" :class="{ active: local.ctaMode === 'section' }" @click="setCtaMode('section')">
                  Ir para seção
                </button>
              </div>
            </div>

            <div class="grid-2">
              <div class="field">
                <label>Texto do botão <span class="help" data-tip="Texto exibido no botão.">?</span></label>
                <input v-model="local.ctaLabel" :placeholder="viewCopy.cta.textPlaceholder" />
              </div>
              <div class="field cta-link-field">
                <label>Destino do clique <span class="help" data-tip="URL externa ou âncora de seção.">?</span></label>
                <template v-if="local.ctaMode === 'section'">
                  <div ref="sectionDropdownRef" class="section-dropdown">
                    <button type="button" class="section-dropdown-trigger" @click="toggleSectionDropdown">
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
                      <SectionHoverVisualPreview :label="hoveredSectionOption.label" :section="hoveredSectionOption.section" />
                    </div>
                  </div>
                </template>
                <template v-else>
                  <input v-model="local.ctaLink" :placeholder="viewCopy.cta.linkPlaceholder" />
                  <label class="inline-check cta-newtab-check"><input type="checkbox" v-model="local.ctaOpenInNewTab" /> {{ viewCopy.cta.newTabLabel }}</label>
                </template>
              </div>
            </div>

            <div class="note-box">{{ viewCopy.cta.colorInfo }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import SectionHoverVisualPreview from "./SectionHoverVisualPreview.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { FeaturedVideoSection, PageSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { sectionsInjectionKey } from "./sectionsContext";
import { describeSection, sectionLabels } from "../../utils/sectionLabels";
import { adminTabIcons } from "../../utils/adminTabIcons";

const props = defineProps<{ modelValue: FeaturedVideoSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FeaturedVideoSection): void }>();
const headingDefaults = getSectionHeadingDefaults("featured_video");
const t = createAdminLocalizer();
const activePanel = ref<"text" | "video" | "button">("text");
const sections = inject(sectionsInjectionKey, ref<PageSection[]>([]));
const sectionDropdownOpen = ref(false);
const sectionDropdownRef = ref<HTMLElement | null>(null);

type SectionOption = { value: string; label: string; section: PageSection };
const hoveredSectionOption = ref<SectionOption | null>(null);

const viewCopy = {
  fields: {
    titlePlaceholder: t({ pt: "Apresente o vídeo com um título forte", es: "Presenta el video con un título fuerte" }),
    subtitlePlaceholder: t({ pt: "Explique o contexto do vídeo em poucas frases", es: "Explica el contexto del video en pocas frases" }),
    videoPlaceholder: "https://www.youtube.com/watch?v=...",
    videoHelper: t({ pt: "Aceita links completos ou o código iframe do YouTube/Vimeo.", es: "Acepta enlaces completos o el código iframe de YouTube/Vimeo." })
  },
  cta: {
    textPlaceholder: t({ pt: "Assistir agora", es: "Ver ahora" }),
    newTabLabel: t({ pt: "Abrir em nova aba", es: "Abrir en nueva pestaña" }),
    linkPlaceholder: t({ pt: "https://wa.me/", es: "https://wa.me/" }),
    colorInfo: t({
      pt: 'A cor do botão segue a configuração global "Cor de botões e destaques".',
      es: 'El color del botón sigue la configuración global "Color de botones y destacados".'
    })
  }
};

const local = reactive<FeaturedVideoSection>({
  type: "featured_video",
  enabled: true,
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title || viewCopy.fields.titlePlaceholder,
  subtitle: props.modelValue.subtitle || "",
  videoUrl: props.modelValue.videoUrl || "",
  ctaEnabled: props.modelValue.ctaEnabled !== false,
  ctaLabel: props.modelValue.ctaLabel || viewCopy.cta.textPlaceholder,
  ctaLink: props.modelValue.ctaLink || viewCopy.cta.linkPlaceholder,
  ctaMode: props.modelValue.ctaMode || "link",
  ctaSectionId: props.modelValue.ctaSectionId ?? null,
  ctaOpenInNewTab: props.modelValue.ctaOpenInNewTab !== false
});

const sectionOptions = computed(() => {
  const list = sections?.value || [];
  return list
    .filter(section => section.anchorId && section.anchorId !== local.anchorId && section.enabled !== false)
    .map(section => ({
      value: section.anchorId as string,
      label: `${sectionLabels[section.type] || "Seção"} • ${describeSection(section)}`,
      section
    }));
});

const selectedSectionOption = computed(() => sectionOptions.value.find(option => option.value === local.ctaSectionId) || null);

const setCtaMode = (mode: "link" | "section") => {
  local.ctaMode = mode;
  if (mode === "link") {
    local.ctaSectionId = null;
    sectionDropdownOpen.value = false;
    hoveredSectionOption.value = null;
    return;
  }
  if (!local.ctaSectionId) {
    local.ctaSectionId = sectionOptions.value[0]?.value || null;
  }
};

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
const syncFromProps = (value: FeaturedVideoSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.title = value.title || viewCopy.fields.titlePlaceholder;
  local.subtitle = value.subtitle || "";
  local.videoUrl = value.videoUrl || "";
  local.ctaEnabled = value.ctaEnabled !== false;
  local.ctaLabel = value.ctaLabel || viewCopy.cta.textPlaceholder;
  local.ctaLink = value.ctaLink || viewCopy.cta.linkPlaceholder;
  local.ctaMode = value.ctaMode || "link";
  local.ctaSectionId = value.ctaSectionId ?? null;
  local.ctaOpenInNewTab = value.ctaOpenInNewTab !== false;
  nextTick(() => {
    syncing = false;
  });
};

watch(() => props.modelValue, value => { if (value) syncFromProps(value); }, { deep: true, immediate: true });
watch(() => ({ ...local }), value => { if (!syncing) emit("update:modelValue", value as FeaturedVideoSection); }, { deep: true });
</script>

<style scoped>
.featured-video-proto-body { display: grid; grid-template-columns: 178px 1fr; min-height: 0; height: 100%; align-items: stretch; }
.tabs { border-right: 1px solid #e6eee8; padding: 16px 12px 16px 12px; display: flex; flex-direction: column; gap: 8px; background: #fff; }
.tab { display: flex; align-items: center; gap: 10px; border: 1px solid #d8dfda; border-radius: 14px; padding: 7px 9px; background: #eef2ef; color: #0f172a; text-align: left; }
.tab.active { background: #34c759; border-color: #34c759; }
.tab-icon { width: 22px; height: 22px; border-radius: 8px; background: rgba(255,255,255,.82); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; }
.tab > span { display: flex; flex-direction: column; gap: 1px; font-size: 15px; font-weight: 700; line-height: 1.15; }
.tab > span small { font-size: 12px; font-weight: 600; color: rgba(15,23,42,.55); }

.editor { padding: 0; background: #edf1ef; min-width: 0; min-height: 100%; }
.section-card { background: transparent; border: 0; min-height: 0; }
.section-head { padding: 14px 16px 10px; border-bottom: 1px solid #dde5e1; }
.section-title { margin: 0; font-size: 18px; line-height: 1.15; color: #0f172a; font-weight: 800; }
.section-desc { margin: 6px 0 0; font-size: 13px; color: #6a7e74; }
.content-area { padding: 12px 14px; display: grid; gap: 10px; min-width: 0; align-content: start; }

.field { display: grid; gap: 6px; }
.field label { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; color: #6a7e74; display: inline-flex; align-items: center; gap: 7px; }
.field-hint { margin: 0; font-size: 11px; color: #7d9087; }
.help { width: 16px; height: 16px; border: 1px solid #cdd8d2; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; color: #8ca198; position: relative; cursor: help; background: #eef4f1; text-transform: none; }
.help:hover::after { content: attr(data-tip); position: absolute; left: 22px; top: 50%; transform: translateY(-50%); white-space: nowrap; padding: 6px 8px; background: #0f172a; color: #fff; font-size: 11px; border-radius: 8px; z-index: 20; text-transform: none; letter-spacing: 0; }
input { width: 100%; border: 1px solid #cad7d1; border-radius: 12px; background: #fff; font-size: 16px; line-height: 1.25; padding: 9px 12px; color: #1f2937; }
input:focus { outline: none; border-color: #9cb5aa; box-shadow: 0 0 0 2px rgba(52,199,89,.15); }

.grid-2 { display: grid; gap: 10px; grid-template-columns: 1fr 1fr; align-items: start; }
.pill-row { display: flex; gap: 8px; flex-wrap: wrap; }
.pill { border-radius: 12px; border: 1px solid #dfe8e2; padding: 8px 11px; color: #516358; font-size: 13px; font-weight: 700; background: #fff; }
.pill.active { background: var(--primary); border-color: var(--primary); color: var(--primary-foreground); }
.inline-check { display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: #475569; text-transform: none; letter-spacing: 0; font-weight: 700; }
.inline-check input { width: 14px; height: 14px; }
.cta-link-field { align-content: start; }
.cta-newtab-check { margin-top: 8px; justify-self: start; line-height: 1; }
.cta-box { border: 0; border-radius: 0; background: transparent; padding: 0; display: grid; gap: 10px; }
.note-box { border: 1px dashed #cad7d1; border-radius: 12px; padding: 10px; font-size: 12px; color: #64748b; background: #f8fafc; }

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

.featured-video-proto-body,
.editor {
  background: var(--background);
  color: var(--foreground);
}
.tabs { border-color: var(--border); background: var(--card); }
.tab { border-color: var(--border); background: var(--muted); color: var(--foreground); }
.tab.active { border-color: var(--primary); background: var(--primary); color: var(--primary-foreground); }
.tab > span small,
.section-desc,
.field-hint,
.inline-check,
.note-box { color: var(--muted-foreground); }
.section-head { border-color: color-mix(in srgb, var(--border) 62%, transparent); }
.section-title { color: var(--foreground); }
input,
.section-dropdown-trigger {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}
input:focus,
.section-dropdown-trigger:focus {
  outline: none;
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent);
}
.pill {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}
.pill:hover {
  border-color: color-mix(in srgb, var(--primary) 38%, var(--border));
  background: var(--accent);
}
.pill.active {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-foreground);
}
.note-box {
  border-color: var(--border);
  background: var(--muted);
}
.section-dropdown-menu,
.section-hover-preview {
  border-color: var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}
.section-dropdown-item {
  color: var(--popover-foreground);
}
.section-dropdown-item:hover {
  background: var(--accent);
  color: var(--accent-foreground);
}
.help:hover::after {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

@media (max-width: 900px) {
  .featured-video-proto-body { grid-template-columns: 1fr; min-height: 100%; height: 100%; }
  .tabs { border-right: 0; border-bottom: 0; padding: 8px 8px 8px 16px; margin-bottom: 8px; flex-direction: row; }
  .tab { flex: 1; min-width: 0; }
  .tab > span small { display: none; }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>

