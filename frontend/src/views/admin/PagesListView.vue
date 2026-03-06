<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-bold uppercase tracking-[0.3em] text-slate-500">Páginas</p>
      </div>
      <button
        @click="openCreateModal"
        class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
        :disabled="!hasAgency"
      >
        Nova pagina
      </button>
    </div>

    <div v-if="!hasAgency" class="flex flex-col gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 sm:flex-row sm:items-center sm:justify-between">
      <span>
        Crie uma agencia primeiro em
        <router-link to="/admin/agency" class="font-semibold underline">Configuracao da agencia</router-link>
        para poder criar paginas.
      </span>
      <router-link
        to="/admin/agency"
        class="inline-flex items-center justify-center rounded-full bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-amber-500"
      >
        Criar minha agência
      </router-link>
    </div>

    <div
      v-if="createOptionsOpen"
      class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4 py-8"
    >
      <div class="w-full max-w-4xl rounded-3xl bg-white p-8 shadow-2xl">
        <div class="mb-6 space-y-1">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Novo roteiro</p>
          <h2 class="text-2xl font-bold text-slate-900">Como deseja começar?</h2>
          <p class="text-sm text-slate-500">Escolha entre montar tudo do zero ou partir de um template pronto.</p>
        </div>

        <div class="grid gap-4 md:grid-cols-3">
          <button
            class="rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50"
            @click="createPageFromScratch"
          >
            <span class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">
              Recomendado
            </span>
            <h3 class="mt-3 text-lg font-semibold text-slate-900">Criar página do zero</h3>
            <p class="mt-1 text-sm text-slate-600">
              Acesse o editor completo para personalizar cada seção do seu roteiro.
            </p>
          </button>

          <button
            class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-left text-slate-600 transition hover:-translate-y-0.5 hover:border-slate-300"
            @click="createPageFromTemplate"
          >
            <span class="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">
              Em breve
            </span>
            <h3 class="mt-3 text-lg font-semibold text-slate-900">Criar a partir de modelo</h3>
            <p class="mt-1 text-sm text-slate-600">
              Selecione um layout pronto e personalize apenas o conteúdo.
            </p>
          </button>

          <button
            class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-left text-slate-600 transition hover:-translate-y-0.5 hover:border-slate-300"
            @click="createPageWithAi"
          >
            <span class="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">
              Em breve
            </span>
            <h3 class="mt-3 text-lg font-semibold text-slate-900">Criar com IA</h3>
            <p class="mt-1 text-sm text-slate-600">
              Gere um roteiro inicial com inteligência artificial e refine os detalhes depois.
            </p>
          </button>
        </div>

        <div class="mt-6 flex justify-end">
          <button class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100" @click="closeCreateModal">
            Cancelar
          </button>
        </div>
    </div>
  </div>

    <transition name="fade">
      <div
        v-if="trialLimitDialogOpen"
        class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">Limite atingido</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">Você usou as 3 páginas do plano trial</h2>
          <p class="mt-2 text-sm text-slate-600">
            Continue criando roteiros ilimitados ativando um plano agora mesmo.
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="trialLimitDialogOpen = false"
            >
              Fechar
            </button>
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="goPlans"
            >
              Ver planos
            </button>
          </div>
        </div>
      </div>
    </transition>

    <div class="overflow-x-auto">
      <div class="min-w-[880px] overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-md">
        <div
          class="hidden grid-cols-[1.2fr,0.9fr,0.9fr,1.6fr,0.6fr,1.9fr] gap-6 border-b border-slate-100 px-6 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 md:grid"
        >
          <span>Nome</span>
          <span>Visualizacoes</span>
          <span>Cliques CTA</span>
          <span>Link</span>
          <span>Status</span>
          <span class="text-right">Acoes</span>
        </div>

        <div v-if="pages.length" class="divide-y divide-slate-100">
          <div
            v-for="page in pages"
            :key="page.id"
            class="grid grid-cols-1 items-center gap-6 px-6 py-5 transition hover:bg-slate-50/70 md:grid-cols-[1.2fr,0.9fr,0.9fr,1.6fr,0.6fr,1.9fr]"
          >
            <div class="flex flex-wrap items-center gap-3">
              <p class="text-base font-semibold text-slate-900">{{ page.title }}</p>
              <span
                v-if="page.is_default"
                class="rounded-full bg-emerald-50 px-3 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-600 ring-1 ring-emerald-100"
              >
                Padrao
              </span>
            </div>

            <div class="flex justify-center">
              <button
                v-if="isFree"
                type="button"
                class="inline-flex min-w-[3rem] items-center justify-center rounded-full border border-emerald-200 bg-white px-4 py-1.5 text-sm font-semibold text-emerald-600 shadow-sm transition hover:bg-emerald-50"
                title="Funcionalidade premium. Faca upgrade."
                @click="goPlans"
              >
                <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.329 19.159q-.323-.14-.566-.432L3.267 9.731q-.186-.217-.28-.475t-.093-.55q0-.187.047-.366q.048-.18.134-.361l1.779-3.59q.217-.405.603-.647t.845-.242h11.396q.46 0 .845.242t.603.646l1.779 3.59q.087.182.134.362t.047.366q0 .292-.094.55t-.28.475l-7.495 8.996q-.243.292-.566.432q-.323.139-.671.139t-.671-.14M8.817 8.5h6.366l-2-4h-2.366zm2.683 9.56V9.5H4.392zm1 0l7.108-8.56H12.5zm3.792-9.56h3.766L18.23 4.846q-.077-.154-.231-.25t-.327-.096h-3.38zm-12.35 0h3.766l2-4H6.327q-.173 0-.327.096t-.23.25z" />
                </svg>
              </button>
              <span
                v-else
                class="inline-flex min-w-[3rem] justify-center rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-600"
              >
                {{ getPageVisits(page.id) }}
              </span>
            </div>

            <div class="flex justify-center">
              <button
                v-if="isFree"
                type="button"
                class="inline-flex min-w-[3rem] items-center justify-center rounded-full border border-indigo-200 bg-white px-4 py-1.5 text-sm font-semibold text-indigo-600 shadow-sm transition hover:bg-indigo-50"
                title="Funcionalidade premium. Faca upgrade."
                @click="goPlans"
              >
                <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.329 19.159q-.323-.14-.566-.432L3.267 9.731q-.186-.217-.28-.475t-.093-.55q0-.187.047-.366q.048-.18.134-.361l1.779-3.59q.217-.405.603-.647t.845-.242h11.396q.46 0 .845.242t.603.646l1.779 3.59q.087.182.134.362t.047.366q0 .292-.094.55t-.28.475l-7.495 8.996q-.243.292-.566.432q-.323.139-.671.139t-.671-.14M8.817 8.5h6.366l-2-4h-2.366zm2.683 9.56V9.5H4.392zm1 0l7.108-8.56H12.5zm3.792-9.56h3.766L18.23 4.846q-.077-.154-.231-.25t-.327-.096h-3.38zm-12.35 0h3.766l2-4H6.327q-.173 0-.327.096t-.23.25z" />
                </svg>
              </button>
              <span
                v-else
                class="inline-flex min-w-[3rem] justify-center rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-600"
              >
                {{ getPageClicks(page.id) }}
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <template v-if="page.status === 'published' && pagePublicUrl(page)">
                <a
                  :href="pagePublicUrl(page)"
                  target="_blank"
                  class="max-w-[220px] truncate text-sm font-medium text-brand hover:text-brand-dark"
                >
                  {{ pagePublicUrl(page) }}
                </a>
                <button
                  class="text-xs font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-600"
                  @click="copyLink(page)"
                >
                  Copiar
                </button>
              </template>
              <span v-else class="text-xs uppercase tracking-wide text-slate-400">Link disponivel apos publicar</span>
            </div>

            <div>
              <span
                class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
                :class="getStatusClasses(page.status)"
              >
                {{ getStatusLabel(page.status) }}
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-2 md:justify-end">
              <button
                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                title="Duplicar"
                @click="openDuplicateDialog(page)"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <rect x="9" y="9" width="11" height="11" rx="2" />
                  <rect x="4" y="4" width="11" height="11" rx="2" />
                </svg>
              </button>

              <router-link
                :to="`/admin/pages/${page.id}/edit`"
                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                title="Editar"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4Z" />
                </svg>
              </router-link>

              <a
                v-if="pagePublicUrl(page)"
                :href="pagePublicUrl(page)"
                target="_blank"
                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                title="Ver pagina"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </a>

              <button
                v-if="page.status === 'published'"
                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-amber-200 text-amber-500 transition hover:border-amber-300 hover:text-amber-600"
                title="Despublicar"
                @click="unpublishPage(page)"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="m7 10 5 5 5-5" />
                  <path d="M12 4v10" />
                </svg>
              </button>

              <button
                v-if="page.status === 'published'"
                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-slate-300 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="page.is_default"
                title="Definir padrao"
                @click="setDefaultPage(page)"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="m12 3 2.09 6.26h6.58L15.29 13l2.12 6.24L12 15.77l-5.41 3.47L8.71 13 3.33 9.26h6.58Z" />
                </svg>
              </button>

              <button
                class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-red-200 text-red-500 transition hover:border-red-300 hover:text-red-600"
                title="Excluir"
                @click="deletePage(page)"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="M3 6h18" />
                  <path d="M8 6V4h8v2" />
                  <path d="m9 10 1 8" />
                  <path d="m15 10-1 8" />
                  <path d="M5 6l1 14h12l1-14" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="px-6 py-10 text-center text-sm text-slate-500">Nenhuma pagina ainda.</div>
      </div>
    </div>

    <div
      v-if="duplicateDialogOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200">
        <div class="flex items-start justify-between">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">Duplicar pagina</h3>
            <p class="text-sm text-slate-500">Cria um rascunho copiando conteudo e ajustando slug.</p>
          </div>
          <button class="text-slate-500 hover:text-slate-700" @click="closeDuplicateDialog">x</button>
        </div>
        <div class="mt-4 space-y-4">
          <div>
            <label class="text-sm font-semibold text-slate-700">Titulo</label>
            <input
              v-model="duplicateTitle"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              placeholder="Novo titulo"
              @input="autoSlugFromTitle"
            />
          </div>
          <div>
            <label class="text-sm font-semibold text-slate-700">Slug</label>
            <input
              v-model="duplicateSlug"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
              placeholder="novo-slug"
            />
            <p class="mt-1 text-xs text-slate-500">Link final: /{{ currentAgencySlug }}/{{ duplicateSlug || 'slug' }}</p>
          </div>
        </div>
        <div class="mt-6 flex items-center justify-end gap-3">
          <button class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100" @click="closeDuplicateDialog">Cancelar</button>
          <button
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="!duplicateTitle || !duplicateSlug"
            @click="confirmDuplicate"
          >
            Duplicar
          </button>
        </div>
      </div>
    </div>
  </div>

  <transition name="fade">
    <div
      v-if="snackbar.open"
      class="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full px-5 py-3 text-sm font-semibold text-white shadow-2xl"
      :class="snackbar.tone === 'error' ? 'bg-rose-600' : 'bg-slate-900'"
    >
      {{ snackbar.text }}
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";

