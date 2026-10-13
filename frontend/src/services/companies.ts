import api from "./api";

export type CompanyStatusKey =
  | "active"
  | "trial"
  | "free"
  | "free_expired"
  | "trial_ended"
  | "cancelling"
  | "past_due"
  | "inactive"
  | "internal"
  | "combo"
  | "no_owner";
export type MediaStage = "hot" | "cool" | "archive" | "restoring" | "deleted";

export interface Company {
  id: number;
  name: string;
  slug: string;
  owner_id: number | null;
  owner_name: string | null;
  owner_email: string | null;
  owner_whatsapp: string | null;
  owner_is_superuser: boolean;
  plan: string | null;
  status: CompanyStatusKey;
  status_label: string;
  online: boolean;
  status_since: string | null;
  status_days: number | null;
  since_estimated: boolean;
  /** Até quando vale o acesso atual: fim do teste, prazo do gratuito ou fim do período pago. */
  access_until: string | null;
  valid_until: string | null;
  trial_plan: string | null;
  trial_ends_at: string | null;
  subscription_provider: string | null;
  subscription_status: string | null;
  subscription_asaas_subscription_id: string | null;
  subscription_cakto_order_id: string | null;
  subscription_cakto_subscription_code: string | null;
  billing_cycle: string | null;
  payment_method: string | null;
  mrr_amount: number;
  failed_attempts: number;
  members_count: number;
  created_at: string | null;
  last_access_at: string | null;
  pages_total: number;
  pages_published: number;
  visits_30d: number;
  media_stage: MediaStage;
  media_files: number;
  media_bytes: number;
  media_shared_skipped: number;
  media_measured_at: string | null;
  media_error: string | null;
  next_step: string | null;
}

export interface CompaniesResponse {
  items: Company[];
  summary: {
    counts: Partial<Record<CompanyStatusKey, number>>;
    total: number;
    inactive_over_30: number;
    inactive_bytes: number;
    archived_bytes: number;
    automation: boolean;
    rules: { cool_after_days: number; archive_after_days: number; orphan_grace_days: number; free_access_days?: number };
  };
}

export interface StorageStatus {
  status: "idle" | "running" | "done" | "error";
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  summary: {
    total_files?: number;
    total_bytes?: number;
    tiers?: Record<string, { files: number; bytes: number }>;
    inactive?: { companies: number; files: number; bytes: number };
  };
  orphans: { groups: number; bytes: number; ready_groups: number; ready_bytes: number; oldest_seen_at: string | null };
}

export interface CompanyMember {
  user_id: number;
  name: string;
  email: string;
  role: string;
  is_owner: boolean;
  last_access_at: string | null;
}

export interface CompanyPage {
  id: number;
  title: string;
  slug: string;
  status: string;
  published_at: string | null;
  updated_at: string | null;
  visits: number;
  clicks: number;
}

export interface CompanyTracking {
  id: number;
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  utm_term: string | null;
  utm_content: string | null;
  referrer: string | null;
  created_at: string | null;
}

export interface CompanyDetail {
  id: number;
  slug: string;
  members: CompanyMember[];
  pages: CompanyPage[];
  tracking: CompanyTracking[];
}

const base = "/admin/master/companies";

export const listCompanies = async () => (await api.get<CompaniesResponse>(base)).data;
export const getCompanyDetail = async (id: number) => (await api.get<CompanyDetail>(`${base}/${id}`)).data;
export const getStorageStatus = async () => (await api.get<StorageStatus>(`${base}/storage`)).data;
export const startStorageAnalysis = async () => (await api.post<{ status: string }>(`${base}/storage/analyze`)).data;
export const moveCompanyMedia = async (id: number, action: "cool" | "archive" | "restore") =>
  (await api.post(`${base}/${id}/media/${action}`)).data;
export const deleteCompanyMedia = async (id: number, confirm: string) =>
  (await api.post(`${base}/${id}/media/delete`, { confirm })).data;
export const deleteReadyOrphans = async (confirm: string) =>
  (await api.post<{ deleted_files: number; deleted_bytes: number; kept: number }>(`${base}/orphans/delete-ready`, { confirm })).data;
