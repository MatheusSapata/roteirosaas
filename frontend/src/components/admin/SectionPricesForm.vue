<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-slate-900">Preços</h3>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="local.enabled" class="h-4 w-4" />
        Ativar
      </label>
    </div>
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />
    <div class="space-y-3">
      <div>
        <label class="text-sm font-semibold text-slate-600">Descrição geral</label>
        <textarea
          v-model="local.description"
          rows="2"
          placeholder="Ex.: Valores sujeitos a alteração sem aviso prévio."
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        ></textarea>
        <p class="text-xs text-slate-500">Mostra um aviso/observação abaixo do título da seção.</p>
      </div>
      <div v-for="(item, index) in local.items" :key="index" class="space-y-3 rounded-lg border border-slate-100 p-3">
        <div class="grid gap-3 md:grid-cols-3">
          <input
            v-model="item.title"
            placeholder="Título"
            class="rounded-lg border border-slate-200 px-3 py-2"
          />
          <div class="flex gap-2">
            <input
              v-model.number="item.price"
              type="number"
              placeholder="Preço"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
            <select v-model="item.currency" class="min-w-[110px] rounded-lg border border-slate-200 px-2 py-2 text-sm">
              <option v-for="option in currencyOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <input
            v-model="item.badge"
            placeholder="Badge (ex.: Mais popular)"
            class="rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <input
            v-model="item.titleLabel"
            placeholder='Texto acima do título (ex.: "Pacote")'
            class="rounded-lg border border-slate-200 px-3 py-2"
          />
          <input
            v-model="item.priceLabel"
            placeholder="Texto acima do preço (ex.: Por pessoa)"
            class="rounded-lg border border-slate-200 px-3 py-2"
          />
          <input
            v-model="item.description"
            placeholder="Texto abaixo do preço"
            class="rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <label class="flex items-center gap-2 text-sm font-semibold text-slate-600">
            <input type="checkbox" v-model="item.highlight" class="h-4 w-4" />
            Destacar plano
          </label>
          <button class="text-sm text-red-500" type="button" @click="removeItem(index)">Remover</button>
        </div>
      </div>
      <button class="text-sm font-semibold text-brand" @click="addItem">+ Adicionar preço</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { CurrencyCode, PriceItem, PricesSection } from "../../types/page";

const props = defineProps<{ modelValue: PricesSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PricesSection): void }>();
const currencyOptions: { label: string; value: CurrencyCode }[] = [
  { label: "Real (R$)", value: "BRL" },
  { label: "Dólar (US$)", value: "USD" },
  { label: "Euro (€)", value: "EUR" },
  { label: "Pesos ($)", value: "ARS" }
];

const cloneItems = (items?: PriceItem[]) =>
  Array.isArray(items)
    ? items.map(item => ({
        ...item,
        highlight: !!item.highlight,
        currency: (item.currency as CurrencyCode) || "BRL",
        titleLabel: item.titleLabel || "",
        priceLabel: item.priceLabel || "",
        badge: item.badge || "",
        description: item.description || ""
      }))
    : [];
const headingDefaults = getSectionHeadingDefaults("prices");

const local = reactive<PricesSection>({
  ...props.modelValue,
  layout: "columns",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  items: cloneItems(props.modelValue.items)
});
let syncing = false;
const syncFromProps = (value: PricesSection) => {
  syncing = true;
  Object.assign(local, value);
  local.layout = "columns";
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.items = cloneItems(value.items);
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
const colorOptions = [
  { label: "Branco", value: "#ffffff" },
  { label: "Cinza suave", value: "#f8fafc" },
  { label: "Azul claro", value: "#e0f2fe" },
  { label: "Marfim", value: "#fef3c7" },
  { label: "Rosa claro", value: "#fdf2f8" },
  { label: "Verde menta", value: "#ecfdf3" },
  { label: "Lilás", value: "#f5f3ff" },
  { label: "Turquesa", value: "#e0f7f7" },
  { label: "Cinza médio", value: "#e2e8f0" },
  { label: "Grafite", value: "#0f172a" }
];

const addItem = () =>
  local.items.push({
    title: "",
    titleLabel: "",
    price: 0,
    description: "",
    priceLabel: "",
    badge: "",
    currency: "BRL",
    highlight: false
  });
const removeItem = (index: number) => local.items.splice(index, 1);

watch(
  () => ({ ...local, items: local.items.map(item => ({ ...item, highlight: !!item.highlight })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as PricesSection);
  },
  { deep: true }
);
</script>
