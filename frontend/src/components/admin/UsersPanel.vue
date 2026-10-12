<template>
  <section class="am-page">
    <AdminMasterHeader
      title="Usuários"
      subtitle="As pessoas com acesso ao Roteiro Online: em qual empresa estão, com que papel e quando entraram por último. Plano e cobrança ficam em Empresas."
    >
      <router-link to="/admin/administracao/empresas" class="am-btn"><AmIcon name="building" />Empresas</router-link>
      <button type="button" class="am-btn" :disabled="loading" @click="load()"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-grid-4">
      <AdminMasterKpi icon="users" tone="info" label="Pessoas" :value="formatInt(people.length)" :hint="`${formatInt(filterCount('owners'))} donos · ${formatInt(filterCount('team'))} da equipe`" />
      <AdminMasterKpi icon="pulse" tone="success" label="Online agora" :value="formatInt(filterCount('online'))" hint="Ativas nos últimos 10 minutos" />
      <AdminMasterKpi icon="history" tone="violet" label="Entraram em 7 dias" :value="formatInt(filterCount('recent'))" :hint="`${formatInt(filterCount('idle_30'))} sem entrar há mais de 30 dias`" />
      <AdminMasterKpi icon="alert" tone="warning" label="Nunca entraram" :value="formatInt(filterCount('never'))" hint="Conta criada, sem nenhum acesso registrado" />
    </section>

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
          {{ option.label }} <span class="am-count am-num">{{ formatInt(filterCount(option.value)) }}</span>
        </button>
      </div>
      <div class="am-toolbar">
        <label class="am-search">
          <AmIcon name="search" />
          <input v-model="query" type="search" placeholder="Buscar por nome, e-mail, WhatsApp ou empresa" aria-label="Buscar usuário" />
        </label>
        <select v-model="roleFilter" class="am-select" aria-label="Filtrar por papel">
          <option value="">Papel: todos</option>
          <option v-for="role in roleChoices" :key="role" :value="role">{{ roleLabel(role) }}</option>
        </select>
      </div>

      <div class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th v-for="column in columns" :key="column.key" :class="column.right ? 'am-right' : ''" :aria-sort="column.sortable ? sort.ariaSort(column.key) : undefined">
                <button v-if="column.sortable" type="button" class="up-sort" :class="{ on: sort.sortKey.value === column.key }" @click="sort.setSort(column.key)">
                  {{ column.label }} <span aria-hidden="true">{{ sort.arrow(column.key) }}</span>
                </button>
                <span v-else>{{ column.label }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading && !people.length">
              <td :colspan="columns.length"><div class="am-empty"><div class="am-spinner"></div>Carregando usuários...</div></td>
            </tr>
            <tr v-for="person in pageItems" :key="person.id">
              <td>
                <div class="am-who">
                  <span class="am-avatar relative">
                    {{ initials(person.name) }}
                    <i v-if="person.online" class="up-online" title="Online agora"></i>
                  </span>
                  <div class="min-w-0 select-text">
                    <b class="max-w-[240px] truncate">{{ person.name }}</b>
                    <small class="max-w-[240px] truncate">{{ person.email }}</small>
                  </div>
                  <span v-if="person.is_superuser" class="am-badge am-tone-violet">Superusuário</span>
                  <span v-else-if="person.global_admin" class="am-badge am-tone-violet">Admin global</span>
                </div>
              </td>
              <td>
                <template v-if="person.companies.length">
                  <RouterLink :to="companyLink(person.companies[0])" class="up-company">{{ person.companies[0].name }}</RouterLink>
                  <small class="am-muted block whitespace-nowrap">
                    {{ person.companies[0].is_owner ? "Dono" : roleLabel(person.companies[0].role) }}
                    <template v-if="person.companies.length > 1"> · +{{ person.companies.length - 1 }} {{ person.companies.length === 2 ? "empresa" : "empresas" }}</template>
                  </small>
                </template>
                <span v-else class="am-muted">Sem empresa</span>
              </td>
              <td>
                <span v-if="person.companies.length" class="am-badge am-dot" :class="statusTone(person.companies[0].status)">{{ person.companies[0].status_label }}</span>
                <span v-else class="am-muted">—</span>
              </td>
              <td class="am-num">
                <span v-if="person.online" class="font-semibold text-status-success-foreground">Online agora</span>
                <template v-else>{{ person.last_access_at ? relativeDay(person.last_access_at) : "Nunca entrou" }}</template>
                <small v-if="person.active_sessions" class="am-muted block">{{ plural(person.active_sessions, "sessão aberta", "sessões abertas") }}</small>
              </td>
              <td class="am-num">{{ formatDate(person.created_at) }}</td>
              <td class="am-right">
                <div class="relative inline-block" data-user-menu="true">
                  <button
                    type="button"
                    class="am-icon-btn"
                    :aria-label="`Ações de ${person.name}`"
                    :aria-expanded="menuId === person.id"
                    @click="menuId = menuId === person.id ? null : person.id"
                  >
                    <AmIcon name="dots" />
                  </button>
                  <div v-if="menuId === person.id" class="am-menu right-0 top-full mt-1">
                    <RouterLink v-for="company in person.companies" :key="company.id" :to="companyLink(company)" @click="menuId = null">
                      <AmIcon name="building" />Abrir {{ company.name }}
                    </RouterLink>
                    <button type="button" @click="run(() => copyEmail(person))"><AmIcon name="copy" />Copiar e-mail</button>
                    <a v-if="whatsappLink(person)" :href="whatsappLink(person)" target="_blank" rel="noopener noreferrer" @click="menuId = null">
                      <AmIcon name="wa" />Chamar no WhatsApp
                    </a>
                    <button type="button" :disabled="!person.active_sessions" @click="run(() => ask('logout', person))">
                      <AmIcon name="logout" />{{ person.active_sessions ? "Deslogar de todos os aparelhos" : "Sem sessão aberta" }}
                    </button>
                    <button v-if="!person.is_superuser" type="button" class="is-danger" @click="run(() => ask('delete', person))">
                      <AmIcon name="trash" />Excluir usuário
                    </button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !pageItems.length">
              <td :colspan="columns.length"><div class="am-empty">Nenhuma pessoa com esses filtros.</div></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="am-foot">
        <span>Mostrando {{ formatInt(range.start) }}–{{ formatInt(range.end) }} de {{ formatInt(sorted.length) }}</span>
        <div class="flex flex-wrap items-center gap-2">
          <label class="flex items-center gap-2">
            Linhas
            <select v-model.number="pageSize" class="am-select">
              <option v-for="size in [25, 50, 100]" :key="size" :value="size">{{ size }}</option>
            </select>
          </label>
          <button type="button" class="am-chip" :disabled="page <= 1" @click="page -= 1">Anterior</button>
          <span>Página {{ page }} de {{ totalPages }}</span>
          <button type="button" class="am-chip" :disabled="page >= totalPages" @click="page += 1">Próxima</button>
        </div>
      </div>
    </section>

    <AdminMasterConfirm
      :open="Boolean(pending)"
      :title="pending?.action === 'delete' ? `Excluir ${pending.person.name}?` : `Deslogar ${pending?.person.name}?`"
      :confirm-label="pending?.action === 'delete' ? 'Excluir de vez' : 'Deslogar agora'"
      :busy-label="pending?.action === 'delete' ? 'Excluindo...' : 'Deslogando...'"
      :busy="busy"
      :error="actionError"
      :icon="pending?.action === 'delete' ? 'trash' : 'logout'"
      :tone="pending?.action === 'delete' ? 'danger' : 'warning'"
      @close="closeConfirm"
      @confirm="runAction"
    >
      <template v-if="pending?.action === 'logout'">
        <p>Encerra {{ plural(pending.person.active_sessions, "sessão aberta", "sessões abertas") }}. A pessoa precisa entrar de novo com a senha em todos os aparelhos.</p>
      </template>
      <template v-else-if="pending">
        <p v-if="ownedCompanies(pending.person).length">
          {{ pending.person.name }} é dono de {{ ownedCompanies(pending.person).map(company => company.name).join(", ") }}.
          Excluir apaga a conta e também essas empresas, com as páginas. Não dá para desfazer.
        </p>
        <p v-else>Apaga a conta de {{ pending.person.name }} e tira a pessoa das equipes em que está. Não dá para desfazer.</p>
      </template>
    </AdminMasterConfirm>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { deleteUser, listMasterUsers, revokeUserSessions, type MasterUser, type MasterUserCompany } from "../../services/adminMaster";
import AmIcon from "./master/AmIcon.vue";
import AdminMasterHeader from "./master/AdminMasterHeader.vue";
import AdminMasterKpi from "./master/AdminMasterKpi.vue";
import AdminMasterConfirm from "./master/AdminMasterConfirm.vue";
import { useTableSort } from "./master/useTableSort";
import { daysSince, formatDate, formatInt, initials, plural, relativeDay, statusTone } from "./master/format";

type Filter = "all" | "online" | "owners" | "team" | "no_company" | "recent" | "idle_30" | "never" | "admins";
const filters: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "Todos" },
  { value: "online", label: "Online agora" },
  { value: "owners", label: "Donos de empresa" },
  { value: "team", label: "Equipe" },
  { value: "no_company", label: "Sem empresa" },
  { value: "recent", label: "Entraram em 7 dias" },
  { value: "idle_30", label: "Sem entrar +30 dias" },
  { value: "never", label: "Nunca entraram" },
  { value: "admins", label: "Admins" }
];
const columns = [
  { key: "name", label: "Pessoa", sortable: true },
  { key: "company", label: "Empresa", sortable: true },
  { key: "status", label: "Situação da empresa" },
  { key: "last_access", label: "Último acesso", sortable: true },
  { key: "created", label: "Cadastro", sortable: true },
  { key: "actions", label: "", right: true }
];
const roleLabels: Record<string, string> = { owner: "Dono", admin: "Administrador", editor: "Editor", viewer: "Leitura", member: "Membro" };
const roleLabel = (role: string) => roleLabels[role] || role || "Membro";

