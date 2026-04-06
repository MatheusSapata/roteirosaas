<template>
  <section class="w-full" :id="section.anchorId || undefined" :style="sectionStyle">
    <div class="mx-auto max-w-6xl px-6 py-12 space-y-8">
      <div class="text-center">
        <div class="flex justify-center">
          <SectionHeadingChip :text="headingLabel" :styleType="headingStyle" :accent="accentColor" />
        </div>
        <h2 class="mt-2 text-3xl font-bold md:text-4xl" :style="{ color: primaryText }">{{ title }}</h2>
        <p v-if="subtitle" class="text-sm" :style="{ color: mutedText }">{{ subtitle }}</p>
      </div>

      <div v-if="loading" class="rounded-3xl border border-dashed border-slate-200 bg-white/60 p-6 text-center text-sm text-slate-500 shadow-sm">
        Atualizando disponibilidade...
      </div>

      <div
        v-else-if="errorMessage"
        class="rounded-3xl border border-rose-200 bg-rose-50/70 p-6 text-center text-sm font-medium text-rose-700"
      >
        {{ errorMessage }}
      </div>

      <div
        v-else-if="!product"
        class="rounded-3xl border border-dashed border-slate-200 bg-white/60 p-6 text-center text-sm text-slate-500 shadow-sm"
      >
        Selecione um produto no editor para habilitar esta seção.
      </div>

      <div v-else class="grid gap-8 lg:grid-cols-[minmax(0,2fr),minmax(320px,1fr)]">
        <div class="space-y-4">
          <article
            v-for="variation in activeVariations"
            :key="variation.public_id"
            class="space-y-3 rounded-3xl border border-slate-100 bg-white/90 p-5 shadow-lg shadow-slate-900/5 transition"
            :class="[{ 'opacity-60': !productActive || isOutOfStock(variation) }]"
          >
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Pacote</p>
                <h3 class="text-xl font-semibold text-slate-900">{{ variation.name }}</h3>
                <p v-if="variation.description" class="text-sm text-slate-600">{{ variation.description }}</p>
              </div>
              <span
                v-if="variationBadge(variation)"
                class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700"
              >
                {{ variationBadge(variation) }}
              </span>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p class="text-2xl font-bold text-slate-900">
                  {{ formatCurrency(variation.price_cents, variation.currency) }}
                </p>
                <p class="text-xs text-slate-500">
                  Inclui {{ variation.people_included }}
                  {{ variation.people_included === 1 ? "pessoa" : "pessoas" }}
                </p>
              </div>
              <div class="flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1">
                <button
                  type="button"
                  class="grid h-9 w-9 place-items-center rounded-full border border-slate-200 text-lg font-semibold text-slate-700 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
                  @click="decrement(variation)"
                  :disabled="!canDecrement(variation)"
                >
                  &minus;
                </button>
                <span class="min-w-[2ch] text-center font-semibold text-slate-900">{{ getQuantity(variation) }}</span>
                <button
                  type="button"
                  class="grid h-9 w-9 place-items-center rounded-full border border-slate-200 bg-white text-lg font-semibold text-slate-900 transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-40"
                  @click="increment(variation)"
                  :disabled="!canIncrement(variation)"
                >
                  +
                </button>
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
              <span>{{ variationAvailabilityText(variation) }}</span>
              <span v-if="isOutOfStock(variation)" class="font-semibold text-rose-600">Sem vagas</span>
              <span v-else-if="isLowStock(variation)" class="font-semibold text-amber-600">Últimas vagas</span>
            </div>
          </article>

          <div
            v-if="!activeVariations.length"
            class="rounded-3xl border border-dashed border-slate-200 bg-white/60 p-6 text-center text-sm text-slate-500"
          >
            Nenhuma variação ativa disponível neste produto.
          </div>
        </div>

        <aside class="space-y-4 rounded-3xl border border-slate-100 bg-white/90 p-5 shadow-xl shadow-slate-900/5">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Informações da viagem</p>
              <span
                class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
                :class="productActive ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
              >
                {{ productStatusLabel }}
              </span>
            </div>
            <p class="text-sm font-semibold text-slate-900">{{ tripDateLabel }}</p>
          </div>

          <div class="space-y-3 rounded-3xl border border-slate-100 bg-slate-50/70 p-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-900">Carrinho</p>
              <button
                v-if="!cartEmpty"
                type="button"
                class="text-xs font-semibold text-slate-500 hover:text-rose-500"
                @click="clearCart"
              >
                Limpar
              </button>
            </div>
            <ul v-if="!cartEmpty" class="space-y-2">
              <li
                v-for="item in selectedItems"
                :key="item.variation.public_id"
                class="flex items-center justify-between text-sm text-slate-700"
              >
                <div>
                  <p class="font-semibold text-slate-900">{{ item.quantity }}x {{ item.variation.name }}</p>
                  <p class="text-xs text-slate-500">
                    {{ item.peopleCount }} {{ item.peopleCount === 1 ? "passageiro" : "passageiros" }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="font-semibold text-slate-900">
                    {{ formatCurrency(item.lineTotal, item.variation.currency) }}
                  </p>
                  <button
                    type="button"
                    class="text-[11px] font-semibold text-rose-500 hover:underline"
                    @click="setQuantity(item.variation, 0)"
                  >
                    remover
                  </button>
                </div>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">Selecione quantidades nos pacotes para montar a venda.</p>
            <div class="flex items-center justify-between border-t border-slate-200 pt-3 text-sm font-semibold text-slate-900">
              <span>Total</span>
              <span>{{ formatCurrency(cartTotalCents, cartCurrency) }}</span>
            </div>
            <p v-if="cartPassengers" class="text-xs text-slate-500">
              Inclui {{ cartPassengers }} {{ cartPassengers === 1 ? "passageiro" : "passageiros" }}.
            </p>
            <button
              type="button"
              class="w-full rounded-full px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              :style="{ backgroundColor: accentColor }"
              :disabled="!canCheckout"
              @click="handleCheckout"
            >
              {{ checkoutButtonLabel }}
            </button>
            <p v-if="!checkoutAvailable" class="text-xs text-slate-500">
              Checkout disponível apenas na visualização pública.
            </p>
            <p v-else-if="!productActive" class="text-xs text-rose-500">
              Ative o produto para habilitar novas vendas.
            </p>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, reactive, ref, watch } from "vue";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { getSectionHeadingDefaults, resolveHeadingLabel } from "../../utils/sectionHeadings";
