<template>
  <div class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
    <SectionHeadingControls v-model:label="local.headingLabel" v-model:style="local.headingLabelStyle" />

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="input-label">Título</label>
        <input v-model="local.title" class="input" :placeholder="defaultTitle" />
      </div>
      <div>
        <label class="input-label">Subtítulo</label>
        <input v-model="local.subtitle" class="input" :placeholder="defaultSubtitle" />
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="input-label">Texto do botão</label>
        <input v-model="local.ctaLabel" class="input" :placeholder="defaultCtaLabel" />
      </div>
      <div>
        <label class="input-label">Cor de destaque</label>
        <input v-model="local.accentColor" type="color" class="input h-11 cursor-pointer" />
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <div>
        <label class="input-label">Etiqueta — estoque compartilhado</label>
        <input v-model="local.sharedBadgeLabel" class="input" :placeholder="defaultSharedBadge" />
      </div>
      <div>
        <label class="input-label">Etiqueta — estoque individual</label>
        <input v-model="local.variantBadgeLabel" class="input" :placeholder="defaultVariantBadge" />
      </div>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-semibold text-slate-900">Produto vinculado</p>
          <p class="text-xs text-slate-500">Selecione qual viagem/pacote será exibido no site.</p>
        </div>
        <button
          type="button"
          class="text-xs font-semibold text-slate-500"
          @click="loadProducts"
          :disabled="productsLoading"
        >
          Atualizar
        </button>
      </div>
      <div
        v-if="productsLoading"
        class="rounded-xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500"
      >
        Carregando produtos...
      </div>
      <div
        v-else-if="!productOptions.length"
        class="rounded-xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500"
      >
        Nenhum produto encontrado. Cadastre produtos em Financeiro &gt; Produtos para habilitar esta seção.
      </div>
      <div v-else class="space-y-3">
        <label
          v-for="productOption in productOptions"
          :key="productOption.public_id"
          class="flex cursor-pointer flex-col gap-2 rounded-2xl border p-3 transition hover:border-emerald-400"
          :class="local.productId === productOption.public_id ? 'border-emerald-400 bg-emerald-50/40' : 'border-slate-200 bg-white'"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-semibold text-slate-900">{{ productOption.name }}</p>
              <p v-if="productOption.description" class="text-xs text-slate-500">{{ productOption.description }}</p>
              <p class="text-xs text-slate-500">
                Estoque: {{ productOption.available_slots }} / {{ productOption.total_slots }}
              </p>
            </div>
            <input
              type="radio"
              class="h-4 w-4"
              name="product-selection"
              :value="productOption.public_id"
              v-model="local.productId"
            />
          </div>
          <div class="space-y-1 rounded-xl bg-white/70 p-2 text-xs text-slate-600">
            <p class="font-semibold text-slate-900">
              Pacotes ativos ({{ productOption.variations.filter(variation => variation.status === "active").length }})
            </p>
            <p
              v-for="variation in productOption.variations.filter(variation => variation.status === 'active').slice(0, 2)"
              :key="variation.public_id"
            >
              • {{ variation.name }} — {{ formatCurrency(variation.price_cents) }}
            </p>
            <p v-if="productOption.variations.filter(variation => variation.status === 'active').length === 0">
              Nenhum pacote ativo.
            </p>
          </div>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { listProducts } from "../../services/finance";
import type { ProductsSection } from "../../types/page";
import type { ProductSummary } from "../../types/finance";

const defaultTitle = "Pacotes disponíveis";
const defaultSubtitle = "Escolha os pacotes ideais para sua viagem";
const defaultCtaLabel = "Ir para checkout";
const defaultSharedBadge = "Estoque compartilhado";
const defaultVariantBadge = "Estoque individual";
const defaultAccent = "#059669";

const props = defineProps<{ modelValue: ProductsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ProductsSection): void }>();

const productOptions = ref<ProductSummary[]>([]);
const productsLoading = ref(false);

const local = reactive<ProductsSection>({
  ...props.modelValue,
  productId: props.modelValue.productId ?? null,
  title: props.modelValue.title ?? defaultTitle,
  subtitle: props.modelValue.subtitle ?? defaultSubtitle,
  ctaLabel: props.modelValue.ctaLabel ?? defaultCtaLabel,
  accentColor: props.modelValue.accentColor ?? defaultAccent,
  sharedBadgeLabel: props.modelValue.sharedBadgeLabel ?? defaultSharedBadge,
  variantBadgeLabel: props.modelValue.variantBadgeLabel ?? defaultVariantBadge
});

const formatCurrency = (value?: number | null) => {
  const amount = typeof value === "number" ? value : 0;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(amount / 100);
};

const loadProducts = async () => {
  productsLoading.value = true;
  try {
    const { data } = await listProducts();
    productOptions.value = data.items || [];
    if (!local.productId && productOptions.value.length) {
      local.productId = productOptions.value[0].public_id;
    }
  } catch (err) {
    console.error("Erro ao carregar produtos", err);
    productOptions.value = [];
  } finally {
    productsLoading.value = false;
  }
};

watch(
  () => props.modelValue,
  value => {
    Object.assign(local, value);
    local.productId = value.productId ?? null;
    local.title = value.title ?? defaultTitle;
    local.subtitle = value.subtitle ?? defaultSubtitle;
    local.ctaLabel = value.ctaLabel ?? defaultCtaLabel;
    local.accentColor = value.accentColor ?? defaultAccent;
    local.sharedBadgeLabel = value.sharedBadgeLabel ?? defaultSharedBadge;
    local.variantBadgeLabel = value.variantBadgeLabel ?? defaultVariantBadge;
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    emit("update:modelValue", value as ProductsSection);
  },
  { deep: true }
);

onMounted(() => {
  loadProducts();
});
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none;
}
.input-label {
  @apply text-xs font-semibold uppercase tracking-wide text-slate-500;
}
</style>