const route = useRoute();
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const people = ref<MasterUser[]>([]);
const filter = ref<Filter>("all");
const query = ref(String(route.query.busca || ""));
const roleFilter = ref("");

const isAdmin = (person: MasterUser) => person.is_superuser || person.global_admin;
const ownedCompanies = (person: MasterUser) => person.companies.filter(company => company.is_owner);
const mainRole = (person: MasterUser) => {
  const first = person.companies[0];
  if (!first) return "";
  return first.is_owner ? "owner" : first.role || "member";
};
const matches = (person: MasterUser, value: Filter) => {
  const since = daysSince(person.last_access_at);
  switch (value) {
    case "online":
      return person.online;
    case "owners":
      return ownedCompanies(person).length > 0;
    case "team":
      return person.companies.length > 0 && !ownedCompanies(person).length;
    case "no_company":
      return !person.companies.length && !isAdmin(person);
    case "recent":
      return since !== null && since < 7;
    case "idle_30":
      return since !== null && since >= 30;
    case "never":
      return !person.last_access_at;
    case "admins":
      return isAdmin(person);
    default:
      return true;
  }
};
const filterCount = (value: Filter) => people.value.filter(person => matches(person, value)).length;
const roleChoices = computed(() => [...new Set(people.value.map(mainRole).filter(Boolean))].sort());

