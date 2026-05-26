<template>
  <div class="cta-proto-body">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: activePanel === 'content' }" @click="activePanel = 'content'">
        <span class="tab-icon" v-html="adminTabIcons.text"></span>
        <span>Textos<small>Chamada principal</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'button' }" @click="activePanel = 'button'">
        <span class="tab-icon" v-html="adminTabIcons.button"></span>
        <span>Botão<small>Ação do visitante</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activePanel === 'content'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure a chamada principal e o texto complementar desta seção.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido acima do título da seção.">?</span></label>
            <input v-model="local.headingLabel" />
          </div>

          <div class="field">
            <label>Título da seção <span class="help" data-tip="Texto principal da chamada para ação.">?</span></label>
            <input v-model="local.label" />
          </div>

          <div class="field">
            <label>Descrição <span class="help" data-tip="Texto complementar opcional da chamada.">?</span></label>
            <RichTextEditor v-model="local.description" :placeholder="viewCopy.fields.descriptionPlaceholder" />
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Botão da seção</h2>
            <p class="section-desc">Defina o texto, link e comportamento do botão de ação.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="grid-2">
            <div class="field">
              <label>Texto do botão <span class="help" data-tip="Texto exibido no botão de ação.">?</span></label>
              <input v-model="local.ctaText" :placeholder="viewCopy.cta.textPlaceholder" />
            </div>
            <div class="field">
              <label>Link do botão <span class="help" data-tip="Destino aberto ao clicar no botão.">?</span></label>
              <input v-model="local.link" :placeholder="viewCopy.cta.linkPlaceholder" />
            </div>
          </div>

          <div class="field">
            <label class="inline-check"><input type="checkbox" v-model="local.ctaOpenInNewTab" /> Abrir em nova aba</label>
          </div>

          <div class="highlight-box">
            <label class="inline-check">
              <input type="checkbox" v-model="local.highlight" />
              {{ viewCopy.highlight.label }}
            </label>
            <div v-if="local.highlight" class="highlight-color-row">
              <input type="color" v-model="local.highlightColor" class="color-picker" />
              <input v-model="local.highlightColor" placeholder="#0f172a" />
            </div>
          </div>

          <div class="note-box">{{ viewCopy.notes.colorInfo }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, ref, watch } from "vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { CtaSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { adminTabIcons } from "../../utils/adminTabIcons";

const props = defineProps<{ modelValue: CtaSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CtaSection): void }>();
const headingDefaults = getSectionHeadingDefaults("cta");
const t = createAdminLocalizer();
const activePanel = ref<"content" | "button">("content");

const viewCopy = {
  fields: {
    descriptionPlaceholder: t({ pt: "Use este espaço para reforçar sua oferta", es: "Usa este espacio para reforzar tu oferta" })
  },
  cta: {
    textPlaceholder: t({ pt: "Falar com especialista", es: "Hablar con un especialista" }),
    linkPlaceholder: t({ pt: "https://wa.me/", es: "https://wa.me/" })
  },
  highlight: {
    label: t({ pt: "Destacar card", es: "Destacar tarjeta" })
  },
  notes: {
    colorInfo: t({
      pt: 'A cor do botão segue a opção global "Cor de botões e destaques" configurada no topo do editor.',
      es: 'El color del botón sigue la opción global "Color de botones y destacados" configurada en la parte superior del editor.'
    })
  }
};

const local = reactive<CtaSection>({
  ...props.modelValue,
  layout: props.modelValue.layout || "simple",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  link: props.modelValue.link || "https://wa.me/",
  ctaMode: "link",
  ctaSectionId: null,
  ctaOpenInNewTab: props.modelValue.ctaOpenInNewTab !== false,
  ctaText: props.modelValue.ctaText || viewCopy.cta.textPlaceholder,
  highlight: props.modelValue.highlight ?? false,
  highlightColor: props.modelValue.highlightColor || props.modelValue.ctaColor || "#0f172a"
});

