<template>
  <div class="modal-overlay">
    <div class="modal-card">
      <button class="modal-close" @click="$router.back()">&times;</button>
      <div class="modal-scroll flex flex-col gap-6">
      <div class="rounded-3xl bg-white p-6 shadow-xl section-card">
        <div v-if="formInfo" class="space-y-4">
          <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Resumo da venda</p>
              <h1 class="text-3xl font-bold text-slate-900">{{ formInfo.product_title }}</h1>
              <p class="text-sm text-slate-500">
                Venda #{{ formInfo.sale_id }} • {{ saleChannelLabel(formInfo.channel) }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2 text-xs font-semibold">
              <span class="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700">
                {{ paymentStatusLabel(formInfo.payment_status) }}
              </span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">
                {{ payoutStatusLabel(formInfo.payout_status) }}
              </span>
              <span class="rounded-full bg-sky-100 px-3 py-1 text-sky-700">
                {{ passengerStatusLabel(formInfo.passenger_status) }}
              </span>
            </div>
          </div>
          <div class="grid gap-4 text-sm sm:grid-cols-2">
            <div class="space-y-3">
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Descrição do produto</p>
                <p class="text-base font-semibold text-slate-900">
                  {{ formInfo.product_description || "Sem descrição disponível" }}
                </p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Passageiros previstos</p>
                <p class="text-base font-semibold text-slate-900">{{ formInfo.passengers_required }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Canal</p>
                <p class="text-base font-semibold text-slate-900">{{ saleChannelLabel(formInfo.channel) }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Cliente</p>
                <p class="text-base font-semibold text-slate-900">
                  {{ formInfo.customer_name || "Não informado" }}
                </p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Contato</p>
                <p class="text-base font-semibold text-slate-900">
                  {{ formInfo.customer_email || formInfo.customer_phone || "-" }}
                </p>
              </div>
            </div>
            <div>
              <p class="text-xs uppercase tracking-wide text-slate-400">Pacotes e variações adquiridas</p>
              <ul class="mt-2 space-y-2 text-slate-600">
                <li
                  v-for="item in formItems"
                  :key="item.id"
                  class="rounded-2xl border border-slate-100 bg-slate-50 px-3 py-2"
                >
                  <p class="font-semibold text-slate-900">{{ item.variation_name }}</p>
                  <p>
                    {{ item.quantity }} x {{ formatCurrency(item.unit_price) }}
                    <span class="text-xs text-slate-500">
                      ({{ item.people_count * item.quantity }} passageiros)
                    </span>
                  </p>
                </li>
                <li v-if="!formItems.length" class="text-xs text-slate-500">Nenhum item associado.</li>
              </ul>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-sm text-slate-500">Carregando resumo da venda...</div>
      </div>

      <div class="rounded-3xl bg-white p-6 shadow-xl section-card">
        <template v-if="loading">
          <div class="text-center text-sm text-slate-500">Carregando formulário...</div>
        </template>
        <template v-else>
          <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Dados dos passageiros</p>
              <p class="text-sm text-slate-500">Informe todos os passageiros para liberar o roteiro.</p>
            </div>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300"
              @click="addPassenger"
            >
              + Passageiro
            </button>
          </div>

          <div v-if="passengers.length" class="mt-4 space-y-4">
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(passenger, index) in passengers"
                :key="passenger.localId"
                type="button"
                class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                :class="
                  activePassengerTab === index
                    ? 'border-emerald-500 bg-emerald-500 text-white'
                    : 'border-slate-200 bg-white text-slate-600 hover-border-slate-300'
                "
                @click="activePassengerTab = index"
              >
                Passageiro {{ index + 1 }}
              </button>
            </div>

            <div
              v-if="currentPassenger"
              :key="currentPassenger.localId"
              class="space-y-4 rounded-2xl border border-slate-200 p-4"
            >
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-slate-900">Passageiro {{ activePassengerTab + 1 }}</p>
                <button
                  v-if="passengers.length > 1"
                  type="button"
                  class="text-xs font-semibold text-rose-500"
                  @click="removePassenger(activePassengerTab)"
                >
                  Remover
                </button>
              </div>
              <div class="grid gap-3 md:grid-cols-2">
                <div class="md:col-span-2">
                  <label class="input-label">Nome completo</label>
                  <input v-model="currentPassenger.name" class="input mt-1" placeholder="Nome completo" />
                </div>
                <div>
                  <label class="input-label">CPF</label>
                  <input v-model="currentPassenger.cpf" class="input mt-1" placeholder="000.000.000-00" />
                </div>
                <div>
                  <label class="input-label">Nascimento</label>
                  <input v-model="currentPassenger.birthdate" type="date" class="input mt-1" />
                </div>
                <div>
                  <label class="input-label">Telefone</label>
                  <input v-model="currentPassenger.phone" class="input mt-1" placeholder="(00) 00000-0000" />
                </div>
                <div>
                  <label class="input-label">WhatsApp</label>
                  <input v-model="currentPassenger.whatsapp" class="input mt-1" placeholder="(00) 00000-0000" />
                </div>
                <div class="md:col-span-2">
                  <label class="input-label">Local de embarque</label>
                  <input v-model="currentPassenger.boarding_location" class="input mt-1" placeholder="Ponto de encontro" />
                </div>
              </div>
              <div>
                <label class="input-label">Observa��es</label>
                <textarea
                  v-model="currentPassenger.extras"
                  rows="3"
                  class="input mt-1"
                  placeholder="Informa��es importantes"
                ></textarea>
              </div>
            </div>
          </div>
          <div
            v-else
            class="mt-4 rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500"
          >
            Nenhum passageiro cadastrado ainda.
          </div>

          <p v-if="errorMessage" class="mt-4 text-sm text-rose-500">{{ errorMessage }}</p>
          <div class="mt-6 flex justify-end gap-3">
            <button
              type="button"
              class="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
              :disabled="saving"
              @click="submitPassengers"
            >
              {{ saving ? "Enviando..." : "Enviar passageiros" }}
            </button>
          </div>
        </template>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { getPublicPassengerForm, submitPublicPassengers } from "../../services/finance";
import type { Passenger, PassengerFormResponse } from "../../types/finance";

type PassengerEntry = Passenger & { localId: string };

const route = useRoute();
const passengers = ref<PassengerEntry[]>([]);
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref<string | null>(null);
const activePassengerTab = ref(0);
const currentPassenger = computed(() => passengers.value[activePassengerTab.value] || null);

const createPassenger = (): PassengerEntry => ({
  id: 0,
  localId: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2),
  name: "",
  cpf: "",
  birthdate: "",
  phone: "",
  whatsapp: "",
  boarding_location: "",
  extras: "",
});

const passengersRequired = computed(() => Math.max(formInfo.value?.passengers_required || 1, 1));
const formItems = computed(() => formInfo.value?.items || []);

const ensureMinimum = () => {
  while (passengers.value.length < passengersRequired.value) {
    passengers.value.push(createPassenger());
  }
};

const syncPassengers = (data?: Passenger[]) => {
  const base = data && data.length ? data : [];
  passengers.value = base.map(passenger => ({ ...createPassenger(), ...passenger }));
  ensureMinimum();
  activePassengerTab.value = 0;
};

const loadForm = async () => {
  const token = typeof route.params.token === "string" ? route.params.token : null;
  if (!token) {
    errorMessage.value = "Link inválido.";
    return;
  }
  loading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerForm(token);
    formInfo.value = data;
    syncPassengers(data.passengers || []);
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar o formulário.";
    passengers.value = [];
  } finally {
    loading.value = false;
  }
};

