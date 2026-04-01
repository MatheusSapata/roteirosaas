<template>
  <teleport to="body">
    <transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="w-full max-w-3xl rounded-3xl bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Checkout seguro</p>
              <h2 class="text-2xl font-bold text-slate-900">{{ product?.title }}</h2>
              <p class="text-sm text-slate-500" v-if="product">
                {{ formatCurrency(product.price, product.currency) }}
                <span v-if="product.passengersRequired > 0" class="text-slate-400">
                  • {{ product.passengersRequired }} passageiros
                </span>
              </p>
            </div>
            <button
              type="button"
              class="rounded-full p-2 text-slate-500 transition hover:bg-slate-100"
              @click="handleClose"
            >
              <span class="sr-only">Fechar</span>
              ✕
            </button>
          </div>

          <div v-if="!product" class="mt-6 rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
            Selecione um plano para continuar.
          </div>

          <form v-else-if="!clientSecret" class="mt-6 space-y-4" @submit.prevent="submitCustomerDetails">
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
              <p>
                Após o pagamento iremos solicitar os dados dos passageiros de forma segura. Nenhum dado de cartão é
                armazenado na plataforma.
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-4">
              <button
                type="submit"
                class="rounded-full bg-emerald-500 px-6 py-3 font-semibold text-white shadow-lg shadow-emerald-500/40 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
                :disabled="loading || !isFormValid"
              >
                {{ loading ? "Preparando..." : "Ir para pagamento" }}
              </button>
              <span class="text-xs text-slate-500">Processado por Stripe</span>
            </div>
            <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
          </form>

          <div v-else class="mt-6 space-y-4">
            <div class="rounded-2xl border border-slate-200 p-4">
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-slate-700">Pagamento</p>
                <p class="text-xs text-slate-500">Stripe Payment Element</p>
              </div>
              <div ref="paymentElementRef" class="mt-4"></div>
            </div>
            <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
            <button
              type="button"
              class="w-full rounded-full bg-emerald-500 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/40 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
              :disabled="loading"
              @click="confirmPayment"
            >
              {{ loading ? "Processando..." : "Confirmar pagamento" }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { loadStripe, type Stripe, type StripeElements, type StripePaymentElement } from "@stripe/stripe-js";
import { createPublicCheckoutIntent } from "../../services/finance";
import type { CheckoutIntentRequest } from "../../types/finance";

interface CheckoutProduct {
  productId: string;
  title: string;
  price: number;
  currency?: string;
  passengersRequired: number;
}

const props = defineProps<{
  modelValue: boolean;
  pageId: number | null;
  pageSlug?: string | null;
  agencySlug?: string | null;
  pageUrl?: string | null;
  product: CheckoutProduct | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "payment-succeeded", payload: { passengerToken: string; saleId: number }): void;
}>();

const visible = computed(() => props.modelValue);
const customer = ref({ name: "", email: "", phone: "" });
const loading = ref(false);
const errorMessage = ref<string | null>(null);
const clientSecret = ref<string | null>(null);
const passengerToken = ref<string | null>(null);
const saleId = ref<number | null>(null);
const paymentElementRef = ref<HTMLDivElement | null>(null);

const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "";
const stripePromise = publishableKey ? loadStripe(publishableKey) : null;
let stripeInstance: Stripe | null = null;
let stripeElements: StripeElements | null = null;
let paymentElement: StripePaymentElement | null = null;

const resetState = () => {
  customer.value = { name: "", email: "", phone: "" };
  clientSecret.value = null;
  passengerToken.value = null;
  saleId.value = null;
  errorMessage.value = null;
  destroyPaymentElement();
};

const handleClose = () => {
  emit("update:modelValue", false);
};

const isFormValid = computed(
  () => !!customer.value.name.trim() && !!customer.value.email.trim() && !!customer.value.phone.trim()
);

const formatCurrency = (price: number, currency = "BRL") => {
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(price);
  } catch {
    return `R$ ${price.toFixed(2)}`;
  }
};

const submitCustomerDetails = async () => {
  if (!props.product || !props.pageId) return;
  if (!publishableKey) {
    errorMessage.value = "Stripe não configurado.";
    return;
  }
  loading.value = true;
  errorMessage.value = null;
  const payload: CheckoutIntentRequest = {
    page_id: props.pageId,
    product_id: props.product.productId,
    page_slug: props.pageSlug ?? undefined,
    agency_slug: props.agencySlug ?? undefined,
    source_url: props.pageUrl ?? (typeof window !== "undefined" ? window.location.href : undefined),
    customer: {
      name: customer.value.name.trim(),
      email: customer.value.email.trim(),
      phone: customer.value.phone.trim()
    }
  };
  try {
    const { data } = await createPublicCheckoutIntent(payload);
    clientSecret.value = data.client_secret;
    passengerToken.value = data.passenger_token;
    saleId.value = data.sale_id;
    await nextTick();
    await mountPaymentElement();
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível iniciar o checkout.";
  } finally {
    loading.value = false;
  }
};

const mountPaymentElement = async () => {
  if (!stripePromise || !clientSecret.value) {
    throw new Error("Stripe não configurado.");
  }
  stripeInstance = await stripePromise;
  if (!stripeInstance) throw new Error("Stripe indisponível.");
  stripeElements = stripeInstance.elements({ clientSecret: clientSecret.value });
  paymentElement = stripeElements.create("payment");
  if (paymentElementRef.value) {
    paymentElement.mount(paymentElementRef.value);
  }
};

const destroyPaymentElement = () => {
  if (paymentElement) {
    paymentElement.destroy();
    paymentElement = null;
  }
  stripeElements = null;
};

const confirmPayment = async () => {
  if (!stripeInstance || !stripeElements || !clientSecret.value) return;
  loading.value = true;
  errorMessage.value = null;
  try {
    const { error, paymentIntent } = await stripeInstance.confirmPayment({
      elements: stripeElements,
      redirect: "if_required"
    });
    if (error) {
      errorMessage.value = error.message || "Não foi possível confirmar o pagamento.";
      return;
    }
    if (paymentIntent && paymentIntent.status === "succeeded" && passengerToken.value && saleId.value) {
      emit("payment-succeeded", {
        passengerToken: passengerToken.value,
        saleId: saleId.value
      });
      emit("update:modelValue", false);
      resetState();
    }
  } catch (err: any) {
    errorMessage.value = err?.message || "Erro ao confirmar pagamento.";
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.modelValue,
  value => {
    if (!value) {
      resetState();
    }
  }
);

onMounted(() => {
  if (!publishableKey) {
    console.warn("STRIPE_PUBLISHABLE_KEY não configurada.");
  }
});
</script>