interface Page {
  id: number;
  title: string;
  status: string;
  created_at?: string;
  slug?: string;
  config_json?: unknown;
  template_id?: number | null;
  is_default?: boolean;
}

interface PageStatsSummary {
  page_id: number;
  visits: number;
  clicks_cta: number;
  clicks_whatsapp: number;
}

const router = useRouter();
const agencyStore = useAgencyStore();
const authStore = useAuthStore();
const pages = ref<Page[]>([]);
const pageStats = ref<Record<number, { visits: number; cta: number; whatsapp: number }>>({});
const hasAgency = ref(false);
const errorMessage = ref("");
const message = ref("");
const duplicateDialogOpen = ref(false);
const createOptionsOpen = ref(false);
const snackbar = ref<{ open: boolean; text: string; tone: "success" | "error" }>({
  open: false,
  text: "",
  tone: "success"
});
const duplicateTitle = ref("");
const duplicateSlug = ref("");
const duplicateSourcePage = ref<Page | null>(null);
const trialLimitDialogOpen = ref(false);

const currentAgencySlug = computed(() => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.slug || "";
});
const isFree = computed(() => (authStore.user?.plan || "free") === "free");

const loadPages = async () => {
  errorMessage.value = "";
  await agencyStore.loadAgencies();
  hasAgency.value = !!agencyStore.currentAgencyId;
  if (!hasAgency.value) return;
  try {
    const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyStore.currentAgencyId } });
    pages.value = res.data;
    await loadPageStats();
  } catch (err) {
    console.error(err);
    showSnackbar("Nao foi possivel carregar as paginas.", "error");
  }
};