import type { ProductsSection } from "../../types/page";
import type { ProductDetail, ProductVariation } from "../../types/finance";
import { getPublicProductDetail } from "../../services/finance";
import { createLocalizer, getCurrentLanguage, type LocalizedString } from "../../utils/i18n";
import { deriveTextPalette } from "../../utils/colorContrast";
import { PUBLIC_PRODUCT_CHECKOUT_KEY, type ProductCheckoutPayload } from "../../utils/checkoutKeys";

const props = defineProps<{ section: ProductsSection }>();

const headingDefaults = getSectionHeadingDefaults("products");
const currentLanguage = getCurrentLanguage();
const localize = createLocalizer(currentLanguage);

const loading = ref(false);
const errorMessage = ref<string | null>(null);
const product = ref<ProductDetail | null>(null);
const cart = reactive<Record<string, number>>({});
const checkoutBridge = inject(PUBLIC_PRODUCT_CHECKOUT_KEY, null);

const sectionStyle = computed(() => ({
  background: props.section.backgroundColor || "linear-gradient(180deg,#f8fafc,#fff)"
}));

const headingLabel = computed(() => resolveHeadingLabel(props.section.headingLabel, headingDefaults.label, localize));
const headingStyle = computed(() => props.section.headingLabelStyle || headingDefaults.style);
const defaultTitle: LocalizedString = { pt: "Pacotes disponíveis", es: "Paquetes disponibles" };
const defaultSubtitle: LocalizedString = {
  pt: "Monte o carrinho escolhendo as variações e quantidades desejadas.",
  es: "Arma tu carrito seleccionando las variaciones y cantidades deseadas."
};
const defaultButton: LocalizedString = { pt: "Ir para checkout", es: "Ir al checkout" };
const defaultSharedBadge: LocalizedString = { pt: "Estoque compartilhado", es: "Inventario compartido" };
const defaultVariantBadge: LocalizedString = { pt: "Estoque individual", es: "Inventario individual" };
const title = computed(() => {
  const value = localize(props.section.title || defaultTitle);
  return value.trim() ? value : localize(defaultTitle);
});
const subtitle = computed(() => {
  const value = localize(props.section.subtitle || defaultSubtitle);
  return value.trim();
});
const checkoutButtonLabel = computed(() => {
  const value = localize((props.section as any).ctaLabel || defaultButton);
  return value.trim() ? value : localize(defaultButton);
});
const accentColor = computed(() => props.section.accentColor || "#059669");
const sharedBadgeOverride = computed(() => localize(props.section.sharedBadgeLabel || "").trim());
const variantBadgeOverride = computed(() => localize(props.section.variantBadgeLabel || "").trim());
const sharedBadgeText = computed(() => (sharedBadgeOverride.value.length ? sharedBadgeOverride.value : localize(defaultSharedBadge)));
const variantBadgeText = computed(() => (variantBadgeOverride.value.length ? variantBadgeOverride.value : localize(defaultVariantBadge)));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => textPalette.value.primary);
const mutedText = computed(() => textPalette.value.muted);

