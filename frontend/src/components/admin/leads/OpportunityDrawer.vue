<template>
  <Teleport to="body">
    <transition name="crm-drawer-fade">
      <div v-if="modelValue" class="fixed inset-0 z-[400]">
        <div class="absolute inset-0 bg-[rgba(17,26,20,.44)]" @click="close"></div>
        <transition :name="isModalMode ? 'crm-modal-scale' : 'crm-drawer-slide'">
          <aside
            v-if="modelValue"
            class="opp-dr absolute flex flex-col overflow-hidden shadow-2xl"
            :class="
              isModalMode
                ? 'inset-x-4 top-6 bottom-6 mx-auto w-auto max-w-[1120px] rounded-[32px] border border-slate-200 bg-white md:inset-x-8'
                : 'opp-drawer-shell inset-y-0 right-0 h-full w-full max-w-[660px] bg-white'
            "
          >
            <div class="opp-hd flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-3">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Oportunidade</p>
              </div>
              <button
                type="button"
                class="opp-x rounded-[8px] border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
                @click="close"
              >
                <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </div>

            <div v-if="loading && !details" class="flex flex-1 items-center justify-center">
              <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
            </div>

            <div v-else class="opp-body flex-1 overflow-y-auto">
              <div class="opp-head-content">
                <h2 class="opp-name truncate">
                  {{ headerTitle }}
                </h2>
                <div class="opp-origin-row">
                  <span class="opp-chip page">
                    <svg viewBox="0 0 24 24"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5"/></svg>
                    {{ details?.pageTitle || details?.pageSlug || "Página" }}
                  </span>
                  <span class="opp-chip form">
                    <svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    {{ details?.formName || "Formulário" }}
                  </span>
                  <span class="opp-date">· {{ formatDateTime(details?.created_at || null) }}</span>
                </div>
                <div class="opp-meta-row">
                  <span class="opp-stage" :style="statusBadgeStyle">{{ details?.statusName || "Sem etapa" }}</span>
                  <span class="opp-status" :class="opportunityStatusBadgeClass">{{ opportunityStatusLabel }}</span>
                  <span class="opp-value">Valor: <strong>{{ currencyLabel(details?.estimatedValueCents ?? 0) }}</strong></span>
                  <div class="opp-hl-wrap">
                    <button
                      type="button"
                      class="opp-hl-btn opp-hl-won"
                      :class="{ active: details?.closeOutcome === 'won' }"
                      @click="finalizeOutcome = 'won'; handleFinalizeOpportunity()"
                    >
                      <svg viewBox="0 0 24 24"><path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z"/><path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/></svg>
                    </button>
                    <button
                      type="button"
                      class="opp-hl-btn opp-hl-lost"
                      :class="{ active: details?.closeOutcome === 'lost' }"
                      @click="finalizeOutcome = 'lost'; handleFinalizeOpportunity()"
                    >
                      <svg viewBox="0 0 24 24"><path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z"/><path d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17"/></svg>
                    </button>
                  </div>
                </div>
              </div>

              <div class="opp-info">
                <div class="opp-line">
                  <p class="opp-lbl">Telefone</p>
                  <p class="opp-val">{{ formatPhone(details?.phone) || "Não informado" }}</p>
                </div>
                <div class="opp-line">
                  <div class="opp-line-head">
                    <div>
                      <p class="opp-lbl">Cliente</p>
                      <p v-if="!details?.client" class="opp-sub">Nenhum cliente vinculado</p>
                    </div>
                    <button v-if="!details?.client" type="button" class="opp-link-btn" @click="linkMode = 'search'">
                      + Vincular cliente
                    </button>
                  </div>
                  <div
                    v-if="details?.client"
                    class="opp-client-card"
                    role="button"
                    tabindex="0"
                    @click="goToClient(details.client.id)"
                    @keydown.enter="goToClient(details.client.id)"
                  >
                    <span class="opp-client-av">{{ (details.client.name || "C").slice(0,2).toUpperCase() }}</span>
                    <span class="opp-client-info">
                      <span class="opp-client-name">{{ details.client.name }}</span>
                      <span class="opp-client-email">{{ details.client.email || "Sem e-mail" }}</span>
                    </span>
                    <button
                      type="button"
                      class="opp-client-unlink"
                      title="Remover vínculo"
                      @click.stop="handleUnlinkClient"
                    >
                      <svg viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                    </button>
                    <svg class="opp-client-open" viewBox="0 0 24 24"><path d="M14 3h7v7"/><path d="M10 14L21 3"/><path d="M21 14v7h-7"/><path d="M3 10v11h11"/></svg>
                  </div>
                  <div v-if="linkMode === 'search'" class="opp-link-search">
                    <input
                      v-model="clientSearch"
                      type="text"
                      class="opp-link-input"
                      placeholder="Nome, CPF, telefone ou e-mail"
                    />
                    <div class="opp-link-results">
                      <button
                        v-for="client in clientResults"
                        :key="client.id"
                        type="button"
                        class="opp-link-result"
                        @click="handleLinkClient(client.id)"
                      >
                        <span>{{ client.name }}{{ client.cpf ? ` · ${formatCpf(client.cpf)}` : "" }}</span>
                        <span>Vincular</span>
                      </button>
                      <p v-if="clientSearch.trim().length >= 2 && !clientResults.length && !searchingClients" class="opp-empty">
                        Nenhum cliente encontrado.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="opp-tabs">
                <button type="button" class="opp-tab-btn" :class="{ on: activeTab === 'notes' }" @click="activeTab = 'notes'">
                  <svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                  Notas
                </button>
                <button type="button" class="opp-tab-btn" :class="{ on: activeTab === 'documents' }" @click="activeTab = 'documents'">
                  <svg viewBox="0 0 24 24"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                  Documentos
                </button>
                <button type="button" class="opp-tab-btn" :class="{ on: activeTab === 'history' }" @click="activeTab = 'history'">
                  <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  Histórico
                </button>
              </div>

              <div class="opp-pane" v-if="activeTab === 'notes'">
                <textarea v-model="newNote" rows="4" class="opp-note-ta" placeholder="Escreva uma nota sobre este atendimento..."></textarea>
                <div class="opp-pane-actions">
                  <button type="button" class="opp-add-btn" :disabled="savingNote || !newNote.trim()" @click="handleSaveNote">+ Adicionar nota</button>
                </div>
                <div class="opp-note-list">
                  <article v-for="note in details?.notes || []" :key="note.id" class="opp-note">
                    <p class="opp-note-meta">{{ formatDateTime(note.created_at) }}{{ note.author?.name ? ` · ${note.author.name}` : "" }}</p>
                    <p class="opp-note-text">{{ note.content }}</p>
                  </article>
                </div>
              </div>

              <div class="opp-pane" v-else-if="activeTab === 'documents'">
                <label class="opp-doc-upload">
                  + Adicionar documento
                  <input type="file" class="hidden" @change="handleDocumentInput" />
                </label>
                <div class="opp-doc-list">
                  <article v-for="document in details?.documents || []" :key="document.id" class="opp-doc-row">
                    <a :href="document.fileUrl" target="_blank" rel="noopener" class="opp-doc-link">{{ document.fileName }}</a>
                    <button type="button" class="opp-doc-del" @click="handleDeleteDocument(document.id)">Remover</button>
                  </article>
                  <p v-if="!(details?.documents || []).length" class="opp-empty">Nenhum documento anexado.</p>
                </div>
              </div>

              <div class="opp-pane" v-else>
                <div class="opp-timeline">
                  <article v-for="item in historyItems" :key="item.key" class="opp-tl-item">
                    <div class="opp-tl-left">
                      <div class="opp-tl-dot" :class="`opp-tl-dot--${historyKind(item)}`">
                        <svg v-if="historyKind(item) === 'visit'" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                        <svg v-else-if="historyKind(item) === 'lead'" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                        <svg v-else viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      </div>
                      <div class="opp-tl-line"></div>
                    </div>
                    <div class="opp-tl-body">
                      <p class="opp-tl-title">{{ item.title }}</p>
                      <p class="opp-tl-detail">{{ item.detail }}</p>
                      <p class="opp-tl-time">
                        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        {{ formatDateTime(item.date) }}
                      </p>
                    </div>
                  </article>
                  <p v-if="!historyItems.length" class="opp-empty">Sem histórico.</p>
                </div>
              </div>
            </div>
          </aside>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { useLeadCaptureStore } from "../../../store/useLeadCaptureStore";
