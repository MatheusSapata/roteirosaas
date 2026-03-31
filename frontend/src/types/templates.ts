import type { PageConfig } from "./page";

export interface PageTemplate {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  is_default: boolean;
  config_json: PageConfig;
}

export interface CreateTemplateFromPagePayload {
  page_id: number;
  name: string;
  slug: string;
  description?: string;
  is_default?: boolean;
}