const filtered = computed(() => {
  const text = query.value.trim().toLowerCase();
  const digits = text.replace(/\D/g, "");
  return people.value.filter(person => {
    if (!matches(person, filter.value)) return false;
    if (roleFilter.value && mainRole(person) !== roleFilter.value) return false;
    if (!text) return true;
    const haystack = `${person.name} ${person.email} ${person.companies.map(company => company.name).join(" ")}`.toLowerCase();
    if (haystack.includes(text)) return true;
    return digits.length >= 4 && String(person.whatsapp || "").replace(/\D/g, "").includes(digits);
  });
});

const time = (value?: string | null) => (value ? new Date(value).getTime() : null);
const sort = useTableSort(
  filtered,
  {
    name: person => person.name,
    company: person => person.companies[0]?.name,
    last_access: person => (person.online ? Date.now() : time(person.last_access_at) ?? 0),
    created: person => time(person.created_at)
  },
  { key: "created", dir: "desc" },
  { created: "desc", last_access: "desc" }
);
const sorted = sort.sorted;

const page = ref(1);
const pageSize = ref(25);
const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / pageSize.value)));
const pageItems = computed(() => sorted.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value));
const range = computed(() => {
  if (!sorted.value.length) return { start: 0, end: 0 };
  const start = (page.value - 1) * pageSize.value + 1;
  return { start, end: Math.min(sorted.value.length, start + pageSize.value - 1) };
});
watch([filter, query, roleFilter, pageSize, () => sort.sortKey.value, () => sort.sortDir.value], () => {
  page.value = 1;
});
watch(totalPages, total => {
  if (page.value > total) page.value = total;
});
watch(
  () => route.query.busca,
  value => {
    if (value !== undefined) query.value = String(value || "");
  }
);

