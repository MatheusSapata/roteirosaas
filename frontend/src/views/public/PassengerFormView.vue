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
                  <p class="text-xs uppercase tracking-wide text-slate-400">Ocupação consumida</p>
                  <p class="text-base font-semibold text-slate-900">{{ formInfo.consumed_capacity }}</p>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Cliente</p>
                  <p class="text-base font-semibold text-slate-900">{{ formInfo.customer_name || "Não informado" }}</p>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-slate-400">Contato</p>
                  <p class="text-base font-semibold text-slate-900">
                    {{ formInfo.customer_email || formInfo.customer_phone || "-" }}
                  </p>
                </div>
              </div>
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-400">Pacotes adquiridos</p>
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
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Grupos de passageiros</p>
                <p class="text-sm text-slate-500">
                  Cada pacote gera um grupo independente. Salve antes de mudar de grupo.
                </p>
              </div>
              <button
                type="button"
                class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300"
                :disabled="groupsLoading"
                @click="loadPassengerGroups"
              >
                Atualizar grupos
              </button>
            </div>

            <div v-if="groupsLoading" class="py-8 text-center text-sm text-slate-500">Carregando grupos...</div>

            <div v-else>
              <div v-if="passengerGroups.length" class="space-y-4 pt-4">
                <div class="flex gap-2 overflow-x-auto">
                  <button
                    v-for="(group, index) in passengerGroups"
                    :key="group.id"
                    type="button"
                    class="group-chip"
                    :class="index === activeGroupIndex ? 'group-chip-active' : ''"
                    @click="selectGroup(index)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-sm font-semibold text-slate-900">{{ group.label }}</p>
                        <p class="text-xs text-slate-500">{{ group.occupied_slots }} / {{ group.capacity }} ocupados</p>
                      </div>
                      <span :class="['badge', groupBadgeClass(group.status)]">
                        {{ passengerStatusLabel(group.status) }}
                      </span>
                    </div>
                  </button>
                </div>

                <div v-if="activeGroup" class="space-y-4 rounded-2xl border border-slate-100 p-4 shadow-sm">
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-wide text-slate-400">{{ activeGroup.product_name }}</p>
                      <p class="text-sm font-semibold text-slate-900">
                        Capacidade {{ activeGroup.capacity }} pessoas
                      </p>
                    </div>
                    <div class="rounded-full bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-600">
                      {{ activeGroup.occupied_slots }} / {{ activeGroup.capacity }} ocupados
                    </div>
                  </div>

                  <div class="flex flex-wrap gap-2 overflow-x-auto border-b border-slate-100 pb-3">
                    <button
                      v-for="(passenger, index) in activeGroup.passengers"
                      :key="`slot-${passenger.passenger_index}`"
                      type="button"
                      class="passenger-chip"
                      :class="[
                        passengerChipState(passengerSlotState(passenger)),
                        index === activePassengerIndex ? 'passenger-chip-active' : '',
                      ]"
                      @click="selectPassenger(index)"
                    >
                      <span>Passageiro {{ passenger.passenger_index }}</span>
                      <span class="text-[10px] uppercase tracking-wide">
                        {{ passengerSlotLabel(passengerSlotState(passenger)) }}
                      </span>
                    </button>
                  </div>

                  <div v-if="activePassenger" class="space-y-4">
                    <div class="grid gap-3 md:grid-cols-2">
                      <div>
                        <label class="input-label">Tipo</label>
                        <select v-model="activePassenger.type" class="input mt-1">
                          <option value="adult">Adulto</option>
                          <option value="child_paid">Criança paga</option>
                          <option value="child_free">Criança gratuita</option>
                        </select>
                      </div>
                      <div class="md:col-span-2">
                        <label class="input-label">Nome completo</label>
                        <input v-model="activePassenger.name" class="input mt-1" placeholder="Nome completo" />
                      </div>
                      <div>
                        <label class="input-label">CPF</label>
                        <input v-model="activePassenger.cpf" class="input mt-1" placeholder="000.000.000-00" />
                      </div>
                      <div>
                        <label class="input-label">Nascimento</label>
                        <input v-model="activePassenger.birthdate" type="date" class="input mt-1" />
                      </div>
                      <div>
                        <label class="input-label">Telefone</label>
                        <input v-model="activePassenger.phone" class="input mt-1" placeholder="(00) 00000-0000" />
                      </div>
                      <div>
                        <label class="input-label">WhatsApp</label>
                        <input v-model="activePassenger.whatsapp" class="input mt-1" placeholder="(00) 00000-0000" />
                      </div>
                      <div class="md:col-span-2">
                        <label class="input-label">Local de embarque</label>
                        <select v-model="activePassenger.boarding_location" class="input mt-1">
                          <option value="">Não definir</option>
                          <option v-for="option in boardingOptions" :key="option" :value="option">{{ option }}</option>
                        </select>
                        <p v-if="!boardingOptions.length" class="mt-1 text-xs text-slate-500">
                          Nenhum local cadastrado para este produto.
                        </p>
                      </div>
                    </div>
                    <div>
                      <label class="input-label">Observações</label>
                      <textarea
                        v-model="activePassenger.extras"
                        rows="3"
                        class="input mt-1"
                        placeholder="Informações importantes"
                      ></textarea>
                    </div>
                  </div>
                </div>
              </div>

              <div
                v-else
                class="mt-4 rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500"
              >
                Nenhum grupo disponível.
              </div>
            </div>

            <p v-if="errorMessage" class="mt-4 text-sm text-rose-500">{{ errorMessage }}</p>
            <div class="mt-6 flex flex-wrap justify-end gap-3">
              <button class="pill" type="button" :disabled="saving || !activeGroup" @click="saveCurrentGroup">
                {{ saving && savingGroupMode === "group" ? "Salvando..." : "Salvar grupo" }}
              </button>
              <button
                type="button"
                class="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
                :disabled="saving || !passengerGroups.length"
                @click="submitPassengers"
              >
                {{ saving && savingGroupMode === "all" ? "Enviando..." : "Enviar passageiros" }}
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
import {
  getPublicPassengerForm,
  getPublicPassengerGroups,
  savePublicPassengerGroup,
} from "../../services/finance";
import type {
  Passenger,
  PassengerFormResponse,
  PassengerGroup,
  PassengerGroupSavePayload,
  PassengerType,
  SaleItem,
} from "../../types/finance";

