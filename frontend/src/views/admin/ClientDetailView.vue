<template>
  <div class="space-y-6">
    <section v-if="loading && !client" class="flex min-h-[60vh] items-center justify-center">
      <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
    </section>

    <template v-else-if="client">
      <section class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Cliente</p>
            <h1 class="mt-2 text-3xl font-bold text-slate-900">{{ client.name }}</h1>
            <div class="mt-3 flex flex-wrap gap-3 text-sm text-slate-500">
              <span>{{ formatCpf(client.cpf) || "CPF não informado" }}</span>
              <span>{{ formatPhone(client.phone) || "Telefone não informado" }}</span>
              <span>{{ client.email || "E-mail não informado" }}</span>
              <span>{{ client.city || "Cidade não informada" }}</span>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <a
              v-if="clientWhatsappLink"
              :href="clientWhatsappLink"
              target="_blank"
              rel="noopener"
              class="rounded-full border border-emerald-200 px-4 py-2 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
            >
              Chamar no WhatsApp
            </a>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              @click="editing = !editing"
            >
              {{ editing ? "Fechar edição" : "Editar" }}
            </button>
            <button
              type="button"
              class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
              @click="newOpportunityOpen = !newOpportunityOpen"
            >
              + Nova oportunidade
            </button>
          </div>
        </div>

        <div class="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Total de oportunidades</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ client.opportunitiesCount }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Abertas</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ client.openOpportunitiesCount }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Valores em aberto</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ formatCurrency(futureEstimatedValueCents) }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Valor já ganho</p>
            <p class="mt-2 text-2xl font-bold text-emerald-700">{{ formatCurrency(wonValueCents) }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Valor perdido</p>
            <p class="mt-2 text-2xl font-bold text-rose-700">{{ formatCurrency(lostValueCents) }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">Ultima interacao</p>
            <p class="mt-2 text-lg font-bold text-slate-900">{{ formatDateTime(lastInteractionAt) }}</p>
          </div>
        </div>
      </section>

      <section v-if="editing" class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-bold text-slate-900">Editar dados do cliente</h2>
        <div class="mt-4 grid gap-3 md:grid-cols-2">
          <input v-model="editForm.name" type="text" placeholder="Nome" class="crm-input md:col-span-2" />
          <input v-model="editForm.cpf" type="text" placeholder="CPF" class="crm-input" />
          <input v-model="editForm.phone" type="text" placeholder="Telefone" class="crm-input" />
          <input v-model="editForm.email" type="email" placeholder="E-mail" class="crm-input" />
          <input v-model="editForm.city" type="text" placeholder="Cidade" class="crm-input" />
          <input v-model="editForm.state" type="text" maxlength="2" placeholder="UF" class="crm-input" />
          <input v-model="editForm.zipcode" type="text" placeholder="CEP" class="crm-input" />
          <input v-model="editForm.street" type="text" placeholder="Logradouro" class="crm-input md:col-span-2" />
          <input v-model="editForm.number" type="text" placeholder="Numero" class="crm-input" />
          <input v-model="editForm.complement" type="text" placeholder="Complemento" class="crm-input" />
          <input v-model="editForm.neighborhood" type="text" placeholder="Bairro" class="crm-input md:col-span-2" />
          <input v-model="editForm.birthdate" type="date" class="crm-input" />
        </div>
        <textarea v-model="editForm.notes" rows="4" class="crm-input mt-3" placeholder="Observações"></textarea>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="resetEditForm">
            Cancelar
          </button>
          <button type="button" class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white" @click="handleUpdateClient">
            Salvar alterações
          </button>
        </div>
      </section>

      <section v-if="newOpportunityOpen" class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-bold text-slate-900">Nova oportunidade</h2>
        <div class="mt-4 grid gap-3 md:grid-cols-2">
          <input v-model="opportunityForm.opportunityName" type="text" placeholder="Nome da oportunidade" class="crm-input md:col-span-2" />
          <input v-model="opportunityForm.estimatedValue" type="text" placeholder="R$ 0,00" class="crm-input" />
          <select v-model="opportunityForm.statusId" class="crm-input">
            <option value="">Sem status</option>
            <option v-for="status in statuses" :key="status.id" :value="String(status.id)">{{ status.name }}</option>
          </select>
        </div>
        <textarea v-model="opportunityForm.internalNotes" rows="4" class="crm-input mt-3" placeholder="Observação inicial"></textarea>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" @click="newOpportunityOpen = false">
            Cancelar
          </button>
          <button type="button" class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white" @click="handleCreateOpportunity">
            Criar oportunidade
          </button>
        </div>
      </section>

      <section class="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex flex-wrap gap-2">
          <button v-for="tab in tabs" :key="tab.id" type="button" class="rounded-full px-4 py-2 text-sm font-semibold transition" :class="activeTab === tab.id ? 'bg-brand text-white' : 'border border-slate-200 text-slate-600 hover:bg-slate-50'" @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
        </div>

        <div v-if="activeTab === 'opportunities'" class="mt-5 space-y-3">
          <article
            v-for="opportunity in client.opportunities"
            :key="opportunity.id"
            class="rounded-2xl border border-slate-200 p-4"
          >
            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h3 class="text-base font-bold text-slate-900">{{ opportunity.opportunityName || opportunity.name || "Nova oportunidade" }}</h3>
                <p class="mt-2 text-sm text-slate-500">
                  Status: {{ opportunity.statusName || "Sem status" }} | Valor: {{ formatCurrency(opportunity.estimatedValueCents || 0) }}
                </p>
                <p v-if="opportunity.notes.length" class="mt-2 text-sm text-slate-600">
                  Última nota: {{ opportunity.notes[0]?.content }}
                </p>
              </div>
              <button
                type="button"
                class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                @click="openOpportunityModal(opportunity.id)"
              >
                Abrir oportunidade
              </button>
            </div>
          </article>
          <p v-if="!client.opportunities.length" class="text-sm text-slate-500">Nenhuma oportunidade vinculada.</p>
        </div>

        <div v-else-if="activeTab === 'notes'" class="mt-5">
          <div class="rounded-2xl border border-slate-200 p-4">
            <textarea v-model="newClientNote" rows="4" class="crm-input" placeholder="Adicionar nota do cliente"></textarea>
            <div class="mt-3 flex justify-end">
              <button type="button" class="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white" @click="handleCreateClientNote">
                Salvar nota
              </button>
            </div>
          </div>
          <div class="mt-4 space-y-3">
            <article v-for="note in client.notesTimeline" :key="note.id" class="rounded-2xl border border-slate-200 p-4">
              <p class="text-xs text-slate-400">{{ formatDateTime(note.created_at) }}{{ note.author?.name ? ` · ${note.author.name}` : "" }}</p>
              <p class="mt-2 whitespace-pre-wrap text-sm text-slate-700">{{ note.content }}</p>
            </article>
            <p v-if="!client.notesTimeline.length" class="text-sm text-slate-500">Nenhuma nota do cliente.</p>
          </div>
        </div>

        <div v-else-if="activeTab === 'documents'" class="mt-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="inline-flex rounded-full border border-slate-200 bg-slate-50 p-1">
              <button
                type="button"
                class="rounded-full px-3 py-1.5 text-xs font-semibold transition"
                :class="documentsViewMode === 'list' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                @click="documentsViewMode = 'list'"
              >
                Lista
              </button>
              <button
                type="button"
                class="rounded-full px-3 py-1.5 text-xs font-semibold transition"
                :class="documentsViewMode === 'grid' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                @click="documentsViewMode = 'grid'"
              >
                Grid
              </button>
            </div>
            <label class="inline-flex cursor-pointer items-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
              + Adicionar documento
              <input type="file" class="hidden" @change="handleClientDocumentInput" />
            </label>
          </div>
          <div
            v-if="documentsViewMode === 'grid'"
            class="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4"
          >
            <article
              v-for="document in client.documents"
              :key="document.id"
              class="overflow-hidden rounded-2xl border border-slate-200 bg-white"
            >
              <a
                :href="document.fileUrl"
                target="_blank"
                rel="noopener"
                class="flex aspect-[4/3] items-center justify-center overflow-hidden bg-slate-100"
              >
                <iframe
                  v-if="isPreviewablePdf(document)"
                  :src="buildPdfPreviewUrl(document.fileUrl)"
                  class="h-full w-full border-0"
                  loading="lazy"
                  title="Preview do documento"
                ></iframe>
                <img
                  v-else-if="isPreviewableImage(document)"
                  :src="document.fileUrl"
                  :alt="document.fileName"
                  class="h-full w-full object-cover"
                />
                <div v-else class="flex flex-col items-center justify-center gap-2 text-slate-400">
                  <svg viewBox="0 0 24 24" class="h-10 w-10" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M14 2v5h5" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                  <span class="rounded-full bg-white px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    {{ documentExtensionLabel(document.fileName) }}
                  </span>
                </div>
              </a>
              <div class="space-y-3 p-3">
                <div class="min-w-0">
                  <a :href="document.fileUrl" target="_blank" rel="noopener" class="block truncate text-sm font-semibold text-brand hover:underline">
                    {{ document.fileName }}
                  </a>
                  <p class="mt-1 text-xs text-slate-400">{{ document.sourceLabel || "Cliente" }}</p>
                </div>
                <button type="button" class="w-full rounded-full border border-rose-200 px-3 py-2 text-xs font-semibold text-rose-600 transition hover:bg-rose-50" @click="handleDeleteDocument(document.id)">
                  Remover
                </button>
              </div>
            </article>
            <p v-if="!client.documents.length" class="text-sm text-slate-500 md:col-span-2 xl:col-span-4">Nenhum documento dispon?vel.</p>
          </div>
          <div v-else class="mt-4 space-y-3">
            <article v-for="document in client.documents" :key="document.id" class="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 p-4">
              <div class="flex min-w-0 items-center gap-3">
                <div class="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-slate-100">
                  <iframe
                    v-if="isPreviewablePdf(document)"
                    :src="buildPdfPreviewUrl(document.fileUrl)"
                    class="h-full w-full border-0"
                    loading="lazy"
                    title="Preview do documento"
                  ></iframe>
                  <img
                    v-else-if="isPreviewableImage(document)"
                    :src="document.fileUrl"
                    :alt="document.fileName"
                    class="h-full w-full object-cover"
                  />
                  <span v-else class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    {{ documentExtensionLabel(document.fileName) }}
                  </span>
                </div>
                <div class="min-w-0">
                  <a :href="document.fileUrl" target="_blank" rel="noopener" class="block truncate text-sm font-semibold text-brand hover:underline">
                    {{ document.fileName }}
                  </a>
                  <p class="mt-1 text-xs text-slate-400">{{ document.sourceLabel || "Cliente" }}</p>
                </div>
              </div>
              <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50" @click="handleDeleteDocument(document.id)">
                Remover
              </button>
            </article>
            <p v-if="!client.documents.length" class="text-sm text-slate-500">Nenhum documento dispon?vel.</p>
          </div>
        </div>

        <div v-else class="mt-5 rounded-2xl border border-slate-200 p-4 text-sm text-slate-600">
          <p><strong>Nome:</strong> {{ client.name }}</p>
          <p class="mt-2"><strong>CPF:</strong> {{ formatCpf(client.cpf) || "-" }}</p>
          <p class="mt-2"><strong>Telefone:</strong> {{ formatPhone(client.phone) || "-" }}</p>
          <p class="mt-2"><strong>E-mail:</strong> {{ client.email || "-" }}</p>
          <p class="mt-2"><strong>Cidade:</strong> {{ client.city || "-" }}</p>
          <p class="mt-2"><strong>CEP:</strong> {{ client.zipcode || "-" }}</p>
          <p class="mt-2"><strong>Logradouro:</strong> {{ client.street || "-" }}</p>
          <p class="mt-2"><strong>Numero:</strong> {{ client.number || "-" }}</p>
          <p class="mt-2"><strong>Complemento:</strong> {{ client.complement || "-" }}</p>
          <p class="mt-2"><strong>Bairro:</strong> {{ client.neighborhood || "-" }}</p>
          <p class="mt-2"><strong>UF:</strong> {{ client.state || "-" }}</p>
          <p class="mt-2"><strong>Nascimento:</strong> {{ client.birthdate ? formatDateTime(client.birthdate) : "-" }}</p>
          <p class="mt-2 whitespace-pre-wrap"><strong>Observações:</strong> {{ client.notes || "-" }}</p>
        </div>
      </section>

      <OpportunityDrawer
        v-model="isOpportunityModalOpen"
        :contact-id="selectedOpportunityId"
        :statuses="statuses"
        mode="modal"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import OpportunityDrawer from "../../components/admin/leads/OpportunityDrawer.vue";
import { useLeadCaptureStore } from "../../store/useLeadCaptureStore";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";

const route = useRoute();
const leadStore = useLeadCaptureStore();

const client = computed(() => leadStore.clientDetail);
const loading = computed(() => leadStore.clientDetailLoading);
const statuses = computed(() => leadStore.statuses);

const tabs = [
  { id: "opportunities", label: "Oportunidades" },
  { id: "notes", label: "Notas" },
  { id: "documents", label: "Documentos" },
  { id: "data", label: "Dados do cliente" }
] as const;

const activeTab = ref<(typeof tabs)[number]["id"]>("opportunities");
const documentsViewMode = ref<"list" | "grid">("list");
const editing = ref(false);
const newOpportunityOpen = ref(false);
const newClientNote = ref("");
const isOpportunityModalOpen = ref(false);
const selectedOpportunityId = ref<number | null>(null);
const editForm = reactive({
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
const opportunityForm = reactive({
  opportunityName: "",
  estimatedValue: "",
  statusId: "",
  internalNotes: ""
});

const clientId = computed(() => Number(route.params.id));
const lastInteractionAt = computed(() => {
  const noteDate = client.value?.notesTimeline?.[0]?.created_at || null;
  const opportunityDate = client.value?.lastOpportunityAt || null;
  return noteDate || opportunityDate;
});
const futureEstimatedValueCents = computed(() =>
  (client.value?.opportunities || []).reduce((total, opportunity) => {
    if (opportunity.closedAt) return total;
    return total + (opportunity.estimatedValueCents || 0);
  }, 0)
);
const wonValueCents = computed(() =>
  (client.value?.opportunities || []).reduce((total, opportunity) => {
    if (opportunity.closeOutcome !== "won") return total;
    return total + (opportunity.estimatedValueCents || 0);
  }, 0)
);
const lostValueCents = computed(() =>
  (client.value?.opportunities || []).reduce((total, opportunity) => {
    if (opportunity.closeOutcome !== "lost") return total;
    return total + (opportunity.estimatedValueCents || 0);
  }, 0)
);
const clientWhatsappLink = computed(() => {
  const digits = normalizeWhatsappDigits(client.value?.phone || "");
  return digits ? `https://wa.me/${digits}` : "";
});

const load = async () => {
  if (!clientId.value) return;
  await Promise.all([leadStore.fetchClientDetail(clientId.value), leadStore.fetchStatuses()]);
  resetEditForm();
};

const resetEditForm = () => {
  editForm.name = client.value?.name || "";
  editForm.cpf = client.value?.cpf || "";
  editForm.phone = client.value?.phone || "";
  editForm.email = client.value?.email || "";
  editForm.city = client.value?.city || "";
  editForm.zipcode = client.value?.zipcode || "";
  editForm.street = client.value?.street || "";
  editForm.number = client.value?.number || "";
  editForm.complement = client.value?.complement || "";
  editForm.neighborhood = client.value?.neighborhood || "";
  editForm.state = client.value?.state || "";
  editForm.birthdate = client.value?.birthdate || "";
  editForm.notes = client.value?.notes || "";
  editing.value = false;
};

const handleUpdateClient = async () => {
  if (!clientId.value) return;
  try {
    await leadStore.updateClient(clientId.value, {
      name: editForm.name.trim() || undefined,
      cpf: editForm.cpf.trim() || null,
      phone: editForm.phone.trim() || null,
      email: editForm.email.trim() || null,
      city: editForm.city.trim() || null,
      zipcode: editForm.zipcode.trim() || null,
      street: editForm.street.trim() || null,
      number: editForm.number.trim() || null,
      complement: editForm.complement.trim() || null,
      neighborhood: editForm.neighborhood.trim() || null,
      state: editForm.state.trim().toUpperCase() || null,
      birthdate: editForm.birthdate || null,
      notes: editForm.notes.trim() || null
    });
    await leadStore.fetchClientDetail(clientId.value);
    resetEditForm();
  } catch (error) {
    console.error(error);
  }
};

const handleCreateOpportunity = async () => {
  if (!clientId.value || !opportunityForm.opportunityName.trim()) return;
  try {
    await leadStore.createOpportunityFromClient(clientId.value, {
      opportunityName: opportunityForm.opportunityName.trim(),
      estimatedValueCents: inputToCents(opportunityForm.estimatedValue),
      statusId: opportunityForm.statusId ? Number(opportunityForm.statusId) : null,
      internalNotes: opportunityForm.internalNotes.trim() || null
    });
    opportunityForm.opportunityName = "";
    opportunityForm.estimatedValue = "";
    opportunityForm.statusId = "";
    opportunityForm.internalNotes = "";
    newOpportunityOpen.value = false;
  } catch (error) {
    console.error(error);
  }
};

const handleCreateClientNote = async () => {
  if (!clientId.value || !newClientNote.value.trim()) return;
  try {
    await leadStore.createClientNote(clientId.value, newClientNote.value.trim());
    newClientNote.value = "";
  } catch (error) {
    console.error(error);
  }
};

const handleClientDocumentInput = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!clientId.value || !file) return;
  try {
    await leadStore.uploadClientDocument(clientId.value, file);
  } catch (error) {
    console.error(error);
  } finally {
    input.value = "";
  }
};

const handleDeleteDocument = async (documentId: number) => {
  if (!window.confirm("Remover este documento?")) return;
  try {
    await leadStore.deleteDocument(documentId);
    await leadStore.fetchClientDetail(clientId.value);
  } catch (error) {
    console.error(error);
  }
};

const openOpportunityModal = (opportunityId: number) => {
  selectedOpportunityId.value = opportunityId;
  isOpportunityModalOpen.value = true;
};

watch(
  () => route.params.id,
  () => {
    load().catch(error => console.error(error));
  },
  { immediate: true }
);

watch(isOpportunityModalOpen, value => {
  if (!value) {
    load().catch(error => console.error(error));
  }
});

function inputToCents(value: string) {
  const digits = value.replace(/\D/g, "");
  if (!digits) return null;
  return Number(digits);
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format((value || 0) / 100);
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: value.includes("T") ? "short" : undefined
  }).format(date);
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
function isPreviewableImage(document: { fileType?: string | null; fileName: string }) {
  const fileType = (document.fileType || "").toLowerCase();
  if (fileType.startsWith("image/")) return true;
  const fileName = document.fileName.toLowerCase();
  return [".png", ".jpg", ".jpeg", ".webp", ".gif"].some(extension => fileName.endsWith(extension));
}

function isPreviewablePdf(document: { fileType?: string | null; fileName: string }) {
  const fileType = (document.fileType || "").toLowerCase();
  if (fileType === "application/pdf") return true;
  return document.fileName.toLowerCase().endsWith(".pdf");
}

function buildPdfPreviewUrl(fileUrl: string) {
  return `${fileUrl}#toolbar=0&navpanes=0&scrollbar=0&view=FitH`;
}

function documentExtensionLabel(fileName: string) {
  const extension = fileName.split(".").pop()?.trim().toUpperCase();
  return extension || "ARQ";
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
