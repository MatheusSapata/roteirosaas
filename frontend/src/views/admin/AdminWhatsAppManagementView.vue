<template>
  <section class="admin-master-surface am-page w-full">
    <AdminMasterHeader title="WhatsApp" subtitle="Conexões das agências e quem tem a caixa de entrada liberada.">
      <button type="button" class="am-btn" :disabled="refreshing" @click="refreshAll">
        <AmIcon name="refresh" :class="refreshing ? 'animate-spin' : ''" />Atualizar
      </button>
    </AdminMasterHeader>

    <section class="am-grid-4">
      <AdminMasterKpi icon="wa" tone="success" label="Conectadas" :value="formatInt(overview?.connected_connections)" :hint="`de ${formatInt(overview?.total_connections)} conexões · ${formatInt(overview?.agencies_with_whatsapp)} agências`" />
      <AdminMasterKpi icon="alert" tone="danger" label="Desconectadas" :value="formatInt(overview?.disconnected_connections)" hint="Precisam ler o QR code de novo" />
      <AdminMasterKpi icon="history" tone="warning" label="Conectando" :value="formatInt(overview?.connecting_connections)" hint="Esperando o QR code" />
      <AdminMasterKpi icon="users" tone="info" label="Caixa de entrada liberada" :value="formatInt((overview?.inbox_enabled_users ?? 0) + (overview?.inbox_enabled_agencies ?? 0))" :hint="`${formatInt(overview?.inbox_enabled_users)} pessoas · ${formatInt(overview?.inbox_enabled_agencies)} agências`" />
    </section>

    <section class="am-card am-card-flush">
      <nav class="am-tabs px-2.5" aria-label="Seções do WhatsApp">
        <button type="button" class="am-tab" :class="{ on: tab === 'connections' }" @click="tab = 'connections'">
          Conexões <span class="am-count">{{ connections.length }}</span>
        </button>
        <button type="button" class="am-tab" :class="{ on: tab === 'permissions' }" @click="tab = 'permissions'">
          Caixa de entrada liberada <span class="am-count">{{ permissions.length }}</span>
        </button>
      </nav>

      <template v-if="tab === 'connections'">
        <div class="am-toolbar">
          <label class="am-search">
            <AmIcon name="search" />
            <input v-model="connectionsQuery" type="search" placeholder="Buscar por agência, pessoa, número ou conexão" aria-label="Buscar conexão" />
          </label>
          <button
            v-for="option in connectionFilters"
            :key="option.id"
            type="button"
            class="am-chip"
            :class="{ on: connectionFilter === option.id }"
            @click="connectionFilter = option.id"
          >
            {{ option.label }} <span class="am-count">{{ connectionCounts[option.id] }}</span>
          </button>
        </div>
        <div class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Agência</th>
                <th>Pessoa</th>
                <th>Número</th>
                <th>Situação</th>
                <th>Conexão</th>
                <th>Criada em</th>
                <th>Conectada em</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in visibleConnections" :key="row.id">
                <td><b class="font-semibold">{{ row.agency_name || "—" }}</b></td>
                <td>
                  {{ row.owner_name || "—" }}
                  <small v-if="row.owner_email" class="am-muted block text-xs">{{ row.owner_email }}</small>
                </td>
                <td class="am-num">{{ row.phone_number ? formatPhone(row.phone_number) : "—" }}</td>
                <td><span class="am-badge am-dot" :class="statusTone(row.status)">{{ statusLabel(row.status) }}</span></td>
                <td>
                  {{ row.name }}
                  <small class="am-mono am-muted block">{{ row.instance_name }}</small>
                </td>
                <td class="am-num">{{ formatDate(row.created_at) }}</td>
                <td class="am-num">{{ formatDate(row.connected_at) }}</td>
              </tr>
              <tr v-if="!visibleConnections.length">
                <td colspan="7"><div class="am-empty">Nenhuma conexão encontrada.</div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <template v-else>
        <div class="am-toolbar">
          <label class="am-search">
            <AmIcon name="search" />
            <input
              v-model="permissionsQuery"
              type="search"
              placeholder="Buscar por nome, e-mail ou agência"
              aria-label="Buscar pessoa"
              @keydown.enter="searchUsers"
            />
          </label>
          <button type="button" class="am-btn am-btn-sm am-btn-primary" @click="searchUsers"><AmIcon name="search" />Buscar para liberar</button>
        </div>

        <div v-if="usersFound.length" class="border-b border-border bg-accent/40 px-3.5 py-3">
          <p class="am-eyebrow mb-2">Encontrados · clique em Liberar para dar acesso</p>
          <div class="am-table-wrap rounded-xl border border-border bg-card">
            <table class="am-table">
              <thead>
                <tr>
                  <th>Pessoa</th>
                  <th>Telefone</th>
                  <th>CPF/CNPJ</th>
                  <th>Agência</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in usersFound" :key="u.user_id">
                  <td>
                    <b class="font-semibold">{{ u.name }}</b>
                    <small class="am-muted block text-xs">{{ u.email || "—" }}</small>
                  </td>
                  <td class="am-num">{{ u.whatsapp ? formatPhone(u.whatsapp) : "—" }}</td>
                  <td class="am-num">{{ u.cpf || u.cnpj || "—" }}</td>
                  <td>{{ u.agency_name || "Sem agência" }}</td>
                  <td class="am-right"><button type="button" class="am-btn am-btn-sm am-btn-primary" @click="grant(u.user_id)">Liberar</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Pessoa</th>
                <th>Agência</th>
                <th>Acesso</th>
                <th>Liberado em</th>
                <th>Por</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in permissions" :key="row.id">
                <td>
                  <b class="font-semibold">{{ row.user_name || "—" }}</b>
                  <small class="am-muted block text-xs">{{ row.user_email || "—" }}</small>
                </td>
                <td>{{ row.agency_name || "—" }}</td>
                <td>
                  <span class="am-badge am-dot" :class="row.enabled ? 'am-tone-success' : 'am-tone-neutral'">{{ row.enabled ? "Liberado" : "Revogado" }}</span>
                </td>
                <td class="am-num">{{ formatDate(row.granted_at) }}</td>
                <td>{{ row.granted_by_name || "—" }}</td>
                <td class="am-right">
                  <button type="button" class="am-btn am-btn-sm" :class="row.enabled ? 'am-btn-danger' : ''" @click="togglePermission(row)">
                    {{ row.enabled ? "Revogar acesso" : "Liberar de novo" }}
                  </button>
                </td>
              </tr>
              <tr v-if="!permissions.length">
                <td colspan="6"><div class="am-empty">Ninguém com a caixa de entrada liberada.</div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
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
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";
import { formatPhoneBR } from "../../utils/format";
import type { AdminMasterWhatsAppConnection, AdminMasterWhatsAppInboxPermission, AdminMasterWhatsAppOverview } from "../../types/whatsapp";

