<template>
  <div class="prices-proto-body">
    <aside class="tabs">
      <button type="button" class="tab" :class="{ active: activePanel === 'texts' }" @click="activePanel = 'texts'">
        <span class="tab-icon" v-html="adminTabIcons.text"></span>
        <span>Textos<small>Chamada da seção</small></span>
      </button>
      <button type="button" class="tab" :class="{ active: activePanel === 'plans' }" @click="activePanel = 'plans'">
        <span class="tab-icon" v-html="adminTabIcons.prices"></span>
        <span>Preços<small>Valores e condições</small></span>
      </button>
    </aside>

    <section class="editor">
      <div v-if="activePanel === 'texts'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure a chamada exibida acima dos planos e a observação geral exibida no final.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>Etiqueta acima do título <span class="help" data-tip="Texto pequeno exibido acima do título, como Sobre os valores ou Planos disponíveis.">?</span></label>
            <input v-model="local.headingLabel" />
          </div>

          <div class="field">
            <label>Título da seção <span class="help" data-tip="Título principal exibido acima dos cards de preço.">?</span></label>
            <input v-model="local.title" />
          </div>

          <div class="field">
            <label>Subtítulo <span class="help" data-tip="Texto complementar abaixo do título. Use para orientar a escolha do visitante.">?</span></label>
            <input v-model="local.subtitle" />
          </div>

          <div class="field">
            <label>Observação geral ao final <span class="help" data-tip="Texto exibido abaixo de todos os preços.">?</span></label>
            <textarea v-model="local.description" rows="3"></textarea>
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Planos e valores</h2>
            <p class="section-desc">Adicione, selecione e reordene os cards de preço exibidos na seção.</p>
          </div>
          <div class="segment-actions segment-actions--head">
            <button class="add-segment" type="button" @click="addItem">+ Adicionar plano</button>
          </div>
        </div>

        <div class="content-area">
          <div class="segment-bar">
            <div ref="planTabsRef" class="segment-tabs">
              <button
                v-for="(item, index) in local.items"
                :key="getPlanKey(item)"
                type="button"
                data-plan-chip
                class="segment-tab"
                :class="{ active: selectedPlanIndex === index }"
                @click="selectedPlanIndex = index"
              >
                <span class="segment-handle">⋮⋮</span>
                <span class="segment-name">{{ item.title?.trim() || `Plano ${index + 1}` }}</span>
                <span class="segment-remove" @click.stop="removeItem(index)">×</span>
              </button>
            </div>
          </div>

          <div v-if="selectedPlan" class="segment-panel">
            <div class="feature-toggle" :class="{ highlighted: selectedPlan.highlight }">
              <div>
                <strong>Destacar plano</strong>
                <span>Este card ganha mais contraste na página.</span>
              </div>
              <label class="check-pill" :class="{ inactive: !selectedPlan.highlight }">
                <input type="checkbox" v-model="selectedPlan.highlight" />
                {{ selectedPlan.highlight ? "Ativo" : "Inativo" }}
              </label>
            </div>

            <div class="price-row-double">
              <div class="field">
                <label>Texto acima do nome <span class="help" data-tip="Texto pequeno exibido acima do nome do pacote.">?</span></label>
                <input v-model="selectedPlan.titleLabel" />
              </div>
              <div class="field">
                <label>Nome do plano <span class="help" data-tip="Nome principal exibido no card de preço.">?</span></label>
                <input v-model="selectedPlan.title" />
              </div>
            </div>

            <div class="price-row-triple">
              <div class="field">
                <label>Etiqueta acima do preço <span class="help" data-tip="Texto curto exibido acima do valor principal, como Promoção ou Mais vendido.">?</span></label>
                <input v-model="selectedPlan.badge" placeholder="Ex: Promoção" />
              </div>
              <div class="field">
                <label>Prefixo do valor <span class="help" data-tip="Texto exibido antes do preço.">?</span></label>
                <input v-model="selectedPlan.priceLabel" placeholder="por apenas" />
              </div>
              <div class="field">
                <label>Valor principal <span class="help" data-tip="Valor em destaque no card.">?</span></label>
                <div class="price-input-row">
                  <input
                    :value="priceDrafts[selectedPlanIndex] ?? formatPriceDraft(selectedPlan.price)"
                    @input="onPriceDraftInput(selectedPlanIndex, ($event.target as HTMLInputElement).value)"
                    placeholder="Ex: 1.499,00"
                    inputmode="decimal"
                  />
                  <select v-model="selectedPlan.currency" aria-label="Moeda do valor">
                    <option v-for="currency in currencyOptions" :key="currency.code" :value="currency.code">
                      {{ currency.code }} — {{ currency.label }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="field">
                <label>Condição abaixo do valor <span class="help" data-tip="Texto exibido abaixo do preço.">?</span></label>
                <input v-model="selectedPlan.description" placeholder="em até 10x sem juros" />
              </div>
            </div>

            <div class="button-link-grid">
              <div class="field">
                <label>Texto do botão <span class="help" data-tip="Frase exibida no botão deste plano.">?</span></label>
                <input v-model="selectedPlan.ctaLabel" />
              </div>
              <div class="field">
                <label>Link do botão <span class="help" data-tip="Link aberto no clique deste plano.">?</span></label>
                <input v-model="selectedPlan.ctaLink" />
              </div>
              <div class="field price-inline-toggle">
                <label class="inline-check"><input type="checkbox" v-model="selectedPlan.ctaOpenInNewTab" /> Abrir em nova aba</label>
              </div>
            </div>

          </div>

          <div v-else class="empty-state">Adicione um plano para começar.</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable, { type SortableEvent } from "sortablejs";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { CurrencyCode, PriceItem, PricesSection } from "../../types/page";
import { adminTabIcons } from "../../utils/adminTabIcons";

const props = defineProps<{ modelValue: PricesSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PricesSection): void }>();