type PassengerSlot = {
  id?: number;
  passenger_group_id: number;
  passenger_index: number;
  type: PassengerType;
  name: string;
  cpf?: string | null;
  birthdate?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  boarding_location?: string | null;
  extras?: string | null;
};

type PassengerGroupForm = PassengerGroup & { passengers: PassengerSlot[] };

const route = useRoute();
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const groupsLoading = ref(false);
const saving = ref(false);
const savingGroupMode = ref<"group" | "all" | null>(null);
const errorMessage = ref<string | null>(null);
const passengerGroups = ref<PassengerGroupForm[]>([]);
const activeGroupIndex = ref(0);
const activePassengerIndex = ref(0);

const token = computed(() => {
  const value = route.params.token;
  return typeof value === "string" ? value : null;
});

const formItems = computed<SaleItem[]>(() => formInfo.value?.items || []);
const activeGroup = computed(() => passengerGroups.value[activeGroupIndex.value] || null);
const activePassenger = computed(() => activeGroup.value?.passengers[activePassengerIndex.value] || null);
const boardingOptions = computed(() => formInfo.value?.boarding_locations || []);

const passengerSlotHasData = (slot?: PassengerSlot | null) => {
  if (!slot) return false;
  return Boolean(
    slot.name?.trim() ||
      slot.cpf?.trim() ||
      slot.phone?.trim() ||
      slot.whatsapp?.trim() ||
      slot.boarding_location?.trim() ||
      slot.extras?.trim(),
  );
};

