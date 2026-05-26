<template>
  <div class="clients-page space-y-5">
    <p class="clients-sub">Gerencie sua base de clientes e histórico de oportunidades.</p>
    <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <article class="kpi-card">
        <span class="kpi-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><path d="M20 8v6"/><path d="M23 11h-6"/></svg>
        </span>
        <p class="kpi-value">{{ clients.length }}</p>
        <p class="kpi-label">Total de clientes</p>
        <p class="kpi-sub">Base comercial ativa</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-icon kpi-icon--doc" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v3h3"/></svg>
        </span>
        <p class="kpi-value">{{ clientsWithOpportunities }}</p>
        <p class="kpi-label">Com oportunidades</p>
        <p class="kpi-sub">Clientes em negociação</p>
      </article>
      <article class="kpi-card" :class="{ 'kpi-card--revenue-positive': totalRevenueCents > 0 }">
        <span class="kpi-icon kpi-icon--money" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M12 2v20"/><path d="M17 6H9.5a3.5 3.5 0 0 0 0 7H14.5a3.5 3.5 0 0 1 0 7H6"/></svg>
        </span>
        <p class="kpi-value">{{ formatCurrency(totalRevenueCents) }}</p>
        <p class="kpi-label">Receita total</p>
        <p class="kpi-sub">Somatório estimado</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
        </span>
        <p class="kpi-value text-lg">{{ latestOpportunityDate }}</p>
        <p class="kpi-label">Última oportunidade</p>
        <p class="kpi-sub">Movimento mais recente</p>
      </article>
    </section>

    <section class="p-0">
      <div class="clients-filters-row grid gap-2 md:grid-cols-[2fr_0.9fr_0.6fr_0.6fr]">
        <div class="search-wrap">
          <span class="search-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg></span>
          <input v-model="filters.q" type="text" placeholder="Buscar cliente, CPF, telefone ou e-mail..." class="crm-input crm-input--search" />
        </div>
        <div class="city-wrap">
          <span class="city-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg></span>
          <input v-model="filters.city" type="text" placeholder="Cidade" class="crm-input crm-input--city" />
        </div>
        <select v-model="filters.period" class="crm-input">
          <option value="all">Período</option>
          <option value="7">Últimos 7 dias</option>
          <option value="30">Últimos 30 dias</option>
          <option value="90">Últimos 90 dias</option>
        </select>
        <select v-model="filters.status" class="crm-input">
          <option value="all">Status</option>
          <option value="with">Com oportunidades</option>
          <option value="without">Sem oportunidades</option>
        </select>
      </div>
    </section>

    <section class="overflow-visible rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div v-if="loading" class="flex min-h-[260px] items-center justify-center">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
      </div>

      <div v-else-if="!clients.length" class="empty-state">
        <div class="empty-icon" aria-hidden="true">🗂️</div>
        <h3 class="text-lg font-semibold text-slate-900">Nenhum cliente encontrado</h3>
        <p class="text-sm text-slate-500">Crie um cliente ou ajuste os filtros</p>
        <button type="button" class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white" @click="openCreateModal">+ Novo cliente</button>
      </div>

      <div v-else>
        <div class="hidden overflow-x-auto overflow-y-visible lg:block">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-4 py-3">Cliente</th>
                <th class="px-4 py-3">Contato</th>
                <th class="px-4 py-3">Cidade</th>
                <th class="px-4 py-3">Oportunidades</th>
                <th class="px-4 py-3">Total</th>
                <th class="px-4 py-3">Última oportunidade</th>
                <th class="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr v-for="client in clients" :key="client.id" class="client-row cursor-pointer text-slate-700 transition" @click="goToClient(client.id)">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <span class="avatar-chip" :style="avatarChipStyle(client)">{{ clientInitials(client.name) }}</span>
                    <div>
                      <p class="text-[0.98rem] font-semibold leading-tight text-slate-900">{{ client.name }}</p>
                      <p class="text-[0.76rem] text-slate-500">Cliente desde {{ formatDate(client.created_at) }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <p class="truncate">{{ client.email || '-' }}</p>
                  <p class="text-xs text-slate-500">{{ formatPhone(client.phone) || '-' }}</p>
                </td>
                <td class="px-4 py-3">{{ locationLabel(client) }}</td>
                <td class="px-4 py-3">
                  <span class="op-badge" :class="client.opportunitiesCount > 0 ? 'is-hot' : 'is-cold'">
                    {{ client.opportunitiesCount }} oportunidades
                  </span>
                </td>
                <td class="px-4 py-3 text-[1.05rem] font-semibold text-slate-900">{{ formatCurrency(client.totalEstimatedValueCents) }}</td>
                <td class="px-4 py-3">{{ formatDate(client.lastOpportunityAt) }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center justify-end" @click.stop>
                    <div class="inline-flex items-center gap-2">
                      <button type="button" class="menu-trigger" title="Ver cliente" @click.stop="goToClient(client.id)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
                          <path d="M2 12s3.6-6 10-6s10 6 10 6s-3.6 6-10 6s-10-6-10-6z" />
                          <circle cx="12" cy="12" r="2.8" />
                        </svg>
                      </button>
                      <button type="button" class="menu-trigger menu-trigger--danger" title="Excluir cliente" @click.stop="handleDeleteClient(client.id)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
                          <path d="M3 6h18" />
                          <path d="M8 6V4h8v2" />
                          <path d="M19 6l-1 14H6L5 6" />
                          <path d="M10 11v6M14 11v6" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="space-y-3 p-3 lg:hidden">
          <article v-for="client in clients" :key="`mobile-${client.id}`" class="client-card rounded-2xl border border-slate-200 bg-white p-4 shadow-sm" @click="goToClient(client.id)">
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-start gap-3">
                <span class="avatar-chip" :style="avatarChipStyle(client)">{{ clientInitials(client.name) }}</span>
                <div>
                  <p class="text-[0.95rem] font-semibold text-slate-900">{{ client.name }}</p>
                  <p class="text-[0.72rem] text-slate-500">Cliente desde {{ formatDate(client.created_at) }}</p>
                </div>
              </div>
              <span class="op-badge" :class="client.opportunitiesCount > 0 ? 'is-hot' : 'is-cold'">{{ client.opportunitiesCount }} oportunidades</span>
            </div>
            <div class="mt-2 text-sm text-slate-700">
              <p>{{ client.email || '-' }}</p>
              <p class="text-xs text-slate-500">{{ formatPhone(client.phone) || '-' }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ locationLabel(client) }}</p>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <p class="font-semibold text-slate-800">{{ formatCurrency(client.totalEstimatedValueCents) }}</p>
              <p class="text-xs text-slate-500">{{ formatDate(client.lastOpportunityAt) }}</p>
            </div>
            <div class="mt-3 flex gap-2" @click.stop>
              <button type="button" class="table-action table-action--primary" @click="goToClient(client.id)">Ver perfil</button>
              <button type="button" class="table-action table-action--danger" @click="handleDeleteClient(client.id)">Excluir</button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="createModalOpen" class="app-modal-overlay fixed inset-0 z-[150] flex items-center justify-center p-3 md:px-4">
        <div class="flex w-full max-w-2xl flex-col overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-2xl max-h-[calc(100vh-24px)] md:max-h-[calc(100vh-48px)]">
          <div class="flex shrink-0 items-start justify-between gap-4 border-b border-slate-100 px-4 py-4 md:px-6">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Clientes</p>
              <h2 class="mt-2 text-2xl font-bold text-slate-900">Novo cliente</h2>
            </div>
            <button type="button" class="rounded-full border border-slate-200 p-2 text-slate-500" @click="closeCreateModal">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto px-4 py-4 md:px-6">
            <div class="grid gap-3 md:grid-cols-2">
              <input v-model="createForm.name" type="text" placeholder="Nome" class="crm-input md:col-span-2" />
              <input v-model="createForm.cpf" type="text" placeholder="CPF" class="crm-input" />
              <input v-model="createForm.phone" type="text" placeholder="Telefone" class="crm-input" />
              <input v-model="createForm.email" type="email" placeholder="E-mail" class="crm-input" />
              <input v-model="createForm.city" type="text" placeholder="Cidade" class="crm-input" />
              <input v-model="createForm.state" type="text" maxlength="2" placeholder="UF" class="crm-input" />
              <input v-model="createForm.zipcode" type="text" placeholder="CEP" class="crm-input" />
              <input v-model="createForm.street" type="text" placeholder="Logradouro" class="crm-input md:col-span-2" />
              <input v-model="createForm.number" type="text" placeholder="Número" class="crm-input" />
              <input v-model="createForm.complement" type="text" placeholder="Complemento" class="crm-input" />
              <input v-model="createForm.neighborhood" type="text" placeholder="Bairro" class="crm-input md:col-span-2" />
              <input v-model="createForm.birthdate" type="date" class="crm-input" />
            </div>
            <textarea v-model="createForm.notes" rows="4" placeholder="Observações" class="crm-input mt-3"></textarea>
          </div>
          <div class="flex shrink-0 justify-end gap-2 border-t border-slate-100 px-4 py-3 md:px-6">
            <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeCreateModal">Cancelar</button>
            <button type="button" class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60" :disabled="creating" @click="handleCreateClient">
              {{ creating ? "Salvando..." : "Salvar cliente" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import { useAuthStore } from "../../store/useAuthStore";
import { API_PERMISSION_DENIED_EVENT } from "../../services/api";

const router = useRouter();
const leadStore = useLeadCaptureStore();
const authStore = useAuthStore();

const clients = computed(() => leadStore.clients);
const loading = computed(() => leadStore.clientsLoading);

const clientsWithOpportunities = computed(() => clients.value.filter(client => (client.opportunitiesCount || 0) > 0).length);
const totalRevenueCents = computed(() => clients.value.reduce((sum, client) => sum + Number(client.totalEstimatedValueCents || 0), 0));
const latestOpportunityDate = computed(() => {
  const sorted = [...clients.value]
    .map(client => client.lastOpportunityAt)
    .filter(Boolean)
    .sort((a, b) => new Date(String(b)).getTime() - new Date(String(a)).getTime());
  if (!sorted.length) return "Sem oportunidades";
  return formatDate(sorted[0]);
});

const filters = reactive({
  q: "",
  city: "",
  period: "all",
  status: "all"
});

const createModalOpen = ref(false);
const creating = ref(false);
const createForm = reactive({
  name: "",
  cpf: "",
  phone: "",
  email: "",
  city: "",
  zipcode: "",
  street: "",
  number: "",
  complement: "",
  neighborhood: "",
  state: "",
  birthdate: "",
  notes: ""
});

const loadClients = async () => {
  const now = new Date();
  let createdFrom: string | undefined;
  if (filters.period !== "all") {
    const days = Number(filters.period || 0);
    if (days > 0) {
      const start = new Date(now);
      start.setDate(now.getDate() - days);
      createdFrom = start.toISOString().slice(0, 10);
    }
  }

  await leadStore.fetchClients({
    q: filters.q.trim() || undefined,
    city: filters.city.trim() || undefined,
    hasOpenOpportunities: filters.status === "with" ? true : undefined,
    withoutOpportunities: filters.status === "without" ? true : undefined,
    createdFrom
  });
};

const canManageLeads = computed(() => {
  const user = authStore.user;
  if (!user) return true;
  if (user.is_owner ?? true) return true;
  if ((user.role || "member").toLowerCase() === "admin") return true;
  const effective = user.effective_permissions || [];
  return effective.includes("leads_manager") || effective.includes("leads_full");
});

const showReadOnlySnackbar = (message = "Seu perfil permite apenas visualização.") => {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent(API_PERMISSION_DENIED_EVENT, {
      detail: { message, status: 403, method: "post" }
    })
  );
};

const showSuccessSnackbar = (message: string) => {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent(API_PERMISSION_DENIED_EVENT, {
      detail: { message, status: 200, method: "delete" }
    })
  );
};

const goToClient = (clientId: number) => router.push(`/admin/leads/clients/${clientId}`);
const handleDeleteClient = async (clientId: number) => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  if (!window.confirm("Excluir este cliente? Esta ação não pode ser desfeita.")) return;
  try {
    await leadStore.deleteClient(clientId);
    await loadClients();
    showSuccessSnackbar("Cliente excluído com sucesso.");
  } catch (error) {
    console.error("Erro ao excluir cliente", error);
  }
};

