<template>
  <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.general.titleLabel }}</label>
        <input
          v-model="local.title"
          :placeholder="viewCopy.general.titlePlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.general.subtitleLabel }}</label>
        <textarea
          v-model="local.subtitle"
          :placeholder="viewCopy.general.subtitlePlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          rows="2"
        ></textarea>
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.label }}</label>
        <input
          v-model="local.ctaLabel"
          :placeholder="viewCopy.cta.placeholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
        <p class="mt-1 text-xs text-slate-500">{{ viewCopy.cta.helper }}</p>
      </div>
      <div>
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.cta.linkLabel }}</label>
        <input
          v-model="local.ctaLink"
          :placeholder="viewCopy.cta.linkPlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
        />
        <p class="mt-1 text-xs text-slate-500">{{ viewCopy.cta.linkHelper }}</p>
      </div>
      <div class="md:col-span-2">
        <label class="text-sm font-semibold text-slate-600">{{ viewCopy.description.label }}</label>
        <textarea
          v-model="local.description"
          rows="2"
          :placeholder="viewCopy.description.placeholder"
          class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        ></textarea>
        <p class="mt-1 text-xs text-slate-500">{{ viewCopy.description.helper }}</p>
      </div>
    </div>

    <div class="space-y-3">
      <div
        v-for="(item, index) in local.items"
        :key="index"
        class="space-y-3 rounded-lg border border-slate-100 p-3"
      >
        <div class="grid gap-3 md:grid-cols-3">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.planLabel }}</label>
            <input
              v-model="item.title"
              :placeholder="viewCopy.items.planPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.priceLabel }}</label>
            <div class="flex gap-2">
              <input
                v-model.number="item.price"
                type="number"
                :placeholder="viewCopy.items.pricePlaceholder"
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
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.badgeLabel }}</label>
            <input
              v-model="item.badge"
              :placeholder="viewCopy.items.badgePlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.titleLabelLabel }}</label>
            <input
              v-model="item.titleLabel"
              :placeholder="viewCopy.items.titleLabelPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.priceLabelLabel }}</label>
            <input
              v-model="item.priceLabel"
              :placeholder="viewCopy.items.priceLabelPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.descriptionLabel }}</label>
          <textarea
            v-model="item.description"
            rows="2"
            :placeholder="viewCopy.items.descriptionPlaceholder"
            class="w-full rounded-lg border border-slate-200 px-3 py-2"
          ></textarea>
        </div>

        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.cardCtaLabel }}</label>
            <input
              v-model="item.ctaLabel"
              :placeholder="viewCopy.items.cardCtaPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.items.cardLinkLabel }}</label>
            <input
              v-model="item.ctaLink"
              :placeholder="viewCopy.items.cardLinkPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="item.highlight" class="h-4 w-4" />
          <label class="text-xs font-semibold text-slate-600">{{ viewCopy.items.highlightLabel }}</label>
        </div>

        <div class="rounded-2xl border border-dashed border-emerald-200/70 p-3">
          <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700">{{ viewCopy.checkout.title }}</p>
              <p class="text-xs text-slate-500">{{ viewCopy.checkout.description }}</p>
            </div>
            <label class="inline-flex items-center gap-2 text-xs font-semibold text-slate-600">
              <input
                type="checkbox"
                v-model="item.checkout.enabled"
                class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
              <span>{{
                item.checkout?.enabled ? viewCopy.checkout.enabledLabel : viewCopy.checkout.disabledLabel
              }}</span>
            </label>
          </div>
          <div v-if="item.checkout?.enabled" class="mt-4 space-y-3">
            <div class="grid gap-3 md:grid-cols-2">
              <div>
                <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.checkout.productId }}</label>
                <div class="flex gap-2">
                  <input
                    v-model="item.checkout.productId"
                    readonly
                    class="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-mono"
                  />
                  <button
                    type="button"
                    class="rounded-lg border border-emerald-200 px-3 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
                    @click="copyProductId(item.checkout.productId)"
                  >
                    {{ copiedProductId === item.checkout.productId ? viewCopy.checkout.copied : viewCopy.checkout.copy }}
                  </button>
                </div>
              </div>
              <div>
                <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.checkout.passengersRequired }}</label>
                <input
                  v-model.number="item.checkout.passengersRequired"
                  type="number"
                  min="0"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <p class="mt-1 text-[11px] text-slate-500">{{ viewCopy.checkout.passengersHint }}</p>
              </div>
            </div>
            <div class="grid gap-3 md:grid-cols-3">
              <div>
                <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.checkout.installments }}</label>
                <input
                  v-model.number="item.checkout.installments"
                  type="number"
                  min="1"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <p class="mt-1 text-[11px] text-slate-500">{{ viewCopy.checkout.installmentsHint }}</p>
              </div>
              <div>
                <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.checkout.interestMode }}</label>
                <select
                  v-model="item.checkout.interestMode"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2"
                >
                  <option v-for="option in checkoutInterestOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
              <div>
                <label class="mb-1 block text-xs font-semibold text-slate-500">{{ viewCopy.checkout.maxNoInterest }}</label>
                <input
                  v-model.number="item.checkout.maxInstallmentsNoInterest"
                  type="number"
                  min="0"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <p class="mt-1 text-[11px] text-slate-500">{{ viewCopy.checkout.maxNoInterestHint }}</p>
              </div>
            </div>
          </div>
        </div>

        <button
          class="text-sm font-semibold text-rose-500"
          type="button"
          @click="removeItem(index)"
        >
          {{ viewCopy.items.removeButton }}
        </button>
      </div>

      <button
        class="w-full rounded-lg border border-dashed border-slate-300 px-3 py-3 text-sm font-semibold text-slate-600 hover:border-slate-400"
        type="button"
        @click="addItem"
      >
        {{ viewCopy.items.addButton }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { CurrencyCode, PriceCheckoutConfig, PriceItem, PricesSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: PricesSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PricesSection): void }>();