const passengerSlotState = (slot?: PassengerSlot | null): "empty" | "partial" | "complete" => {
  if (!passengerSlotHasData(slot)) return "empty";
  if (slot?.name && slot?.cpf) return "complete";
  return "partial";
};

const passengerSlotLabel = (state: "empty" | "partial" | "complete") => {
  if (state === "complete") return "Completo";
  if (state === "partial") return "Incompleto";
  return "Livre";
};

const passengerChipState = (state: "empty" | "partial" | "complete") => {
  if (state === "complete") return "passenger-chip-complete";
  if (state === "partial") return "passenger-chip-partial";
  return "passenger-chip-empty";
};

const createSlot = (groupId: number, index: number, passenger?: Passenger): PassengerSlot => ({
  id: passenger?.id ?? undefined,
  passenger_group_id: groupId,
  passenger_index: index,
  type: (passenger?.type as PassengerType) || "adult",
  name: passenger?.name || "",
  cpf: passenger?.cpf || "",
  birthdate: passenger?.birthdate || "",
  phone: passenger?.phone || "",
  whatsapp: passenger?.whatsapp || "",
  boarding_location: passenger?.boarding_location || "",
  extras: passenger?.extras || "",
});

const normalizeGroup = (group: PassengerGroup): PassengerGroupForm => {
  const passengers: PassengerSlot[] = Array.from({ length: group.capacity }, (_, idx) => {
    const existing = (group.passengers || []).find(entry => entry.passenger_index === idx + 1);
    return createSlot(group.id, idx + 1, existing);
  });
  return { ...group, passengers };
};

const selectGroup = (index: number) => {
  if (!passengerGroups.value.length) return;
  const safeIndex = Math.max(0, Math.min(index, passengerGroups.value.length - 1));
  activeGroupIndex.value = safeIndex;
  const group = passengerGroups.value[safeIndex];
  const nextPassenger = group.passengers.findIndex(slot => passengerSlotState(slot) !== "complete");
  activePassengerIndex.value = nextPassenger >= 0 ? nextPassenger : 0;
};

const selectPassenger = (index: number) => {
  const group = activeGroup.value;
  if (!group) return;
  activePassengerIndex.value = Math.max(0, Math.min(index, group.passengers.length - 1));
};

const applyGroupResponse = (groups: PassengerGroup[]) => {
  passengerGroups.value = groups.map(normalizeGroup);
  if (passengerGroups.value.length) {
    const firstPending = passengerGroups.value.findIndex(group => group.status !== "complete");
    selectGroup(firstPending >= 0 ? firstPending : 0);
  } else {
    activeGroupIndex.value = 0;
    activePassengerIndex.value = 0;
  }
};

const loadPassengerGroups = async () => {
  if (!token.value) return;
  groupsLoading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerGroups(token.value);
    applyGroupResponse(data.groups);
    if (formInfo.value) {
      formInfo.value.passenger_status = data.passenger_status;
      formInfo.value.passengers_required = data.passengers_required;
      formInfo.value.contract_id = data.contract_id || null;
      formInfo.value.contract_signature_link = data.contract_signature_link || null;
      formInfo.value.contract_signature_token = data.contract_signature_token || null;
    }
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar os grupos.";
  } finally {
    groupsLoading.value = false;
  }
};

const loadForm = async () => {
  if (!token.value) {
    errorMessage.value = "Link inválido.";
    return;
  }
  loading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerForm(token.value);
    formInfo.value = data;
    await loadPassengerGroups();
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar o formulário.";
  } finally {
    loading.value = false;
  }
};

const buildGroupPayload = (group: PassengerGroupForm): PassengerGroupSavePayload => ({
  passengers: group.passengers
    .filter(passengerSlotHasData)
    .map(slot => ({
      passenger_index: slot.passenger_index,
      type: slot.type,
      name: slot.name,
      cpf: slot.cpf || "",
      birth_date: slot.birthdate || "",
      birthdate: slot.birthdate || "",
      phone: slot.phone || "",
      whatsapp: slot.whatsapp || "",
      boarding_location: slot.boarding_location || "",
      notes: slot.extras || "",
      extras: slot.extras || "",
    })),
});

