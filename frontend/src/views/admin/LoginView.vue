<template>
  <!-- Login no modelo "cartão ao centro" (como o do Viaje On), sobre o verde da marca
       com desenhos de páginas ao fundo (components/auth/AuthPagesBackdrop.vue). -->
  <div class="lg">
    <AuthPagesBackdrop />

    <main class="lg-main">
      <img src="../../assets/Logo Branco - Roteiro Online.png" :alt="viewCopy.brand.alt" class="lg-logo" />
      <h1 class="sr-only">{{ viewCopy.brand.tagline }}</h1>

      <div class="lg-card">
        <header class="lg-head">
          <p class="lg-eyebrow">{{ viewCopy.card.eyebrow }}</p>
          <h2>{{ viewCopy.card.title }}</h2>
          <p class="lg-desc">{{ viewCopy.card.description }}</p>
        </header>

        <form class="lg-form" @submit.prevent="onSubmit">
          <div class="lg-field">
            <label for="login-email">{{ viewCopy.form.emailLabel }}</label>
            <input id="login-email" v-model="email" type="email" autocomplete="email" required />
          </div>
          <div class="lg-field">
            <div class="lg-label-row">
              <label for="login-password">{{ viewCopy.form.passwordLabel }}</label>
              <router-link to="/forgot-password" class="lg-link">{{ viewCopy.links.forgotPassword }}</router-link>
            </div>
            <div class="lg-pass">
              <input
                id="login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
              />
              <button type="button" class="lg-eye" :aria-label="viewCopy.form.passwordToggleAria" @click="showPassword = !showPassword">
                <EyeIcon v-if="!showPassword" aria-hidden="true" />
                <EyeOffIcon v-else aria-hidden="true" />
              </button>
            </div>
            <p class="lg-hint">{{ viewCopy.form.passwordHint }}</p>
          </div>

          <p v-if="error" class="lg-error" role="alert">{{ error }}</p>

          <button type="submit" class="lg-submit" :disabled="loading">
            <span v-if="loading" class="lg-spin" aria-hidden="true"></span>
            {{ loading ? viewCopy.form.submitting : viewCopy.form.submit }}
          </button>
        </form>
      </div>

      <router-link to="/register" class="lg-register">
        {{ viewCopy.links.registerPrompt }}
        <b>{{ viewCopy.links.registerCta }}</b>
        <ArrowUpRightIcon aria-hidden="true" />
      </router-link>
    </main>

    <p class="lg-copy">© {{ year }} Roteiro Online</p>
  </div>
</template>

<script setup lang="ts">
import { ArrowUpRightIcon, EyeIcon, EyeOffIcon } from "lucide-vue-next";
import AuthPagesBackdrop from "../../components/auth/AuthPagesBackdrop.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { createAdminLocalizer } from "../../utils/adminI18n";

const router = useRouter();
const auth = useAuthStore();
const t = createAdminLocalizer();

const viewCopy = {
  brand: {
    alt: t({ pt: "Roteiro Online", es: "Roteiro Online" }),
    tagline: t({
      pt: "Roteiro Online: páginas de viagem que vendem",
      es: "Roteiro Online: páginas de viaje que venden"
    })
  },
  card: {
    eyebrow: t({ pt: "Bem-vindo ao Roteiro Online", es: "Bienvenido a Roteiro Online" }),
    title: t({ pt: "Login", es: "Iniciar sesión" }),
    description: t({
      pt: "Entre para continuar acompanhando suas campanhas e páginas.",
      es: "Ingresa para seguir tus campañas y páginas."
    })
  },
  form: {
    emailLabel: t({ pt: "E-mail", es: "Correo" }),
    passwordLabel: t({ pt: "Senha", es: "Contraseña" }),
    passwordHint: t({
      pt: "Use sua senha com no mínimo 8 caracteres, incluindo maiúscula, minúscula e número.",
      es: "Usa tu contraseña con al menos 8 caracteres, incluyendo mayúsculas, minúsculas y números."
    }),
    passwordToggleAria: t({
      pt: "Alternar visualização da senha",
      es: "Alternar visualización de la contraseña"
    }),
    submit: t({ pt: "Entrar", es: "Ingresar" }),
    submitting: t({ pt: "Entrando…", es: "Ingresando…" })
  },
  links: {
    forgotPassword: t({ pt: "Esqueci minha senha", es: "Olvidé mi contraseña" }),
    registerPrompt: t({ pt: "Novo aqui?", es: "¿Nuevo por aquí?" }),
    registerCta: t({ pt: "Criar conta", es: "Crear cuenta" })
  },
  feedback: {
    failure: t({
      pt: "Não foi possível entrar. Verifique suas credenciais.",
      es: "No fue posible ingresar. Verifica tus credenciales."
    })
  }
};

