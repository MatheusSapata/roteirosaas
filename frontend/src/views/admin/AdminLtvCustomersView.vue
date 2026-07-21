<template>
  <div class="admin-master-surface space-y-4">
    <section class="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">LTV por cliente</p>
          <h2 class="text-2xl font-bold text-slate-900">Clientes Cakto</h2>
          <p class="text-sm text-slate-500">Baseado em eventos de pagamento/renovação/cancelamento da tabela <code>cakto_event_logs</code>.</p>
        </div>
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          :disabled="loading"
          @click="loadLtv"
        >
          {{ loading ? "Atualizando..." : "Atualizar" }}
        </button>
      </div>

      <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-4">
        <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Clientes</p>
          <p class="mt-1 text-2xl font-bold text-slate-900">{{ ltv?.total_customers || 0 }}</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Ativos</p>
          <p class="mt-1 text-2xl font-bold text-emerald-700">{{ ltv?.active_customers || 0 }}</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Cancelados</p>
          <p class="mt-1 text-2xl font-bold text-rose-700">{{ ltv?.cancelled_customers || 0 }}</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Receita acumulada</p>
          <p class="mt-1 text-2xl font-bold text-slate-900">{{ formatCurrency(ltv?.total_revenue || 0) }}</p>
        </div>
      </div>

      <p v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{{ error }}</p>

      <div class="mt-4 overflow-x-auto rounded-2xl border border-slate-100">
        <table class="min-w-[1100px] w-full text-sm">
          <thead class="bg-slate-50 text-slate-600">
            <tr>
              <th class="px-3 py-2 text-left">Cliente</th>
              <th class="px-3 py-2 text-left">Entrou em</th>
              <th class="px-3 py-2 text-left">Status</th>
              <th class="px-3 py-2 text-right">Renovações</th>
              <th class="px-3 py-2 text-right">Total deixado</th>
              <th class="px-3 py-2 text-left">Cancelou em</th>
              <th class="px-3 py-2 text-left">Próxima renovação</th>
              <th class="px-3 py-2 text-left">Último evento</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="8" class="px-3 py-6 text-center text-slate-500">Carregando...</td>
            </tr>
            <tr v-else-if="!rows.length">
              <td colspan="8" class="px-3 py-6 text-center text-slate-500">Sem dados de LTV.</td>
            </tr>
            <tr v-for="row in rows" :key="row.email" class="border-t border-slate-100">
              <td class="px-3 py-2">
                <p class="font-semibold text-slate-900">{{ row.name || "Sem nome" }}</p>
                <p class="text-xs text-slate-500">{{ row.email }}</p>
              </td>
              <td class="px-3 py-2 text-slate-700">{{ formatDate(row.entered_at) }}</td>
              <td class="px-3 py-2">
                <span
                  class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                  :class="row.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
                >
                  {{ row.is_active ? "Ativo" : "Inativo" }}
                </span>
              </td>
              <td class="px-3 py-2 text-right font-semibold text-slate-900">{{ row.renewals_count }}</td>
              <td class="px-3 py-2 text-right font-semibold text-slate-900">{{ formatCurrency(row.total_revenue) }}</td>
              <td class="px-3 py-2 text-slate-700">{{ formatDate(row.cancelled_at) }}</td>
              <td class="px-3 py-2 text-slate-700">{{ formatDate(row.next_renewal_at) }}</td>
              <td class="px-3 py-2 text-slate-700">
                <p>{{ row.last_event_type || "--" }}</p>
                <p class="text-xs text-slate-500">{{ formatDateTime(row.last_event_at) }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import api from "../../services/api";

interface LtvRow {
  email: string;
  name?: string | null;
  entered_at?: string | null;
  is_active: boolean;
  renewals_count: number;
  total_revenue: number;
  cancelled_at?: string | null;
  next_renewal_at?: string | null;
  last_event_type?: string | null;
  last_event_at?: string | null;
}

interface LtvResponse {
  total_customers: number;
  active_customers: number;
  cancelled_customers: number;
  total_revenue: number;
  customers: LtvRow[];
}

const ltv = ref<LtvResponse | null>(null);
const rows = ref<LtvRow[]>([]);
const loading = ref(false);
const error = ref("");

const formatDate = (value?: string | null) => {
  if (!value) return "--";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "--";
  return d.toLocaleDateString("pt-BR");
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "--";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "--";
  return d.toLocaleString("pt-BR");
};

const formatCurrency = (value: number) =>
  Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const loadLtv = async () => {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await api.get<LtvResponse>("/admin/ltv-customers");
    ltv.value = data;
    rows.value = data.customers || [];
  } catch (err: any) {
    ltv.value = null;
    rows.value = [];
    error.value = err?.response?.data?.detail || "Não foi possível carregar o dashboard de LTV.";
  } finally {
    loading.value = false;
  }
};

onMounted(loadLtv);
</script>
