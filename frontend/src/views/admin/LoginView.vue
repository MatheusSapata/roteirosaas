<template>
  <div class="flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-[#41ce5f] lg:flex"
      style="background-color: #41ce5f;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="w-full max-w-[180px]" />
        <h2 class="text-4xl font-bold leading-tight text-white">Mais organização<br>Mais profissionalismo<br>Mais vendas</h2>
        <p class="text-lg text-white">
          Acesse seus roteiros, edite informações, acompanhe acessos e mantenha tudo organizado para vender melhor.
          </p>
        <div class="flex items-center gap-3 text-sm text-white">
          <span class="h-1 w-12 rounded-full bg-white"></span>
          Seu painel disponível sempre que você precisar.
        </div>
      </div>
    </div>
    <div class="flex w-full items-center justify-center bg-[#f8f8f8] px-4 py-10 lg:w-2/5 lg:px-12">
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Bem-vindo ao roteiro online </p>
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

            <div class="relative mt-1">

              <input

                v-model="password"

                :type="showPassword ? 'text' : 'password'"

                required

                class="w-full rounded-lg border border-slate-200 px-3 py-2 pr-11 focus:border-brand focus:outline-none"

              />

              <button

                type="button"

                class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600"

                @click="showPassword = !showPassword"

                aria-label="Alternar visualiza��o da senha"

              >

                <svg

                  v-if="!showPassword"

                  class="h-5 w-5"

                  viewBox="0 0 24 24"

                  fill="none"

                  stroke="currentColor"

                  stroke-width="1.8"

                  stroke-linecap="round"

                  stroke-linejoin="round"

                >

                  <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />

                  <circle cx="12" cy="12" r="3" />

                </svg>

                <svg

                  v-else

                  class="h-5 w-5"

                  viewBox="0 0 24 24"

                  fill="none"

                  stroke="currentColor"

                  stroke-width="1.8"

                  stroke-linecap="round"

                  stroke-linejoin="round"

                >

                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />

                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8 a18.5 18.5 0 0 1-2.08 3.17" />

                  <line x1="1" y1="1" x2="23" y2="23" />

                </svg>

              </button>

            </div>

            <p class="mt-1 text-xs text-slate-500">Use sua senha com no mínimo 8 caracteres, incluindo maiúscula, minúscula e número.</p>

          </div>
        <button
          type="submit"
          class="w-full rounded-lg px-4 py-2 font-semibold text-white transition hover:opacity-90"
          style="background-color: #41ce5f;"
        >
          Entrar
        </button>
        <p class="text-center text-sm text-slate-600">
          <router-link to="/forgot-password" class="font-semibold transition hover:opacity-80" style="color: #41ce5f;"
            >Esqueci minha senha</router-link
          >
        </p>
        <p class="text-center text-sm text-slate-600">
          Novo aqui?
          <router-link to="/register" class="font-semibold transition hover:opacity-80" style="color: #41ce5f;"
            >Criar conta</router-link
          >
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
const showPassword = ref(false);

const onSubmit = async () => {
  try {
    const form = new FormData();
    form.append("username", email.value);
    form.append("password", password.value);
    const res = await api.post("/auth/login", form, { headers: { "Content-Type": "multipart/form-data" } });
    auth.setTokens(res.data.access_token, res.data.refresh_token);
    await auth.fetchProfile();
    router.push("/admin/dashboard");
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível entrar. Verifique suas credenciais.";
  }
};
</script>
