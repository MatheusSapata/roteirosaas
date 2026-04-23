<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <header class="space-y-1">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500 dark:text-white/70">
        {{ viewCopy.header.eyebrow }}
      </p>
      <h1 class="text-3xl font-bold text-slate-900 dark:text-white">
        {{ viewCopy.header.title }}
      </h1>
      <p class="text-sm text-slate-600 dark:text-slate-200">
        {{ viewCopy.header.description }}
      </p>
    </header>

    <div
      class="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md dark:border-[#2b2b2b] dark:bg-[#202020]"
      :class="isFree ? 'opacity-60' : ''"
    >
      <div class="grid gap-6 p-6 md:grid-cols-3">
        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700 dark:text-white">
            {{ viewCopy.form.nameLabel }}
          </p>
          <input
            v-model="nameInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 dark:border-[#3a3a3a] dark:bg-[#101010] dark:text-white"
            :placeholder="viewCopy.form.namePlaceholder"
            :disabled="!canCreate"
          />
        </div>

        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700 dark:text-white">
            {{ viewCopy.form.platformLabel }}
          </p>
          <select
            v-model="typeInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 dark:border-[#3a3a3a] dark:bg-[#101010] dark:text-white"
            :disabled="!canCreate"
          >
            <option value="meta">{{ viewCopy.form.platformOptions.meta }}</option>
            <option value="ga">{{ viewCopy.form.platformOptions.ga }}</option>
          </select>
        </div>

        <div class="space-y-3">
          <p class="text-sm font-semibold text-slate-700 dark:text-white">
            {{ viewCopy.form.codeLabel }}
          </p>
          <input
            v-model="idInput"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 dark:border-[#3a3a3a] dark:bg-[#101010] dark:text-white"
            :placeholder="viewCopy.form.codePlaceholder"
            :disabled="!canCreate"
          />
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/70 px-6 py-4 text-sm text-slate-700 dark:border-[#2b2b2b] dark:bg-[#161616] dark:text-slate-100">
        <div class="flex flex-wrap items-center gap-3">
          <span class="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-white dark:text-black">
            {{ viewCopy.statusBar.limitPrefix }} {{ limitLabel }}
          </span>
          <span class="text-slate-500 dark:text-slate-300">{{ connectionsInfo }}</span>
        </div>

        <button
          class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:opacity-50"
          @click="savePixel"
          :disabled="!canCreate"
        >
          {{ viewCopy.form.save }}
        </button>
      </div>

      <div class="px-6 pb-2 text-xs text-slate-500 dark:text-slate-300">
        {{ viewCopy.statusBar.planNote }}
      </div>

      <div class="px-6 pb-6">
        <p class="mb-2 text-sm font-semibold text-slate-700 dark:text-white">
          {{ viewCopy.list.title }}
        </p>

        <div class="grid gap-3 md:grid-cols-2">
          <div
            v-for="(p, idx) in pixels"
            :key="p.id ?? idx"
            class="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-[#2b2b2b] dark:bg-[#181818]"
          >
            <div class="text-sm text-slate-800 dark:text-slate-100">
              <p class="font-semibold">
                {{ p.name }} -
                {{ p.type === "meta" ? viewCopy.list.typeMeta : viewCopy.list.typeGa }}
              </p>
              <p class="text-slate-600 dark:text-slate-300">{{ p.value }}</p>
            </div>

            <button
              class="text-sm font-semibold text-rose-600 hover:text-rose-500 disabled:opacity-50"
              @click="removePixel(idx)"
              :disabled="isFree"
            >
              {{ viewCopy.list.remove }}
            </button>
          </div>

          <p
            v-if="!pixels.length"
            class="text-sm text-slate-500 dark:text-slate-400"
          >
            {{ viewCopy.list.empty }}
          </p>
        </div>
      </div>

      <div
        v-if="isFree"
        class="absolute inset-0 flex items-center justify-center bg-white/70 backdrop-blur-sm dark:bg-black/60"
      >
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-center shadow-md dark:border-emerald-900 dark:bg-[#052e16] dark:text-emerald-50">
          <p class="text-sm font-semibold text-emerald-800 dark:text-emerald-100">
            {{ viewCopy.overlay.title }}
          </p>
          <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-200/80">
            {{ viewCopy.overlay.description }}
          </p>
        </div>
      </div>
    </div>

    <p v-if="errorMessage" class="text-sm font-semibold text-rose-600">
      {{ errorMessage }}
    </p>
    <p v-if="message" class="text-sm font-semibold text-emerald-600">
      {{ message }}
    </p>
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

const planNames = {
  free: t({ pt: "Começo", es: "Inicio" }),
  essencial: t({ pt: "Essencial", es: "Esencial" }),
  growth: t({ pt: "Agência", es: "Agencia" }),
  infinity: t({ pt: "Escala", es: "Escala" })
};

const viewCopy = {
  header: {
    eyebrow: t({ pt: "Integrações de anúncios", es: "Integraciones de anuncios" }),
    title: t({ pt: "Conexões com Facebook e Google", es: "Conexiones con Facebook y Google" }),
    description: t({
      pt: "Conecte sua página ao Facebook ou Google para acompanhar acessos e otimizar seus anúncios.",
      es: "Conecta tu página a Facebook o Google para seguir los accesos y optimizar tus anuncios."
    })
  },
  form: {
    nameLabel: t({ pt: "Nome da conexão", es: "Nombre de la conexión" }),
    namePlaceholder: t({ pt: "Ex.: Roteiro São Paulo", es: "Ej.: Itinerario São Paulo" }),
    platformLabel: t({ pt: "Plataforma", es: "Plataforma" }),
    codeLabel: t({ pt: "Código de acompanhamento", es: "Código de seguimiento" }),
    codePlaceholder: t({ pt: "Ex.: 123456789012345 ou G-XXXX", es: "Ej.: 123456789012345 o G-XXXX" }),
    save: t({ pt: "Salvar conexão", es: "Guardar conexión" }),
    platformOptions: {
      meta: t({ pt: "Meta", es: "Meta" }),
      ga: t({ pt: "Google", es: "Google" })
    }
  },
  statusBar: {
    limitPrefix: t({ pt: "Limite:", es: "Límite:" }),
    unlimited: t({ pt: "Conforme o plano", es: "Según el plan" }),
    connectionsInfo: (count: number, limitText: string, unlimited: boolean) =>
      t({
        pt: unlimited ? `Conexões cadastradas: ${count}` : `Conexões cadastradas: ${count} / ${limitText}`,
        es: unlimited ? `Conexiones registradas: ${count}` : `Conexiones registradas: ${count} / ${limitText}`
      }),
    planNote: t({
      pt: "Integrações disponíveis conforme seu plano.",
      es: "Puedes conectar según tu plan."
    })
  },
  list: {
    title: t({ pt: "Conexões cadastradas", es: "Conexiones registradas" }),
    typeMeta: t({ pt: "Facebook", es: "Facebook" }),
    typeGa: t({ pt: "Google", es: "Google" }),
    remove: t({ pt: "Remover", es: "Eliminar" }),
    empty: t({ pt: "Nenhuma conexão cadastrada.", es: "No hay conexiones registradas." })
  },
  overlay: {
    title: t({
      pt: `Disponível a partir do plano ${planNames.essencial}`,
      es: `Disponible a partir del plan ${planNames.essencial}`
    }),
    description: t({
      pt: "Faça upgrade para habilitar integrações.",
      es: "Haz upgrade para habilitar integraciones."
    })
  },
  messages: {
    loadError: t({ pt: "Não foi possível carregar as conexões.", es: "No fue posible cargar las conexiones." }),
    limitReached: t({ pt: "Limite de conexões atingido para seu plano.", es: "Límite de conexiones alcanzado para tu plan." }),
    missingFields: t({ pt: "Preencha nome e código da conexão.", es: "Completa el nombre y el código de la conexión." }),
    saveSuccess: t({ pt: "Conexão salva.", es: "Conexión guardada." }),
    saveError: t({ pt: "Erro ao salvar conexão.", es: "Error al guardar la conexión." }),
    removeSuccess: t({ pt: "Conexão removida.", es: "Conexión eliminada." }),
    removeError: t({ pt: "Erro ao remover conexão.", es: "Error al eliminar la conexión." }),
    invalidRemove: t({ pt: "Não foi possível identificar a conexão para remover.", es: "No fue posible identificar la conexión a eliminar." })
  }
};

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

const limitLabel = computed(() =>
  limit.value === Infinity ? viewCopy.statusBar.unlimited : `${limit.value}`
);

const connectionsInfo = computed(() =>
  viewCopy.statusBar.connectionsInfo(
    pixels.value.length,
    limitLabel.value,
    limit.value === Infinity
  )
);

const canCreate = computed(() => {
  if (isFree.value) return false;
  if (limit.value === Infinity) return true;
  return pixels.value.length < limit.value;
});

const fetchPixels = async () => {
  errorMessage.value = "";

  try {
    const res = await api.get("/pixels/");
    pixels.value = Array.isArray(res.data) ? res.data : [];
  } catch (err) {
    console.error(err);
    errorMessage.value = viewCopy.messages.loadError;
  }
};

const savePixel = async () => {
  errorMessage.value = "";
  message.value = "";

  if (!canCreate.value) {
    errorMessage.value = viewCopy.messages.limitReached;
    return;
  }

  if (!nameInput.value.trim() || !idInput.value.trim()) {
    errorMessage.value = viewCopy.messages.missingFields;
    return;
  }

  try {
    await api.post("/pixels/", {
      name: nameInput.value.trim(),
      type: typeInput.value,
      value: idInput.value.trim()
    });

    await fetchPixels();

    nameInput.value = "";
    idInput.value = "";
    typeInput.value = "meta";
    message.value = viewCopy.messages.saveSuccess;
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || viewCopy.messages.saveError;
  }
};

const removePixel = async (idx: number) => {
  errorMessage.value = "";
  message.value = "";

  const pixel = pixels.value[idx];

  if (!pixel?.id) {
    errorMessage.value = viewCopy.messages.invalidRemove;
    return;
  }

  try {
    await api.delete(`/pixels/${pixel.id}`);
    await fetchPixels();
    message.value = viewCopy.messages.removeSuccess;
  } catch (err) {
    console.error(err);
    errorMessage.value = viewCopy.messages.removeError;
  }
};

onMounted(() => {
  fetchPixels();
});
</script>