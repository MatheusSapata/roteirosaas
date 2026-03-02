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
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Assinatura</p>
            <h2 class="text-xl font-bold text-slate-900">Gestão do meu plano</h2>
            <p class="text-sm text-slate-600">Atualize o cartão ou encerre a renovação quando precisar.</p>
          </div>
          <button
            class="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
            @click="goPlans"
          >
            Ver planos disponíveis
          </button>
        </div>

        <div class="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <span :class="statusBadgeClass">{{ billingStatusLabel }}</span>
          <span class="font-semibold text-slate-900">{{ currentPlanLabel }}</span>
          <span v-if="billing?.valid_until">Válido até {{ formatDate(billing?.valid_until) }}</span>
          <span class="text-xs uppercase tracking-[0.2em] text-slate-400">
            {{ billingCycleLabel }}
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <button
            class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 disabled:opacity-60"
            :disabled="!isPaidPlan"
            @click="toggleCardForm"
          >
            <span>{{ showCardForm ? "Fechar formulário" : "Atualizar cartão" }}</span>
          </button>
          <a
            href="#"
            class="text-xs font-semibold text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline"
            :class="{ 'pointer-events-none opacity-40': !isPaidPlan || actionLoading }"
            @click.prevent="cancelSubscription"
          >
            Cancelar renovação
          </a>
        </div>

        <div
          v-if="showCardForm"
          class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm text-slate-700"
        >
          <p class="mb-3 text-xs text-slate-500">
            Nenhuma cobrança será feita agora. O novo cartão será usado automaticamente na próxima renovação.
          </p>
          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-1 text-xs font-semibold">
              Nome impresso
              <input
                v-model="cardForm.holderName"
                type="text"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                placeholder="Nome completo"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold">
              Número do cartão
              <input
                v-model="cardForm.number"
                type="text"
                inputmode="numeric"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                placeholder="0000 0000 0000 0000"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold">
              Mês de validade
              <input
                v-model="cardForm.expiryMonth"
                type="text"
                inputmode="numeric"
                maxlength="2"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                placeholder="MM"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold">
              Ano de validade
              <input
                v-model="cardForm.expiryYear"
                type="text"
                inputmode="numeric"
                maxlength="4"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                placeholder="AAAA"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold">
              Código de segurança
              <input
                v-model="cardForm.ccv"
                type="text"
                inputmode="numeric"
                maxlength="4"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                placeholder="CVV"
              />
            </label>
          </div>
          <div class="mt-4 flex flex-wrap gap-3">
            <button
              class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 disabled:opacity-60"
              :disabled="cardSubmitting"
              @click="submitCardUpdate"
            >
              <span v-if="cardSubmitting">Enviando...</span>
              <span v-else>Salvar novo cartão</span>
            </button>
            <button
              type="button"
              class="text-xs font-semibold text-slate-500 hover:text-slate-700"
              @click="resetCardForm"
            >
              Limpar campos
            </button>
          </div>
        </div>

        <p class="text-xs text-slate-500">
          Você manterá o acesso até o fim do período pago mesmo após cancelar ou voltar ao plano gratuito.
        </p>

        <p v-if="message" class="text-xs font-semibold text-emerald-600">{{ message }}</p>
        <p v-if="error" class="text-xs font-semibold text-rose-600">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, reactive } from "vue";
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
  billing_cycle?: string | null;
}

const authStore = useAuthStore();
const router = useRouter();
const user = computed(() => authStore.user);
const billing = ref<BillingInfo | null>(null);
const message = ref<string | null>(null);
const error = ref<string | null>(null);
const actionLoading = ref(false);
const showCardForm = ref(false);
const cardSubmitting = ref(false);
const cardForm = reactive({
  holderName: "",
  number: "",
  expiryMonth: "",
  expiryYear: "",
  ccv: ""
});
const billingStatusLabel = computed(() => {
  const status = billing.value?.status || "inactive";
  const statusMap: Record<string, string> = {
    active: "Ativa",
    past_due: "Pagamento pendente",
    cancelled: "Cancelada",
    cancel_at_period_end: "Cancela no fim do ciclo",
    pending: "Aguardando pagamento",
    inactive: "Inativa"
  };
  return statusMap[status] || status;
});
const statusBadgeClass = computed(() => {
  const status = billing.value?.status || "inactive";
  if (status === "active") return "rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700";
  if (status === "cancel_at_period_end")
    return "rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700";
  if (status === "past_due") return "rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700";
  if (status === "cancelled") return "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600";
  return "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500";
});
const billingCycleLabel = computed(() => {
  const cycle = billing.value?.billing_cycle;
  if (cycle === "annual") return "Plano anual";
  if (cycle === "monthly") return "Plano mensal";
  return "Ciclo padrão";
});
const currentPlanLabel = computed(() => getPlanLabel(billing.value?.plan || user.value?.plan));
const isPaidPlan = computed(() => {
  const plan = billing.value?.plan || user.value?.plan;
  return !!plan && plan !== "free";
});

const formatDate = (iso?: string | null) => {
  if (!iso) return "";
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
  if (!isPaidPlan.value) return;
  const confirmCancel = window.confirm("Cancelar a renovação? Você manterá o acesso até o fim do ciclo atual.");
  if (!confirmCancel) return;
  actionLoading.value = true;
  message.value = null;
  error.value = null;
  try {
    const res = await api.post<BillingInfo>("/billing/cancel");
    billing.value = res.data;
    message.value = "Renovação cancelada. Acesso mantido até o fim do ciclo pago.";
  } catch (err) {
    console.error(err);
    error.value = "Falha ao cancelar assinatura.";
  } finally {
    actionLoading.value = false;
  }
};

const toggleCardForm = () => {
  if (!isPaidPlan.value) return;
  showCardForm.value = !showCardForm.value;
  if (!showCardForm.value) {
    resetCardForm();
  }
};

const resetCardForm = () => {
  cardForm.holderName = "";
  cardForm.number = "";
  cardForm.expiryMonth = "";
  cardForm.expiryYear = "";
  cardForm.ccv = "";
};

const submitCardUpdate = async () => {
  if (!isPaidPlan.value) return;
  if (!cardForm.holderName || !cardForm.number || !cardForm.expiryMonth || !cardForm.expiryYear || !cardForm.ccv) {
    error.value = "Preencha todos os campos do cartão.";
    return;
  }
  cardSubmitting.value = true;
  message.value = null;
  error.value = null;
  try {
    await api.post("/billing/update-card", {
      holder_name: cardForm.holderName,
      number: cardForm.number.replace(/\s+/g, ""),
      expiry_month: cardForm.expiryMonth,
      expiry_year: cardForm.expiryYear,
      ccv: cardForm.ccv
    });
    message.value = "Cartão atualizado com sucesso. Ele será usado na próxima renovação.";
    showCardForm.value = false;
    resetCardForm();
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível atualizar o cartão. Verifique os dados e tente novamente.";
  } finally {
    cardSubmitting.value = false;
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
