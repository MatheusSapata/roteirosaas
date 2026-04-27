<template>
  <div class="space-y-6">
    <section class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Clientes</p>
          <h1 class="mt-2 text-3xl font-bold text-slate-900">Base de clientes</h1>
          <p class="mt-2 text-sm text-slate-500">
            Histórico comercial consolidado da agência.
          </p>
        </div>
        <button
          type="button"
          class="rounded-full bg-brand px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-dark"
          @click="openCreateModal"
        >
          + Novo cliente
        </button>
      </div>

      <div class="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <input v-model="filters.q" type="text" placeholder="Buscar cliente, CPF, telefone ou e-mail..." class="crm-input xl:col-span-2" />
        <input v-model="filters.city" type="text" placeholder="Cidade" class="crm-input" />
        <input v-model="filters.createdFrom" type="date" class="crm-input" />
        <input v-model="filters.createdTo" type="date" class="crm-input" />
      </div>

      <div class="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full border px-4 py-2 text-sm font-semibold transition"
          :class="filters.hasOpenOpportunities ? 'border-brand bg-brand/10 text-brand' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
          @click="toggleOpenOpportunities"
        >
          Com oportunidades abertas
        </button>
        <button
          type="button"
          class="rounded-full border px-4 py-2 text-sm font-semibold transition"
          :class="filters.withoutOpportunities ? 'border-brand bg-brand/10 text-brand' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
          @click="toggleWithoutOpportunities"
        >
          Sem oportunidades
        </button>
      </div>
    </section>

    <section class="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm">
      <div v-if="loading" class="flex min-h-[260px] items-center justify-center">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th class="px-4 py-3">Nome</th>
              <th class="px-4 py-3">CPF</th>
              <th class="px-4 py-3">Telefone</th>
              <th class="px-4 py-3">E-mail</th>
              <th class="px-4 py-3">Cidade</th>
              <th class="px-4 py-3">Oportunidades</th>
              <th class="px-4 py-3">Total</th>
              <th class="px-4 py-3">Última oportunidade</th>
              <th class="px-4 py-3">Criado em</th>
              <th class="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200">
            <tr
              v-for="client in clients"
              :key="client.id"
              class="cursor-pointer text-slate-700 transition hover:bg-slate-50"
              @click="goToClient(client.id)"
            >
              <td class="px-4 py-3 font-semibold text-slate-900">{{ client.name }}</td>
              <td class="px-4 py-3">{{ formatCpf(client.cpf) || "-" }}</td>
              <td class="px-4 py-3">{{ formatPhone(client.phone) || "-" }}</td>
              <td class="px-4 py-3">{{ client.email || "-" }}</td>
              <td class="px-4 py-3">{{ client.city || "-" }}</td>
              <td class="px-4 py-3">{{ client.opportunitiesCount }}</td>
              <td class="px-4 py-3">{{ formatCurrency(client.totalEstimatedValueCents) }}</td>
              <td class="px-4 py-3">{{ formatDate(client.lastOpportunityAt) }}</td>
              <td class="px-4 py-3">{{ formatDate(client.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <button
                  type="button"
                  class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                  @click.stop="goToClient(client.id)"
                >
                  Ver
                </button>
              </td>
            </tr>
            <tr v-if="!clients.length">
              <td colspan="10" class="px-4 py-10 text-center text-sm text-slate-500">
                Nenhum cliente encontrado.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="createModalOpen" class="fixed inset-0 z-[150] flex items-center justify-center bg-slate-900/45 px-4">
        <div class="w-full max-w-2xl rounded-[28px] bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4">
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
          <div class="mt-5 grid gap-3 md:grid-cols-2">
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
          <textarea
            v-model="createForm.notes"
            rows="4"
            placeholder="Observações"
            class="crm-input mt-3"
          ></textarea>
          <div class="mt-5 flex justify-end gap-2">
            <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="closeCreateModal">
              Cancelar
            </button>
            <button
              type="button"
              class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
              :disabled="creating"
              @click="handleCreateClient"
            >
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

const router = useRouter();
const leadStore = useLeadCaptureStore();

const clients = computed(() => leadStore.clients);
const loading = computed(() => leadStore.clientsLoading);

const filters = reactive({
  q: "",
  city: "",
  hasOpenOpportunities: false,
  withoutOpportunities: false,
  createdFrom: "",
  createdTo: ""
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
  await leadStore.fetchClients({
    q: filters.q.trim() || undefined,
    city: filters.city.trim() || undefined,
    hasOpenOpportunities: filters.hasOpenOpportunities || undefined,
    withoutOpportunities: filters.withoutOpportunities || undefined,
    createdFrom: filters.createdFrom || undefined,
    createdTo: filters.createdTo || undefined
  });
};

const goToClient = (clientId: number) => {
  router.push(`/admin/leads/clients/${clientId}`);
};

const openCreateModal = () => {
  createModalOpen.value = true;
};

const closeCreateModal = () => {
  createModalOpen.value = false;
  createForm.name = "";
  createForm.cpf = "";
  createForm.phone = "";
  createForm.email = "";
  createForm.city = "";
  createForm.zipcode = "";
  createForm.street = "";
  createForm.number = "";
  createForm.complement = "";
  createForm.neighborhood = "";
  createForm.state = "";
  createForm.birthdate = "";
  createForm.notes = "";
};

const handleCreateClient = async () => {
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
  } catch (error) {
    console.error(error);
  } finally {
    creating.value = false;
  }
};

const toggleOpenOpportunities = () => {
  filters.hasOpenOpportunities = !filters.hasOpenOpportunities;
  if (filters.hasOpenOpportunities) {
    filters.withoutOpportunities = false;
  }
};

const toggleWithoutOpportunities = () => {
  filters.withoutOpportunities = !filters.withoutOpportunities;
  if (filters.withoutOpportunities) {
    filters.hasOpenOpportunities = false;
  }
};

watch(
  () => ({ ...filters }),
  () => {
    window.clearTimeout((loadClients as any)._debounce);
    (loadClients as any)._debounce = window.setTimeout(() => {
      loadClients().catch(error => console.error(error));
    }, 320);
  },
  { deep: true, immediate: true }
);

function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format((value || 0) / 100);
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(date);
}

function formatPhone(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length === 13 && digits.startsWith("55")) return `+55 (${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9, 13)}`;
  if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
  if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6, 10)}`;
  return value || "";
}

function formatCpf(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length !== 11) return value || "";
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9, 11)}`;
}
</script>

<style scoped>
.crm-input {
  width: 100%;
  border-radius: 1rem;
  border: 1px solid rgb(226 232 240);
  padding: 0.75rem 0.875rem;
  font-size: 0.875rem;
  color: rgb(15 23 42);
  outline: none;
}

.crm-input:focus {
  border-color: var(--color-brand, #22c55e);
  box-shadow: 0 0 0 2px rgb(34 197 94 / 0.15);
}
</style>
