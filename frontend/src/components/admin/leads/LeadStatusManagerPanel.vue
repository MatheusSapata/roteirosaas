<template>
  <section class="pipeline-settings space-y-5">
    <section class="list-card p-4 md:p-5">
      <div class="mb-4">
        <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.pipeline.title }}</h3>
        <p class="text-sm text-slate-500">{{ viewCopy.pipeline.helper }}</p>
      </div>

      <div
        v-if="loading && !orderedStatuses.length"
        class="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500"
      >
        {{ viewCopy.pipeline.loading }}
      </div>
      <div
        v-else-if="!orderedStatuses.length"
        class="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500"
      >
        {{ viewCopy.pipeline.empty }}
      </div>

      <ul v-else class="space-y-3">
        <li
          v-for="status in orderedStatuses"
          :key="status.id"
          class="pipeline-card group"
          :class="{
            'is-drag-over': dragOverStatusId === idKey(status.id),
            'is-dragging': dragStatusId === idKey(status.id)
          }"
          :style="{ '--status-color': status.color || defaultStatusColor }"
          draggable="true"
          @dragstart="handleDragStart(status.id)"
          @dragenter.prevent="handleDragEnter(status.id)"
          @dragover.prevent="handleDragEnter(status.id)"
          @dragend="handleDragEnd"
          @drop.prevent="handleDrop(status.id)"
        >
          <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div class="flex min-w-0 flex-1 gap-3">
              <button
                type="button"
                class="drag-handle"
                :aria-label="viewCopy.pipeline.dragAria"
                @mousedown.prevent
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="currentColor">
                  <path d="M9 5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m9-14a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0m0 7a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0" />
                </svg>
              </button>

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
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-2 self-end md:self-start">
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
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                @click="handleDuplicateStatus(status)"
              >
                {{ viewCopy.actions.duplicate }}
              </button>

              <button
                v-if="canDelete"
                type="button"
                class="rounded-full border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-100 disabled:opacity-60"
                :disabled="deletingMap[idKey(status.id)]"
                @click="handleDeleteStatus(status)"
              >
                {{ deletingMap[idKey(status.id)] ? viewCopy.actions.deleting : viewCopy.actions.delete }}
              </button>
            </div>
          </div>
        </li>
      </ul>
    </section>

    <Teleport to="body">
      <div v-if="statusModalOpen" class="app-modal-overlay fixed inset-0 z-[170] flex items-center justify-center px-4">
        <div class="w-full max-w-xl rounded-[28px] border border-slate-200 bg-white p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">{{ viewCopy.modal.eyebrow }}</p>
              <h3 class="mt-2 text-2xl font-bold text-slate-900">
                {{ statusModalMode === "create" ? viewCopy.modal.createTitle : viewCopy.modal.editTitle }}
              </h3>
            </div>
            <button type="button" class="rounded-full border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-50" @click="closeStatusModal">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>

          <div class="mt-5 grid gap-4">
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
                  <input v-model="statusModalColor" type="color" :aria-label="viewCopy.modal.colorAria" class="absolute inset-0 h-full w-full cursor-pointer opacity-0" />
                  <span class="block h-full w-full" :style="{ backgroundColor: statusModalColor }"></span>
                </label>
                <p class="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600">{{ statusModalColor }}</p>
              </div>
            </div>

            <label v-if="statusModalMode === 'create'" class="block">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.modal.positionLabel }}</span>
              <select
                v-model="statusModalPosition"
                class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
              >
                <option value="end">{{ viewCopy.modal.positionEnd }}</option>
                <option v-for="(option, index) in orderedStatuses" :key="option.id" :value="String(index)">
                  {{ viewCopy.modal.positionBefore }} {{ option.name }}
                </option>
              </select>
            </label>
          </div>

          <div class="mt-6 flex justify-end gap-2">
            <button type="button" class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50" @click="closeStatusModal">
              {{ viewCopy.modal.cancel }}
            </button>
            <button
              type="button"
              class="btn-brand rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-60"
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
import { useAuthStore } from "../../../store/useAuthStore";
import { API_PERMISSION_DENIED_EVENT } from "../../../services/api";
import { createAdminLocalizer, getAdminLanguage } from "../../../utils/adminI18n";

