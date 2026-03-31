import api from "./api";
import type { CreateTemplateFromPagePayload, PageTemplate, UpdateTemplatePayload } from "../types/templates";

export const listPageTemplates = async () => {
  const response = await api.get<PageTemplate[]>("/page-templates");
  return response.data;
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
