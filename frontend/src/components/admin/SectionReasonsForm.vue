<template>
  <div class="items-proto-body" v-bind="$attrs">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: activePanel === 'texts' }" @click="activePanel = 'texts'">
        <span class="tab-icon">✎</span>
        <span>Textos<small>Título da seção</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'items' }" @click="activePanel = 'items'">
        <span class="tab-icon">✓</span>
        <span>Itens<small>Benefícios e detalhes</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activePanel === 'texts'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure a chamada principal exibida acima da lista de itens ou benefícios.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido acima do título, como Benefícios, Inclusos ou Aproveite demais.">?</span></label>
            <input v-model="local.headingLabel" />
          </div>

          <div class="field">
            <label>Título da seção <span class="help" data-tip="Título principal da seção de itens. Use para apresentar o valor do que está incluso ou os diferenciais da viagem.">?</span></label>
            <input v-model="local.title" />
          </div>

          <div class="field">
            <label>Subtítulo <span class="help" data-tip="Texto complementar abaixo do título. Pode ser deixado em branco.">?</span></label>
            <input v-model="local.subtitle" placeholder="Ex: Tudo pensado para você aproveitar sem preocupação." />
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Itens da seção</h2>
            <p class="section-desc">Adicione, selecione e reordene os itens exibidos nesta seção.</p>
          </div>
          <div class="segment-actions segment-actions--head">
            <button class="add-segment" type="button" @click="addItem" :disabled="local.items.length >= MAX_ITEMS">+ Adicionar item</button>
          </div>
        </div>

        <div class="content-area">
          <div class="segment-bar">
            <div ref="itemTabsRef" class="segment-tabs">
              <button
                v-for="(item, index) in local.items"
                :key="`item-tab-${index}`"
                type="button"
                data-item-chip
                class="segment-tab"
                :class="{ active: selectedItemIndex === index }"
                @click="selectedItemIndex = index"
              >
                <span class="segment-handle">⋮⋮</span>
                <span class="segment-name">{{ item.title?.trim() || `Item ${index + 1}` }}</span>
                <span class="segment-remove" @click.stop="removeItem(index)">×</span>
              </button>
            </div>
          </div>

          <div v-if="selectedItem" class="segment-panel">
            <div class="item-line-grid">
              <div class="field">
                <label>Ícone <span class="help" data-tip="Escolha um ícone visual para representar este item.">?</span></label>
                <div class="icon-picker-row">
                  <input v-model="selectedItem.icon" />
                  <button type="button" @click="toggleItemPicker(selectedItemIndex, $event)">Escolher ícone</button>
                </div>
              </div>

              <div class="field">
                <label>Título do item <span class="help" data-tip="Nome curto do benefício ou informação exibida no item.">?</span></label>
                <input v-model="selectedItem.title" />
              </div>

              <div class="field description-field">
                <label>Descrição do item <span class="help" data-tip="Explique rapidamente o benefício ou detalhe deste item.">?</span></label>
                <RichTextEditor v-model="selectedItem.description" placeholder="Detalhe o benefício deste item." />
              </div>
            </div>
          </div>

          <div v-else class="empty-state">Adicione um item para começar.</div>
        </div>
      </div>
    </section>
  </div>

  <Teleport to="body">
    <div
      v-if="iconPickerIndex !== null"
      class="icon-picker-overlay"
      @click="closeIconPicker"
    >
      <div class="icon-picker-popover" :style="iconPickerStyle" @click.stop>
        <div class="icon-picker-grid">
          <button
            v-for="icon in allIcons"
            :key="icon"
            type="button"
            class="icon-chip"
            @click="applyIcon(iconPickerIndex, icon)"
          >
            {{ icon }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable, { type SortableEvent } from "sortablejs";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ReasonsSection } from "../../types/page";

defineOptions({ inheritAttrs: false });

const props = defineProps<{ modelValue: ReasonsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ReasonsSection): void }>();
const headingDefaults = getSectionHeadingDefaults("reasons");