const leadStore = useLeadCaptureStore();
const authStore = useAuthStore();
const props = withDefaults(defineProps<{ canDelete?: boolean }>(), { canDelete: true });

const canDelete = computed(() => props.canDelete);
const canManageLeads = computed(() => {
  const user = authStore.user;
  if (!user) return true;
  if (user.is_owner ?? true) return true;
  if ((user.role || "member").toLowerCase() === "admin") return true;
  const effective = user.effective_permissions || [];
  return effective.includes("leads_manager") || effective.includes("leads_full");
});

const defaultStatusColor = "#22c55e";
const statusOrderStorageKey = "lead_status_pipeline_order_v1";

const adminLanguage = getAdminLanguage();
const t = createAdminLocalizer(adminLanguage);

const viewCopy = {
  header: {
    title: t({ pt: "Configurações de pipeline", es: "Configuración del pipeline" }),
    description: t({ pt: "Organize o funil comercial e defina a ordem das etapas.", es: "Organiza el embudo comercial y define el orden de las etapas." })
  },
  pipeline: {
    title: t({ pt: "Ordem do funil", es: "Orden del embudo" }),
    helper: t({ pt: "Arraste para definir a ordem das etapas", es: "Arrastra para definir el orden de las etapas" }),
    loading: t({ pt: "Carregando status...", es: "Cargando estados..." }),
    empty: t({ pt: "Nenhum status cadastrado.", es: "No hay estados registrados." }),
    dragAria: t({ pt: "Reordenar etapa", es: "Reordenar etapa" })
  },
  actions: {
    newStatus: t({ pt: "Nova etapa do funil", es: "Nueva etapa del embudo" }),
    edit: t({ pt: "Editar", es: "Editar" }),
    duplicate: t({ pt: "Duplicar", es: "Duplicar" }),
    delete: t({ pt: "Excluir", es: "Eliminar" }),
    deleting: t({ pt: "Excluindo...", es: "Eliminando..." }),
    saving: t({ pt: "Salvando...", es: "Guardando..." })
  },
  badges: {
    won: t({ pt: "Ganho", es: "Ganado" }),
    lost: t({ pt: "Perdido", es: "Perdido" })
  },
  modal: {
    eyebrow: t({ pt: "Etapa", es: "Etapa" }),
    createTitle: t({ pt: "Nova etapa do pipeline", es: "Nueva etapa del pipeline" }),
    editTitle: t({ pt: "Editar etapa", es: "Editar etapa" }),
    nameLabel: t({ pt: "Nome da etapa", es: "Nombre de la etapa" }),
    namePlaceholder: t({ pt: "Ex: Proposta enviada", es: "Ej: Propuesta enviada" }),
    colorLabel: t({ pt: "Cor", es: "Color" }),
    colorAria: t({ pt: "Selecionar cor da etapa", es: "Seleccionar color de la etapa" }),
    positionLabel: t({ pt: "Posição", es: "Posición" }),
    positionEnd: t({ pt: "No fim do funil", es: "Al final del embudo" }),
    positionBefore: t({ pt: "Antes de", es: "Antes de" }),
    cancel: t({ pt: "Cancelar", es: "Cancelar" }),
    createAction: t({ pt: "Criar etapa", es: "Crear etapa" }),
    saveAction: t({ pt: "Salvar alterações", es: "Guardar cambios" }),
    creating: t({ pt: "Criando...", es: "Creando..." }),
    saving: t({ pt: "Salvando...", es: "Guardando..." })
  },
  feedback: {
    loadError: t({ pt: "Não foi possível carregar os status.", es: "No fue posible cargar los estados." }),
    createSuccess: t({ pt: "Etapa criada com sucesso.", es: "Etapa creada con éxito." }),
    createError: t({ pt: "Não foi possível criar a etapa.", es: "No fue posible crear la etapa." }),
    updateSuccess: t({ pt: "Etapa atualizada.", es: "Etapa actualizada." }),
    updateError: t({ pt: "Erro ao atualizar etapa.", es: "Error al actualizar la etapa." }),
    deleteSuccess: t({ pt: "Etapa removida.", es: "Etapa eliminada." }),
    deleteError: t({ pt: "Não foi possível remover a etapa.", es: "No fue posible eliminar la etapa." }),
    reorderSuccess: t({ pt: "Ordem do pipeline atualizada.", es: "Orden del pipeline actualizada." }),
    reorderError: t({ pt: "Não foi possível salvar. Tente novamente.", es: "No fue posible guardar. Intenta nuevamente." }),
    confirmDelete: (name: string) => t({ pt: `Excluir a etapa "${name}"?`, es: `¿Eliminar la etapa "${name}"?` })
  }
};

