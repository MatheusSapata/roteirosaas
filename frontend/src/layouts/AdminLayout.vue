<template>
  <div class="min-h-screen light-theme">
    <div class="flex min-h-screen">
      <aside
        class="hidden w-64 flex-shrink-0 flex-col justify-between border-r border-slate-200 bg-white/90 px-4 py-6 text-slate-800 shadow-md md:flex md:sticky md:top-0 md:h-screen"
      >
        <div class="flex flex-1 flex-col overflow-y-auto">
          <div class="mb-8 flex items-center justify-center gap-3">
            <template v-if="agencyLogo">
              <img :src="agencyLogo" alt="Logo" class="h-16 w-16 rounded-lg object-contain" />
            </template>
            <template v-else>
              <div class="min-w-0">
                <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Painel</p>
                <p class="text-lg font-bold truncate">{{ agencyName || 'Agencia' }}</p>
              </div>
            </template>
          </div>
          <nav class="flex-1 space-y-1">
            <RouterLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition"
              :class="isActive(item.to) ? activeClass : inactiveClass"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="navIcons[item.to] || navIcons['/admin/dashboard']"></path>
                </svg>
              </span>
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>
        </div>

        <div class="mt-8 border-t border-slate-200 pt-4">
          <button
            type="button"
            @click="handleLogout"
            class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-red-50 hover:text-red-600"
          >
            <span class="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-red-600">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3v9m5.657-6.657a8 8 0 1 1-11.314 0" />
              </svg>
            </span>
            <span>Sair</span>
          </button>
        </div>
      </aside>

      <main class="flex-1">
        <header class="flex items-center justify-between bg-white px-4 py-3 text-slate-900 shadow-sm">
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 text-slate-700 transition hover:bg-slate-50 md:hidden"
              @click="mobileMenuOpen = true"
            >
              <span class="sr-only">Abrir menu</span>
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 class="text-lg font-bold">Dashboard</h1>
          </div>
          <div class="flex items-center gap-2"></div>
        </header>
        <div class="px-3 py-4 md:px-6 md:py-6">
          <RouterView />
        </div>
      </main>
    </div>

    <transition name="fade">
      <div
        v-if="mobileMenuOpen"
        class="fixed inset-0 z-40 flex md:hidden"
      >
        <div class="flex-1 bg-slate-900/60" @click="mobileMenuOpen = false"></div>
        <div class="w-72 max-w-full bg-white p-5 shadow-2xl">
          <div class="mb-6 flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Menu</p>
              <p class="text-sm font-semibold text-slate-900 truncate">{{ agencyName || 'Agencia' }}</p>
            </div>
            <button
              type="button"
              class="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-600"
              @click="mobileMenuOpen = false"
            >
              <span class="sr-only">Fechar</span>
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M6 6l12 12M6 18 18 6" />
              </svg>
            </button>
          </div>
          <nav class="space-y-1">
            <RouterLink
              v-for="item in navItems"
              :key="'mobile-' + item.to"
              :to="item.to"
              class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition"
              :class="isActive(item.to) ? activeClass : inactiveClass"
              @click="mobileMenuOpen = false"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="navIcons[item.to] || navIcons['/admin/dashboard']"></path>
                </svg>
              </span>
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>
          <div class="mt-6 border-t border-slate-200 pt-4">
            <button
              type="button"
              @click="handleLogout"
              class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-red-50 hover:text-red-600"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-red-600">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 3v9m5.657-6.657a8 8 0 1 1-11.314 0" />
                </svg>
              </span>
              <span>Sair</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showWelcomeDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Upgrade exclusivo</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Você ganhou {{ auth.user?.trial_plan?.toUpperCase() }} por 7 dias!</h2>
          <p class="mt-2 text-sm text-slate-600">
            Aproveite todos os recursos do plano premium até {{ formattedDate }}. Explore integrações, limites liberados e páginas ilimitadas.
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="acknowledgeTrial('start')"
            >
              Começar agora
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showEndDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-500">Período finalizado</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Gostou do plano Infinity?</h2>
          <p class="mt-2 text-sm text-slate-600">
            Seu acesso promocional terminou. Escolha manter o plano completo ou voltar ao plano original.
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="acknowledgeTrial('end')"
            >
              Continuar no plano anterior
            </button>
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="acknowledgeTrial('end', true)"
            >
              Assinar Infinity
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { resolveMediaUrl } from "../utils/media";
import api from "../services/api";
import { useAgencyStore } from "../store/useAgencyStore";
import { useAuthStore } from "../store/useAuthStore";

