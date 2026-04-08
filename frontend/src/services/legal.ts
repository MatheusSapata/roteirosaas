import api from "./api";
import type {
  LegalContract,
  LegalContractListResponse,
  LegalContractSignaturePublic,
  LegalContractSignatureSubmitPayload,
  LegalContractSignatureSubmitResponse,
  LegalContractVerificationDetail,
  LegalContractAuditEventList,
  LegalSignatureProfile,
  LegalSignatureProfilePayload,
  LegalTemplateDetail,
  LegalTemplateListResponse,
  LegalTemplatePayload,
  LegalVariablesResponse,
} from "../types/legal";

export const listLegalTemplates = () => api.get<LegalTemplateListResponse>("/legal/templates");

export const getLegalTemplateDetail = (templateId: number) =>
  api.get<LegalTemplateDetail>(`/legal/templates/${templateId}`);

export const createLegalTemplate = (payload: LegalTemplatePayload) =>
  api.post<LegalTemplateDetail>("/legal/templates", payload);

export const updateLegalTemplate = (templateId: number, payload: LegalTemplatePayload) =>
  api.put<LegalTemplateDetail>(`/legal/templates/${templateId}`, payload);

export const deleteLegalTemplate = (templateId: number) => api.delete(`/legal/templates/${templateId}`);

export const getLegalVariables = () => api.get<LegalVariablesResponse>("/legal/variables");

export const listLegalContracts = () => api.get<LegalContractListResponse>("/legal/contracts");

export const getLegalContractDetail = (contractId: number) =>
  api.get<LegalContract>(`/legal/contracts/${contractId}`);

export const getLegalContractVerification = (contractId: number) =>
  api.get<LegalContractVerificationDetail>(`/legal/contracts/${contractId}/verification`);

export const getLegalContractAuditEvents = (
  contractId: number,
  params?: { limit?: number; full?: boolean }
) => api.get<LegalContractAuditEventList>(`/legal/contracts/${contractId}/audit-events`, { params });

export const regenerateLegalContractVerification = (contractId: number) =>
  api.post<LegalContractVerificationDetail>(`/legal/contracts/${contractId}/verification/regenerate`, {});

export const getPublicSignatureContract = (token: string) =>
  api.get<LegalContractSignaturePublic>(`/public/legal/signatures/${token}`);

export const submitSignatureContract = (token: string, payload: LegalContractSignatureSubmitPayload) =>
  api.post<LegalContractSignatureSubmitResponse>(`/public/legal/signatures/${token}`, payload);

export const getPublicContractVerification = (token: string) =>
  api.get<LegalContractVerificationDetail>(`/public/legal/verification/${token}`);

export const getPublicContractAuditEvents = (
  token: string,
  params?: { limit?: number; full?: boolean }
) => api.get<LegalContractAuditEventList>(`/public/legal/verification/${token}/audit-events`, { params });

export const getLegalSignatureProfile = () =>
  api.get<LegalSignatureProfile | null>("/legal/signature-profile");

export const saveLegalSignatureProfile = (payload: LegalSignatureProfilePayload) =>
  api.put<LegalSignatureProfile>("/legal/signature-profile", payload);

export const deleteLegalSignatureProfile = () => api.delete("/legal/signature-profile");
