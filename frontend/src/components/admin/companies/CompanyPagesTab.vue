<template>
  <section class="am-card am-card-flush">
    <div class="am-card-head cp-head">
      <div>
        <div class="am-card-title">Páginas</div>
        <div class="am-card-sub">{{ publishedCount }} publicadas · {{ pages.length - publishedCount }} rascunhos</div>
      </div>
      <button type="button" class="am-btn am-btn-sm" :disabled="!agencyStore.currentAgencyId" @click="openLinkPage">
        <AmIcon name="link" />Vincular uma página minha
      </button>
    </div>
    <div v-if="pageNotice" class="am-notice mx-4 mb-3" :class="`am-tone-${pageNotice.tone}`">
      <AmIcon :name="pageNotice.tone === 'success' ? 'check' : 'alert'" /><span>{{ pageNotice.text }}</span>
    </div>
    <div v-if="loading" class="am-empty"><div class="am-spinner"></div></div>
    <div v-else-if="pages.length" class="am-table-wrap">
      <table class="am-table">
        <thead>
          <tr>
            <th>Página</th>
            <th>Atualizada</th>
            <th class="am-right">Visitas</th>
            <th class="am-right">Cliques</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="page in pages" :key="page.id">
            <td>
              <b class="font-semibold">{{ page.title }}</b>
              <span class="am-badge ml-1.5" :class="page.status === 'published' ? 'am-tone-success' : 'am-tone-neutral'">
                {{ page.status === "published" ? "Publicada" : "Rascunho" }}
              </span>
              <div class="am-mono am-muted">/{{ slug }}/{{ page.slug }}</div>
            </td>
            <td class="am-num">{{ page.updated_at ? relativeDay(page.updated_at) : "—" }}</td>
            <td class="am-right am-num">{{ formatInt(page.visits) }}</td>
            <td class="am-right am-num">{{ formatInt(page.clicks) }}</td>
            <td class="am-right whitespace-nowrap">
              <a v-if="page.status === 'published'" :href="`/${slug}/${page.slug}`" target="_blank" rel="noopener noreferrer" class="am-btn am-btn-sm">
                <AmIcon name="eye" />Ver
              </a>
              <RouterLink :to="{ name: 'page-edit', params: { id: page.id } }" class="am-btn am-btn-sm ml-1"><AmIcon name="edit" />Editar</RouterLink>
              <button
                type="button"
                class="am-btn am-btn-sm ml-1"
                :disabled="copyingPageId === page.id || !agencyStore.currentAgencyId"
                @click="copyToMe(page)"
              >
                <AmIcon name="copy" />{{ copyingPageId === page.id ? "Copiando..." : "Copiar para mim" }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="am-empty">Nenhuma página criada.</div>
  </section>

  <AdminMasterConfirm
    :open="linkDialog.open"
    :title="`Vincular página a ${companyName}`"
    confirm-label="Copiar para a empresa"
    busy-label="Copiando..."
    :busy="linkDialog.saving"
    :error="linkDialog.error"
    icon="link"
    tone="info"
    :disabled="!linkDialog.pageId || !linkDialog.title.trim()"
    @close="linkDialog.open = false"
    @confirm="confirmLinkPage"
  >
    <p>Uma cópia de uma página da sua agência atual vai para esta empresa, publicada.</p>
    <div v-if="linkDialog.loading" class="am-empty !py-4"><div class="am-spinner"></div></div>
    <template v-else-if="linkDialog.pages.length">
      <div class="am-field mt-3">
        <label for="cp-link-page">Página de origem</label>
        <select id="cp-link-page" v-model="linkDialog.pageId" class="am-input">
          <option v-for="page in linkDialog.pages" :key="page.id" :value="page.id">
            {{ page.title }} · {{ page.status === "published" ? "Publicada" : "Rascunho" }}
          </option>
        </select>
      </div>
      <div class="am-field mt-3">
        <label for="cp-link-title">Nome do roteiro na empresa</label>
        <input id="cp-link-title" v-model="linkDialog.title" type="text" class="am-input" />
      </div>
    </template>
    <p v-else class="mt-3">Sua agência atual não tem páginas para copiar.</p>
  </AdminMasterConfirm>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import api from "../../../services/api";
import type { CompanyPage } from "../../../services/companies";
import { useAgencyStore } from "../../../store/useAgencyStore";
import AmIcon from "../master/AmIcon.vue";
import AdminMasterConfirm from "../master/AdminMasterConfirm.vue";
import { formatInt, relativeDay } from "../master/format";

const props = defineProps<{ companyId: number; companyName: string; slug: string; pages: CompanyPage[]; loading: boolean }>();
const emit = defineEmits<{ (e: "changed", message: string): void }>();

const agencyStore = useAgencyStore();
const publishedCount = computed(() => props.pages.filter(page => page.status === "published").length);

const copyingPageId = ref<number | null>(null);
const pageNotice = ref<{ tone: "success" | "danger"; text: string } | null>(null);
const copyToMe = async (page: CompanyPage) => {
  if (!agencyStore.currentAgencyId) return;
  copyingPageId.value = page.id;
  try {
    await api.post(`/admin/pages/${page.id}/clone`, {
      target_agency_id: agencyStore.currentAgencyId,
      title: `${page.title} - ${props.companyName}`
    });
    pageNotice.value = { tone: "success", text: `“${page.title}” foi copiada para a sua agência atual.` };
  } catch (error: any) {
    pageNotice.value = { tone: "danger", text: error?.response?.data?.detail || "Não foi possível copiar esta página." };
  } finally {
    copyingPageId.value = null;
  }
};

const linkDialog = reactive({
  open: false,
  loading: false,
  saving: false,
  error: "",
  pages: [] as Array<{ id: number; title: string; status: string }>,
  pageId: null as number | null,
  title: ""
});
watch(
  () => linkDialog.pageId,
  id => {
    linkDialog.title = linkDialog.pages.find(page => page.id === id)?.title || "";
  }
);
const openLinkPage = async () => {
  if (!agencyStore.currentAgencyId) return;
  Object.assign(linkDialog, { open: true, loading: true, saving: false, error: "", pages: [], pageId: null, title: "" });
  try {
    const { data } = await api.get<Array<{ id: number; title: string; status: string }>>("/pages", {
      params: { agency_id: agencyStore.currentAgencyId }
    });
    linkDialog.pages = data || [];
    linkDialog.pageId = linkDialog.pages[0]?.id ?? null;
  } catch {
    linkDialog.error = "Não foi possível carregar as suas páginas.";
  } finally {
    linkDialog.loading = false;
  }
};
const confirmLinkPage = async () => {
  if (!linkDialog.pageId) return;
  linkDialog.saving = true;
  linkDialog.error = "";
  try {
    await api.post(`/admin/pages/${linkDialog.pageId}/clone`, { target_agency_id: props.companyId, title: linkDialog.title.trim() });
    linkDialog.open = false;
    pageNotice.value = { tone: "success", text: `“${linkDialog.title.trim()}” foi copiada e publicada na empresa.` };
    emit("changed", "");
  } catch (error: any) {
    linkDialog.error = error?.response?.data?.detail || "Não foi possível vincular a página.";
  } finally {
    linkDialog.saving = false;
  }
};
</script>

<style scoped>
.cp-head {
  padding: 16px 16px 10px;
  margin: 0;
}
</style>