const route = useRoute();
const router = useRouter();
const agencyStore = useAgencyStore();
const auth = useAuthStore();

const navIcons: Record<string, string> = {
  "/admin/dashboard": "M12 2a8 8 0 1 1-8 8 8 8 0 0 1 8-8zm0 3v6l4 2",
  "/admin/pages": "M4 4h16v3H4zm0 6h16v3H4zm0 6h10v3H4z",
  "/admin/planos": "M12 3l8 4v8c0 5-8 7-8 7s-8-2-8-7V7z",
  "/admin/integracoes": "M12 3v3m0 12v3m9-9h-3M6 12H3m13.07 5.07l-2.12-2.12M7.05 7.05 4.93 4.93m0 14.14 2.12-2.12m10.02-10.02 2.12-2.12",
  "/admin/agency": "M4 11V5h16v6M2 19h20v-2l-2-6H4l-2 6z",
  "/admin/perfil": "M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5zm-7 8v-1a5 5 0 0 1 10 0v1z",
  "/admin/administracao": "M4 5h16v4H4zm2 6h12v10H6z"
};

const navItems = computed(() => {
  const items = [
    { label: "Dashboard", to: "/admin/dashboard" },
    { label: "Paginas", to: "/admin/pages" },
    { label: "Planos", to: "/admin/planos" },
    { label: "Integracoes", to: "/admin/integracoes" },
    { label: "Configuracoes", to: "/admin/agency" },
    { label: "Perfil", to: "/admin/perfil" }
  ];
  if (auth.user?.is_superuser) {
    items.splice(1, 0, { label: "Admin Master", to: "/admin/administracao" });
  }
  return items;
});

const activeClass = "bg-slate-100 text-slate-900";
const inactiveClass = "text-slate-700 hover:bg-slate-100";

const agencyName = computed(() => agencyStore.currentAgency?.name || agencyStore.agencies[0]?.name || "");
const agencyLogo = computed(() =>
  resolveMediaUrl(agencyStore.currentAgency?.logo_url || agencyStore.agencies[0]?.logo_url || "")
);

const isActive = (to: string) => route.path.startsWith(to);

const handleLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};

const showWelcomeDialog = ref(false);
const showEndDialog = ref(false);
const mobileMenuOpen = ref(false);

const trialStartDate = computed(() => (auth.user?.trial_started_at ? new Date(auth.user.trial_started_at) : null));
const trialEndDate = computed(() => (auth.user?.trial_ends_at ? new Date(auth.user.trial_ends_at) : null));
const trialActive = computed(() => {
  if (!auth.user?.trial_plan) return false;
  if (!trialStartDate.value || !trialEndDate.value) return false;
  const now = new Date();
  return now >= trialStartDate.value && now <= trialEndDate.value;
});

watch(
  () => [auth.user?.id, trialActive.value, auth.user?.trial_ack_start],
  () => {
    showWelcomeDialog.value = Boolean(trialActive.value && auth.user?.trial_ack_start === false);
  },
  { immediate: true }
);

watch(
  () => route.path,
  () => {
    mobileMenuOpen.value = false;
  }
);

watch(
  () => [auth.user?.id, auth.user?.trial_ack_end, auth.user?.trial_plan, auth.user?.trial_ends_at],
  () => {
    const ended = !auth.user?.trial_plan && auth.user?.trial_ack_end === false && !!auth.user?.trial_original_plan;
    const expiredByDate =
      auth.user?.trial_ack_end === false &&
      auth.user?.trial_plan &&
      trialEndDate.value &&
      new Date() > trialEndDate.value;
    showEndDialog.value = Boolean(ended || expiredByDate);
  },
  { immediate: true }
);

const acknowledgeTrial = async (stage: "start" | "end", redirectToPlans = false) => {
  try {
    await api.post("/auth/trial/ack", { stage });
    await auth.fetchProfile();
    if (stage === "start") {
      showWelcomeDialog.value = false;
    } else {
      showEndDialog.value = false;
      if (redirectToPlans) {
        router.push("/admin/planos");
      }
    }
  } catch (err) {
    console.error("Erro ao confirmar trial", err);
  }
};

const formattedDate = computed(() => (trialEndDate.value ? trialEndDate.value.toLocaleDateString() : ""));

onMounted(async () => {
  if (!agencyStore.agencies.length) {
    await agencyStore.loadAgencies();
  }
  if (!auth.user && auth.token) {
    await auth.fetchProfile();
  }
});
</script>

<style>
.light-theme {
  background: #f8fafc;
  color: #0f172a;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>


