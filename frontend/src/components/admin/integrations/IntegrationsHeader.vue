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
        :class="{ on: route.path === tab.path || (tab.alsoActive || []).includes(route.path) }"
      >
        {{ tab.label }}
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../../store/useAuthStore";

const route = useRoute();
const auth = useAuthStore();

// Mesma regra do menu lateral: "Notificações" (WhatsApp) só nos planos Escala e Teste.
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
    { label: "Rastreamento", path: "/admin/integracoes/rastreamento" },
    { label: "Integrações externas", path: "/admin/integracoes/externas", alsoActive: ["/admin/integracoes/viajeon"] },
    { label: "Notificações", path: "/admin/integracoes/atendimento", whatsapp: true }
  ].filter(tab => !tab.whatsapp || hasWhatsAppPlanAccess.value)
);
</script>

<style scoped>
.ih { display: flex; flex-direction: column; gap: 16px; }
.ih-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.ih-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.ih-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; color: var(--foreground); }
.ih-sub { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.ih-actions { display: flex; flex-shrink: 0; gap: 8px; }
.ih-tabs { display: flex; gap: 4px; overflow-x: auto; border-bottom: 1px solid var(--border); }
.ih-tab { flex-shrink: 0; margin-bottom: -1px; border-bottom: 2px solid transparent; padding: 10px 14px; font-size: 13.5px; font-weight: 600; white-space: nowrap; color: var(--muted-foreground); }
.ih-tab:hover { color: var(--foreground); }
.ih-tab.on { border-bottom-color: var(--primary); color: var(--foreground); }
@media (max-width: 640px) {
  .ih-head { flex-direction: column; align-items: flex-start; }
}
</style>