const activePanel = ref<"texts" | "items">("texts");
const selectedItemIndex = ref(0);
const iconOptions = ["✨", "🚀", "🌍", "❤️", "⭐", "⚡", "🏆", "📍", "✅", "🎯"];
const extraIcons = ["💡", "🛡️", "🎒", "☎️", "📸", "🧳", "🌐", "🏖️", "⛰️", "💎"];
const allIcons = computed(() => Array.from(new Set([...iconOptions, ...extraIcons])));
const iconPickerIndex = ref<number | null>(null);
const iconPickerStyle = ref<Record<string, string>>({});
const itemTabsRef = ref<HTMLElement | null>(null);
let itemsSortable: Sortable | null = null;

const DEFAULT_ANIMATION_DURATION = 1000;
const DEFAULT_ANIMATION_STAGGER = 300;
const clampDuration = (value?: number) => (typeof value === "number" && !Number.isNaN(value) ? value : DEFAULT_ANIMATION_DURATION);
const clampStagger = (value?: number) => (typeof value === "number" && !Number.isNaN(value) ? value : DEFAULT_ANIMATION_STAGGER);
const MAX_ITEMS = 8;

const local = reactive<ReasonsSection>({
  type: "reasons",
  enabled: true,
  layout: "grid",
  items: [],
  ...props.modelValue,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  enableAnimation: true,
  animationDuration: clampDuration(props.modelValue.animationDuration),
  cardAnimationStagger: clampStagger(props.modelValue.cardAnimationStagger)
});

const selectedItem = computed(() => local.items[selectedItemIndex.value] || null);
let syncing = false;

const syncFromProps = (value: ReasonsSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.items = Array.isArray(value.items) ? value.items.map(item => ({ ...item })) : [];
  local.enableAnimation = true;
  local.animationDuration = clampDuration(value.animationDuration);
  local.cardAnimationStagger = clampStagger(value.cardAnimationStagger);
  if (selectedItemIndex.value >= local.items.length) selectedItemIndex.value = Math.max(0, local.items.length - 1);
  nextTick(() => {
    syncing = false;
  });
};

const addItem = () => {
  if (local.items.length >= MAX_ITEMS) return;
  local.items.push({ title: `Item ${local.items.length + 1}`, description: "Descreva o benefício", icon: "✨" });
  selectedItemIndex.value = local.items.length - 1;
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
  if (iconPickerIndex.value === index) closeIconPicker();
  if (selectedItemIndex.value >= local.items.length) selectedItemIndex.value = Math.max(0, local.items.length - 1);
};

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
    draggable: "button[data-item-chip]",
    handle: ".segment-handle",
    onEnd: handleDragEnd
  });
};

const scheduleSortableRefresh = () => nextTick(initSortable);

const closeIconPicker = () => {
  iconPickerIndex.value = null;
};

const toggleItemPicker = (index: number, event: MouseEvent) => {
  if (iconPickerIndex.value === index) {
    closeIconPicker();
    return;
  }
  const trigger = event.currentTarget as HTMLElement | null;
  if (!trigger) return;
  const rect = trigger.getBoundingClientRect();
  iconPickerStyle.value = {
    top: `${rect.bottom + 8}px`,
    left: `${rect.left}px`
  };
  iconPickerIndex.value = index;
};

const applyIcon = (index: number, icon: string) => {
  if (!local.items[index]) return;
  local.items[index].icon = icon;
  closeIconPicker();
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

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as ReasonsSection);
  },
  { deep: true }
);
</script>

<style scoped>
.items-proto-body {
  display: grid;
  grid-template-columns: 178px 1fr;
  min-height: 0;
  height: 100%;
  align-items: stretch;
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
  padding: 0 9px;
  background: #eef2ef;
  color: #0f172a;
  text-align: left;
  height: 38px;
  min-height: 38px;
  max-height: 38px;
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
  flex-direction: row;
  gap: 1px;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  align-items: center;
}

.tab > span small {
  display: none;
}

