<template>
  <div class="flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-slate-900 lg:flex"
      style="background-image: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(14,165,233,0.7)), url('https://images.unsplash.com/photo-1511910849309-0e3cbde44163?auto=format&fit=crop&w=1400&q=80'); background-size: cover; background-position: center;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <p class="inline-flex items-center rounded-full bg-white/10 px-4 py-1 text-sm font-semibold backdrop-blur">
          Reforço de segurança
        </p>
        <h2 class="text-4xl font-bold leading-tight">Crie uma nova senha com os requisitos recomendados</h2>
        <p class="text-lg text-white/80">
          Senhas fortes protegem seus dados e os de seus clientes. Use letras maiúsculas, minúsculas e números.
        </p>
        <div class="flex items-center gap-3 text-sm text-white/70">
          <span class="h-1 w-12 rounded-full bg-cyan-300"></span>
          Você verá o resultado em tempo real abaixo.
        </div>
      </div>
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900/40 to-slate-900/20"></div>
    </div>
    <div class="flex w-full items-center justify-center px-4 py-10 lg:w-2/5 lg:px-12">
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Redefinir senha</p>
          <h1 class="text-3xl font-bold text-slate-900">Criar nova senha</h1>
          <p class="text-sm text-slate-500">Cole o token recebido por e-mail ou use o link enviado pelo suporte.</p>
        </div>
        <form class="space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="text-sm font-semibold text-slate-600">Token de redefinição</label>
            <input
              v-model="token"
              required
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-sm focus:border-brand focus:outline-none"
              placeholder="Cole aqui o token recebido"
            />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Nova senha</label>
            <input
              v-model="password"
              type="password"
              required
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
              placeholder="Min. 8 caracteres, com maiúscula, minúscula e número"
            />
            <PasswordRequirements :password="password" />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Confirme a nova senha</label>
            <input
              v-model="confirmPassword"
              type="password"
              required
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            />
          </div>
          <button
            type="submit"
            :disabled="loading || !passwordValid || password !== confirmPassword"
            class="w-full rounded-lg bg-brand px-4 py-2 font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{ loading ? "Atualizando..." : "Atualizar senha" }}
          </button>
          <p v-if="successMessage" class="rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
            {{ successMessage }}
          </p>
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        </form>
        <p class="mt-6 text-center text-sm text-slate-600">
          Já pode acessar?
          <RouterLink to="/login" class="text-brand">Voltar para login</RouterLink>
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

const route = useRoute();
const token = ref<string>((route.query.token as string) || "");
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref("");
const successMessage = ref("");

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
  successMessage.value = "";
  try {
    await api.post("/auth/password/reset", {
      token: token.value.trim(),
      password: password.value
    });
    successMessage.value = "Senha atualizada com sucesso! Agora você já pode fazer login novamente.";
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail;
    error.value = detail || "Não foi possível atualizar a senha. Verifique o token e tente novamente.";
  } finally {
    loading.value = false;
  }
};
</script>
