<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm uppercase tracking-wide text-slate-500 dark:text-slate-400">Roteiros</p>
        <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-50">Paginas</h1>
      </div>
      <button
        @click="createDraft"
        class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
        :disabled="!hasAgency"
      >
        Nova pagina
      </button>
    </div>

    <div v-if="!hasAgency" class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      Crie uma agencia primeiro em
      <router-link to="/admin/agency" class="font-semibold underline">Configuracao da agencia</router-link>
      para poder criar paginas.
    </div>

    <div class="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-md">
      <table class="min-w-full divide-y divide-slate-100">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Titulo</th>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Status</th>
            <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Criada em</th>
            <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Acoes</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 bg-white">
          <tr v-for="page in pages" :key="page.id" class="hover:bg-slate-50">
            <td class="px-4 py-3 text-sm font-semibold text-slate-900">
              <div class="flex items-center gap-2">
                <span>{{ page.title }}</span>
                <span
                  v-if="page.is_default"
                  class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-100"
                >
                  Padrao
                </span>
              </div>
            </td>
            <td class="px-4 py-3 text-sm text-slate-600">
              <span :class="page.status === 'published' ? 'text-emerald-500' : 'text-amber-500'">
                {{ page.status === "published" ? "Publicada" : "Rascunho" }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-slate-600">{{ formatDate(page.created_at) }}</td>
            <td class="px-4 py-3 text-right text-sm">
              <div class="flex flex-wrap items-center justify-end gap-3">
                <button class="text-slate-500 hover:text-slate-700" @click="openDuplicateDialog(page)">
                  Duplicar
                </button>
                <router-link :to="`/admin/pages/${page.id}/edit`" class="text-brand hover:text-brand-dark">Editar</router-link>
                <a
                  v-if="currentAgencySlug && page.slug"
                  :href="`/${currentAgencySlug}/${page.slug}`"
                  target="_blank"
                  class="text-slate-500 hover:text-slate-700"
                >
                  Ver
                </a>
                <button
                  v-if="page.status === 'published'"
                  class="text-slate-500 hover:text-slate-700 disabled:cursor-not-allowed disabled:text-slate-400"
                  :disabled="page.is_default"
                  @click="setDefaultPage(page)"
                >
                  {{ page.is_default ? "Padrao atual" : "Definir padrao" }}
                </button>
                <button
                  v-if="page.status === 'published' && currentAgencySlug && page.slug"
                  class="text-slate-500 hover:text-slate-700"
                  @click="copyLink(page)"
                >
                  Copiar link
                </button>
                <button class="text-red-500 hover:text-red-700" @click="deletePage(page)">Excluir</button>
              </div>
            </td>
          </tr>
          <tr v-if="pages.length === 0">
            <td colspan="4" class="px-4 py-6 text-center text-sm text-slate-500">Nenhuma pagina ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</p>
    <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>

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
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";

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

const router = useRouter();
const agencyStore = useAgencyStore();
const pages = ref<Page[]>([]);
const hasAgency = ref(false);
const errorMessage = ref("");
const message = ref("");
const duplicateDialogOpen = ref(false);
const duplicateTitle = ref("");
const duplicateSlug = ref("");
const duplicateSourcePage = ref<Page | null>(null);

const currentAgencySlug = computed(() => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.slug || "";
});

const loadPages = async () => {
  errorMessage.value = "";
  await agencyStore.loadAgencies();
  hasAgency.value = !!agencyStore.currentAgencyId;
  if (!hasAgency.value) return;
  try {
    const res = await api.get<Page[]>("/pages", { params: { agency_id: agencyStore.currentAgencyId } });
    pages.value = res.data;
  } catch (err) {
    console.error(err);
    errorMessage.value = "Nao foi possivel carregar as paginas.";
  }
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

const createDraft = async () => {
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
  } catch (err) {
    console.error(err);
    errorMessage.value = "Nao foi possivel criar a pagina. Verifique se voce esta logado e tem acesso a agencia.";
  }
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
    errorMessage.value = "Selecione uma agencia.";
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
    message.value = "Pagina duplicada.";
    closeDuplicateDialog();
    router.push(`/admin/pages/${res.data.id}/edit`);
  } catch (err) {
    console.error(err);
    errorMessage.value = "Nao foi possivel duplicar. Verifique se o slug ja existe ou se voce esta logado.";
  }
};

const copyLink = async (page: Page) => {
  if (!currentAgencySlug.value || !page.slug) return;
  const url = `${window.location.origin}/${currentAgencySlug.value}/${page.slug}`;
  try {
    await navigator.clipboard.writeText(url);
    message.value = "Link copiado para a area de transferencia.";
  } catch {
    errorMessage.value = "Nao foi possivel copiar o link.";
  }
};

const setDefaultPage = async (page: Page) => {
  if (page.status !== "published") {
    errorMessage.value = "Apenas paginas publicadas podem ser padrao.";
    return;
  }
  try {
    await api.post(`/pages/${page.id}/set-default`);
    message.value = `"${page.title}" definida como pagina padrao.`;
    pages.value = pages.value.map(p => ({ ...p, is_default: p.id === page.id }));
    const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
    if (agency) {
      agency.default_page_id = page.id;
    }
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || "Nao foi possivel definir a pagina padrao.";
  }
};

const deletePage = async (page: Page) => {
  if (!confirm(`Tem certeza que deseja excluir "${page.title}"? Esta acao nao pode ser desfeita.`)) {
    return;
  }
  try {
    await api.delete(`/pages/${page.id}`);
    pages.value = pages.value.filter(p => p.id !== page.id);
    message.value = "Pagina excluida.";
    if (page.is_default) {
      const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
      if (agency) {
        agency.default_page_id = null;
      }
    }
  } catch (err) {
    console.error(err);
    errorMessage.value = "Nao foi possivel excluir a pagina.";
  }
};

const formatDate = (date?: string) => (date ? new Date(date).toLocaleDateString("pt-BR") : "-");

onMounted(loadPages);
</script>