const activePanel = ref<"texts" | "plans">("texts");
const selectedPlanIndex = ref(0);
const planTabsRef = ref<HTMLElement | null>(null);
let plansSortable: Sortable | null = null;
const planKeys = new WeakMap<object, number>();
let nextPlanKey = 0;

const getPlanKey = (item: PriceItem) => {
  const existingKey = planKeys.get(item);
  if (existingKey !== undefined) return existingKey;
  const key = nextPlanKey++;
  planKeys.set(item, key);
  return key;
};

const headingDefaults = getSectionHeadingDefaults("prices");
const priceDrafts = ref<string[]>([]);

const currencyOptions: Array<{ code: CurrencyCode; label: string }> = [
  { code: "BRL", label: "Real brasileiro" },
  { code: "USD", label: "Dólar americano" },
  { code: "EUR", label: "Euro" },
  { code: "GBP", label: "Libra esterlina" },
  { code: "JPY", label: "Iene japonês" },
  { code: "CNY", label: "Yuan chinês" },
  { code: "CAD", label: "Dólar canadense" },
  { code: "AUD", label: "Dólar australiano" },
  { code: "CHF", label: "Franco suíço" },
  { code: "INR", label: "Rupia indiana" },
  { code: "MXN", label: "Peso mexicano" },
  { code: "ARS", label: "Peso argentino" },
  { code: "CLP", label: "Peso chileno" },
  { code: "COP", label: "Peso colombiano" },
  { code: "PEN", label: "Sol peruano" },
  { code: "UYU", label: "Peso uruguaio" },
  { code: "AED", label: "Dirham dos Emirados" },
  { code: "NZD", label: "Dólar neozelandês" },
  { code: "SGD", label: "Dólar de Singapura" },
  { code: "HKD", label: "Dólar de Hong Kong" },
  { code: "KRW", label: "Won sul-coreano" },
  { code: "ZAR", label: "Rand sul-africano" }
];

const normalizeLink = (value?: string | null) => {
  if (!value) return "";
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed) || trimmed.startsWith("#")) return trimmed;
  return `https://${trimmed}`;
};

const cloneItems = (items?: PriceItem[]): PriceItem[] =>
  Array.isArray(items)
    ? items.map(item => ({
        ...item,
        title: item.title || "",
        titleLabel: item.titleLabel || "",
        price: Number(item.price || 0),
        description: item.description || "",
        priceLabel: item.priceLabel || "",
        badge: item.badge || "",
        ctaLabel: item.ctaLabel || "",
        ctaLink: item.ctaLink || "",
        ctaOpenInNewTab: item.ctaOpenInNewTab !== false,
        currency: (item.currency as CurrencyCode) || "BRL",
        highlight: !!item.highlight
      }))
    : [];

const formatPriceDraft = (value?: number) => {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return String(value);
};

const parsePriceInput = (raw: string) => {
  const onlyNumeric = raw.replace(/[^\d.,]/g, "").trim();
  if (!onlyNumeric) return 0;
  const normalized = onlyNumeric.replace(/\./g, "").replace(",", ".");
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
};