const clampSlots = (value?: number | null) => (typeof value === "number" && Number.isFinite(value) ? Math.max(0, value) : 0);
const unlimitedInventory = computed(
  () => !!product.value && (product.value.inventory_strategy === "unlimited" || product.value.allow_oversell)
);
const productAvailability = computed(() =>
  unlimitedInventory.value ? Number.MAX_SAFE_INTEGER : clampSlots(product.value?.available_slots)
);

const activeVariations = computed(() => {
  if (!product.value?.variations?.length) return [];
  return [...product.value.variations]
    .filter(variation => variation.status === "active")
    .sort((a, b) => {
      if (a.sort_order === b.sort_order) {
        return a.name.localeCompare(b.name);
      }
      return a.sort_order - b.sort_order;
    });
});

const productActive = computed(() => product.value?.status === "active");
const productStatusLabel = computed(() => {
  if (!product.value) return "Indefinido";
  switch (product.value.status) {
    case "active":
      return "Ativo";
    case "inactive":
      return "Inativo";
    case "draft":
      return "Rascunho";
    default:
      return product.value.status;
  }
});

const resetCart = () => {
  Object.keys(cart).forEach(key => delete cart[key]);
};

const fetchProduct = async () => {
  resetCart();
  if (!props.section.productId) {
    product.value = null;
    errorMessage.value = "Selecione um produto no painel financeiro para ativar esta seção.";
    return;
  }
  loading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicProductDetail(props.section.productId);
    product.value = data;
  } catch (err) {
    console.error("Erro ao carregar produto público", err);
    product.value = null;
    errorMessage.value = "Não foi possível carregar o produto. Tente novamente em instantes.";
  } finally {
    loading.value = false;
  }
};

onMounted(fetchProduct);
watch(
  () => props.section.productId,
  () => fetchProduct()
);

watch(
  () => activeVariations.value.map(variation => variation.public_id),
  () => {
    const ids = new Set(activeVariations.value.map(variation => variation.public_id));
    Object.keys(cart).forEach(key => {
      if (!ids.has(key)) {
        delete cart[key];
      }
    });
  }
);

const getQuantity = (variation: ProductVariation) => cart[variation.public_id] || 0;
const setQuantity = (variation: ProductVariation, quantity: number) => {
  const safeQuantity = Math.max(0, Math.floor(quantity));
  if (safeQuantity <= 0) {
    delete cart[variation.public_id];
  } else {
    const max = getMaxSelectable(variation);
    const next = max === Number.MAX_SAFE_INTEGER ? safeQuantity : Math.min(safeQuantity, max);
    if (next <= 0) {
      delete cart[variation.public_id];
    } else {
      cart[variation.public_id] = next;
    }
  }
};

const sharedSelectedCount = (excludeId?: string) =>
  activeVariations.value.reduce((sum, variation) => {
    if (variation.stock_mode === "shared" && variation.public_id !== excludeId) {
      return sum + getQuantity(variation);
    }
    return sum;
  }, 0);

const variationBaseAvailability = (variation: ProductVariation) => {
  if (typeof variation.available_slots === "number") {
    return clampSlots(variation.available_slots);
  }
  if (variation.stock_mode === "shared") {
    return productAvailability.value;
  }
  return clampSlots(variation.total_slots);
};

const getMaxSelectable = (variation: ProductVariation) => {
  if (!product.value) return 0;
  if (unlimitedInventory.value) return Number.MAX_SAFE_INTEGER;
  const base = variationBaseAvailability(variation);
  if (variation.stock_mode === "shared") {
    const remainingGlobal = Math.max(productAvailability.value - sharedSelectedCount(variation.public_id), 0);
    return Math.min(base || productAvailability.value, remainingGlobal);
  }
  return base;
};

