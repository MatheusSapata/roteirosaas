import type { PageSection } from "../types/page";
import api from "./api";
import { API_BASE_URL } from "../utils/apiBase";

export interface AiAssistantChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AiAssistantHistoryMessage extends AiAssistantChatMessage {
  id: number;
  created_at: string;
}

/** Seção da página como está no editor agora, para a IA saber o que já existe e o que trocar. */
export interface AiPageSectionSummary {
  type: string;
  anchorId?: string;
  enabled?: boolean;
  title?: unknown;
  label?: unknown;
  caption?: unknown;
  headingLabel?: unknown;
  badge?: unknown;
  /** Diferenciais: cards com ícones da biblioteca ("icon") ou emojis ("emoji"). */
  iconMode?: string;
  /** Menu do topo como está (a IA mexe só no que pedirem, sem apagar os itens atuais). */
  mode?: string;
  stickyEnabled?: boolean;
  actionType?: string;
  contactLabel?: unknown;
  links?: Array<{ label: unknown; target?: string; targetType?: string }>;
}

interface AiAssistantChatResponse {
  reply: string;
}

export interface AiAssistantUsageResponse {
  period_key: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  unlimited: boolean;
  renewal_at?: string | null;
}

interface AiAssistantCreatePageBaseResponse {
  page: unknown;
}

export const sendAiAssistantConversation = async (
  pageId: number,
  conversation: AiAssistantChatMessage[],
  attachments: File[] = [],
  pageSections: AiPageSectionSummary[] = [],
  includeImages = true
): Promise<{ reply: string; usage?: AiAssistantUsageResponse }> => {
  const form = new FormData();
  form.append("page_id", String(pageId));
  form.append("conversation", JSON.stringify(conversation));
  form.append("page_sections", JSON.stringify(pageSections));
  form.append("include_images", includeImages ? "true" : "false");

  for (const file of attachments) {
    form.append("attachments", file, file.name);
  }

  const response = await api.post<AiAssistantChatResponse>("/ai-assistant/chat", form, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });

  const headers = response.headers || {};
  const parseNumber = (value: unknown): number | null => {
    if (value === undefined || value === null || value === "") return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  };

  return {
    reply: response.data.reply,
    usage: {
      period_key: String(headers["x-ai-assistant-period"] || ""),
      used: parseNumber(headers["x-ai-assistant-usage"]) ?? 0,
      limit:
        String(headers["x-ai-assistant-limit"] || "").toLowerCase() === "unlimited"
          ? null
          : parseNumber(headers["x-ai-assistant-limit"]),
      remaining:
        String(headers["x-ai-assistant-remaining"] || "").toLowerCase() === "unlimited"
          ? null
          : parseNumber(headers["x-ai-assistant-remaining"]),
      unlimited: String(headers["x-ai-assistant-limit"] || "").toLowerCase() === "unlimited"
    }
  };
};

export const fetchAiAssistantHistory = async (pageId: number): Promise<AiAssistantHistoryMessage[]> => {
  const { data } = await api.get<AiAssistantHistoryMessage[]>(`/ai-assistant/pages/${pageId}/history`);
  return Array.isArray(data) ? data : [];
};

export const fetchAiAssistantUsage = async (): Promise<AiAssistantUsageResponse> => {
  const { data } = await api.get<AiAssistantUsageResponse>("/ai-assistant/usage");
  return data;
};

export const createAiAssistantPageBase = async (
  pageId: number,
  reply: string
): Promise<unknown> => {
  const { data } = await api.post<AiAssistantCreatePageBaseResponse>("/ai-assistant/create-page-base", {
    page_id: pageId,
    reply
  });

  return data.page;
};

