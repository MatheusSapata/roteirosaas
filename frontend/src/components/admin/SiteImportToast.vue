<template>
  <div v-if="visible" class="sit-wrap">
    <div v-if="expanded" class="sit-panel">
      <div class="sit-panel-head">
        <span class="sit-panel-title">Importando o site{{ job!.source_title ? `: ${job!.source_title}` : "" }}</span>
        <button type="button" class="sit-icon-btn" aria-label="Recolher" @click="expanded = false">—</button>
      </div>
      <p v-if="job!.status === 'running'" class="sit-hint">
        Isso leva alguns minutos. Evite salvar a página onde a importação começou até terminar.
      </p>
      <ul class="sit-items">
        <li v-for="item in job!.items" :key="item.url" class="sit-item">
          <span class="sit-item-icon" :class="iconClass(item.stage)" aria-hidden="true">{{ iconFor(item.stage) }}</span>
          <RouterLink v-if="item.page_id" :to="`/admin/pages/${item.page_id}/edit`" class="sit-item-title">
            {{ item.title }}
          </RouterLink>
          <span v-else class="sit-item-title is-muted">{{ item.title }}</span>
          <span class="sit-item-stage">{{ stageLabel(item.stage) }}</span>
        </li>
      </ul>
      <div class="sit-home">
        <span class="sit-item-icon" :class="iconClass(job!.home.stage)" aria-hidden="true">{{ iconFor(job!.home.stage) }}</span>
        <RouterLink v-if="job!.home.page_id" :to="`/admin/pages/${job!.home.page_id}/edit`" class="sit-item-title">
          Página principal{{ job!.home.title ? `: ${job!.home.title}` : "" }}
        </RouterLink>
        <span v-else class="sit-item-title is-muted">Página principal</span>
        <span class="sit-item-stage">{{ stageLabel(job!.home.stage) }}</span>
      </div>
      <p v-if="job!.error" class="sit-error">{{ job!.error }}</p>
      <div v-if="job!.status !== 'running'" class="sit-panel-footer">
        <button type="button" class="sit-close-btn" @click="close">Fechar</button>
      </div>
    </div>
    <button type="button" class="sit-chip" :class="chipClass" @click="expanded = !expanded">
      <span v-if="job!.status === 'running'" class="sit-spinner" aria-hidden="true"></span>
      <span v-else aria-hidden="true">{{ job!.status === "completed" ? "✓" : "⚠" }}</span>
      <span>{{ chipText }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
/** Andamento da importação do site inteiro pelo assistente de IA, visível em qualquer página do
 * admin (a pessoa pode seguir trabalhando enquanto o site inteiro é montado em segundo plano). */
import { computed, ref, watch } from "vue";
import { dismissSiteImportJob, siteImportState } from "../../services/siteImportStatus";
import type { SiteImportStage } from "../../services/siteImportJobs";

const expanded = ref(false);

const job = computed(() => siteImportState.job);

const visible = computed(() => !!job.value && job.value.id !== siteImportState.dismissedJobId);

// Importação nova (id diferente da última fechada): abre sozinho na primeira vez que aparece.
watch(
  () => job.value?.id,
  (id, previous) => {
    if (id && id !== previous && id !== siteImportState.dismissedJobId) expanded.value = true;
  }
);

const close = () => {
  if (job.value) dismissSiteImportJob(job.value.id);
  expanded.value = false;
};

const chipClass = computed(() => (job.value?.status === "completed" ? "is-done" : job.value?.status === "failed" ? "is-error" : ""));

const chipText = computed(() => {
  if (!job.value) return "";
  if (job.value.status === "running") {
    if (job.value.stage === "home") return "Importando o site: montando a página principal";
    return `Importando o site: ${job.value.done} de ${job.value.total} páginas`;
  }
  if (job.value.status === "completed") return `Site importado: ${job.value.done} de ${job.value.total} páginas`;
  return "A importação do site deu erro";
});

const stageLabel = (stage: SiteImportStage) =>
  ({
    waiting: "Na fila",
    scraping: "Lendo a página",
    generating: "Montando",
    done: "Pronta",
    error: "Erro"
  })[stage];

const iconFor = (stage: SiteImportStage) => ({ waiting: "·", scraping: "…", generating: "…", done: "✓", error: "⚠" })[stage];
const iconClass = (stage: SiteImportStage) => (stage === "done" ? "is-done" : stage === "error" ? "is-error" : "is-pending");
</script>

<style scoped>
.sit-wrap {
  position: fixed;
  left: 20px;
  bottom: 20px;
  z-index: 60;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}
.sit-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border: none;
  border-radius: 999px;
  background: var(--foreground, #111);
  color: var(--background, #fff);
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  cursor: pointer;
}
.sit-chip.is-done {
  background: var(--primary, #0f7a4f);
  color: var(--primary-foreground, #fff);
}
.sit-chip.is-error {
  background: var(--destructive, #b3261e);
  color: var(--destructive-foreground, #fff);
}
.sit-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 999px;
  animation: sit-spin 0.8s linear infinite;
  flex: 0 0 auto;
}
@keyframes sit-spin {
  to {
    transform: rotate(360deg);
  }
}
.sit-panel {
  width: min(360px, calc(100vw - 40px));
  max-height: min(60vh, 460px);
  overflow-y: auto;
  border-radius: 16px;
  background: var(--card, #fff);
  color: var(--foreground, #111);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  padding: 14px 16px;
}
.sit-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-weight: 700;
  font-size: 13px;
}
.sit-panel-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sit-icon-btn {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  color: var(--muted-foreground, #666);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 2px 6px;
}
.sit-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--muted-foreground, #666);
}
.sit-items,
.sit-home {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.sit-home {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border, #e5e5e5);
}
.sit-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}
.sit-item-icon {
  flex: 0 0 auto;
  width: 16px;
  text-align: center;
  font-weight: 700;
}
.sit-item-icon.is-done {
  color: var(--status-success, #1a7f37);
}
.sit-item-icon.is-error {
  color: var(--status-danger, #b3261e);
}
.sit-item-icon.is-pending {
  color: var(--muted-foreground, #999);
}
.sit-item-title {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: inherit;
  text-decoration: none;
}
.sit-item-title:not(.is-muted):hover {
  text-decoration: underline;
}
.sit-item-title.is-muted {
  color: var(--muted-foreground, #999);
}
.sit-item-stage {
  flex: 0 0 auto;
  font-size: 11px;
  color: var(--muted-foreground, #999);
}
.sit-error {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--status-danger, #b3261e);
}
.sit-panel-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.sit-close-btn {
  border: 1px solid var(--border, #e5e5e5);
  background: transparent;
  color: var(--foreground, #111);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}
</style>
