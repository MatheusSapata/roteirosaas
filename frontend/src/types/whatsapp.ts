export type WhatsAppConnectionStatus = "connected" | "disconnected" | "connecting" | "qr_needed" | "error";

export interface WhatsAppConnection {
  id: number;
  agencyId: number;
  name: string;
  instanceName: string;
  phoneNumber: string | null;
  status: string;
  isDefault: boolean;
  createdByUserId: number | null;
  connectedAt: string | null;
  disconnectedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface WhatsAppConnectionStatusResponse {
  connectionId: number;
  instanceName: string;
  status: string;
  rawState?: string | null;
  raw?: Record<string, unknown>;
}

export interface WhatsAppConnectionCreatePayload {
  agencyId: number;
  name: string;
}

export interface WhatsAppQrResponse {
  connectionId: number;
  instanceName: string;
  qr_code_base64?: string | null;
  pairing_code?: string | null;
  code?: string | null;
  count?: number | null;
  diagnosis?: string | null;
  diagnostics?: unknown;
  attempts?: unknown;
  raw?: unknown;
}

export interface WhatsAppConversation {
  id: number;
  agencyId: number;
  connectionId: number;
  clientId: number | null;
  opportunityId: number | null;
  remotePhone: string;
  remoteName: string | null;
  avatarUrl?: string | null;
  lastMessageText: string | null;
  lastMessageAt: string | null;
  unreadCount: number;
  openOpportunitiesCount?: number | null;
  openOpportunitiesValueCents?: number | null;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface WhatsAppMessage {
  id: number;
  agencyId: number;
  connectionId: number;
  conversationId: number;
  externalMessageId: string | null;
  direction: "inbound" | "outbound";
  messageType: string;
  body: string;
  status: string | null;
  remotePhone: string;
  mediaUrl?: string | null;
  mediaMimeType?: string | null;
  mediaFileName?: string | null;
  mediaSize?: number | null;
  mediaDuration?: number | null;
  sentAt: string | null;
  receivedAt: string | null;
  createdAt: string | null;
}

export interface WhatsAppUnreadCountResponse {
  total_unread: number;
}

export interface WhatsAppInboxAccessResponse {
  enabled: boolean;
}

export interface AdminMasterWhatsAppOverview {
  total_connections: number;
  connected_connections: number;
  disconnected_connections: number;
  connecting_connections: number;
  agencies_with_whatsapp: number;
  inbox_enabled_users: number;
  inbox_enabled_agencies: number;
}

export interface AdminMasterWhatsAppConnection {
  id: number;
  agency_id: number;
  agency_name: string | null;
  owner_user_id: number | null;
  owner_name: string | null;
  owner_email: string | null;
  name: string;
  phone_number: string | null;
  status: string;
  instance_name: string;
  created_at: string | null;
  connected_at: string | null;
  updated_at: string | null;
}

export interface AdminMasterWhatsAppInboxPermission {
  id: number;
  user_id: number | null;
  user_name: string | null;
  user_email: string | null;
  agency_id: number | null;
  agency_name: string | null;
  enabled: boolean;
  granted_at: string | null;
  revoked_at: string | null;
  granted_by_user_id: number | null;
  granted_by_name: string | null;
  created_at: string | null;
  updated_at: string | null;
}
