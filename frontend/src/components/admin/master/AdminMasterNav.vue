<template>
  <aside class="amn" aria-label="Menu do admin master">
    <div class="amn-head">
      <span class="amn-tile"><AmIcon name="crown" /></span>
      <div>
        <b>Admin master</b>
        <small>Toda a plataforma</small>
      </div>
    </div>
    <nav ref="scrollEl" class="amn-scroll">
      <section v-for="group in adminMasterNav" :key="group.label" class="amn-group">
        <p class="amn-group-label">{{ group.label }}</p>
        <RouterLink
          v-for="item in group.items"
          :key="item.path"
          :to="item.path"
          class="amn-item"
          :class="{ on: isActive(item.path) }"
        >
          <AmIcon :name="item.icon" />
          <span class="amn-label">{{ item.label }}</span>
          <span v-if="item.badge === 'online' && adminMasterCounts.online" class="amn-live">{{ adminMasterCounts.online }}</span>
          <span v-else-if="item.badge === 'whatsapp' && adminMasterCounts.whatsappIssues" class="amn-warn">{{ adminMasterCounts.whatsappIssues }}</span>
        </RouterLink>
      </section>
    </nav>
    <RouterLink to="/admin/dashboard" class="amn-back">
      <AmIcon name="chevron-left" />
      <span>Voltar ao painel</span>
    </RouterLink>
  </aside>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AmIcon from "./AmIcon.vue";
import { adminMasterNav } from "./nav";
import { adminMasterCounts, loadAdminMasterCounts } from "../../../composables/useAdminMasterCounts";

const route = useRoute();
const isActive = (path: string) => route.path === path || route.path.startsWith(`${path}/`);

// No celular o menu vira uma faixa: deixa o item da tela atual visível.
const scrollEl = ref<HTMLElement | null>(null);
const revealActive = async () => {
  await nextTick();
  if (typeof window === "undefined" || window.innerWidth >= 1180) return;
  scrollEl.value?.querySelector<HTMLElement>(".amn-item.on")?.scrollIntoView({ inline: "center", block: "nearest" });
};
watch(() => route.path, revealActive);

let timer: ReturnType<typeof setInterval> | null = null;
onMounted(() => {
  void revealActive();
  void loadAdminMasterCounts(true);
  timer = setInterval(() => void loadAdminMasterCounts(), 60_000);
});
onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
/* Cartão âmbar ao lado do menu principal recolhido (mesmo desenho do Viaje On). */
.amn {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 20px;
  background: var(--admin-surface);
  color: var(--admin-ink);
  box-shadow: var(--shadow-card);
}
.amn-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 12px 4px;
  padding: 16px 4px 12px;
  border-bottom: 1px solid var(--admin-border);
}
.amn-head b {
  display: block;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--admin-ink);
}
.amn-head small {
  display: block;
  font-size: 12px;
  color: var(--admin-muted);
}
.amn-tile {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  color: #ffffff;
  box-shadow: 0 8px 18px -10px rgba(234, 88, 12, 0.8);
}
.amn-tile svg {
  width: 16px;
  height: 16px;
}
.amn-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 12px 12px;
  scrollbar-width: thin;
}
.amn-group-label {
  display: flex;
  align-items: center;
  height: 30px;
  padding: 0 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--admin-muted);
}
.amn-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 400;
  color: var(--admin-ink);
  transition: background-color 200ms ease-out, color 200ms ease-out;
}
.amn-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--admin-accent);
}
.amn-item:hover {
  background: var(--admin-soft);
}
.amn-item.on {
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 8px 18px -10px rgba(234, 88, 12, 0.8);
}
.amn-item.on svg {
  color: #ffffff;
}
.amn-item:focus-visible,
.amn-back:focus-visible {
  outline: 2px solid var(--admin-accent);
  outline-offset: 1px;
}
.amn-label {
  flex: 1;
  min-width: 0;
}
.amn-live {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--status-success-foreground);
}
.amn-live::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 0 3px var(--status-success);
}
.amn-item.on .amn-live {
  color: #ffffff;
}
.amn-warn {
  border-radius: 999px;
  background: var(--status-warning);
  padding: 0 7px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--status-warning-foreground);
}
.amn-back {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 12px 12px;
  padding: 12px 12px 0;
  border-top: 1px solid var(--admin-border);
  font-size: 14px;
  color: var(--admin-muted);
  transition: color 200ms ease-out;
}
.amn-back:hover {
  color: var(--admin-ink);
}
.amn-back svg {
  width: 16px;
  height: 16px;
}

/* Telas menores: o menu vira uma faixa rolável no topo do conteúdo. */
@media (max-width: 1179px) {
  .amn {
    overflow: visible;
    border-radius: 0;
    border-bottom: 1px solid var(--border);
    background: transparent;
    box-shadow: none;
  }
  .amn-head,
  .amn-back {
    display: none;
  }
  .amn-scroll {
    display: flex;
    gap: 4px;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0 0 10px;
  }
  .amn-group {
    display: contents;
  }
  .amn-group-label {
    display: none;
  }
  .amn-item {
    flex-shrink: 0;
    border: 1px solid var(--border);
    background: var(--card);
    white-space: nowrap;
  }
  .amn-item.on {
    border-color: transparent;
  }
}
</style>
