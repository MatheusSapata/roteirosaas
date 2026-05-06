<template>
  <div class="det-page">
    <section v-if="loading && !client" class="flex min-h-[60vh] items-center justify-center">
      <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
    </section>

    <template v-else-if="client">
      <button type="button" class="det-back-btn" @click="goBack">
        <svg class="det-back-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m15 18-6-6 6-6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
        Clientes
      </button>

      <section class="det-card">
        <div class="det-hd-top">
          <div class="det-hd-inner">
            <div class="det-hd-left">
              <div class="det-avatar">{{ clientInitial }}</div>
              <div class="det-name-block">
                <p class="det-eyebrow">Cliente</p>
                <h1 class="det-name">{{ client.name }}</h1>
                <div class="det-meta">
                  <span class="det-meta-item val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.12.9.33 1.77.63 2.61a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.47-1.2a2 2 0 0 1 2.11-.45c.84.3 1.71.51 2.61.63A2 2 0 0 1 22 16.92z" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>{{ formatPhone(client.phone) || "Telefone nao informado" }}</span>
                  <span class="det-meta-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 4h16a2 2 0 0 1 2 2v.01L12 13 2 6.01V6a2 2 0 0 1 2-2Z" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 8v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>{{ client.email || "E-mail nao informado" }}</span>
                  <span class="det-meta-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 1 1 18 0Z" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="10" r="3" stroke-width="1.9"/></svg>{{ client.city || "Cidade nao informada" }}</span>
                  <span class="det-meta-item">Cliente desde <strong>{{ clientSinceLabel }}</strong></span>
                </div>
              </div>
            </div>
            <div class="det-hd-actions">
              <a v-if="clientWhatsappLink" :href="clientWhatsappLink" target="_blank" rel="noopener" class="btn btn-p btn-wpp">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M16.75 13.96c-.25-.13-1.47-.72-1.7-.8-.23-.08-.4-.12-.57.12-.17.25-.65.8-.8.96-.14.17-.3.19-.55.06-.25-.13-1.06-.39-2.02-1.23-.74-.66-1.25-1.47-1.4-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.3.37-.45.12-.14.17-.25.25-.42.08-.17.04-.31-.02-.45-.06-.14-.57-1.37-.78-1.87-.2-.49-.41-.42-.57-.43h-.48c-.17 0-.45.06-.68.31-.23.25-.88.86-.88 2.1s.9 2.43 1.02 2.6c.12.17 1.76 2.69 4.25 3.77.59.26 1.06.42 1.42.54.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.17.21-.57.21-1.06.15-1.17-.06-.11-.23-.17-.48-.3Z" />
                  <path d="M12.04 2C6.77 2 2.5 6.26 2.5 11.52c0 1.85.53 3.65 1.52 5.2L2.4 21.5l4.9-1.57c1.43.78 3.04 1.2 4.7 1.2h.04c5.26 0 9.53-4.26 9.53-9.52C21.57 6.26 17.3 2 12.04 2Zm0 17.42h-.03c-1.5 0-2.97-.4-4.25-1.16l-.3-.18-2.9.93.95-2.82-.2-.29a7.83 7.83 0 0 1-1.2-4.18c0-4.3 3.5-7.8 7.82-7.8 2.08 0 4.03.8 5.5 2.28a7.75 7.75 0 0 1 2.29 5.5c0 4.3-3.5 7.8-7.8 7.8Z" />
                </svg>
                <span class="btn-wpp-label">WhatsApp</span>
              </a>
              <button type="button" class="btn btn-o" @click="editing = !editing">{{ editing ? "Fechar edicao" : "Editar" }}</button>
              <button type="button" class="btn btn-p" @click="newOpportunityOpen = !newOpportunityOpen">+ Nova oportunidade</button>
            </div>
          </div>
        </div>

        <div class="det-stats-inner">
          <div class="ds"><span class="ds-icon ds-icon--violet"><svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v3h3"/></svg></span><p class="ds-lbl">Total de oportunidades</p><p class="ds-val">{{ client.opportunitiesCount }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--amber"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg></span><p class="ds-lbl">Abertas</p><p class="ds-val">{{ client.openOpportunitiesCount }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--blue"><svg viewBox="0 0 24 24"><path d="M12 2v20"/><path d="M17 6H9.5a3.5 3.5 0 0 0 0 7H14.5a3.5 3.5 0 0 1 0 7H6"/></svg></span><p class="ds-lbl">Valores em aberto</p><p class="ds-val">{{ formatCurrency(futureEstimatedValueCents) }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--green"><svg viewBox="0 0 24 24"><path d="M4 14l5-5 4 4 7-7"/><path d="M15 6h5v5"/></svg></span><p class="ds-lbl">Valor ja ganho</p><p class="ds-val g">{{ formatCurrency(wonValueCents) }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--red"><svg viewBox="0 0 24 24"><path d="M4 10l5 5 4-4 7 7"/><path d="M15 18h5v-5"/></svg></span><p class="ds-lbl">Valor perdido</p><p class="ds-val r">{{ formatCurrency(lostValueCents) }}</p></div>
          <div class="ds"><span class="ds-icon ds-icon--purple"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l2 2"/></svg></span><p class="ds-lbl">Ultima interacao</p><p class="ds-val ds-time">{{ formatDateTime(lastInteractionAt) }}</p></div>
        </div>

        <div class="det-tabs">
          <button v-for="tab in tabs" :key="tab.id" type="button" class="tab-btn" :class="{ on: activeTab === tab.id }" @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
        </div>

        <div class="det-body">
          <section v-if="editing" class="dados-block">
            <div class="dados-block-head">
              <p class="dados-block-eye">Editar cliente</p>
              <h2 class="dados-block-title">Dados do cliente</h2>
            </div>
            <div class="dados-grid2">
              <input v-model="editForm.name" type="text" placeholder="Nome" class="crm-input full" />
              <input v-model="editForm.cpf" type="text" placeholder="CPF" class="crm-input" />
              <input v-model="editForm.phone" type="text" placeholder="Telefone" class="crm-input" />
              <input v-model="editForm.email" type="email" placeholder="E-mail" class="crm-input" />
              <input v-model="editForm.city" type="text" placeholder="Cidade" class="crm-input" />
              <input v-model="editForm.state" type="text" maxlength="2" placeholder="UF" class="crm-input" />
              <input v-model="editForm.zipcode" type="text" placeholder="CEP" class="crm-input" />
              <input v-model="editForm.street" type="text" placeholder="Logradouro" class="crm-input full" />
              <input v-model="editForm.number" type="text" placeholder="Numero" class="crm-input" />
              <input v-model="editForm.complement" type="text" placeholder="Complemento" class="crm-input" />
              <input v-model="editForm.neighborhood" type="text" placeholder="Bairro" class="crm-input full" />
              <input v-model="editForm.birthdate" type="date" class="crm-input" />
              <textarea v-model="editForm.notes" rows="4" class="crm-input full" placeholder="Observacoes"></textarea>
            </div>
            <div class="det-actions-row">
              <button type="button" class="btn btn-o" @click="resetEditForm">Cancelar</button>
              <button type="button" class="btn btn-p" @click="handleUpdateClient">Salvar alteracoes</button>
            </div>
          </section>

          <section v-if="newOpportunityOpen" class="dados-block">
            <div class="dados-block-head">
              <p class="dados-block-eye">Nova oportunidade</p>
              <h2 class="dados-block-title">Cadastrar oportunidade</h2>
            </div>
            <div class="dados-grid2">
              <input v-model="opportunityForm.opportunityName" type="text" placeholder="Nome da oportunidade" class="crm-input full" />
              <input v-model="opportunityForm.estimatedValue" type="text" placeholder="R$ 0,00" class="crm-input" />
              <select v-model="opportunityForm.statusId" class="crm-input">
                <option value="">Sem status</option>
                <option v-for="status in statuses" :key="status.id" :value="String(status.id)">{{ status.name }}</option>
              </select>
              <textarea v-model="opportunityForm.internalNotes" rows="4" class="crm-input full" placeholder="Observacao inicial"></textarea>
            </div>
            <div class="det-actions-row">
              <button type="button" class="btn btn-o" @click="newOpportunityOpen = false">Cancelar</button>
              <button type="button" class="btn btn-p" @click="handleCreateOpportunity">Criar oportunidade</button>
            </div>
          </section>

          <div v-if="activeTab === 'opportunities'" class="space-y-3">
            <article v-for="opportunity in client.opportunities" :key="opportunity.id" class="opp-item">
              <div>
                <h3 class="opp-item-name">{{ opportunity.opportunityName || opportunity.name || "Nova oportunidade" }}</h3>
                <p class="opp-item-meta">Status: {{ opportunity.statusName || "Sem status" }} | Valor: {{ formatCurrency(opportunity.estimatedValueCents || 0) }}</p>
              </div>
              <button type="button" class="btn btn-o btn-sm" @click="openOpportunityModal(opportunity.id)">Abrir oportunidade</button>
            </article>
            <p v-if="!client.opportunities.length" class="text-sm text-slate-500">Nenhuma oportunidade vinculada.</p>
          </div>

          <div v-else-if="activeTab === 'notes'" class="space-y-3">
            <div class="rounded-2xl border border-slate-200 p-4">
              <textarea v-model="newClientNote" rows="4" class="crm-input" placeholder="Adicionar nota do cliente"></textarea>
              <div class="mt-3 flex justify-end">
                <button type="button" class="btn btn-p" @click="handleCreateClientNote">Salvar nota</button>
              </div>
            </div>
            <article v-for="note in client.notesTimeline" :key="note.id" class="rounded-2xl border border-slate-200 p-4">
              <p class="text-xs text-slate-400">{{ formatDateTime(note.created_at) }}{{ note.author?.name ? ` · ${note.author.name}` : "" }}</p>
              <p class="mt-2 whitespace-pre-wrap text-sm text-slate-700">{{ note.content }}</p>
            </article>
            <p v-if="!client.notesTimeline.length" class="text-sm text-slate-500">Nenhuma nota do cliente.</p>
          </div>

          <div v-else-if="activeTab === 'documents'" class="docs-tab-wrap">
            <div v-if="!client.documents.length" class="docs-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 2v5h5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <p>Nenhum documento anexado ainda.</p>
              <label class="btn btn-o btn-sm">
                + Adicionar documento
                <input type="file" class="hidden" @change="handleClientDocumentInput" />
              </label>
            </div>
            <div v-else class="space-y-3">
              <article v-for="document in client.documents" :key="document.id" class="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 p-4">
                <div class="min-w-0">
                  <a :href="document.fileUrl" target="_blank" rel="noopener" class="block truncate text-sm font-semibold text-brand hover:underline">{{ document.fileName }}</a>
                  <p class="mt-1 text-xs text-slate-400">{{ document.sourceLabel || "Cliente" }}</p>
                </div>
                <button type="button" class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50" @click="handleDeleteDocument(document.id)">Remover</button>
              </article>
            </div>
          </div>

          <div v-else class="space-y-3">
            <section class="dados-block">
              <div class="dados-block-head"><p class="dados-block-eye">Identificacao</p><h2 class="dados-block-title">Dados pessoais</h2></div>
              <div class="dados-grid2">
                <input v-model="editForm.name" type="text" placeholder="Nome completo" class="crm-input" />
                <input v-model="editForm.cpf" type="text" placeholder="000.000.000-00" class="crm-input" />
                <input v-model="editForm.birthdate" type="date" class="crm-input" />
                <input :value="clientSinceLabel" type="text" disabled class="crm-input" />
              </div>
            </section>
            <section class="dados-block">
              <div class="dados-block-head"><p class="dados-block-eye">Contato</p><h2 class="dados-block-title">Formas de contato</h2></div>
              <div class="dados-grid2">
                <input v-model="editForm.phone" type="text" placeholder="Telefone / WhatsApp" class="crm-input" />
                <input v-model="editForm.email" type="email" placeholder="email@exemplo.com" class="crm-input" />
              </div>
            </section>
            <section class="dados-block">
              <div class="dados-block-head"><p class="dados-block-eye">Localizacao</p><h2 class="dados-block-title">Endereco</h2></div>
              <div class="dados-grid2">
                <input v-model="editForm.city" type="text" placeholder="Cidade" class="crm-input" />
                <input v-model="editForm.state" type="text" placeholder="Estado (UF)" class="crm-input" />
              </div>
            </section>
            <div class="det-actions-row det-actions-row--left">
              <button type="button" class="btn btn-p" @click="handleUpdateClient">Salvar alteracoes</button>
              <span class="text-xs text-slate-500">Alteracoes refletidas em todas as oportunidades deste cliente.</span>
            </div>
          </div>
        </div>
      </section>

      <OpportunityDrawer v-model="isOpportunityModalOpen" :contact-id="selectedOpportunityId" :statuses="statuses" mode="modal" />
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
const clientInitial = computed(() => (client.value?.name?.trim()?.charAt(0) || "C").toUpperCase());
const clientSinceLabel = computed(() => {
  const raw = (client.value as any)?.createdAt || (client.value as any)?.created_at || null;
  return formatDateOnly(raw) || "-";
});
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

const goBack = () => {
  window.history.back();
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

function formatDateOnly(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(date);
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

</script>

<style scoped>
.det-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.det-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 9px;
  background: #f5f7f5;
  border: 1.5px solid #e4e9e4;
  font-size: 12px;
  font-weight: 600;
  color: #4a5e4a;
}
.det-back-ic {
  width: 13px;
  height: 13px;
}

.det-card {
  background: #fff;
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.det-hd-top {
  padding: 16px 20px;
  border-bottom: 1.5px solid #e4e9e4;
}

.det-hd-inner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.det-hd-left {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.det-avatar {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: #2fb752;
  color: #fff;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.det-eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  color: #8a9e8a;
  letter-spacing: 0.08em;
}

.det-name {
  font-size: 22px;
  line-height: 1.15;
  font-weight: 800;
  color: #111a14;
}

.det-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  color: #8a9e8a;
  font-size: 13px;
}

.det-meta-item.val {
  color: #4a5e4a;
}
.det-meta-item svg {
  width: 13px;
  height: 13px;
  opacity: 0.75;
  flex-shrink: 0;
}

.det-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  line-height: 1;
}

.det-hd-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  border: 1.5px solid transparent;
  transition: all 0.15s ease;
}

.btn-p {
  background: #3dcc5f;
  color: #0f1f14;
  border-color: #3dcc5f;
}
.btn-p:hover {
  background: #2ead4c;
  border-color: #2ead4c;
}

.btn-o {
  background: #fff;
  color: #4a5e4a;
  border-color: #d7e1d7;
}
.btn-o:hover {
  border-color: #c7d4c7;
  color: #111a14;
  background: #f7faf7;
}

.btn-sm {
  padding: 8px 12px;
}

.btn-wpp {
  background: #25d366;
  border-color: #25d366;
  color: #fff;
}
.btn-wpp:hover {
  background: #22c55e;
  border-color: #22c55e;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.28);
}
.btn-wpp svg {
  width: 13px;
  height: 13px;
  margin-right: 2px;
  color: #fff;
}

.btn-wpp:hover .btn-wpp-label {
  color: #0f1f14;
}

.det-stats-inner {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1.5px solid #e4e9e4;
}

.ds {
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  padding: 12px 14px;
  background: #fff;
}
.ds-icon {
  display: inline-flex;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  margin-bottom: 8px;
  align-items: center;
  justify-content: center;
}
.ds-icon svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ds-icon--violet { background: rgba(99, 102, 241, 0.16); color: #6366f1; }
.ds-icon--amber { background: rgba(245, 158, 11, 0.16); color: #d97706; }
.ds-icon--blue { background: rgba(59, 130, 246, 0.16); color: #2563eb; }
.ds-icon--green { background: rgba(34, 197, 94, 0.16); color: #16a34a; }
.ds-icon--red { background: rgba(239, 68, 68, 0.16); color: #dc2626; }
.ds-icon--purple { background: rgba(139, 92, 246, 0.16); color: #7c3aed; }

.ds-lbl {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #8a9e8a;
}

.ds-val {
  margin-top: 4px;
  font-size: 18px;
  line-height: 1;
  font-weight: 800;
  color: #111a14;
}

.ds-val.g {
  color: #1a7a35;
}

.ds-val.r {
  color: #c0392b;
}

.ds-time {
  font-size: 16px;
}

.det-tabs {
  display: flex;
  gap: 0;
  padding: 0 20px;
  border-bottom: 1.5px solid #e4e9e4;
}

.tab-btn {
  border: none;
  background: transparent;
  padding: 12px 16px;
  margin-bottom: -1px;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 600;
  color: #8a9e8a;
}

.tab-btn.on {
  color: #2ead4c;
  border-bottom-color: #2ead4c;
}

.det-body {
  padding: 20px;
}

.opp-item {
  background: #fff;
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}
.opp-item:hover {
  border-color: #cdd8cd;
  background: #fafcfa;
}

.opp-item-name {
  font-size: 14px;
  font-weight: 700;
  color: #111a14;
}

.opp-item-meta {
  margin-top: 4px;
  color: #8a9e8a;
  font-size: 13px;
}

.dados-block {
  border: 1.5px solid #e4e9e4;
  border-radius: 12px;
  margin-bottom: 14px;
  overflow: hidden;
}

.dados-block-head {
  padding: 14px 18px;
  border-bottom: 1.5px solid #e4e9e4;
}

.dados-block-eye {
  font-size: 11px;
  text-transform: uppercase;
  color: #8a9e8a;
  font-weight: 700;
}

.dados-block-title {
  font-size: 16px;
  font-weight: 700;
  color: #111a14;
}

.dados-grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px;
}

.crm-input {
  width: 100%;
  border-radius: 10px;
  border: 1.5px solid #d8e1d8;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
}

.crm-input.full {
  grid-column: 1 / -1;
}

.det-actions-row {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 16px 16px;
}

.det-actions-row--left {
  justify-content: flex-start;
  align-items: center;
}

.docs-tab-wrap {
  min-height: 240px;
}

.docs-empty {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #8a9e8a;
}

.docs-empty svg {
  width: 34px;
  height: 34px;
}

@media (max-width: 1100px) {
  .det-stats-inner {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .det-name {
    font-size: 20px;
  }

  .ds-val {
    font-size: 16px;
  }

  .opp-item-name {
    font-size: 13px;
  }

  .opp-item-meta {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .dados-grid2 {
    grid-template-columns: 1fr;
  }

  .det-stats-inner {
    grid-template-columns: 1fr 1fr;
  }

  .det-body {
    padding: 14px;
  }

  .det-tabs {
    padding: 0 8px;
    overflow-x: auto;
  }

  .tab-btn {
    white-space: nowrap;
  }
}
</style>
