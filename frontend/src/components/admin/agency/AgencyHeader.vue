<template>
  <div class="ah">
    <div class="ah-head">
      <div class="min-w-0">
        <p class="ah-eyebrow">Configurar</p>
        <h1 class="ah-title">Minha agência</h1>
        <p class="ah-sub">Dados que aparecem nas suas páginas, quem usa a conta e as faturas do plano.</p>
      </div>
      <div class="ah-actions"><slot name="actions" /></div>
    </div>
    <nav class="ah-tabs" aria-label="Seções de Minha agência">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="ah-tab"
        :class="{ on: route.path === tab.path }"
      >
        {{ tab.label }}
        <span v-if="tab.count !== null" class="ah-count">{{ tab.count }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../../store/useAuthStore";
import { canAccessPermission, type PermissionKey } from "../../../utils/permissions";
import { agencyCounts, loadAgencyCounts } from "../../../composables/useAgencyCounts";

const route = useRoute();
const auth = useAuthStore();

// Mesmas regras do menu lateral.
const hasPermission = (permission: PermissionKey) =>
  canAccessPermission(permission, {
    isOwner: auth.user?.is_owner,
    selected: auth.user?.permissions || [],
    plan: auth.user?.plan,
    effective: auth.user?.effective_permissions || []
  });
const canManageTeam = computed(() => {
  const isOwner = auth.user?.is_owner ?? true;
  const role = String(auth.user?.role || "admin").toLowerCase();
  return isOwner && (role === "admin" || role === "owner") && hasPermission("team_management");
});
const canSeeSettings = computed(() => hasPermission("settings"));

const tabs = computed(() =>
  [
    { label: "Dados da agência", path: "/admin/agency", count: null as number | null, show: canSeeSettings.value },
    { label: "Equipe", path: "/admin/agency/team", count: agencyCounts.team, show: canManageTeam.value },
    { label: "Faturas", path: "/admin/agency/invoices", count: agencyCounts.invoices, show: canSeeSettings.value }
  ].filter(tab => tab.show)
);

onMounted(() => {
  loadAgencyCounts({ team: canManageTeam.value, invoices: canSeeSettings.value });
});
</script>

<style scoped>
.ah { display: flex; flex-direction: column; gap: 16px; }
.ah-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.ah-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.ah-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; color: var(--foreground); }
.ah-sub { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.ah-actions { display: flex; flex-shrink: 0; gap: 8px; }
.ah-actions:empty { display: none; }
.ah-tabs { display: flex; gap: 4px; overflow-x: auto; border-bottom: 1px solid var(--border); }
.ah-tab { display: inline-flex; flex-shrink: 0; align-items: center; gap: 8px; padding: 10px 14px; font-size: 13.5px; font-weight: 600; white-space: nowrap; color: var(--muted-foreground); }
.ah-tab:hover { color: var(--foreground); }
.ah-tab.on { box-shadow: inset 0 -2px 0 var(--primary); color: var(--foreground); }
.ah-count { border-radius: 999px; background: var(--muted); padding: 0 7px; font-size: 11px; color: var(--muted-foreground); }
.ah-tab.on .ah-count { background: var(--accent); color: var(--accent-foreground); }
@media (max-width: 640px) {
  .ah-head { flex-direction: column; align-items: flex-start; }
}
</style>