const local = reactive<PricesSection>({
  ...props.modelValue,
  layout: "columns",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title ?? "Planos e opções",
  subtitle: props.modelValue.subtitle ?? "Escolha o formato que combina com você.",
  description: props.modelValue.description || "",
  ctaLabel: props.modelValue.ctaLabel || "Reservar agora",
  ctaLink: props.modelValue.ctaLink || "",
  ctaOpenInNewTab: props.modelValue.ctaOpenInNewTab !== false,
  items: cloneItems(props.modelValue.items)
});

const selectedPlan = computed(() => local.items[selectedPlanIndex.value] || null);
let syncing = false;

const handleDragEnd = (event: SortableEvent) => {
  const from = event.oldIndex;
  const to = event.newIndex;
  if (from === undefined || to === undefined || from === to) return;
  const moved = local.items.splice(from, 1)[0];
  if (!moved) return;
  local.items.splice(to, 0, moved);
  const movedDraft = priceDrafts.value.splice(from, 1)[0];
  priceDrafts.value.splice(to, 0, movedDraft ?? formatPriceDraft(moved.price));
  if (selectedPlanIndex.value === from) selectedPlanIndex.value = to;
  else if (selectedPlanIndex.value > from && selectedPlanIndex.value <= to) selectedPlanIndex.value -= 1;
  else if (selectedPlanIndex.value < from && selectedPlanIndex.value >= to) selectedPlanIndex.value += 1;
};

const destroySortable = () => {
  if (!plansSortable) return;
  plansSortable.destroy();
  plansSortable = null;
};

const initSortable = () => {
  if (!planTabsRef.value || local.items.length <= 1) {
    destroySortable();
    return;
  }
  destroySortable();
  plansSortable = Sortable.create(planTabsRef.value, {
    animation: 160,
    draggable: "button[data-plan-chip]",
    handle: ".segment-handle",
    onEnd: handleDragEnd
  });
};

const scheduleSortableRefresh = () => nextTick(initSortable);

const syncFromProps = (value: PricesSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = "columns";
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle ?? headingDefaults.style;
  local.title = value.title ?? "Planos e opções";
  local.subtitle = value.subtitle ?? "Escolha o formato que combina com você.";
  local.description = value.description || "";
  local.ctaLabel = value.ctaLabel || "Reservar agora";
  local.ctaLink = value.ctaLink || "";
  local.ctaOpenInNewTab = value.ctaOpenInNewTab !== false;
  local.items = cloneItems(value.items);
  priceDrafts.value = local.items.map(item => formatPriceDraft(item.price));
  if (selectedPlanIndex.value >= local.items.length) selectedPlanIndex.value = Math.max(0, local.items.length - 1);
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
    if (panel === "plans") scheduleSortableRefresh();
  }
);

const addItem = () => {
  local.items.push({
    title: `Plano ${local.items.length + 1}`,
    titleLabel: "",
    price: 0,
    description: "",
    priceLabel: "",
    badge: "",
    ctaLabel: "",
    ctaLink: "",
    ctaOpenInNewTab: true,
    currency: "BRL",
    highlight: false
  });
  priceDrafts.value.push("");
  selectedPlanIndex.value = local.items.length - 1;
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
  priceDrafts.value.splice(index, 1);
  if (selectedPlanIndex.value >= local.items.length) selectedPlanIndex.value = Math.max(0, local.items.length - 1);
};

const onPriceDraftInput = (index: number, raw: string) => {
  priceDrafts.value[index] = raw;
  if (!local.items[index]) return;
  local.items[index].price = parsePriceInput(raw);
};

watch(
  () => ({
    ...local,
    layout: "columns",
    ctaLink: normalizeLink(local.ctaLink),
    items: local.items.map(item => ({
      ...item,
      title: item.title || "",
      titleLabel: item.titleLabel || "",
      price: Number(item.price || 0),
      description: item.description || "",
      priceLabel: item.priceLabel || "",
      badge: item.badge || "",
      ctaLabel: item.ctaLabel || "",
      ctaLink: normalizeLink(item.ctaLink),
      ctaOpenInNewTab: item.ctaOpenInNewTab !== false,
      currency: (item.currency as CurrencyCode) || "BRL",
      highlight: !!item.highlight
    }))
  }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as PricesSection);
  },
  { deep: true }
);
</script>

