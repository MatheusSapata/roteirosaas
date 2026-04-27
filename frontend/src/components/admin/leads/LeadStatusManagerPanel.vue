<template>
  <section class="space-y-5">
    <header class="flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white px-5 py-5 shadow-sm md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">{{ viewCopy.header.eyebrow }}</p>
        <h2 class="mt-2 text-2xl font-bold text-slate-900">{{ viewCopy.header.title }}</h2>
        <p class="mt-1 text-sm text-slate-500">{{ viewCopy.header.description }}</p>
      </div>
      <button
        type="button"
        class="inline-flex items-center justify-center rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800"
        @click="openCreateModal"
      >
        + {{ viewCopy.actions.newStatus }}
      </button>
    </header>

    <div class="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <div class="mb-4 flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <span>{{ viewCopy.pipeline.title }}</span>
        <span class="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] normal-case tracking-normal text-slate-600">
          {{ viewCopy.pipeline.helper }}
        </span>
      </div>

      <div v-if="loading && !orderedStatuses.length" class="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
        {{ viewCopy.pipeline.loading }}
      </div>
      <div v-else-if="!orderedStatuses.length" class="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
        {{ viewCopy.pipeline.empty }}
      </div>
      <ul v-else class="space-y-3">
        <li
          v-for="status in orderedStatuses"
          :key="status.id"
          class="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300"
          :class="dragOverStatusId === idKey(status.id) ? 'ring-2 ring-brand/40' : ''"
          draggable="true"
          @dragstart="handleDragStart(status.id)"
          @dragenter.prevent="handleDragEnter(status.id)"
          @dragover.prevent="handleDragEnter(status.id)"
          @dragend="handleDragEnd"
          @drop.prevent="handleDrop(status.id)"
        >
          <div class="flex flex-col gap-3 md:flex-row md:items-center">
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-400 transition group-hover:text-slate-600"
              :aria-label="viewCopy.pipeline.dragAria"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="currentColor">
                <path d="M9 5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m9-14a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0" />
              </svg>
            </button>

            <span class="h-3.5 w-3.5 rounded-full border border-slate-200" :style="{ backgroundColor: status.color }"></span>

            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="truncate text-base font-semibold text-slate-900">{{ status.name }}</p>
                <span
                  v-if="resolveSpecialBadge(status.name)"
                  class="rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide"
                  :class="resolveSpecialBadge(status.name) === 'won' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
                >
                  {{ resolveSpecialBadge(status.name) === "won" ? viewCopy.badges.won : viewCopy.badges.lost }}
                </span>
              </div>
              <p class="mt-1 text-xs text-slate-500">
                {{ usageCount(status.id) }} {{ usageCount(status.id) === 1 ? viewCopy.pipeline.usageSingle : viewCopy.pipeline.usagePlural }}
              </p>
            </div>

            <div class="flex items-center gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                :disabled="savingMap[idKey(status.id)]"
                @click="openEditModal(status)"
              >
                {{ savingMap[idKey(status.id)] ? viewCopy.actions.saving : viewCopy.actions.edit }}
              </button>
              <button
                type="button"
                class="rounded-full border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 disabled:opacity-60"
                :disabled="deletingMap[idKey(status.id)]"
                @click="handleDeleteStatus(status)"
              >
                {{ deletingMap[idKey(status.id)] ? viewCopy.actions.deleting : viewCopy.actions.delete }}
              </button>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <div
      v-if="feedback.text"
      class="rounded-2xl border px-4 py-2 text-sm"
      :class="feedback.error ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'"
    >
      {{ feedback.text }}
    </div>

    <Teleport to="body">
      <div v-if="statusModalOpen" class="fixed inset-0 z-[170] flex items-center justify-center bg-slate-900/45 px-4">
        <div class="w-full max-w-lg rounded-[28px] border border-slate-200 bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">{{ viewCopy.modal.eyebrow }}</p>
              <h3 class="mt-2 text-2xl font-bold text-slate-900">
                {{ statusModalMode === "create" ? viewCopy.modal.createTitle : viewCopy.modal.editTitle }}
              </h3>
            </div>
            <button
              type="button"
              class="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50"
              @click="closeStatusModal"
            >
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>

          <div class="mt-5 space-y-4">
            <label class="block">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.modal.nameLabel }}</span>
              <input
                v-model="statusModalName"
                type="text"
                :placeholder="viewCopy.modal.namePlaceholder"
                class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
            </label>
            <div>
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.modal.colorLabel }}</span>
              <div class="mt-2 flex items-center gap-3">
                <label class="relative block h-10 w-10 cursor-pointer overflow-hidden rounded-xl border border-slate-200">
                  <input
                    v-model="statusModalColor"
                    type="color"
                    :aria-label="viewCopy.modal.colorAria"
                    class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                  />
                  <span class="block h-full w-full" :style="{ backgroundColor: statusModalColor }"></span>
                </label>
                <p class="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  {{ statusModalColor }}
                </p>
              </div>
            </div>
          </div>

          <div class="mt-6 flex justify-end gap-2">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              @click="closeStatusModal"
            >
              {{ viewCopy.modal.cancel }}
            </button>
            <button
              type="button"
              class="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800 disabled:opacity-60"
              :disabled="statusModalSaving || !statusModalName.trim()"
              @click="submitStatusModal"
            >
              {{
                statusModalSaving
                  ? statusModalMode === "create"
                    ? viewCopy.modal.creating
                    : viewCopy.modal.saving
                  : statusModalMode === "create"
                    ? viewCopy.modal.createAction
                    : viewCopy.modal.saveAction
              }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import type { LeadStatus } from "../../../types/leads";
import { useLeadCaptureStore } from "../../../store/useLeadCaptureStore";
import { createAdminLocalizer, getAdminLanguage } from "../../../utils/adminI18n";

const leadStore = useLeadCaptureStore();
const defaultStatusColor = "#22c55e";
const statusOrderStorageKey = "lead_status_pipeline_order_v1";

const adminLanguage = getAdminLanguage();
const t = createAdminLocalizer(adminLanguage);

const viewCopy = {
  header: {
    eyebrow: t({ pt: "CRM Pipeline", es: "Pipeline CRM" }),
    title: t({ pt: "Configurações de status", es: "Configuración de estados" }),
    description: t({
      pt: "Organize o funil comercial, personalize etapas e mantenha o pipeline consistente.",
      es: "Organiza el embudo comercial, personaliza etapas y mantén el pipeline consistente."
    })
  },
  pipeline: {
    title: t({ pt: "Ordem do pipeline", es: "Orden del pipeline" }),
    helper: t({ pt: "Arraste para reorganizar", es: "Arrastra para reorganizar" }),
    loading: t({ pt: "Carregando status...", es: "Cargando estados..." }),
    empty: t({ pt: "Nenhum status cadastrado.", es: "No hay estados registrados." }),
    usageSingle: t({ pt: "oportunidade", es: "oportunidad" }),
    usagePlural: t({ pt: "oportunidades", es: "oportunidades" }),
    dragAria: t({ pt: "Reordenar status", es: "Reordenar estado" })
  },
  actions: {
    newStatus: t({ pt: "Novo status", es: "Nuevo estado" }),
    edit: t({ pt: "Editar", es: "Editar" }),
    delete: t({ pt: "Excluir", es: "Eliminar" }),
    deleting: t({ pt: "Excluindo...", es: "Eliminando..." }),
    saving: t({ pt: "Salvando...", es: "Guardando..." })
  },
  badges: {
    won: t({ pt: "Ganho", es: "Ganado" }),
    lost: t({ pt: "Perdido", es: "Perdido" })
  },
  modal: {
    eyebrow: t({ pt: "Status", es: "Estado" }),
    createTitle: t({ pt: "Novo status do pipeline", es: "Nuevo estado del pipeline" }),
    editTitle: t({ pt: "Editar status", es: "Editar estado" }),
    nameLabel: t({ pt: "Nome", es: "Nombre" }),
    namePlaceholder: t({ pt: "Ex: Proposta enviada", es: "Ej: Propuesta enviada" }),
    colorLabel: t({ pt: "Cor", es: "Color" }),
    colorAria: t({ pt: "Selecionar cor do status", es: "Seleccionar color del estado" }),
    cancel: t({ pt: "Cancelar", es: "Cancelar" }),
    createAction: t({ pt: "Criar status", es: "Crear estado" }),
    saveAction: t({ pt: "Salvar alterações", es: "Guardar cambios" }),
    creating: t({ pt: "Criando...", es: "Creando..." }),
    saving: t({ pt: "Salvando...", es: "Guardando..." })
  },
  feedback: {
    loadError: t({ pt: "Não foi possível carregar os status.", es: "No fue posible cargar los estados." }),
    createSuccess: t({ pt: "Status criado com sucesso.", es: "Estado creado con éxito." }),
    createError: t({ pt: "Não foi possível criar o status.", es: "No fue posible crear el estado." }),
    updateSuccess: t({ pt: "Status atualizado.", es: "Estado actualizado." }),
    updateError: t({ pt: "Erro ao atualizar status.", es: "Error al actualizar el estado." }),
    deleteSuccess: t({ pt: "Status removido.", es: "Estado eliminado." }),
    deleteError: t({ pt: "Não foi possível remover o status.", es: "No fue posible eliminar el estado." }),
    confirmDelete: (name: string) =>
      t({
        pt: `Excluir o status "${name}"?`,
        es: `¿Eliminar el estado "${name}"?`
      })
  }
};

const statusModalOpen = ref(false);
const statusModalMode = ref<"create" | "edit">("create");
const statusModalTargetId = ref<string | null>(null);
const statusModalName = ref("");
const statusModalColor = ref(defaultStatusColor);
const statusModalSaving = ref(false);

const feedback = ref<{ text: string; error: boolean }>({ text: "", error: false });
const savingMap = reactive<Record<string, boolean>>({});
const deletingMap = reactive<Record<string, boolean>>({});

const dragStatusId = ref<string | null>(null);
const dragOverStatusId = ref<string | null>(null);
const statusOrder = ref<string[]>([]);

const statusList = computed(() => leadStore.statuses);
const loading = computed(() => leadStore.statusesLoading);
const contacts = computed(() => leadStore.contacts);

const idKey = (value: string | number) => String(value);

const usageByStatusId = computed<Record<string, number>>(() => {
  const map: Record<string, number> = {};
  contacts.value.forEach(contact => {
    if (contact.status_id === null || typeof contact.status_id === "undefined") return;
    const key = idKey(contact.status_id);
    map[key] = (map[key] || 0) + 1;
  });
  return map;
});

const orderedStatuses = computed(() => {
  if (!statusOrder.value.length) return statusList.value;
  const indexMap = new Map(statusOrder.value.map((id, index) => [id, index]));
  return [...statusList.value].sort((a, b) => {
    const aIndex = indexMap.get(idKey(a.id));
    const bIndex = indexMap.get(idKey(b.id));
    if (typeof aIndex === "number" && typeof bIndex === "number") return aIndex - bIndex;
    if (typeof aIndex === "number") return -1;
    if (typeof bIndex === "number") return 1;
    return 0;
  });
});

const usageCount = (statusId: string | number) => usageByStatusId.value[idKey(statusId)] || 0;

const setFeedback = (text = "", error = false) => {
  feedback.value = { text, error };
  if (text) {
    setTimeout(() => {
      feedback.value = { text: "", error: false };
    }, 3200);
  }
};

const persistStatusOrder = () => {
  if (typeof window === "undefined") return;
  localStorage.setItem(statusOrderStorageKey, JSON.stringify(statusOrder.value));
};

const loadStatusOrder = () => {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem(statusOrderStorageKey);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return;
    statusOrder.value = parsed.map(item => String(item));
  } catch {
    statusOrder.value = [];
  }
};

