import { getPlanLabel } from "../../../utils/planLabels";
import type { CompanyStatusKey } from "../../../services/companies";

// Formatação comum às telas do admin master (Painel, Empresas, Usuários).
const intFormatter = new Intl.NumberFormat("pt-BR");
const moneyFormatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const DAY = 86_400_000;

export const formatInt = (value?: number | null) => intFormatter.format(Number(value || 0));

export const formatMoney = (value?: number | null) =>
  value === null || value === undefined || !Number.isFinite(Number(value)) ? "—" : moneyFormatter.format(Number(value));

/** R$ sem centavos, para eixos e rótulos curtos (R$ 1.234 / R$ 12 mil). */
export const formatMoneyShort = (value: number) => {
  const amount = Math.round(Number(value || 0));
  if (Math.abs(amount) >= 10_000) return `R$ ${intFormatter.format(Math.round(amount / 1000))} mil`;
  return `R$ ${intFormatter.format(amount)}`;
};

export const formatDate = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("pt-BR");
};

export const formatDateTime = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return `${date.toLocaleDateString("pt-BR")} ${date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`;
};

/** Dias inteiros até a data (negativo = já passou). */
export const daysUntil = (value?: string | null) => {
  if (!value) return null;
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? null : Math.ceil((time - Date.now()) / DAY);
};

export const daysSince = (value?: string | null) => {
  if (!value) return null;
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? null : Math.floor((Date.now() - time) / DAY);
};

export const plural = (count: number, one: string, many: string) => `${formatInt(count)} ${count === 1 ? one : many}`;

/** "Hoje", "Ontem", "Há 5 dias", "Há 3 meses". */
export const relativeDay = (value?: string | null) => {
  const days = daysSince(value);
  if (days === null) return "—";
  if (days <= 0) return "Hoje";
  if (days === 1) return "Ontem";
  if (days < 60) return `Há ${days} dias`;
  if (days < 730) return `Há ${Math.round(days / 30)} meses`;
  return `Há ${Math.round(days / 365)} anos`;
};

export const planLabel = (plan?: string | null) => (plan ? getPlanLabel(plan) : "Sem plano");

export const gatewayLabel = (value?: string | null) => {
  const provider = String(value || "").trim().toLowerCase();
  if (!provider) return "Sem cobrança";
  if (provider === "asaas") return "Asaas";
  if (provider === "cakto") return "Cakto";
  if (provider === "manual") return "Manual (admin)";
  return provider.charAt(0).toUpperCase() + provider.slice(1);
};

export const initials = (name?: string | null) =>
  String(name || "?")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "?";

export const statusTone = (status: CompanyStatusKey | string) =>
  ({
    active: "am-tone-success",
    internal: "am-tone-violet",
    trial: "am-tone-info",
    free: "am-tone-neutral",
    free_expired: "am-tone-warning",
    trial_ended: "am-tone-neutral",
    cancelling: "am-tone-warning",
    past_due: "am-tone-danger",
    inactive: "am-tone-danger",
    no_owner: "am-tone-neutral"
  })[status] || "am-tone-neutral";