const sanitizedPassengers = () => passengers.value.map(({ localId, ...rest }) => rest);

const submitPassengers = async () => {
  const token = typeof route.params.token === "string" ? route.params.token : null;
  if (!token) return;
  saving.value = true;
  errorMessage.value = null;
  try {
    const { data } = await submitPublicPassengers(token, sanitizedPassengers());
    formInfo.value = data;
    syncPassengers(data.passengers || []);
    alert("Passageiros enviados com sucesso!");
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar os passageiros.";
  } finally {
    saving.value = false;
  }
};

const addPassenger = () => {
  passengers.value.push(createPassenger());
  activePassengerTab.value = passengers.value.length - 1;
};

const removePassenger = (index: number) => {
  if (passengers.value.length <= 1) return;
  passengers.value.splice(index, 1);
  ensureMinimum();
  if (activePassengerTab.value >= passengers.value.length) {
    activePassengerTab.value = passengers.value.length - 1;
  }
};

watch(passengersRequired, ensureMinimum);

watch(
  () => passengers.value.length,
  length => {
    if (!length) activePassengerTab.value = 0;
    else if (activePassengerTab.value >= length) activePassengerTab.value = length - 1;
  },
);

const formatCurrency = (value?: number | null) => {
  const cents = typeof value === "number" ? value : 0;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
};

const paymentStatusLabel = (status: string) =>
  (
    {
      pending: "Pagamento pendente",
      processing: "Processando pagamento",
      paid: "Pagamento confirmado",
      canceled: "Pagamento cancelado",
      refunded: "Pagamento reembolsado",
    } as Record<string, string>
  )[status] || status;

const payoutStatusLabel = (status: string) =>
  (
    {
      pending: "Repasse pendente",
      available: "Repasse disponível",
      payout_paid: "Repasse realizado",
      payout_failed: "Repasse com falha",
    } as Record<string, string>
  )[status] || status;

const passengerStatusLabel = (status: string) =>
  (
    {
      not_started: "Passageiros pendentes",
      partial: "Passageiros parciais",
      completed: "Passageiros completos",
    } as Record<string, string>
  )[status] || status;

const saleChannelLabel = (channel: string) => {
  if (channel === "pos") return "PDV";
  if (channel === "link") return "Link";
  return "Checkout";
};

onMounted(loadForm);
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  z-index: 50;
}

.modal-card {
  position: relative;
  width: 100%;
  max-width: 60rem;
  border-radius: 1.5rem;
  background: #f8fafc;
  box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.35);
}

.modal-scroll {
  max-height: 85vh;
  overflow-y: auto;
  padding: 1.5rem;
}

.modal-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: #94a3b8;
  cursor: pointer;
}

.modal-close:hover {
  color: #0f172a;
}

.section-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.1);
}

.input-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.input {
  width: 100%;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
  transition: border-color 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.2);
}
</style>