const t = createAdminLocalizer();

const viewCopy = {
  general: {
    titleLabel: t({ pt: "Titulo", es: "Titulo" }),
    titlePlaceholder: t({ pt: "Planos e opcoes", es: "Planes y opciones" }),
    subtitleLabel: t({ pt: "Subtitulo", es: "Subtitulo" }),
    subtitlePlaceholder: t({ pt: "Escolha o formato que combina com voce.", es: "Elige el formato que combina contigo." })
  },
  cta: {
    label: t({ pt: "Texto do botao", es: "Texto del boton" }),
    placeholder: t({ pt: "Reservar agora", es: "Reservar ahora" }),
    helper: t({ pt: "Define o texto do botao exibido em cada card.", es: "Define el texto del boton mostrado en cada tarjeta." }),
    linkLabel: t({ pt: "Link do botao", es: "Link del boton" }),
    linkPlaceholder: t({ pt: "https://wa.me/...", es: "https://wa.me/..." }),
    linkHelper: t({
      pt: "Por padrao usamos o WhatsApp configurado na agencia com uma mensagem automatica.",
      es: "Por defecto usamos el WhatsApp configurado en la agencia con un mensaje automatico."
    })
  },
  description: {
    label: t({ pt: "Descricao geral", es: "Descripcion general" }),
    placeholder: t({ pt: "Valores sujeitos a alteracao sem aviso previo.", es: "Valores sujetos a cambio sin aviso previo." }),
    helper: t({ pt: "Mostra um aviso abaixo da lista de planos.", es: "Muestra un aviso debajo de la lista de planes." })
  },
  items: {
    planLabel: t({ pt: "Nome do plano", es: "Nombre del plan" }),
    planPlaceholder: t({ pt: "Apartamento duplo", es: "Apartamento doble" }),
    priceLabel: t({ pt: "Valor", es: "Valor" }),
    pricePlaceholder: t({ pt: "3490", es: "3490" }),
    badgeLabel: t({ pt: "Destaque (badge)", es: "Destacado (badge)" }),
    badgePlaceholder: t({ pt: "Mais popular", es: "Mas popular" }),
    titleLabelLabel: t({ pt: "Texto acima do plano", es: "Texto encima del plan" }),
    titleLabelPlaceholder: t({ pt: "Pacote", es: "Paquete" }),
    priceLabelLabel: t({ pt: "Texto ao lado do valor", es: "Texto junto al valor" }),
    priceLabelPlaceholder: t({ pt: "Por pessoa", es: "Por persona" }),
    descriptionLabel: t({ pt: "Descricao do plano", es: "Descripcion del plan" }),
    descriptionPlaceholder: t({ pt: "Inclua detalhes do que esta incluso.", es: "Incluye detalles de lo que esta incluido." }),
    cardCtaLabel: t({ pt: "Texto do botao (card)", es: "Texto del boton (card)" }),
    cardCtaPlaceholder: t({ pt: "Quero saber mais", es: "Quiero saber mas" }),
    cardLinkLabel: t({ pt: "Link do botao (card)", es: "Link del boton (card)" }),
    cardLinkPlaceholder: t({ pt: "https://wa.me/...", es: "https://wa.me/..." }),
    highlightLabel: t({ pt: "Destacar este plano", es: "Destacar este plan" }),
    removeButton: t({ pt: "Remover plano", es: "Eliminar plan" }),
    addButton: t({ pt: "+ Adicionar plano", es: "+ Agregar plan" })
  },
  checkout: {
    title: t({ pt: "Checkout & vendas", es: "Checkout y ventas" }),
    description: t({
      pt: "Ative para vender diretamente via Stripe Connect.",
      es: "Activa para vender directamente con Stripe Connect."
    }),
    productId: t({ pt: "ID do produto", es: "ID del producto" }),
    copy: t({ pt: "Copiar ID", es: "Copiar ID" }),
    copied: t({ pt: "Copiado!", es: "¡Copiado!" }),
    passengersRequired: t({ pt: "Qtd. passageiros", es: "Cant. pasajeros" }),
    passengersHint: t({
      pt: "Define quantos passageiros devem preencher o pós-venda.",
      es: "Define cuántos pasajeros deben completar el post-viaje."
    }),
    installments: t({ pt: "Parcelas máximas", es: "Cuotas máximas" }),
    installmentsHint: t({
      pt: "Informe até quantas parcelas oferecer.",
      es: "Indica hasta cuántas cuotas ofrecer."
    }),
    interestMode: t({ pt: "Juros", es: "Interés" }),
    interestModes: {
      merchant: t({ pt: "Agência absorve juros", es: "Agencia asume intereses" }),
      client: t({ pt: "Cliente paga juros", es: "Cliente paga intereses" })
    },
    maxNoInterest: t({ pt: "Parcelas sem juros", es: "Cuotas sin interés" }),
    maxNoInterestHint: t({
      pt: "0 = nenhuma. Use para limitar as sem juros.",
      es: "0 = ninguna. Úsalo para limitar las sin interés."
    }),
    enabledLabel: t({ pt: "Ativado", es: "Activado" }),
    disabledLabel: t({ pt: "Desativado", es: "Desactivado" })
  }
};

