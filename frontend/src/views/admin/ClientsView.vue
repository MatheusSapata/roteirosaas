<template>
  <div class="space-y-5">
    <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <article class="kpi-card">
        <span class="kpi-icon">👥</span>
        <p class="kpi-label">Total de clientes</p>
        <p class="kpi-value">{{ clients.length }}</p>
        <p class="kpi-sub">Base comercial ativa</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-icon">📈</span>
        <p class="kpi-label">Com oportunidades</p>
        <p class="kpi-value">{{ clientsWithOpportunities }}</p>
        <p class="kpi-sub">Clientes em negociação</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-icon">💰</span>
        <p class="kpi-label">Receita total</p>
        <p class="kpi-value">{{ formatCurrency(totalRevenueCents) }}</p>
        <p class="kpi-sub">Somatório estimado</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-icon">🕒</span>
        <p class="kpi-label">Última oportunidade</p>
        <p class="kpi-value text-lg">{{ latestOpportunityDate }}</p>
        <p class="kpi-sub">Movimento mais recente</p>
      </article>
    </section>

    <section class="rounded-3xl border border-slate-200 bg-white p-3 shadow-sm">
      <div class="grid gap-2 md:grid-cols-[1.7fr_repeat(3,minmax(0,1fr))]">
        <div class="search-wrap">
          <span class="search-icon">⌕</span>
          <input v-model="filters.q" type="text" placeholder="Buscar cliente, CPF, telefone ou e-mail..." class="crm-input crm-input--search" />
        </div>
        <input v-model="filters.city" type="text" placeholder="Cidade" class="crm-input" />
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
        <div class="empty-icon">◌</div>
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
                    <span class="avatar-chip">{{ clientInitials(client.name) }}</span>
                    <div>
                      <p class="text-[1.06rem] font-semibold leading-tight text-slate-900">{{ client.name }}</p>
                      <p class="text-sm text-slate-500">Cliente desde {{ formatDate(client.created_at) }}</p>
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
                    <button type="button" class="menu-trigger" @click.stop="toggleRowMenu(client.id, $event)">
                      •••
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="space-y-3 p-3 lg:hidden">
          <article v-for="client in clients" :key="`mobile-${client.id}`" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="font-semibold text-slate-900">{{ client.name }}</p>
                <p class="text-xs text-slate-500">Cliente desde {{ formatDate(client.created_at) }}</p>
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
            <div class="mt-3 flex gap-2">
              <button type="button" class="table-action" @click="goToClient(client.id)">Ver perfil</button>
              <button type="button" class="table-action" @click="openNewOpportunity(client.id)">Nova oportunidade</button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <Teleport to="body">
      <div
        v-if="openRowMenuId !== null"
        class="row-menu row-menu--floating"
        :style="{ top: `${rowMenuPosition.top}px`, left: `${rowMenuPosition.left}px` }"
        @click.stop
      >
        <button type="button" @click="goToClient(openRowMenuId)">Ver cliente</button>
        <button type="button" @click="openNewOpportunity(openRowMenuId)">Nova oportunidade</button>
        <button type="button" @click="goToClient(openRowMenuId)">Editar cliente</button>
        <button type="button" class="danger" @click="handleDeleteClient(openRowMenuId)">Excluir</button>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="createModalOpen" class="fixed inset-0 z-[150] flex items-center justify-center bg-slate-900/45 p-3 md:px-4">
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
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
const openRowMenuId = ref<number | null>(null);
const rowMenuPosition = ref({ top: 0, left: 0 });
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

const goToClient = (clientId: number) => router.push(`/admin/leads/clients/${clientId}`);
const openNewOpportunity = (clientId: number) => router.push(`/admin/leads/opportunities?clientId=${clientId}`);
const toggleRowMenu = (clientId: number, event: MouseEvent) => {
  if (openRowMenuId.value === clientId) {
    openRowMenuId.value = null;
    return;
  }
  const trigger = event.currentTarget as HTMLElement | null;
  if (!trigger) return;
  const rect = trigger.getBoundingClientRect();
  const menuWidth = 196;
  const viewportPadding = 8;
  const left = Math.min(
    window.innerWidth - menuWidth - viewportPadding,
    Math.max(viewportPadding, rect.right - menuWidth)
  );
  const top = rect.bottom + 8;
  rowMenuPosition.value = { top, left };
  openRowMenuId.value = clientId;
};
const handleDeleteClient = (clientId: number) => {
  openRowMenuId.value = null;
  router.push(`/admin/leads/clients/${clientId}`);
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

const closeRowMenu = () => {
  openRowMenuId.value = null;
};

onMounted(() => {
  window.addEventListener("click", closeRowMenu);
});

onUnmounted(() => {
  window.removeEventListener("click", closeRowMenu);
});

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
.crm-input {
  width: 100%;
  border-radius: 0.95rem;
  border: 1px solid rgb(226 232 240);
  padding: 0.65rem 0.85rem;
  font-size: 0.875rem;
  color: rgb(15 23 42);
  outline: none;
  background: #fff;
}
.crm-input:focus {
  border-color: var(--color-brand, #22c55e);
  box-shadow: 0 0 0 2px rgb(34 197 94 / 0.15);
}
.crm-input--search { padding-left: 2rem; }
.search-wrap { position: relative; }
.search-icon {
  position: absolute;
  left: 0.7rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 0.82rem;
  pointer-events: none;
}
.kpi-card {
  border: 1px solid rgb(226 232 240);
  background: #fff;
  border-radius: 1rem;
  padding: 0.85rem 1rem;
  position: relative;
}
.kpi-icon {
  position: absolute;
  right: 0.75rem;
  top: 0.6rem;
  opacity: 0.55;
  font-size: 0.95rem;
}
.kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .08em; color: #64748b; font-weight: 700; }
.kpi-value { font-size: 1.35rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem; }
.kpi-sub { font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; }
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
  padding: 0.25rem 0.6rem;
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
.client-row {
  box-shadow: inset 0 0 0 0 rgba(15, 23, 42, 0);
}
.client-row:hover {
  background: #f8fbff;
  box-shadow: inset 0 1px 0 rgba(226, 232, 240, 0.9), inset 0 -1px 0 rgba(226, 232, 240, 0.9), 0 6px 16px -16px rgba(15, 23, 42, 0.4);
}
.menu-trigger {
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  width: 1.85rem;
  height: 1.85rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  line-height: 1;
  letter-spacing: 0.02em;
  font-weight: 600;
  color: #64748b;
  background: #fff;
}
.menu-trigger:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #475569;
}
.row-menu {
  position: fixed;
  z-index: 1200;
  min-width: 180px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 0.85rem;
  box-shadow: 0 16px 30px -20px rgba(15, 23, 42, 0.4);
  overflow: hidden;
}
.row-menu button {
  width: 100%;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  padding: 0.6rem 0.8rem;
  border: 0;
  background: transparent;
}
.row-menu button:hover { background: #f8fafc; }
.row-menu button.danger { color: #b91c1c; }
.row-menu--floating { min-width: 196px; }
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
</style>
