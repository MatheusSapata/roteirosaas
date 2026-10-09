<template>
  <div class="auth-view min-h-screen bg-[#41ce5f] px-4 py-10">
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
          <div v-if="isLoadingSession" key="loading-step" class="py-6 text-center text-sm text-slate-500">
            {{ viewCopy.loading }}
          </div>

          <div v-else-if="!canSetPassword" key="invalid-step">
            <h2 class="text-2xl font-bold text-slate-900">{{ viewCopy.invalidLink.title }}</h2>
            <p class="mt-2 text-sm text-slate-500">
              {{ viewCopy.invalidLink.description }}
            </p>
            <p v-if="sessionError" class="mt-3 text-sm text-red-500">
              {{ sessionError }}
            </p>
            <RouterLink
              :to="{ name: 'forgot-password' }"
              class="mt-6 flex w-full items-center justify-center rounded-xl bg-[#41ce5f] px-4 py-3 text-base font-semibold text-white transition hover:brightness-110"
            >
              {{ viewCopy.invalidLink.button }}
            </RouterLink>
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
                    <EyeIcon v-if="!showPassword" class="h-5 w-5" aria-hidden="true" />
                    <EyeOffIcon v-else class="h-5 w-5" aria-hidden="true" />
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
                    <EyeIcon v-if="!showConfirmPassword" class="h-5 w-5" aria-hidden="true" />
                    <EyeOffIcon v-else class="h-5 w-5" aria-hidden="true" />
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
import { EyeIcon, EyeOffIcon } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { fetchOnboardingSession, submitOnboardingPassword } from "../../services/cakto";
import { useAuthStore } from "../../store/useAuthStore";
import { createAdminLocalizer } from "../../utils/adminI18n";

interface OnboardingSession {
  email: string;
  name?: string | null;
  plan: string;
  cycle: string;
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
  loading: t({ pt: "Carregando seu pedido...", es: "Cargando tu pedido..." }),
  invalidLink: {
    title: t({ pt: "Link inválido ou expirado", es: "Enlace inválido o vencido" }),
    description: t({
      pt: "Este link de criação de senha não é mais válido. Para acessar o painel, defina uma nova senha pela opção Esqueci minha senha.",
      es: "Este enlace para crear la contraseña ya no es válido. Para acceder al panel, define una nueva contraseña con la opción Olvidé mi contraseña."
    }),
    button: t({ pt: "Ir para Esqueci minha senha", es: "Ir a Olvidé mi contraseña" })
  },
  passwordStep: {
    badge: t({ pt: "Último passo", es: "Último paso" }),
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
    passwordRequirements: t({
      pt: "A senha deve ter pelo menos 8 caracteres, com letra maiúscula, minúscula e número.",
      es: "La contraseña debe tener al menos 8 caracteres, con mayúsculas, minúsculas y números."
    }),
    passwordMismatch: t({
      pt: "As senhas não coincidem. Verifique e tente novamente.",
      es: "Las contraseñas no coinciden. Verifica e intenta de nuevo."
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
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const formError = ref("");
const success = ref("");
const isSubmitting = ref(false);

const session = ref<OnboardingSession | null>(null);
const isLoadingSession = ref(true);
const sessionError = ref("");

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

const canSetPassword = computed(() => !!session.value);

const identityEmail = computed(() => session.value?.email ?? "");

const identityName = computed(() => session.value?.name || identityEmail.value);

const loadSession = async () => {
  const params = identifierParams();

  if (!Object.keys(params).length) {
    isLoadingSession.value = false;
    return;
  }

  try {
    const { data } = await fetchOnboardingSession(params);
    session.value = data;
    sessionError.value = "";
  } catch (err: any) {
    sessionError.value = err?.response?.data?.detail || "";
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

  const loginEmail = identityEmail.value;

  isSubmitting.value = true;

  try {
    await submitOnboardingPassword(identifierParams(), { password: password.value });

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

<style scoped>
.auth-view :deep(.bg-white), .auth-view :deep(.bg-white\/95) { background: var(--card) !important; }
.auth-view :deep(.border-slate-200), .auth-view :deep(.border-slate-300) { border-color: var(--border) !important; }
.auth-view :deep(.text-slate-900), .auth-view :deep(.text-slate-700) { color: var(--foreground) !important; }
.auth-view :deep(.text-slate-600), .auth-view :deep(.text-slate-500) { color: var(--muted-foreground) !important; }
.auth-view :deep(input) { border-color: var(--input) !important; background: var(--background) !important; color: var(--foreground) !important; }
</style>
