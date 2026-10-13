import api from "./api";

// Painel de receita: somente leitura (não cria, altera nem cancela cobrança).
export interface RevenueItem {
  subscription_id: number;
  user_id: number;
  name: string;
  email: string;
  plan: string;
  cycle: string;
  provider: string;
  method: string;
  due_on: string;
  amount: number;
  alerts: string[];
}

export interface RevenuePayment {
  source: string;
  paid_at: string;
  gross: number;
  net: number;
  method: string;
  email: string | null;
  description: string;
}

export interface RevenueOverview {
  month: string;
  mrr: number;
  arr: number;
  mrr_at_risk: number;
  paying_customers: number;
  arpa: number;
  mrr_by_plan: Record<string, number>;
  mrr_by_cycle: Record<string, number>;
  mrr_by_method: Record<string, number>;
  month_received_gross: number;
  month_received_net: number;
  month_refunded: number;
  month_payments: number;
  /** Pagamentos de outros produtos na mesma conta da Asaas/Cakto (ex.: combo da Viaje On), fora da receita. */
  month_other_received: number;
  month_other_payments: number;
  month_to_receive: number | null;
  month_to_receive_count: number | null;
  month_expected: number;
  overdue: number;
  overdue_items: RevenueItem[];
  upcoming: RevenueItem[];
  upcoming_total: number;
  upcoming_by_week: Record<string, number>;
  horizon_days: number;
  payments: RevenuePayment[];
}

export interface AsaasOpenCharges {
  until: string;
  pending: { count: number; amount: number };
  overdue: { count: number; amount: number };
}

export const getRevenue = async (month?: string, horizon = 60) =>
  (await api.get<RevenueOverview>("/admin/master/revenue", { params: { month, horizon } })).data;
export const getAsaasOpenCharges = async () => (await api.get<AsaasOpenCharges>("/admin/master/revenue/asaas-open")).data;
