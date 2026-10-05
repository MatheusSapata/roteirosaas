import { ref } from "vue";
import api from "../../../services/api";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { buildPublicPagePath } from "../../../utils/publicPagePath";

export interface AgencyPage {
  id: number;
  title: string;
  slug: string;
  status: string;
  cover_image_url?: string;
  seo_title?: string;
  seo_description?: string;
  config_json?: Record<string, any> | string | null;
}

/** Páginas da agência, para links do Menu do topo e cards de Outros roteiros. */
export const useAgencyPages = () => {
  const agencyStore = useAgencyStore();
  const pages = ref<AgencyPage[]>([]);
  const loading = ref(false);

  const pageUrl = (page: AgencyPage) => {
    const agency = agencyStore.agencies.find(item => item.id === agencyStore.currentAgencyId);
    return buildPublicPagePath(page.slug, agency?.slug, agencyStore.currentPrimaryDomain);
  };

  const load = async () => {
    loading.value = true;
    try {
      if (!agencyStore.currentAgencyId) await agencyStore.loadAgencies().catch(() => undefined);
      const agencyId = agencyStore.currentAgencyId;
      if (!agencyId) return;
      if (!(agencyId in agencyStore.primaryDomains)) await agencyStore.loadPrimaryDomain(agencyId).catch(() => undefined);
      pages.value = (await api.get<AgencyPage[]>("/pages", { params: { agency_id: agencyId } })).data.filter(
        page => page.status === "published" || page.status === "draft"
      );
    } catch {
      pages.value = [];
    } finally {
      loading.value = false;
    }
  };

  return { pages, loading, load, pageUrl };
};
