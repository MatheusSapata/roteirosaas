import api from "./api";

/** Estágio de cada página (ou da home) da importação do site inteiro. */
export type SiteImportStage = "waiting" | "scraping" | "generating" | "done" | "error";

export interface SiteImportItem {
  url: string;
  title: string;
  stage: SiteImportStage;
  page_id: number | null;
  slug: string | null;
  error: string | null;
}

export interface SiteImportHome {
  page_id: number | null;
  slug: string | null;
  title: string | null;
  stage: SiteImportStage;
}

export interface SiteImportJob {
  id: number;
  agency_id: number;
  status: "running" | "completed" | "failed";
  stage: "pages" | "home" | null;
  source_url: string;
  source_title: string | null;
  total_found: number;
  total: number;
  done: number;
  failed: number;
  items: SiteImportItem[];
  home: SiteImportHome;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
}

/** Importação do site inteiro em andamento (ou concluída há pouco) da agência, para o aviso
 * global do painel. Sem agencyId, o backend olha as agências do usuário logado. */
export const fetchActiveSiteImportJob = async (agencyId?: number | null): Promise<SiteImportJob | null> => {
  const { data } = await api.get<{ job: SiteImportJob | null }>("/ai-assistant/import-jobs/active", {
    params: agencyId ? { agency_id: agencyId } : {}
  });
  return data.job;
};
