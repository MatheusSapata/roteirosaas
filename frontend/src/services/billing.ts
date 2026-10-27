import api from "./api";
import type { BillingCycle } from "../utils/billingCycle";

export type InvoiceBucket = "paid" | "overdue" | "upcoming" | "replaced";

export type PixAutomaticStatus = "ACTIVE" | "CANCELLED" | "EXPIRED" | "REFUSED";

export interface BillingRenewalOffer {
  plan: string;
  billing_cycle: BillingCycle;
  amount: number;
  title: string;
}

export interface BillingInvoice {
  id: string;
  customer_id?: string | null;
  subscription_id?: string | null;
  status: string;
  billing_type?: string | null;
  description?: string | null;
  value: number;
  due_date?: string | null;
  payment_date?: string | null;
  invoice_url?: string | null;
  bank_slip_url?: string | null;
  receipt_url?: string | null;
  pay_url?: string | null;
  download_url?: string | null;
  is_paid: boolean;
  bucket: InvoiceBucket;
  period_start?: string | null;
  period_end?: string | null;
}

export interface BillingAccount {
  status: "active" | "past_due" | "blocked" | "cancelling" | "inactive";
  blocked: boolean;
  access_until?: string | null;
  open_amount: number;
  open_count: number;
  next_charge?: { due_date: string; amount: number } | null;
  unlocking_invoice_id?: string | null;
  pix_automatic_status?: PixAutomaticStatus | null;
  renewal_offer?: BillingRenewalOffer | null;
}

export interface BillingInvoicesResponse {
  items: BillingInvoice[];
  total: number;
  counts: Record<InvoiceBucket, number>;
  account?: BillingAccount | null;
}

export interface InvoiceSyncResult {
  paid: boolean;
  applied: boolean;
  status: string;
  invoice: BillingInvoice;
}

export const getBillingInvoices = async () => {
  const response = await api.get<BillingInvoicesResponse>("/billing/invoices");
  return response.data;
};

/** Confere a fatura no Asaas na hora e, se estiver paga, libera a conta. Limite: 1 chamada a cada 10 s. */
export const syncBillingInvoice = async (invoiceId: string) => {
  const response = await api.post<InvoiceSyncResult>(`/billing/invoices/${encodeURIComponent(invoiceId)}/sync`);
  return response.data;
};

export const formatBRL = (value: number | string | null | undefined) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value) || 0);

export const formatInvoiceDate = (value?: string | null) => {
  if (!value) return "--";
  const parsed = value.length === 10 ? new Date(`${value}T00:00:00`) : new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("pt-BR");
};

export const formatInvoiceDayMonth = (value?: string | null) => {
  if (!value) return "--";
  const parsed = value.length === 10 ? new Date(`${value}T00:00:00`) : new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
};

export const invoiceMonthName = (value?: string | null) => {
  if (!value) return "";
  const parsed = value.length === 10 ? new Date(`${value}T00:00:00`) : new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleDateString("pt-BR", { month: "long" });
};