const currencyOptions: { label: string; value: CurrencyCode }[] = [
  { label: t({ pt: "Real (R$)", es: "Real (R$)" }), value: "BRL" },
  { label: t({ pt: "Dolar (US$)", es: "Dolar (US$)" }), value: "USD" },
  { label: t({ pt: "Euro (€)", es: "Euro (€)" }), value: "EUR" },
  { label: t({ pt: "Pesos ($)", es: "Pesos ($)" }), value: "ARS" }
];

const checkoutInterestOptions = [
  { label: viewCopy.checkout.interestModes.merchant, value: "merchant" },
  { label: viewCopy.checkout.interestModes.client, value: "client" }
];

const headingDefaults = getSectionHeadingDefaults("prices");
const defaultTitle = viewCopy.general.titlePlaceholder;
const defaultSubtitle = viewCopy.general.subtitlePlaceholder;
const defaultCtaLabel = viewCopy.cta.placeholder;

const normalizeLink = (value?: string | null) => {
  if (!value) return "";
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed) || trimmed.startsWith("#")) return trimmed;
  return `https://${trimmed}`;
};

const generateProductId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `price_${Math.random().toString(36).slice(2, 10)}`;
};

const ensureCheckoutConfig = (checkout?: PriceCheckoutConfig | null): PriceCheckoutConfig => ({
  enabled: checkout?.enabled ?? false,
  productId: checkout?.productId || generateProductId(),
  passengersRequired: Number(checkout?.passengersRequired ?? 0),
  installments: Number(checkout?.installments ?? 1),
  interestMode: checkout?.interestMode === "client" ? "client" : "merchant",
  maxInstallmentsNoInterest: checkout?.maxInstallmentsNoInterest ?? 0
});

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
        currency: (item.currency as CurrencyCode) || "BRL",
        highlight: !!item.highlight,
        checkout: ensureCheckoutConfig(item.checkout)
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
  value => {
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
    ctaLabel: "",
    ctaLink: "",
    currency: "BRL",
    highlight: false,
    checkout: ensureCheckoutConfig()
  });
};

const removeItem = (index: number) => {
  local.items.splice(index, 1);
};

const copiedProductId = ref<string | null>(null);
let copyTimeout: number | null = null;

const copyProductId = async (productId: string) => {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(productId);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = productId;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    copiedProductId.value = productId;
    if (copyTimeout) {
      window.clearTimeout(copyTimeout);
    }
    copyTimeout = window.setTimeout(() => {
      copiedProductId.value = null;
      copyTimeout = null;
    }, 2000);
  } catch {
    copiedProductId.value = null;
  }
};

onBeforeUnmount(() => {
  if (copyTimeout) {
    window.clearTimeout(copyTimeout);
    copyTimeout = null;
  }
});

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
      currency: (item.currency as CurrencyCode) || "BRL",
      highlight: !!item.highlight,
      checkout: ensureCheckoutConfig(item.checkout)
    }))
  }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as PricesSection);
  },
  { deep: true }
);
</script>
