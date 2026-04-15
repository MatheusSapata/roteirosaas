<template>
  <div class="settings-view space-y-6">
    <div class="rounded-3xl border border-slate-200 bg-white p-3 shadow-sm">
      <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="rounded-2xl px-4 py-3 text-left text-sm font-semibold transition"
          :class="activeTab === tab.id ? 'bg-[#41ce5f] text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          @click="setActiveTab(tab.id)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <section v-show="activeTab === 'profile'">
      <ProfileView />
    </section>

    <section v-show="activeTab === 'agency'">
      <AgencySettingsView />
    </section>

    <section v-show="activeTab === 'domains'">
      <AgencyDomainsView />
    </section>

    <section v-show="activeTab === 'fleet'">
      <SeatLayoutsView />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import AgencyDomainsView from "./AgencyDomainsView.vue";
import AgencySettingsView from "./AgencySettingsView.vue";
import ProfileView from "./ProfileView.vue";
import SeatLayoutsView from "./SeatLayoutsView.vue";
import { createAdminLocalizer } from "../../utils/adminI18n";

type SettingsTabId = "profile" | "agency" | "domains" | "fleet";

const VALID_TABS: SettingsTabId[] = ["profile", "agency", "domains", "fleet"];

const route = useRoute();
const router = useRouter();
const t = createAdminLocalizer();

const viewCopy = {
  header: {
    eyebrow: t({ pt: "Painel", es: "Panel" }),
    title: t({ pt: "Configuracoes", es: "Configuraciones" }),
    description: t({
      pt: "Centralize os dados do perfil, da agencia, dos dominios e da frota em um unico lugar.",
      es: "Centraliza los datos del perfil, de la agencia, de los dominios y de la flota en un solo lugar."
    })
  },
  tabs: {
    profile: t({ pt: "Perfil", es: "Perfil" }),
    agency: t({ pt: "Minha Agencia", es: "Mi Agencia" }),
    domains: t({ pt: "Dominios", es: "Dominios" }),
    fleet: t({ pt: "Frota", es: "Flota" })
  }
} as const;

const normalizeTab = (value: unknown): SettingsTabId => {
  const normalized = typeof value === "string" ? (value as SettingsTabId) : "profile";
  return VALID_TABS.includes(normalized) ? normalized : "profile";
};

const activeTab = computed<SettingsTabId>(() => normalizeTab(route.query.tab));

const tabs = [
  { id: "profile" as const, label: viewCopy.tabs.profile },
  { id: "agency" as const, label: viewCopy.tabs.agency },
  { id: "domains" as const, label: viewCopy.tabs.domains },
  { id: "fleet" as const, label: viewCopy.tabs.fleet }
];

const setActiveTab = (tab: SettingsTabId) => {
  if (activeTab.value === tab) return;
  router.replace({
    name: "settings",
    query: { ...route.query, tab }
  });
};
</script>

<style scoped>
:global(.dark-theme .settings-view > .rounded-3xl) {
  background-color: #202020;
  border-color: rgba(255, 255, 255, 0.12);
}
</style>
