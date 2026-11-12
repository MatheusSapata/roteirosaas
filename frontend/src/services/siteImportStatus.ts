import { reactive } from "vue";
import { fetchActiveSiteImportJob, type SiteImportJob } from "./siteImportJobs";

/**
 * Importação do site inteiro pelo assistente de IA, consultada em segundo plano: a pessoa pode
 * navegar para qualquer tela do admin que o aviso continua visível (mesmo padrão do envio de
 * fotos em `stockPhotoUploads.ts`). `dismissedJobId` esconde um job já concluído/com erro que a
 * pessoa já fechou, sem precisar que o backend pare de devolvê-lo.
 */
export const siteImportState = reactive({
  job: null as SiteImportJob | null,
  dismissedJobId: null as number | null
});

const POLL_MS = 6000;
let timer: ReturnType<typeof setInterval> | null = null;
let getAgencyId: (() => number | null | undefined) | null = null;

const poll = async () => {
  try {
    const job = await fetchActiveSiteImportJob(getAgencyId?.() ?? undefined);
    siteImportState.job = job;
  } catch {
    // Falha de rede ou sessão renovando: tenta de novo no próximo ciclo, sem incomodar.
  }
};

/** Começa a consultar o andamento. Chame uma vez no layout do admin (onMounted). */
export const startSiteImportPolling = (agencyIdGetter: () => number | null | undefined) => {
  getAgencyId = agencyIdGetter;
  void poll();
  if (timer !== null) return;
  timer = setInterval(poll, POLL_MS);
};

export const stopSiteImportPolling = () => {
  if (timer !== null) {
    clearInterval(timer);
    timer = null;
  }
};

export const dismissSiteImportJob = (jobId: number) => {
  siteImportState.dismissedJobId = jobId;
};