const companyLink = (company: MasterUserCompany) => ({ path: "/admin/administracao/empresas", query: { empresa: String(company.id) } });
const whatsappLink = (person: MasterUser) => {
  const digits = String(person.whatsapp || "").replace(/\D/g, "");
  if (!digits) return "";
  return `https://wa.me/${digits.length <= 11 ? `55${digits}` : digits}`;
};

// ---------- Menu e ações ----------
const menuId = ref<number | null>(null);
const run = (action: () => unknown) => {
  menuId.value = null;
  void action();
};
const closeMenuOutside = (event: MouseEvent) => {
  if (menuId.value === null) return;
  const inside = event.composedPath().some(el => (el as HTMLElement)?.dataset?.userMenu === "true");
  if (!inside) menuId.value = null;
};

const copyEmail = async (person: MasterUser) => {
  try {
    await navigator.clipboard.writeText(person.email);
    successMessage.value = `E-mail de ${person.name} copiado.`;
  } catch {
    window.prompt("Copie o e-mail:", person.email);
  }
};

const pending = ref<{ action: "logout" | "delete"; person: MasterUser } | null>(null);
const busy = ref(false);
const actionError = ref("");
const ask = (action: "logout" | "delete", person: MasterUser) => {
  pending.value = { action, person };
  actionError.value = "";
};
const closeConfirm = () => {
  if (!busy.value) pending.value = null;
};
const runAction = async () => {
  if (!pending.value) return;
  const { action, person } = pending.value;
  busy.value = true;
  actionError.value = "";
  try {
    if (action === "logout") {
      await revokeUserSessions(person.id);
      successMessage.value = `${person.name} foi deslogado de todos os aparelhos.`;
    } else {
      await deleteUser(person.id);
      successMessage.value = `${person.name} foi excluído.`;
    }
    pending.value = null;
    await load(true);
  } catch (error: any) {
    actionError.value = error?.response?.data?.detail || "Não foi possível concluir agora. Tente de novo.";
  } finally {
    busy.value = false;
  }
};

const load = async (keepMessage = false) => {
  loading.value = true;
  errorMessage.value = "";
  if (!keepMessage) successMessage.value = "";
  try {
    people.value = await listMasterUsers();
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || "Não foi possível carregar os usuários.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  window.addEventListener("click", closeMenuOutside);
  void load();
});
onBeforeUnmount(() => window.removeEventListener("click", closeMenuOutside));
</script>

<style scoped>
.up-online {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 10px;
  height: 10px;
  border: 2px solid var(--card);
  border-radius: 999px;
  background: var(--status-success-foreground);
}
.up-company {
  display: block;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  color: var(--foreground);
}
.up-company:hover {
  text-decoration: underline;
}
.up-sort {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: inherit;
  color: inherit;
  text-transform: inherit;
  letter-spacing: inherit;
  white-space: nowrap;
}
.up-sort span {
  opacity: 0.45;
}
.up-sort.on,
.up-sort.on span {
  color: var(--foreground);
  opacity: 1;
}
</style>
