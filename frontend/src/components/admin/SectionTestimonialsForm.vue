<template>
  <div class="testimonials-proto-body">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: activePanel === 'texts' }" @click="activePanel = 'texts'">
        <span class="tab-icon" v-html="adminTabIcons.text"></span>
        <span>Textos<small>Chamada da seção</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'items' }" @click="activePanel = 'items'">
        <span class="tab-icon" v-html="adminTabIcons.testimonials"></span>
        <span>Depoimentos<small>Clientes e feedbacks</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activePanel === 'texts'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure o título e subtítulo exibidos acima dos depoimentos.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido acima do título principal.">?</span></label>
            <input v-model="local.headingLabel" />
          </div>

          <div class="field">
            <label>Título da seção <span class="help" data-tip="Título principal da seção de depoimentos.">?</span></label>
            <input v-model="local.title" :placeholder="viewCopy.fields.sectionTitlePlaceholder" />
          </div>

          <div class="field">
            <label>Subtítulo <span class="help" data-tip="Texto complementar abaixo do título.">?</span></label>
            <RichTextEditor v-model="local.subtitle" :placeholder="viewCopy.fields.sectionSubtitlePlaceholder" />
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Depoimentos</h2>
            <p class="section-desc">Adicione, selecione e edite os depoimentos exibidos na seção.</p>
          </div>
          <div class="segment-actions segment-actions--head">
            <button type="button" class="add-segment" @click="addItem">+ Adicionar depoimento</button>
          </div>
        </div>

        <div class="content-area">
          <div class="segment-bar">
            <div ref="itemTabsRef" class="segment-tabs">
              <button
                v-for="(item, index) in local.items"
                :key="`testimonial-${index}`"
                type="button"
                data-testimonial-chip
                class="segment-tab"
                :class="{ active: selectedItemIndex === index }"
                @click="selectedItemIndex = index"
              >
                <span class="segment-handle">⋮⋮</span>
                <span class="segment-name">{{ item.name?.trim() || `Depoimento ${index + 1}` }}</span>
                <span class="segment-remove" @click.stop="removeItem(index)">×</span>
              </button>
            </div>
          </div>

          <div v-if="selectedItem" class="segment-panel">
            <div class="item-top-grid">
              <div class="field">
                <label>Foto <span class="help" data-tip="Imagem do cliente exibida no card de depoimento.">?</span></label>
                <ImageUploadField v-model="selectedItem.avatar" label="" hint="" replace-label="Substituir" :enable-crop="true" :crop-aspect="1" />
              </div>
              <div class="item-top-fields">
                <div class="field">
                  <label>Nome <span class="help" data-tip="Nome do cliente ou viajante.">?</span></label>
                  <input v-model="selectedItem.name" :placeholder="viewCopy.items.namePlaceholder" />
                </div>
                <div class="field">
                  <label>Etiqueta <span class="help" data-tip="Texto opcional como cidade, perfil ou contexto.">?</span></label>
                  <input v-model="selectedItem.role" :placeholder="viewCopy.items.rolePlaceholder" />
                </div>
                <div class="field">
                  <label>Depoimento <span class="help" data-tip="Texto principal do feedback do cliente.">?</span></label>
                  <textarea v-model="selectedItem.text" :placeholder="viewCopy.items.textPlaceholder" rows="5"></textarea>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">Adicione um depoimento para começar.</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable, { type SortableEvent } from "sortablejs";
import ImageUploadField from "./inputs/ImageUploadField.vue";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { TestimonialsSection } from "../../types/page";
import defaultAvatarImage from "../../assets/avatar.jpeg";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { adminTabIcons } from "../../utils/adminTabIcons";

const props = defineProps<{ modelValue: TestimonialsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: TestimonialsSection): void }>();

const headingDefaults = getSectionHeadingDefaults("testimonials");
const t = createAdminLocalizer();
const activePanel = ref<"texts" | "items">("texts");
const selectedItemIndex = ref(0);
const itemTabsRef = ref<HTMLElement | null>(null);
let itemsSortable: Sortable | null = null;

