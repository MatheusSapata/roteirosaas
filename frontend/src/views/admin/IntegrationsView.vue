<template>
  <div v-if="isBootstrappingIntegrations" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>

  <div v-else class="w-full space-y-6 px-4 py-6 md:px-8">
    <header class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-slate-900">{{ viewCopy.header.title }}</h1>
        <p class="mt-1 text-sm text-slate-600">{{ viewCopy.header.description }}</p>
      </div>

      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-[10px] bg-[#3DCC5F] px-4 py-[9px] text-[13px] font-semibold text-[#0F1F14] transition hover:bg-[#5BE07A]"
        :disabled="isReadOnly"
        @click="prepareNewIntegration"
      >
        <span class="text-[15px] leading-none font-bold">+</span>
        {{ viewCopy.actions.new }}
      </button>
    </header>

    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <p class="text-sm font-semibold text-slate-700">
        {{ viewCopy.summary.label }}: <span class="text-slate-900">{{ pixels.length }}</span>
      </p>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <div class="mb-4 flex items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-slate-900">{{ viewCopy.list.title }}</h2>
      </div>

      <div v-if="!pixels.length" class="rounded-xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
        {{ viewCopy.list.empty }}
      </div>

      <div v-else class="space-y-3">
        <article
          v-for="pixel in pixels"
          :key="pixel.id"
          class="integration-item flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 transition hover:-translate-y-[1px] hover:shadow-md md:flex-row md:items-center md:justify-between"
        >
          <div class="min-w-0">
            <span
              class="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
              :class="pixel.type === 'meta' ? 'bg-blue-100 text-blue-700' : 'bg-rose-100 text-rose-700'"
            >
              {{ pixel.type === "meta" ? viewCopy.list.typeMeta : viewCopy.list.typeGa }}
            </span>

            <p class="mt-2 text-base font-semibold text-slate-900">{{ pixel.name }}</p>
            <p class="mt-1 text-sm text-slate-500">{{ viewCopy.list.codePrefix }} {{ maskedCode(pixel.value) }}</p>
          </div>

          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded-xl border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              :disabled="isReadOnly"
              @click="editPixel(pixel)"
            >
              {{ viewCopy.actions.edit }}
            </button>
            <button
              type="button"
              class="rounded-xl border border-rose-200 px-3 py-1.5 text-sm font-semibold text-rose-600 transition hover:bg-rose-50"
              :disabled="isReadOnly"
              @click="removePixel(pixel)"
            >
              {{ viewCopy.actions.remove }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="modalOpen" class="fixed inset-0 z-[180] flex items-center justify-center bg-slate-900/45 px-4">
        <div class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl md:p-5">
          <div class="mb-4 flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.form.eyebrow }}</p>
            <button type="button" class="rounded-full border border-slate-200 p-2 text-slate-500 hover:bg-slate-50" @click="closeModal">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M6 18 18 6" stroke-linecap="round" /></svg>
            </button>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-2 md:col-span-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.form.nameLabel }}</span>
              <input v-model="nameInput" type="text" :placeholder="viewCopy.form.namePlaceholder" :disabled="!canSubmit" class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:cursor-not-allowed disabled:bg-slate-100" />
            </label>
            <label class="space-y-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.form.platformLabel }}</span>
              <select v-model="typeInput" :disabled="!canSubmit" class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:cursor-not-allowed disabled:bg-slate-100">
                <option value="meta">{{ viewCopy.form.platformOptions.meta }}</option>
                <option value="ga">{{ viewCopy.form.platformOptions.ga }}</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ viewCopy.form.codeLabel }}</span>
              <input v-model="idInput" type="text" :placeholder="viewCopy.form.codePlaceholder" :disabled="!canSubmit" class="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:cursor-not-allowed disabled:bg-slate-100" />
            </label>
          </div>
          <div class="mt-4 flex flex-col-reverse gap-3 border-t border-slate-100 pt-4 md:flex-row md:items-center md:justify-between">
            <p class="text-xs font-semibold text-slate-500">{{ isEditing ? viewCopy.form.editingHint : viewCopy.form.createHint }}</p>
            <div class="flex w-full gap-2 md:w-auto">
              <button v-if="isEditing" type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50" :disabled="saving" @click="cancelEditing">{{ viewCopy.actions.cancel }}</button>
              <button type="button" class="w-full rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50 md:w-auto" :disabled="!canSubmit || saving" @click="savePixel">
                {{ saving ? viewCopy.actions.saving : isEditing ? viewCopy.actions.update : viewCopy.actions.save }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="toastMessage"
        class="fixed left-1/2 top-6 z-[200] -translate-x-1/2 rounded-full border px-4 py-2 text-sm font-semibold shadow-lg"
        :class="toastError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'"
      >
        {{ toastMessage }}
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useAuthStore } from "../../store/useAuthStore";
import api from "../../services/api";
import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";

