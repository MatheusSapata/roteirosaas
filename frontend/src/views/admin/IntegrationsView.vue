<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="space-y-1">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500 dark:text-white/70">Integrações de anúncios</p>
      <h1 class="text-3xl font-bold text-slate-900 dark:text-white">Conexões com Facebook e Google</h1>
      <p class="text-sm text-slate-600 dark:text-slate-200">
        Conecte sua página ao Facebook ou Google para acompanhar quem visitou e melhorar seus anúncios.
      </p>
    </header>

    <div
      class="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md dark:border-[#2b2b2b] dark:bg-[#202020]"
      :class="isFree ? 'opacity-60' : ''"
    >
      <div class="grid gap-6 p-6 md:grid-cols-3">
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700 dark:text-white">Nome da conexão</p>
          <input
            v-model="nameInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 dark:border-[#3a3a3a] dark:bg-[#101010] dark:text-white"
            placeholder="Ex.: Roteiro São Paulo"
            :disabled="!canEdit"
          />
        </div>
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700 dark:text-white">Plataforma</p>
          <select
            v-model="typeInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 dark:border-[#3a3a3a] dark:bg-[#101010] dark:text-white"
            :disabled="!canEdit"
          >
            <option value="meta">Meta</option>
            <option value="ga">Google</option>
          </select>
        </div>
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700 dark:text-white">Código de acompanhamento</p>
          <input
            v-model="idInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 dark:border-[#3a3a3a] dark:bg-[#101010] dark:text-white"
            placeholder="Ex.: 123456789012345 ou G-XXXX"
            :disabled="!canEdit"
          />
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/70 px-6 py-4 text-sm text-slate-700 dark:border-[#2b2b2b] dark:bg-[#161616] dark:text-slate-100">
        <div class="flex flex-wrap items-center gap-3">
          <span class="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-white dark:text-black">Limite: {{ limitLabel }}</span>
          <span class="text-slate-500 dark:text-slate-300">Conexões cadastradas: {{ pixels.length }}{{ limitLabelSuffix }}</span>
        </div>
        <button
          class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:opacity-50"
          @click="savePixel"
          :disabled="!canEdit"
        >
          Salvar conexão
        </button>
      </div>
      <div class="px-6 pb-2 text-xs text-slate-500 dark:text-slate-300">
        Você pode conectar conforme o seu plano.
      </div>

      <div class="px-6 pb-6">
        <p class="text-sm font-semibold text-slate-700 mb-2 dark:text-white">Conexões cadastradas</p>
        <div class="grid gap-3 md:grid-cols-2">
          <div
            v-for="(p, idx) in pixels"
            :key="idx"
            class="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-[#2b2b2b] dark:bg-[#181818]"
          >
            <div class="text-sm text-slate-800 dark:text-slate-100">
              <p class="font-semibold">{{ p.name }} · {{ p.type === 'meta' ? 'Facebook' : 'Google' }}</p>
              <p class="text-slate-600 dark:text-slate-300">{{ p.value }}</p>
            </div>
            <button
              class="text-sm font-semibold text-rose-600 hover:text-rose-500 disabled:opacity-50"
              @click="removePixel(idx)"
              :disabled="!canEdit"
            >
              Remover
            </button>
          </div>
          <p v-if="!pixels.length" class="text-sm text-slate-500 dark:text-slate-400">Nenhuma conexão cadastrada.</p>
        </div>
      </div>

      <div
        v-if="isFree"
        class="absolute inset-0 flex items-center justify-center bg-white/70 backdrop-blur-sm dark:bg-black/60"
      >
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-center shadow-md dark:bg-[#052e16] dark:text-emerald-50">
          <p class="text-sm font-semibold text-emerald-800 dark:text-emerald-100">Disponível a partir do plano Essencial</p>
          <p class="text-xs text-emerald-700 mt-1 dark:text-emerald-200/80">Faça upgrade para habilitar integrações.</p>
        </div>
      </div>
    </div>

    <p v-if="errorMessage" class="text-sm font-semibold text-rose-600">{{ errorMessage }}</p>
    <p v-if="message" class="text-sm font-semibold text-emerald-600">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { useAuthStore } from "../../store/useAuthStore";
import api from "../../services/api";

type PixelType = "meta" | "ga";
interface PixelEntry {
  name: string;
  type: PixelType;
  value: string;
}

const auth = useAuthStore();
const nameInput = ref("");
const typeInput = ref<PixelType>("meta");
const idInput = ref("");
const pixels = ref<PixelEntry[]>([]);
const message = ref("");
const errorMessage = ref("");

const plan = computed(() => auth.user?.plan || "free");
const isFree = computed(() => plan.value === "free");

const limit = computed(() => {
  if (plan.value === "free") return 0;
  if (plan.value === "essencial") return 1;
  if (plan.value === "growth") return 3;
  return Infinity;
});
const limitLabel = computed(() => (limit.value === Infinity ? "Conforme o plano" : `${limit.value}`));
const limitLabelSuffix = computed(() => (limit.value === Infinity ? "" : ` / ${limitLabel.value}`));
const canEdit = computed(() => limit.value > 0 && pixels.value.length < limit.value);

const storageKey = computed(() => (auth.user ? `pixels_${auth.user.id}` : null));

const persist = () => {
  if (!storageKey.value) return;
  localStorage.setItem(storageKey.value, JSON.stringify(pixels.value));
};
const load = () => {
  if (!storageKey.value) return;
  const saved = localStorage.getItem(storageKey.value);
  if (saved) {
    try {
      pixels.value = JSON.parse(saved);
    } catch {
      pixels.value = [];
    }
  }
};

watch(pixels, persist, { deep: true });

const fetchPixels = async () => {
  errorMessage.value = "";
  try {
  const res = await api.get("/pixels/");
    pixels.value = res.data;
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possível carregar as conexões.";
  }
};

const savePixel = async () => {
  errorMessage.value = "";
  message.value = "";
  if (!canEdit.value) {
    errorMessage.value = "Limite de conexões atingido para seu plano.";
    return;
  }
  if (!nameInput.value.trim() || !idInput.value.trim()) {
    errorMessage.value = "Preencha nome e código da conexão.";
    return;
  }
  try {
    await api.post("/pixels/", { name: nameInput.value.trim(), type: typeInput.value, value: idInput.value.trim() });
    await fetchPixels();
    nameInput.value = "";
    idInput.value = "";
    message.value = "Conexão salva.";
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || "Erro ao salvar conexão.";
  }
};

const removePixel = async (idx: number) => {
  const pixel = pixels.value[idx];
  if (!pixel) return;
  try {
    await api.delete(`/pixels/${pixel.id}`);
    await fetchPixels();
    message.value = "Conexão removida.";
  } catch (err) {
    console.error(err);
    errorMessage.value = "Erro ao remover conexão.";
  }
};

onMounted(() => {
  fetchPixels();
});
</script>
