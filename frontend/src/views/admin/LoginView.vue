<template>
  <div class="flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-slate-900 lg:flex"
      style="background-image: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(14,165,233,0.7)), url('https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1400&q=80'); background-size: cover; background-position: center;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <p class="inline-flex items-center rounded-full bg-white/10 px-4 py-1 text-sm font-semibold backdrop-blur">
          Bem-vindo ao painel Travel Pages
        </p>
        <h2 class="text-4xl font-bold leading-tight">Centralize seus planos, campanhas e resultados em um só lugar</h2>
        <p class="text-lg text-white/80">
          Dashboards em tempo real, modelos prontos e integrações com os principais canais para acelerar o crescimento da sua agência.
        </p>
        <div class="flex items-center gap-3 text-sm text-white/70">
          <span class="h-1 w-12 rounded-full bg-cyan-300"></span>
          Acesso seguro e monitorado 24h.
        </div>
      </div>
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900/40 to-slate-900/20"></div>
    </div>
    <div class="flex w-full items-center justify-center px-4 py-10 lg:w-2/5 lg:px-12">
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Bem-vindo de volta</p>
          <h1 class="text-3xl font-bold text-slate-900">Login</h1>
          <p class="text-sm text-slate-500">Entre para continuar acompanhando suas campanhas e páginas.</p>
        </div>
        <form class="space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="text-sm font-semibold text-slate-600">E-mail</label>
            <input v-model="email" type="email" required class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none" />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-600">Senha</label>
            <input v-model="password" type="password" required class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none" />
            <p class="mt-1 text-xs text-slate-500">Use sua senha com no mínimo 8 caracteres, incluindo maiúscula, minúscula e número.</p>
          </div>
        <button type="submit" class="w-full rounded-lg bg-brand px-4 py-2 font-semibold text-white hover:bg-brand-dark">Entrar</button>
        <p class="text-center text-sm text-slate-600">
          <router-link to="/forgot-password" class="text-brand">Esqueci minha senha</router-link>
        </p>
        <p class="text-center text-sm text-slate-600">
          Novo aqui?
          <router-link to="/register" class="text-brand">Criar conta</router-link>
        </p>
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";

const router = useRouter();
const auth = useAuthStore();
const email = ref("");
const password = ref("");
const error = ref("");

const onSubmit = async () => {
  try {
    const form = new FormData();
    form.append("username", email.value);
    form.append("password", password.value);
    const res = await api.post("/auth/login", form, { headers: { "Content-Type": "multipart/form-data" } });
    auth.setToken(res.data.access_token);
    await auth.fetchProfile();
    router.push("/admin/dashboard");
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível entrar. Verifique suas credenciais.";
  }
};
</script>
