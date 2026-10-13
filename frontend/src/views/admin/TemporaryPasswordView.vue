<template>
  <div class="auth-view flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-slate-900 lg:flex"
      style="background-image: linear-gradient(135deg, rgba(7,22,16,0.9), rgba(29,233,160,0.55)), url('https://images.unsplash.com/photo-1511910849309-0e3cbde44163?auto=format&fit=crop&w=1400&q=80'); background-size: cover; background-position: center;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <p class="inline-flex items-center rounded-full bg-white/10 px-4 py-1 text-sm font-semibold backdrop-blur">
          Reforço de segurança
        </p>
        <h2 class="text-4xl font-bold leading-tight">Sua senha foi redefinida pelo suporte</h2>
        <p class="text-lg text-white/80">
          A senha que você recebeu vale só para este primeiro acesso. Crie agora uma senha só sua para continuar.
        </p>
      </div>
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900/40 to-slate-900/20"></div>
    </div>
    <div class="flex w-full items-center justify-center px-4 py-10 lg:w-2/5 lg:px-12">
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Primeiro acesso</p>
          <h1 class="text-3xl font-bold text-slate-900">Crie sua senha</h1>
          <p class="text-sm text-slate-500">
            {{ auth.user?.email }} · você entrou com uma senha temporária. Escolha uma nova para usar daqui em diante.
          </p>
        </div>
        <form class="space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="text-sm font-semibold text-slate-600" for="tp-current">Senha temporária</label>
            <input
              id="tp-current"
              v-model="current"
              type="password"
              required
              autocomplete="current-password"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
              placeholder="A senha que você recebeu"
            />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600" for="tp-new">Nova senha</label>
            <input
              id="tp-new"
              v-model="password"
              type="password"
              required
              autocomplete="new-password"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
              placeholder="Min. 8 caracteres, com maiúscula, minúscula e número"
            />
            <PasswordRequirements :password="password" />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600" for="tp-confirm">Confirme a nova senha</label>
            <input
              id="tp-confirm"
              v-model="confirmPassword"
              type="password"
              required
              autocomplete="new-password"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            />
            <p v-if="confirmPassword && password !== confirmPassword" class="mt-1 text-sm text-red-500">As senhas não são iguais.</p>
          </div>
          <button
            type="submit"
            :disabled="loading || !passwordValid || password !== confirmPassword || !current"
            class="w-full rounded-lg bg-brand px-4 py-2 font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{ loading ? "Salvando..." : "Salvar e continuar" }}
          </button>
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        </form>
        <p class="mt-6 text-center text-sm text-slate-600">
          Não é você?
          <button type="button" class="text-brand" @click="leave">Sair</button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import PasswordRequirements from "../../components/forms/PasswordRequirements.vue";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const current = ref("");
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref("");

const passwordValid = computed(
  () => password.value.length >= 8 && /[A-Z]/.test(password.value) && /[a-z]/.test(password.value) && /\d/.test(password.value)
);
// Só volta para um endereço interno do painel.
const nextPath = () => {
  const raw = String(route.query.redirect || "");
  return raw.startsWith("/admin") ? raw : "/admin/dashboard";
};

onMounted(() => {
  if (auth.user && !auth.user.temporary_password) void router.replace(nextPath());
});

const onSubmit = async () => {
  if (!passwordValid.value || password.value !== confirmPassword.value) return;
  loading.value = true;
  error.value = "";
  try {
    await api.post("/auth/me/password", { current_password: current.value, new_password: password.value });
    await auth.fetchProfile();
    await router.replace(nextPath());
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "Não foi possível salvar a nova senha. Tente de novo.";
  } finally {
    loading.value = false;
  }
};

const leave = async () => {
  await auth.logout();
  await router.replace({ name: "login" });
};
</script>

<style scoped>
.auth-view { background: var(--background); color: var(--foreground); }
.auth-view :deep(.bg-white) { background: var(--card) !important; }
.auth-view :deep(.border-slate-200), .auth-view :deep(.border-slate-300) { border-color: var(--border) !important; }
.auth-view :deep(.text-slate-900), .auth-view :deep(.text-slate-700) { color: var(--foreground) !important; }
.auth-view :deep(.text-slate-600), .auth-view :deep(.text-slate-500) { color: var(--muted-foreground) !important; }
.auth-view :deep(input) { border-color: var(--input) !important; background: var(--background) !important; color: var(--foreground) !important; }
</style>
