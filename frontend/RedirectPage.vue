<template>
  <div class="min-h-screen flex items-center justify-center bg-white px-4">
    <div class="text-center">
      <h1 class="text-xl font-semibold text-slate-900">{{ redirectHeading }}</h1>
      <p class="mt-2 text-sm text-slate-500">{{ redirectDescription }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import { createLocalizer, getCurrentLanguage } from "./src/utils/i18n";

type RedirectMap = Record<string, string>;

const route = useRoute();
const localize = createLocalizer(getCurrentLanguage());
const redirectCopy = {
  heading: { pt: "Redirecionando...", es: "Redirigiendo..." },
  description: { pt: "Aguarde um instante.", es: "Espera un momento." }
} as const;
const redirectHeading = localize(redirectCopy.heading);
const redirectDescription = localize(redirectCopy.description);

const redirects: RedirectMap = {
  profissionalmensal: "https://pay.cakto.com.br/7o7zrup_800651",
  profissionalanual: "https://pay.cakto.com.br/nxc42uz",
  agenciamensal: "https://pay.cakto.com.br/n7vnc73_800688",
  agenciaanual: "https://pay.cakto.com.br/32uvp8b",
  escalamensal: "https://pay.cakto.com.br/iexkakw_800692",
  escalaanual: "https://pay.cakto.com.br/pxzgp5s",
  profissional: "https://pay.cakto.com.br/7o7zrup_818166",
  agencia: "https://pay.cakto.com.br/n7vnc73_818167",
  escala: "https://pay.cakto.com.br/iexkakw_818426"
};

onMounted(() => {
  const slugParam = route.params.slug;
  const slug = Array.isArray(slugParam) ? slugParam[0] : slugParam;
  const target = slug ? redirects[slug] : undefined;
  window.location.href = target || "/";
});
</script>
