<template>
  <div class="min-h-screen bg-[#41ce5f] px-4 py-10">
    <div class="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center">
      <div class="mb-8 flex flex-col items-center text-center text-white">
        <img
          src="../../assets/Logo Branco - Roteiro Online.png"
          :alt="viewCopy.brand.alt"
          class="mb-6 w-32 drop-shadow-lg"
        />
        <h1 class="text-4xl font-bold">{{ viewCopy.hero.title }}</h1>
        <p class="mt-2 text-lg text-white/90">{{ viewCopy.hero.description }}</p>
      </div>

      <div class="w-full rounded-3xl bg-white p-6 shadow-[0_30px_80px_rgba(0,0,0,0.18)] md:p-8">
        <transition name="step" mode="out-in">
          <div v-if="!canSetPassword" key="email-step">
            <p class="text-sm font-semibold uppercase tracking-[0.35em] text-slate-500">
              {{ viewCopy.emailStep.badge }}
            </p>
            <h2 class="mt-1 text-2xl font-bold text-slate-900">{{ viewCopy.emailStep.title }}</h2>
            <p class="mt-2 text-sm text-slate-500">
              {{ viewCopy.emailStep.description }}
            </p>

            <form class="mt-6 space-y-4" @submit.prevent="onEmailSubmit">
              <div>
                <label class="text-sm font-semibold text-slate-600">{{ viewCopy.emailStep.label }}</label>
                <input
                  v-model.trim="email"
                  type="email"
                  required
                  :disabled="isValidatingEmail"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 text-base focus:border-[#41ce5f] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                  :placeholder="viewCopy.emailStep.placeholder"
                />
              </div>

              <button
                type="submit"
                class="flex w-full items-center justify-center rounded-xl bg-[#41ce5f] px-4 py-3 text-base font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="isValidatingEmail"
              >
                {{ isValidatingEmail ? viewCopy.emailStep.buttonLoading : viewCopy.emailStep.buttonSubmit }}
              </button>
            </form>

            <p v-if="manualValidationError" class="mt-3 text-sm text-red-500">
              {{ manualValidationError }}
            </p>
          </div>

          <div v-else key="password-step" class="space-y-5">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.5em] text-slate-500">
                {{ viewCopy.passwordStep.badge }}
              </p>
              <h2 class="mt-2 text-3xl font-bold text-slate-900">
                {{ viewCopy.passwordStep.greeting(identityName) }}
              </h2>
              <p class="mt-2 text-sm text-slate-500">
                {{ viewCopy.passwordStep.description }}
              </p>
            </div>

            <form class="space-y-5" @submit.prevent="onSubmit">
              <div>
                <label class="text-sm font-semibold text-slate-600">{{ viewCopy.passwordForm.passwordLabel }}</label>
                <div class="relative mt-1">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    minlength="8"
                    :disabled="isSubmitting"
                    class="w-full rounded-xl border border-slate-200 px-4 py-3 pr-12 focus:border-[#41ce5f] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                  <button
                    type="button"
                    class="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-slate-600"
                    @click="showPassword = !showPassword"
                    :disabled="isSubmitting"
                    :aria-label="viewCopy.passwordForm.togglePasswordAria"
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
                  {{ viewCopy.passwordForm.helper }}
                </p>
              </div>

              <div>
                <label class="text-sm font-semibold text-slate-600">{{ viewCopy.passwordForm.confirmLabel }}</label>
                <div class="relative mt-1">
                  <input
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    required
                    :disabled="isSubmitting"
                    class="w-full rounded-xl border border-slate-200 px-4 py-3 pr-12 focus:border-[#41ce5f] focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                  <button
                    type="button"
                    class="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-slate-600"
                    @click="showConfirmPassword = !showConfirmPassword"
                    :disabled="isSubmitting"
                    :aria-label="viewCopy.passwordForm.toggleConfirmAria"
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
                {{ isSubmitting ? viewCopy.passwordForm.submitSaving : viewCopy.passwordForm.submitLabel }}
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
  validateManualOnboardingEmail
} from "../../services/cakto";
import { useAuthStore } from "../../store/useAuthStore";
import { createAdminLocalizer } from "../../utils/adminI18n";

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
const t = createAdminLocalizer();

