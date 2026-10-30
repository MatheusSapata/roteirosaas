import { computed, ref } from "vue";
import api from "../services/api";
import type { PageTag, PageTagBrief, TagColor } from "../types/pageTag";

// Uma lista só para a lista de páginas, o editor e o painel de tags: o que muda num aparece nos outros.
const tags = ref<PageTag[]>([]);
const loadedAgencyId = ref<number | null>(null);
const loading = ref(false);
let pending: Promise<void> | null = null;

const sortTags = (list: PageTag[]) => [...list].sort((a, b) => a.name.localeCompare(b.name, "pt-BR", { sensitivity: "base" }));

const upsert = (tag: PageTag) => {
  const others = tags.value.filter(item => item.id !== tag.id);
  tags.value = sortTags([...others, tag]);
};

export const errorDetail = (error: any, fallback: string) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" && detail ? detail : fallback;
};

export const usePageTags = () => {
  const load = async (agencyId: number | null | undefined, force = false) => {
    if (!agencyId) return;
    if (!force && loadedAgencyId.value === agencyId) return pending || undefined;
    loadedAgencyId.value = agencyId;
    loading.value = true;
    pending = api
      .get<PageTag[]>("/page-tags", { params: { agency_id: agencyId } })
      .then(res => {
        if (loadedAgencyId.value === agencyId) tags.value = sortTags(res.data);
      })
      .catch(() => {
        if (loadedAgencyId.value === agencyId) tags.value = [];
      })
      .finally(() => {
        loading.value = false;
        pending = null;
      });
    return pending;
  };

  const reload = () => load(loadedAgencyId.value, true);

  const create = async (agencyId: number, name: string, color?: TagColor) => {
    const { data } = await api.post<PageTag>("/page-tags", { agency_id: agencyId, name, color });
    upsert(data);
    return data;
  };

  const update = async (tagId: number, changes: { name?: string; color?: TagColor }) => {
    const { data } = await api.put<PageTag>(`/page-tags/${tagId}`, changes);
    upsert(data);
    return data;
  };

  const remove = async (tagId: number) => {
    await api.delete(`/page-tags/${tagId}`);
    tags.value = tags.value.filter(tag => tag.id !== tagId);
  };

  const merge = async (tagId: number, intoTagId: number) => {
    const { data } = await api.post<PageTag>(`/page-tags/${tagId}/merge`, { into_tag_id: intoTagId });
    tags.value = tags.value.filter(tag => tag.id !== tagId);
    upsert(data);
    return data;
  };

  /** Troca as tags de uma página. Devolve as tags que ficaram. */
  const setPageTags = async (pageId: number, tagIds: number[]) => {
    const { data } = await api.put<PageTagBrief[]>(`/pages/${pageId}/tags`, { tag_ids: tagIds });
    void reload();
    return data;
  };

  const bulk = async (agencyId: number, pageIds: number[], add: number[], removeIds: number[]) => {
    const { data } = await api.post<PageTag[]>("/page-tags/bulk", {
      agency_id: agencyId,
      page_ids: pageIds,
      add_tag_ids: add,
      remove_tag_ids: removeIds
    });
    tags.value = sortTags(data);
  };

  const byId = computed(() => new Map(tags.value.map(tag => [tag.id, tag])));

  return { tags, loading, load, reload, create, update, remove, merge, setPageTags, bulk, byId };
};
