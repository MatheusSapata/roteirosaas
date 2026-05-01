<template>
  <div class="min-h-screen bg-[#41ce5f] px-4 py-10">
    <div class="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center">
      <div class="mb-8 flex flex-col items-center text-center text-white">
        <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="mb-6 w-32 drop-shadow-lg" />
        <h1 class="text-4xl font-bold">Aceitar convite</h1>
        <p class="mt-2 text-lg text-white/90">Finalize seu acesso à equipe agora.</p>
      </div>

      <div class="w-full rounded-3xl bg-white p-6 shadow-[0_30px_80px_rgba(0,0,0,0.18)] md:p-8">
        <p class="text-sm text-slate-600" v-if="info.valid">
          Você foi convidado para se juntar à equipe da <strong>{{ info.agency_name }}</strong>.
        </p>
        <p class="text-sm text-red-600" v-else>{{ invalidMessage }}</p>

        <form v-if="info.valid" class="mt-6 space-y-5" @submit.prevent="submit">
          <div>
            <label class="text-sm font-semibold text-slate-600">Senha</label>
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 focus:border-[#41ce5f] focus:outline-none"
            />
          </div>

          <div>
            <label class="text-sm font-semibold text-slate-600">Confirmar senha</label>
            <input
              v-model="confirm"
              :type="showConfirm ? 'text' : 'password'"
              class="mt-1 w-full rounded-xl border border-slate-200 px-4 py-3 focus:border-[#41ce5f] focus:outline-none"
            />
          </div>

          <div class="flex gap-3">
            <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-sm" @click="showPassword = !showPassword">Mostrar senha</button>
            <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-sm" @click="showConfirm = !showConfirm">Mostrar confirmação</button>
          </div>

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
          <p v-if="success" class="text-sm text-emerald-600">{{ success }}</p>

          <button
            type="submit"
            class="w-full rounded-xl bg-[#41ce5f] px-4 py-3 text-base font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
            :disabled="loading"
          >
            {{ loading ? "Criando..." : "Criar senha e acessar" }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const token = computed(() => String(route.query.token || ""));
const info = ref<{ valid: boolean; reason?: string; agency_name?: string }>({ valid: false });
const password = ref("");
const confirm = ref("");
const showPassword = ref(false);
const showConfirm = ref(false);
const error = ref("");
const success = ref("");
const loading = ref(false);

const invalidMessage = computed(() => {
  if (info.value.reason === "expired") return "Este convite expirou.";
  if (info.value.reason === "accepted") return "Este convite já foi aceito.";
  if (info.value.reason === "cancelled") return "Este convite foi cancelado.";
  return "Token inválido.";
});

const loadInfo = async () => {
  if (!token.value) return;
  const { data } = await api.get("/auth/invite-info", { params: { token: token.value } });
  info.value = data;
};

const submit = async () => {
  error.value = "";
  success.value = "";
  if (!password.value || password.value !== confirm.value) {
    error.value = "As senhas precisam coincidir.";
    return;
  }
  loading.value = true;
  try {
    await api.post("/auth/accept-invite", { token: token.value, password: password.value });
    success.value = "Senha criada com sucesso. Faça login para continuar.";
    await auth.logout();
    setTimeout(() => router.push({ name: "login" }), 900);
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "Não foi possível aceitar o convite.";
  } finally {
    loading.value = false;
  }
};

onMounted(loadInfo);
</script>
