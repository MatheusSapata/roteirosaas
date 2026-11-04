<template>
  <section class="am-card am-card-flush">
    <div class="am-toolbar">
      <button
        v-for="option in filters"
        :key="option.value"
        type="button"
        class="am-chip"
        :class="{ on: filter === option.value }"
        @click="filter = option.value"
      >
        {{ option.label }} <span class="am-count am-num">{{ formatInt(count(option.value)) }}</span>
      </button>
      <label class="am-search ml-auto">
        <AmIcon name="search" />
        <input v-model="query" type="search" placeholder="Buscar no log" aria-label="Buscar no log" />
      </label>
      <button type="button" class="am-btn am-btn-sm" :disabled="loading" @click="load"><AmIcon name="refresh" />Atualizar</button>
    </div>

    <div v-if="loading && !items.length" class="am-empty"><div class="am-spinner"></div>Carregando logs...</div>
    <div v-else-if="loadError" class="am-notice am-tone-danger m-4"><AmIcon name="alert" /><span>{{ loadError }}</span></div>
    <div v-else-if="!filtered.length" class="am-empty">Nada registrado com esses filtros.</div>
    <ol v-else class="cl-list">
      <li v-for="item in visible" :key="item.id" class="cl-row">
        <span class="am-tile" :class="sourceMeta[item.source]?.tone || 'am-tone-neutral'"><AmIcon :name="sourceMeta[item.source]?.icon || 'info'" /></span>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <b class="text-[13.5px] font-semibold">{{ item.title }}</b>
            <span class="am-badge am-tone-neutral">{{ sourceMeta[item.source]?.label || item.source }}</span>
            <span v-if="item.status === 'error'" class="am-badge am-tone-danger">Erro</span>
            <span v-if="item.status === 'revoked'" class="am-badge am-tone-neutral">Sessão encerrada</span>
          </div>
          <small v-if="item.detail" class="am-muted block select-text">{{ item.detail }}</small>
          <small v-if="item.error" class="cl-error block">{{ item.error }}</small>
          <button v-if="item.data" type="button" class="cl-toggle" @click="toggle(item.id)">
            {{ open.has(item.id) ? "Esconder dados" : "Ver dados" }}
          </button>
          <pre v-if="item.data && open.has(item.id)" class="cl-data">{{ JSON.stringify(item.data, null, 2) }}</pre>
        </div>
        <small class="am-muted whitespace-nowrap text-right">
          {{ formatDateTime(item.at) }}
          <span class="block">{{ relativeDay(item.at) }}</span>
        </small>
      </li>
    </ol>
    <div v-if="filtered.length > limit" class="am-foot justify-center">
      <button type="button" class="am-chip" @click="limit += 100">Mostrar mais ({{ formatInt(filtered.length - limit) }} restantes)</button>
    </div>
    <div class="am-foot">
      <span>Ações do Admin Master, avisos do Asaas e da Cakto, compras no checkout e entradas no painel. As ações do Admin Master passaram a ser registradas agora.</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getCompanyLogs, type CompanyLog, type CompanyLogSource } from "../../../services/companies";
import AmIcon from "../master/AmIcon.vue";
import { formatDateTime, formatInt, relativeDay } from "../master/format";

const props = defineProps<{ companyId: number; reloadKey?: number }>();

const sourceMeta: Record<CompanyLogSource, { label: string; icon: string; tone: string }> = {
  admin: { label: "Admin Master", icon: "shield", tone: "am-tone-violet" },
  asaas: { label: "Asaas", icon: "card", tone: "am-tone-info" },
  cakto: { label: "Cakto", icon: "wallet", tone: "am-tone-warning" },
  checkout: { label: "Checkout", icon: "tag", tone: "am-tone-success" },
  login: { label: "Acesso", icon: "user", tone: "am-tone-neutral" }
};

const items = ref<CompanyLog[]>([]);
const loading = ref(false);
const loadError = ref("");

const load = async () => {
  loading.value = true;
  loadError.value = "";
  try {
    items.value = (await getCompanyLogs(props.companyId)).items;
  } catch (error: any) {
    loadError.value = error?.response?.data?.detail || "Não foi possível carregar os logs.";
  } finally {
    loading.value = false;
  }
};
onMounted(load);
watch(() => [props.companyId, props.reloadKey], load);

type Filter = "all" | CompanyLogSource | "errors";
const filter = ref<Filter>("all");
const query = ref("");
const limit = ref(100);
const filters: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "Tudo" },
  { value: "admin", label: "Admin Master" },
  { value: "asaas", label: "Asaas" },
  { value: "cakto", label: "Cakto" },
  { value: "checkout", label: "Checkout" },
  { value: "login", label: "Acessos" },
  { value: "errors", label: "Erros" }
];
const matches = (item: CompanyLog, value: Filter) => {
  if (value === "all") return true;
  if (value === "errors") return item.status === "error";
  return item.source === value;
};
const count = (value: Filter) => items.value.filter(item => matches(item, value)).length;
const filtered = computed(() => {
  const term = query.value.trim().toLowerCase();
  return items.value.filter(
    item => matches(item, filter.value) && (!term || `${item.title} ${item.detail} ${item.event || ""}`.toLowerCase().includes(term))
  );
});
const visible = computed(() => filtered.value.slice(0, limit.value));
watch([filter, query], () => {
  limit.value = 100;
});

const open = ref(new Set<string>());
const toggle = (id: string) => {
  const next = new Set(open.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  open.value = next;
};
</script>

<style scoped>
.cl-list > li + li {
  border-top: 1px solid var(--border);
}
.cl-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
}
.cl-error {
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--status-danger-foreground);
  overflow-wrap: anywhere;
}
.cl-toggle {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
}
.cl-data {
  margin-top: 6px;
  max-height: 320px;
  overflow: auto;
  border-radius: 10px;
  background: var(--muted);
  padding: 10px 12px;
  font-size: 11.5px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
