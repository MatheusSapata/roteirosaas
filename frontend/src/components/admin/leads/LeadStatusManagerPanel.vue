<template>
  <section class="pipeline-settings space-y-5">
    <section class="list-card p-4 md:p-5">
      <div class="pipeline-card-header">
        <div>
          <p class="pipeline-eyebrow">FUNIL COMERCIAL</p>
          <h3>{{ viewCopy.pipeline.title }}</h3>
          <p>{{ viewCopy.pipeline.helper }}</p>
        </div>
        <span class="pipeline-summary">{{ orderedStatuses.length }} etapas</span>
      </div>

      <div
        v-if="loading && !orderedStatuses.length"
        class="pipeline-empty-state"
      >
        {{ viewCopy.pipeline.loading }}
      </div>
      <div
        v-else-if="!orderedStatuses.length"
        class="pipeline-empty-state"
      >
        {{ viewCopy.pipeline.empty }}
      </div>

      <ul v-else class="pipeline-list">
        <li
          v-for="(status, index) in orderedStatuses"
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
                <div class="flex items-center gap-3">
                  <span class="pipeline-color-dot" aria-hidden="true"></span>
                  <div class="min-w-0">
                    <p class="pipeline-name">{{ status.name }}</p>
                    <p class="pipeline-position">Etapa {{ index + 1 }} do funil</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-2 self-end md:self-start">
              <button
                type="button"
                class="pipeline-action-btn"
                :disabled="savingMap[idKey(status.id)]"
                @click="openEditModal(status)"
              >
                {{ savingMap[idKey(status.id)] ? viewCopy.actions.saving : viewCopy.actions.edit }}
              </button>

              <button
                type="button"
                class="pipeline-action-btn"
                @click="handleDuplicateStatus(status)"
              >
                {{ viewCopy.actions.duplicate }}
              </button>

              <button
                v-if="canDelete"
                type="button"
                class="pipeline-action-btn pipeline-action-btn--danger"
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
        <div class="pipeline-modal-shell w-full max-w-xl p-6">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="pipeline-modal-eyebrow">{{ viewCopy.modal.eyebrow }}</p>
              <h3 class="mt-2 text-2xl font-bold">
                {{ statusModalMode === "create" ? viewCopy.modal.createTitle : viewCopy.modal.editTitle }}
              </h3>
            </div>
            <button type="button" class="pipeline-modal-close" @click="closeStatusModal">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>

          <div class="mt-5 grid gap-4">
            <label class="block">
              <span class="pipeline-modal-label">{{ viewCopy.modal.nameLabel }}</span>
              <input
                v-model="statusModalName"
                type="text"
                :placeholder="viewCopy.modal.namePlaceholder"
                class="pipeline-modal-input mt-2 w-full px-4 py-2.5 text-sm outline-none transition"
              />
            </label>

            <div>
              <span class="pipeline-modal-label">{{ viewCopy.modal.colorLabel }}</span>
              <div class="mt-2 flex items-center gap-3">
                <label class="pipeline-color-picker relative block h-10 w-10 cursor-pointer overflow-hidden">
                  <input v-model="statusModalColor" type="color" :aria-label="viewCopy.modal.colorAria" class="absolute inset-0 h-full w-full cursor-pointer opacity-0" />
                  <span class="block h-full w-full" :style="{ backgroundColor: statusModalColor }"></span>
                </label>
                <p class="pipeline-color-code">{{ statusModalColor }}</p>
              </div>
            </div>

            <label v-if="statusModalMode === 'create'" class="block">
              <span class="pipeline-modal-label">{{ viewCopy.modal.positionLabel }}</span>
              <select
                v-model="statusModalPosition"
                class="pipeline-modal-input mt-2 w-full px-4 py-2.5 text-sm outline-none transition"
              >
                <option value="end">{{ viewCopy.modal.positionEnd }}</option>
                <option v-for="(option, index) in orderedStatuses" :key="option.id" :value="String(index)">
                  {{ viewCopy.modal.positionBefore }} {{ option.name }}
                </option>
              </select>
            </label>
          </div>

          <div class="mt-6 flex justify-end gap-2">
            <button type="button" class="pipeline-modal-cancel" @click="closeStatusModal">
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
    loading: t({ pt: "Carregando etapas...", es: "Cargando etapas..." }),
    empty: t({ pt: "Nenhuma etapa cadastrada.", es: "No hay etapas registradas." }),
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
    loadError: t({ pt: "Não foi possível carregar as etapas.", es: "No fue posible cargar las etapas." }),
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
  border-radius: var(--radius-xl);
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-soft);
}