type PixelType = "meta" | "ga";

interface PixelEntry {
  id?: number | string;
  name: string;
  type: PixelType;
  value: string;
}

const auth = useAuthStore();
const adminLanguage = getAdminLanguage();
const t = createAdminLocalizer(adminLanguage);

const viewCopy = {
  header: {
    title: t({ pt: "Integrações", es: "Integraciones" }),
    description: t({
      pt: "Cadastre códigos Meta ou Google para utilizar nas suas páginas.",
      es: "Registra códigos Meta o Google para usarlos en tus páginas."
    })
  },
  form: {
    eyebrow: t({ pt: "Nova integração", es: "Nueva integración" }),
    nameLabel: t({ pt: "Nome da integração", es: "Nombre de la integración" }),
    namePlaceholder: t({ pt: "Ex.: Roteiro São Paulo", es: "Ej.: Itinerario São Paulo" }),
    platformLabel: t({ pt: "Plataforma", es: "Plataforma" }),
    codeLabel: t({ pt: "Código de acompanhamento", es: "Código de seguimiento" }),
    codePlaceholder: t({ pt: "Ex.: 1234567890 ou G-XXXXXXX", es: "Ej.: 1234567890 o G-XXXXXXX" }),
    platformOptions: {
      meta: t({ pt: "Meta", es: "Meta" }),
      ga: t({ pt: "Google", es: "Google" })
    },
    createHint: t({ pt: "Cadastre o código para usar nas páginas.", es: "Registra el código para usarlo en las páginas." }),
    editingHint: t({ pt: "Editando integração selecionada.", es: "Editando integración seleccionada." })
  },
  summary: {
    label: t({ pt: "Integrações cadastradas", es: "Integraciones registradas" })
  },
  list: {
    title: t({ pt: "Integrações cadastradas", es: "Integraciones registradas" }),
    typeMeta: t({ pt: "Meta", es: "Meta" }),
    typeGa: t({ pt: "Google", es: "Google" }),
    codePrefix: t({ pt: "Código:", es: "Código:" }),
    empty: t({ pt: "Nenhuma integração cadastrada.", es: "No hay integraciones registradas." })
  },
  actions: {
    new: t({ pt: "Nova integração", es: "Nueva integración" }),
    save: t({ pt: "Salvar integração", es: "Guardar integración" }),
    update: t({ pt: "Salvar alterações", es: "Guardar cambios" }),
    saving: t({ pt: "Salvando...", es: "Guardando..." }),
    cancel: t({ pt: "Cancelar", es: "Cancelar" }),
    edit: t({ pt: "Editar", es: "Editar" }),
    remove: t({ pt: "Remover", es: "Eliminar" })
  },
  messages: {
    loadError: t({ pt: "Não foi possível carregar as integrações.", es: "No fue posible cargar las integraciones." }),
    missingFields: t({ pt: "Preencha nome e código da integração.", es: "Completa el nombre y el código de la integración." }),
    saveSuccess: t({ pt: "Integração salva com sucesso.", es: "Integración guardada con éxito." }),
    saveError: t({ pt: "Não foi possível salvar a integração.", es: "No fue posible guardar la integración." }),
    removeSuccess: t({ pt: "Integração removida.", es: "Integración eliminada." }),
    removeError: t({ pt: "Não foi possível remover a integração.", es: "No fue posible eliminar la integración." }),
    confirmRemove: t({ pt: "Remover esta integração?", es: "¿Eliminar esta integración?" }),
    readOnly: t({ pt: "Seu perfil permite apenas visualização.", es: "Tu perfil permite solo visualización." })
  }
};

