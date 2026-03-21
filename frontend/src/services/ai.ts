import api from "./api";

export interface AiAttachmentPayload {
  name: string;
  mime_type?: string;
  data: string;
}

export interface AiManualMediaPayload {
  url: string;
  label?: string | null;
  section_hint?: "hero" | "story" | "gallery" | "photo" | "banner" | null;
}

export interface AiImageSelectionPayload {
  section: "hero" | "story" | "gallery" | "photo" | "banner" | "itinerary";
  prompt_hint?: string | null;
  count?: number | null;
  per_day?: boolean;
}

export interface AiAnswersPayload {
  destination?: string | null;
  travel_dates?: string | null;
  audience?: string | null;
  highlights?: string | null;
  pricing?: string | null;
  included_services?: string | null;
  exclusions?: string | null;
  urgency?: string | null;
  call_to_action?: string | null;
  tone?: string | null;
}

export interface AiPagePayload {
  agency_id: number;
  briefing: string;
  preferred_title?: string | null;
  answers: AiAnswersPayload;
  attachments: AiAttachmentPayload[];
  manual_media: AiManualMediaPayload[];
  video_url?: string | null;
  generate_ai_images: boolean;
  ai_image_targets: AiImageSelectionPayload[];
  auto_publish: boolean;
  theme_mode?: "light" | "dark";
}

export interface AiPageResponse {
  page_id: number;
  redirect_url: string;
  published: boolean;
  credits_spent: number;
  credits_balance: number;
  message: string;
}

export type FollowUpKey =
  | "destination"
  | "travel_dates"
  | "audience"
  | "included_services"
  | "highlights"
  | "pricing"
  | "call_to_action"
  | "urgency"
  | "exclusions"
  | "tone";

export interface AiBriefingInterpretPayload {
  agency_id: number;
  briefing: string;
  attachments: AiAttachmentPayload[];
}

export interface AiBriefingInterpretResponse {
  summary?: string | null;
  answers: AiAnswersPayload;
  missing: FollowUpKey[];
  notes: string[];
  raw_text?: string | null;
}

export interface AiCreditTransaction {
  id: number;
  delta: number;
  reason: string;
  created_at: string;
  metadata?: Record<string, unknown> | null;
}

export interface AiCreditWallet {
  balance: number;
  transactions: AiCreditTransaction[];
}

export const fetchAiCredits = async () => {
  const { data } = await api.get<AiCreditWallet>("/ai/credits");
  return data;
};

export const createAiPage = async (payload: AiPagePayload) => {
  const { data } = await api.post<AiPageResponse>("/ai/pages", payload);
  return data;
};

export const interpretBriefing = async (payload: AiBriefingInterpretPayload) => {
  const { data } = await api.post<AiBriefingInterpretResponse>("/ai/briefing/interpret", payload);
  return data;
};
