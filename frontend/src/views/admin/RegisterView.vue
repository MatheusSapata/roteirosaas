<template>
  <div class="flex min-h-screen">
    <div
      class="relative hidden w-3/5 items-center justify-center overflow-hidden bg-slate-900 lg:flex"
      style="background-image: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(14,165,233,0.7)), url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80'); background-size: cover; background-position: center;"
    >
      <div class="relative z-10 max-w-xl space-y-6 p-16 text-white">
        <p class="inline-flex items-center rounded-full bg-white/10 px-4 py-1 text-sm font-semibold backdrop-blur">
          Plataforma Travel Pages SaaS
        </p>
        <h2 class="text-4xl font-bold leading-tight">Crie experiências digitais inesquecíveis para sua agência</h2>
        <p class="text-lg text-white/80">
          Construa landing pages, acompanhe leads e mantenha seu time focado no que importa. Tudo em uma única plataforma.
        </p>
        <div class="flex items-center gap-3 text-sm text-white/70">
          <span class="h-1 w-12 rounded-full bg-cyan-300"></span>
          Centenas de agências já confiam no Travel Pages.
        </div>
      </div>
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900/40 to-slate-900/20"></div>
    </div>
    <div class="flex w-full items-center justify-center px-4 py-10 lg:w-2/5 lg:px-12">
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
          :class="[
            'w-full rounded-lg px-4 py-2 font-semibold text-white transition-colors',
            canSubmit ? 'bg-brand hover:bg-brand-dark' : 'cursor-not-allowed bg-slate-300 text-slate-600'
          ]"
        >
          Registrar
        </button>
        <p class="text-center text-sm text-slate-600">
          Já possui conta?
          <router-link to="/login" class="text-brand">Entrar</router-link>
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