const loadPageStats = async () => {
  if (!agencyStore.currentAgencyId) return;
  try {
    const res = await api.get<PageStatsSummary[]>("/stats/pages", { params: { agency_id: agencyStore.currentAgencyId } });
    const map: Record<number, { visits: number; cta: number; whatsapp: number }> = {};
    res.data.forEach(item => {
      map[item.page_id] = {
        visits: item.visits ?? 0,
        cta: item.clicks_cta ?? 0,
        whatsapp: item.clicks_whatsapp ?? 0
      };
    });
    pageStats.value = map;
  } catch (err) {
    console.error(err);
  }
};

const isTrialLimitError = (err: unknown) => {
  const response = (err as any)?.response;
  if (!response) return false;
  const headerCode = (response.headers?.["x-error-code"] || response.headers?.["X-Error-Code"]) as string | undefined;
  if (headerCode && String(headerCode).toLowerCase() === "trial_page_limit") {
    return true;
  }
  const detail = response.data?.detail;
  if (typeof detail === "string") {
    return detail.toLowerCase().includes("plano trial");
  }
  return false;
};

const handleTrialLimitError = (err: unknown) => {
  if (!isTrialLimitError(err)) return false;
  trialLimitDialogOpen.value = true;
  return true;
};

const buildFriendlySlug = () => {
  const existing = new Set(
    pages.value
      .map(page => page.slug)
      .filter((slug): slug is string => !!slug)
      .map(slug => slug.toLowerCase())
  );
  let counter = 1;
  let candidate = `roteiro-${counter}`;
  while (existing.has(candidate)) {
    counter += 1;
    candidate = `roteiro-${counter}`;
  }
  return candidate;
};

