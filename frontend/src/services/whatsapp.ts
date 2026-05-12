import api from "./api";
import type {
  AdminMasterWhatsAppConnection,
  AdminMasterWhatsAppInboxPermission,
  AdminMasterWhatsAppOverview,
  WhatsAppConnection,
  WhatsAppConnectionCreatePayload,
  WhatsAppConnectionStatusResponse,
  WhatsAppConversation,
  WhatsAppInboxAccessResponse,
  WhatsAppMessage,
  WhatsAppQrResponse
} from "../types/whatsapp";

export const listWhatsAppConnections = async (agencyId: number) => {
  const response = await api.get<WhatsAppConnection[]>("/whatsapp/connections", {
    params: { agencyId }
  });
  return response.data;
};

export const createWhatsAppConnection = async (payload: WhatsAppConnectionCreatePayload) => {
  const response = await api.post<WhatsAppConnection>("/whatsapp/connections", payload);
  return response.data;
};

export const getWhatsAppConnectionQr = async (connectionId: number, agencyId: number) => {
  const response = await api.get<WhatsAppQrResponse>(`/whatsapp/connections/${connectionId}/qr`, {
    params: { agencyId }
  });
  return response.data;
};

export const getWhatsAppConnectionStatus = async (connectionId: number, agencyId: number) => {
  const response = await api.get<WhatsAppConnectionStatusResponse>(`/whatsapp/connections/${connectionId}/status`, {
    params: { agencyId }
  });
  return response.data;
};

export const disconnectWhatsAppConnection = async (connectionId: number, agencyId: number) => {
  const response = await api.post<{ status: string }>(`/whatsapp/connections/${connectionId}/disconnect`, null, {
    params: { agencyId }
  });
  return response.data;
};

export const listWhatsAppConversations = async (agencyId: number, connectionId?: number | null) => {
  const response = await api.get<WhatsAppConversation[]>("/whatsapp/conversations", {
    params: { agencyId, ...(connectionId ? { connectionId } : {}) }
  });
  return response.data;
};

export const listWhatsAppMessages = async (conversationId: number, agencyId: number) => {
  const response = await api.get<WhatsAppMessage[]>(`/whatsapp/conversations/${conversationId}/messages`, {
    params: { agencyId }
  });
  return response.data;
};

export const sendWhatsAppText = async (conversationId: number, agencyId: number, text: string) => {
  const response = await api.post<WhatsAppMessage>(
    `/whatsapp/conversations/${conversationId}/send-text`,
    { text },
    { params: { agencyId } }
  );
  return response.data;
};

export const sendWhatsAppMedia = async (
  conversationId: number,
  agencyId: number,
  file: File,
  caption = ""
) => {
  const form = new FormData();
  form.append("file", file);
  form.append("caption", caption);
  const response = await api.post<WhatsAppMessage>(`/whatsapp/conversations/${conversationId}/send-media`, form, {
    params: { agencyId },
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

export const markWhatsAppConversationRead = async (conversationId: number, agencyId: number) => {
  const response = await api.post(`/whatsapp/conversations/${conversationId}/mark-read`, null, {
    params: { agencyId }
  });
  return response.data;
};

export const updateWhatsAppConversation = async (
  conversationId: number,
  agencyId: number,
  payload: { remoteName?: string; clientId?: number; opportunityId?: number }
) => {
  const response = await api.patch<WhatsAppConversation>(`/whatsapp/conversations/${conversationId}`, payload, {
    params: { agencyId }
  });
  return response.data;
};

export const ensureWhatsAppConversation = async (
  agencyId: number,
  payload: { remotePhone?: string; remoteName?: string; clientId?: number }
) => {
  const response = await api.post<WhatsAppConversation>("/whatsapp/conversations/ensure", payload, {
    params: { agencyId }
  });
  return response.data;
};

export const getWhatsAppUnreadCount = async (agencyId: number) => {
  const response = await api.get<{ total_unread: number }>("/whatsapp/unread-count", {
    params: { agencyId }
  });
  return response.data;
};

export const getWhatsAppInboxAccess = async (agencyId?: number | null) => {
  const response = await api.get<WhatsAppInboxAccessResponse>("/whatsapp/inbox-access", {
    params: agencyId ? { agencyId } : {}
  });
  return response.data;
};

export const getAdminMasterWhatsAppOverview = async () => {
  const response = await api.get<AdminMasterWhatsAppOverview>("/admin-master/whatsapp/overview");
  return response.data;
};

export const listAdminMasterWhatsAppConnections = async (q = "") => {
  const response = await api.get<AdminMasterWhatsAppConnection[]>("/admin-master/whatsapp/connections", {
    params: q ? { q } : {}
  });
  return response.data;
};

export const listAdminMasterInboxPermissions = async (q = "") => {
  const response = await api.get<AdminMasterWhatsAppInboxPermission[]>("/admin-master/whatsapp/inbox-permissions", {
    params: q ? { q } : {}
  });
  return response.data;
};

export const upsertAdminMasterInboxPermission = async (payload: { userId?: number; agencyId?: number; enabled: boolean }) => {
  const response = await api.post<AdminMasterWhatsAppInboxPermission>("/admin-master/whatsapp/inbox-permissions", payload);
  return response.data;
};

export const revokeAdminMasterInboxPermission = async (permissionId: number) => {
  await api.delete(`/admin-master/whatsapp/inbox-permissions/${permissionId}`);
};
