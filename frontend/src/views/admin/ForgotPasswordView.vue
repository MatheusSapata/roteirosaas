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

          <p class="text-sm text-slate-500">Confirme seu e-mail e CPF para criar uma nova senha com seguranca.</p>

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

          <div>

            <label class="text-sm font-semibold text-slate-600">CPF</label>

            <input

              v-model="cpf"

              inputmode="numeric"

              required

              maxlength="14"

              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"

              placeholder="000.000.000-00"

            />

          </div>

          <div>

            <label class="text-sm font-semibold text-slate-600">Nova senha</label>

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

                aria-label="Alternar visualizacao da senha"

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

            <p class="mt-1 text-xs text-slate-500">Precisa de pelo menos 8 caracteres, com maiuscula, minuscula e numero.</p>

          </div>

          <div>

            <label class="text-sm font-semibold text-slate-600">Confirmar nova senha</label>

            <div class="relative mt-1">

              <input

                v-model="passwordConfirm"

                :type="showConfirmPassword ? 'text' : 'password'"

                required

                class="w-full rounded-lg border border-slate-200 px-3 py-2 pr-11 focus:border-brand focus:outline-none"

              />

              <button

                type="button"

                class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600"

                @click="showConfirmPassword = !showConfirmPassword"

                aria-label="Alternar visualizacao da confirmacao"

              >

                <svg

                  v-if="!showConfirmPassword"

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

          </div>

          <button

            type="submit"

            :disabled="loading"

            class="w-full rounded-lg bg-brand px-4 py-2 font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"

          >

            {{ loading ? "Salvando..." : "Salvar nova senha" }}

          </button>

          <p v-if="successMessage" class="rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">

            {{ successMessage }}

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
const cpf = ref("");
const password = ref("");
const passwordConfirm = ref("");
const loading = ref(false);
const successMessage = ref("");
const error = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);

const onSubmit = async () => {
  loading.value = true;
  error.value = "";
  successMessage.value = "";
  try {
    if (password.value !== passwordConfirm.value) {
      throw new Error("As senhas nao conferem.");
    }
    const normalizedEmail = email.value.trim();
    const normalizedCpf = cpf.value.replace(/[^0-9]/g, "");
    if (normalizedCpf.length !== 11) {
      throw new Error("Informe um CPF valido.");
    }
    await api.post("/auth/password/reset/by-profile", {
      email: normalizedEmail,
      cpf: normalizedCpf,
      password: password.value
    });
    successMessage.value = "Senha atualizada com sucesso! Agora voce ja pode fazer login.";
  } catch (err) {
    console.error(err);
    const detail = err?.response?.data?.detail;
    error.value = detail || err.message || "Nao foi possivel atualizar a senha.";
  } finally {
    loading.value = false;
  }
};
</script>
