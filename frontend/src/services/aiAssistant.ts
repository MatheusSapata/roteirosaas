import api from "./api";

export interface AiAssistantChatMessage {
  role: "user" | "assistant";
  content: string;
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
  conversation: AiAssistantChatMessage[],
  attachments: File[] = []
): Promise<{ reply: string; usage?: AiAssistantUsageResponse }> => {
  const form = new FormData();
  form.append("conversation", JSON.stringify(conversation));

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
