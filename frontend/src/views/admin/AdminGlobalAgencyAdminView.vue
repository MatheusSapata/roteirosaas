<template>
  <div class="admin-master-view w-full space-y-6 px-4 py-8 md:px-8">
    <section class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
      <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">Admin master</p>
          <h1 class="text-2xl font-bold text-slate-900">Admin global</h1>
          <p class="mt-1 text-sm text-slate-500">
            Crie um usuário com acesso de admin vinculado a uma agência, sem exibir esse vínculo na equipe do frontend.
          </p>
        </div>
        <button
          type="button"
          class="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-60"
          :disabled="loading"
          @click="resetForm"
        >
          Limpar formulário
        </button>
      </div>

      <div v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ error }}
      </div>

      <div class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <label class="space-y-1 text-xs font-semibold text-slate-600">
          <span>Nome</span>
          <input
            v-model="form.name"
            type="text"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
            placeholder="Nome completo"
          />
        </label>

        <label class="space-y-1 text-xs font-semibold text-slate-600">
          <span>E-mail</span>
          <input
            v-model="form.email"
            type="email"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
            placeholder="usuario@dominio.com"
          />
        </label>

        <label class="space-y-1 text-xs font-semibold text-slate-600">
          <span>Senha</span>
          <input
            v-model="form.password"
            type="password"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
            placeholder="Senha de acesso"
          />
        </label>

        <label class="space-y-1 text-xs font-semibold text-slate-600">
          <span>CPF opcional</span>
          <input
            v-model="form.cpf"
            type="text"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
            placeholder="000.000.000-00"
          />
        </label>

        <label class="space-y-1 text-xs font-semibold text-slate-600">
          <span>WhatsApp opcional</span>
          <input
            v-model="form.whatsapp"
            type="text"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
            placeholder="(00) 00000-0000"
          />
        </label>

        <label class="space-y-1 text-xs font-semibold text-slate-600">
          <span>CNPJ opcional</span>
          <input
            v-model="form.cnpj"
            type="text"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
            placeholder="00.000.000/0000-00"
          />
        </label>

        <label class="space-y-1 text-xs font-semibold text-slate-600 md:col-span-2 xl:col-span-1">
          <span>Agência opcional</span>
          <select
            v-model.number="form.agency_id"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none"
          >
            <option :value="null">Selecionar depois</option>
            <option v-for="agency in agencyOptions" :key="agency.id" :value="agency.id">
              {{ agency.name }} ({{ agency.slug }})
            </option>
          </select>
        </label>
      </div>

      <div class="mt-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-60"
          :disabled="loading"
          @click="createGlobalAdmin"
        >
          {{ loading ? "Salvando..." : "Criar admin global" }}
        </button>
        <p class="text-xs text-slate-500">
          Esse vínculo será oculto da listagem da equipe, mas o usuário terá permissão de admin na agência escolhida.
        </p>
      </div>
    </section>

    <section class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">Agências disponíveis</h2>
          <p class="text-sm text-slate-500">A lista vem do cadastro completo de agências do admin master.</p>
        </div>
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
          :disabled="agenciesLoading"
          @click="loadAgencies"
        >
          Recarregar
        </button>
      </div>

      <div v-if="agenciesError" class="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        {{ agenciesError }}
      </div>

      <div class="mt-4 overflow-hidden rounded-xl border border-slate-200">
        <div class="grid grid-cols-1 divide-y divide-slate-100 md:grid-cols-3 md:divide-x md:divide-y-0">
          <div class="bg-slate-50 px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">Selecionada</p>
            <p class="mt-1 text-sm font-semibold text-slate-900">
              {{ selectedAgency?.name || "Nenhuma" }}
            </p>
          </div>
          <div class="px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">Slug</p>
            <p class="mt-1 text-sm font-semibold text-slate-900">
              {{ selectedAgency?.slug || "--" }}
            </p>
          </div>
          <div class="bg-slate-50 px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">Qtd.</p>
            <p class="mt-1 text-sm font-semibold text-slate-900">{{ agencyOptions.length }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl bg-white p-6 shadow-md ring-1 ring-slate-100">
      <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">Admins globais criados</h2>
          <p class="text-sm text-slate-500">Esses usuários têm vínculo oculto da equipe na agência selecionada.</p>
        </div>
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <span class="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-700">
            {{ globalAdmins.length }} registros
          </span>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-4 py-2 font-semibold text-slate-700 transition hover:bg-slate-50"
            :disabled="adminsLoading"
            @click="loadGlobalAdmins"
          >
            Atualizar lista
          </button>
        </div>
      </div>

      <div v-if="adminsError" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ adminsError }}
      </div>

      <div v-if="adminsLoading" class="mt-4 text-sm text-slate-500">
        Carregando admins globais...
      </div>

      <div v-else class="mt-4 overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-sm text-slate-700">
          <thead class="bg-slate-50 text-left text-xs uppercase tracking-[0.2em] text-slate-500">
            <tr>
              <th class="px-3 py-3">Nome</th>
              <th class="px-3 py-3">E-mail</th>
              <th class="px-3 py-3">Agência</th>
              <th class="px-3 py-3">Status</th>
              <th class="px-3 py-3">Criado em</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="admin in globalAdmins" :key="admin.id">
              <td class="px-3 py-3 font-semibold text-slate-900">{{ admin.name }}</td>
              <td class="px-3 py-3">{{ admin.email }}</td>
              <td class="px-3 py-3">
                <div class="font-semibold text-slate-900">{{ admin.agency_name }}</div>
                <div class="text-xs text-slate-500">/{{ admin.agency_slug }}</div>
              </td>
              <td class="px-3 py-3">
                <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  {{ admin.status || "active" }}
                </span>
              </td>
              <td class="px-3 py-3 text-slate-500">
                {{ formatDate(admin.created_at) }}
              </td>
            </tr>
            <tr v-if="!globalAdmins.length">
              <td colspan="5" class="px-3 py-8 text-center text-slate-500">
                Nenhum admin global cadastrado ainda.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div
      v-if="snackbar"
      class="fixed bottom-5 right-5 z-50 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-lg"
    >
      {{ snackbar }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";

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

const selectedAgency = computed(() => agencyOptions.value.find(agency => agency.id === form.agency_id) || null);

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
    showSnackbar("Admin global criado com sucesso.");
    resetForm();
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