const viewCopy = {
  fields: {
    sectionTitlePlaceholder: t({ pt: "Quem já viajou com a gente", es: "Quién ya viajó con nosotros" }),
    sectionSubtitlePlaceholder: t({ pt: "Feedbacks reais de clientes", es: "Comentarios reales de clientes" })
  },
  items: {
    namePlaceholder: t({ pt: "Nome", es: "Nombre" }),
    rolePlaceholder: t({ pt: "(opcional)", es: "(opcional)" }),
    textPlaceholder: t({ pt: "Depoimento", es: "Testimonio" })
  }
};

const normalizeItems = (items?: any[]) =>
  Array.isArray(items) ? items.map(i => ({ ...i, avatar: i.avatar || defaultAvatarImage })) : [];

const local = reactive<TestimonialsSection>({
  layout: "grid",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title || "",
  subtitle: props.modelValue.subtitle || "",
  ...props.modelValue,
  items: normalizeItems(props.modelValue.items)
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
    draggable: "button[data-testimonial-chip]",
    handle: ".segment-handle",
    onEnd: handleDragEnd
  });
};

const scheduleSortableRefresh = () => nextTick(initSortable);

const syncFromProps = (value: TestimonialsSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = value.layout || "grid";
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle ?? headingDefaults.style;
  local.title = value.title || "";
  local.subtitle = value.subtitle || "";
  local.items = normalizeItems(value.items);
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
  local.items.push({ name: "", role: "", text: "", avatar: defaultAvatarImage } as any);
  selectedItemIndex.value = local.items.length - 1;
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
  if (selectedItemIndex.value >= local.items.length) {
    selectedItemIndex.value = Math.max(0, local.items.length - 1);
  }
};

watch(
  () => ({ ...local, items: local.items.map(i => ({ ...i })) }),
  value => {
    if (syncing) return;
    const cleaned = { ...(value as any) };
    delete cleaned.backgroundColor;
    delete cleaned.cardColor;
    delete cleaned.ctaMode;
    delete cleaned.ctaSectionId;
    delete cleaned.ctaLink;
    delete cleaned.ctaLabel;
    emit("update:modelValue", cleaned as TestimonialsSection);
  },
  { deep: true }
);
</script>

<style scoped>
.testimonials-proto-body { display: grid; grid-template-columns: 178px 1fr; min-height: 0; height: 100%; align-items: stretch; }
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
textarea { resize: vertical; min-height: 120px; }

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
.item-grid { display: grid; gap: 10px; grid-template-columns: 1fr 1fr; }
.item-grid--media { grid-template-columns: minmax(0, 220px); }
.item-top-grid { display: grid; gap: 12px; grid-template-columns: 200px 1fr; align-items: start; }
.item-top-fields { display: grid; gap: 10px; grid-template-columns: 1fr; }
.item-top-grid :deep(.image-upload-preview),
.item-top-grid :deep(.mb-3 > .flex.max-h-\[320px\].min-h-\[220px\].w-full.items-center.justify-center.overflow-hidden.rounded-lg.border.border-slate-200.bg-slate-50) {
  min-height: 120px !important;
  max-height: 140px !important;
}
.item-top-grid :deep(.flex.flex-wrap.items-center.gap-3) {
  margin-top: 8px !important;
  display: flex !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  gap: 8px !important;
}
.item-top-grid :deep(.flex.flex-wrap.items-center.gap-3 > label) {
  padding: 6px 10px !important;
  border-radius: 10px !important;
  font-size: 12px !important;
  line-height: 1.2 !important;
}
.item-top-grid :deep(.flex.flex-wrap.items-center.gap-3 > button.text-sm.font-semibold.text-red-500) {
  font-size: 12px !important;
  line-height: 1.2 !important;
  padding: 6px 2px !important;
  margin: 0 !important;
}
.empty-state { border: 1px dashed #cad7d1; border-radius: 12px; padding: 14px; font-size: 13px; color: #64748b; background: #f8fafc; }

@media (max-width: 900px) {
  .testimonials-proto-body { grid-template-columns: 1fr; min-height: 100%; height: 100%; }
  .tabs { border-right: 0; border-bottom: 0; padding: 8px 8px 8px 16px; margin-bottom: 8px; flex-direction: row; }
  .tab { flex: 1; min-width: 0; }
  .tab > span small { display: none; }
  .segment-bar { flex-wrap: wrap; }
  .item-grid, .item-grid--media, .item-top-grid { grid-template-columns: 1fr; }
  .item-top-grid :deep(.flex.flex-wrap.items-center.gap-3) {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
  }
}
</style>