import type { ClientSummary, LeadStatus } from "../../../types/leads";
import { normalizeWhatsappDigits } from "../../../utils/whatsapp";

const props = defineProps<{
  modelValue: boolean;
  contactId: string | number | null;
  statuses: LeadStatus[];
  mode?: "drawer" | "modal";
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

const router = useRouter();
const leadStore = useLeadCaptureStore();

const details = computed(() => leadStore.opportunityDetails);
const loading = computed(() => leadStore.opportunityDetailsLoading);
const displayMode = computed(() => props.mode ?? "drawer");
const isModalMode = computed(() => displayMode.value === "modal");

const form = reactive({
  opportunityName: "",
  estimatedValue: "",
  statusId: "",
  expectedCloseDate: "",
  internalNotes: ""
});

const saveFeedback = ref("");
const saveFeedbackTone = ref<"ok" | "error" | "loading">("ok");
const saveTimer = ref<number | null>(null);
const saveSequence = ref(0);
const activeTab = ref<"notes" | "documents" | "history">("notes");
const noteEditorOpen = ref(false);
const newNote = ref("");
const savingNote = ref(false);
const finalizeEditorOpen = ref(false);
const finalizeOutcome = ref<"won" | "lost" | null>(null);
const finalizeNote = ref("");
const savingFinalize = ref(false);
const linkMode = ref<null | "search" | "create">(null);
const clientSearch = ref("");
const clientResults = ref<ClientSummary[]>([]);
const searchingClients = ref(false);
const creatingClient = ref(false);
const createClientForm = reactive({
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

const statusBadgeStyle = computed(() => {
  const color = details.value?.statusColor || "#E2E8F0";
  return {
    borderColor: color,
    color: color,
    backgroundColor: `${color}14`
  };
});

const opportunityStatusLabel = computed(() => {
  if (details.value?.closeOutcome === "won") return "Ganha";
  if (details.value?.closeOutcome === "lost") return "Perdida";
  return "Aberta";
});

const opportunityStatusBadgeClass = computed(() => {
  if (details.value?.closeOutcome === "won") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (details.value?.closeOutcome === "lost") return "border-rose-200 bg-rose-50 text-rose-700";
  return "border-sky-200 bg-sky-50 text-sky-700";
});

const saveFeedbackClass = computed(() =>
  saveFeedbackTone.value === "error" ? "text-rose-500" : "text-emerald-600"
);

const headerTitle = computed(() => {
  if (details.value?.name?.trim()) return details.value.name.trim();
  if (details.value?.opportunityName?.trim()) return details.value.opportunityName.trim();
  return "Nova oportunidade";
});

const originLabel = computed(() => {
  if (!details.value) return "NÃ£o informado";
  const parts = [details.value.formName, details.value.pageTitle || details.value.pageSlug].filter(Boolean);
  return parts.length ? parts.join(" / ") : details.value.source || "NÃ£o informado";
});

const clientWhatsappLink = computed(() => {
  const digits = normalizeWhatsappDigits(details.value?.client?.phone || details.value?.phone || "");
  return digits ? `https://wa.me/${digits}` : "";
});
const autoLinkedLabel = computed(() => {
  const mode = details.value?.autoLinkedBy;
  if (!mode || !details.value?.client) return "";
  if (mode === "cpf") return "Vinculado automaticamente por CPF";
  if (mode === "email") return "Vinculado automaticamente por e-mail";
  if (mode === "phone") return "Vinculado automaticamente por telefone";
  return "";
});
const historyItems = computed(() => {
  const items: Array<{ key: string; title: string; detail: string; date: string }> = [];
  if (details.value?.created_at) {
    items.push({
      key: `created-${details.value.id}-${details.value.created_at}`,
      title: "Oportunidade criada",
      detail: details.value.opportunityName || details.value.name || "Oportunidade",
      date: details.value.created_at
    });
  }
  if (details.value?.closedAt) {
    items.push({
      key: `closed-${details.value.id}-${details.value.closedAt}`,
      title: details.value.closeOutcome === "won" ? "Oportunidade ganha" : "Oportunidade perdida",
      detail: currencyLabel(details.value.estimatedValueCents || 0),
      date: details.value.closedAt
    });
  }
  for (const note of details.value?.notes || []) {
    items.push({
      key: `note-${note.id}-${note.created_at}`,
      title: "Nota adicionada",
      detail: note.content || "Sem conteúdo",
      date: note.created_at
    });
  }
  return items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
});

const close = () => emit("update:modelValue", false);

const hydrateForm = () => {
  form.opportunityName = details.value?.opportunityName || "";
  form.estimatedValue = centsToInput(details.value?.estimatedValueCents);
  form.statusId = details.value?.statusId ? String(details.value.statusId) : "";
  form.expectedCloseDate = details.value?.expectedCloseDate || "";
  form.internalNotes = details.value?.internalNotes || "";
};

const fillClientFormFromLead = () => {
  createClientForm.name = details.value?.name || "";
  createClientForm.cpf = details.value?.cpf || "";
  createClientForm.phone = details.value?.phone || "";
  createClientForm.email = details.value?.email || "";
  createClientForm.city = details.value?.city || "";
  createClientForm.zipcode = "";
  createClientForm.street = "";
  createClientForm.number = "";
  createClientForm.complement = "";
  createClientForm.neighborhood = "";
  createClientForm.state = "";
  createClientForm.birthdate = details.value?.birthdate || "";
  createClientForm.notes = "";
};

const showSaveFeedback = (message: string, tone: "ok" | "error" | "loading") => {
  saveFeedback.value = message;
  saveFeedbackTone.value = tone;
};

const persistForm = async () => {
  if (!props.contactId) return;
  const current = ++saveSequence.value;
  showSaveFeedback("Salvando...", "loading");
  try {
    await leadStore.updateOpportunity(props.contactId, {
      opportunityName: form.opportunityName.trim() || null,
      estimatedValueCents: inputToCents(form.estimatedValue),
      statusId: form.statusId ? Number(form.statusId) : null,
      expectedCloseDate: form.expectedCloseDate || null,
      internalNotes: form.internalNotes.trim() || null
    });
    if (current === saveSequence.value) {
      showSaveFeedback("Salvo", "ok");
    }
  } catch (error) {
    console.error(error);
    showSaveFeedback("Erro ao salvar", "error");
  }
};

const schedulePersist = () => {
  if (saveTimer.value) window.clearTimeout(saveTimer.value);
  saveTimer.value = window.setTimeout(() => {
    persistForm();
  }, 550);
};

const normalizeCurrencyField = () => {
  form.estimatedValue = centsToInput(inputToCents(form.estimatedValue));
};

const cancelNoteEditor = () => {
  noteEditorOpen.value = false;
  newNote.value = "";
};

const cancelFinalizeEditor = () => {
  finalizeEditorOpen.value = false;
  finalizeOutcome.value = null;
  finalizeNote.value = "";
};

const handleSaveNote = async () => {
  if (!props.contactId || !newNote.value.trim()) return;
  savingNote.value = true;
  try {
    await leadStore.addOpportunityNote(props.contactId, newNote.value.trim());
    newNote.value = "";
    noteEditorOpen.value = false;
  } catch (error) {
    console.error(error);
  } finally {
    savingNote.value = false;
  }
};

const handleFinalizeOpportunity = async () => {
  if (!props.contactId || !finalizeOutcome.value) return;
  if (saveTimer.value) {
    window.clearTimeout(saveTimer.value);
    saveTimer.value = null;
  }
  savingFinalize.value = true;
  try {
    await persistForm();
    await leadStore.finalizeOpportunity(props.contactId, {
      outcome: finalizeOutcome.value,
      note: finalizeNote.value.trim() || null,
    });
    cancelFinalizeEditor();
  } catch (error) {
    console.error(error);
  } finally {
    savingFinalize.value = false;
  }
};

const handleDocumentInput = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!props.contactId || !file) return;
  try {
    await leadStore.uploadOpportunityDocument(props.contactId, file);
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
  } catch (error) {
    console.error(error);
  }
};

const handleLinkClient = async (clientId: number) => {
  if (!props.contactId) return;
  try {
    await leadStore.linkOpportunityClient(props.contactId, clientId);
    linkMode.value = null;
    clientSearch.value = "";
    clientResults.value = [];
  } catch (error) {
    console.error(error);
  }
};

const handleUnlinkClient = async () => {
  if (!props.contactId) return;
  try {
    await leadStore.unlinkOpportunityClient(props.contactId);
  } catch (error) {
    console.error(error);
  }
};

const handleCreateClient = async () => {
  if (!createClientForm.name.trim() || !props.contactId) return;
  creatingClient.value = true;
  try {
    const client = await leadStore.createClient({
      name: createClientForm.name.trim(),
      cpf: createClientForm.cpf.trim() || null,
      phone: createClientForm.phone.trim() || null,
      email: createClientForm.email.trim() || null,
      city: createClientForm.city.trim() || null,
      zipcode: createClientForm.zipcode.trim() || null,
      street: createClientForm.street.trim() || null,
      number: createClientForm.number.trim() || null,
      complement: createClientForm.complement.trim() || null,
      neighborhood: createClientForm.neighborhood.trim() || null,
      state: createClientForm.state.trim().toUpperCase() || null,
      birthdate: createClientForm.birthdate || null,
      notes: createClientForm.notes.trim() || null
    });
    await leadStore.linkOpportunityClient(props.contactId, client.id);
    linkMode.value = null;
  } catch (error) {
    console.error(error);
  } finally {
    creatingClient.value = false;
  }
};

const goToClient = (clientId: number) => {
  router.push(`/admin/clientes/${clientId}`);
};

watch(
  () => props.modelValue,
  value => {
    if (typeof document !== "undefined") {
      document.body.style.overflow = value ? "hidden" : "";
    }
    if (value && props.contactId) {
      leadStore.fetchOpportunityDetails(props.contactId).then(() => {
        hydrateForm();
        fillClientFormFromLead();
        cancelFinalizeEditor();
      });
    }
  }
);

watch(
  () => props.contactId,
  async contactId => {
    if (!props.modelValue || !contactId) return;
    await leadStore.fetchOpportunityDetails(contactId);
    hydrateForm();
    fillClientFormFromLead();
    cancelFinalizeEditor();
  }
);

watch(
  () => details.value,
  () => {
    hydrateForm();
    fillClientFormFromLead();
    if (details.value?.closedAt) {
      cancelFinalizeEditor();
    }
  }
);

watch(
  () => [form.opportunityName, form.estimatedValue, form.statusId, form.expectedCloseDate, form.internalNotes],
  () => {
    if (!props.modelValue || !details.value) return;
    schedulePersist();
  },
  { deep: true }
);

watch(clientSearch, async value => {
  const query = value.trim();
  if (query.length < 2) {
    clientResults.value = [];
    return;
  }
  searchingClients.value = true;
  try {
    clientResults.value = await leadStore.searchClients(query);
  } catch (error) {
    console.error(error);
    clientResults.value = [];
  } finally {
    searchingClients.value = false;
  }
});

function inputToCents(value: string) {
  const digits = value.replace(/\D/g, "");
  if (!digits) return null;
  return Number(digits);
}

function centsToInput(value?: number | null) {
  return currencyLabel(value || 0);
}

function currencyLabel(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format((value || 0) / 100);
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}

function formatPhone(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length === 13 && digits.startsWith("55")) {
    return `+55 (${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9, 13)}`;
  }
  if (digits.length === 11) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
  }
  if (digits.length === 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6, 10)}`;
  }
  return value || "";
}

function formatCpf(value?: string | null) {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length !== 11) return value || "";
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9, 11)}`;
}

