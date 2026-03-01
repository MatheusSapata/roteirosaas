<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="space-y-1">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Integrações de anúncios</p>
      <h1 class="text-3xl font-bold text-slate-900">Conexões com Facebook e Google</h1>
      <p class="text-sm text-slate-600">
        Conecte sua página ao Facebook ou Google para acompanhar quem visitou e melhorar seus anúncios.
      </p>
    </header>

    <div class="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md" :class="isFree ? 'opacity-60' : ''">
      <div class="grid gap-6 p-6 md:grid-cols-3">
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700">Nome da conexão</p>
          <input
            v-model="nameInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800"
            placeholder="Ex.: Roteiro São Paulo"
            :disabled="!canEdit"
          />
        </div>
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700">Plataforma</p>
          <select v-model="typeInput" class="w-full rounded-lg border border-slate-200 px-3 py-2" :disabled="!canEdit">
            <option value="meta">Facebook</option>
            <option value="ga">Google</option>
          </select>
        </div>
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700">Código de acompanhamento</p>
          <input
            v-model="idInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800"
            placeholder="Ex.: 123456789012345 ou G-XXXX"
            :disabled="!canEdit"
          />
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-slate-100 bg-slate-50/70 px-6 py-4 text-sm text-slate-700">
        <div class="flex flex-wrap items-center gap-3">
          <span class="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">Limite: {{ limitLabel }}</span>
          <span class="text-slate-500">Conexões cadastradas: {{ pixels.length }}{{ limitLabelSuffix }}</span>
        </div>
        <button
          class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:opacity-50"
          @click="savePixel"
          :disabled="!canEdit"
        >
          Salvar conexão
        </button>
      </div>
      <div class="px-6 pb-2 text-xs text-slate-500">
        Você pode conectar conforme o seu plano.
      </div>

      <div class="px-6 pb-6">
        <p class="text-sm font-semibold text-slate-700 mb-2">Conexões cadastradas</p>
        <div class="grid gap-3 md:grid-cols-2">
          <div
            v-for="(p, idx) in pixels"
            :key="idx"
            class="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3"
          >
            <div class="text-sm text-slate-800">
              <p class="font-semibold">{{ p.name }} · {{ p.type === 'meta' ? 'Facebook' : 'Google' }}</p>
              <p class="text-slate-600">{{ p.value }}</p>
            </div>
            <button
              class="text-sm font-semibold text-rose-600 hover:text-rose-700 disabled:opacity-50"
              @click="removePixel(idx)"
              :disabled="!canEdit"
            >
              Remover
            </button>
          </div>
          <p v-if="!pixels.length" class="text-sm text-slate-500">Nenhuma conexão cadastrada.</p>
        </div>
      </div>

      <div
        v-if="isFree"
        class="absolute inset-0 flex items-center justify-center bg-white/70 backdrop-blur-sm"
      >
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-center shadow-md">
          <p class="text-sm font-semibold text-emerald-800">Disponível a partir do plano Essencial</p>
          <p class="text-xs text-emerald-700 mt-1">Faça upgrade para habilitar integrações.</p>
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
    await api.post("/pixels", { name: nameInput.value.trim(), type: typeInput.value, value: idInput.value.trim() });
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
