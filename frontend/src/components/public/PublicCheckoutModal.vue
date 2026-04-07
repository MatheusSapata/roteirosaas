<template>
  <teleport to="body">
    <transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="w-full max-w-3xl rounded-3xl bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Checkout seguro</p>
              <h2 class="text-2xl font-bold text-slate-900">{{ checkoutData?.productName || "Selecione os pacotes" }}</h2>
              <p class="text-sm text-slate-500" v-if="hasCart">
                {{ formatCurrency(checkoutData?.totalAmount || 0, checkoutData?.currency || "BRL") }}
                <span v-if="passengersCount > 0" class="text-slate-400">
                  • {{ passengersCount }} {{ passengersCount === 1 ? "passageiro" : "passageiros" }}
                </span>
              </p>
            </div>
            <button type="button" class="rounded-full p-2 text-slate-500 transition hover:bg-slate-100" @click="handleClose">
              <span class="sr-only">Fechar</span>
              ×
            </button>
          </div>

          <div
            v-if="!hasCart"
            class="mt-6 rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500"
          >
            Monte seu carrinho na seção de produtos para continuar.
          </div>

          <form v-else-if="hasCart && !saleResult" class="mt-6 space-y-4" @submit.prevent="submitCustomerDetails">
            <div class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-slate-700">Resumo da compra</p>
                <p class="text-xs text-slate-500">Atualiza em tempo real</p>
              </div>
              <ul class="mt-3 space-y-2">
                <li v-for="item in cartItems" :key="item.variationId" class="flex items-center justify-between text-sm text-slate-700">
                  <div>
                    <p class="font-semibold text-slate-900">{{ item.quantity }}x {{ item.name }}</p>
                    <p class="text-xs text-slate-500">
                      Inclui {{ item.peopleCount * item.quantity }}
                      {{ item.peopleCount * item.quantity === 1 ? "passageiro" : "passageiros" }}
                    </p>
                  </div>
                  <p class="font-semibold text-slate-900">
                    {{ formatCurrency(item.unitAmount * item.quantity, item.currency) }}
                  </p>
                </li>
              </ul>
              <div class="mt-3 flex items-center justify-between border-t border-slate-200 pt-3 text-sm font-semibold text-slate-900">
                <span>Total</span>
                <span>{{ formatCurrency(checkoutData?.totalAmount || 0, checkoutData?.currency || "BRL") }}</span>
              </div>
              <p class="mt-1 text-xs text-slate-500" v-if="passengersCount > 0">
                Após o pagamento coletaremos os dados de {{ passengersCount }}
                {{ passengersCount === 1 ? "passageiro" : "passageiros" }}.
              </p>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <div class="md:col-span-2">
                <label class="mb-1 block text-sm font-semibold text-slate-600">Nome completo</label>
                <input
                  v-model="customer.name"
                  type="text"
                  required
                  class="w-full rounded-xl border border-slate-200 px-4 py-3"
                  placeholder="Nome do comprador"
                />
              </div>
              <div>
                <label class="mb-1 block text-sm font-semibold text-slate-600">E-mail</label>
                <input
                  v-model="customer.email"
                  type="email"
                  required
                  class="w-full rounded-xl border border-slate-200 px-4 py-3"
                  placeholder="seu@email.com"
                />
              </div>
              <div>
                <label class="mb-1 block text-sm font-semibold text-slate-600">Telefone / WhatsApp</label>
                <input
                  v-model="customer.phone"
                  type="tel"
                  required
                  class="w-full rounded-xl border border-slate-200 px-4 py-3"
                  placeholder="(11) 99999-0000"
                />
              </div>
            </div>

            <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
              <p>Após o pagamento solicitaremos os dados dos passageiros de forma segura.</p>
            </div>

            <div class="flex flex-wrap items-center gap-4">
              <button
                type="submit"
                class="btn-primary"
                :disabled="loading || !isFormValid"
              >
                {{ loading ? "Processando..." : "Avançar para pagamento" }}
              </button>
              <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
            </div>
          </form>

          <div v-else-if="hasCart && saleResult" class="mt-6 space-y-4">
            <div class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-slate-700">Pagamento simulador</p>
                <span class="text-xs uppercase text-slate-500">Ref {{ saleResult.checkout_reference }}</span>
              </div>
              <dl class="mt-3 space-y-2 text-sm">
                <div class="flex items-center justify-between">
                  <dt class="text-slate-500">Valor base</dt>
                  <dd class="font-semibold text-slate-900">
                    {{ formatCurrency(saleResult.breakdown.base_amount_cents, saleResult.breakdown.currency) }}
                  </dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-slate-500">Margem plataforma</dt>
                  <dd class="font-semibold text-slate-900">
                    {{ formatCurrency(saleResult.breakdown.platform_fee_amount_cents, saleResult.breakdown.currency) }}
                  </dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-slate-500">Taxa gateway estimada</dt>
                  <dd class="font-semibold text-slate-900">
                    {{ formatCurrency(saleResult.breakdown.gateway_fee_estimated_cents, saleResult.breakdown.currency) }}
                  </dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-slate-500">Total pago</dt>
                  <dd class="font-semibold text-slate-900">
                    {{ formatCurrency(saleResult.breakdown.gross_amount_cents, saleResult.breakdown.currency) }}
                  </dd>
                </div>
                <div class="flex items-center justify-between">
                  <dt class="text-slate-500">Repasse agência</dt>
                  <dd class="font-semibold text-slate-900">
                    {{ formatCurrency(saleResult.breakdown.agency_net_amount_cents, saleResult.breakdown.currency) }}
                  </dd>
                </div>
              </dl>
              <p class="mt-3 text-xs text-slate-500">
                Provedor: {{ saleResult.provider }} • Status: {{ saleResult.provider_status }}
              </p>
            </div>

            <div class="rounded-2xl border border-slate-100 p-4">
              <label class="mb-1 block text-sm font-semibold text-slate-600">Método de pagamento</label>
              <select v-model="paymentMethod" class="w-full rounded-xl border border-slate-200 px-4 py-3">
                <option value="credit_card">Cartão de crédito</option>
                <option value="pix">Pix</option>
                <option value="boleto">Boleto</option>
              </select>
              <p class="mt-2 text-sm text-slate-600">
                {{ saleResult.breakdown.installments }}x de
                {{ formatCurrency(saleResult.breakdown.installment_amount_cents, saleResult.breakdown.currency) }}.
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <button type="button" class="pill" :disabled="confirming" @click="saleResult = null">Editar dados</button>
              <button type="button" class="btn-primary" :disabled="confirming" @click="confirmPayment">
                {{ confirming ? "Confirmando..." : "Confirmar pagamento simulado" }}
              </button>
              <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { confirmPublicSale, createProductPublicCheckoutIntent } from "../../services/finance";
