import api from "./api";
import type { CompanyStatusKey } from "./companies";

// Painel do admin master: números da plataforma num período (somente leitura).
export interface DashboardBucket {
  start: string;
  end: string;
  received: number;
  payments: number;
  new_paying: number;
  signups: number;
  signups_paying: number;
}

export interface DashboardData {
  period: { start: string; end: string; days: number; weekly: boolean };
  mrr: number;
  arr: number;
  mrr_at_risk: number;
  paying_customers: number;
  arpa: number;
  mrr_by_plan: Array<{ plan: string; mrr: number; customers: number }>;
  received: number;
  received_previous: number;
  refunded: number;
  payments: number;
  new_paying: number;
  new_paying_previous: number;
  signups: number;
  signups_paying: number;
  signups_previous: number;
  left: number;
  trials_ending: number;
  companies: Partial<Record<CompanyStatusKey, number>>;
  users: number;
  pages: number;
  pages_published: number;
  series: DashboardBucket[];
}

export const getDashboard = async (params: { days?: number; start_date?: string; end_date?: string }) =>
  (await api.get<DashboardData>("/admin/master/dashboard", { params })).data;

// Usuários: as pessoas com acesso e em quais empresas estão.
export interface MasterUserCompany {
  id: number;
  name: string;
  slug: string;
  role: string;
  is_owner: boolean;
  status: CompanyStatusKey;
  status_label: string;
  plan: string | null;
}

export interface MasterUser {
  id: number;
  name: string;
  email: string;
  whatsapp: string | null;
  is_superuser: boolean;
  global_admin: boolean;
  source: string | null;
  created_at: string | null;
  last_access_at: string | null;
  active_sessions: number;
  online: boolean;
  companies: MasterUserCompany[];
}

export const listMasterUsers = async () => (await api.get<MasterUser[]>("/admin/master/users")).data;
export const revokeUserSessions = async (userId: number) =>
  (await api.post<{ detail: string }>(`/admin/online-sessions/user/${userId}/revoke`)).data;
export const deleteUser = async (userId: number) => (await api.delete<{ detail: string }>(`/admin/users/${userId}`)).data;
