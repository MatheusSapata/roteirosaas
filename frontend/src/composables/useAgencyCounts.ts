import { reactive } from "vue";
import api from "../services/api";

// Números das abas de Minha agência: pessoas na equipe e faturas em aberto.
// As telas de Equipe e Faturas atualizam este estado quando carregam os dados.
export const agencyCounts = reactive({
  team: null as number | null,
  invoices: null as number | null
});

export const loadAgencyCounts = async (options: { team?: boolean; invoices?: boolean }) => {
  const tasks: Promise<unknown>[] = [];
  if (options.team && agencyCounts.team === null) {
    tasks.push(
      api.get("/agency/team").then(res => {
        agencyCounts.team = Array.isArray(res.data?.members) ? res.data.members.length : 0;
      })
    );
  }
  if (options.invoices && agencyCounts.invoices === null) {
    tasks.push(
      api.get("/billing/invoices").then(res => {
        const counts = res.data?.counts || {};
        agencyCounts.invoices = (Number(counts.upcoming) || 0) + (Number(counts.overdue) || 0);
      })
    );
  }
  await Promise.allSettled(tasks);
};
