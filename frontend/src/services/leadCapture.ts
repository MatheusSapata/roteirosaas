import api from "./api";
import platformApi from "./platformApi";
import type { LeadForm, LeadFormSubmissionPayload } from "../types/leads";

export const fetchPublicLeadForm = async (
  formId: string | number,
  params?: { pageId?: string | number | null; pageSlug?: string | null }
) => {
  const normalizedId = String(formId);
  const res = await platformApi.get<LeadForm>(`/public/lead-forms/${normalizedId}`, {
    params: {
      pageId: params?.pageId ?? undefined,
      pageSlug: params?.pageSlug ?? undefined
    }
  });
  return res.data;
};

export const submitLeadForm = async (formId: string | number, payload: LeadFormSubmissionPayload) => {
  const normalizedId = String(formId);
  const body: LeadFormSubmissionPayload = {
    ...payload,
    formId: normalizedId
  };
  await platformApi.post(`/public/lead-forms/${normalizedId}/submit`, body);
};
