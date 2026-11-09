import type { PageConfig } from "./page";

export interface PageTemplate {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  is_default: boolean;
  config_json: PageConfig;
  /** Preenchido quando o modelo foi salvo pelo cliente (próprio da agência). */
  agency_id?: number | null;
  created_at?: string | null;
}

export interface CreateAgencyTemplatePayload {
  agency_id: number;
  name: string;
  description?: string | null;
  config_json: PageConfig;
}

export interface UpdateAgencyTemplatePayload {
  name?: string;
  description?: string | null;
}

export interface CreateTemplateFromPagePayload {
  page_id: number;
  name: string;
  slug: string;
  description?: string;
  is_default?: boolean;
}

export interface UpdateTemplatePayload {
  name?: string;
  slug?: string;
  description?: string | null;
  is_default?: boolean;
}
