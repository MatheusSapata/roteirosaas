<template>
  <div class="flex min-h-screen items-center justify-center bg-[#41ce5f] px-4">
    <div class="w-full max-w-md rounded-3xl bg-white/95 p-8 text-center shadow-2xl shadow-emerald-900/30">
      <img
        src="../../assets/Logo Cor - Roteiro Online.png"
        alt="Roteiro Online"
        class="mx-auto mb-6 w-32"
      />

      <h1 class="text-2xl font-bold text-slate-900">Processando seu acesso</h1>

      <p class="mt-3 text-sm text-slate-600">
        {{ statusMessage }}
      </p>

      <div class="mt-6 flex justify-center">
        <span class="h-16 w-16 animate-spin rounded-full border-4 border-emerald-200 border-t-white"></span>
      </div>

      <p class="mt-6 text-sm font-medium text-slate-700">
        Em instantes voc√™ ser√° levado para definir sua senha de acesso.
      </p>

      <p v-if="!orderIdFound" class="mt-2 text-xs text-amber-600">
        Caso o redirecionamento n√£o aconte√ßa, use o link do e-mail de confirma√ß√£o.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AxiosError } from "axios";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CHECKOUT_SESSION_STORAGE_KEY, getCheckoutSessionStatus } from "../../services/cakto";

const router = useRouter();
const route = useRoute();

const sessionToken = ref<string | null>(null);
const statusMessage = ref("Estamos finalizando tudo para vocÍ...");
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
    statusMessage.value =
      "N„o conseguimos identificar sua compra. Use o link do e-mail de confirmaÁ„o.";
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
      statusMessage.value = "O pagamento foi confirmado, mas ainda estamos finalizando seu acesso.";
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
    statusMessage.value = "N„o conseguimos confirmar seu pedido. Use o link enviado por e-mail.";
  }
};
</script>



