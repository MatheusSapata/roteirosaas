<template>
  <teleport to="body">
    <transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4">
        <div class="w-full max-w-4xl rounded-3xl bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Pós-venda</p>
              <h2 class="text-2xl font-bold text-slate-900">{{ formInfo?.product_title || "Dados dos passageiros" }}</h2>
              <p class="text-sm text-slate-500">
                Complete as informações para {{ formInfo?.passengers_required || 0 }} passageiros.
              </p>
            </div>
            <button type="button" class="rounded-full p-2 text-slate-500 hover:bg-slate-100" @click="handleClose">
              ✕
            </button>
          </div>

          <div v-if="loading" class="mt-6 text-center text-sm text-slate-500">Carregando formulário...</div>
          <div v-else class="mt-6 space-y-4">
            <PassengerFormFields v-model="passengers" :passengers-required="formInfo?.passengers_required || 0" />
            <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
            <div class="flex justify-end">
              <button
                type="button"
                class="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/40 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
                :disabled="saving"
                @click="submitPassengers"
              >
                {{ saving ? "Salvando..." : "Enviar passageiros" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import PassengerFormFields from "../finance/PassengerFormFields.vue";
import { getPublicPassengerForm, submitPublicPassengers } from "../../services/finance";
import type { Passenger, PassengerFormResponse } from "../../types/finance";

const props = defineProps<{ modelValue: boolean; token: string | null }>();
const emit = defineEmits<{ (e: "update:modelValue", value: boolean): void; (e: "completed"): void }>();

const visible = computed(() => props.modelValue);
const passengers = ref<Passenger[]>([]);
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref<string | null>(null);

const handleClose = () => emit("update:modelValue", false);

const loadForm = async () => {
  if (!props.token) return;
  loading.value = true;
  errorMessage.value = null;
  try {
    const { data } = await getPublicPassengerForm(props.token);
    formInfo.value = data;
    passengers.value = data.passengers || [];
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar o formulário.";
  } finally {
    loading.value = false;
  }
};

const submitPassengers = async () => {
  if (!props.token) return;
  saving.value = true;
  errorMessage.value = null;
  try {
    const { data } = await submitPublicPassengers(props.token, passengers.value);
    formInfo.value = data;
    passengers.value = data.passengers || [];
    emit("completed");
    emit("update:modelValue", false);
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar os passageiros.";
  } finally {
    saving.value = false;
  }
};

watch(
  () => props.modelValue,
  value => {
    if (value) {
      loadForm();
    }
  }
);
</script>
