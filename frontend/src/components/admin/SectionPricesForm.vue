<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <SectionHeadingControls
      v-model:label="local.headingLabel"
      v-model:style="local.headingLabelStyle"
    />

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Título</label>
        <input
          v-model="local.title"
          placeholder="Planos e opções"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>

      <div>
        <label class="text-sm font-semibold text-slate-600">Subtítulo</label>
        <textarea
          v-model="local.subtitle"
          placeholder="Escolha o formato que combina com você."
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          rows="2"
        ></textarea>
      </div>
    </div>

    <!-- Configurações gerais -->
    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">Texto do botão</label>
        <input
          v-model="local.ctaLabel"
          placeholder="Ex.: Reservar agora"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
        <p class="mt-1 text-xs text-slate-500">Define o texto do botão exibido nos cards.</p>
      </div>

      <div>
        <label class="text-sm font-semibold text-slate-600">Link do botão</label>
        <input
          v-model="local.ctaLink"
          placeholder="https://wa.me/55999...?text=Oi%20tenho%20interesse..."
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
        <p class="mt-1 text-xs text-slate-500">
          Por padrão usamos o WhatsApp configurado na agência com a mensagem
          “Oi, tenho interesse no plano &lt;nome&gt; do roteiro &lt;roteiro&gt;”.
        </p>
      </div>

      <div class="md:col-span-2">
        <label class="text-sm font-semibold text-slate-600">Descrição geral</label>
        <textarea
          v-model="local.description"
          rows="2"
          placeholder="Ex.: Valores sujeitos a alteração sem aviso prévio."
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        ></textarea>
        <p class="mt-1 text-xs text-slate-500">
          Mostra um aviso/observação abaixo de todos os planos/valores no fim da seção.
        </p>
      </div>
    </div>

    <!-- Itens -->
    <div class="space-y-3">
      <div
        v-for="(item, index) in local.items"
        :key="index"
        class="space-y-3 rounded-lg border border-slate-100 p-3"
      >
        <div class="grid gap-3 md:grid-cols-3">
          <!-- Nome do plano -->
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Nome do plano</label>
            <input
              v-model="item.title"
              placeholder="Ex: Apartamento duplo"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>

          <!-- Valor -->
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Valor</label>
            <div class="flex gap-2">
              <input
                v-model.number="item.price"
                type="number"
                placeholder="3490"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
              <select
                v-model="item.currency"
                class="min-w-[110px] rounded-lg border border-slate-200 px-2 py-2 text-sm"
              >
                <option v-for="option in currencyOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- Badge -->
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Destaque (badge)</label>
            <input
              v-model="item.badge"
              placeholder="Ex: Mais popular"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2">
          <!-- Texto acima do plano -->
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Texto acima do plano</label>
            <input
              v-model="item.titleLabel"
              placeholder="Ex: Pacote"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>

          <!-- Texto acima do preço -->
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Texto acima do preço</label>
            <input
              v-model="item.priceLabel"
              placeholder="Ex: Por pessoa"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>

          <!-- Texto abaixo do preço -->
          <div class="md:col-span-2">
            <label class="mb-1 block text-xs font-semibold text-slate-500">Texto abaixo do preço</label>
            <input
              v-model="item.description"
              placeholder="Ex: Entrada + hospedagem + café"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3">
          <label class="flex items-center gap-2 text-sm font-semibold text-slate-600">
            <input type="checkbox" v-model="item.highlight" class="h-4 w-4" />
            Destacar plano
          </label>

          <button class="text-sm text-red-500" type="button" @click="removeItem(index)">
            Remover
          </button>
        </div>
      </div>

      <button type="button" class="text-sm font-semibold text-brand" @click="addItem">
        + Adicionar preço
      </button>
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

const headingDefaults = getSectionHeadingDefaults("prices");
const defaultTitle = "Planos e opções";
const defaultSubtitle = "Escolha o formato que combina com você.";
const defaultCtaLabel = "Reservar agora";

const normalizeLink = (value?: string | null) => {
  if (!value) return "";
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed) || trimmed.startsWith("#")) return trimmed;
  return `https://${trimmed}`;
};

const cloneItems = (items?: PriceItem[]): PriceItem[] =>
  Array.isArray(items)
    ? items.map((item) => ({
        ...item,
        title: item.title || "",
        titleLabel: item.titleLabel || "",
        price: Number(item.price || 0),
        description: item.description || "",
        priceLabel: item.priceLabel || "",
        badge: item.badge || "",
        currency: (item.currency as CurrencyCode) || "BRL",
        highlight: !!item.highlight
      }))
    : [];

const local = reactive<PricesSection>({
  ...props.modelValue,
  layout: "columns",
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  title: props.modelValue.title ?? defaultTitle,
  subtitle: props.modelValue.subtitle ?? defaultSubtitle,
  description: props.modelValue.description || "",
  ctaLabel: props.modelValue.ctaLabel || defaultCtaLabel,
  ctaLink: props.modelValue.ctaLink || "",
  items: cloneItems(props.modelValue.items)
});

let syncing = false;

const syncFromProps = (value: PricesSection) => {
  syncing = true;

  Object.assign(local, value);

  local.layout = "columns";
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle ?? headingDefaults.style;
  local.title = value.title ?? defaultTitle;
  local.subtitle = value.subtitle ?? defaultSubtitle;
  local.description = value.description || "";
  local.ctaLabel = value.ctaLabel || defaultCtaLabel;
  local.ctaLink = value.ctaLink || "";
  local.items = cloneItems(value.items);

  nextTick(() => {
    syncing = false;
  });
};

watch(
  () => props.modelValue,
  (value) => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

const addItem = () => {
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
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
};

watch(
  () => ({
    ...local,
    layout: "columns",
    ctaLink: normalizeLink(local.ctaLink),
    items: local.items.map((item) => ({
      ...item,
      title: item.title || "",
      titleLabel: item.titleLabel || "",
      price: Number(item.price || 0),
      description: item.description || "",
      priceLabel: item.priceLabel || "",
      badge: item.badge || "",
      currency: (item.currency as CurrencyCode) || "BRL",
      highlight: !!item.highlight
    }))
  }),
  (value) => {
    if (syncing) return;
    emit("update:modelValue", value as PricesSection);
  },
  { deep: true }
);
</script>