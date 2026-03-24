<template>
  <div class="profile-view space-y-6">
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

    <div class="space-y-4">
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
          <!-- <button
            class="inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            style="background-color: #41ce5f"
            :disabled="!isPaidPlan"
            @click="toggleCardForm"
          >
            <span>{{ showCardForm ? "Fechar formulário" : "Atualizar cartão" }}</span>
          </button>-->

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

      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Dados</p>
            <h2 class="text-xl font-bold text-slate-900">Informações pessoais</h2>
            <p class="text-sm text-slate-600">Revise ou ajuste os dados exibidos no painel.</p>
          </div>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Nome completo
            <input
              v-model="profileForm.name"
              type="text"
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
              placeholder="Seu nome"
            />
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500">
            E-mail
            <input
              v-model="profileForm.email"
              type="email"
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
              placeholder="email@exemplo.com"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            CPF
            <input
              type="text"
              :value="formattedCpf"
              readonly
              disabled
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Telefone
            <input
              v-model="profileForm.whatsapp"
              type="text"
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
              placeholder="(00) 00000-0000"
            />
          </label>
        </div>
        <div class="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            style="background-color: #41ce5f"
            :disabled="profileSaving"
            @click="saveProfile"
          >
            {{ profileSaving ? "Salvando..." : "Salvar dados" }}
          </button>
          <span v-if="profileMessage" class="text-xs font-semibold text-emerald-600">{{ profileMessage }}</span>
          <span v-if="profileError" class="text-xs font-semibold text-rose-600">{{ profileError }}</span>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm space-y-4">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Segurança</p>
          <h2 class="text-xl font-bold text-slate-900">Alterar senha</h2>
          <p class="text-sm text-slate-600">
            A senha precisa ter pelo menos 8 caracteres, conter letras maiúsculas e minúsculas e pelo menos um número.
          </p>
        </div>
        <div class="grid gap-4 md:grid-cols-3">
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Senha atual
            <input
              v-model="passwordForm.current"
              type="password"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="••••••••"
              autocomplete="current-password"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Nova senha
            <input
              v-model="passwordForm.new"
              type="password"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="Nova senha"
              autocomplete="new-password"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Confirmar nova senha
            <input
              v-model="passwordForm.confirm"
              type="password"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="Repita a nova senha"
              autocomplete="new-password"
            />
          </label>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            :disabled="passwordSaving"
            style="background-color: #41ce5f"
            @click="changePassword"
          >
            {{ passwordSaving ? "Alterando..." : "Salvar nova senha" }}
          </button>
          <span v-if="passwordMessage" class="text-xs font-semibold text-emerald-600">{{ passwordMessage }}</span>
          <span v-if="passwordError" class="text-xs font-semibold text-rose-600">{{ passwordError }}</span>
        </div>
      </div>
    </div>

    <div
      v-if="showCancelModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-md rounded-3xl bg-white p-6 text-left shadow-2xl shadow-emerald-900/20">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">Deseja proseguir com o cancelamento?</h3>
          <button class="text-slate-400 transition hover:text-slate-600" @click="closeCancelModal">
            <span class="sr-only">Fechar</span>
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <p class="mt-3 text-sm text-slate-600">
          Vamos continuar o atendimento pelo WhatsApp. Confirme para abrir a conversa com nossa equipe.
        </p>
        <div class="mt-6 flex flex-wrap gap-3">
          <button
            class="inline-flex flex-1 items-center justify-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500"
            @click="confirmCancelContact"
          >
            Falar no WhatsApp
          </button>
          <button
            type="button"
            class="flex-1 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
            @click="closeCancelModal"
          >
            Voltar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, reactive, watch } from "vue";
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
const formattedCpf = computed(() => formatCpf(user.value?.cpf || ""));
const billing = ref<BillingInfo | null>(null);

const message = ref<string | null>(null);
const error = ref<string | null>(null);
const passwordForm = reactive({
  current: "",
  new: "",
  confirm: ""
});
const passwordSaving = ref(false);
const passwordMessage = ref<string | null>(null);
const passwordError = ref<string | null>(null);
const profileForm = reactive({
  name: "",
  email: "",
  whatsapp: ""
});
const profileSaving = ref(false);
const profileMessage = ref<string | null>(null);
const profileError = ref<string | null>(null);

