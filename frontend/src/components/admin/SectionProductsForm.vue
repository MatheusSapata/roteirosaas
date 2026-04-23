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

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-semibold text-slate-900">Produtos da seção</p>
          <p class="text-xs text-slate-500">1 produto mantém fluxo atual. 2+ ativa checkout multi-item.</p>
        </div>
        <button type="button" class="text-xs font-semibold text-slate-500" @click="loadProducts" :disabled="productsLoading">
          Atualizar
        </button>
      </div>
      <div
        v-if="productsLoading && !productOptions.length"
        class="rounded-xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500"
      >
        Carregando produtos...
      </div>
      <div
        v-else-if="productsError"
        class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-center text-sm text-rose-600"
      >
        {{ productsError }}
      </div>
      <div v-else-if="!productOptions.length" class="rounded-xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500">
        Nenhum produto encontrado.
      </div>
      <div v-else class="space-y-2">
        <p v-if="productsLoading" class="text-xs text-slate-500">Atualizando lista...</p>
        <label
          v-for="productOption in productOptions"
          :key="productOption.public_id"
          class="flex items-center justify-between gap-3 rounded-2xl border p-3"
          :class="selectedIds.includes(productOption.public_id) ? 'border-emerald-400 bg-emerald-50/40' : 'border-slate-200 bg-white'"
        >
          <div>
            <p class="text-sm font-semibold text-slate-900">{{ productOption.name }}</p>
            <p class="text-xs text-slate-500">Ativo: {{ productOption.status === "active" ? "sim" : "não" }}</p>
          </div>
          <input type="checkbox" class="h-4 w-4" :checked="selectedIds.includes(productOption.public_id)" @change="toggleProduct(productOption.public_id)" />
        </label>
      </div>

      <div v-if="selectedProducts.length" class="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Ordem exibida</p>
        <div v-for="(productId, index) in selectedProducts" :key="`${productId}-${index}`" class="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-sm">
          <span>{{ resolveProductName(productId) }}</span>
          <div class="flex gap-1">
            <button type="button" class="pill" :disabled="index === 0" @click="move(index, -1)">↑</button>
            <button type="button" class="pill" :disabled="index === selectedProducts.length - 1" @click="move(index, 1)">↓</button>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
      <p class="text-sm font-semibold text-slate-900">Taxa do checkout</p>
      <select v-model="local.feeMode" class="input">
        <option value="absorb">Assumir taxa (mostrar so o valor base)</option>
        <option value="pass_through">Repassar taxa (subtotal + taxa + total)</option>
      </select>
      <div class="grid gap-2 md:grid-cols-2">
        <label class="space-y-1">
          <span class="input-label">Parcelas maximas no cartao</span>
          <input v-model.number="local.installments" type="number" min="1" max="12" class="input" />
        </label>
        <label class="space-y-1">
          <span class="input-label">Modo de juros no cartao</span>
          <select v-model="local.interestMode" class="input" :disabled="local.feeMode === 'pass_through'">
            <option value="merchant">Assumir juros em todas as parcelas</option>
            <option value="customer">Repassar juros ao cliente</option>
          </select>
        </label>
      </div>
      <label v-if="local.feeMode === 'absorb' && local.interestMode === 'customer'" class="space-y-1">
        <span class="input-label">Assumir juros ate parcela (opcional)</span>
        <input
          :value="maxNoInterestInput"
          type="text"
          inputmode="numeric"
          class="input"
          placeholder="Ex.: 4"
          @input="onMaxNoInterestInput"
        />
        <p class="text-xs text-slate-500">
          Ate esta parcela fica sem juros; acima dela o valor vem com juros.
        </p>
      </label>
    </div>

    <div class="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
      <p class="text-sm font-semibold text-slate-900">Desconto da seção</p>
      <div class="grid gap-2 md:grid-cols-2">
        <select v-model="discount.ruleType" class="input">
          <option :value="null">Sem regra</option>
          <option value="min_quantity">Quantidade mínima</option>
          <option value="exact_combination">Combinação específica</option>
        </select>
        <select v-model="discount.discountType" class="input">
          <option :value="null">Sem desconto</option>
          <option value="percentage">Percentual (0-100)</option>
          <option value="fixed">Fixo (cents)</option>
        </select>
      </div>
      <div class="grid gap-2 md:grid-cols-2">
        <input v-model.number="discount.minSelectedProducts" type="number" min="1" class="input" placeholder="Mínimo de produtos" />
        <input v-model.number="discount.discountValue" type="number" min="0" class="input" placeholder="Valor do desconto" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import SectionHeadingControls from "./inputs/SectionHeadingControls.vue";
import { listProducts } from "../../services/finance";
import type { ProductSummary } from "../../types/finance";
import type { ProductsSection } from "../../types/page";

const defaultTitle = "Pacotes disponíveis";
const defaultSubtitle = "Escolha os pacotes ideais para sua viagem";
const defaultCtaLabel = "Ir para checkout";

