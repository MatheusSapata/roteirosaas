<template>
  <teleport to="body">
    <transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="w-full max-w-4xl rounded-3xl bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Pos-venda</p>
              <h2 class="text-2xl font-bold text-slate-900">{{ formInfo?.product_title || "Dados dos passageiros" }}</h2>
              <p class="text-sm text-slate-500">
                Complete as informacoes para {{ formInfo?.passengers_required || 0 }} passageiros.
              </p>
            </div>
            <button type="button" class="rounded-full p-2 text-slate-500 hover:bg-slate-100" @click="handleClose">
              &times;
            </button>
          </div>

          <div v-if="loading" class="mt-6 text-center text-sm text-slate-500">Carregando formulario...</div>
          <div v-else class="mt-6 space-y-4">
            <transition name="fade">
              <div
                v-if="successVisible"
                class="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-emerald-800"
              >
                <span class="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-xl text-white">
                  ✓
                </span>
                <div>
                  <p class="text-sm font-semibold">Passageiros enviados!</p>
                  <p class="text-xs text-emerald-700">
                    As informacoes foram salvas. Voce sera redirecionado em instantes.
                  </p>
                </div>
              </div>
            </transition>

            <template v-if="!successVisible">
              <PassengerFormFields
                v-model="passengers"
                :passengers-required="formInfo?.passengers_required || 0"
                ref="passengerFields"
              />
              <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
              <div class="flex justify-end">
                <button
                  type="button"
                  class="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/40 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
                  :disabled="saving || !canSubmitPassengers"
                  @click="submitPassengers"
                >
                  {{ saving ? "Salvando..." : "Enviar passageiros" }}
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import PassengerFormFields from "../finance/PassengerFormFields.vue";
import { getPublicPassengerForm, submitPublicPassengers } from "../../services/finance";
import type { Passenger, PassengerFormResponse } from "../../types/finance";

const props = defineProps<{ modelValue: boolean; token: string | null }>();
const emit = defineEmits<{ (e: "update:modelValue", value: boolean): void; (e: "completed"): void }>();

const visible = computed(() => props.modelValue);
const passengers = ref<Passenger[]>([]);
const passengerFields = ref<InstanceType<typeof PassengerFormFields> | null>(null);
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref<string | null>(null);
const successVisible = ref(false);
const canSubmitPassengers = computed(() => passengerFields.value?.valid ?? false);
let successTimer: ReturnType<typeof setTimeout> | null = null;

const resetSuccessState = () => {
  if (successTimer) {
    clearTimeout(successTimer);
    successTimer = null;
  }
  successVisible.value = false;
};

const handleClose = () => {
  resetSuccessState();
  emit("update:modelValue", false);
};

const loadForm = async () => {
  if (!props.token) return;
  loading.value = true;
  errorMessage.value = null;
  resetSuccessState();
  try {
    const { data } = await getPublicPassengerForm(props.token);
    formInfo.value = data;
    passengers.value = data.passengers || [];
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Nao foi possivel carregar o formulario.";
  } finally {
    loading.value = false;
  }
};

const submitPassengers = async () => {
  if (!props.token) return;
  if (!canSubmitPassengers.value) {
    errorMessage.value = "Preencha ao menos o nome de todos os passageiros.";
    return;
  }
  saving.value = true;
  errorMessage.value = null;
  try {
    const { data } = await submitPublicPassengers(props.token, passengers.value);
    formInfo.value = data;
    passengers.value = data.passengers || [];
    successVisible.value = true;
    successTimer = setTimeout(() => {
      resetSuccessState();
      emit("completed");
      emit("update:modelValue", false);
    }, 3000);
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Nao foi possivel salvar os passageiros.";
  } finally {
    saving.value = false;
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
  }
);

onUnmounted(() => {
  resetSuccessState();
});
</script>

