<template>
  <div class="ih">
    <div class="ih-head">
      <div class="min-w-0">
        <p class="ih-eyebrow">Configurar</p>
        <h1 class="ih-title">Integrações</h1>
        <p class="ih-sub">Conecte o Roteiro Online às ferramentas que a sua agência já usa.</p>
      </div>
      <div class="ih-actions"><slot name="actions" /></div>
    </div>
    <nav class="ih-tabs" aria-label="Seções de integrações">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="ih-tab"
        :class="{ on: route.path === tab.path }"
      >
        <i v-if="tab.on !== undefined" class="ih-dot" :class="{ 'is-on': tab.on }" :title="tab.on ? 'Configurado' : 'Não configurado'"></i>
        {{ tab.label }}
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../../store/useAuthStore";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { integrationStatus, loadIntegrationStatus, loadWhatsAppStatus } from "../../../composables/useIntegrationStatus";

const route = useRoute();
const auth = useAuthStore();
const agencyStore = useAgencyStore();

// Mesma regra do menu lateral: WhatsApp só nos planos Escala e Teste.
const normalizePlanKey = (value: string | null | undefined) => {
  const key = String(value || "").trim().toLowerCase();
  if (key === "escala" || key === "infinity" || key === "scale") return "scale";
  if (key === "teste" || key === "test") return "test";
  return key;
};
const hasWhatsAppPlanAccess = computed(() => {
  const allowed = new Set(["scale", "test"]);
  return allowed.has(normalizePlanKey((auth.user as any)?.trial_plan)) || allowed.has(normalizePlanKey(auth.user?.plan));
});

const tabs = computed(() =>
  [
    { label: "Visão geral", path: "/admin/integracoes", on: undefined as boolean | undefined },
    { label: "Rastreamento", path: "/admin/integracoes/rastreamento", on: (integrationStatus.pixels || 0) > 0 },
    { label: "Viaje On", path: "/admin/integracoes/viajeon", on: !!integrationStatus.viajeon },
    { label: "ViajeChat", path: "/admin/integracoes/viajechat", on: !!integrationStatus.viajechat },
    { label: "WhatsApp", path: "/admin/integracoes/atendimento", on: !!integrationStatus.whatsapp, whatsapp: true }
  ].filter(tab => !tab.whatsapp || hasWhatsAppPlanAccess.value)
);

onMounted(() => {
  loadIntegrationStatus({ agencyId: agencyStore.currentAgencyId, whatsapp: hasWhatsAppPlanAccess.value });
});
// A agência pode chegar depois da tela; aí busca só a situação do WhatsApp.
watch(
  () => agencyStore.currentAgencyId,
  (agencyId, previous) => {
    if (agencyId && !previous && hasWhatsAppPlanAccess.value) loadWhatsAppStatus(agencyId);
  }
);
</script>

<style scoped>
.ih { display: flex; flex-direction: column; gap: 16px; }
.ih-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.ih-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.ih-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; color: var(--foreground); }
.ih-sub { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.ih-actions { display: flex; flex-shrink: 0; gap: 8px; }
.ih-actions:empty { display: none; }
.ih-tabs { display: flex; gap: 4px; overflow-x: auto; border-bottom: 1px solid var(--border); }
.ih-tab { display: inline-flex; flex-shrink: 0; align-items: center; gap: 8px; padding: 10px 14px; font-size: 13.5px; font-weight: 600; white-space: nowrap; color: var(--muted-foreground); }
.ih-tab:hover { color: var(--foreground); }
.ih-tab.on { box-shadow: inset 0 -2px 0 var(--primary); color: var(--foreground); }
.ih-dot { width: 7px; height: 7px; border-radius: 999px; background: color-mix(in srgb, var(--muted-foreground) 70%, transparent); }
.ih-dot.is-on { background: var(--primary); }
@media (max-width: 640px) {
  .ih-head { flex-direction: column; align-items: flex-start; }
}
</style>
