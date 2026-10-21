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
        <div v-if="sent" class="space-y-4">
          <p class="rounded-lg bg-emerald-50 px-3 py-3 text-sm font-semibold text-emerald-700">{{ viewCopy.sent }}</p>
          <p class="text-sm text-slate-500">{{ viewCopy.sentHint }}</p>
        </div>
        <form v-else class="space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="text-sm font-semibold text-slate-600" for="forgot-email">{{ viewCopy.emailLabel }}</label>
            <input
              id="forgot-email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full rounded-lg px-4 py-2 font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            style="background-color: #41ce5f;"
          >
            {{ loading ? viewCopy.sending : viewCopy.submit }}
          </button>
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        </form>
        <p class="mt-6 text-center text-sm text-slate-600">
          {{ viewCopy.remembered }}
          <RouterLink to="/login" class="font-semibold transition hover:opacity-80" style="color: #41ce5f;">{{ viewCopy.backToLogin }}</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";
import api from "../../services/api";
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
    eyebrow: t({ pt: "Recuperar acesso", es: "Recuperar acceso" }),
    title: t({ pt: "Esqueci minha senha", es: "Olvidé mi contraseña" }),
    description: t({
      pt: "Informe o e-mail da sua conta e enviaremos um link para você criar uma nova senha.",
      es: "Ingresa el correo de tu cuenta y te enviaremos un enlace para crear una nueva contraseña."
    })
  },
  emailLabel: t({ pt: "E-mail", es: "Correo" }),
  submit: t({ pt: "Enviar link por e-mail", es: "Enviar enlace por correo" }),
  sending: t({ pt: "Enviando...", es: "Enviando..." }),
  sent: t({
    pt: "Se o e-mail estiver cadastrado, o link de redefinição já está a caminho.",
    es: "Si el correo está registrado, el enlace de restablecimiento ya está en camino."
  }),
  sentHint: t({
    pt: "O link vale por 60 minutos. Se não encontrar, olhe a caixa de spam.",
    es: "El enlace vale por 60 minutos. Si no lo encuentras, revisa la carpeta de spam."
  }),
  remembered: t({ pt: "Lembrou a senha?", es: "¿Recordaste la contraseña?" }),
  backToLogin: t({ pt: "Voltar para o login", es: "Volver al inicio de sesión" }),
  failure: t({
    pt: "Não foi possível enviar agora. Tente novamente em instantes.",
    es: "No fue posible enviar ahora. Inténtalo de nuevo en unos instantes."
  })
};

const email = ref("");
const loading = ref(false);
const sent = ref(false);
const error = ref("");

const onSubmit = async () => {
  loading.value = true;
  error.value = "";
  try {
    await api.post("/auth/password/forgot", { email: email.value.trim().toLowerCase() });
    sent.value = true;
  } catch (err) {
    console.error(err);
    error.value = viewCopy.failure;
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