const overview = ref<AdminMasterWhatsAppOverview | null>(null);
const tab = ref<"connections" | "permissions">("connections");
const connections = ref<AdminMasterWhatsAppConnection[]>([]);
const permissions = ref<AdminMasterWhatsAppInboxPermission[]>([]);
const connectionsQuery = ref("");
const permissionsQuery = ref("");
const usersFound = ref<Array<{ user_id: number; name: string; email: string; whatsapp?: string; cpf?: string; cnpj?: string; agency_name?: string }>>([]);

type ConnectionFilter = "all" | "connected" | "problem";
const connectionFilter = ref<ConnectionFilter>("all");
const connectionFilters: Array<{ id: ConnectionFilter; label: string }> = [
  { id: "all", label: "Todas" },
  { id: "connected", label: "Conectadas" },
  { id: "problem", label: "Com problema" }
];
const normalizedStatus = (status?: string | null) => String(status || "disconnected").toLowerCase();
const isConnected = (status?: string | null) => normalizedStatus(status) === "connected";
const connectionCounts = computed(() => ({
  all: connections.value.length,
  connected: connections.value.filter(row => isConnected(row.status)).length,
  problem: connections.value.filter(row => !isConnected(row.status)).length
}));
const visibleConnections = computed(() => {
  if (connectionFilter.value === "connected") return connections.value.filter(row => isConnected(row.status));
  if (connectionFilter.value === "problem") return connections.value.filter(row => !isConnected(row.status));
  return connections.value;
});

const formatInt = (value?: number | null) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const formatPhone = (value: string) => formatPhoneBR(value) || value;
const formatDate = (value?: string | null) =>
  value ? new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—";
const statusLabel = (status?: string | null) => {
  const normalized = normalizedStatus(status);
  if (normalized === "connected") return "Conectado";
  if (normalized === "disconnected") return "Desconectado";
  if (["qrcode", "pairing"].includes(normalized)) return "Lendo QR code";
  if (["connecting", "open"].includes(normalized)) return "Conectando";
  return status || "—";
};
const statusTone = (status?: string | null) => {
  const normalized = normalizedStatus(status);
  if (normalized === "connected") return "am-tone-success";
  if (normalized === "disconnected") return "am-tone-danger";
  return "am-tone-warning";
};
const refreshing = ref(false);
const refreshAll = async () => {
  refreshing.value = true;
  try {
    await Promise.all([loadOverview(), loadConnections(), loadPermissions()]);
  } finally {
    refreshing.value = false;
  }
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

