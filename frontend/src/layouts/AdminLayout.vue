<template>
  <div class="min-h-screen light-theme overflow-x-hidden">
    <div class="flex min-h-screen">
      <aside
        class="hidden w-64 flex-shrink-0 flex-col justify-between border-r border-slate-200 bg-white/90 px-4 py-6 text-slate-800 shadow-md md:fixed md:inset-y-0 md:left-0 md:flex"
      >
        <div class="flex flex-1 flex-col overflow-y-auto">
          <div class="mb-8 flex items-center justify-center">
            <img :src="sidebarLogoSrc" alt="Roteiro Online" class="max-h-16 w-full object-contain" />
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
                <svg
                  viewBox="0 0 24 24"
                  class="h-4 w-4"
                  v-html="navIcons[item.to] || navIcons.default"
                ></svg>
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

      <main class="flex-1 overflow-x-hidden md:ml-64">
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
                <svg
                  viewBox="0 0 24 24"
                  class="h-4 w-4"
                  v-html="navIcons[item.to] || navIcons.default"
                ></svg>
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
        <div class="flex-1 bg-slate-900/60" @click="mobileMenuOpen = false"></div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showWelcomeDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">Upgrade exclusivo</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Você ganhou o plano {{ trialPlanName }} por 7 dias!</h2>
          <p class="mt-2 text-sm text-slate-600">
            Aproveite todos os recursos do plano premium até {{ formattedDate }}. Explore integrações, limites liberados e seções ilimitadas dentro de cada roteiro.
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
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Gostou do plano {{ planLabels.infinity }}?</h2>
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
              Assinar {{ planLabels.infinity }}
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
import SidebarLogo from "../assets/Logo Cor - Roteiro Online.png";
import api from "../services/api";
import { useAgencyStore } from "../store/useAgencyStore";
import { useAuthStore } from "../store/useAuthStore";
import { getPlanLabel, planLabels } from "../utils/planLabels";

const route = useRoute();
const router = useRouter();
const agencyStore = useAgencyStore();
const auth = useAuthStore();

