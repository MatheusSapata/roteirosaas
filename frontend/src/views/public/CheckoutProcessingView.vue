<template>
  <div class="flex min-h-screen items-center justify-center bg-[#41ce5f] px-4">
    <div class="w-full max-w-md rounded-3xl bg-white/95 p-8 text-center shadow-2xl shadow-emerald-900/30">
      <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="mx-auto mb-6 w-32" />
      <h1 class="text-2xl font-bold text-slate-900">Processando seu acesso</h1>
      <p class="mt-3 text-sm text-slate-600">
        Estamos confirmando seu pagamento e configurando seu painel. Isso leva poucos segundos.
      </p>
      <div class="mt-6 flex justify-center">
        <span class="h-16 w-16 animate-spin rounded-full border-4 border-emerald-200 border-t-white"></span>
      </div>
      <p class="mt-6 text-sm font-medium text-slate-700">
        Em instantes você será levado para definir sua senha de acesso.
      </p>
      <p v-if="!orderIdFound" class="mt-2 text-xs text-amber-600">
        Caso o redirecionamento não aconteça, use o link do e-mail de confirmação.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

const extractOrderFromReferrer = (): string | null => {
  if (typeof document === "undefined") return null;
  const ref = document.referrer || "";
  const match = ref.match(/payment\/status\/([a-f0-9-]+)/i);
  if (match?.[1]) return match[1];
  const fallback = ref.match(/orders?\/([a-f0-9-]+)/i);
  return fallback?.[1] ?? null;
};

const getOrderId = () => {
  const maybe = route.query.order_id || route.query.orderId;
  if (typeof maybe === "string" && maybe.trim()) return maybe.trim();
  return extractOrderFromReferrer();
};

const orderId = getOrderId();
const orderIdFound = computed(() => !!orderId);

onMounted(() => {
  setTimeout(() => {
    const params: Record<string, string> = {};
    if (orderId) params.order_id = orderId;
    const token = typeof route.query.token === "string" ? route.query.token : null;
    if (token) params.token = token;
    router.replace({ name: "create-password", query: params });
  }, 5000);
});
</script>
