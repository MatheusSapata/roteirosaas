export type LeadFieldType = "name" | "phone" | "email" | "city";

export interface LeadFormField {
  id: string;
  type: LeadFieldType;
  label: string;
  placeholder?: string;
  required: boolean;
}

export interface LeadForm {
  id: number | string;
  name: string;
  title: string;
  subtitle?: string;
  buttonLabel: string;
  buttonColor?: string;
  fields: LeadFormField[];
  defaultStatusId?: string | number | null;
  defaultStatusName?: string | null;
  alreadySubmitted?: boolean;
  total_leads?: number;
  created_at?: string;
  updated_at?: string;
}

export interface LeadFormPayload {
  name: string;
  title: string;
  subtitle?: string;
  buttonLabel: string;
  buttonColor?: string;
  fields: LeadFormField[];
  defaultStatusId?: string | number | null;
}

export interface LeadContact {
  id: string | number;
  form_id: string | number;
  form_name: string;
  page_id?: number | string | null;
  page_title?: string | null;
  page_slug?: string | null;
  page_url?: string | null;
  name?: string;
  phone?: string;
  email?: string;
  city?: string;
  status_id?: string | number | null;
  status_name?: string | null;
  status_color?: string | null;
  created_at?: string;
}

export interface LeadContactGroup {
  formId: string;
  formName: string;
  contacts: LeadContact[];
}

export interface LeadFormSubmissionField {
  fieldId: string;
  type: LeadFieldType;
  value: string;
}

export interface LeadFormSubmissionPayload {
  formId?: string | number;
  values: LeadFormSubmissionField[];
  source?: string;
  pageId?: number | null;
  pageSlug?: string | null;
  pageTitle?: string | null;
  pageUrl?: string | null;
}

export interface PageLeadCaptureConfig {
  formId: string;
  optional?: boolean;
}

export interface LeadStatus {
  id: string | number;
  name: string;
  color: string;
  created_at?: string;
  updated_at?: string;
}

export interface LeadStatusPayload {
  name: string;
  color: string;
}