.pipeline-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.pipeline-card-header h3 {
  margin-top: 0.25rem;
  color: var(--foreground);
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 650;
}

.pipeline-card-header > div > p:last-child,
.pipeline-position {
  color: var(--muted-foreground);
  font-size: 0.8125rem;
}

.pipeline-eyebrow,
.pipeline-modal-eyebrow,
.pipeline-modal-label {
  color: var(--muted-foreground);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.pipeline-summary {
  flex: none;
  border: 1px solid color-mix(in srgb, var(--primary) 25%, var(--border));
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary) 10%, var(--card));
  color: var(--primary);
  padding: 0.35rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 700;
}

.pipeline-list {
  display: grid;
  gap: 0.625rem;
}

.pipeline-empty-state {
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  background: var(--muted);
  color: var(--muted-foreground);
  padding: 2rem 1rem;
  text-align: center;
  font-size: 0.875rem;
}

.btn-brand {
  background: var(--primary);
  color: var(--primary-foreground);
  box-shadow: var(--shadow-soft);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.btn-brand:hover {
  transform: translateY(-1px);
  filter: brightness(0.98);
}

.pipeline-card {
  border-radius: 1rem;
  border: 1px solid var(--border);
  border-left: 4px solid var(--status-color);
  background: var(--background);
  padding: 1rem;
  box-shadow: 0 10px 24px -26px rgb(0 0 0 / 45%);
  transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
}

.pipeline-card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--foreground) 15%, var(--border));
  box-shadow: var(--shadow-soft);
}

.pipeline-card.is-dragging {
  transform: scale(1.02);
  opacity: 0.92;
  z-index: 10;
  box-shadow: 0 30px 40px -28px rgba(15, 23, 42, 0.5);
}

.pipeline-card.is-drag-over {
  border-style: dashed;
  border-color: color-mix(in srgb, var(--primary) 65%, var(--border));
  background: color-mix(in srgb, var(--primary) 5%, var(--background));
}

.pipeline-color-dot {
  display: block;
  flex: none;
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 999px;
  background: var(--status-color);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--status-color) 16%, transparent);
}

.pipeline-name {
  overflow: hidden;
  color: var(--foreground);
  font-size: 0.9375rem;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drag-handle {
  margin-top: 0.1rem;
  display: inline-flex;
  height: 2rem;
  width: 2rem;
  align-items: center;
  justify-content: center;
  border-radius: 0.6rem;
  border: 1px solid var(--border);
  background: var(--muted);
  color: var(--muted-foreground);
  cursor: grab;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle:hover {
  background: var(--accent);
  color: var(--foreground);
}

.pipeline-action-btn,
.pipeline-modal-cancel {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--background);
  color: var(--foreground);
  padding: 0.4rem 0.8rem;
  font-size: 0.75rem;
  font-weight: 650;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.pipeline-action-btn:hover,
.pipeline-modal-cancel:hover {
  background: var(--accent);
  border-color: color-mix(in srgb, var(--foreground) 15%, var(--border));
}

.pipeline-action-btn--danger {
  border-color: color-mix(in srgb, var(--destructive) 30%, var(--border));
  background: color-mix(in srgb, var(--destructive) 9%, var(--background));
  color: var(--destructive);
}

.pipeline-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.pipeline-modal-shell {
  border: 1px solid var(--border);
  border-radius: 1.5rem;
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-xl);
}

.pipeline-modal-shell h3 {
  color: var(--foreground);
  font-family: var(--font-display);
}

.pipeline-modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  background: var(--muted);
  color: var(--muted-foreground);
  padding: 0.5rem;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.pipeline-modal-close:hover {
  background: var(--accent);
  color: var(--foreground);
}

.pipeline-modal-label {
  display: inline-block;
  letter-spacing: 0.08em;
}

.pipeline-modal-input,
.pipeline-color-picker,
.pipeline-color-code {
  border: 1px solid var(--input);
  border-radius: 0.75rem;
  background: var(--background);
  color: var(--foreground);
}

.pipeline-modal-input:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent);
}

.pipeline-modal-input option {
  background: var(--popover);
  color: var(--popover-foreground);
}

.pipeline-color-code {
  padding: 0.4rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.pipeline-modal-cancel {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}
</style>