const updateGroup = (updated: PassengerGroup) => {
  const normalized = normalizeGroup(updated);
  const index = passengerGroups.value.findIndex(group => group.id === updated.id);
  if (index >= 0) {
    passengerGroups.value.splice(index, 1, normalized);
    selectGroup(index);
  }
};

const saveGroup = async (group: PassengerGroupForm) => {
  if (!token.value) throw new Error("Token ausente.");
  const payload = buildGroupPayload(group);
  const { data } = await savePublicPassengerGroup(token.value, group.id, payload);
  updateGroup(data);
};

const saveCurrentGroup = async () => {
  const group = activeGroup.value;
  if (!group) return;
  saving.value = true;
  savingGroupMode.value = "group";
  errorMessage.value = null;
  try {
    await saveGroup(group);
    await loadPassengerGroups();
    alert("Grupo salvo com sucesso!");
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar o grupo.";
  } finally {
    saving.value = false;
    savingGroupMode.value = null;
  }
};

const submitPassengers = async () => {
  if (!token.value || !passengerGroups.value.length) return;
  saving.value = true;
  savingGroupMode.value = "all";
  errorMessage.value = null;
  try {
    for (const group of passengerGroups.value) {
      await saveGroup(group);
    }
    await loadPassengerGroups();
    alert("Passageiros enviados com sucesso!");
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar os passageiros.";
  } finally {
    saving.value = false;
    savingGroupMode.value = null;
  }
};

watch(
  () => passengerGroups.value.length,
  length => {
    if (!length) {
      activeGroupIndex.value = 0;
      activePassengerIndex.value = 0;
    } else if (activeGroupIndex.value >= length) {
      selectGroup(length - 1);
    }
  },
);

onMounted(loadForm);

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
      pending: "Grupo pendente",
      partial: "Passageiros parciais",
      completed: "Passageiros completos",
    } as Record<string, string>
  )[status] || status;

const groupBadgeClass = (status: string) => ({
  completed: "bg-emerald-100 text-emerald-700",
  partial: "bg-amber-100 text-amber-700",
  pending: "bg-slate-100 text-slate-600",
}[status as "completed" | "partial" | "pending"] || "bg-slate-100 text-slate-600");

const saleChannelLabel = (channel: string) => {
  if (channel === "pos") return "PDV";
  if (channel === "link") return "Link";
  return "Checkout";
};
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

.pill {
  border-radius: 9999px;
  border: 1px solid #e2e8f0;
  padding: 0.375rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  transition: border-color 0.2s ease;
}

.pill:hover {
  border-color: #cbd5f5;
}

.pill:disabled {
  cursor: not-allowed;
  border-color: #f1f5f9;
  color: #cbd5f5;
  opacity: 0.6;
}

.group-chip {
  min-width: 180px;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  padding: 0.75rem 1rem;
  text-align: left;
  transition: border-color 0.2s ease;
}

.group-chip:hover {
  border-color: #cbd5f5;
}

.group-chip-active {
  border-color: #34d399;
  background: #ecfdf5;
}

.passenger-chip {
  border-radius: 9999px;
  border: 1px solid #e2e8f0;
  padding: 0.25rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.passenger-chip-active {
  border-color: #10b981;
  background: #10b981;
  color: #fff;
}

.passenger-chip-complete {
  border-color: #a7f3d0;
  background: #ecfdf5;
  color: #047857;
}

.passenger-chip-partial {
  border-color: #fcd34d;
  background: #fffbeb;
  color: #b45309;
}

.passenger-chip-empty {
  border-color: #e2e8f0;
  background: #fff;
  color: #64748b;
}
</style>
