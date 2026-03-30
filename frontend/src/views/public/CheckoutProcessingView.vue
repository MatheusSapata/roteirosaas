<template>
  <div class="flex min-h-screen items-center justify-center bg-[#41ce5f] px-4">
    <div class="w-full max-w-md rounded-3xl bg-white/95 p-8 text-center shadow-2xl shadow-emerald-900/30">
      <img src="../../assets/Logo Cor - Roteiro Online.png" :alt="viewCopy.brand.alt" class="mx-auto mb-6 w-32" />

      <h1 class="text-2xl font-bold text-slate-900">{{ viewCopy.heading }}</h1>

      <p class="mt-3 text-sm text-slate-600">
        {{ statusMessage }}
      </p>

      <div class="mt-6 flex justify-center">
        <span class="h-16 w-16 animate-spin rounded-full border-4 border-emerald-200 border-t-white"></span>
      </div>

      <p class="mt-6 text-sm font-medium text-slate-700">
        {{ viewCopy.redirectInfo }}
      </p>

      <p v-if="!orderIdFound" class="mt-2 text-xs text-amber-600">
        {{ viewCopy.fallbackInfo }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AxiosError } from "axios";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CHECKOUT_SESSION_STORAGE_KEY, getCheckoutSessionStatus } from "../../services/cakto";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";

const router = useRouter();
const route = useRoute();
const t = createLocalizer(getCurrentLanguage());

const viewCopy = {
  brand: {
    alt: t({ pt: "Roteiro Online", es: "Roteiro Online" })
  },
  heading: t({ pt: "Processando seu acesso", es: "Procesando tu acceso" }),
  waiting: t({ pt: "Estamos finalizando tudo para você...", es: "Estamos finalizando todo para ti..." }),
  noToken: t({
    pt: "Não conseguimos identificar sua compra. Use o link do e-mail de confirmação.",
    es: "No pudimos identificar tu compra. Usa el enlace del correo de confirmación."
  }),
  finalized: t({
    pt: "O pagamento foi confirmado, mas ainda estamos finalizando seu acesso.",
    es: "El pago fue confirmado, pero aún estamos finalizando tu acceso."
  }),
  error: t({
    pt: "Não conseguimos confirmar seu pedido. Use o link enviado por e-mail.",
    es: "No pudimos confirmar tu pedido. Usa el enlace enviado por correo."
  }),
  redirectInfo: t({
    pt: "Em instantes você será levado para definir sua senha de acesso.",
    es: "En instantes te llevaremos para definir tu contraseña de acceso."
  }),
  fallbackInfo: t({
    pt: "Caso o redirecionamento não aconteça, use o link do e-mail de confirmação.",
    es: "Si el redireccionamiento no ocurre, utiliza el enlace del correo de confirmación."
  })
} as const;

const sessionToken = ref<string | null>(null);
const statusMessage = ref(viewCopy.waiting);
const hasError = ref(false);
const orderIdFound = computed(() => !!sessionToken.value);

let fallbackTimer: number | null = null;

const redirectToLogin = () => {
  localStorage.removeItem(CHECKOUT_SESSION_STORAGE_KEY);
  router.replace({
    name: "login",
    query: { checkout: "success" },
  });
};

onMounted(() => {
  const stored = localStorage.getItem(CHECKOUT_SESSION_STORAGE_KEY);

  const queryToken =
    (typeof route.query.sck === "string" && route.query.sck.trim()) ||
    (typeof route.query.token === "string" && route.query.token.trim()) ||
    null;

  const effectiveToken = stored || queryToken;

  if (effectiveToken) {
    sessionToken.value = effectiveToken;

    if (!stored && queryToken) {
      localStorage.setItem(CHECKOUT_SESSION_STORAGE_KEY, queryToken);
    }

    pollStatus();
  } else {
    hasError.value = true;
    statusMessage.value = viewCopy.noToken;
  }

  fallbackTimer = window.setTimeout(() => {
    router.replace({ name: "create-password" });
  }, 5000);
});

onUnmounted(() => {
  if (fallbackTimer) {
    clearTimeout(fallbackTimer);
    fallbackTimer = null;
  }
});

const pollStatus = async (attempt = 0) => {
  if (!sessionToken.value) return;

  try {
    const { data } = await getCheckoutSessionStatus(sessionToken.value);

    if (data.status === "ready") {
      localStorage.removeItem(CHECKOUT_SESSION_STORAGE_KEY);

      if (fallbackTimer) {
        clearTimeout(fallbackTimer);
        fallbackTimer = null;
      }

      if (data.redirect_token) {
        router.replace({
          name: "create-password",
          query: { token: data.redirect_token },
        });
      } else {
        redirectToLogin();
      }
      return;
    }

    if (attempt >= 10) {
      statusMessage.value = viewCopy.finalized;
      return;
    }

    setTimeout(() => pollStatus(attempt + 1), 2000);
  } catch (err) {
    console.error(err);
    const status = (err as AxiosError)?.response?.status;
    if (status === 404) {
      redirectToLogin();
      return;
    }
    hasError.value = true;
    statusMessage.value = viewCopy.error;
  }
};
</script>
