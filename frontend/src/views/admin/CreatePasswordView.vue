<template>
  <div class="min-h-screen bg-[#41ce5f] px-4 py-10 flex items-center justify-center">
    <div class="w-full max-w-2xl">
      <div class="mb-8 flex flex-col items-center text-center text-white">
        <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="mb-4 w-32 drop-shadow-lg" />
        <p class="text-xs font-semibold uppercase tracking-[0.5em] text-white/70">Roteiro Online</p>
        <h1 class="mt-2 text-3xl font-bold">Seja bem-vindo!</h1>
        <p class="mt-2 text-base text-white/85">Vamos finalizar seu cadastro agora mesmo.</p>
      </div>
      <div class="rounded-3xl bg-white/95 p-6 shadow-[0_30px_80px_rgba(0,0,0,0.25)] backdrop-blur md:p-10">
        <transition name="step">
          <div
            v-if="!canSetPassword"
            key="email-step"
            class="rounded-2xl border border-slate-200 bg-white p-6"
          >
            <p class="text-sm font-semibold uppercase tracking-[0.35em] text-slate-500">Passo 1</p>
            <h2 class="mt-1 text-2xl font-bold text-slate-900">Valide seu e-mail</h2>
            <p class="mt-2 text-sm text-slate-500">Digite o e-mail usado na compra e clique em avançar.</p>
            <form class="mt-6 space-y-4" @submit.prevent="onEmailSubmit">
              <div>
                <label class="text-sm font-semibold text-slate-600">E-mail usado na compra</label>
                <input
                  v-model.trim="email"
                  type="email"
                  required
                  :disabled="isValidatingEmail"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-base focus:border-brand focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                  placeholder="voce@agencia.com"
                />
              </div>
              <button
                type="submit"
                class="flex w-full items-center justify-center rounded-xl bg-[#41ce5f] px-4 py-3 text-base font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="isValidatingEmail"
              >
                {{ isValidatingEmail ? "Validando..." : "Avançar" }}
              </button>
            </form>
            <p v-if="manualValidationError" class="mt-3 text-sm text-red-500">{{ manualValidationError }}</p>
          </div>
          <div
            v-else
            key="password-step"
            class="rounded-2xl border border-slate-200 bg-white p-6 space-y-5"
          >
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.5em] text-slate-500">Passo 2</p>
              <h2 class="mt-2 text-3xl font-bold text-slate-900">Olá, {{ identityName }}</h2>
              <p class="mt-2 text-sm text-slate-500">
                Defina uma senha segura para acessar o painel. Assim que concluir, faremos o login automaticamente.
              </p>
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
                    :disabled="isSubmitting"
                    class="w-full rounded-xl border border-slate-200 px-4 py-3 pr-12 focus:border-brand focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                  <button
                    type="button"
                    class="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-slate-600"
                    @click="showPassword = !showPassword"
                    :disabled="isSubmitting"
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
                <p class="mt-1 text-xs text-slate-500">Use pelo menos 8 caracteres com maiúsculas, minúsculas e números.</p>
              </div>
              <div>
                <label class="text-sm font-semibold text-slate-600">Confirmar senha</label>
                <div class="relative mt-1">
                  <input
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    required
                    :disabled="isSubmitting"
                    class="w-full rounded-xl border border-slate-200 px-4 py-3 pr-12 focus:border-brand focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                  <button
                    type="button"
                    class="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-slate-600"
                    @click="showConfirmPassword = !showConfirmPassword"
                    :disabled="isSubmitting"
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
              <button
                type="submit"
                class="w-full rounded-xl bg-[#41ce5f] px-4 py-3 text-base font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="isSubmitting"
              >
                {{ isSubmitting ? "Salvando..." : "Finalizar e acessar" }}
              </button>
              <p v-if="formError" class="text-center text-sm text-red-500">{{ formError }}</p>
              <p v-if="success" class="text-center text-sm text-emerald-600">{{ success }}</p>
            </form>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import {
  fetchOnboardingSession,
  submitManualOnboardingPassword,
  submitOnboardingPassword,
  validateManualOnboardingEmail,
} from "../../services/cakto";
import { useAuthStore } from "../../store/useAuthStore";

