<template>
  <section class="space-y-5 px-4 py-4 md:px-6">
    <header class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h1 class="text-2xl font-semibold text-slate-900">Gestão WhatsApp</h1>
      <p class="mt-1 text-sm text-slate-600">Controle conexões, status e liberação da Inbox para usuários.</p>
    </header>

    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <article v-for="card in summaryCards" :key="card.label" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ card.label }}</p>
        <p class="mt-2 text-2xl font-bold text-slate-900">{{ card.value }}</p>
      </article>
    </div>

    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <button class="tab-btn" :class="{ active: tab === 'connections' }" @click="tab = 'connections'">Conexões</button>
        <button class="tab-btn" :class="{ active: tab === 'permissions' }" @click="tab = 'permissions'">Usuários permitidos</button>
      </div>

      <div class="p-4">
        <div v-if="tab === 'connections'" class="space-y-3">
          <input v-model="connectionsQuery" class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Buscar por agência, usuário, número, conexão..." />
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead><tr class="text-left text-slate-500"><th>Agência</th><th>Usuário</th><th>Número</th><th>Status</th><th>Conexão</th><th>Criada em</th><th>Conectada em</th></tr></thead>
              <tbody>
                <tr v-for="row in connections" :key="row.id" class="border-t border-slate-100">
                  <td class="py-2">{{ row.agency_name || '-' }}</td><td>{{ row.owner_name || '-' }}</td><td>{{ row.phone_number || '-' }}</td>
                  <td><span class="rounded-full px-2 py-1 text-xs" :class="statusClass(row.status)">{{ row.status }}</span></td>
                  <td>{{ row.name }} <span class="text-xs text-slate-400">({{ row.instance_name }})</span></td>
                  <td>{{ formatDate(row.created_at) }}</td><td>{{ formatDate(row.connected_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else class="space-y-3">
          <div class="flex gap-2">
            <input v-model="permissionsQuery" class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Buscar nome, email, agência..." />
            <button class="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-white" @click="searchUsers">Buscar</button>
          </div>
          <div v-if="usersFound.length" class="overflow-x-auto rounded-xl border border-emerald-100 bg-emerald-50/40">
            <table class="min-w-full text-sm">
              <thead><tr class="text-left text-slate-600"><th class="px-3 py-2">Usuário</th><th>Email</th><th>Telefone</th><th>CPF/CNPJ</th><th>Agência</th><th></th></tr></thead>
              <tbody>
                <tr v-for="u in usersFound" :key="u.user_id" class="border-t border-emerald-100">
                  <td class="px-3 py-2 font-medium text-slate-800">{{ u.name }}</td>
                  <td>{{ u.email || '-' }}</td>
                  <td>{{ u.whatsapp || '-' }}</td>
                  <td>{{ u.cpf || u.cnpj || '-' }}</td>
                  <td>{{ u.agency_name || 'Sem agência' }}</td>
                  <td class="pr-3 text-right">
                    <button class="rounded-lg bg-emerald-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-emerald-700" @click="grant(u.user_id)">Liberar</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead><tr class="text-left text-slate-500"><th>Usuário</th><th>Email</th><th>Agência</th><th>Permissão</th><th>Liberado em</th><th>Por</th><th></th></tr></thead>
              <tbody>
                <tr v-for="row in permissions" :key="row.id" class="border-t border-slate-100">
                  <td class="py-2">{{ row.user_name || '-' }}</td><td>{{ row.user_email || '-' }}</td><td>{{ row.agency_name || '-' }}</td>
                  <td><span class="rounded-full px-2 py-1 text-xs" :class="row.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'">{{ row.enabled ? 'Ativa' : 'Inativa' }}</span></td>
                  <td>{{ formatDate(row.granted_at) }}</td><td>{{ row.granted_by_name || '-' }}</td>
                  <td>
                    <button
                      class="text-xs font-semibold"
                      :class="row.enabled ? 'text-rose-600' : 'text-emerald-700'"
                      @click="togglePermission(row)"
                    >
                      {{ row.enabled ? 'Revogar acesso' : 'Liberar acesso' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  getAdminMasterWhatsAppOverview,
  listAdminMasterInboxPermissions,
  listAdminMasterWhatsAppConnections,
  revokeAdminMasterInboxPermission,
  upsertAdminMasterInboxPermission
} from "../../services/whatsapp";
import api from "../../services/api";
import type { AdminMasterWhatsAppConnection, AdminMasterWhatsAppInboxPermission, AdminMasterWhatsAppOverview } from "../../types/whatsapp";

const overview = ref<AdminMasterWhatsAppOverview | null>(null);
const tab = ref<"connections" | "permissions">("connections");
const connections = ref<AdminMasterWhatsAppConnection[]>([]);
const permissions = ref<AdminMasterWhatsAppInboxPermission[]>([]);
const connectionsQuery = ref("");
const permissionsQuery = ref("");
const usersFound = ref<Array<{ user_id: number; name: string; email: string; whatsapp?: string; cpf?: string; cnpj?: string; agency_name?: string }>>([]);

const summaryCards = computed(() => {
  const data = overview.value;
  return [
    { label: "Conexões totais", value: data?.total_connections ?? 0 },
    { label: "Conectadas", value: data?.connected_connections ?? 0 },
    { label: "Desconectadas", value: data?.disconnected_connections ?? 0 },
    { label: "Em conexão", value: data?.connecting_connections ?? 0 },
    { label: "Agências com WhatsApp", value: data?.agencies_with_whatsapp ?? 0 },
    { label: "Inbox liberada", value: (data?.inbox_enabled_users ?? 0) + (data?.inbox_enabled_agencies ?? 0) }
  ];
});

const formatDate = (value?: string | null) => (value ? new Date(value).toLocaleString("pt-BR") : "-");
const statusClass = (status: string) => {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "connected") return "bg-emerald-100 text-emerald-700";
  if (normalized === "disconnected") return "bg-rose-100 text-rose-700";
  return "bg-amber-100 text-amber-700";
};

const loadOverview = async () => {
  overview.value = await getAdminMasterWhatsAppOverview();
};
const loadConnections = async () => {
  connections.value = await listAdminMasterWhatsAppConnections(connectionsQuery.value.trim());
};
const loadPermissions = async () => {
  permissions.value = await listAdminMasterInboxPermissions(permissionsQuery.value.trim());
};
const revoke = async (permissionId: number) => {
  await revokeAdminMasterInboxPermission(permissionId);
  await Promise.all([loadPermissions(), loadOverview()]);
};
const enablePermission = async (permissionId: number) => {
  const row = permissions.value.find(item => item.id === permissionId);
  if (!row) return;
  await upsertAdminMasterInboxPermission({
    userId: row.user_id || undefined,
    agencyId: row.agency_id || undefined,
    enabled: true
  });
  await Promise.all([loadPermissions(), loadOverview()]);
};
const togglePermission = async (row: AdminMasterWhatsAppInboxPermission) => {
  if (row.enabled) {
    await revoke(row.id);
    return;
  }
  await enablePermission(row.id);
};
const grant = async (userId: number) => {
  await upsertAdminMasterInboxPermission({ userId, enabled: true });
  await Promise.all([loadPermissions(), loadOverview()]);
};
const searchUsers = async () => {
  const query = permissionsQuery.value.trim();
  if (query.length < 2) {
    usersFound.value = [];
    return;
  }
  const { data } = await api.get("/admin-master/whatsapp/users-search", { params: { q: query } });
  usersFound.value = Array.isArray(data) ? data : [];
};

watch(connectionsQuery, loadConnections);
watch(permissionsQuery, async value => {
  await loadPermissions();
  if (!value.trim()) usersFound.value = [];
});

onMounted(async () => {
  await Promise.all([loadOverview(), loadConnections(), loadPermissions()]);
});
</script>

<style scoped>
.tab-btn { border-radius: 10px; padding: 6px 10px; font-size: 13px; font-weight: 600; color: #475569; }
.tab-btn.active { background: #e2f7e8; color: #047857; }
</style>
