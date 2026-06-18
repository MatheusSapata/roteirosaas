import api from "./api";

export interface PromptConstructorVersion {
  id: number;
  prompt_text: string;
  source: string;
  created_at?: string | null;
  created_by_user_id?: number | null;
  created_by_name?: string | null;
}

export interface PromptConstructorConfig {
  id: number;
  key: string;
  active_prompt: string;
  default_prompt: string;
  gpt_model: string;
  updated_at?: string | null;
  updated_by_user_id?: number | null;
  updated_by_name?: string | null;
  versions: PromptConstructorVersion[];
}

export interface PromptConstructorTestResult {
  reply: string;
  validation_error?: string | null;
  prompt_source: string;
  model: string;
  prompt_length: number;
  prompt_preview: string;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    cached_input_tokens: number;
    estimated_cost_usd: number;
  } | null;
}

export const fetchPromptConstructorConfig = async () => {
  const { data } = await api.get<PromptConstructorConfig>("/admin-master/prompt-construtor");
  return data;
};

export const savePromptConstructorConfig = async (promptText: string, gptModel?: string) => {
  const { data } = await api.put<PromptConstructorConfig>("/admin-master/prompt-construtor", {
    prompt_text: promptText,
    gpt_model: gptModel
  });
  return data;
};

export const restoreDefaultPromptConstructorConfig = async () => {
  const { data } = await api.post<PromptConstructorConfig>("/admin-master/prompt-construtor/restore-default");
  return data;
};

export const restorePromptConstructorVersion = async (versionId: number) => {
  const { data } = await api.post<PromptConstructorConfig>(
    `/admin-master/prompt-construtor/versions/${versionId}/restore`
  );
  return data;
};

export const testPromptConstructorConfig = async (travelInput: string, model?: string) => {
  const { data } = await api.post<PromptConstructorTestResult>("/admin-master/prompt-construtor/test", {
    travel_input: travelInput,
    model
  });
  return data;
};
