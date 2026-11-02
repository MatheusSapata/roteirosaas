<template>
  <!-- Login no modelo do Viaje On: cartão ao centro sobre o gradiente animado da marca,
       com luzes que se movem devagar (components/auth/AuthBackdrop.vue). -->
  <div class="lg">
    <AuthBackdrop />

    <main class="lg-main">
      <img :src="brandLogoWhite" :alt="viewCopy.brand.alt" class="lg-logo" />
      <h1 class="sr-only">{{ viewCopy.brand.tagline }}</h1>

      <div class="lg-card">
        <header class="lg-head">
          <h2>{{ viewCopy.card.title }}</h2>
          <p>{{ viewCopy.card.description }}</p>
        </header>

        <form class="lg-form" novalidate @submit.prevent="onSubmit">
          <div class="lg-field">
            <label for="login-email">{{ viewCopy.form.emailLabel }}</label>
            <input id="login-email" v-model="email" type="email" autocomplete="email" required />
          </div>
          <div class="lg-field">
            <label for="login-password">{{ viewCopy.form.passwordLabel }}</label>
            <div class="lg-pass">
              <input
                id="login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
              />
              <button
                type="button"
                class="lg-eye"
                :aria-label="showPassword ? viewCopy.form.hidePassword : viewCopy.form.showPassword"
                @click="showPassword = !showPassword"
              >
                <EyeOffIcon v-if="showPassword" aria-hidden="true" />
                <EyeIcon v-else aria-hidden="true" />
              </button>
            </div>
          </div>

          <p v-if="error" class="lg-error" role="alert">{{ error }}</p>

          <button type="submit" class="lg-submit" :disabled="loading">
            <Loader2Icon v-if="loading" class="lg-spin" aria-hidden="true" />
            {{ viewCopy.form.submit }}
          </button>
        </form>

        <div class="lg-forgot">
          <router-link to="/forgot-password" class="lg-link">{{ viewCopy.links.forgotPassword }}</router-link>
        </div>
        <p class="lg-first">
          {{ viewCopy.links.firstAccessPrompt }}
          <router-link to="/create-password" class="lg-link">{{ viewCopy.links.firstAccessCta }}</router-link>
        </p>
      </div>

      <router-link to="/lp" class="lg-register">
        {{ viewCopy.links.notClient }}
        <b>{{ viewCopy.links.knowMore }}</b>
        <ArrowUpRightIcon aria-hidden="true" />
      </router-link>
    </main>

    <p class="lg-copy">© {{ year }} Roteiro Online</p>
  </div>
</template>

<script setup lang="ts">
import { ArrowUpRightIcon, EyeIcon, EyeOffIcon, Loader2Icon } from "lucide-vue-next";
import AuthBackdrop from "../../components/auth/AuthBackdrop.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { usePlatformBranding } from "../../composables/usePlatformBranding";
const { logoWhite: brandLogoWhite, logoColor: brandLogoColor } = usePlatformBranding();

const router = useRouter();
const auth = useAuthStore();
const t = createAdminLocalizer();

