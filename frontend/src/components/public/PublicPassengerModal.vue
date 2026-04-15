<template>
  <teleport to="body">
    <transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="modal-card w-full max-w-4xl rounded-3xl bg-white shadow-2xl">
          <div class="modal-header flex items-start justify-between gap-4 px-6 pt-4 pb-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Pós-venda</p>
              <h2 class="text-2xl font-bold text-slate-900">{{ formInfo?.product_title || "Dados dos passageiros" }}</h2>
              <p class="text-sm text-slate-500">
                Complete as informações para {{ formInfo?.passengers_required || 0 }} passageiros.
              </p>
            </div>
            <button type="button" class="rounded-full p-2 text-slate-500 hover:bg-slate-100" @click="handleClose">
              &times;
            </button>
          </div>

          <div class="modal-body px-6 pb-6">
            <div v-if="loading" class="py-10 text-center text-sm text-slate-500">Carregando formulário...</div>
            <div v-else class="space-y-4">
            <transition name="fade">
              <div
                v-if="successVisible"
                class="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-emerald-800"
              >
                <span class="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-xl text-white">
                  ✔
                </span>
                <div>
                  <p class="text-sm font-semibold">Passageiros enviados!</p>
                  <p class="text-xs text-emerald-700">
                    As informações foram salvas. Você será redirecionado em instantes.
                  </p>
                </div>
              </div>
            </transition>

            <template v-if="!successVisible">
              <div class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-sm text-slate-600">
                <p>
                  Cliente:
                  <span class="font-semibold text-slate-900">{{ formInfo?.customer_name || "Não informado" }}</span>
                </p>
                <p>
                  Passageiros previstos:
                  <span class="font-semibold text-slate-900">{{ formInfo?.passengers_required || 0 }}</span>
                </p>
              </div>

              <div class="space-y-4 rounded-2xl border border-slate-100 p-4">
                <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">
                      Grupos de passageiros
                    </p>
                    <p class="text-sm text-slate-500">Cada unidade do pacote gera um grupo independente.</p>
                  </div>
                  <button
                    type="button"
                    class="pill"
                    :disabled="groupsLoading"
                    @click="loadPassengerGroups"
                  >
                    Atualizar grupos
                  </button>
                </div>

                <div v-if="groupsLoading" class="py-6 text-center text-sm text-slate-500">Carregando grupos...</div>

                <div v-else>
                  <div v-if="passengerGroups.length" class="space-y-4">
                    <div class="flex gap-3 overflow-x-auto">
                      <button
                        v-for="(group, index) in passengerGroups"
                        :key="group.id"
                        type="button"
                        class="group-chip"
                        :class="[
                          index === activeGroupIndex ? 'group-chip-active' : '',
                          groupStatusClass(group.status),
                        ]"
                        @click="selectGroup(index)"
                      >
                        <div class="flex items-center justify-between gap-4">
                          <div class="text-left">
                            <p class="text-sm font-semibold text-slate-900">{{ group.label }}</p>
                            <p class="text-xs text-slate-500">{{ group.occupied_slots }} / {{ group.capacity }} ocupados</p>
                          </div>
                          <p class="text-sm font-semibold" :class="groupStatusTextClass(group.status)">
                            {{ passengerStatusLabel(group.status) }}
                          </p>
                        </div>
                      </button>
                    </div>

                    <div v-if="activeGroup" class="space-y-4 rounded-2xl border border-slate-100 p-4">
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
                          <span class="passenger-label">Passageiro {{ passenger.passenger_index }}</span>
                          <span class="text-[10px] uppercase tracking-wide passenger-status">
                            {{ passengerSlotLabel(passengerSlotState(passenger)) }}
                          </span>
                        </button>
                      </div>

                      <div v-if="activePassenger" class="space-y-4">
                        <div class="grid gap-4 md:grid-cols-2">
                          <div class="field-block">
                            <label class="input-label">Tipo</label>
                            <select v-model="activePassenger.type" class="input">
                              <option value="adult">Adulto</option>
                              <option value="child_paid">Criança paga</option>
                              <option value="child_free">Criança gratuita</option>
                            </select>
                          </div>
                          <div class="field-block md:col-span-2">
                            <label class="input-label">Nome completo</label>
                            <input v-model="activePassenger.name" class="input" placeholder="Nome completo" />
                          </div>
                          <div class="field-block">
                            <label class="input-label">CPF</label>
                            <input v-model="activePassenger.cpf" class="input" placeholder="000.000.000-00" />
                          </div>
                          <div class="field-block">
                            <label class="input-label">Nascimento</label>
                            <input v-model="activePassenger.birthdate" type="date" class="input" />
                          </div>
                          <div class="field-block">
                            <label class="input-label">Telefone</label>
                            <input v-model="activePassenger.phone" class="input" placeholder="(00) 00000-0000" />
                          </div>
                          <div class="field-block">
                            <label class="input-label">WhatsApp</label>
                            <input v-model="activePassenger.whatsapp" class="input" placeholder="(00) 00000-0000" />
                          </div>
                      <div class="field-block md:col-span-2">
                        <label class="input-label">Local de embarque</label>
                        <select v-model="activePassenger.boarding_location" class="input">
                          <option value="">Não definir</option>
                          <option v-for="option in boardingOptions" :key="option" :value="option">{{ option }}</option>
                        </select>
                        <p v-if="!boardingOptions.length" class="mt-1 text-xs text-slate-500">
                          Nenhum local cadastrado para este produto.
                        </p>
                      </div>
                        </div>
                        <div class="field-block">
                          <label class="input-label">Observações</label>
                          <textarea
                            v-model="activePassenger.extras"
                            rows="3"
                            class="input"
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

                                <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
                <div class="flex flex-wrap justify-end gap-3">
                  <button class="pill" type="button" :disabled="saving || !activeGroup" @click="saveCurrentGroup">
                    {{ saving && savingMode === "group" ? "Salvando..." : "Salvar grupo" }}
                  </button>
                  <button
                    type="button"
                    class="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/40 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
                    :disabled="saving || !passengerGroups.length"
                    @click="submitPassengers"
                  >
                    {{ saving && savingMode === "all" ? "Enviando..." : "Enviar passageiros" }}
                  </button>
                </div>
              </div>
            </template>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
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