const statusModalOpen = ref(false);
const statusModalMode = ref<"create" | "edit">("create");
const statusModalTargetId = ref<string | null>(null);
const statusModalName = ref("");
const statusModalColor = ref(defaultStatusColor);
const statusModalPosition = ref<string>("end");
const statusModalSaving = ref(false);

const savingMap = reactive<Record<string, boolean>>({});
const deletingMap = reactive<Record<string, boolean>>({});

const dragStatusId = ref<string | null>(null);
const dragOverStatusId = ref<string | null>(null);
const statusOrder = ref<string[]>([]);

const statusList = computed(() => leadStore.statuses);
const loading = computed(() => leadStore.statusesLoading);

const idKey = (value: string | number) => String(value);

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

const showReadOnlySnackbar = (message = "Seu perfil permite apenas visualização.") => {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(API_PERMISSION_DENIED_EVENT, { detail: { message, status: 403, method: "post" } }));
};

const dispatchToast = (message: string, error = false) => {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(API_PERMISSION_DENIED_EVENT, { detail: { message, status: error ? 500 : 200, method: "post" } }));
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

const ensureStatuses = () => leadStore.fetchStatuses().catch(() => dispatchToast(viewCopy.feedback.loadError, true));

const normalizeName = (value: string) =>
  value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();

const resolveSpecialBadge = (name: string) => {
  const normalized = normalizeName(name);
  if (normalized === "ganho" || normalized === "won") return "won";
  if (normalized === "perdido" || normalized === "lost") return "lost";
  return null;
};

const openCreateModal = () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  statusModalMode.value = "create";
  statusModalTargetId.value = null;
  statusModalName.value = "";
  statusModalColor.value = defaultStatusColor;
  statusModalPosition.value = "end";
  statusModalOpen.value = true;
};

const openEditModal = (status: LeadStatus) => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
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

const insertCreatedStatusInOrder = (createdId: string) => {
  if (statusModalPosition.value === "end") {
    statusOrder.value.push(createdId);
    return;
  }
  const index = Number(statusModalPosition.value);
  if (!Number.isInteger(index) || index < 0 || index > statusOrder.value.length) {
    statusOrder.value.push(createdId);
    return;
  }
  statusOrder.value.splice(index, 0, createdId);
};

const submitStatusModal = async () => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  const name = statusModalName.value.trim();
  const color = statusModalColor.value || defaultStatusColor;
  if (!name || statusModalSaving.value) return;

  statusModalSaving.value = true;
  try {
    if (statusModalMode.value === "create") {
      const created = await leadStore.createStatus({ name, color });
      insertCreatedStatusInOrder(idKey(created.id));
      persistStatusOrder();
      dispatchToast(viewCopy.feedback.createSuccess);
    } else if (statusModalTargetId.value) {
      savingMap[statusModalTargetId.value] = true;
      await leadStore.updateStatus(statusModalTargetId.value, { name, color });
      dispatchToast(viewCopy.feedback.updateSuccess);
    }
    statusModalOpen.value = false;
  } catch (err) {
    console.error(err);
    dispatchToast(statusModalMode.value === "create" ? viewCopy.feedback.createError : viewCopy.feedback.updateError, true);
  } finally {
    if (statusModalTargetId.value) savingMap[statusModalTargetId.value] = false;
    statusModalSaving.value = false;
  }
};

