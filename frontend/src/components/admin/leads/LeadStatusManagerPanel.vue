<template>
  <section class="space-y-6">
    <header class="flex flex-col gap-2 border-b border-slate-100 pb-4 dark:border-white/10">
      
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Configurações de status</h2>
      <p class="text-sm text-slate-500 dark:text-slate-300">
        Crie, edite e personalize os status utilizados para organizar seus contatos.
      </p>
    </header>

    <div class="space-y-6">
      <div>
        <p class="text-sm font-semibold text-slate-700 dark:text-slate-100">Status existentes</p>
        <p v-if="loading && !statusList.length" class="mt-2 text-sm text-slate-500">Carregando status...</p>
        <p v-else-if="!statusList.length" class="mt-2 text-sm text-slate-500">Nenhum status cadastrado ainda.</p>
        <ul v-else class="mt-3 space-y-2">
          <li
            v-for="status in statusList"
            :key="status.id"
            class="flex flex-col gap-4 rounded-2xl border border-slate-100 px-4 py-3 dark:border-white/10 md:flex-row md:items-center md:justify-between"
          >
            <div class="flex flex-1 flex-col gap-3 md:flex-row md:items-center md:gap-4">
              <label class="relative flex h-12 w-12 items-center justify-center">
                <input
                  type="color"
                  v-model="editableColors[idKey(status.id)]"
                  aria-label="Selecionar cor do status"
                  class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                />
                <span
                  class="block h-10 w-10 rounded-full border border-slate-200 dark:border-white/10"
                  :style="{ backgroundColor: editableColors[idKey(status.id)] || status.color }"
                ></span>
              </label>
              <input
                v-model="editableNames[idKey(status.id)]"
                type="text"
                class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand/50 dark:border-white/10 dark:bg-transparent"
              />
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/20 dark:text-white dark:hover:bg-white/10"
                :disabled="!canSave(status) || savingMap[idKey(status.id)]"
                @click="handleUpdateStatus(status)"
              >
                {{ savingMap[idKey(status.id)] ? "Salvando..." : "Salvar" }}
              </button>
              <button
                type="button"
                class="rounded-full border border-rose-200 px-4 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-rose-500/40 dark:text-rose-200 dark:hover:bg-rose-500/10"
                :disabled="deletingMap[idKey(status.id)]"
                @click="handleDeleteStatus(status)"
              >
                {{ deletingMap[idKey(status.id)] ? "Excluindo..." : "Excluir" }}
              </button>
            </div>
          </li>
        </ul>
      </div>

      <div class="border-t border-slate-100 pt-4 dark:border-white/10">
        <p class="text-sm	font-semibold text-slate-700 dark:text-slate-100">Adicionar novo status</p>
        <div class="mt-3 flex flex-col gap-3 md:flex-row md:items-center">
          <label class="relative block h-10 w-10 cursor-pointer">
            <input
              v-model="newStatusColor"
              type="color"
              aria-label="Selecionar cor do novo status"
              class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            />
            <span class="block h-full w-full rounded-full border border-slate-200 dark:border-white/10" :style="{ backgroundColor: newStatusColor }"></span>
          </label>
          <input
            v-model="newStatusName"
            type="text"
            placeholder="Nome do status"
            class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand/50 dark:border-white/10 dark:bg-transparent"
          />
          <button
            type="button"
            class="rounded-full bg-brand px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white shadow transition hover:bg-brand-dark disabled:opacity-60"
            :disabled="!newStatusName.trim() || creating"
            @click="handleCreateStatus"
          >
            {{ creating ? "Criando..." : "Adicionar" }}
          </button>
        </div>
      </div>

      <div
        v-if="feedback.text"
        class="rounded-2xl border px-4 py-2 text-sm"
        :class="feedback.error ? 'border-rose-200 bg-rose-50 text-rose-600 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200' : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-500/10 dark:text-emerald-100'"
      >
        {{ feedback.text }}
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import type { LeadStatus } from "../../../types/leads";
import { useLeadCaptureStore } from "../../../store/useLeadCaptureStore";

const leadStore = useLeadCaptureStore();
const defaultStatusColor = "#22c55e";

const newStatusName = ref("");
const newStatusColor = ref(defaultStatusColor);
const creating = ref(false);
const feedback = ref<{ text: string; error: boolean }>({ text: "", error: false });
const editableNames = reactive<Record<string, string>>({});
const editableColors = reactive<Record<string, string>>({});
const savingMap = reactive<Record<string, boolean>>({});
const deletingMap = reactive<Record<string, boolean>>({});

const statusList = computed(() => leadStore.statuses);
const loading = computed(() => leadStore.statusesLoading);

const idKey = (value: string | number) => String(value);

const setFeedback = (text = "", error = false) => {
  feedback.value = { text, error };
  if (text) {
    setTimeout(() => (feedback.value = { text: "", error: false }), 3000);
  }
};

const ensureStatuses = () =>
  leadStore.fetchStatuses().catch(() => setFeedback("Não foi possível carregar os status.", true));

onMounted(() => ensureStatuses());

watch(
  statusList,
  list => {
    const keys = new Set(list.map(status => idKey(status.id)));
    list.forEach(status => {
      const key = idKey(status.id);
      editableNames[key] = status.name;
      editableColors[key] = status.color;
    });
    Object.keys(editableNames).forEach(key => {
      if (!keys.has(key)) delete editableNames[key];
    });
    Object.keys(editableColors).forEach(key => {
      if (!keys.has(key)) delete editableColors[key];
    });
  },
  { immediate: true }
);

const normalizeColor = (value?: string | null) => (value || "").trim().toLowerCase();

const handleCreateStatus = async () => {
  const name = newStatusName.value.trim();
  const color = newStatusColor.value || defaultStatusColor;
  if (!name || creating.value) return;
  creating.value = true;
  try {
    await leadStore.createStatus({ name, color });
    newStatusName.value = "";
    newStatusColor.value = defaultStatusColor;
    setFeedback("Status criado com sucesso.");
  } catch (err) {
    console.error(err);
    setFeedback("Não foi possível criar o status.", true);
  } finally {
    creating.value = false;
  }
};

const canSave = (status: LeadStatus) => {
  const key = idKey(status.id);
  const nextName = (editableNames[key] || "").trim();
  if (!nextName) return false;
  const nextColor = editableColors[key] || status.color;
  return nextName !== status.name || normalizeColor(nextColor) !== normalizeColor(status.color);
};

const handleUpdateStatus = async (status: LeadStatus) => {
  const key = idKey(status.id);
  if (!canSave(status) || savingMap[key]) return;
  savingMap[key] = true;
  try {
    await leadStore.updateStatus(status.id, {
      name: (editableNames[key] || status.name).trim(),
      color: editableColors[key] || status.color || defaultStatusColor
    });
    setFeedback("Status atualizado.");
  } catch (err) {
    console.error(err);
    setFeedback("Erro ao atualizar status.", true);
  } finally {
    savingMap[key] = false;
  }
};

const handleDeleteStatus = async (status: LeadStatus) => {
  const key = idKey(status.id);
  if (deletingMap[key]) return;
  const confirmed = window.confirm(`Excluir o status "${status.name}"?`);
  if (!confirmed) return;
  deletingMap[key] = true;
  try {
    await leadStore.deleteStatus(status.id);
    delete editableNames[key];
    delete editableColors[key];
    setFeedback("Status removido.");
  } catch (err) {
    console.error(err);
    setFeedback("Não foi possível remover o status.", true);
  } finally {
    deletingMap[key] = false;
  }
};
</script>