let syncing = false;
const syncFromProps = (value: CtaSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.ctaMode = "link";
  local.ctaSectionId = null;
  local.ctaOpenInNewTab = value.ctaOpenInNewTab !== false;
  local.link = value.link || "https://wa.me/";
  local.highlight = value.highlight ?? false;
  local.highlightColor = value.highlightColor || local.highlightColor || "#0f172a";
  local.ctaText = value.ctaText || viewCopy.cta.textPlaceholder;
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
  { deep: true, immediate: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as CtaSection);
  },
  { deep: true }
);

watch(
  () => local.highlight,
  value => {
    if (value && !local.highlightColor) local.highlightColor = "#0f172a";
  }
);
</script>

<style scoped>
.cta-proto-body { display: grid; grid-template-columns: 178px 1fr; min-height: 0; height: 100%; align-items: stretch; }
.tabs { border-right: 1px solid #e6eee8; padding: 16px 12px 16px 12px; display: flex; flex-direction: column; gap: 8px; background: #fff; }
.tab { display: flex; align-items: center; gap: 10px; border: 1px solid #d8dfda; border-radius: 14px; padding: 7px 9px; background: #eef2ef; color: #0f172a; text-align: left; }
.tab.active { background: #34c759; border-color: #34c759; }
.tab-icon { width: 22px; height: 22px; border-radius: 8px; background: rgba(255,255,255,.82); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; }
.tab > span { display: flex; flex-direction: column; gap: 1px; font-size: 15px; font-weight: 700; line-height: 1.15; }
.tab > span small { font-size: 12px; font-weight: 600; color: rgba(15, 23, 42, 0.55); }

.editor { padding: 0; background: #edf1ef; min-width: 0; min-height: 100%; }
.section-card { background: transparent; border: 0; min-height: 0; }
.section-head { padding: 14px 16px 10px; border-bottom: 1px solid #dde5e1; }
.section-title { margin: 0; font-size: 18px; line-height: 1.15; color: #0f172a; font-weight: 800; }
.section-desc { margin: 6px 0 0; font-size: 13px; color: #6a7e74; }
.content-area { padding: 12px 14px; display: grid; gap: 10px; min-width: 0; align-content: start; }

.field { display: grid; gap: 6px; }
.field label { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; color: #6a7e74; display: inline-flex; align-items: center; gap: 7px; }
.help { width: 16px; height: 16px; border: 1px solid #cdd8d2; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; color: #8ca198; position: relative; cursor: help; background: #eef4f1; text-transform: none; }
.help:hover::after { content: attr(data-tip); position: absolute; left: 22px; top: 50%; transform: translateY(-50%); white-space: nowrap; padding: 6px 8px; background: #0f172a; color: #fff; font-size: 11px; border-radius: 8px; z-index: 20; text-transform: none; letter-spacing: 0; }
input { width: 100%; border: 1px solid #cad7d1; border-radius: 12px; background: #fff; font-size: 16px; line-height: 1.25; padding: 9px 12px; color: #1f2937; }
input:focus { outline: none; border-color: #9cb5aa; box-shadow: 0 0 0 2px rgba(52,199,89,.15); }

.grid-2 { display: grid; gap: 10px; grid-template-columns: 1fr 1fr; }
.inline-check { display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: #475569; text-transform: none; letter-spacing: 0; font-weight: 700; }
.inline-check input { width: 14px; height: 14px; }
.highlight-box { border: 1px solid #cad7d1; border-radius: 12px; padding: 10px; background: #fff; display: grid; gap: 10px; }
.highlight-color-row { display: grid; gap: 8px; grid-template-columns: 44px 1fr; }
.color-picker { width: 44px; height: 40px; border: 1px solid #cad7d1; border-radius: 10px; padding: 2px; }
.note-box { border: 1px dashed #cad7d1; border-radius: 12px; padding: 10px; font-size: 12px; color: #64748b; background: #f8fafc; }

@media (max-width: 900px) {
  .cta-proto-body { grid-template-columns: 1fr; min-height: 100%; height: 100%; }
  .tabs { border-right: 0; border-bottom: 0; padding: 8px 8px 8px 16px; margin-bottom: 8px; flex-direction: row; }
  .tab { flex: 1; min-width: 0; }
  .tab > span small { display: none; }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>