const openCreateModal = () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  createModalOpen.value = true;
};

const closeCreateModal = () => {
  createModalOpen.value = false;
  Object.assign(createForm, {
    name: "",
    cpf: "",
    phone: "",
    email: "",
    city: "",
    zipcode: "",
    street: "",
    number: "",
    complement: "",
    neighborhood: "",
    state: "",
    birthdate: "",
    notes: ""
  });
};

const handleCreateClient = async () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  if (!createForm.name.trim()) return;
  creating.value = true;
  try {
    const client = await leadStore.createClient({
      name: createForm.name.trim(),
      cpf: createForm.cpf.trim() || null,
      phone: createForm.phone.trim() || null,
      email: createForm.email.trim() || null,
      city: createForm.city.trim() || null,
      zipcode: createForm.zipcode.trim() || null,
      street: createForm.street.trim() || null,
      number: createForm.number.trim() || null,
      complement: createForm.complement.trim() || null,
      neighborhood: createForm.neighborhood.trim() || null,
      state: createForm.state.trim().toUpperCase() || null,
      birthdate: createForm.birthdate || null,
      notes: createForm.notes.trim() || null
    });
    closeCreateModal();
    goToClient(client.id);
  } finally {
    creating.value = false;
  }
};

watch(
  () => ({ ...filters }),
  () => {
    window.clearTimeout((loadClients as any)._debounce);
    (loadClients as any)._debounce = window.setTimeout(() => {
      loadClients().catch(error => console.error(error));
    }, 280);
  },
  { deep: true, immediate: true }
);