const props = defineProps<{ modelValue: boolean; token: string | null }>();
const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (
    e: "completed",
    payload?: {
      contractSignatureLink?: string | null;
      contractSignatureToken?: string | null;
      passengerToken?: string | null;
      isRoadTrip?: boolean;
    },
  ): void;
}>();

const visible = computed(() => props.modelValue);
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const groupsLoading = ref(false);
const saving = ref(false);
const savingMode = ref<"group" | "all" | null>(null);
const passengerGroups = ref<PassengerGroupForm[]>([]);
const activeGroupIndex = ref(0);
const activePassengerIndex = ref(0);
const errorMessage = ref<string | null>(null);
const successVisible = ref(false);
const lastContractInfo = ref<{ contractSignatureLink: string | null; contractSignatureToken: string | null } | null>(null);
let successTimer: ReturnType<typeof setTimeout> | null = null;

const activeGroup = computed(() => passengerGroups.value[activeGroupIndex.value] || null);
const activePassenger = computed(() => activeGroup.value?.passengers[activePassengerIndex.value] || null);
const boardingOptions = computed(() => formInfo.value?.boarding_locations || []);

const groupBadgeClass = (status: string) => {
  if (status === "complete" || status === "completed") return "badge-success";
  if (status === "partial") return "badge-warning";
  return "badge-muted";
};

const passengerStatusLabel = (status: string) =>
  (
    {
      not_started: "Pendentes",
      pending: "Pendentes",
      partial: "Parciais",
      complete: "Completos",
      completed: "Completos",
    } as Record<string, string>
  )[status] || status;

const resetSuccessState = () => {
  if (successTimer) {
    clearTimeout(successTimer);
    successTimer = null;
  }
  successVisible.value = false;
  lastContractInfo.value = null;
};

const handleClose = () => {
  resetSuccessState();
  emit("update:modelValue", false);
};

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

const groupStatusClass = (status: string) => {
  if (status === "complete" || status === "completed") return "group-chip-success";
  if (status === "partial") return "group-chip-warning";
  return "group-chip-muted";
};