export const previewAiAssistantPageBase = async (
  pageId: number,
  reply: string,
  options: { includeImages?: boolean; currentPhotos?: string[]; itineraryDays?: Record<string, number> } = {}
): Promise<PageSection[]> => {
  const { data } = await api.post<{ sections: PageSection[] }>("/ai-assistant/preview-page-base", {
    page_id: pageId,
    reply,
    // Opção "Inserir imagens" do assistente; e as fotos que já estão na página (a troca não repete).
    include_images: options.includeImages ?? true,
    current_photos: (options.currentPhotos || []).slice(0, 400),
    // Dias de cada Roteiro dia a dia: a troca só da foto do roteiro põe uma foto nova por dia.
    itinerary_days: options.itineraryDays || {}
  });
  if (!Array.isArray(data.sections) || !data.sections.length) {
    throw new Error("A sugestão não contém seções válidas.");
  }
  return data.sections;
};

export type AiAssistantStreamStep = "reading" | "thinking" | "writing" | "fixing";

export type AiAssistantStreamEvent =
  | { type: "status"; step: AiAssistantStreamStep; attachments?: number }
  | { type: "delta"; text: string }
  | { type: "replace"; text: string }
  | { type: "done"; reply: string; usage?: AiAssistantUsageResponse }
  | { type: "error"; status?: number; detail?: string };

/** Erro do assistente com o status HTTP, para a tela decidir a mensagem (ou tentar o /chat). */
export class AiAssistantRequestError extends Error {
  constructor(message: string, readonly status: number, readonly started = false) {
    super(message);
  }
}

/**
 * Conversa com o assistente recebendo a resposta enquanto a IA escreve (linhas JSON):
 * etapas, trechos do texto e, no fim, a resposta completa com o uso do mês.
 */
export const streamAiAssistantConversation = async (
  pageId: number,
  conversation: AiAssistantChatMessage[],
  attachments: File[],
  onEvent: (event: AiAssistantStreamEvent) => void,
  pageSections: AiPageSectionSummary[] = [],
  includeImages = true
): Promise<{ reply: string; usage?: AiAssistantUsageResponse }> => {
  const form = new FormData();
  form.append("page_id", String(pageId));
  form.append("conversation", JSON.stringify(conversation));
  form.append("page_sections", JSON.stringify(pageSections));
  form.append("include_images", includeImages ? "true" : "false");
  for (const file of attachments) form.append("attachments", file, file.name);

  const authorization = api.defaults.headers.common?.Authorization;
  const response = await fetch(`${API_BASE_URL}/ai-assistant/chat-stream`, {
    method: "POST",
    body: form,
    headers: authorization ? { Authorization: String(authorization) } : undefined
  });
  if (!response.ok || !response.body) {
    let detail = "";
    try {
      detail = (await response.json())?.detail || "";
    } catch {
      detail = "";
    }
    throw new AiAssistantRequestError(typeof detail === "string" ? detail : "", response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: { reply: string; usage?: AiAssistantUsageResponse } | null = null;
  const handle = (line: string) => {
    if (!line.trim()) return;
    const event = JSON.parse(line) as AiAssistantStreamEvent;
    if (event.type === "error") throw new AiAssistantRequestError(event.detail || "", event.status || 502, true);
    if (event.type === "done") result = { reply: event.reply, usage: event.usage };
    onEvent(event);
  };
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newline = buffer.indexOf("\n");
    while (newline >= 0) {
      handle(buffer.slice(0, newline));
      buffer = buffer.slice(newline + 1);
      newline = buffer.indexOf("\n");
    }
  }
  handle(buffer + decoder.decode());
  if (!result) throw new AiAssistantRequestError("A conexão caiu antes do fim da resposta.", 502, true);
  return result;
};

/** Texto falado num áudio gravado no chat. */
export const transcribeAiAssistantAudio = async (pageId: number, audio: Blob, filename: string): Promise<string> => {
  const form = new FormData();
  form.append("page_id", String(pageId));
  form.append("audio", audio, filename);
  const { data } = await api.post<{ text: string }>("/ai-assistant/transcribe", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data.text || "";
};
