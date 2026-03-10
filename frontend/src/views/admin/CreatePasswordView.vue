<template>
  <div class="flex min-h-screen bg-[#41ce5f] lg:bg-transparent">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-[#41ce5f] lg:flex"
      style="background-color: #41ce5f;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="w-full max-w-[180px]" />
        <h2 class="text-4xl font-bold leading-tight text-white">
          Falta pouco para acessar<br />
          seu painel completo
        </h2>
        <p class="text-lg text-white">
          Crie uma senha segura e finalize seu cadastro para começar a editar páginas, acompanhar métricas e vender mais.
        </p>
        <div class="flex items-center gap-3 text-sm text-white">
          <span class="h-1 w-12 rounded-full bg-white"></span>
          Segurança e praticidade para o seu time.
        </div>
      </div>
    </div>
    <div class="flex w-full flex-col items-center bg-[#41ce5f] px-4 py-10 lg:w-2/5 lg:bg-[#f8f8f8] lg:px-12">
      <div class="mb-8 flex w-full justify-center lg:hidden">
        <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="w-40" />
      </div>
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2 text-center lg:text-left">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Ative seu acesso</p>
          <h1 class="text-3xl font-bold text-slate-900">Crie sua senha</h1>
          <p class="text-sm text-slate-500">
            Defina uma senha para entrar no painel. Essa credencial será usada para logins futuros.
          </p>
          <p
            v-if="session && !sessionError"
            class="text-base font-semibold text-slate-700"
          >
            Olá, {{ session?.name || session?.email }} 👋
          </p>
        </div>
        <div
          v-if="sessionMessage"
          class="mb-4 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-600"
        >
          {{ sessionMessage }}
        </div>
        <form class="space-y-5" @submit.prevent="onSubmit">
          <div>
            <label class="text-sm font-semibold text-slate-600">Senha</label>
            <div class="relative mt-1">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                minlength="8"
                :disabled="isFormDisabled"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 pr-11 focus:border-brand focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600"
                @click="showPassword = !showPassword"
                :disabled="isFormDisabled"
                aria-label="Alternar visualização da senha"
              >
                <svg
                  v-if="!showPassword"
                  class="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                <svg
                  v-else
                  class="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.08 3.17" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              </button>
            </div>
            <p class="mt-1 text-xs text-slate-500">
              Use no mínimo 8 caracteres, com maiúsculas, minúsculas e números.
            </p>
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Confirmar senha</label>
            <div class="relative mt-1">
              <input
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                required
                :disabled="isFormDisabled"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 pr-11 focus:border-brand focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600"
                @click="showConfirmPassword = !showConfirmPassword"
                :disabled="isFormDisabled"
                aria-label="Alternar visualização da confirmação de senha"
              >
                <svg
                  v-if="!showConfirmPassword"
                  class="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                <svg
                  v-else
                  class="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.08 3.17" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              </button>
            </div>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
            <p class="font-semibold text-slate-700">Dica rápida</p>
            <p>Evite senhas óbvias e, se possível, use um gerenciador para guardar com segurança.</p>
          </div>
          <button
            type="submit"
            :disabled="isFormDisabled"
            class="w-full rounded-lg px-4 py-2 font-semibold text-white transition hover:opacity-90"
            :class="isFormDisabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'"
            style="background-color: #41ce5f;"
          >
            {{ isSubmitting ? "Salvando..." : "Salvar senha" }}
          </button>
          <p v-if="formError" class="text-center text-sm text-red-500">{{ formError }}</p>
          <p v-if="success" class="text-center text-sm text-emerald-600">{{ success }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

interface OnboardingSession {
  email: string;
  name?: string | null;
  plan: string;
  cycle: string;
}

const route = useRoute();
const router = useRouter();

const apiBase = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");
const caktoClient = axios.create({
  baseURL: `${apiBase}/api/cakto`
});

const password = ref("");
const confirmPassword = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const formError = ref("");
const success = ref("");
const isSubmitting = ref(false);

const session = ref<OnboardingSession | null>(null);
const isLoadingSession = ref(true);
const sessionError = ref("");

const identifierParams = () => {
  const params: Record<string, string> = {};
  const { order_id, orderId, ref, ref_id, token, subscription_code } = route.query;
  const assign = (key: string, value: unknown) => {
    if (typeof value === "string" && value.trim()) {
      params[key] = value.trim();
    }
  };
  assign("order_id", order_id ?? orderId ?? extractOrderFromReferrer());
  assign("ref_id", ref ?? ref_id ?? extractRefFromReferrer());
  assign("token", token);
  assign("subscription_code", subscription_code);
  return params;
};

const extractOrderFromReferrer = (): string | null => {
  if (typeof document === "undefined") return null;
  const ref = document.referrer || "";
  const match = ref.match(/payment\/status\/([a-f0-9-]+)/i);
  if (match?.[1]) {
    return match[1];
  }
  const idMatch = ref.match(/orders?\/([a-f0-9-]+)/i);
  return idMatch?.[1] ?? null;
};

const extractRefFromReferrer = (): string | null => {
  if (typeof document === "undefined") return null;
  const ref = document.referrer || "";
  const match = ref.match(/refId=([A-Za-z0-9]+)/i);
  return match?.[1] ?? null;
};

const sessionMessage = computed(() => {
  if (isLoadingSession.value) {
    return "Estamos validando seu pedido. Aguarde um instante...";
  }
  if (sessionError.value) {
    return sessionError.value;
  }
  if (session.value) {
    return `Pedido localizado para ${session.value.email}. Plano ${session.value.plan} (${session.value.cycle}).`;
  }
  return "";
});

const isFormDisabled = computed(() => {
  if (isLoadingSession.value || !!sessionError.value || !session.value) {
    return true;
  }
  return isSubmitting.value;
});

const loadSession = async () => {
  const params = identifierParams();
  if (!Object.keys(params).length) {
    sessionError.value = "Não conseguimos identificar seu pedido. Use o link enviado no e-mail de confirmação.";
    isLoadingSession.value = false;
    return;
  }
  try {
    const { data } = await caktoClient.get<OnboardingSession>("/onboarding/session", { params });
    session.value = data;
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    sessionError.value = detail || "Não encontramos o pedido. Verifique o link ou fale com o suporte.";
  } finally {
    isLoadingSession.value = false;
  }
};

onMounted(() => {
  loadSession();
});

const redirectToLogin = () => {
  setTimeout(() => {
    router.push({ name: "login" });
  }, 1500);
};

const onSubmit = () => {
  formError.value = "";
  success.value = "";

  if (isFormDisabled.value) {
    return;
  }

  if (password.value !== confirmPassword.value) {
    formError.value = "As senhas não coincidem. Verifique e tente novamente.";
    return;
  }

  isSubmitting.value = true;
  const params = identifierParams();

  caktoClient
    .post(
      "/onboarding/session/password",
      { password: password.value },
      { params }
    )
    .then(() => {
      success.value = "Senha definida com sucesso! Você já pode acessar o painel.";
      formError.value = "";
      redirectToLogin();
    })
    .catch(err => {
      const detail = err?.response?.data?.detail;
      formError.value = detail || "Não foi possível salvar sua senha. Tente novamente em instantes.";
    })
    .finally(() => {
      isSubmitting.value = false;
    });
};
</script>