import type { ProductCheckoutRequest, PublicCheckoutResponse } from "../../types/finance";
import type { ProductCheckoutPayload } from "../../utils/checkoutKeys";

const props = defineProps<{
  modelValue: boolean;
  pageId: number | null;
  pageSlug?: string | null;
  agencySlug?: string | null;
  pageUrl?: string | null;
  checkoutData: ProductCheckoutPayload | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "payment-succeeded", payload: { passengerToken: string; saleId: number }): void;
}>();

const visible = computed(() => props.modelValue);
const customer = ref({ name: "", email: "", phone: "" });
const saleResult = ref<PublicCheckoutResponse | null>(null);
const paymentMethod = ref("credit_card");
const loading = ref(false);
const confirming = ref(false);
const errorMessage = ref<string | null>(null);

const cartItems = computed(() => props.checkoutData?.items ?? []);
const hasCart = computed(() => cartItems.value.length > 0);
const passengersCount = computed(() => props.checkoutData?.passengersRequired || 0);

const resetState = () => {
  customer.value = { name: "", email: "", phone: "" };
  saleResult.value = null;
  paymentMethod.value = "credit_card";
  errorMessage.value = null;
};

const handleClose = () => {
  emit("update:modelValue", false);
  resetState();
};

const isFormValid = computed(
  () => !!customer.value.name.trim() && !!customer.value.email.trim() && !!customer.value.phone.trim(),
);

const formatCurrency = (amountCents: number, currency = "BRL") => {
  const value = (amountCents || 0) / 100;
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value);
  } catch {
    return `R$ ${value.toFixed(2)}`;
  }
};

const submitCustomerDetails = async () => {
  if (!props.checkoutData || !props.pageId || !hasCart.value) {
    errorMessage.value = "Selecione os pacotes para continuar.";
    return;
  }
  loading.value = true;
  errorMessage.value = null;
  const payload: ProductCheckoutRequest = {
    product_id: props.checkoutData.productId,
    items: cartItems.value.map(item => ({
      variation_id: item.variationId,
      quantity: item.quantity,
    })),
    customer: {
      name: customer.value.name.trim(),
      email: customer.value.email.trim(),
      phone: customer.value.phone.trim(),
    },
    page_id: props.pageId,
    page_slug: props.pageSlug ?? undefined,
    agency_slug: props.agencySlug ?? undefined,
    source_url: props.pageUrl ?? (typeof window !== "undefined" ? window.location.href : undefined),
    channel: "public_page",
  };
  try {
    const { data } = await createProductPublicCheckoutIntent(payload);
    saleResult.value = data;
    paymentMethod.value = data.breakdown.payment_method || "credit_card";
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível iniciar o checkout.";
  } finally {
    loading.value = false;
  }
};

const confirmPayment = async () => {
  if (!saleResult.value) return;
  confirming.value = true;
  errorMessage.value = null;
  try {
    const { data } = await confirmPublicSale(saleResult.value.sale_id, {
      payment_method: paymentMethod.value,
      installments: saleResult.value.breakdown.installments,
    });
    saleResult.value = data;
    emit("payment-succeeded", {
      passengerToken: data.passenger_token,
      saleId: data.sale_id,
    });
    emit("update:modelValue", false);
    resetState();
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || err?.message || "Não foi possível confirmar o pagamento.";
  } finally {
    confirming.value = false;
  }
};

watch(
  () => props.modelValue,
  value => {
    if (!value) {
      resetState();
    }
  },
);

watch(
  () => props.checkoutData,
  value => {
    if (!value) {
      resetState();
    }
  },
);
</script>