interface OnboardingSession {
  email: string;
  name?: string | null;
  plan: string;
  cycle: string;
}

interface ManualValidation {
  email: string;
  name?: string | null;
}

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const password = ref("");
const confirmPassword = ref("");
const email = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const formError = ref("");
const success = ref("");
const isSubmitting = ref(false);

const session = ref<OnboardingSession | null>(null);
const isLoadingSession = ref(true);
const manualValidatedUser = ref<ManualValidation | null>(null);
const manualValidatedEmail = ref("");
const manualValidationError = ref("");
const isValidatingEmail = ref(false);

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

const canSetPassword = computed(() => {
  return !!session.value || !!manualValidatedUser.value;
});

const identityEmail = computed(() => session.value?.email ?? manualValidatedUser.value?.email ?? "");
const identityName = computed(() => session.value?.name ?? manualValidatedUser.value?.name ?? identityEmail.value);

const loadSession = async () => {
  const params = identifierParams();
  if (!Object.keys(params).length) {
    isLoadingSession.value = false;
    return;
  }
  try {
    const { data } = await fetchOnboardingSession(params);
    session.value = data;
    email.value = data.email;
    manualValidationError.value = "";
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    manualValidationError.value =
      detail ||
      "Não encontramos o pedido automaticamente. Valide o e-mail usado na compra para continuar.";
  } finally {
    isLoadingSession.value = false;
  }
};

const resetManualValidation = () => {
  manualValidatedEmail.value = "";
  manualValidatedUser.value = null;
  manualValidationError.value = "";
};

watch(email, newValue => {
  if (session.value) return;
  if (!newValue) {
    manualValidationError.value = "";
  }
  if (!manualValidatedEmail.value) return;
  if (newValue.trim().toLowerCase() !== manualValidatedEmail.value) {
    resetManualValidation();
  }
});

onMounted(() => {
  loadSession();
});

const onEmailSubmit = async () => {
  manualValidationError.value = "";
  if (!email.value.trim()) {
    manualValidationError.value = "Informe o e-mail utilizado na compra.";
    return;
  }
  isValidatingEmail.value = true;
  try {
    const normalized = email.value.trim().toLowerCase();
    const { data } = await validateManualOnboardingEmail({ email: normalized });
    manualValidatedEmail.value = data.email.trim().toLowerCase();
    manualValidatedUser.value = data;
    email.value = data.email;
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    manualValidationError.value = detail || "Não encontramos o cadastro para este e-mail.";
  } finally {
    isValidatingEmail.value = false;
  }
};

const redirectToLogin = () => {
  setTimeout(() => {
    router.push({ name: "login" });
  }, 1500);
};

const autoLogin = async (loginEmail: string) => {
  const formData = new FormData();
  formData.append("username", loginEmail);
  formData.append("password", password.value);
  try {
    const res = await api.post("/auth/login", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    auth.setTokens(res.data.access_token, res.data.refresh_token);
    await auth.fetchProfile();
    router.push("/admin/dashboard");
  } catch (err) {
    console.error("Auto login failed", err);
    success.value = "Senha definida! Você será redirecionado para fazer login.";
    redirectToLogin();
  }
};

const onSubmit = async () => {
  formError.value = "";
  success.value = "";

  if (!canSetPassword.value || isSubmitting.value) {
    return;
  }

  if (password.value !== confirmPassword.value) {
    formError.value = "As senhas não coincidem. Verifique e tente novamente.";
    return;
  }

  const loginEmail = identityEmail.value || email.value.trim().toLowerCase();
  if (!loginEmail) {
    formError.value = "Não conseguimos identificar o usuário. Valide seu e-mail novamente.";
    return;
  }

  isSubmitting.value = true;
  try {
    if (session.value) {
      await submitOnboardingPassword(identifierParams(), { password: password.value });
    } else {
      await submitManualOnboardingPassword({
        email: manualValidatedUser.value?.email || loginEmail,
        password: password.value,
      });
    }
    success.value = "Senha definida com sucesso! Acessando seu painel...";
    await autoLogin(loginEmail);
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    formError.value = detail || "Não foi possível salvar sua senha. Tente novamente em instantes.";
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.step-enter-active,
.step-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.step-enter-from,
.step-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
