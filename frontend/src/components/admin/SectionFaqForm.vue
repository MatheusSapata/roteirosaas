<template>
  <div class="faq-proto-body">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: activePanel === 'texts' }" @click="activePanel = 'texts'">
        <span class="tab-icon" v-html="adminTabIcons.text"></span>
        <span>Textos<small>Chamada da seção</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'items' }" @click="activePanel = 'items'">
        <span class="tab-icon" v-html="adminTabIcons.faq"></span>
        <span>Perguntas<small>FAQ</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activePanel === 'texts'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure o título e subtítulo exibidos acima da lista de perguntas.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido acima do título principal.">?</span></label>
            <input v-model="local.headingLabel" />
          </div>

          <div class="field">
            <label>Título <span class="help" data-tip="Título principal da seção FAQ.">?</span></label>
            <input v-model="local.title" :placeholder="viewCopy.fields.titlePlaceholder" />
          </div>

          <div class="field">
            <label>Subtítulo <span class="help" data-tip="Texto complementar para contextualizar as perguntas.">?</span></label>
            <textarea v-model="local.subtitle" :placeholder="viewCopy.fields.subtitlePlaceholder" rows="3"></textarea>
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Perguntas frequentes</h2>
            <p class="section-desc">Adicione, selecione e edite os itens do FAQ.</p>
          </div>
          <div class="segment-actions segment-actions--head">
            <button type="button" class="add-segment" @click="addItem">+ Adicionar pergunta</button>
          </div>
        </div>

        <div class="content-area">
          <div class="segment-bar">
            <div ref="itemTabsRef" class="segment-tabs">
              <button
                v-for="(item, index) in local.items"
                :key="`faq-${index}`"
                type="button"
                data-faq-chip
                class="segment-tab"
                :class="{ active: selectedItemIndex === index }"
                @click="selectedItemIndex = index"
              >
                <span class="segment-handle">⋮⋮</span>
                <span class="segment-name">{{ item.question?.trim() || `Pergunta ${index + 1}` }}</span>
                <span class="segment-remove" @click.stop="removeItem(index)">×</span>
              </button>
            </div>
          </div>

          <div v-if="selectedItem" class="segment-panel">
            <div class="field">
              <label>Pergunta <span class="help" data-tip="Pergunta exibida no accordion de FAQ.">?</span></label>
              <input v-model="selectedItem.question" :placeholder="viewCopy.items.questionPlaceholder" />
            </div>

            <div class="field">
              <label>Resposta <span class="help" data-tip="Resposta detalhada para a pergunta selecionada.">?</span></label>
              <RichTextEditor v-model="selectedItem.answer" :placeholder="viewCopy.items.answerPlaceholder" />
            </div>
          </div>

          <div v-else class="empty-state">Adicione uma pergunta para começar.</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable, { type SortableEvent } from "sortablejs";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { FaqSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { adminTabIcons } from "../../utils/adminTabIcons";

const props = defineProps<{ modelValue: FaqSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: FaqSection): void }>();
const headingDefaults = getSectionHeadingDefaults("faq");
const t = createAdminLocalizer();
const activePanel = ref<"texts" | "items">("texts");
const selectedItemIndex = ref(0);
const itemTabsRef = ref<HTMLElement | null>(null);
let itemsSortable: Sortable | null = null;

const viewCopy = {
  fields: {
    titlePlaceholder: t({ pt: "Perguntas frequentes", es: "Preguntas frecuentes" }),
    subtitlePlaceholder: t({ pt: "As dúvidas mais comuns sobre o roteiro.", es: "Las dudas más comunes sobre el itinerario." })
  },
  items: {
    questionPlaceholder: t({ pt: "Pergunta", es: "Pregunta" }),
    answerPlaceholder: t({ pt: "Adicione uma resposta formatada", es: "Agrega una respuesta formateada" })
  }
};

const defaultTitle = viewCopy.fields.titlePlaceholder;
const defaultSubtitle = viewCopy.fields.subtitlePlaceholder;