const props = defineProps<{ modelValue: ProductsSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ProductsSection): void }>();

const productOptions = ref<ProductSummary[]>([]);
const productsLoading = ref(false);
const productsError = ref<string | null>(null);
const lastEmittedSnapshot = ref("");

const normalizeProductIds = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value
    .map(item => String(item || "").trim())
    .filter(item => item.length > 0);
};

const toStringOrNull = (value: unknown): string | null => {
  const parsed = typeof value === "string" ? value.trim() : "";
  return parsed.length ? parsed : null;
};

const normalizeInstallments = (value: unknown): number => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 12;
  return Math.max(1, Math.min(Math.trunc(parsed), 12));
};

const normalizeMaxNoInterest = (value: unknown): number | null => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return null;
  return Math.max(1, Math.min(Math.trunc(parsed), 12));
};

const resolveSectionMaxNoInterest = (
  value: unknown,
  feeMode: ProductsSection["feeMode"],
  interestMode: ProductsSection["interestMode"],
): number | null => {
  if (feeMode !== "absorb") return null;
  if (interestMode !== "customer") return null;
  return normalizeMaxNoInterest(value);
};

const local = reactive<ProductsSection>({
  ...props.modelValue,
  productId: toStringOrNull(props.modelValue.productId),
  productIds: normalizeProductIds(props.modelValue.productIds).length
    ? normalizeProductIds(props.modelValue.productIds)
    : toStringOrNull(props.modelValue.productId)
      ? [String(props.modelValue.productId).trim()]
      : [],
  title: props.modelValue.title ?? defaultTitle,
  subtitle: props.modelValue.subtitle ?? defaultSubtitle,
  ctaLabel: props.modelValue.ctaLabel ?? defaultCtaLabel,
  accentColor: props.modelValue.accentColor ?? "#059669",
  feeMode: props.modelValue.feeMode === "pass_through" ? "pass_through" : "absorb",
  installments: normalizeInstallments(props.modelValue.installments),
  interestMode: props.modelValue.interestMode === "customer" ? "customer" : "merchant",
  maxInstallmentsNoInterest: resolveSectionMaxNoInterest(
    props.modelValue.maxInstallmentsNoInterest,
    props.modelValue.feeMode === "pass_through" ? "pass_through" : "absorb",
    props.modelValue.interestMode === "customer" ? "customer" : "merchant",
  ),
  discount: props.modelValue.discount ?? null,
});
const maxNoInterestInput = ref(local.maxInstallmentsNoInterest != null ? String(local.maxInstallmentsNoInterest) : "");

const discount = reactive({
  ruleType: local.discount?.ruleType ?? null,
  minSelectedProducts: local.discount?.minSelectedProducts ?? 2,
  requiredProductIds: local.discount?.requiredProductIds ?? [],
  discountType: local.discount?.discountType ?? null,
  discountValue: local.discount?.discountValue ?? 0,
});

const selectedProducts = computed({
  get: () => (Array.isArray(local.productIds) ? (local.productIds as string[]) : []),
  set: value => {
    const normalized = normalizeProductIds(value);
    local.productIds = [...normalized];
    local.productId = normalized[0] || null;
  },
});

const selectedIds = computed(() => selectedProducts.value);

const paymentMethodsMap = computed(() => {
  const map = new Map<string, string[]>();
  for (const option of productOptions.value) {
    const raw = Array.isArray((option as any).allowed_payment_methods)
      ? ((option as any).allowed_payment_methods as string[])
      : ["pix", "credit_card", "boleto"];
    const normalized = Array.from(
      new Set(
        raw
          .map(item => String(item || "").trim().toLowerCase())
          .filter(item => item === "pix" || item === "credit_card" || item === "boleto"),
      ),
    );
    map.set(option.public_id, normalized.length ? normalized : ["pix", "credit_card", "boleto"]);
  }
  return map;
});

const methodsSignature = (methods: string[]) => [...methods].sort().join("|");

const toggleProduct = (productId: string) => {
  if (selectedProducts.value.includes(productId)) {
    selectedProducts.value = selectedProducts.value.filter(item => item !== productId);
  } else {
    const baselineId = selectedProducts.value[0];
    if (baselineId) {
      const baselineMethods = paymentMethodsMap.value.get(baselineId) || ["pix", "credit_card", "boleto"];
      const candidateMethods = paymentMethodsMap.value.get(productId) || ["pix", "credit_card", "boleto"];
      if (methodsSignature(baselineMethods) !== methodsSignature(candidateMethods)) {
        productsError.value =
          "Este produto nao pode ser combinado com os ja selecionados porque possui formas de pagamento diferentes.";
        return;
      }
    }
    selectedProducts.value = [...selectedProducts.value, productId];
    productsError.value = null;
  }
};