const openCreateModal = () => {
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Crie uma agencia antes de adicionar paginas.", "error");
    return;
  }
  createOptionsOpen.value = true;
};

const closeCreateModal = () => {
  createOptionsOpen.value = false;
};

const createPageFromScratch = async () => {
  errorMessage.value = "";
  message.value = "";
  if (!agencyStore.currentAgencyId) {
    errorMessage.value = "Crie uma agencia antes de adicionar paginas.";
    return;
  }
  try {
    const friendlySlug = buildFriendlySlug();
    const res = await api.post<Page>("/pages", {
      agency_id: agencyStore.currentAgencyId,
      title: "Novo roteiro",
      slug: friendlySlug || `novo-roteiro-${Date.now()}`,
      status: "draft"
    });
    pages.value.push({ ...res.data });
    router.push(`/admin/pages/${res.data.id}/edit`);
    createOptionsOpen.value = false;
  } catch (err) {
    console.error(err);
    if (handleTrialLimitError(err)) {
      createOptionsOpen.value = false;
      return;
    }
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || "Nao foi possivel criar a pagina. Verifique se voce esta logado e tem acesso a agencia.";
    createOptionsOpen.value = false;
  }
};

const showSnackbar = (text: string, tone: "success" | "error" = "success") => {
  snackbar.value = { open: true, text, tone };
  setTimeout(() => (snackbar.value.open = false), 4000);
};

const createPageFromTemplate = () => {
  showSnackbar("Funcionalidade em desenvolvimento. Em breve você poderá usar modelos prontos.");
};

const createPageWithAi = () => {
  showSnackbar("Funcionalidade em desenvolvimento. Em breve você poderá criar páginas com IA.");
};

const slugify = (value: string) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .substring(0, 80) || `pagina-${Date.now()}`;

const openDuplicateDialog = (page: Page) => {
  duplicateSourcePage.value = page;
  duplicateTitle.value = `${page.title} (copia)`;
  const baseSlug = page.slug ? `${page.slug}-copia` : duplicateTitle.value;
  duplicateSlug.value = slugify(baseSlug);
  duplicateDialogOpen.value = true;
};

const closeDuplicateDialog = () => {
  duplicateDialogOpen.value = false;
  duplicateTitle.value = "";
  duplicateSlug.value = "";
  duplicateSourcePage.value = null;
};

const autoSlugFromTitle = () => {
  if (!duplicateTitle.value) return;
  duplicateSlug.value = slugify(duplicateTitle.value);
};