const syncStatusOrderWithList = () => {
  const available = statusList.value.map(status => idKey(status.id));
  const availableSet = new Set(available);
  const current = statusOrder.value.filter(id => availableSet.has(id));
  available.forEach(id => {
    if (!current.includes(id)) current.push(id);
  });
  statusOrder.value = current;
  persistStatusOrder();
};

const ensureStatuses = () =>
  leadStore.fetchStatuses().catch(() => setFeedback(viewCopy.feedback.loadError, true));

const normalizeName = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();

const resolveSpecialBadge = (name: string) => {
  const normalized = normalizeName(name);
  if (normalized === "ganho" || normalized === "won") return "won";
  if (normalized === "perdido" || normalized === "lost") return "lost";
  return null;
};

const openCreateModal = () => {
  statusModalMode.value = "create";
  statusModalTargetId.value = null;
  statusModalName.value = "";
  statusModalColor.value = defaultStatusColor;
  statusModalOpen.value = true;
};

const openEditModal = (status: LeadStatus) => {
  statusModalMode.value = "edit";
  statusModalTargetId.value = idKey(status.id);
  statusModalName.value = status.name;
  statusModalColor.value = status.color || defaultStatusColor;
  statusModalOpen.value = true;
};

const closeStatusModal = () => {
  if (statusModalSaving.value) return;
  statusModalOpen.value = false;
};