const handleDuplicateStatus = async (status: LeadStatus) => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
  try {
    const created = await leadStore.createStatus({
      name: `${status.name} (cópia)`,
      color: status.color || defaultStatusColor
    });
    const sourceIndex = statusOrder.value.indexOf(idKey(status.id));
    if (sourceIndex >= 0) statusOrder.value.splice(sourceIndex + 1, 0, idKey(created.id));
    else statusOrder.value.push(idKey(created.id));
    persistStatusOrder();
    dispatchToast(viewCopy.feedback.createSuccess);
  } catch (err) {
    console.error(err);
    dispatchToast(viewCopy.feedback.createError, true);
  }
};

const handleDeleteStatus = async (status: LeadStatus) => {
  if (!canDelete.value) {
    dispatchToast("Seu nível gerencial não permite excluir.", true);
    return;
  }
  const key = idKey(status.id);
  if (deletingMap[key]) return;
  const confirmed = window.confirm(viewCopy.feedback.confirmDelete(status.name));
  if (!confirmed) return;
  deletingMap[key] = true;
  try {
    await leadStore.deleteStatus(status.id);
    statusOrder.value = statusOrder.value.filter(id => id !== key);
    persistStatusOrder();
    dispatchToast(viewCopy.feedback.deleteSuccess);
  } catch (err) {
    console.error(err);
    dispatchToast(viewCopy.feedback.deleteError, true);
  } finally {
    deletingMap[key] = false;
  }
};

const handleDragStart = (statusId: string | number) => {
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
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
  if (!canManageLeads.value) {
    showReadOnlySnackbar();
    return;
  }
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
  dispatchToast(viewCopy.feedback.reorderSuccess);
  handleDragEnd();
};

onMounted(async () => {
  loadStatusOrder();
  await ensureStatuses();
});

defineExpose({
  openCreateModal
});

watch(
  statusList,
  () => {
    syncStatusOrderWithList();
  },
  { immediate: true }
);
</script>

<style scoped>
.list-card {
  border-radius: 1.25rem;
  border: 1px solid rgb(226 232 240);
  background: #fff;
  box-shadow: 0 10px 24px -24px rgba(15, 23, 42, 0.45);
}

.btn-brand {
  background: rgb(34 197 94);
  color: #08220f;
  box-shadow: 0 10px 20px -16px rgba(34, 197, 94, 0.8);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.btn-brand:hover {
  transform: translateY(-1px);
  filter: brightness(0.98);
}

.pipeline-card {
  border-radius: 1rem;
  border: 1px solid rgb(226 232 240);
  border-left: 4px solid var(--status-color);
  background: #fff;
  padding: 1rem;
  box-shadow: 0 10px 24px -24px rgba(15, 23, 42, 0.45);
  transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
}

.pipeline-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 20px 30px -24px rgba(15, 23, 42, 0.45);
}

.pipeline-card.is-dragging {
  transform: scale(1.02);
  opacity: 0.92;
  z-index: 10;
  box-shadow: 0 30px 40px -28px rgba(15, 23, 42, 0.5);
}

.pipeline-card.is-drag-over {
  border-style: dashed;
  border-color: rgba(34, 197, 94, 0.65);
  background: rgba(34, 197, 94, 0.03);
}

.drag-handle {
  margin-top: 0.1rem;
  display: inline-flex;
  height: 2rem;
  width: 2rem;
  align-items: center;
  justify-content: center;
  border-radius: 0.6rem;
  border: 1px solid rgb(226 232 240);
  color: rgb(100 116 139);
  cursor: grab;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle:hover {
  background: rgb(248 250 252);
  color: rgb(30 41 59);
}
</style>
