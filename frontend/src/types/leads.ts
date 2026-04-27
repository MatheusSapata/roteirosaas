export type LeadFieldType = "name" | "phone" | "email" | "city" | "cpf" | "birthdate";

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
  showLogo?: boolean;
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
  showLogo?: boolean;
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
  cpf?: string | null;
  phone?: string;
  email?: string;
  city?: string;
  source?: string | null;
  opportunity_name?: string | null;
  estimated_value_cents?: number | null;
  status_id?: string | number | null;
  status_name?: string | null;
  status_color?: string | null;
  client_id?: string | number | null;
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

export interface ClientSummary {
  id: number;
  name: string;
  cpf?: string | null;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  zipcode?: string | null;
  street?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  state?: string | null;
}

export interface NoteAuthor {
  id?: number | null;
  name?: string | null;
}

export interface OpportunityNote {
  id: number;
  opportunityId: number;
  agencyId: number;
  userId?: number | null;
  content: string;
  created_at?: string;
  updated_at?: string | null;
  author?: NoteAuthor | null;
}

export interface ClientNote {
  id: number;
  clientId: number;
  agencyId: number;
  userId?: number | null;
  content: string;
  created_at?: string;
  updated_at?: string | null;
  author?: NoteAuthor | null;
}

export interface LeadDocument {
  id: number;
  agencyId: number;
  clientId?: number | null;
  opportunityId?: number | null;
  uploadedByUserId?: number | null;
  fileName: string;
  fileUrl: string;
  fileType?: string | null;
  fileSize?: number | null;
  created_at?: string;
  sourceLabel?: string | null;
}

export interface OpportunityDetails {
  id: number;
  agencyId: number;
  formId: number;
  formName: string;
  pageId?: number | null;
  pageTitle?: string | null;
  pageSlug?: string | null;
  pageUrl?: string | null;
  name?: string | null;
  cpf?: string | null;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  birthdate?: string | null;
  source?: string | null;
  statusId?: number | null;
  statusName?: string | null;
  statusColor?: string | null;
  opportunityName?: string | null;
  estimatedValueCents?: number | null;
  expectedCloseDate?: string | null;
  internalNotes?: string | null;
  autoLinkedBy?: "cpf" | "email" | "phone" | null;
  autoLinkedAt?: string | null;
  closeOutcome?: "won" | "lost" | null;
  closedAt?: string | null;
  responsibleUserId?: number | null;
  created_at?: string;
  updated_at?: string | null;
  payload?: Record<string, unknown> | null;
  client?: ClientSummary | null;
  notes: OpportunityNote[];
  documents: LeadDocument[];
  clientSuggestions: ClientSummary[];
}

export interface OpportunityUpdatePayload {
  opportunityName?: string | null;
  estimatedValueCents?: number | null;
  statusId?: number | string | null;
  internalNotes?: string | null;
  responsibleUserId?: number | string | null;
  expectedCloseDate?: string | null;
}

export interface OpportunityFinalizePayload {
  outcome: "won" | "lost";
  note?: string | null;
}

export interface ManualOpportunityPayload {
  agencyId: number;
  clientId?: number | null;
  name: string;
  opportunityName?: string | null;
  cpf?: string | null;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  birthdate?: string | null;
  estimatedValueCents?: number | null;
  statusId?: number | string | null;
  internalNotes?: string | null;
  responsibleUserId?: number | string | null;
  expectedCloseDate?: string | null;
}

export interface ClientPayload {
  agencyId: number;
  name: string;
  cpf?: string | null;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  zipcode?: string | null;
  street?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  state?: string | null;
  birthdate?: string | null;
  notes?: string | null;
  tags?: string[] | null;
}

export interface Client {
  id: number;
  agencyId: number;
  name: string;
  cpf?: string | null;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  zipcode?: string | null;
  street?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  state?: string | null;
  birthdate?: string | null;
  notes?: string | null;
  tags?: string[] | null;
  opportunitiesCount: number;
  openOpportunitiesCount: number;
  totalEstimatedValueCents: number;
  lastOpportunityAt?: string | null;
  created_at?: string;
  updated_at?: string | null;
}

export interface ClientDetail extends Client {
  opportunities: OpportunityDetails[];
  notesTimeline: ClientNote[];
  documents: LeadDocument[];
}

export interface ClientFilters {
  q?: string;
  city?: string;
  hasOpenOpportunities?: boolean;
  withoutOpportunities?: boolean;
  createdFrom?: string;
  createdTo?: string;
}