const move = (index: number, direction: number) => {
  const target = index + direction;
  if (target < 0 || target >= selectedProducts.value.length) return;
  const next = [...selectedProducts.value];
  const temp = next[index];
  next[index] = next[target];
  next[target] = temp;
  selectedProducts.value = next;
};

const resolveProductName = (productId: string) => productOptions.value.find(item => item.public_id === productId)?.name || productId;
const onMaxNoInterestInput = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const digits = String(input.value || "").replace(/\D/g, "").slice(0, 2);
  maxNoInterestInput.value = digits;
  if (!digits) {
    local.maxInstallmentsNoInterest = null;
    return;
  }
  local.maxInstallmentsNoInterest = Number(digits);
};

const loadProducts = async () => {
  productsLoading.value = true;
  productsError.value = null;
  try {
    const { data } = await listProducts();
    const payload = data as any;
    const rawItems = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.items)
        ? payload.items
        : Array.isArray(payload?.data?.items)
          ? payload.data.items
          : [];
    const items = rawItems
      .filter((item: any) => item && typeof item === "object")
      .filter((item: any) => typeof item.public_id === "string" && item.public_id.trim() && typeof item.name === "string" && item.name.trim());
    productOptions.value = items;
    if (!selectedProducts.value.length && productOptions.value.length) {
      selectedProducts.value = [productOptions.value[0].public_id];
    }
  } catch (err) {
    console.error("Erro ao carregar produtos", err);
    productOptions.value = [];
    productsError.value = "Não foi possível carregar os produtos agora.";
  } finally {
    productsLoading.value = false;
  }
};

const buildSectionPayload = (): ProductsSection => ({
  ...(local as ProductsSection),
  productId: selectedProducts.value[0] || null,
  productIds: [...selectedProducts.value],
  feeMode: local.feeMode === "pass_through" ? "pass_through" : "absorb",
  installments: normalizeInstallments(local.installments),
  interestMode: local.feeMode === "pass_through" ? "customer" : (local.interestMode === "customer" ? "customer" : "merchant"),
  maxInstallmentsNoInterest:
    local.feeMode === "absorb" && local.interestMode === "customer"
      ? normalizeMaxNoInterest(local.maxInstallmentsNoInterest)
      : null,
  discount: discount.ruleType && discount.discountType
    ? {
        ruleType: discount.ruleType,
        minSelectedProducts: Math.max(1, Number(discount.minSelectedProducts || 1)),
        requiredProductIds: [...(discount.requiredProductIds || [])],
        discountType: discount.discountType,
        discountValue: Math.max(0, Number(discount.discountValue || 0)),
      }
    : null,
});

watch(
  () => props.modelValue,
  value => {
    Object.assign(local, value);
    const normalizedIds = normalizeProductIds(value.productIds);
    const fallbackId = toStringOrNull(value.productId);
    local.productIds = normalizedIds.length ? [...normalizedIds] : fallbackId ? [fallbackId] : [];
    local.productId = local.productIds[0] || fallbackId || null;
    local.title = value.title ?? defaultTitle;
    local.subtitle = value.subtitle ?? defaultSubtitle;
    local.ctaLabel = value.ctaLabel ?? defaultCtaLabel;
    local.accentColor = value.accentColor ?? "#059669";
    local.feeMode = value.feeMode === "pass_through" ? "pass_through" : "absorb";
    local.installments = normalizeInstallments(value.installments);
    local.interestMode = value.interestMode === "customer" ? "customer" : "merchant";
    local.maxInstallmentsNoInterest = resolveSectionMaxNoInterest(
      value.maxInstallmentsNoInterest,
      local.feeMode,
      local.interestMode,
    );
    maxNoInterestInput.value = local.maxInstallmentsNoInterest != null ? String(local.maxInstallmentsNoInterest) : "";
    discount.ruleType = value.discount?.ruleType ?? null;
    discount.minSelectedProducts = value.discount?.minSelectedProducts ?? 2;
    discount.requiredProductIds = value.discount?.requiredProductIds ?? [];
    discount.discountType = value.discount?.discountType ?? null;
    discount.discountValue = value.discount?.discountValue ?? 0;
    lastEmittedSnapshot.value = JSON.stringify(buildSectionPayload());
  },
  { deep: true },
);

watch(
  () => ({ ...local, productIds: selectedProducts.value, discount: { ...discount, requiredProductIds: [...(discount.requiredProductIds || [])] } }),
  () => {
    const payload = buildSectionPayload();
    const snapshot = JSON.stringify(payload);
    if (snapshot === lastEmittedSnapshot.value) return;
    lastEmittedSnapshot.value = snapshot;
    emit("update:modelValue", payload);
  },
  { deep: true },
);

onMounted(loadProducts);
</script>

<style scoped>
.input {
  @apply w-full rounded-xl border border-slate-200 px-3 py-2 text-sm;
}
.input-label {
  @apply text-xs font-semibold uppercase tracking-wide text-slate-500;
}
.pill {
  @apply rounded-lg border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-600;
}
</style>