function historyKind(item: { title: string }) {
  const title = item.title.toLowerCase();
  if (title.includes("visit")) return "visit";
  if (title.includes("lead") || title.includes("criada")) return "lead";
  return "update";
}
</script>

<style scoped>
.opp-drawer-shell {
  background: #ffffff;
  border-left: 1.5px solid #e4e9e4;
  box-shadow: -12px 0 48px rgba(0, 0, 0, 0.14);
  font-family: "Plus Jakarta Sans", sans-serif;
}

.opp-hd {
  background: #ffffff;
  border-bottom: none;
}

.opp-x {
  background: #f5f7f5;
  border: 1.5px solid var(--opp-br);
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.opp-x:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.opp-ey {
  color: #8a9e8a;
  font-size: 10px;
  letter-spacing: 0.11em;
}

.opp-hd h2 {
  color: #111a14 !important;
  font-size: 22px;
  line-height: 1.2;
  letter-spacing: -0.4px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  margin-top: 1px;
  margin-bottom: 0;
}

.opp-name{
  color:#111a14;
  font-size:22px;
  line-height:1.2;
  letter-spacing:-0.4px;
  font-weight:700;
  margin:0 0 2px 0;
}

.opp-meta {
  gap: 7px !important;
}

.opp-body {
  background: #ffffff;
  padding: 0;
  min-height: 100%;
}

.opp-body::-webkit-scrollbar {
  width: 4px;
}

.opp-body::-webkit-scrollbar-thumb {
  background: #cdd8cd;
  border-radius: 99px;
}

.opp-card {
  border: 1.5px solid var(--opp-br) !important;
  border-radius: 22px !important;
  box-shadow: none !important;
  background: #fff !important;
  padding: 18px !important;
}

.opp-card p.text-xs {
  color: #8ea0bb !important;
  letter-spacing: 0.18em !important;
  font-size: 11px !important;
}

.opp-card label {
  font-size: 13px !important;
  font-weight: 700 !important;
  color: #6a7b95 !important;
  letter-spacing: 0.01em !important;
}

.opp-card input,
.opp-card select,
.opp-card textarea,
.opp-card .crm-input {
  border: 1.5px solid #d7e0ee !important;
  border-radius: 16px !important;
  background: #fff !important;
  box-shadow: none !important;
}

.opp-card input:focus,
.opp-card select:focus,
.opp-card textarea:focus,
.opp-card .crm-input:focus {
  border-color: rgba(61, 204, 95, 0.45) !important;
  box-shadow: 0 0 0 3px rgba(61, 204, 95, 0.1) !important;
}

.opp-card .bg-brand,
.opp-card .btn-p {
  background: #3dcc5f !important;
  color: #fff !important;
  border-radius: 999px !important;
}

.opp-head-content{padding:0 24px 14px;background:#fff;margin-top:0}
.opp-origin-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.opp-chip{display:inline-flex;align-items:center;padding:3px 10px;border-radius:8px;font-size:12px;font-weight:600;border:1.5px solid transparent}
.opp-chip svg{width:11px;height:11px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;margin-right:4px;flex-shrink:0}
.opp-chip.page{background:rgba(99,102,241,.08);color:#4338CA;border-color:rgba(99,102,241,.18)}
.opp-chip.form{background:rgba(245,158,11,.08);color:#92400E;border-color:rgba(245,158,11,.18)}
.opp-date{font-size:12px;color:#8a9e8a}
.opp-meta-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.opp-meta-row{padding-bottom:10px;border-bottom:1px solid #e4e9e4}
.opp-stage{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;border:1.5px solid;font-size:12px;font-weight:700}
.opp-status{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;border:1.5px solid transparent}
.opp-status.border-emerald-200{background:rgba(61,204,95,.1);color:#1A7A35;border-color:rgba(61,204,95,.22)}
.opp-status.border-rose-200{background:rgba(239,68,68,.07);color:#B91C1C;border-color:rgba(239,68,68,.2)}
.opp-status.border-sky-200{background:rgba(245,158,11,.07);color:#92400E;border-color:rgba(245,158,11,.2)}
.opp-value{font-size:14px;color:#8a9e8a}
.opp-value strong{color:#2f4c35}
.opp-hl-wrap{display:flex;align-items:center;gap:4px}
.opp-hl-btn{width:32px;height:32px;border-radius:8px;border:1.5px solid #e4e9e4;background:#f5f7f5;display:flex;align-items:center;justify-content:center}
.opp-hl-btn svg{width:14px;height:14px;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.opp-hl-won svg{stroke:rgba(46,173,76,.45)}
.opp-hl-lost svg{stroke:rgba(239,68,68,.45)}
.opp-hl-won.active,.opp-hl-won:hover{background:rgba(61,204,95,.1);border-color:rgba(61,204,95,.22)}
.opp-hl-lost.active,.opp-hl-lost:hover{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.2)}
.opp-info{padding:0 24px 10px;background:#fff;border-bottom:1.5px solid #e4e9e4}
.opp-line{padding:10px 0;border-bottom:1px solid #e4e9e4}
.opp-line:last-child{border-bottom:none}
.opp-line-head{display:flex;align-items:center;justify-content:space-between;gap:12px}
.opp-lbl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8a9e8a}
.opp-sub{font-size:13px;color:#4a5e4a}
.opp-val{font-size:16px;font-weight:500;color:#111a14}
.opp-link-btn{height:34px;padding:0 14px;border-radius:999px;border:1.5px solid #d5ddd5;background:#fff;color:#2d4637;font-size:13px;font-weight:500}
.opp-client-card{margin-top:10px;width:100%;display:flex;align-items:center;gap:10px;padding:10px 12px;border:1.5px solid #d5ddd5;border-radius:8px;background:#f5f7f5;text-align:left}
.opp-client-av{width:32px;height:32px;border-radius:8px;background:#3DCC5F;color:#0F1F14;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0}
.opp-client-info{display:flex;flex-direction:column;min-width:0;flex:1}
.opp-client-name{font-size:13px;font-weight:700;color:#111a14;line-height:1.2}
.opp-client-email{font-size:11px;color:#8a9e8a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2}
.opp-client-open{width:14px;height:14px;stroke:#8a9e8a;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}
.opp-client-unlink{width:24px;height:24px;border-radius:6px;border:1px solid #f1d1d1;background:#fff;display:flex;align-items:center;justify-content:center;margin-right:6px;flex-shrink:0}
.opp-client-unlink svg{width:12px;height:12px;stroke:#d35b5b;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.opp-client-unlink:hover{background:#fff5f5;border-color:#efb6b6}
.opp-link-search{margin-top:10px;padding:10px;border:1.5px solid #e4e9e4;border-radius:10px;background:#fff}
.opp-link-input{width:100%;height:36px;border:1.5px solid #d5ddd5;border-radius:8px;padding:0 10px;font-size:13px;outline:none}
.opp-link-input:focus{border-color:rgba(61,204,95,.5);box-shadow:0 0 0 3px rgba(61,204,95,.1)}
.opp-link-results{margin-top:8px;display:flex;flex-direction:column;gap:6px}
.opp-link-result{display:flex;justify-content:space-between;align-items:center;border:1px solid #e4e9e4;background:#fff;border-radius:8px;padding:8px 10px;font-size:12px;color:#3a4f3f}
.opp-link-result span:last-child{font-weight:700;color:#1A7A35}
.opp-tabs{display:flex;gap:8px;padding:0 24px;background:#fff;border-bottom:1.5px solid #e4e9e4}
.opp-tab-btn{padding:12px 14px;border:2px solid transparent;background:transparent;color:#6f896f;font-weight:600;font-size:13px;border-radius:4px;display:inline-flex;align-items:center;gap:6px}
.opp-tab-btn svg{width:13px;height:13px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;opacity:.75}
.opp-tab-btn.on{color:#2ead4c;border-color:transparent;background:#fff}
.opp-tab-btn.on svg{opacity:1}
.opp-pane{padding:18px 24px 40px}
.opp-pane{background:#fff}
.opp-note-ta{width:100%;min-height:108px;border:1.5px solid #d7dfd7;border-radius:10px;padding:12px;font-size:13px;color:#38503f;outline:none;resize:vertical}
.opp-pane-actions{display:flex;justify-content:flex-end;margin-top:10px}
.opp-add-btn{height:34px;padding:0 16px;border:none;border-radius:999px;background:#3dcc5f;color:#0f1f14;font-weight:700;font-size:13px}
.opp-add-btn:disabled{opacity:.5}
.opp-note-list{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.opp-note{background:#f5f7f5;border:1.5px solid #e4e9e4;border-radius:10px;padding:10px 12px}
.opp-note-meta{font-size:11px;color:#8a9e8a}
.opp-note-text{font-size:13px;color:#1d3424;white-space:pre-wrap}
.opp-doc-upload{display:inline-flex;align-items:center;height:34px;padding:0 14px;border-radius:999px;border:1.5px solid #d5ddd5;background:#fff;color:#2d4637;font-weight:600}
.opp-doc-list{margin-top:10px;display:flex;flex-direction:column;gap:8px}
.opp-doc-row{display:flex;align-items:center;justify-content:space-between;gap:8px;border:1.5px solid #e4e9e4;border-radius:10px;padding:9px 12px;background:#fff}
.opp-doc-link{font-size:13px;color:#1a7a35;text-decoration:none}
.opp-doc-del{border:1.5px solid #f4cccc;background:#fff;border-radius:999px;height:28px;padding:0 12px;font-size:11px;color:#b91c1c}
.opp-empty{font-size:13px;color:#8a9e8a}
.opp-timeline{display:flex;flex-direction:column;gap:10px}
.opp-tl-item{display:flex;gap:12px;padding-bottom:14px}
.opp-tl-item:last-child{padding-bottom:0}
.opp-tl-left{display:flex;flex-direction:column;align-items:center;width:24px;flex-shrink:0}
.opp-tl-dot{width:24px;height:24px;border-radius:8px;display:flex;align-items:center;justify-content:center}
.opp-tl-dot svg{width:12px;height:12px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.opp-tl-dot--visit{background:rgba(99,102,241,.12);color:#6366F1}
.opp-tl-dot--lead{background:rgba(61,204,95,.12);color:#2EAD4C}
.opp-tl-dot--update{background:rgba(245,158,11,.12);color:#D97706}
.opp-tl-line{width:1.5px;background:#e4e9e4;flex:1;margin-top:4px;min-height:10px}
.opp-tl-item:last-child .opp-tl-line{display:none}
.opp-tl-title{font-size:13px;font-weight:700;color:#1b2e1f}
.opp-tl-detail{font-size:12px;color:#6a806a}
.opp-tl-time{font-size:10px;color:#8a9e8a;display:flex;align-items:center;gap:4px;margin-top:4px}
.opp-tl-time svg{width:10px;height:10px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}

.crm-input {
  width: 100%;
  border-radius: 1rem;
  border: 1px solid rgb(226 232 240);
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  color: rgb(15 23 42);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.crm-input:focus {
  border-color: var(--color-brand, #22c55e);
  box-shadow: 0 0 0 2px rgb(34 197 94 / 0.2);
}

.crm-drawer-fade-enter-active,
.crm-drawer-fade-leave-active {
  transition: opacity 0.18s ease;
}

.crm-drawer-fade-enter-from,
.crm-drawer-fade-leave-to {
  opacity: 0;
}

.crm-drawer-slide-enter-active,
.crm-drawer-slide-leave-active {
  transition: transform 0.22s ease;
}

.crm-drawer-slide-enter-from,
.crm-drawer-slide-leave-to {
  transform: translateX(100%);
}

.crm-modal-scale-enter-active,
.crm-modal-scale-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.crm-modal-scale-enter-from,
.crm-modal-scale-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}
</style>