const nameInput = ref("");
const typeInput = ref<PixelType>("meta");
const idInput = ref("");
const pixels = ref<PixelEntry[]>([]);
const saving = ref(false);
const isBootstrappingIntegrations = ref(true);
const editingId = ref<string | number | null>(null);
const modalOpen = ref(false);

const toastMessage = ref("");
const toastError = ref(false);
let toastTimer: ReturnType<typeof setTimeout> | null = null;

const isReadOnly = computed(() => {
  const user = auth.user;
  if (!user) return false;
  if (user.is_owner ?? true) return false;
  return (user.role || "member").toLowerCase() === "viewer";
});

const canSubmit = computed(() => !isReadOnly.value);
const isEditing = computed(() => editingId.value !== null);

const showToast = (message: string, error = false) => {
  toastMessage.value = message;
  toastError.value = error;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = "";
    toastError.value = false;
  }, 2600);
};

const fetchPixels = async () => {
  try {
    const res = await api.get("/pixels/");
    pixels.value = Array.isArray(res.data) ? res.data : [];
  } catch (err) {
    console.error(err);
    showToast(viewCopy.messages.loadError, true);
  }
};

const resetForm = () => {
  editingId.value = null;
  nameInput.value = "";
  typeInput.value = "meta";
  idInput.value = "";
};

const prepareNewIntegration = () => {
  if (isReadOnly.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }
  resetForm();
  modalOpen.value = true;
};

const editPixel = (pixel: PixelEntry) => {
  if (isReadOnly.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }
  editingId.value = pixel.id || null;
  nameInput.value = pixel.name;
  typeInput.value = pixel.type;
  idInput.value = pixel.value;
  modalOpen.value = true;
};

const cancelEditing = () => {
  resetForm();
  modalOpen.value = false;
};

const closeModal = () => {
  if (saving.value) return;
  resetForm();
  modalOpen.value = false;
};

const savePixel = async () => {
  if (!canSubmit.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }

  const name = nameInput.value.trim();
  const value = idInput.value.trim();
  if (!name || !value) {
    showToast(viewCopy.messages.missingFields, true);
    return;
  }

  saving.value = true;
  try {
    if (editingId.value !== null) {
      await api.put(`/pixels/${editingId.value}`, {
        name,
        type: typeInput.value,
        value
      });
    } else {
      await api.post("/pixels/", {
        name,
        type: typeInput.value,
        value
      });
    }

    await fetchPixels();
    resetForm();
    modalOpen.value = false;
    showToast(viewCopy.messages.saveSuccess);
  } catch (err: any) {
    console.error(err);
    showToast(err?.response?.data?.detail || viewCopy.messages.saveError, true);
  } finally {
    saving.value = false;
  }
};

const removePixel = async (pixel: PixelEntry) => {
  if (!pixel.id) return;
  if (isReadOnly.value) {
    showToast(viewCopy.messages.readOnly, true);
    return;
  }

  const confirmed = window.confirm(viewCopy.messages.confirmRemove);
  if (!confirmed) return;

  try {
    await api.delete(`/pixels/${pixel.id}`);
    if (editingId.value === pixel.id) resetForm();
    await fetchPixels();
    showToast(viewCopy.messages.removeSuccess);
  } catch (err) {
    console.error(err);
    showToast(viewCopy.messages.removeError, true);
  }
};

const maskedCode = (raw: string) => {
  const value = String(raw || "").trim();
  if (!value) return "-";
  if (value.length <= 4) return `${value.slice(0, 1)}••`;

  if (value.toUpperCase().startsWith("G-")) {
    const tail = value.slice(2);
    if (tail.length <= 2) return `G-${tail}••`;
    return `G-${tail.slice(0, 2)}••••`;
  }

  const start = value.slice(0, 3);
  const end = value.slice(-3);
  return `${start}••••${end}`;
};

onMounted(async () => {
  try {
    await fetchPixels();
  } finally {
    isBootstrappingIntegrations.value = false;
  }
});
</script>
