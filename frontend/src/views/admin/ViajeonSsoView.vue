<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-950 px-5 text-white">
    <div class="w-full max-w-md text-center">
      <div v-if="loading" class="mx-auto h-11 w-11 animate-spin rounded-full border-4 border-white/20 border-t-emerald-400"></div>
      <h1 class="mt-5 text-2xl font-bold">{{ loading ? "Entrando no Roteiro Online..." : "Não foi possível entrar" }}</h1>
      <p class="mt-2 text-sm text-slate-300">{{ message }}</p>
      <RouterLink v-if="!loading" to="/login" class="mt-6 inline-flex rounded-xl bg-emerald-500 px-5 py-2.5 font-semibold text-slate-950">
        Ir para o login
      </RouterLink>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const loading = ref(true);
const message = ref("Validando seu acesso enviado pelo Viajeon.");

onMounted(async () => {
  const ticket = String(route.query.ticket || "").trim();
  if (!ticket) {
    loading.value = false;
    message.value = "O link de acesso está incompleto.";
    return;
  }
  try {
    const response = await api.post("/public/integrations/viajeon/sso/exchange", { ticket });
    auth.setTokens(response.data.access_token, response.data.refresh_token);
    await auth.fetchProfile();
    await router.replace("/admin/dashboard");
  } catch (error: any) {
    auth.setTokens(null, null);
    loading.value = false;
    message.value = error?.response?.data?.detail?.error === "invalid-or-expired-ticket"
      ? "Este link já foi usado ou expirou. Gere um novo acesso no Viajeon."
      : "Não foi possível validar este acesso. Tente novamente pelo Viajeon.";
  }
});
</script>
