<template>
  <div class="flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-slate-900 lg:flex"
      style="background-image: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(14,165,233,0.7)), url('https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1400&q=80'); background-size: cover; background-position: center;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <p class="inline-flex items-center rounded-full bg-white/10 px-4 py-1 text-sm font-semibold backdrop-blur">
          Recuperar acesso com segurança
        </p>
        <h2 class="text-4xl font-bold leading-tight">Envie instruções de redefinição em segundos</h2>
        <p class="text-lg text-white/80">
          Informe o e-mail cadastrado e enviaremos um link seguro para você criar uma nova senha e voltar ao painel.
        </p>
        <div class="flex items-center gap-3 text-sm text-white/70">
          <span class="h-1 w-12 rounded-full bg-cyan-300"></span>
          Tokens expiram em 60 minutos por segurança.
        </div>
      </div>
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900/40 to-slate-900/20"></div>
    </div>
    <div class="flex w-full items-center justify-center px-4 py-10 lg:w-2/5 lg:px-12">
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Recuperar acesso</p>
          <h1 class="text-3xl font-bold text-slate-900">Esqueci minha senha</h1>
          <p class="text-sm text-slate-500">Digite o e-mail cadastrado. Vamos enviar um link seguro para você redefinir a senha.</p>
        </div>
        <form class="space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="text-sm font-semibold text-slate-600">E-mail</label>
            <input
              v-model="email"
              type="email"
              required
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
              placeholder="voce@agencia.com"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full rounded-lg bg-brand px-4 py-2 font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{ loading ? "Enviando..." : "Enviar instruções" }}
          </button>
          <p v-if="successMessage" class="rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
            {{ successMessage }}
          </p>
          <p v-if="devToken" class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
            Token gerado (ambiente {{ envLabel }}): <span class="font-mono">{{ devToken }}</span>
          </p>
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        </form>
        <p class="mt-6 text-center text-sm text-slate-600">
          Lembrou a senha?
          <RouterLink to="/login" class="text-brand">Voltar para login</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";
import api from "../../services/api";

const email = ref("");
const loading = ref(false);
const successMessage = ref("");
const error = ref("");
const devToken = ref("");
const envLabel = import.meta.env.MODE || "dev";

const onSubmit = async () => {
  loading.value = true;
  error.value = "";
  successMessage.value = "";
  devToken.value = "";
  try {
    const normalizedEmail = email.value.trim();
    const res = await api.post("/auth/password/forgot", { email: normalizedEmail });
    successMessage.value = res.data?.detail || "Se o email estiver cadastrado, enviaremos as instruções.";
    if (res.data?.reset_token) {
      devToken.value = res.data.reset_token;
    }
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível enviar as instruções. Tente novamente.";
  } finally {
    loading.value = false;
  }
};
</script>
