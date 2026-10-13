import type { Company, CompanyStatusKey } from "../../../services/companies";
import { daysUntil, formatDate } from "../master/format";

/** Mesma regra do backend (company_status.PAYMENT_RETRY_DAYS). */
export const PAYMENT_RETRY_DAYS = 30;

const days = (count: number) => `${count} ${count === 1 ? "dia" : "dias"}`;

/** Situações de quem paga: em dia, com cobrança atrasada ou cancelando no fim do período. */
export const PAYING_STATUSES: CompanyStatusKey[] = ["active", "past_due", "cancelling"];

/** Uma linha que explica a situação: há quanto tempo, até quando ou desde quando venceu. */
export const statusDetail = (item: Company) => {
  const since = item.status_days;
  const left = daysUntil(item.access_until);
  switch (item.status) {
    case "inactive":
      return since === null ? "Fora do ar, sem data registrada" : `Fora do ar há ${item.since_estimated ? "≈ " : ""}${days(since)}`;
    case "cancelling":
      return item.access_until ? `No ar até ${formatDate(item.access_until)}` : "Cancelamento agendado";
    case "trial":
      return left === null ? "Teste em andamento" : left <= 0 ? "Teste termina hoje" : `Teste termina em ${days(left)}`;
    case "trial_ended":
      return since === null ? "Teste encerrado sem pagamento" : `Teste acabou há ${days(since)}`;
    case "free":
      return left === null ? "Gratuita sem prazo" : left <= 0 ? "Acesso gratuito vence hoje" : `Acesso gratuito vence em ${days(left)}`;
    case "free_expired":
      return since === null ? "Acesso gratuito vencido" : `Acesso gratuito venceu há ${days(since)}`;
    case "past_due": {
      // Cobrança falhou: no ar por 3 dias depois do vencimento e cobrando por 30.
      if (!item.valid_until) return "Cobrança em atraso";
      const retryEnds = new Date(new Date(item.valid_until).getTime() + PAYMENT_RETRY_DAYS * 86_400_000).toISOString();
      if (item.online) return `Cobrança falhou · no ar até ${formatDate(item.access_until)}`;
      return `Fora do ar · cobrando até ${formatDate(retryEnds)}`;
    }
    case "active":
      if (left !== null && left >= 0 && left <= 7) return `Renova em ${days(left)}`;
      return since === null ? "Cliente" : `Cliente há ${days(since)}`;
    case "internal":
      return "Conta da casa, fora das contas de clientes";
    case "combo":
      if (left !== null && left >= 0 && left <= 7) return `Pago na Viaje On · renova em ${days(left)}`;
      return item.access_until ? `Pago na Viaje On · até ${formatDate(item.access_until)}` : "Pago na Viaje On";
    default:
      return "Sem dono vinculado";
  }
};

/** Acesso pago na Viaje On (combo): não é receita do Roteiro Online, então não mostra valor mensal. */
export const isCombo = (item: Company) => (item.subscription_provider || "").toLowerCase() === "viajeon";

/** Quem cobra de fato: só conta se há valor ou id de cobrança (o banco grava "asaas" como padrão até em conta gratuita). */
export const billingProvider = (item: Company) =>
  isCombo(item)
    ? "viajeon"
    : item.mrr_amount > 0 || item.subscription_asaas_subscription_id || item.subscription_cakto_order_id || item.subscription_cakto_subscription_code
    ? (item.subscription_provider || "").toLowerCase()
    : "";