const viewCopy = {
  brand: {
    alt: t({ pt: "Roteiro Online", es: "Roteiro Online" })
  },
  hero: {
    title: t({ pt: "Seja bem-vindo!", es: "¡Bienvenido!" }),
    description: t({ pt: "Vamos finalizar seu cadastro agora mesmo.", es: "Terminemos tu registro ahora mismo." })
  },
  emailStep: {
    badge: t({ pt: "Passo 1", es: "Paso 1" }),
    title: t({ pt: "Valide seu e-mail", es: "Verifica tu correo" }),
    description: t({
      pt: "Digite o e-mail usado na compra e clique em avançar.",
      es: "Ingresa el correo usado en la compra y haz clic en avanzar."
    }),
    label: t({ pt: "E-mail usado na compra", es: "Correo usado en la compra" }),
    placeholder: t({ pt: "voce@agencia.com", es: "tu@agencia.com" }),
    buttonLoading: t({ pt: "Validando...", es: "Validando..." }),
    buttonSubmit: t({ pt: "Avançar", es: "Avanzar" })
  },
  passwordStep: {
    badge: t({ pt: "Passo 2", es: "Paso 2" }),
    greeting: (name: string) => t({ pt: `Olá, ${name}`, es: `Hola, ${name}` }),
    description: t({
      pt: "Defina uma senha segura para acessar o painel. Assim que concluir, faremos o login automaticamente.",
      es: "Crea una contraseña segura para acceder al panel. Al finalizar, iniciaremos sesión automáticamente."
    })
  },
  passwordForm: {
    passwordLabel: t({ pt: "Senha", es: "Contraseña" }),
    helper: t({
      pt: "Use pelo menos 8 caracteres com maiúsculas, minúsculas e números.",
      es: "Usa al menos 8 caracteres con mayúsculas, minúsculas y números."
    }),
    confirmLabel: t({ pt: "Confirmar senha", es: "Confirmar contraseña" }),
    togglePasswordAria: t({
      pt: "Alternar visualização da senha",
      es: "Alternar visualización de la contraseña"
    }),
    toggleConfirmAria: t({
      pt: "Alternar visualização da confirmação de senha",
      es: "Alternar visualización de la confirmación de contraseña"
    }),
    submitSaving: t({ pt: "Salvando...", es: "Guardando..." }),
    submitLabel: t({ pt: "Finalizar e acessar", es: "Finalizar y acceder" })
  },
  feedback: {
    sessionNotFound: t({
      pt: "Não encontramos o pedido automaticamente. Valide o e-mail usado na compra para continuar.",
      es: "No encontramos el pedido automáticamente. Valida el correo usado en la compra para continuar."
    }),
    emailRequired: t({ pt: "Informe o e-mail utilizado na compra.", es: "Ingresa el correo utilizado en la compra." }),
    emailNotFound: t({ pt: "Não encontramos o cadastro para este e-mail.", es: "No encontramos un registro para este correo." }),
    passwordRequirements: t({
      pt: "A senha deve ter pelo menos 8 caracteres, com letra maiúscula, minúscula e número.",
      es: "La contraseña debe tener al menos 8 caracteres, con mayúsculas, minúsculas y números."
    }),
    passwordMismatch: t({
      pt: "As senhas não coincidem. Verifique e tente novamente.",
      es: "Las contraseñas no coinciden. Verifica e intenta de nuevo."
    }),
    userNotIdentified: t({
      pt: "Não conseguimos identificar o usuário. Valide seu e-mail novamente.",
      es: "No pudimos identificar al usuario. Valida tu correo nuevamente."
    }),
    success: t({
      pt: "Senha definida com sucesso! Acessando seu painel...",
      es: "Contraseña definida con éxito. Accediendo a tu panel..."
    }),
    redirecting: t({
      pt: "Senha definida! Você será redirecionado para fazer login.",
      es: "Contraseña definida. Serás redirigido para iniciar sesión."
    }),
    saveError: t({
      pt: "Não foi possível salvar sua senha. Tente novamente em instantes.",
      es: "No fue posible guardar tu contraseña. Inténtalo nuevamente en instantes."
    })
  }
};

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

const extractOrderFromReferrer = (): string | null => {
  if (typeof document === "undefined") return null;
  const referrer = document.referrer || "";
  const match = referrer.match(/payment\/status\/([a-f0-9-]+)/i);
  if (match?.[1]) return match[1];

  const idMatch = referrer.match(/orders?\/([a-f0-9-]+)/i);
  return idMatch?.[1] ?? null;
};

const extractRefFromReferrer = (): string | null => {
  if (typeof document === "undefined") return null;
  const referrer = document.referrer || "";
  const match = referrer.match(/refId=([A-Za-z0-9]+)/i);
  return match?.[1] ?? null;
};

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

const canSetPassword = computed(() => !!session.value || !!manualValidatedUser.value);

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
    manualValidationError.value = detail || viewCopy.feedback.sessionNotFound;
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
    manualValidationError.value = viewCopy.feedback.emailRequired;
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
    manualValidationError.value = detail || viewCopy.feedback.emailNotFound;
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
      headers: { "Content-Type": "multipart/form-data" }
    });

    auth.setTokens(res.data.access_token, res.data.refresh_token);
    await auth.fetchProfile();
    router.push("/admin/dashboard");
  } catch (err) {
    console.error("Auto login failed", err);
    success.value = viewCopy.feedback.redirecting;
    redirectToLogin();
  }
};

const isStrongPassword = (value: string) => {
  return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(value);
};

const onSubmit = async () => {
  formError.value = "";
  success.value = "";

  if (!canSetPassword.value || isSubmitting.value) return;

  if (!isStrongPassword(password.value)) {
    formError.value = viewCopy.feedback.passwordRequirements;
    return;
  }

  if (password.value !== confirmPassword.value) {
    formError.value = viewCopy.feedback.passwordMismatch;
    return;
  }

  const loginEmail = identityEmail.value || email.value.trim().toLowerCase();

  if (!loginEmail) {
    formError.value = viewCopy.feedback.userNotIdentified;
    return;
  }

  isSubmitting.value = true;

  try {
    if (session.value) {
      await submitOnboardingPassword(identifierParams(), { password: password.value });
    } else {
      await submitManualOnboardingPassword({
        email: manualValidatedUser.value?.email || loginEmail,
        password: password.value
      });
    }

    success.value = viewCopy.feedback.success;
    await autoLogin(loginEmail);
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    formError.value = detail || viewCopy.feedback.saveError;
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
