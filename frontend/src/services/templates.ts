import api from "./api";
import type {
  CreateAgencyTemplatePayload,
  CreateTemplateFromPagePayload,
  PageTemplate,
  UpdateAgencyTemplatePayload,
  UpdateTemplatePayload
} from "../types/templates";

/** Sem agência: só os modelos da plataforma. Com agência: os da plataforma + os salvos por ela. */
export const listPageTemplates = async (agencyId?: number | null) => {
  const response = await api.get<PageTemplate[]>("/page-templates", {
    params: agencyId ? { agency_id: agencyId } : undefined
  });
  return response.data;
};

export const createAgencyTemplate = async (payload: CreateAgencyTemplatePayload) => {
  const response = await api.post<PageTemplate>("/page-templates/agency", payload);
  return response.data;
};

export const updateAgencyTemplate = async (templateId: number, payload: UpdateAgencyTemplatePayload) => {
  const response = await api.patch<PageTemplate>(`/page-templates/agency/${templateId}`, payload);
  return response.data;
};

export const deleteAgencyTemplate = async (templateId: number) => {
  await api.delete(`/page-templates/agency/${templateId}`);
};

export const getPageTemplate = async (templateId: number) => {
  const response = await api.get<PageTemplate>(`/page-templates/${templateId}`);
  return response.data;
};

export const createTemplateFromPage = async (payload: CreateTemplateFromPagePayload) => {
  const response = await api.post<PageTemplate>("/page-templates/from-page", payload);
  return response.data;
};

export const updateTemplate = async (templateId: number, payload: UpdateTemplatePayload) => {
  const response = await api.put<PageTemplate>(`/page-templates/${templateId}`, payload);
  return response.data;
};

export const deleteTemplate = async (templateId: number) => {
  await api.delete(`/page-templates/${templateId}`);
};
