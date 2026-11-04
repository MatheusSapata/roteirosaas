import type { Company } from "../../../services/companies";

export const planOptions = [
  { value: "free", label: "Começo (gratuito)" },
  { value: "essencial", label: "Profissional" },
  { value: "growth", label: "Agência" },
  { value: "infinity", label: "Escala" },
  { value: "trial", label: "Trial" },
  { value: "teste", label: "Teste (interno)" }
];

export const statusOptions = [
  { value: "active", label: "Ativa" },
  { value: "pending", label: "Pendente" },
  { value: "failed", label: "Falha" },
  { value: "past_due", label: "Em atraso" },
  { value: "cancel_at_period_end", label: "Cancelar no fim da validade" },
  { value: "cancelled", label: "Cancelada" },
  { value: "cancelled_admin", label: "Cancelada pelo admin" },
  { value: "inactive", label: "Inativa" }
];

export const subscriptionStatusLabel = (company: Company) => {
  const raw = (company.subscription_status || "").toLowerCase();
  // Antes do "cancelled_admin", o cancelamento imediato da Asaas ficava como "past_due" sem id de assinatura.
  if (raw === "past_due" && company.subscription_provider === "asaas" && !company.subscription_asaas_subscription_id) return "Cancelada";
  return statusOptions.find(option => option.value === raw)?.label || company.subscription_status || "Sem assinatura";
};

const roleLabels: Record<string, string> = { owner: "Dono", admin: "Administrador", editor: "Editor", viewer: "Leitura", member: "Membro" };
export const roleLabel = (role: string) => roleLabels[role] || role || "Membro";

const billingTypeLabels: Record<string, string> = {
  BOLETO: "Boleto",
  CREDIT_CARD: "Cartão",
  DEBIT_CARD: "Débito",
  PIX: "Pix",
  UNDEFINED: "A escolher",
  card: "Cartão",
  credit_card: "Cartão",
  pix: "Pix",
  pix_automatic: "Pix automático",
  boleto: "Boleto"
};
export const billingTypeLabel = (value?: string | null) => (value ? billingTypeLabels[value] || value : "—");

export const invoiceBucketMeta: Record<string, { label: string; tone: string }> = {
  paid: { label: "Paga", tone: "am-tone-success" },
  overdue: { label: "Vencida", tone: "am-tone-danger" },
  upcoming: { label: "A vencer", tone: "am-tone-info" },
  replaced: { label: "Substituída", tone: "am-tone-neutral" }
};

export const sendStatusMeta: Record<string, { label: string; tone: string }> = {
  sent: { label: "Enviado", tone: "am-tone-success" },
  sending: { label: "Saindo", tone: "am-tone-info" },
  failed: { label: "Falhou", tone: "am-tone-danger" },
  cancelled: { label: "Cancelado", tone: "am-tone-neutral" },
  not_configured: { label: "Não saiu (SMTP)", tone: "am-tone-warning" }
};

export const channelLabel = (channel?: string | null) => (channel === "whatsapp" ? "WhatsApp" : channel === "email" ? "E-mail" : channel || "—");

export const formatPlainDate = (value?: string | null) => {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  return day && month && year ? `${day}/${month}/${year}` : value;
};