.editor {
  padding: 0;
  background: #edf1ef;
  min-width: 0;
  overflow: visible;
  min-height: 100%;
}

.section-card {
  background: transparent;
  border: 0;
  min-height: 0;
  overflow: visible;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
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
  min-width: 0;
  align-content: start;
  overflow: visible;
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

.segment-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: nowrap;
}

.segment-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.segment-tab {
  border: 1px solid #cad7d1;
  border-radius: 999px;
  padding: 5px 9px;
  background: #fff;
  color: #0f172a;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.segment-tab.active {
  border-color: #34c759;
  background: #ecfdf2;
}

.segment-handle {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1;
}

.segment-name {
  font-weight: 700;
  line-height: 1.1;
}

.segment-remove {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 1px solid #d6dde8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #64748b;
}

.segment-actions {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.segment-actions--head {
  margin-left: auto;
}

.add-segment {
  border: 1px solid #cad7d1;
  border-radius: 999px;
  background: #fff;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
  padding: 7px 11px;
}

.segment-panel {
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  min-width: 0;
  overflow: visible;
}

.item-line-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: 0.8fr 1.2fr;
  min-width: 0;
}

.item-line-grid > * {
  min-width: 0;
}

.description-field {
  grid-column: 1 / -1;
  min-width: 0;
}

.icon-picker-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-picker-row input {
  width: 56px;
  min-width: 56px;
  max-width: 56px;
  text-align: center;
  padding-left: 0;
  padding-right: 0;
}

.icon-picker-row button {
  flex: 1;
  border: 1px solid #cad7d1;
  border-radius: 10px;
  background: #fff;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.icon-picker-grid {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.icon-chip {
  width: 36px;
  height: 36px;
  border: 1px solid #cad7d1;
  border-radius: 10px;
  background: #fff;
}

.icon-picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
}

.icon-picker-popover {
  position: fixed;
  z-index: 121;
  width: 240px;
  max-width: calc(100vw - 24px);
  border: 1px solid #cad7d1;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.18);
  padding: 10px;
}

.icon-picker-popover .icon-picker-grid {
  margin-top: 0;
}

.empty-state {
  border: 1px dashed #cad7d1;
  border-radius: 12px;
  padding: 14px;
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
}

.description-field :deep(.rich-shell),
.description-field :deep(.ql-container),
.description-field :deep(.ql-editor) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.description-field :deep(.ql-toolbar.ql-snow),
.description-field :deep(.ql-container.ql-snow) {
  border-color: #cad7d1;
}

.description-field :deep(.ql-container.ql-snow) {
  border-top: 0;
  border-radius: 0 0 12px 12px;
  overflow: visible;
}

.description-field :deep(.ql-toolbar.ql-snow) {
  border-radius: 12px 12px 0 0;
  padding: 6px 8px;
}

.description-field :deep(.ql-editor) {
  min-height: 64px;
  max-height: none;
  overflow-y: visible;
  padding: 10px 12px;
  font-size: 14px;
  height: auto;
}

@media (max-width: 900px) {
  .items-proto-body {
    grid-template-columns: 1fr;
    min-height: 100%;
    height: 100%;
    align-content: start;
    grid-auto-rows: min-content;
  }

  .tabs {
    border-right: 0;
    border-bottom: 0;
    padding: 4px 8px 0 16px;
    flex-direction: row;
    margin-bottom: 8px;
  }

  .editor {
    margin-top: 4px;
  }

  .tab {
    flex: 1;
    min-width: 0;
    padding: 4px 9px;
    min-height: 0;
  }

  .tab-icon {
    width: 18px;
    height: 18px;
    font-size: 10px;
  }

  .tab > span {
    font-size: 14px;
    line-height: 1.05;
  }

  .tab > span small {
    display: none;
  }

  .item-line-grid {
    grid-template-columns: 1fr;
  }

  .section-head {
    padding-top: 0;
  }

  .content-area {
    padding-top: 6px;
  }
}
</style>

