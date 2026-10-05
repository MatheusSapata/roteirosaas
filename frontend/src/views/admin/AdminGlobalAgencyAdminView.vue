<template>
  <div class="am-page w-full">
    <AdminMasterHeader title="Admins globais" subtitle="Contas com acesso de admin numa agência, sem aparecer na equipe dela.">
      <button type="button" class="am-btn" :disabled="adminsLoading" @click="loadGlobalAdmins">
        <AmIcon name="refresh" :class="adminsLoading ? 'animate-spin' : ''" />
        Atualizar
      </button>
      <button type="button" class="am-btn am-btn-primary" @click="openPanel">
        <AmIcon name="plus" />
        Criar admin global
      </button>
    </AdminMasterHeader>

    <div v-if="adminsError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ adminsError }}</span></div>

    <section class="am-card am-card-flush">
      <div class="am-toolbar">
        <label class="am-search">
          <AmIcon name="search" />
          <input v-model="search" type="search" placeholder="Buscar por nome, e-mail ou agência" aria-label="Buscar admin global" />
        </label>
        <span class="am-chip">{{ globalAdmins.length }} {{ globalAdmins.length === 1 ? "admin" : "admins" }}</span>
      </div>

      <div v-if="adminsLoading && !globalAdmins.length" class="am-empty">
        <div class="am-spinner"></div>
        Carregando admins globais...
      </div>
      <div v-else class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th>Pessoa</th>
              <th>Agência vinculada</th>
              <th>Situação</th>
              <th>Criado em</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="admin in filteredAdmins" :key="admin.id">
              <td>
                <div class="am-who">
                  <span class="am-avatar">{{ initials(admin.name) }}</span>
                  <div class="min-w-0">
                    <b class="truncate">{{ admin.name }}</b>
                    <small class="truncate">{{ admin.email }}</small>
                  </div>
                </div>
              </td>
              <td>
                <b class="font-semibold">{{ admin.agency_name }}</b>
                <div class="am-mono am-muted">/{{ admin.agency_slug }}</div>
              </td>
              <td>
                <span class="am-badge am-dot" :class="statusTone(admin.status)">{{ statusLabel(admin.status) }}</span>
              </td>
              <td class="am-num">{{ formatDate(admin.created_at) }}</td>
            </tr>
            <tr v-if="!filteredAdmins.length">
              <td colspan="4">
                <div class="am-empty">{{ search ? "Nenhum admin encontrado nessa busca." : "Nenhum admin global cadastrado ainda." }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <AdminMasterDrawer
      :open="panelOpen"
      title="Criar admin global"
      subtitle="Acesso de admin na agência, sem aparecer na equipe."
      icon="shield"
      tone="warning"
      @close="panelOpen = false"
    >
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div class="am-field sm:col-span-2">
          <label for="ga-name">Nome</label>
          <input id="ga-name" v-model="form.name" type="text" class="am-input" placeholder="Nome completo" />
        </div>
        <div class="am-field">
          <label for="ga-email">E-mail</label>
          <input id="ga-email" v-model="form.email" type="email" class="am-input" placeholder="usuario@dominio.com" />
        </div>
        <div class="am-field">
          <label for="ga-pass">Senha</label>
          <input id="ga-pass" v-model="form.password" type="password" class="am-input" placeholder="Mínimo de 8 caracteres" />
        </div>
        <div class="am-field">
          <label for="ga-cpf">CPF <span class="font-normal text-muted-foreground">(opcional)</span></label>
          <input id="ga-cpf" v-model="form.cpf" type="text" class="am-input" placeholder="000.000.000-00" />
        </div>
        <div class="am-field">
          <label for="ga-whats">WhatsApp <span class="font-normal text-muted-foreground">(opcional)</span></label>
          <input id="ga-whats" v-model="form.whatsapp" type="text" class="am-input" placeholder="(00) 00000-0000" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="ga-cnpj">CNPJ <span class="font-normal text-muted-foreground">(opcional)</span></label>
          <input id="ga-cnpj" v-model="form.cnpj" type="text" class="am-input" placeholder="00.000.000/0000-00" />
        </div>
        <div class="am-field sm:col-span-2">
          <label for="ga-agency">Agência</label>
          <select id="ga-agency" v-model.number="form.agency_id" class="am-input" :disabled="agenciesLoading">
            <option :value="null">{{ agenciesLoading ? "Carregando agências..." : "Escolher depois" }}</option>
            <option v-for="agency in agencyOptions" :key="agency.id" :value="agency.id">
              {{ agency.name }} · /{{ agency.slug }}
            </option>
          </select>
          <p class="am-card-sub">{{ agencyOptions.length }} agências disponíveis</p>
        </div>
      </div>
      <div class="am-notice am-tone-info mt-4">
        <AmIcon name="eye" />
        <span>O vínculo fica oculto na equipe da agência, mas a pessoa entra com permissão de admin.</span>
      </div>
      <div v-if="agenciesError" class="am-notice am-tone-danger mt-3"><AmIcon name="alert" /><span>{{ agenciesError }}</span></div>

      <template #footer>
        <button type="button" class="am-btn" :disabled="loading" @click="panelOpen = false">Cancelar</button>
        <button type="button" class="am-btn am-btn-primary" :disabled="loading" @click="createGlobalAdmin">
          {{ loading ? "Criando..." : "Criar admin global" }}
        </button>
      </template>
    </AdminMasterDrawer>

    <div v-if="snackbar" class="fixed bottom-5 right-5 z-50 rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background shadow-lg">
      {{ snackbar }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterDrawer from "../../components/admin/master/AdminMasterDrawer.vue";

interface AdminAgencySummary {
  id: number;
  name: string;
  slug: string;
  created_at?: string;
  pages_count: number;
}

interface AdminGlobalAgencyAdmin {
  id: number;
  name: string;
  email: string;
  agency_id: number;
  agency_name: string;
  agency_slug: string;
  role: string;
  status?: string | null;
  created_at?: string | null;
}

const agencyOptions = ref<AdminAgencySummary[]>([]);
const agenciesLoading = ref(false);
const agenciesError = ref("");
const globalAdmins = ref<AdminGlobalAgencyAdmin[]>([]);
const adminsLoading = ref(false);
const adminsError = ref("");
const snackbar = ref("");
const loading = ref(false);
const form = reactive({
  name: "",
  email: "",
  password: "",
  cpf: "",
  whatsapp: "",
  cnpj: "",
    agency_id: null as number | null
});

const panelOpen = ref(false);
const search = ref("");
const filteredAdmins = computed(() => {
  const term = search.value.trim().toLowerCase();
  if (!term) return globalAdmins.value;
  return globalAdmins.value.filter(admin =>
    [admin.name, admin.email, admin.agency_name, admin.agency_slug].some(value => String(value || "").toLowerCase().includes(term))
  );
});
const initials = (name?: string | null) =>
  String(name || "?")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "?";
const statusLabel = (status?: string | null) => {
  const value = String(status || "active").toLowerCase();
  if (value === "active") return "Ativo";
  if (value === "invited" || value === "pending") return "Convite pendente";
  if (value === "inactive" || value === "disabled") return "Inativo";
  return status || "Ativo";
};
const statusTone = (status?: string | null) => {
  const value = String(status || "active").toLowerCase();
  if (value === "active") return "am-tone-success";
  if (value === "invited" || value === "pending") return "am-tone-warning";
  return "am-tone-neutral";
};
const openPanel = () => {
  agenciesError.value = "";
  panelOpen.value = true;
  if (!agencyOptions.value.length && !agenciesLoading.value) void loadAgencies();
};

const showSnackbar = (text: string) => {
  snackbar.value = text;
  window.setTimeout(() => {
    snackbar.value = "";
  }, 3000);
};

const formatDate = (val?: string | null) => {
  if (!val) return "--";
  const date = new Date(val);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleDateString("pt-BR");
};

const resetForm = () => {
  form.name = "";
  form.email = "";
  form.password = "";
  form.cpf = "";
  form.whatsapp = "";
  form.cnpj = "";
  agenciesError.value = "";
};

const loadAgencies = async () => {
  agenciesLoading.value = true;
  agenciesError.value = "";
  try {
    const { data } = await api.get<AdminAgencySummary[]>("/admin/agencies");
    agencyOptions.value = Array.isArray(data) ? data : [];
  } catch (err: any) {
    console.error(err);
    agenciesError.value = err?.response?.data?.detail || "Não foi possível carregar as agências.";
  } finally {
    agenciesLoading.value = false;
  }
};

const loadGlobalAdmins = async () => {
  adminsLoading.value = true;
  adminsError.value = "";
  try {
    const { data } = await api.get<AdminGlobalAgencyAdmin[]>("/admin/users/global-admins");
    globalAdmins.value = Array.isArray(data) ? data : [];
  } catch (err: any) {
    console.error(err);
    adminsError.value = err?.response?.data?.detail || "Não foi possível carregar os admins globais.";
  } finally {
    adminsLoading.value = false;
  }
};

const createGlobalAdmin = async () => {
  if (loading.value) return;
  const payload = {
    name: form.name.trim(),
    email: form.email.trim(),
    password: form.password.trim(),
    cpf: form.cpf.trim(),
    whatsapp: form.whatsapp.trim(),
    cnpj: form.cnpj.trim() || null,
    agency_id: form.agency_id
  };

  if (!payload.name || !payload.email || !payload.password) {
    agenciesError.value = "Preencha nome, e-mail e senha.";
    return;
  }

  loading.value = true;
  agenciesError.value = "";
  try {
    await api.post("/admin/users/global-admin", payload);
    showSnackbar("Admin global criado.");
    resetForm();
    form.agency_id = null;
    panelOpen.value = false;
    void loadGlobalAdmins();
  } catch (err: any) {
    console.error(err);
    agenciesError.value = err?.response?.data?.detail || "Não foi possível criar o usuário.";
  } finally {
    loading.value = false;
  }
};

watch(
  agencyOptions,
  options => {
    if (!options.length) {
      form.agency_id = null;
    }
  },
  { immediate: true }
);

onMounted(() => {
  void loadAgencies();
  void loadGlobalAdmins();
});
</script>
