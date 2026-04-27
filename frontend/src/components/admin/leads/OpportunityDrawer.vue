<template>
  <Teleport to="body">
    <transition name="crm-drawer-fade">
      <div v-if="modelValue" class="fixed inset-0 z-[160]">
        <div class="absolute inset-0 bg-slate-900/45" @click="close"></div>
        <transition :name="isModalMode ? 'crm-modal-scale' : 'crm-drawer-slide'">
          <aside
            v-if="modelValue"
            class="absolute flex flex-col overflow-hidden bg-white shadow-2xl"
            :class="
              isModalMode
                ? 'inset-x-4 top-6 bottom-6 mx-auto w-auto max-w-[1120px] rounded-[32px] border border-slate-200 md:inset-x-8'
                : 'inset-y-0 right-0 h-full w-full max-w-[680px] border-l border-slate-200'
            "
          >
            <div class="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-5">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Oportunidade</p>
                <h2 class="mt-1 truncate text-xl font-bold text-slate-900">
                  {{ headerTitle }}
                </h2>
                <div class="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                  <span
                    class="rounded-full border px-2.5 py-1 text-xs font-semibold"
                    :style="statusBadgeStyle"
                  >
                    {{ details?.statusName || "Sem status" }}
                  </span>
                  <span>Valor estimado: {{ currencyLabel(details?.estimatedValueCents ?? 0) }}</span>
                  <span v-if="saveFeedback" :class="saveFeedbackClass">{{ saveFeedback }}</span>
                </div>
              </div>
              <button
                type="button"
                class="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
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

            <div v-else class="flex-1 overflow-y-auto px-5 py-5">
              <section class="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Dados comerciais</p>
                <div class="mt-4 space-y-4">
                  <div>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Nome da oportunidade</label>
                    <input
                      v-model="form.opportunityName"
                      type="text"
                      class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                    />
                  </div>
                  <div class="grid gap-4 md:grid-cols-2">
                    <div>
                      <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Valor</label>
                      <input
                        v-model="form.estimatedValue"
                        type="text"
                        inputmode="numeric"
                        class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                        @blur="normalizeCurrencyField"
                      />
                    </div>
                    <div>
                      <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</label>
                      <select
                        v-model="form.statusId"
                        class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                      >
                        <option value="">Sem status</option>
                        <option v-for="status in statuses" :key="status.id" :value="String(status.id)">
                          {{ status.name }}
                        </option>
                      </select>
                    </div>
                  </div>
                  <div class="grid gap-4 md:grid-cols-2">
                    <div>
                      <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Data prevista de fechamento</label>
                      <input
                        v-model="form.expectedCloseDate"
                        type="date"
                        class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                      />
                    </div>
                    <div>
                      <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Origem</label>
                      <div class="mt-1 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-600">
                        {{ originLabel }}
                      </div>
                    </div>
                  </div>
                  <div>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Observação interna</label>
                    <textarea
                      v-model="form.internalNotes"
                      rows="4"
                      class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                    ></textarea>
                  </div>
                </div>
              </section>

              <section class="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Encerramento</p>
                    <p class="mt-1 text-sm text-slate-500">
                      {{ details?.closedAt ? "Oportunidade finalizada." : "Finalize como ganha ou perdida sem sair desta tela." }}
                    </p>
                  </div>
                  <button
                    v-if="!details?.closedAt"
                    type="button"
                    class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
                    @click="finalizeEditorOpen = !finalizeEditorOpen"
                  >
                    Finalizar
                  </button>
                </div>

                <div
                  v-if="details?.closedAt"
                  class="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4"
                >
                  <p class="text-sm font-semibold text-emerald-900">
                    {{ details.closeOutcome === "won" ? "Ganha" : "Perdida" }}
                  </p>
                  <p class="mt-1 text-sm text-emerald-800">
                    Encerrada em {{ formatDateTime(details.closedAt) }}
                  </p>
                </div>

                <div v-else-if="finalizeEditorOpen" class="mt-4 rounded-2xl border border-slate-200 p-4">
                  <div class="grid gap-4 md:grid-cols-2">
                    <button
                      type="button"
                      class="rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition"
                      :class="finalizeOutcome === 'won' ? 'border-emerald-500 bg-emerald-50 text-emerald-900' : 'border-slate-200 text-slate-700 hover:bg-slate-50'"
                      @click="finalizeOutcome = 'won'"
                    >
                      Ganha
                    </button>
                    <button
                      type="button"
                      class="rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition"
                      :class="finalizeOutcome === 'lost' ? 'border-rose-500 bg-rose-50 text-rose-900' : 'border-slate-200 text-slate-700 hover:bg-slate-50'"
                      @click="finalizeOutcome = 'lost'"
                    >
                      Perdida
                    </button>
                  </div>
                  <textarea
                    v-model="finalizeNote"
                    rows="3"
                    class="mt-3 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                    placeholder="Nota de encerramento (opcional)"
                  ></textarea>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
                      :disabled="savingFinalize || !finalizeOutcome"
                      @click="handleFinalizeOpportunity"
                    >
                      {{ savingFinalize ? "Finalizando..." : "Confirmar encerramento" }}
                    </button>
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      @click="cancelFinalizeEditor"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </section>

              <section class="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Cliente</p>
                    <p class="mt-1 text-sm text-slate-500">
                      {{ details?.client ? "Cliente vinculado à oportunidade." : "Nenhum cliente vinculado." }}
                    </p>
                  </div>
                </div>

                <div v-if="details?.client" class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p class="font-semibold text-slate-900">{{ details.client.name }}</p>
                  <p class="mt-2 text-sm text-slate-600">{{ formatCpf(details.client.cpf) || "CPF não informado" }}</p>
                  <p class="text-sm text-slate-600">{{ formatPhone(details.client.phone) || "Telefone não informado" }}</p>
                  <p class="text-sm text-slate-600">{{ details.client.email || "E-mail não informado" }}</p>
                  <p class="text-sm text-slate-600">{{ details.client.city || "Cidade não informada" }}</p>
                  <div class="mt-3 flex flex-wrap gap-2">
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
                      class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
                      @click="goToClient(details.client.id)"
                    >
                      Ver cliente
                    </button>
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      @click="linkMode = 'search'"
                    >
                      Trocar vínculo
                    </button>
                    <button
                      type="button"
                      class="rounded-full border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-50"
                      @click="handleUnlinkClient"
                    >
                      Remover vínculo
                    </button>
                  </div>
                </div>

                <div v-else class="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
                    @click="linkMode = 'create'"
                  >
                    Criar cliente
                  </button>
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                    @click="linkMode = 'search'"
                  >
                    Vincular existente
                  </button>
                </div>

                <div
                  v-if="!details?.client && details?.clientSuggestions?.length"
                  class="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4"
                >
                  <p class="text-sm font-semibold text-amber-900">Possíveis clientes encontrados</p>
                  <div class="mt-3 flex flex-col gap-2">
                    <button
                      v-for="suggestion in details.clientSuggestions"
                      :key="suggestion.id"
                      type="button"
                      class="flex items-center justify-between rounded-2xl border border-amber-200 bg-white px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-amber-50"
                      @click="handleLinkClient(suggestion.id)"
                    >
                      <span>{{ suggestion.name }}{{ suggestion.cpf ? ` · ${formatCpf(suggestion.cpf)}` : "" }}</span>
                      <span class="font-semibold text-brand">Vincular</span>
                    </button>
                  </div>
                </div>

                <div v-if="linkMode === 'search'" class="mt-4 rounded-2xl border border-slate-200 p-4">
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">Buscar cliente</label>
                  <input
                    v-model="clientSearch"
                    type="text"
                    placeholder="Nome, CPF, telefone ou e-mail"
                    class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                  />
                  <div class="mt-3 space-y-2">
                    <button
                      v-for="client in clientResults"
                      :key="client.id"
                      type="button"
                      class="flex w-full items-center justify-between rounded-2xl border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                      @click="handleLinkClient(client.id)"
                    >
                      <span>{{ client.name }}{{ client.cpf ? ` · ${formatCpf(client.cpf)}` : "" }}</span>
                      <span class="font-semibold text-brand">Vincular</span>
                    </button>
                    <p v-if="clientSearch.trim().length >= 2 && !clientResults.length && !searchingClients" class="text-sm text-slate-500">
                      Nenhum cliente encontrado.
                    </p>
                  </div>
                </div>

                <div v-if="linkMode === 'create'" class="mt-4 rounded-2xl border border-slate-200 p-4">
                  <p class="text-sm font-semibold text-slate-900">Criar cliente com os dados do lead</p>
                  <div class="mt-3 grid gap-3 md:grid-cols-2">
                    <input v-model="createClientForm.name" type="text" placeholder="Nome" class="crm-input" />
                    <input v-model="createClientForm.cpf" type="text" placeholder="CPF" class="crm-input" />
                    <input v-model="createClientForm.phone" type="text" placeholder="Telefone" class="crm-input" />
                    <input v-model="createClientForm.email" type="email" placeholder="E-mail" class="crm-input" />
                    <input v-model="createClientForm.city" type="text" placeholder="Cidade" class="crm-input" />
                    <input v-model="createClientForm.state" type="text" maxlength="2" placeholder="UF" class="crm-input" />
                    <input v-model="createClientForm.zipcode" type="text" placeholder="CEP" class="crm-input" />
                    <input v-model="createClientForm.street" type="text" placeholder="Logradouro" class="crm-input md:col-span-2" />
                    <input v-model="createClientForm.number" type="text" placeholder="Numero" class="crm-input" />
                    <input v-model="createClientForm.complement" type="text" placeholder="Complemento" class="crm-input" />
                    <input v-model="createClientForm.neighborhood" type="text" placeholder="Bairro" class="crm-input md:col-span-2" />
                    <input v-model="createClientForm.birthdate" type="date" class="crm-input" />
                  </div>
                  <textarea
                    v-model="createClientForm.notes"
                    rows="3"
                    placeholder="Observações"
                    class="crm-input mt-3"
                  ></textarea>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
                      :disabled="creatingClient"
                      @click="handleCreateClient"
                    >
                      {{ creatingClient ? "Criando..." : "Criar cliente" }}
                    </button>
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      @click="linkMode = null"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </section>

              <section class="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Notas</p>
                    <p class="mt-1 text-sm text-slate-500">Histórico do atendimento comercial.</p>
                  </div>
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                    @click="noteEditorOpen = !noteEditorOpen"
                  >
                    + Adicionar nota
                  </button>
                </div>

                <div v-if="noteEditorOpen" class="mt-4 rounded-2xl border border-slate-200 p-4">
                  <textarea
                    v-model="newNote"
                    rows="4"
                    class="w-full rounded-2xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
                    placeholder="Escreva uma nota interna"
                  ></textarea>
                  <div class="mt-3 flex gap-2">
                    <button
                      type="button"
                      class="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60"
                      :disabled="savingNote"
                      @click="handleSaveNote"
                    >
                      {{ savingNote ? "Salvando..." : "Salvar" }}
                    </button>
                    <button
                      type="button"
                      class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      @click="cancelNoteEditor"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>

                <div class="mt-4 space-y-3">
                  <article
                    v-for="note in details?.notes || []"
                    :key="note.id"
                    class="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <p class="text-xs text-slate-400">
                      {{ formatDateTime(note.created_at) }}{{ note.author?.name ? ` · ${note.author.name}` : "" }}
                    </p>
                    <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ note.content }}</p>
                  </article>
                  <p v-if="!(details?.notes || []).length" class="text-sm text-slate-500">Nenhuma nota registrada.</p>
                </div>
              </section>

              <section class="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Documentos</p>
                    <p class="mt-1 text-sm text-slate-500">Anexos da oportunidade.</p>
                  </div>
                  <label class="inline-flex cursor-pointer items-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                    + Adicionar documento
                    <input type="file" class="hidden" @change="handleDocumentInput" />
                  </label>
                </div>

                <div class="mt-4 space-y-2">
                  <article
                    v-for="document in details?.documents || []"
                    :key="document.id"
                    class="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 px-3 py-3"
                  >
                    <a
                      :href="document.fileUrl"
                      target="_blank"
                      rel="noopener"
                      class="min-w-0 truncate text-sm font-semibold text-brand hover:underline"
                    >
                      {{ document.fileName }}
                    </a>
                    <button
                      type="button"
                      class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50"
                      @click="handleDeleteDocument(document.id)"
                    >
                      Remover
                    </button>
                  </article>
                  <p v-if="!(details?.documents || []).length" class="text-sm text-slate-500">Nenhum documento anexado.</p>
                </div>
              </section>
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

const saveFeedbackClass = computed(() =>
  saveFeedbackTone.value === "error" ? "text-rose-500" : "text-emerald-600"
);

const headerTitle = computed(() => {
  if (details.value?.opportunityName?.trim()) return details.value.opportunityName.trim();
  if (details.value?.name && details.value?.pageTitle) return `${details.value.name} - ${details.value.pageTitle}`;
  if (details.value?.name) return `Nova oportunidade - ${details.value.name}`;
  return "Nova oportunidade";
});

const originLabel = computed(() => {
  if (!details.value) return "Não informado";
  const parts = [details.value.formName, details.value.pageTitle || details.value.pageSlug].filter(Boolean);
  return parts.length ? parts.join(" / ") : details.value.source || "Não informado";
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
</script>

<style scoped>
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