const viewCopy = {
  brand: {
    alt: t({ pt: "Roteiro Online", es: "Roteiro Online" }),
    tagline: t({
      pt: "Páginas de viagem, captação de leads e vendas em um só lugar.",
      es: "Páginas de viaje, captación de leads y ventas en un solo lugar."
    })
  },
  card: {
    title: t({ pt: "Bem-vindo(a) de volta", es: "Bienvenido(a) de nuevo" }),
    description: t({ pt: "Entre para acessar suas páginas.", es: "Ingresa para acceder a tus páginas." })
  },
  form: {
    emailLabel: t({ pt: "E-mail", es: "Correo" }),
    passwordLabel: t({ pt: "Senha", es: "Contraseña" }),
    showPassword: t({ pt: "Mostrar senha", es: "Mostrar contraseña" }),
    hidePassword: t({ pt: "Ocultar senha", es: "Ocultar contraseña" }),
    submit: t({ pt: "Entrar", es: "Ingresar" })
  },
  links: {
    forgotPassword: t({ pt: "Esqueci a senha", es: "Olvidé la contraseña" }),
    firstAccessPrompt: t({ pt: "Comprou e nunca acessou?", es: "¿Compraste y nunca accediste?" }),
    firstAccessCta: t({ pt: "Primeiro acesso", es: "Primer acceso" }),
    notClient: t({ pt: "Ainda não sou cliente.", es: "Todavía no soy cliente." }),
    knowMore: t({ pt: "Quero conhecer", es: "Quiero conocer" })
  },
  feedback: {
    invalidEmail: t({ pt: "Digite um e-mail válido.", es: "Escribe un correo válido." }),
    missingPassword: t({ pt: "Digite sua senha.", es: "Escribe tu contraseña." }),
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
  error.value = "";
  if (!/^\S+@\S+\.\S+$/.test(email.value.trim())) {
    error.value = viewCopy.feedback.invalidEmail;
    return;
  }
  if (!password.value) {
    error.value = viewCopy.feedback.missingPassword;
    return;
  }
  loading.value = true;
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
  background: #0a6346;
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
/* O PNG do logo tem margem transparente em cima e embaixo (o desenho ocupa ~53%
   da altura). O tamanho vem da largura, e a margem negativa tira essa folga. */
.lg-logo {
  width: 180px;
  max-width: 70%;
  height: auto;
  margin: -23px 0;
  filter: drop-shadow(0 2px 12px rgba(0, 0, 0, 0.3));
}
/* O cartão é sempre claro, também com o painel no tema escuro. */
.lg-card {
  width: 100%;
  padding: 28px;
  border-radius: 22px;
  background: #ffffff;
  color: #0e1f17;
  box-shadow: 0 30px 60px -20px rgba(0, 0, 0, 0.6);
}
.lg-head {
  margin-bottom: 24px;
  text-align: center;
}
.lg-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #0e1f17;
}
.lg-head p {
  margin: 4px 0 0;
  font-size: 14px;
  color: #5a6d62;
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
.lg-field input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #d8e0d2;
  border-radius: 12px;
  background: #eef2ec;
  font-size: 15px;
  color: #0e1f17;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
}
.lg-field input:focus {
  outline: none;
  border-color: #0a6346;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(10, 99, 70, 0.18);
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
.lg-link {
  font-weight: 600;
  color: #0a6346;
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
  background: #0a6346;
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  box-shadow: 0 10px 22px -10px rgba(10, 99, 70, 0.8);
  transition: background-color 0.15s ease, transform 0.15s ease;
}
.lg-submit:hover:not(:disabled) {
  background: #084d37;
  transform: translateY(-1px);
}
.lg-submit:disabled {
  opacity: 0.8;
  cursor: progress;
}
.lg-spin {
  width: 16px;
  height: 16px;
  animation: lg-spin 0.8s linear infinite;
}
.lg-forgot {
  margin-top: 14px;
  text-align: center;
  font-size: 13px;
}
.lg-first {
  margin: 14px 0 0;
  text-align: center;
  font-size: 13px;
  color: #5a6d62;
}
.lg-register {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(10, 17, 14, 0.28);
  font-size: 14px;
  color: rgba(230, 242, 234, 0.88);
  backdrop-filter: blur(6px);
  transition: background-color 0.15s ease;
}
.lg-register:hover {
  background: rgba(10, 17, 14, 0.42);
}
.lg-register b,
.lg-register svg {
  color: #90ee8f;
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
  color: rgba(230, 242, 234, 0.7);
}
:where(.lg a, .lg button, .lg input):focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}
.lg-card :where(a, button):focus-visible {
  outline-color: #0a6346;
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
  .lg-logo {
    width: 160px;
    margin: -20px 0;
  }
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