const email = ref("");
const password = ref("");
const error = ref("");
const showPassword = ref(false);
const loading = ref(false);
const year = new Date().getFullYear();

const onSubmit = async () => {
  if (loading.value) return;
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("username", email.value.trim().toLowerCase());
    form.append("password", password.value);
    const res = await api.post("/auth/login", form, { headers: { "Content-Type": "multipart/form-data" } });
    auth.setTokens(res.data.access_token, res.data.refresh_token);
    await auth.fetchProfile();
    router.push("/admin/dashboard");
  } catch (err) {
    console.error(err);
    error.value = viewCopy.feedback.failure;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.lg {
  position: relative;
  isolation: isolate;
  display: flex;
  min-height: 100dvh;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 40px 16px 28px;
  background: #2fb552;
  font-family: var(--font-sans);
}
.lg-main {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  max-width: 420px;
  flex-direction: column;
  align-items: center;
  gap: 26px;
  animation: lg-in 0.6s cubic-bezier(0.22, 0.8, 0.24, 1) both;
}
.lg-logo {
  width: auto;
  height: 52px;
  max-width: 70%;
  object-fit: contain;
  filter: drop-shadow(0 2px 10px rgba(6, 60, 28, 0.25));
}
/* O cartão é sempre claro, também com o painel no tema escuro. */
.lg-card {
  width: 100%;
  padding: 28px;
  border-radius: 22px;
  background: #ffffff;
  color: #10231a;
  box-shadow: 0 30px 60px -20px rgba(6, 60, 28, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.4);
}
.lg-head {
  margin-bottom: 22px;
}
.lg-eyebrow {
  margin: 0;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #15803d;
}
.lg-head h2 {
  margin: 6px 0 0;
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #10231a;
}
.lg-desc {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: #5b6b62;
}
.lg-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.lg-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.lg-field label {
  font-size: 13px;
  font-weight: 600;
  color: #33443b;
}
.lg-label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.lg-field input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #d5e0d8;
  border-radius: 12px;
  background: #f6f9f7;
  font-size: 15px;
  color: #10231a;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
}
.lg-field input:focus {
  outline: none;
  border-color: #15803d;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(65, 206, 95, 0.28);
}
.lg-pass {
  position: relative;
}
.lg-pass input {
  padding-right: 46px;
}
.lg-eye {
  position: absolute;
  top: 0;
  right: 4px;
  bottom: 0;
  display: grid;
  place-items: center;
  width: 40px;
  color: #7b8a82;
}
.lg-eye:hover {
  color: #33443b;
}
.lg-eye svg {
  width: 19px;
  height: 19px;
}
.lg-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: #7b8a82;
}
.lg-link {
  font-size: 12.5px;
  font-weight: 600;
  color: #15803d;
}
.lg-link:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}
.lg-error {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fdecec;
  font-size: 13px;
  color: #b42323;
}
.lg-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 46px;
  margin-top: 4px;
  border-radius: 999px;
  background: #15803d;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  box-shadow: 0 10px 22px -10px rgba(21, 128, 61, 0.8);
  transition: background-color 0.15s ease, transform 0.15s ease;
}
.lg-submit:hover:not(:disabled) {
  background: #116a32;
  transform: translateY(-1px);
}
.lg-submit:disabled {
  opacity: 0.8;
  cursor: progress;
}
.lg-spin {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #ffffff;
  border-radius: 999px;
  animation: lg-spin 0.8s linear infinite;
}
.lg-register {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(6, 60, 28, 0.22);
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(6px);
  transition: background-color 0.15s ease;
}
.lg-register:hover {
  background: rgba(6, 60, 28, 0.34);
}
.lg-register b {
  color: #ffffff;
}
.lg-register svg {
  width: 16px;
  height: 16px;
}
.lg-copy {
  position: relative;
  z-index: 1;
  margin: 36px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
}
:where(.lg a, .lg button, .lg input):focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}
.lg-card :where(a, button):focus-visible {
  outline-color: #15803d;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
@keyframes lg-in {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
}
@keyframes lg-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (max-width: 480px) {
  .lg-card {
    padding: 22px 18px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .lg-main {
    animation: none;
  }
}
</style>