const actionLoading = ref(false);
const showCardForm = ref(false);
const showCancelModal = ref(false);
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
  if (status === "active") return "rounded-full bg-[#3EBD59] px-3 py-1 text-xs font-semibold text-white";
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

function formatCpf(cpf?: string | null) {
  if (!cpf) return "";
  const digits = cpf.replace(/\D/g, "").slice(0, 11);
  if (!digits) return "";
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatPhone(phone?: string | null) {
  if (!phone) return "";
  const digits = phone.replace(/\D/g, "").slice(0, 11);
  if (!digits) return "";
  if (digits.length <= 2) return `(${digits}`;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}


const syncProfileForm = () => {
  profileForm.name = user.value?.name || "";
  profileForm.email = user.value?.email || "";
  profileForm.whatsapp = formatPhone(user.value?.whatsapp || "");
  profileMessage.value = null;
  profileError.value = null;
};

watch(
  () => user.value,
  () => {
    syncProfileForm();
  },
  { immediate: true }
);

watch(
  () => profileForm.whatsapp,
  value => {
    if (value == null) return;
    const formatted = formatPhone(value);
    if (value !== formatted) profileForm.whatsapp = formatted;
  }
);

const loadBilling = async () => {
  try {
    const res = await api.get<BillingInfo>("/billing/me");
    billing.value = res.data;
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível carregar a assinatura.";
  }
};

const cancelSubscription = () => {
  if (!isPaidPlan.value) return;
  showCancelModal.value = true;
};

const closeCancelModal = () => {
  showCancelModal.value = false;
};

const confirmCancelContact = () => {
  const formName = profileForm.name.trim();
  const storedName = (user.value?.name || "").trim();
  const clientName = formName || storedName || "cliente";
  const message =
    "olá , meu nome é : " + clientName + " . Eu gostaria de fazer o cancelamento da minha assinatura";
  const whatsappUrl = `https://wa.me/5553991754616?text=${encodeURIComponent(message)}`;
  window.open(whatsappUrl, "_blank", "noopener");
  showCancelModal.value = false;
};

const toggleCardForm = () => {
  if (!isPaidPlan.value) return;
  showCardForm.value = !showCardForm.value;
  if (!showCardForm.value) resetCardForm();
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

const changePassword = async () => {
  passwordError.value = "";
  passwordMessage.value = "";
  if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
    passwordError.value = "Informe a senha atual e a nova senha duas vezes.";
    return;
  }
  if (passwordForm.new !== passwordForm.confirm) {
    passwordError.value = "As senhas novas precisam coincidir.";
    return;
  }
  passwordSaving.value = true;
  try {
    await api.post("/auth/me/password", {
      current_password: passwordForm.current,
      new_password: passwordForm.new
    });
    passwordMessage.value = "Senha atualizada com sucesso.";
    passwordForm.current = "";
    passwordForm.new = "";
    passwordForm.confirm = "";
  } catch (err) {
    console.error(err);
    passwordError.value = (err as any)?.response?.data?.detail || "Não foi possível alterar a senha.";
  } finally {
    passwordSaving.value = false;
  }
};

const saveProfile = async () => {
  profileError.value = null;
  profileMessage.value = null;
  const name = profileForm.name.trim();
  const email = profileForm.email.trim();
  if (!name || !email) {
    profileError.value = "Informe nome e e-mail.";
    return;
  }
  const phoneDigits = profileForm.whatsapp.replace(/\D/g, "");
  if (phoneDigits && phoneDigits.length < 10) {
    profileError.value = "Informe um telefone válido com DDD.";
    return;
  }
  profileSaving.value = true;
  try {
    await api.put("/auth/me", {
      name,
      email,
      whatsapp: phoneDigits || null
    });
    await authStore.fetchProfile();
    profileMessage.value = "Dados atualizados com sucesso.";
  } catch (err: any) {
    console.error(err);
    profileError.value = err?.response?.data?.detail || "Não foi possível salvar os dados.";
  } finally {
    profileSaving.value = false;
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

<style scoped>
:global(.dark-theme .profile-view input) {
  background-color: #05070f !important;
  color: #f8fafc;
  border-color: rgba(255, 255, 255, 0.15);
}
</style>