const canIncrement = (variation: ProductVariation) => {
  if (!productActive.value) return false;
  const max = getMaxSelectable(variation);
  if (max === Number.MAX_SAFE_INTEGER) return true;
  return getQuantity(variation) < max;
};

const canDecrement = (variation: ProductVariation) => getQuantity(variation) > 0;

const increment = (variation: ProductVariation) => {
  if (!canIncrement(variation)) return;
  setQuantity(variation, getQuantity(variation) + 1);
};

const decrement = (variation: ProductVariation) => {
  if (!canDecrement(variation)) return;
  setQuantity(variation, getQuantity(variation) - 1);
};

const isOutOfStock = (variation: ProductVariation) => !unlimitedInventory.value && getMaxSelectable(variation) <= 0;
const lowStockThreshold = 5;
const isLowStock = (variation: ProductVariation) => {
  if (unlimitedInventory.value || isOutOfStock(variation)) return false;
  const available = variationBaseAvailability(variation);
  return available > 0 && available <= lowStockThreshold;
};

const variationAvailabilityText = (variation: ProductVariation) => {
  if (unlimitedInventory.value) return "Disponibilidade sob consulta";
  const available =
    typeof variation.available_slots === "number"
      ? clampSlots(variation.available_slots)
      : productAvailability.value;
  const reserved = clampSlots(variation.reserved_slots);
  const sold = clampSlots(variation.sold_slots);
  const parts = [`${available} vagas disponíveis`];
  if (reserved) parts.push(`${reserved} reservadas`);
  if (sold) parts.push(`${sold} confirmadas`);
  return parts.join(" · ");
};

const variationBadge = (variation: ProductVariation) => {
  if (variation.stock_mode === "shared") return sharedBadgeText.value;
  if (variation.stock_mode === "variant") return variantBadgeText.value;
  return "";
};

interface SelectedItem {
  variation: ProductVariation;
  quantity: number;
  lineTotal: number;
  peopleCount: number;
}

const selectedItems = computed<SelectedItem[]>(() =>
  activeVariations.value
    .map(variation => {
      const quantity = getQuantity(variation);
      if (!quantity) return null;
      return {
        variation,
        quantity,
        lineTotal: variation.price_cents * quantity,
        peopleCount: quantity * (variation.people_included || 1)
      };
    })
    .filter(Boolean) as SelectedItem[]
);

const cartTotalCents = computed(() => selectedItems.value.reduce((sum, item) => sum + item.lineTotal, 0));
const cartPassengers = computed(() =>
  selectedItems.value.reduce((sum, item) => sum + item.peopleCount, 0)
);
const cartCurrency = computed(() => {
  const selected = selectedItems.value[0];
  if (selected) return selected.variation.currency;
  const firstVariation = activeVariations.value[0];
  return firstVariation?.currency || "BRL";
});
const cartEmpty = computed(() => selectedItems.value.length === 0);

const tripDateLabel = computed(() => {
  const current = product.value;
  if (!current) return "Data a definir";
  if (current.trip_date) {
    try {
      return new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
      }).format(new Date(current.trip_date));
    } catch {
      return current.trip_date;
    }
  }
  return current.date_is_flexible ? "Data flexível" : "Data a definir";
});

const checkoutAvailable = computed(() => !!checkoutBridge);
const canCheckout = computed(() => checkoutAvailable.value && !cartEmpty.value && productActive.value);

const formatCurrency = (amountCents: number, currency = "BRL") => {
  const value = (amountCents || 0) / 100;
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value);
  } catch {
    return `R$ ${value.toFixed(2)}`;
  }
};

const clearCart = () => resetCart();

const handleCheckout = () => {
  if (!checkoutBridge || !product.value || cartEmpty.value) return;
  const payload: ProductCheckoutPayload = {
    productId: product.value.public_id,
    productName: product.value.name,
    productDescription: product.value.description,
    currency: cartCurrency.value,
    totalAmount: cartTotalCents.value,
    passengersRequired: cartPassengers.value,
    items: selectedItems.value.map(item => ({
      variationId: item.variation.public_id,
      name: item.variation.name,
      quantity: item.quantity,
      unitAmount: item.variation.price_cents,
      currency: item.variation.currency,
      peopleCount: item.peopleCount
    }))
  };
  checkoutBridge.startCheckout(payload);
};
</script>