const local = reactive<FaqSection>({
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title ?? defaultTitle,
  subtitle: props.modelValue.subtitle ?? defaultSubtitle,
  layout: "accordion",
  items: Array.isArray(props.modelValue.items) ? props.modelValue.items.map(item => ({ ...item })) : []
});

const selectedItem = computed(() => local.items?.[selectedItemIndex.value] || null);
let syncing = false;

const handleDragEnd = (event: SortableEvent) => {
  const from = event.oldIndex;
  const to = event.newIndex;
  if (from === undefined || to === undefined || from === to) return;
  const moved = local.items.splice(from, 1)[0];
  if (!moved) return;
  local.items.splice(to, 0, moved);
  if (selectedItemIndex.value === from) selectedItemIndex.value = to;
  else if (selectedItemIndex.value > from && selectedItemIndex.value <= to) selectedItemIndex.value -= 1;
  else if (selectedItemIndex.value < from && selectedItemIndex.value >= to) selectedItemIndex.value += 1;
};

const destroySortable = () => {
  if (!itemsSortable) return;
  itemsSortable.destroy();
  itemsSortable = null;
};

const initSortable = () => {
  if (!itemTabsRef.value || local.items.length <= 1) {
    destroySortable();
    return;
  }
  destroySortable();
  itemsSortable = Sortable.create(itemTabsRef.value, {
    animation: 160,
    draggable: "button[data-faq-chip]",
    handle: ".segment-handle",
    onEnd: handleDragEnd
  });
};

const scheduleSortableRefresh = () => nextTick(initSortable);