const submitStatusModal = async () => {
  const name = statusModalName.value.trim();
  const color = statusModalColor.value || defaultStatusColor;
  if (!name || statusModalSaving.value) return;
  statusModalSaving.value = true;
  try {
    if (statusModalMode.value === "create") {
      const created = await leadStore.createStatus({ name, color });
      statusOrder.value.push(idKey(created.id));
      persistStatusOrder();
      setFeedback(viewCopy.feedback.createSuccess);
    } else if (statusModalTargetId.value) {
      savingMap[statusModalTargetId.value] = true;
      await leadStore.updateStatus(statusModalTargetId.value, { name, color });
      setFeedback(viewCopy.feedback.updateSuccess);
    }
    statusModalOpen.value = false;
  } catch (err) {
    console.error(err);
    setFeedback(statusModalMode.value === "create" ? viewCopy.feedback.createError : viewCopy.feedback.updateError, true);
  } finally {
    if (statusModalTargetId.value) savingMap[statusModalTargetId.value] = false;
    statusModalSaving.value = false;
  }
};

const handleDeleteStatus = async (status: LeadStatus) => {
  const key = idKey(status.id);
  if (deletingMap[key]) return;
  const confirmed = window.confirm(viewCopy.feedback.confirmDelete(status.name));
  if (!confirmed) return;
  deletingMap[key] = true;
  try {
    await leadStore.deleteStatus(status.id);
    statusOrder.value = statusOrder.value.filter(id => id !== key);
    persistStatusOrder();
    setFeedback(viewCopy.feedback.deleteSuccess);
  } catch (err) {
    console.error(err);
    setFeedback(viewCopy.feedback.deleteError, true);
  } finally {
    deletingMap[key] = false;
  }
};

const handleDragStart = (statusId: string | number) => {
  dragStatusId.value = idKey(statusId);
};

const handleDragEnter = (statusId: string | number) => {
  dragOverStatusId.value = idKey(statusId);
};

const handleDragEnd = () => {
  dragStatusId.value = null;
  dragOverStatusId.value = null;
};

const handleDrop = (targetStatusId: string | number) => {
  const dragged = dragStatusId.value;
  const target = idKey(targetStatusId);
  dragOverStatusId.value = null;
  if (!dragged || dragged === target) return;
  const next = [...statusOrder.value];
  const fromIndex = next.indexOf(dragged);
  const targetIndex = next.indexOf(target);
  if (fromIndex < 0 || targetIndex < 0) return;
  next.splice(fromIndex, 1);
  next.splice(targetIndex, 0, dragged);
  statusOrder.value = next;
  persistStatusOrder();
  handleDragEnd();
};

onMounted(async () => {
  loadStatusOrder();
  await ensureStatuses();
});

watch(
  statusList,
  () => {
    syncStatusOrderWithList();
  },
  { immediate: true }
);
</script>