const confirmDuplicate = async () => {
  if (!duplicateSourcePage.value) return;
  errorMessage.value = "";
  message.value = "";
  if (!agencyStore.currentAgencyId) {
    showSnackbar("Selecione uma agencia.", "error");
    return;
  }
  try {
    const fullPage =
      duplicateSourcePage.value.config_json !== undefined
        ? duplicateSourcePage.value
        : (await api.get<Page>(`/pages/${duplicateSourcePage.value.id}`)).data;
    const res = await api.post<Page>("/pages", {
      agency_id: agencyStore.currentAgencyId,
      title: duplicateTitle.value,
      slug: slugify(duplicateSlug.value),
      status: "draft",
      template_id: fullPage.template_id || null,
      config_json: fullPage.config_json || null
    });
    showSnackbar("Pagina duplicada.");
    closeDuplicateDialog();
    router.push(`/admin/pages/${res.data.id}/edit`);
  } catch (err) {
    console.error(err);
    if (handleTrialLimitError(err)) {
      closeDuplicateDialog();
      return;
    }
    showSnackbar("Nao foi possivel duplicar. Verifique se o slug ja existe ou se voce esta logado.", "error");
  }
};

const pagePublicUrl = (page: Page) => {
  if (!currentAgencySlug.value || !page.slug) return "";
  return `${window.location.origin}/${currentAgencySlug.value}/${page.slug}`;
};

const copyLink = async (page: Page) => {
  const url = pagePublicUrl(page);
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    showSnackbar("Link copiado para a area de transferencia.");
  } catch {
    showSnackbar("Nao foi possivel copiar o link.", "error");
  }
};

const setDefaultPage = async (page: Page) => {
  if (page.status !== "published") {
    showSnackbar("Apenas paginas publicadas podem ser padrao.", "error");
    return;
  }
  try {
    await api.post(`/pages/${page.id}/set-default`);
    showSnackbar(`"${page.title}" definida como pagina padrao.`);
    pages.value = pages.value.map(p => ({ ...p, is_default: p.id === page.id }));
    const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
    if (agency) {
      agency.default_page_id = page.id;
    }
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    showSnackbar(detail || "Nao foi possivel definir a pagina padrao.", "error");
  }
};

const unpublishPage = async (page: Page) => {
  if (page.status !== "published") return;
  try {
    await api.post(`/pages/${page.id}/publish`, { publish: false });
    pages.value = pages.value.map(p => {
      if (p.id !== page.id) return p;
      return { ...p, status: "draft", is_default: false };
    });
    showSnackbar(`"${page.title}" movida para rascunho.`);
    if (page.is_default) {
      const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
      if (agency) {
        agency.default_page_id = null;
      }
    }
  } catch (err) {
    console.error(err);
    showSnackbar("Nao foi possivel despublicar a pagina.", "error");
  }
};

const deletePage = async (page: Page) => {
  if (!confirm(`Tem certeza que deseja excluir "${page.title}"? Esta acao nao pode ser desfeita.`)) {
    return;
  }
  try {
    await api.delete(`/pages/${page.id}`);
    pages.value = pages.value.filter(p => p.id !== page.id);
    showSnackbar("Pagina excluida.");
    if (page.is_default) {
      const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
      if (agency) {
        agency.default_page_id = null;
      }
    }
  } catch (err) {
    console.error(err);
    showSnackbar("Nao foi possivel excluir a pagina.", "error");
  }
};

const getStatusLabel = (status: string) => (status === "published" ? "Ativo" : status === "draft" ? "Rascunho" : status);
const getStatusClasses = (status: string) => {
  if (status === "published") {
    return "bg-emerald-50 text-emerald-600";
  }
  if (status === "draft") {
    return "bg-amber-50 text-amber-600";
  }
  return "bg-slate-100 text-slate-600";
};
const getPageVisits = (pageId: number) => pageStats.value[pageId]?.visits ?? 0;
const getPageClicks = (pageId: number) => {
  const stats = pageStats.value[pageId];
  if (!stats) return 0;
  return (stats.cta ?? 0) + (stats.whatsapp ?? 0);
};

const goPlans = () => {
  router.push("/admin/planos");
};

onMounted(loadPages);
</script>

<style scoped>
.blurred-value {
  filter: blur(8px);
  opacity: 0.15;
  pointer-events: none;
  user-select: none;
}
</style>