<style scoped>
.prices-proto-body { display: grid; grid-template-columns: 178px 1fr; height: 100%; min-height: 0; align-items: stretch; background: #fff; }
.tabs { border-right: 1px solid #e6eee8; padding: 16px 12px 16px 16px; display: flex; flex-direction: column; gap: 8px; background: #fff; }
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
input, textarea, select { width: 100%; border: 1px solid #cad7d1; border-radius: 12px; background: #fff; font-size: 16px; line-height: 1.25; padding: 9px 12px; color: #1f2937; }
input:focus, textarea:focus, select:focus { outline: none; border-color: #9cb5aa; box-shadow: 0 0 0 2px rgba(52,199,89,.15); }
textarea { resize: vertical; }

.segment-bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.segment-tabs { display: flex; flex-wrap: wrap; gap: 6px; min-width: 0; }
.segment-tab { border: 1px solid #cad7d1; border-radius: 999px; padding: 5px 9px; background: #fff; color: #0f172a; font-size: 11px; display: inline-flex; align-items: center; gap: 6px; }
.segment-tab.active { border-color: #34c759; background: #ecfdf2; }
.segment-handle { color: #94a3b8; font-size: 12px; line-height: 1; }
.segment-handle { cursor: grab; touch-action: none; user-select: none; }
.sortable-chosen .segment-handle { cursor: grabbing; }
.segment-name { font-weight: 700; line-height: 1.1; }
.segment-remove { width: 16px; height: 16px; border-radius: 999px; border: 1px solid #d6dde8; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; color: #64748b; }
.segment-actions { display: flex; flex-shrink: 0; }
.segment-actions--head { margin-left: auto; }
.add-segment { border: 1px solid #cad7d1; border-radius: 999px; background: #fff; color: #475569; font-size: 11px; font-weight: 700; padding: 7px 11px; }

.segment-panel { border: 0; border-radius: 0; padding: 0; background: transparent; display: grid; gap: 10px; }
.feature-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 10px; border-radius: 12px; border: 1px solid #d9e5dd; background: #fff; }
.feature-toggle.highlighted { border-color: #34c759; background: #ecfdf2; }
.feature-toggle strong { display: block; font-size: 13px; color: #0f172a; }
.feature-toggle span { display: block; margin-top: 2px; font-size: 11px; color: #64748b; }
.check-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: #166534; }
.check-pill.inactive { color: #64748b; }

.price-row-double { display: grid; gap: 10px; grid-template-columns: 1fr 1fr; }
.price-row-triple { display: grid; gap: 10px; grid-template-columns: 0.85fr 0.85fr 1.3fr; }
.button-link-grid { display: grid; gap: 10px; grid-template-columns: 1fr 1fr auto; align-items: end; }
.price-input-row { display: grid; gap: 8px; grid-template-columns: 1fr 130px; }
.inline-check { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: #475569; text-transform: none; letter-spacing: 0; font-weight: 700; }
.inline-check { white-space: nowrap; }
.price-inline-toggle { align-self: end; }
.price-inline-toggle { justify-self: start; }
.empty-state { border: 1px dashed #cad7d1; border-radius: 12px; padding: 14px; font-size: 13px; color: #64748b; background: #f8fafc; }

.prices-proto-body,
.editor {
  background: var(--background);
  color: var(--foreground);
}
.tabs { border-color: var(--border); background: var(--card); }
.tab { border-color: var(--border); background: var(--muted); color: var(--foreground); }
.tab.active { border-color: var(--primary); background: var(--primary); color: var(--primary-foreground); }
.tab > span small,
.section-desc,
.feature-toggle span,
.inline-check { color: var(--muted-foreground); }
.section-head { border-color: color-mix(in srgb, var(--border) 62%, transparent); }
.section-title,
.feature-toggle strong { color: var(--foreground); }
input, textarea, select {
  border-color: var(--input);
  background: var(--card);
  color: var(--foreground);
}
input:focus, textarea:focus, select:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent);
}
.segment-tab,
.add-segment,
.feature-toggle,
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
.segment-handle,
.segment-remove { color: var(--muted-foreground); }
.segment-remove {
  border-color: var(--border);
  background: color-mix(in srgb, var(--card) 78%, transparent);
}
.add-segment:hover {
  border-color: color-mix(in srgb, var(--primary) 38%, var(--border));
  background: var(--accent);
}
.feature-toggle.highlighted {
  border-color: color-mix(in srgb, var(--primary) 45%, var(--border));
  background: color-mix(in srgb, var(--primary) 12%, var(--card));
}
.help:hover::after {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

@media (max-width: 900px) {
  .prices-proto-body { grid-template-columns: 1fr; min-height: 100%; height: 100%; }
  .tabs { border-right: 0; border-bottom: 0; padding: 8px 8px 8px 16px; margin-bottom: 8px; flex-direction: row; }
  .tab { flex: 1; min-width: 0; }
  .tab > span small { display: none; }
  .segment-bar { flex-wrap: wrap; }
  .price-row-double, .price-row-triple, .button-link-grid, .price-input-row { grid-template-columns: 1fr; }
}
</style>

