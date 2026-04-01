<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-4xl rounded-3xl bg-white p-6 shadow-xl">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-600">Dados dos passageiros</p>
          <h1 class="text-3xl font-bold text-slate-900">{{ formInfo?.product_title || "Preencha os dados" }}</h1>
          <p class="text-sm text-slate-500">
            Informe todos os passageiros para liberar o roteiro.
          </p>
        </div>
      </div>

      <div v-if="loading" class="mt-8 text-center text-sm text-slate-500">Carregando formulário...</div>

      <div v-else class="mt-6 space-y-4">
        <PassengerFormFields v-model="passengers" :passengers-required="formInfo?.passengers_required || 0" />
        <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-emerald-300"
            :disabled="saving"
            @click="submitPassengers"
          >
            {{ saving ? "Enviando..." : "Enviar passageiros" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import PassengerFormFields from "../../components/finance/PassengerFormFields.vue";
import { getPublicPassengerForm, submitPublicPassengers } from "../../services/finance";
import type { Passenger, PassengerFormResponse } from "../../types/finance";

const route = useRoute();
const passengers = ref<Passenger[]>([]);
const formInfo = ref<PassengerFormResponse | null>(null);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref<string | null>(null);

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
    passengers.value = data.passengers || [];
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar o formulário.";
  } finally {
    loading.value = false;
  }
};

const submitPassengers = async () => {
  const token = typeof route.params.token === "string" ? route.params.token : null;
  if (!token) return;
  saving.value = true;
  errorMessage.value = null;
  try {
    const { data } = await submitPublicPassengers(token, passengers.value);
    formInfo.value = data;
    passengers.value = data.passengers || [];
    alert("Passageiros enviados com sucesso!");
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar os passageiros.";
  } finally {
    saving.value = false;
  }
};

onMounted(loadForm);
</script>
