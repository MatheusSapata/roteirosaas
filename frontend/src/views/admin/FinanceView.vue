<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm font-semibold"
        :class="activeTab === 'config' ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-600'"
        @click="activeTab = 'config'"
      >
        Configurações
      </button>
      <button
        type="button"
        class="rounded-full px-4 py-2 text-sm font-semibold"
        :class="activeTab === 'sales' ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-600'"
        @click="activeTab = 'sales'"
      >
        Vendas
      </button>
    </div>

    <div v-if="activeTab === 'config'" class="grid gap-4 md:grid-cols-2">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow">
        <h3 class="text-lg font-semibold text-slate-900">Conta Stripe</h3>
        <p class="mt-1 text-sm text-slate-500">
          Conecte sua conta para receber pagamentos diretamente nas suas páginas.
        </p>
        <div class="mt-4 space-y-2 text-sm">
          <p>
            <span class="font-semibold text-slate-600">Status:</span>
            <span :class="accountStatus?.connected ? 'text-emerald-600' : 'text-rose-500'">
              {{ accountStatus?.connected ? "Conectado" : "Não conectado" }}
            </span>
          </p>
          <p><span class="font-semibold text-slate-600">E-mail:</span> {{ accountStatus?.email || "-" }}</p>
          <p>
            <span class="font-semibold text-slate-600">Cobranças:</span>
            <span :class="accountStatus?.charges_enabled ? 'text-emerald-600' : 'text-rose-500'">
              {{ accountStatus?.charges_enabled ? "Liberadas" : "Pendentes" }}
            </span>
          </p>
          <p>
            <span class="font-semibold text-slate-600">Pagamentos:</span>
            <span :class="accountStatus?.payouts_enabled ? 'text-emerald-600' : 'text-rose-500'">
              {{ accountStatus?.payouts_enabled ? "Liberados" : "Pendentes" }}
            </span>
          </p>
        </div>
        <div class="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-full bg-emerald-500 px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:bg-emerald-300"
            :disabled="onboardingLoading"
            @click="startOnboarding"
          >
            {{ accountStatus?.connected ? "Atualizar dados" : "Conectar com Stripe" }}
          </button>
          <button type="button" class="text-sm font-semibold text-slate-500" @click="loadAccountStatus">
            Atualizar status
          </button>
        </div>
        <div v-if="accountStatus?.requirements?.length" class="mt-4 rounded-2xl bg-amber-50 p-4 text-sm text-amber-700">
          <p class="font-semibold">Pendências</p>
          <ul class="mt-2 list-disc pl-5">
            <li v-for="req in accountStatus.requirements" :key="req">{{ req }}</li>
          </ul>
        </div>
      </div>
      <div class="rounded-3xl border border-emerald-100 bg-emerald-50 p-6 text-slate-800 shadow">
        <h3 class="text-lg font-semibold">Como funciona</h3>
        <ul class="mt-3 space-y-2 text-sm">
          <li>• Checkout embarcado com Stripe Payment Element.</li>
          <li>• Repasse automático menos 1,5% de comissão.</li>
          <li>• Gestão de passageiros diretamente no painel.</li>
        </ul>
      </div>
    </div>

    <div v-else class="space-y-4">
      <div class="flex items-center justify-between">
        <p class="text-sm text-slate-500">Total de vendas: {{ salesPagination.total }}</p>
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-1.5 text-sm font-semibold text-slate-600"
          @click="loadSales"
        >
          Atualizar
        </button>
      </div>
      <div v-if="sales.length === 0" class="rounded-3xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        Nenhuma venda encontrada.
      </div>
      <div v-else class="grid gap-4">
        <div
          v-for="sale in sales"
          :key="sale.id"
          class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Venda #{{ sale.id }}</p>
              <h4 class="text-lg font-semibold text-slate-900">{{ sale.product_title }}</h4>
              <p class="text-sm text-slate-500">
                {{ formatCurrency(sale.amount_cents) }} • {{ sale.installments }}x •
                {{ sale.customer_name || "Cliente" }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2 text-xs font-semibold">
              <span :class="['rounded-full px-3 py-1', statusClasses.payment[sale.payment_status] || defaultChip]">
                {{ paymentStatusLabel(sale.payment_status) }}
              </span>
              <span :class="['rounded-full px-3 py-1', statusClasses.payout[sale.payout_status] || defaultChip]">
                {{ payoutStatusLabel(sale.payout_status) }}
              </span>
              <span :class="['rounded-full px-3 py-1', statusClasses.passengers[sale.passenger_status] || defaultChip]">
                Passageiros: {{ passengerStatusLabel(sale.passenger_status) }}
              </span>
            </div>
          </div>
          <div class="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
            <p><span class="font-semibold">Taxa Stripe:</span> {{ formatCurrency(sale.stripe_fee_cents) }}</p>
            <p><span class="font-semibold">Comissão:</span> {{ formatCurrency(sale.commission_cents) }}</p>
            <p><span class="font-semibold">Líquido:</span> {{ formatCurrency(sale.net_amount_cents) }}</p>
          </div>
          <div class="mt-4 flex flex-wrap gap-3">
            <button class="text-sm font-semibold text-slate-600" @click="openSaleDetails(sale.id)">Ver detalhes</button>
            <button class="text-sm font-semibold text-slate-600" @click="openPassengerModal(sale.id)">
              Passageiros
            </button>
            <button class="text-sm font-semibold text-slate-600" @click="copyPassengerLink(sale.id)">
              Copiar link
            </button>
          </div>
        </div>
      </div>
    </div>

    <teleport to="body">
      <transition name="fade">
        <div
          v-if="saleDetailsVisible && selectedSale"
          class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
        >
          <div class="w-full max-w-3xl rounded-3xl bg-white p-6 shadow-2xl">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">Resumo</p>
                <h3 class="text-2xl font-bold text-slate-900">{{ selectedSale.product_title }}</h3>
              </div>
              <button type="button" class="rounded-full p-2 text-slate-500 hover:bg-slate-100" @click="saleDetailsVisible = false">
                ✕
              </button>
            </div>
            <div class="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
              <p><span class="font-semibold">Cliente:</span> {{ selectedSale.customer_name || "-" }}</p>
              <p><span class="font-semibold">E-mail:</span> {{ selectedSale.customer_email || "-" }}</p>
              <p><span class="font-semibold">Telefone:</span> {{ selectedSale.customer_phone || "-" }}</p>
              <p><span class="font-semibold">Forma:</span> {{ selectedSale.payment_method || "-" }}</p>
            </div>
            <div class="mt-4 rounded-2xl bg-slate-50 p-4">
              <p class="text-sm font-semibold text-slate-600">Passageiros</p>
              <ul v-if="selectedSale.passengers.length" class="mt-2 space-y-1 text-sm text-slate-600">
                <li v-for="passenger in selectedSale.passengers" :key="passenger.id">
                  {{ passenger.name }} - {{ passenger.cpf || "sem CPF" }}
                </li>
              </ul>
              <p v-else class="mt-2 text-sm text-slate-500">Nenhum passageiro vinculado.</p>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="fade">
        <div
          v-if="passengerModalVisible && passengerSale"
          class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
        >
          <div class="w-full max-w-4xl rounded-3xl bg-white p-6 shadow-2xl">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Passageiros</p>
                <h3 class="text-2xl font-bold text-slate-900">{{ passengerSale.product_title }}</h3>
              </div>
              <button type="button" class="rounded-full p-2 text-slate-500 hover:bg-slate-100" @click="closePassengerModal">
                ✕
              </button>
            </div>
            <div class="mt-4 max-h-[65vh] overflow-y-auto pr-1">
              <PassengerFormFields v-model="passengerForm" :passengers-required="passengerSale.passengers_required" />
            </div>
            <div class="mt-4 flex justify-end gap-3">
              <button type="button" class="rounded-full px-4 py-2 text-sm text-slate-500" @click="closePassengerModal">
                Cancelar
              </button>
              <button
                type="button"
                class="rounded-full bg-emerald-500 px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30"
                :disabled="passengerSaving"
                @click="savePassengers"
              >
                {{ passengerSaving ? "Salvando..." : "Salvar passageiros" }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  createStripeOnboardingLink,
  fetchStripeAccountStatus,
  getPassengerLink,
  getSaleDetails,
  listSales,
  saveSalePassengers
} from "../../services/finance";
import type { Passenger, SaleDetail, SaleSummary, StripeAccountStatus } from "../../types/finance";
import PassengerFormFields from "../../components/finance/PassengerFormFields.vue";

const activeTab = ref<"config" | "sales">("config");
const accountStatus = ref<StripeAccountStatus | null>(null);
const onboardingLoading = ref(false);
const sales = ref<SaleSummary[]>([]);
const salesPagination = ref({ page: 1, pageSize: 10, total: 0 });
const selectedSale = ref<SaleDetail | null>(null);
const saleDetailsVisible = ref(false);
const passengerModalVisible = ref(false);
const passengerSale = ref<SaleDetail | null>(null);
const passengerForm = ref<Passenger[]>([]);
const passengerSaving = ref(false);

const defaultChip = "bg-slate-100 text-slate-600";
const statusClasses = {
  payment: {
    succeeded: "bg-emerald-100 text-emerald-700",
    processing: "bg-amber-100 text-amber-700",
    requires_payment_method: "bg-rose-100 text-rose-600",
    requires_action: "bg-amber-100 text-amber-700",
    canceled: "bg-slate-200 text-slate-600"
  },
  payout: {
    pending: "bg-amber-100 text-amber-700",
    available: "bg-blue-100 text-blue-700",
    payout_paid: "bg-emerald-100 text-emerald-700",
    payout_failed: "bg-rose-100 text-rose-600"
  },
  passengers: {
    not_started: "bg-slate-200 text-slate-600",
    partial: "bg-amber-100 text-amber-700",
    completed: "bg-emerald-100 text-emerald-700"
  }
} as const;

const formatCurrency = (value?: number | null) => {
  const cents = typeof value === "number" ? value : 0;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
};

const paymentStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    succeeded: "Pago",
    processing: "Processando",
    requires_payment_method: "Aguardando",
    requires_action: "Ação necessária",
    canceled: "Cancelado"
  };
  return map[status] || status;
};

const payoutStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: "Aguardando liberação",
    available: "Disponível",
    payout_paid: "Recebido",
    payout_failed: "Falha no saque"
  };
  return map[status] || status;
};

const passengerStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    not_started: "Pendentes",
    partial: "Parcial",
    completed: "Completo"
  };
  return map[status] || status;
};

const loadAccountStatus = async () => {
  try {
    const { data } = await fetchStripeAccountStatus();
    accountStatus.value = data;
  } catch (err) {
    console.error("Erro ao carregar status Stripe", err);
  }
};

const startOnboarding = async () => {
  onboardingLoading.value = true;
  try {
    const { data } = await createStripeOnboardingLink();
    window.location.assign(data.url);
  } catch (err) {
    console.error("Erro ao iniciar onboarding", err);
  } finally {
    onboardingLoading.value = false;
  }
};

const loadSales = async () => {
  try {
    const { data } = await listSales(salesPagination.value.page, salesPagination.value.pageSize);
    sales.value = data.items;
    salesPagination.value.total = data.total;
  } catch (err) {
    console.error("Erro ao carregar vendas", err);
  }
};

const openSaleDetails = async (saleId: number) => {
  try {
    const { data } = await getSaleDetails(saleId);
    selectedSale.value = data;
    saleDetailsVisible.value = true;
  } catch (err) {
    console.error("Erro ao carregar venda", err);
  }
};

const openPassengerModal = async (saleId: number) => {
  try {
    const { data } = await getSaleDetails(saleId);
    passengerSale.value = data;
    passengerForm.value = data.passengers || [];
    passengerModalVisible.value = true;
  } catch (err) {
    console.error("Erro ao carregar passageiros", err);
  }
};

const closePassengerModal = () => {
  passengerModalVisible.value = false;
  passengerForm.value = [];
  passengerSale.value = null;
};

const savePassengers = async () => {
  if (!passengerSale.value) return;
  passengerSaving.value = true;
  try {
    const { data } = await saveSalePassengers(passengerSale.value.id, passengerForm.value);
    passengerSale.value = data;
    passengerForm.value = data.passengers || [];
    await loadSales();
    closePassengerModal();
  } catch (err) {
    console.error("Erro ao salvar passageiros", err);
  } finally {
    passengerSaving.value = false;
  }
};

const copyPassengerLink = async (saleId: number) => {
  try {
    const { data } = await getPassengerLink(saleId);
    await navigator.clipboard.writeText(data.url);
  } catch (err) {
    console.error("Erro ao copiar link", err);
  }
};

onMounted(() => {
  loadAccountStatus();
  loadSales();
});
</script>
