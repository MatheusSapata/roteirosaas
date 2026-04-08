export interface LocalizedText {
  pt?: string;
  es?: string;
  [key: string]: string | undefined;
}

export interface LegalVariableDefinition {
  key: string;
  placeholder: string;
  label: LocalizedText;
  description: LocalizedText;
  sample_value: string;
}

export interface LegalVariableCategory {
  key: string;
  label: LocalizedText;
  variables: LegalVariableDefinition[];
}

export interface LegalVariablesResponse {
  categories: LegalVariableCategory[];
}

export interface LegalTemplateSummary {
  id: number;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface LegalTemplateDetail extends LegalTemplateSummary {
  content: string;
}

export interface LegalTemplateListResponse {
  items: LegalTemplateSummary[];
}

export interface LegalTemplatePayload {
  name: string;
  description?: string | null;
  content: string;
  is_active: boolean;
}

export interface LegalContract {
  id: number;
  sale_id: number;
  template_id?: number | null;
  buyer_name: string;
  product_name: string;
  total_amount: number;
  currency: string;
  status: string;
  pdf_url?: string | null;
  created_at: string;
  generated_at?: string | null;
  last_error?: string | null;
  signature_status: string;
  signature_token?: string | null;
  signature_link?: string | null;
  signature_signed_at?: string | null;
  signature_name?: string | null;
  signature_type?: string | null;
  signature_image_url?: string | null;
  signature_ip?: string | null;
  signature_user_agent?: string | null;
  signed_pdf_url?: string | null;
  signed_pdf_generated_at?: string | null;
  signed_pdf_size_bytes?: number | null;
  document_hash?: string | null;
  document_hash_algorithm?: string | null;
  verification_token?: string | null;
  verification_url?: string | null;
  verification_qr_image_data?: string | null;
  verification_generated_at?: string | null;
  agency_signature_status: string;
  agency_signature_signed_at?: string | null;
  agency_signature_type?: string | null;
  agency_signature_name?: string | null;
  agency_signature_role?: string | null;
  agency_signature_company?: string | null;
  agency_signature_city?: string | null;
  agency_signature_font_style?: string | null;
  agency_signature_typed_value?: string | null;
  agency_signature_image_url?: string | null;
}

export interface LegalContractListResponse {
  items: LegalContract[];
}

export interface LegalContractSignaturePublic {
  contract_id: number;
  sale_id: number;
  token: string;
  buyer_name: string;
  product_name: string;
  currency: string;
  total_amount: number;
  status: string;
  pdf_url?: string | null;
  signature_status: string;
  signature_signed_at?: string | null;
  signature_name?: string | null;
  signature_type?: string | null;
  signature_image_url?: string | null;
  agency_name?: string | null;
  agency_logo_url?: string | null;
  created_at: string;
  generated_at?: string | null;
  signed_pdf_url?: string | null;
  signed_pdf_generated_at?: string | null;
  signed_pdf_size_bytes?: number | null;
  document_hash?: string | null;
  document_hash_algorithm?: string | null;
  verification_token?: string | null;
  verification_url?: string | null;
  verification_qr_image_data?: string | null;
  verification_generated_at?: string | null;
  agency_signature_status: string;
  agency_signature_signed_at?: string | null;
  agency_signature_type?: string | null;
  agency_signature_name?: string | null;
  agency_signature_role?: string | null;
  agency_signature_company?: string | null;
  agency_signature_city?: string | null;
  agency_signature_font_style?: string | null;
  agency_signature_typed_value?: string | null;
  agency_signature_image_url?: string | null;
}

export interface LegalContractSignatureSubmitPayload {
  signature_type: "typed" | "drawn";
  full_name?: string | null;
  signature_image?: string | null;
  accepted_terms: boolean;
}

export interface LegalContractSignatureSubmitResponse {
  detail: LegalContractSignaturePublic;
}

export type LegalContractVerificationStatus = "valid" | "pending" | "incomplete" | "invalid" | "not_found";

export interface LegalContractVerificationDetail {
  status: LegalContractVerificationStatus;
  contract_id?: number | null;
  sale_id?: number | null;
  buyer_name?: string | null;
  product_name?: string | null;
  agency_name?: string | null;
  agency_logo_url?: string | null;
  created_at?: string | null;
  generated_at?: string | null;
  signature_signed_at?: string | null;
  signature_status?: string | null;
  signature_type?: string | null;
  agency_signature_status?: string | null;
  agency_signature_signed_at?: string | null;
  document_hash?: string | null;
  document_hash_algorithm?: string | null;
  signed_pdf_url?: string | null;
  signed_pdf_generated_at?: string | null;
  signed_pdf_size_bytes?: number | null;
  pdf_url?: string | null;
  verification_token?: string | null;
  verification_url?: string | null;
  verification_qr_image_data?: string | null;
  verification_generated_at?: string | null;
  message: string;
}

export type SignatureFontStyle = "classic" | "cursive" | "elegant";

export interface LegalSignatureProfilePayload {
  signature_type: "drawn" | "typed";
  signature_drawn_image?: string | null;
  signature_typed_value?: string | null;
  signature_font_style?: SignatureFontStyle | null;
  signature_display_name: string;
  signature_role?: string | null;
  signature_company_name?: string | null;
  signature_city?: string | null;
}

export interface LegalSignatureProfile extends Omit<LegalSignatureProfilePayload, "signature_drawn_image"> {
  signature_drawn_image_url?: string | null;
  signature_drawn_image_data?: string | null;
  updated_at?: string | null;
}
