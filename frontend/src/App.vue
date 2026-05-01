<template>
  <div :class="appShellClass">
    <router-view />
    <transition name="fade">
      <div
        v-if="showPublicCookieBanner"
        class="fixed inset-x-6 bottom-4 z-40 md:left-1/2 md:top-auto md:bottom-8 md:-translate-x-1/2 md:w-3/4"
      >
        <div class="flex flex-col gap-2 rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-2xl backdrop-blur">
          <div class="flex flex-col items-center gap-3 text-center md:flex-row md:items-center md:justify-center md:text-left">
            <div class="md:flex-1">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">{{ cookieHeading }}</p>
              <p class="text-sm text-slate-600">
                <span class="block">{{ cookieLine1 }}</span>
                <span class="block">{{ cookieLine2 }}</span>
              </p>
            </div>
            <div class="flex w-full flex-wrap items-center justify-center gap-2 md:w-auto md:justify-center">
              <button
                type="button"
                class="order-1 text-[11px] font-semibold text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline md:order-none"
                @click="dismissCookies"
              >
                {{ cookieRejectLabel }}
              </button>
              <button
                type="button"
                class="order-2 w-full rounded-full bg-slate-900 px-5 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 md:order-none md:w-auto md:text-sm"
                @click="acceptCookies"
              >
                {{ cookieAcceptLabel }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { createLocalizer, getCurrentLanguage } from "./utils/i18n";

const route = useRoute();
const localize = createLocalizer(getCurrentLanguage());
const cookieCopy = {
  heading: { pt: "Cookies", es: "Cookies" },
  line1: {
    pt: "Utilizamos cookies para manter sua sessão segura e oferecer uma melhor experiência nas páginas publicadas.",
    es: "Utilizamos cookies para mantener tu sesión segura y ofrecer una mejor experiencia en las páginas publicadas."
  },
  line2: {
    pt: "Continuando sem aceitar, alguns recursos podem não funcionar.",
    es: "Si continúas sin aceptar, algunos recursos pueden no funcionar."
  },
  accept: { pt: "Aceitar cookies", es: "Aceptar cookies" },
  reject: { pt: "Continuar sem aceitar", es: "Continuar sin aceptar" }
} as const;
const COOKIE_KEY = "global_cookie_consent";
const showPublicCookieBanner = ref(false);
const cookieHeading = localize(cookieCopy.heading);
const cookieLine1 = localize(cookieCopy.line1);
const cookieLine2 = localize(cookieCopy.line2);
const cookieAcceptLabel = localize(cookieCopy.accept);
const cookieRejectLabel = localize(cookieCopy.reject);
const publicRouteNames = new Set(["public-page", "custom-domain-default", "custom-domain-page"]);
const publicShellClass = "public-shell";
const adminShellClass = "admin-shell";
const isPublicShellRoute = computed(() => {
  const routeName = typeof route.name === "string" ? route.name : "";
  return publicRouteNames.has(routeName);
});
const appShellClass = computed(() =>
  isPublicShellRoute.value
    ? "min-h-screen bg-black text-white"
    : "min-h-screen bg-slate-50 text-slate-900"
);

const syncBodyShell = (usePublicShell: boolean) => {
  if (typeof document === "undefined") return;
  document.body.classList.toggle(publicShellClass, usePublicShell);
  document.body.classList.toggle(adminShellClass, route.path.startsWith("/admin"));
};

const checkCookieConsent = () => {
  if (typeof window === "undefined") return;
  const consent = localStorage.getItem(COOKIE_KEY);
  const isAdmin = route.path.startsWith("/admin");
  showPublicCookieBanner.value = !consent && !isAdmin;
};

const acceptCookies = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_KEY, "accepted");
  }
  showPublicCookieBanner.value = false;
};

const dismissCookies = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_KEY, "dismissed");
  }
  showPublicCookieBanner.value = false;
};

watch(
  () => route.path,
  () => {
    checkCookieConsent();
  }
);

watch(
  isPublicShellRoute,
  value => {
    syncBodyShell(value);
  },
  { immediate: true }
);

onMounted(() => {
  checkCookieConsent();
});

onBeforeUnmount(() => {
  syncBodyShell(false);
});
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
