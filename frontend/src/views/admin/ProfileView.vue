<template>
  <div class="space-y-6">
    <header class="flex flex-col gap-2">
      <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Conta</p>
      <h1 class="text-2xl font-bold text-slate-900">Perfil e Assinatura</h1>
      <p class="text-sm text-slate-600">Veja seus dados principais, plano atual e validade.</p>
    </header>

    <div
      v-if="trialInfo"
      class="flex flex-col gap-3 rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-5 text-slate-800 shadow-sm md:flex-row md:items-center md:justify-between"
    >
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-600">Trial ativo</p>
        <h3 class="text-lg font-bold">Plano {{ trialInfo.plan }} liberado até {{ trialInfo.endsAt }}</h3>
        <p class="text-sm text-slate-600">
          Aproveite todos os recursos premium durante o período de experiência. Assine agora para manter o acesso.
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-full bg-amber-600 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-amber-500"
        @click="goPlans"
      >
        Ativar plano
      </button>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Dados</p>
            <h2 class="text-xl font-bold text-slate-900">{{ user?.name }}</h2>
            <p class="text-sm text-slate-600">{{ user?.email }}</p>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">ID {{ user?.id }}</span>
        </div>
        <div class="mt-4 space-y-2 text-sm text-slate-700">
          <p><span class="font-semibold">Ativo:</span> {{ user?.is_active ? "Sim" : "Não" }}</p>
          <p><span class="font-semibold">Plano atual:</span> {{ getPlanLabel(billing?.plan || user?.plan) }}</p>
          <p><span class="font-semibold">Status da assinatura:</span> {{ billingStatusLabel }}</p>
          <p>
            <span class="font-semibold">Validade:</span>
            <span v-if="billing?.valid_until">{{ formatDate(billing.valid_until) }}</span>
            <span v-else>Sem validade definida</span>
          </p>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm space-y-4">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Assinatura</p>
            <h2 class="text-xl font-bold text-slate-900">Gestão de plano</h2>
            <p class="text-sm text-slate-600">Você pode cancelar; o acesso permanece até a data de validade.</p>
          </div>
        </div>
        <div class="flex flex-col gap-3">
          <p class="text-xs text-slate-500">
            Para alterar ou cancelar sua assinatura, fale com a nossa equipe. Você continua com acesso até o fim do período atual.
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              class="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="loading || billing?.status === 'cancelled'"
              @click="cancelSubscription"
            >
              <span v-if="loading">Processando...</span>
              <span v-else-if="billing?.status === 'cancelled'">Assinatura já cancelada</span>
              <span v-else>Solicitar cancelamento</span>
            </button>
            <button
              class="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="goPlans"
            >
              Ver planos disponíveis
            </button>
          </div>
          <p v-if="message" class="text-xs font-semibold text-emerald-600">{{ message }}</p>
          <p v-if="error" class="text-xs font-semibold text-rose-600">{{ error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { getPlanLabel } from "../../utils/planLabels";

interface BillingInfo {
  plan: string;
  status: string;
  valid_until: string | null;
  failed_attempts: number;
  preapproval_id?: string | null;
}

const authStore = useAuthStore();
const router = useRouter();
const user = computed(() => authStore.user);
const billing = ref<BillingInfo | null>(null);
const loading = ref(false);
const message = ref<string | null>(null);
const error = ref<string | null>(null);
const billingStatusLabel = computed(() => {
  const status = billing.value?.status || "indefinido";
  const statusMap: Record<string, string> = {
    active: "Ativa",
    past_due: "Com pendência",
    cancelled: "Cancelada",
    inactive: "Inativa",
    indefinido: "Indefinido"
  };
  return statusMap[status] || status;
});

const formatDate = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleDateString();
};

const loadBilling = async () => {
  try {
    const res = await api.get<BillingInfo>("/billing/me");
    billing.value = res.data;
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível carregar a assinatura.";
  }
};

const cancelSubscription = async () => {
  loading.value = true;
  message.value = null;
  error.value = null;
  try {
    const res = await api.post<BillingInfo>("/billing/cancel");
    billing.value = res.data;
    message.value = "Assinatura cancelada. Acesso mantém até o fim da validade.";
  } catch (err) {
    console.error(err);
    error.value = "Falha ao cancelar assinatura.";
  } finally {
    loading.value = false;
  }
};

const trialInfo = computed(() => {
  if (!user.value?.trial_plan || !user.value?.trial_ends_at) return null;
  return {
    plan: getPlanLabel(user.value.trial_plan),
    endsAt: formatDate(user.value.trial_ends_at)
  };
});

const goPlans = () => {
  router.push("/admin/planos");
};

onMounted(loadBilling);
</script>