function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format((value || 0) / 100);
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(date);
}

function formatPhone(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length === 13 && digits.startsWith("55")) return `+55 (${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9, 13)}`;
  if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
  if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6, 10)}`;
  return value || "";
}

function clientInitials(name?: string | null) {
  const words = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!words.length) return "CL";
  return `${words[0][0] || ""}${words[1]?.[0] || ""}`.toUpperCase();
}

function avatarChipStyle(client: any) {
  const palette = [
    { bg: "#dff3e5", fg: "#0f6b35" },
    { bg: "#e4e8ff", fg: "#3748c7" },
    { bg: "#ffeccc", fg: "#b86a00" },
    { bg: "#dff0ff", fg: "#006e9e" },
    { bg: "#f3e8ff", fg: "#6f2dbd" }
  ];
  const seed = String(client?.id ?? client?.name ?? "");
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  const picked = palette[hash % palette.length];
  return {
    backgroundColor: picked.bg,
    color: picked.fg
  };
}

function locationLabel(client: any) {
  const city = (client.city || "").trim();
  const state = (client.state || "").trim();
  if (city && state) return `${city} / ${state}`;
  return city || state || "-";
}

defineExpose({
  openCreateModal
});
</script>

<style scoped>
.clients-page {
  background: #f7f8f7;
}

.clients-sub {
  margin-top: -6px;
  font-size: 13px;
  color: #8a9e8a;
}

.crm-input {
  width: 100%;
  height: 44px;
  border-radius: 0.75rem;
  border: 1px solid #d9e2d9;
  padding: 0.65rem 0.9rem;
  font-size: 0.875rem;
  color: #4a5e4a;
  outline: none;
  background: #fff;
}
.crm-input:focus {
  border-color: var(--color-brand, #22c55e);
  box-shadow: 0 0 0 2px rgb(34 197 94 / 0.15);
}
.crm-input--search { padding-left: 2rem; }
.search-wrap { position: relative; }
.city-wrap { position: relative; }
.search-icon {
  position: absolute;
  left: 0.7rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  color: #8a9e8a;
  pointer-events: none;
}
.city-icon {
  position: absolute;
  left: 0.7rem;
  top: 50%;
  transform: translateY(-50%);
  color: #8a9e8a;
  pointer-events: none;
}
.search-icon svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.city-icon svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.crm-input--city {
  padding-left: 2rem;
}
.clients-filters-row select.crm-input {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238A9E8A' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-size: 14px;
  background-position: right 10px center;
  padding-right: 30px;
}
.kpi-card {
  border: 1px solid rgb(226 232 240);
  background: #fff;
  border-radius: 14px;
  padding: 16px 18px;
  position: relative;
  box-shadow: 0 10px 24px -24px rgba(15, 23, 42, 0.45);
}
.kpi-icon {
  display: inline-flex;
  width: 30px;
  height: 30px;
  color: #8a9e8a;
  opacity: 0.9;
}
.kpi-icon svg {
  width: 100%;
  height: 100%;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.kpi-icon--doc svg,
.kpi-icon--money svg {
  transform: translateX(-4px);
}
.kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .08em; color: #64748b; font-weight: 700; }
.kpi-value { font-size: 1.85rem; font-weight: 800; color: #0f172a; margin-top: 0.35rem; line-height: 1.05; }
.kpi-sub { font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; }
.kpi-card--revenue-positive {
  border-color: rgb(226 232 240);
  background: #fff;
}
.kpi-card--revenue-positive .kpi-icon,
.kpi-card--revenue-positive .kpi-label,
.kpi-card--revenue-positive .kpi-value,
.kpi-card--revenue-positive .kpi-sub {
  color: #15803d;
}
.avatar-chip {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e2f7e8;
  color: #0f5132;
  font-size: .75rem;
  font-weight: 800;
}
.op-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.32rem 0.72rem;
  font-size: 0.73rem;
  font-weight: 700;
}
.op-badge.is-hot { background: #e5f9ec; color: #15803d; }
.op-badge.is-cold { background: #f1f5f9; color: #475569; }
.table-action {
  border: 1px solid #dbe4ee;
  border-radius: 999px;
  padding: 0.34rem 0.68rem;
  font-size: 0.73rem;
  font-weight: 700;
  color: #334155;
  background: #fff;
}
.table-action:hover { background: #f8fafc; }
.table-action--primary {
  border-color: #bbf7d0;
  color: #166534;
  background: #ecfdf3;
}
.table-action--primary:hover { background: #dcfce7; }
.table-action--danger {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff5f5;
}
.table-action--danger:hover { background: #fee2e2; }
.client-row {
  position: relative;
  box-shadow: inset 0 0 0 0 rgba(15, 23, 42, 0);
}
.client-row:hover {
  background: linear-gradient(180deg, #fbfdff 0%, #f8fbff 100%);
  box-shadow: inset 0 1px 0 rgba(226, 232, 240, 0.9), inset 0 -1px 0 rgba(226, 232, 240, 0.9), 0 10px 24px -24px rgba(15, 23, 42, 0.45);
}
.menu-trigger {
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  width: 2rem;
  height: 2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  background: #fff;
  transition: all 0.18s ease;
}
.menu-trigger svg {
  width: 14px;
  height: 14px;
}
.menu-trigger--danger {
  color: #b91c1c;
  border-color: #fecaca;
  background: #fff5f5;
}
.menu-trigger:hover {
  background: #f7fbf8;
  border-color: #cfe6d6;
  color: #2f7f48;
}
.client-card {
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background-color 0.18s ease;
}
.client-card:hover {
  border-color: #d9e6de;
  background: linear-gradient(180deg, #ffffff 0%, #fbfefc 100%);
  box-shadow: 0 16px 32px -28px rgba(15, 23, 42, 0.45);
  transform: translateY(-1px);
}
.empty-state {
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  text-align: center;
}
.empty-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

@media (max-width: 900px) {
  .clients-sub { font-size: 12px; }
  .kpi-value { font-size: 1.9rem; }
  .clients-filters-row {
    grid-template-columns: 1fr !important;
  }
}
</style>
