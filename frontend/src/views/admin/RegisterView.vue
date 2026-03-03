<template>
  <div class="flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-[#41ce5f] lg:flex"
      style="background-color: #41ce5f;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <img src="../../assets/Logo Branco - Roteiro Online.png" alt="Roteiro Online" class="w-full max-w-[180px]" />
        <h2 class="text-4xl font-bold leading-tight text-white">Pare de mandar PDF! Venda suas viagens com páginas profissionais.</h2>
        <p class="text-lg text-white">
         Tudo em um só lugar!<br> Crie páginas para suas viagens, centralize as informações e facilite a decisão do cliente. <br>Criado para a realidade de quem vive de vender viagens         
        </p>
        <p class="text-lg text-white">
        
        </p>
        <div class="flex items-center gap-3 text-sm text-white">
          <span class="h-1 w-12 rounded-full bg-white"></span>
          Você pode começar com 1 roteiro online sem pagar nada.
        </div>
      </div>
    </div>
    <div class="flex w-full items-center justify-center bg-[#f8f8f8] px-4 py-10 lg:w-2/5 lg:px-12">
      <div class="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/40">
        <div class="mb-8 space-y-2">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Comece agora</p>
          <h1 class="text-3xl font-bold text-slate-900">Criar conta</h1>
          <p class="text-sm text-slate-500">Preencha seus dados para criar seu painel e publicar páginas.</p>
        </div>
        <form class="space-y-4" @submit.prevent="onSubmit">
        <div>
          <label class="text-sm font-semibold text-slate-600">Nome</label>
          <input v-model="name" required class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none" />
        </div>
        <div>
          <label class="text-sm font-semibold text-slate-600">CPF</label>
          <input
            v-model="cpf"
            required
            maxlength="14"
            placeholder="000.000.000-00"
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            @input="maskCpf"
          />
        </div>
        <div>
          <label class="text-sm font-semibold text-slate-600">E-mail</label>
          <input v-model="email" type="email" required class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none" />
        </div>
        <div>
          <label class="text-sm font-semibold text-slate-600">Senha</label>
          <input
            v-model="password"
            type="password"
            required
            class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            placeholder="Min. 8 caracteres, com maiuscula, minuscula e numero"
          />
          <PasswordRequirements :password="password" />
        </div>
        <div>
          <label class="text-sm font-semibold text-slate-600">WhatsApp</label>
          <div class="mt-1 flex gap-2">
            <div class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2 py-2">
              <select v-model="dialCode" class="bg-transparent text-sm font-semibold focus:outline-none">
                <option v-for="option in dialOptions" :key="option.code" :value="option.code">
                  {{ option.flag }} {{ option.code }}
                </option>
              </select>
            </div>
            <input
              v-model="whatsapp"
              required
              placeholder="11999999999"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-brand focus:outline-none"
            />
          </div>
          <p class="mt-1 text-xs text-slate-500">DDI fixo do Brasil (+55) e número apenas com dígitos.</p>
        </div>
        <button
          type="submit"
          :disabled="!canSubmit"
          class="w-full rounded-lg px-4 py-2 font-semibold transition hover:opacity-90"
          :class="canSubmit ? 'text-white cursor-pointer' : 'text-slate-600 cursor-not-allowed'"
          :style="canSubmit ? { backgroundColor: '#41ce5f' } : { backgroundColor: '#e2e8f0' }"
        >
          Registrar
        </button>
        <p class="text-center text-sm text-slate-600">
          Já possui conta?
          <router-link to="/login" class="font-semibold transition hover:opacity-80" style="color: #41ce5f;"
            >Entrar</router-link
          >
        </p>
        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
      </form>
    </div>
  </div>
</div>
</template>



<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import PasswordRequirements from "../../components/forms/PasswordRequirements.vue";

const router = useRouter();
const auth = useAuthStore();
const name = ref("");
const cpf = ref("");
const email = ref("");
const password = ref("");
const dialCode = ref("+55");
const whatsapp = ref("");
const error = ref("");

const dialOptions = [{ code: "+55", flag: "BR" }];
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const passwordCriteria = computed(() => ({
  length: password.value.length >= 8,
  uppercase: /[A-Z]/.test(password.value),
  lowercase: /[a-z]/.test(password.value),
  number: /\d/.test(password.value)
}));
const passwordValid = computed(() => Object.values(passwordCriteria.value).every(Boolean));

const maskCpf = () => {
  const digits = cpf.value.replace(/\D/g, "").slice(0, 11);
  const parts = [];
  if (digits.length > 0) parts.push(digits.slice(0, 3));
  if (digits.length > 3) parts.push(digits.slice(3, 6));
  if (digits.length > 6) parts.push(digits.slice(6, 9));
  const suffix = digits.length > 9 ? digits.slice(9, 11) : "";
  cpf.value = parts.join(".") + (suffix ? "-" + suffix : "");
};

const sanitizedCpf = () => cpf.value.replace(/\D/g, "");
const sanitizedWhatsapp = () => whatsapp.value.replace(/\D/g, "");

const isValidCpf = (value: string) => {
  const digits = value.replace(/\D/g, "");
  if (digits.length !== 11 || /^(\d)\1+$/.test(digits)) return false;
  const calc = (slice: number) => {
    let sum = 0;
    for (let i = 0; i < slice; i++) sum += Number(digits[i]) * (slice + 1 - i);
    const mod = (sum * 10) % 11;
    return mod === 10 ? 0 : mod;
  };
  return calc(9) === Number(digits[9]) && calc(10) === Number(digits[10]);
};

const canSubmit = computed(() => {
  const normalizedEmail = email.value.trim();
  const cpfDigits = sanitizedCpf();
  const phoneDigits = sanitizedWhatsapp();
  return Boolean(
    name.value.trim() &&
    emailRegex.test(normalizedEmail) &&
    passwordValid.value &&
    cpfDigits.length === 11 &&
    isValidCpf(cpfDigits) &&
    phoneDigits.length >= 10
  );
});

const onSubmit = async () => {
  try {
    error.value = "";
    const normalizedEmail = email.value.trim();
    if (!emailRegex.test(normalizedEmail)) {
      error.value = "E-mail invalido.";
      return;
    }
    if (!passwordValid.value) {
      error.value = "A senha deve ter pelo menos 8 caracteres, com maiuscula, minuscula e numero.";
      return;
    }
    const cpfDigits = sanitizedCpf();
    if (!isValidCpf(cpfDigits)) {
      error.value = "CPF invalido.";
      return;
    }
    const phoneDigits = sanitizedWhatsapp();
    if (!phoneDigits) {
      error.value = "Informe o WhatsApp.";
      return;
    }

    await api.post("/auth/register", {
      name: name.value,
      email: normalizedEmail,
      password: password.value,
      cpf: cpfDigits,
      whatsapp: `${dialCode.value}${phoneDigits}`
    });
    const form = new FormData();
    form.append("username", normalizedEmail);
    form.append("password", password.value);
    const res = await api.post("/auth/login", form, { headers: { "Content-Type": "multipart/form-data" } });
    auth.setToken(res.data.access_token);
    await auth.fetchProfile();
    router.push("/admin/dashboard");
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail;
    error.value = Array.isArray(detail) ? detail[0]?.msg : detail || "Erro ao registrar usuario.";
  }
};
</script>