const navIcons: Record<string, string> = {
  default: '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 2a8 8 0 1 1-8 8 8 8 0 0 1 8-8zm0 3v6l4 2" />',
  "/admin/dashboard": '<path fill="currentColor" d="M13 8V4q0-.425.288-.712T14 3h6q.425 0 .713.288T21 4v4q0 .425-.288.713T20 9h-6q-.425 0-.712-.288T13 8M3 12V4q0-.425.288-.712T4 3h6q.425 0 .713.288T11 4v8q0 .425-.288.713T10 13H4q-.425 0-.712-.288T3 12m10 8v-8q0-.425.288-.712T14 11h6q.425 0 .713.288T21 12v8q0 .425-.288.713T20 21h-6q-.425 0-.712-.288T13 20M3 20v-4q0-.425.288-.712T4 15h6q.425 0 .713.288T11 16v4q0 .425-.288.713T10 21H4q-.425 0-.712-.288T3 20m2-9h4V5H5zm10 8h4v-6h-4zm0-12h4V5h-4zM5 19h4v-2H5zm4-2"/>' ,
  "/admin/pages": '<g fill="currentColor" fill-rule="evenodd" clip-rule="evenodd"><path d="M9.918 3.632c-.855.652-1.85 1.645-3.246 3.04s-2.388 2.39-3.04 3.246c-.64.838-.882 1.454-.882 2.082s.242 1.244.882 2.082c.652.855 1.645 1.85 3.04 3.246s2.39 2.387 3.246 3.04c.838.64 1.454.882 2.082.882s1.244-.242 2.082-.882c.855-.652 1.85-1.645 3.246-3.04s2.387-2.39 3.04-3.246c.64-.838.882-1.454.882-2.082s-.242-1.244-.882-2.082c-.652-.855-1.645-1.85-3.04-3.246s-2.39-2.388-3.246-3.04c-.838-.64-1.454-.882-2.082-.882s-1.244.242-2.082.882m-.91-1.193C9.98 1.698 10.912 1.25 12 1.25s2.02.448 2.992 1.19c.945.72 2.01 1.785 3.356 3.132l.08.08c1.347 1.347 2.412 2.411 3.133 3.356c.741.972 1.189 1.904 1.189 2.992s-.448 2.02-1.19 2.992c-.72.945-1.785 2.01-3.132 3.356l-.08.08c-1.347 1.347-2.411 2.412-3.356 3.133c-.972.741-1.904 1.189-2.992 1.189s-2.02-.448-2.992-1.19c-.945-.72-2.01-1.785-3.356-3.132l-.08-.08c-1.347-1.347-2.412-2.411-3.133-3.356C1.698 14.02 1.25 13.088 1.25 12s.448-2.02 1.19-2.992c.72-.945 1.785-2.01 3.132-3.356l.08-.08C6.999 4.225 8.063 3.16 9.008 2.439"/><path d="M12.786 8.487a.75.75 0 0 1 1.06-.034l2.667 2.5a.75.75 0 0 1 0 1.094l-2.667 2.5a.75.75 0 0 1-1.026-1.094l1.283-1.203h-3.436c-.334 0-.844.1-1.247.372c-.363.245-.67.643-.67 1.378a.75.75 0 0 1-1.5 0c0-1.265.582-2.117 1.33-2.622c.709-.478 1.532-.628 2.087-.628h3.436L12.82 9.547a.75.75 0 0 1-.034-1.06"/></g>',
  "/admin/integracoes": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M18.364 19.364a9 9 0 1 0-12.728 0"/><path d="M15.536 16.536a5 5 0 1 0-7.072 0"/><path d="M11 13a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/></g>',
  "/admin/agency": '<path fill="currentColor" d="M16 12a4 4 0 1 1-8 0a4 4 0 0 1 8 0m-1.5 0a2.5 2.5 0 1 0-5 0a2.5 2.5 0 0 0 5 0"/><path fill="currentColor" d="M12 1q.4 0 .797.028c.763.055 1.345.617 1.512 1.304l.352 1.45c.019.078.09.171.225.221q.37.134.728.302c.13.061.246.044.315.002l1.275-.776c.603-.368 1.411-.353 1.99.147q.604.524 1.128 1.129c.501.578.515 1.386.147 1.99l-.776 1.274c-.042.069-.058.185.002.315q.168.357.303.728c.048.135.142.205.22.225l1.45.352c.687.167 1.249.749 1.303 1.512q.057.797 0 1.594c-.054.763-.616 1.345-1.303 1.512l-1.45.352c-.078.019-.171.09-.221.225q-.134.372-.302.728c-.061.13-.044.246-.002.315l.776 1.275c.368.603.353 1.411-.147 1.99q-.524.605-1.129 1.128c-.578.501-1.386.515-1.99.147l-1.274-.776c-.069-.042-.185-.058-.314.002a9 9 0 0 1-.729.303c-.135.048-.205.142-.225.22l-.352 1.45c-.167.687-.749 1.249-1.512 1.303q-.797.057-1.594 0c-.763-.054-1.345-.616-1.512-1.303l-.352-1.45c-.019-.078-.09-.171-.225-.221a8 8 0 0 1-.728-.302c-.13-.061-.246-.044-.315-.002l-1.275.776c-.603.368-1.411.353-1.99-.147q-.605-.524-1.128-1.129c-.501-.578-.515-1.386-.147-1.99l.776-1.274c.042-.069.058-.185-.002-.314a9 9 0 0 1-.303-.729c-.048-.135-.142-.205-.22-.225l-1.45-.352c-.687-.167-1.249-.749-1.304-1.512a11 11 0 0 1 0-1.594c.055-.763.617-1.345 1.304-1.512l1.45-.352c.078-.019.171-.09.221-.225q.134-.372.302-.728c.061-.13.044-.246.002-.315l-.776-1.275c-.368-.603-.353-1.411.147-1.99q.524-.605 1.129-1.128c.578-.501 1.386-.515 1.99-.147l1.274.776c.069.042.185.058.315-.002q.357-.168.728-.303c.135-.048.205-.142.225-.22l.352-1.45c.167-.687.749-1.249 1.512-1.304Q11.598 1 12 1"/>',
  "/admin/perfil": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/></g>',
  "/admin/planos": '<path fill="currentColor" d="m21.41 11.58-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58s1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41s-.23-1.06-.59-1.42M13 20.01L4 11V4h7v-.01l9 9z"/><circle cx="6.5" cy="6.5" r="1.5" fill="currentColor"/>',
  "/admin/administracao": '<path fill="currentColor" d="M16 12a4 4 0 1 1-8 0a4 4 0 0 1 8 0m-1.5 0a2.5 2.5 0 1 0-5 0a2.5 2.5 0 0 0 5 0"/><path fill="currentColor" d="M12 1q.4 0 .797.028c.763.055 1.345.617 1.512 1.304l.352 1.45c.019.078.09.171.225.221q.37.134.728.302c.13.061.246.044.315.002l1.275-.776c.603-.368 1.411-.353 1.99.147q.604.524 1.128 1.129c.501.578.515 1.386.147 1.99l-.776 1.274c-.042.069-.058.185.002.315q.168.357.303.728c.048.135.142.205.22.225l1.45.352c.687.167 1.249.749 1.303 1.512q.057.797 0 1.594c-.054.763-.616 1.345-1.303 1.512l-1.45.352c-.078.019-.171.09-.221.225q-.134.372-.302.728c-.061.13-.044.246-.002.315l.776 1.275c.368.603.353 1.411-.147 1.99q-.524.605-1.129 1.128c-.578.501-1.386.515-1.99.147l-1.274-.776c-.069-.042-.185-.058-.314.002a9 9 0 0 1-.729.303c-.135.048-.205.142-.225.22l-.352 1.45c-.167.687-.749 1.249-1.512 1.303q-.797.057-1.594 0c-.763-.054-1.345-.616-1.512-1.303l-.352-1.45c-.019-.078-.09-.171-.225-.221a8 8 0 0 1-.728-.302c-.13-.061-.246-.044-.315-.002l-1.275.776c-.603.368-1.411.353-1.99-.147q-.605-.524-1.128-1.129c-.501-.578-.515-1.386-.147-1.99l.776-1.274c.042-.069.058-.185-.002-.314a9 9 0 0 1-.303-.729c-.048-.135-.142-.205-.22-.225l-1.45-.352c-.687-.167-1.249-.749-1.304-1.512a11 11 0 0 1 0-1.594c.055-.763.617-1.345 1.304-1.512l1.45-.352c.078-.019.171-.09.221-.225q.134-.372.302-.728c.061-.13.044-.246.002-.315l-.776-1.275c-.368-.603-.353-1.411.147-1.99q.524-.605 1.129-1.128c.578-.501 1.386-.515 1.99-.147l1.274.776c.069.042.185.058.315-.002q.357-.168.728-.303c.135-.048.205-.142.225-.22l.352-1.45c.167-.687.749-1.249 1.512-1.304Q11.598 1 12 1"/>'
};

const navItems = computed(() => {
  const items = [
    { label: "Dashboard", to: "/admin/dashboard" },
    { label: "Páginas", to: "/admin/pages" },
    { label: "Integrações", to: "/admin/integracoes" },
    { label: "Configurações", to: "/admin/agency" },
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
const sidebarLogoSrc = SidebarLogo;

const isActive = (to: string) => route.path.startsWith(to);

const handleLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};

const showWelcomeDialog = ref(false);
const showEndDialog = ref(false);
const mobileMenuOpen = ref(false);
const trialPlanName = computed(() => getPlanLabel(auth.user?.trial_plan));

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