const groupStatusTextClass = (status: string) => {
  if (status === "complete" || status === "completed") return "text-emerald-700";
  if (status === "partial") return "text-amber-700";
  return "text-slate-600";
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

const createSlot = (groupId: number, index: number, passenger?: Passenger, slotType?: PassengerType) => ({
  id: passenger?.id,
  passenger_group_id: groupId,
  passenger_index: index,
  type: (passenger?.type as PassengerType) || slotType || "adult",
  name: passenger?.name || "",
  cpf: passenger?.cpf || "",
  birthdate: passenger?.birthdate || "",
  phone: passenger?.phone || "",
  whatsapp: passenger?.whatsapp || "",
  boarding_location: passenger?.boarding_location || "",
  extras: passenger?.extras || "",
});

const resolvedSlotTypes = (group: PassengerGroup): PassengerType[] => {
  if (Array.isArray(group.slot_types) && group.slot_types.length) {
    return [...group.slot_types] as PassengerType[];
  }
  const fallbackLength = Math.max(group.capacity, 0);
  return Array.from({ length: fallbackLength }, () => "adult" as PassengerType);
};

const normalizeGroup = (group: PassengerGroup): PassengerGroupForm => {
  const slotTypes = resolvedSlotTypes(group);
  const slotCount = Math.max(slotTypes.length, group.passengers?.length || 0);
  const passengers: PassengerSlot[] = Array.from({ length: slotCount }, (_, idx) => {
    const existing = (group.passengers || []).find(entry => entry.passenger_index === idx + 1);
    const slotType = slotTypes[idx] || slotTypes[slotTypes.length - 1] || ("adult" as PassengerType);
    return createSlot(group.id, idx + 1, existing, slotType);
  });
  return { ...group, slot_types: slotTypes, passengers };
};

const selectGroup = (index: number) => {
  if (!passengerGroups.value.length) return;
  const safeIndex = Math.max(0, Math.min(index, passengerGroups.value.length - 1));
  activeGroupIndex.value = safeIndex;
  const group = passengerGroups.value[safeIndex];
  const firstPending = group.passengers.findIndex(slot => passengerSlotState(slot) !== "complete");
  activePassengerIndex.value = firstPending >= 0 ? firstPending : 0;
};

const selectPassenger = (index: number) => {
  const group = activeGroup.value;
  if (!group) return;
  activePassengerIndex.value = Math.max(0, Math.min(index, group.passengers.length - 1));
};

const applyGroupResponse = (groups: PassengerGroup[]) => {
  passengerGroups.value = groups.map(normalizeGroup);
  if (passengerGroups.value.length) {
    const nextGroup = passengerGroups.value.findIndex(group => group.status !== "complete");
    selectGroup(nextGroup >= 0 ? nextGroup : 0);
  } else {
    activeGroupIndex.value = 0;
    activePassengerIndex.value = 0;
  }
};

const loadPassengerGroups = async () => {
  if (!props.token) return;
  groupsLoading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerGroups(props.token);
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
  if (!props.token) return;
  loading.value = true;
  errorMessage.value = null;
  resetSuccessState();
  try {
    const { data } = await getPublicPassengerForm(props.token);
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

const saveGroup = async (group: PassengerGroupForm) => {
  if (!props.token) throw new Error("Token ausente.");
  const payload = buildGroupPayload(group);
  const { data } = await savePublicPassengerGroup(props.token, group.id, payload);
  const normalized = normalizeGroup(data);
  const index = passengerGroups.value.findIndex(item => item.id === data.id);
  if (index >= 0) {
    passengerGroups.value.splice(index, 1, normalized);
    selectGroup(index);
  }
};

const saveCurrentGroup = async () => {
  const group = activeGroup.value;
  if (!group) return;
  saving.value = true;
  savingMode.value = "group";
  errorMessage.value = null;
  try {
    await saveGroup(group);
    await loadPassengerGroups();
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar o grupo.";
  } finally {
    saving.value = false;
    savingMode.value = null;
  }
};

const submitPassengers = async () => {
  if (!passengerGroups.value.length) return;
  saving.value = true;
  savingMode.value = "all";
  errorMessage.value = null;
  try {
    for (const group of passengerGroups.value) {
      await saveGroup(group);
    }
    await loadPassengerGroups();
    successVisible.value = true;
    lastContractInfo.value = {
      contractSignatureLink: formInfo.value?.contract_signature_link || null,
      contractSignatureToken: formInfo.value?.contract_signature_token || null,
    };
    successTimer = setTimeout(() => {
      const payload = {
        ...(lastContractInfo.value || {}),
        passengerToken: props.token || null,
        isRoadTrip: !!formInfo.value?.is_road_trip,
      };
      resetSuccessState();
      emit("completed", payload);
      emit("update:modelValue", false);
    }, 3000);
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar os passageiros.";
    successVisible.value = false;
  } finally {
    saving.value = false;
    savingMode.value = null;
  }
};

watch(
  () => props.modelValue,
  value => {
    if (value) {
      loadForm();
    } else {
      resetSuccessState();
    }
  },
);

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

onUnmounted(() => {
  resetSuccessState();
});
</script>

<style scoped>
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
  min-width: 200px;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  padding: 0.8rem 1.25rem;
  text-align: left;
  transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
  display: inline-flex;
  flex-direction: column;
  gap: 0.2rem;
}

.group-chip:hover {
  border-color: #cbd5f5;
}

.group-chip-active {
  border-color: #34d399;
  background: #ecfdf5;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25);
}

.group-chip-success {
  border-color: #34d399;
  background: #ecfdf5;
}

.group-chip-warning {
  border-color: #fbbf24;
  background: #fffbeb;
}

.group-chip-muted {
  border-color: #e2e8f0;
  background: #f8fafc;
}

.passenger-chip {
  border-radius: 9999px;
  border: 1px solid #e2e8f0;
  padding: 0.4rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.passenger-chip-active {
  border-color: #111827;
  color: #111827;
  background: #fff;
  box-shadow: inset 0 0 0 1px #111827;
  transform: none;
  transition: box-shadow 0.2s ease;
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
.passenger-chip .passenger-status {
  margin-left: 4px;
  color: inherit;
}
.modal-card {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.modal-header {
  border-bottom: 1px solid #e2e8f0;
}
.modal-body {
  flex: 1;
  overflow-y: auto;
}
.field-block {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.input-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
}
.input {
  width: 100%;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
  background: #fff;
  transition: border-color 0.2s ease;
}
.input:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.2);
}
</style>
