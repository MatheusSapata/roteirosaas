<template>
  <div class="auth-view flex min-h-screen bg-[#41ce5f] lg:bg-transparent">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-[#41ce5f] lg:flex"
      style="background-color: #41ce5f;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <img src="../../assets/Logo Branco - Roteiro Online.png" :alt="viewCopy.brandAlt" class="w-full max-w-[180px]" />
        <h2 class="text-4xl font-bold leading-tight text-white" v-html="viewCopy.hero.headline"></h2>
        <p class="text-lg text-white">{{ viewCopy.hero.description }}</p>
        <div class="flex items-center gap-3 text-sm text-white">
          <span class="h-1 w-12 rounded-full bg-white"></span>
          {{ viewCopy.hero.caption }}
        </div>
      </div>
    </div>
    <div
      class="flex w-full flex-col items-center bg-[#41ce5f] px-4 py-10 lg:min-h-screen lg:w-2/5 lg:justify-center lg:bg-[#f8f8f8] lg:px-12"
    >
      <div class="mb-8 flex w-full justify-center lg:hidden">
        <img src="../../assets/Logo Branco - Roteiro Online.png" :alt="viewCopy.brandAlt" class="w-32" />
      </div>
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.card.eyebrow }}</p>
          <h1 class="text-3xl font-bold text-slate-900">{{ viewCopy.card.title }}</h1>
          <p class="text-sm text-slate-500">{{ viewCopy.card.description }}</p>
        </div>
        <div v-if="done" class="space-y-4">
          <p class="rounded-lg bg-emerald-50 px-3 py-3 text-sm font-semibold text-emerald-700">{{ viewCopy.success }}</p>
          <RouterLink
            to="/login"
            class="block w-full rounded-lg px-4 py-2 text-center font-semibold text-white transition hover:opacity-90"
            style="background-color: #41ce5f;"
          >
            {{ viewCopy.goLogin }}
          </RouterLink>
        </div>
        <form v-else class="space-y-4" @submit.prevent="onSubmit">
          <div v-if="!tokenFromLink">
            <label class="text-sm font-semibold text-slate-600" for="reset-token">{{ viewCopy.tokenLabel }}</label>
            <input
              id="reset-token"
              v-model="token"
              required
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-sm focus:border-brand focus:outline-none"
              :placeholder="viewCopy.tokenPlaceholder"
            />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600" for="reset-password">{{ viewCopy.passwordLabel }}</label>
            <input
              id="reset-password"
              v-model="password"
              type="password"
              required
              autocomplete="new-password"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            />
            <PasswordRequirements :password="password" />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600" for="reset-confirm">{{ viewCopy.confirmLabel }}</label>
            <input
              id="reset-confirm"
              v-model="confirmPassword"
              type="password"
              required
              autocomplete="new-password"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            />
          </div>
          <button
            type="submit"
            :disabled="loading || !passwordValid || password !== confirmPassword"
            class="w-full rounded-lg px-4 py-2 font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            style="background-color: #41ce5f;"
          >
            {{ loading ? viewCopy.saving : viewCopy.submit }}
          </button>
          <p v-if="error" class="text-sm text-red-500">
            {{ error }}
            <RouterLink to="/forgot-password" class="font-semibold" style="color: #41ce5f;">{{ viewCopy.askAgain }}</RouterLink>
          </p>
        </form>
        <p v-if="!done" class="mt-6 text-center text-sm text-slate-600">
          <RouterLink to="/login" class="font-semibold transition hover:opacity-80" style="color: #41ce5f;">{{ viewCopy.backToLogin }}</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import api from "../../services/api";
import PasswordRequirements from "../../components/forms/PasswordRequirements.vue";
import { createAdminLocalizer } from "../../utils/adminI18n";

const t = createAdminLocalizer();

const viewCopy = {
  brandAlt: t({ pt: "Roteiro Online", es: "Roteiro Online" }),
  hero: {
    headline: t({
      pt: "Mais organização<br>Mais profissionalismo<br>Mais vendas",
      es: "Más organización<br>Más profesionalismo<br>Más ventas"
    }),
    description: t({
      pt: "Acesse seus roteiros, edite informações, acompanhe acessos e mantenha tudo organizado para vender melhor.",
      es: "Accede a tus itinerarios, edita información, sigue los accesos y mantén todo organizado para vender más."
    }),
    caption: t({
      pt: "Seu painel disponível sempre que você precisar.",
      es: "Tu panel disponible siempre que lo necesites."
    })
  },
  card: {
    eyebrow: t({ pt: "Redefinir senha", es: "Restablecer contraseña" }),
    title: t({ pt: "Criar nova senha", es: "Crear nueva contraseña" }),
    description: t({
      pt: "Escolha uma senha nova para voltar ao painel.",
      es: "Elige una contraseña nueva para volver al panel."
    })
  },
  tokenLabel: t({ pt: "Código do link", es: "Código del enlace" }),
  tokenPlaceholder: t({ pt: "Cole aqui o código recebido por e-mail", es: "Pega aquí el código recibido por correo" }),
  passwordLabel: t({ pt: "Nova senha", es: "Nueva contraseña" }),
  confirmLabel: t({ pt: "Confirmar nova senha", es: "Confirmar nueva contraseña" }),
  submit: t({ pt: "Salvar nova senha", es: "Guardar nueva contraseña" }),
  saving: t({ pt: "Salvando...", es: "Guardando..." }),
  success: t({
    pt: "Senha atualizada com sucesso! Agora você já pode entrar.",
    es: "¡Contraseña actualizada con éxito! Ya puedes ingresar."
  }),
  goLogin: t({ pt: "Ir para o login", es: "Ir al inicio de sesión" }),
  backToLogin: t({ pt: "Voltar para o login", es: "Volver al inicio de sesión" }),
  askAgain: t({ pt: "Pedir um novo link", es: "Pedir un nuevo enlace" }),
  failure: t({
    pt: "Não foi possível atualizar a senha. O link pode ter expirado.",
    es: "No fue posible actualizar la contraseña. El enlace puede haber expirado."
  })
};

const route = useRoute();
const token = ref<string>((route.query.token as string) || "");
const tokenFromLink = computed(() => Boolean(route.query.token));
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref("");
const done = ref(false);

const passwordCriteria = computed(() => ({
  length: password.value.length >= 8,
  uppercase: /[A-Z]/.test(password.value),
  lowercase: /[a-z]/.test(password.value),
  number: /\d/.test(password.value)
}));
const passwordValid = computed(() => Object.values(passwordCriteria.value).every(Boolean));

const onSubmit = async () => {
  if (!passwordValid.value || password.value !== confirmPassword.value) return;
  loading.value = true;
  error.value = "";
  try {
    await api.post("/auth/password/reset", { token: token.value.trim(), password: password.value });
    done.value = true;
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || viewCopy.failure;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-view { color: var(--foreground); }
.auth-view :deep(.bg-white) { background: var(--card) !important; }
.auth-view :deep(.border-slate-200),
.auth-view :deep(.border-slate-300) { border-color: var(--border) !important; }
.auth-view :deep(.text-slate-900),
.auth-view :deep(.text-slate-700) { color: var(--foreground) !important; }
.auth-view :deep(.text-slate-600),
.auth-view :deep(.text-slate-500) { color: var(--muted-foreground) !important; }
.auth-view :deep(input) { border-color: var(--input) !important; background: var(--background) !important; color: var(--foreground) !important; }
.auth-view :deep(input:focus) { border-color: var(--ring) !important; box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent) !important; }
</style>
