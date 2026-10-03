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
.amn {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--sidebar-border);
  background: color-mix(in srgb, var(--sidebar) 70%, var(--background));
  color: var(--sidebar-foreground);
}
.amn-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 12px 6px;
  padding: 20px 8px 14px;
  border-bottom: 1px solid var(--sidebar-border);
}
.amn-head b {
  display: block;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--foreground);
}
.amn-head small {
  display: block;
  font-size: 11.5px;
  color: var(--muted-foreground);
}
.amn-tile {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--status-warning);
  color: var(--status-warning-foreground);
}
.amn-tile svg {
  width: 16px;
  height: 16px;
}
.amn-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 12px 16px;
  scrollbar-width: thin;
}
.amn-group-label {
  padding: 12px 10px 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--muted-foreground) 80%, transparent);
}
.amn-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 10px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--muted-foreground);
  transition: background-color 0.15s ease, color 0.15s ease;
}
.amn-item svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}
.amn-item:hover {
  background: var(--sidebar-accent);
  color: var(--foreground);
}
.amn-item.on {
  background: var(--accent);
  color: var(--accent-foreground);
  font-weight: 600;
  box-shadow: inset 2px 0 0 var(--primary);
}
.amn-item:focus-visible {
  outline: 2px solid var(--ring);
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
.amn-warn {
  border-radius: 999px;
  background: var(--status-warning);
  padding: 0 7px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--status-warning-foreground);
}

/* Telas menores: o menu vira uma faixa rolável no topo do conteúdo. */
@media (max-width: 1179px) {
  .amn {
    border-right: 0;
    border-bottom: 1px solid var(--border);
    background: transparent;
  }
  .amn-head {
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
    border-radius: 999px;
    white-space: nowrap;
  }
  .amn-item.on {
    border-color: transparent;
    box-shadow: none;
  }
}
</style>