const syncFromProps = (value: FaqSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.title = value.title ?? defaultTitle;
  local.subtitle = value.subtitle ?? defaultSubtitle;
  local.layout = "accordion";
  local.items = Array.isArray(value.items) ? value.items.map(item => ({ ...item })) : [];
  if (selectedItemIndex.value >= (local.items?.length || 0)) {
    selectedItemIndex.value = Math.max(0, (local.items?.length || 0) - 1);
  }
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

onMounted(scheduleSortableRefresh);
onBeforeUnmount(destroySortable);

watch(
  () => local.items.length,
  () => scheduleSortableRefresh()
);

watch(
  () => activePanel.value,
  panel => {
    if (panel === "items") scheduleSortableRefresh();
  }
);

const addItem = () => {
  local.items.push({ question: "", answer: "" });
  selectedItemIndex.value = local.items.length - 1;
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
  if (selectedItemIndex.value >= local.items.length) {
    selectedItemIndex.value = Math.max(0, local.items.length - 1);
  }
};

watch(
  () => ({ ...local, items: local.items.map(item => ({ ...item })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as FaqSection);
  },
  { deep: true }
);
</script>

<style scoped>
.faq-proto-body { display: grid; grid-template-columns: 178px 1fr; min-height: 0; height: 100%; align-items: stretch; }
.tabs { border-right: 1px solid #e6eee8; padding: 16px 12px 16px 12px; display: flex; flex-direction: column; gap: 8px; background: #fff; }
.tab { display: flex; align-items: center; gap: 10px; border: 1px solid #d8dfda; border-radius: 14px; padding: 7px 9px; background: #eef2ef; color: #0f172a; text-align: left; }
.tab.active { background: #34c759; border-color: #34c759; }
.tab-icon { width: 22px; height: 22px; border-radius: 8px; background: rgba(255,255,255,.82); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; }
.tab > span { display: flex; flex-direction: column; gap: 1px; font-size: 15px; font-weight: 700; line-height: 1.15; }
.tab > span small { font-size: 12px; font-weight: 600; color: rgba(15, 23, 42, 0.55); }

.editor { padding: 0; background: #edf1ef; min-width: 0; min-height: 100%; }
.section-card { background: transparent; border: 0; min-height: 0; }
.section-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding: 14px 16px 10px; border-bottom: 1px solid #dde5e1; }
.section-title { margin: 0; font-size: 18px; line-height: 1.15; color: #0f172a; font-weight: 800; }
.section-desc { margin: 6px 0 0; font-size: 13px; color: #6a7e74; }
.content-area { padding: 12px 14px; display: grid; gap: 10px; min-width: 0; align-content: start; }

.field { display: grid; gap: 6px; }
.field label { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; color: #6a7e74; display: inline-flex; align-items: center; gap: 7px; }
.help { width: 16px; height: 16px; border: 1px solid #cdd8d2; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; color: #8ca198; position: relative; cursor: help; background: #eef4f1; text-transform: none; }
.help:hover::after { content: attr(data-tip); position: absolute; left: 22px; top: 50%; transform: translateY(-50%); white-space: nowrap; padding: 6px 8px; background: #0f172a; color: #fff; font-size: 11px; border-radius: 8px; z-index: 20; text-transform: none; letter-spacing: 0; }
input, textarea { width: 100%; border: 1px solid #cad7d1; border-radius: 12px; background: #fff; font-size: 16px; line-height: 1.25; padding: 9px 12px; color: #1f2937; }
input:focus, textarea:focus { outline: none; border-color: #9cb5aa; box-shadow: 0 0 0 2px rgba(52,199,89,.15); }
textarea { resize: vertical; }

.segment-bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.segment-tabs { display: flex; flex-wrap: wrap; gap: 6px; min-width: 0; }
.segment-tab { border: 1px solid #cad7d1; border-radius: 999px; padding: 5px 9px; background: #fff; color: #0f172a; font-size: 11px; display: inline-flex; align-items: center; gap: 6px; }
.segment-tab.active { border-color: #34c759; background: #ecfdf2; }
.segment-handle { color: #94a3b8; font-size: 12px; line-height: 1; }
.segment-name { font-weight: 700; line-height: 1.1; }
.segment-remove { width: 16px; height: 16px; border-radius: 999px; border: 1px solid #d6dde8; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; color: #64748b; }
.segment-actions { display: flex; flex-shrink: 0; }
.segment-actions--head { margin-left: auto; }
.add-segment { border: 1px solid #cad7d1; border-radius: 999px; background: #fff; color: #475569; font-size: 11px; font-weight: 700; padding: 7px 11px; }

.segment-panel { border: 0; border-radius: 0; padding: 0; background: transparent; display: grid; gap: 10px; }
.empty-state { border: 1px dashed #cad7d1; border-radius: 12px; padding: 14px; font-size: 13px; color: #64748b; background: #f8fafc; }

.faq-proto-body,
.editor {
  background: var(--background);
  color: var(--foreground);
}
.tabs { border-color: var(--border); background: var(--card); }
.tab { border-color: var(--border); background: var(--muted); color: var(--foreground); }
.tab.active { border-color: var(--primary); background: var(--primary); color: var(--primary-foreground); }
.tab > span small,
.section-desc { color: var(--muted-foreground); }
.section-head { border-color: color-mix(in srgb, var(--border) 62%, transparent); }
.section-title { color: var(--foreground); }
input, textarea {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}
input:focus, textarea:focus {
  outline: none;
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent);
}
.segment-tab,
.add-segment,
.empty-state {
  border-color: var(--border);
  background: var(--muted);
  color: var(--foreground);
}
.segment-tab.active {
  border-color: color-mix(in srgb, var(--primary) 55%, var(--border));
  background: color-mix(in srgb, var(--primary) 16%, var(--card));
  color: var(--foreground);
}
.segment-handle { color: var(--muted-foreground); }
.segment-remove {
  border-color: var(--border);
  background: color-mix(in srgb, var(--card) 78%, transparent);
  color: var(--muted-foreground);
}
.add-segment:hover {
  border-color: color-mix(in srgb, var(--primary) 38%, var(--border));
  background: var(--accent);
}
.help:hover::after {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

@media (max-width: 900px) {
  .faq-proto-body { grid-template-columns: 1fr; min-height: 100%; height: 100%; }
  .tabs { border-right: 0; border-bottom: 0; padding: 8px 8px 8px 16px; margin-bottom: 8px; flex-direction: row; }
  .tab { flex: 1; min-width: 0; }
  .tab > span small { display: none; }
  .segment-bar { flex-wrap: wrap; }
}
</style>

