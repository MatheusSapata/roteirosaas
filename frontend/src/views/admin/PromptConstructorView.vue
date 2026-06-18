<template>
  <div class="page-wrap prompt-constructor-page">
    <div class="page-topbar">
      <div>
        <p class="page-eyebrow">Admin Master</p>
        <h1 class="page-title">Configuração do Prompt Construtor</h1>
        <p class="page-sub">
          Edite o prompt ativo do Construtor Roteiro Online, teste com dados de viagem e volte a versões anteriores quando precisar.
        </p>
      </div>

      <div class="top-actions">
        <button type="button" class="btn btn-o" :disabled="saving || loading || restoringDefault" @click="restoreDefaultPrompt">
          {{ restoringDefault ? "Restaurando..." : "Restaurar Prompt Padrão" }}
        </button>
        <button type="button" class="btn btn-p" :disabled="saving || loading || restoringDefault" @click="savePrompt">
          {{ saving ? "Salvando..." : "Salvar Prompt" }}
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <section class="summary-row">
      <article class="summary-card">
        <p class="summary-label">Última atualização</p>
        <p class="summary-value">{{ formatDateTime(config?.updated_at) }}</p>
      </article>
      <article class="summary-card">
        <p class="summary-label">Alterado por</p>
        <p class="summary-value">{{ config?.updated_by_name || "-" }}</p>
      </article>
      <article class="summary-card">
        <p class="summary-label">Versões salvas</p>
        <p class="summary-value">{{ config?.versions?.length || 0 }}</p>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel panel-main">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Prompt ativo</p>
            <h2 class="panel-title">Texto principal do construtor</h2>
          </div>
          <span class="panel-badge">{{ promptLength }} caracteres</span>
        </div>

        <textarea
          v-model="promptText"
          class="prompt-textarea"
          placeholder="Cole aqui o prompt completo do Construtor Roteiro Online"
        />

        <div class="panel-footer">
          <button type="button" class="btn btn-o" :disabled="loading || saving" @click="reloadPrompt">
            Recarregar
          </button>
          <button type="button" class="btn btn-p" :disabled="loading || saving || restoringDefault || !promptText.trim()" @click="savePrompt">
            Salvar Prompt
          </button>
        </div>
      </article>

      <article class="panel panel-side">
        <div class="model-box">
          <label class="model-label" for="prompt-model">Modelo oficial do chat</label>
          <select id="prompt-model" v-model="selectedModel" class="model-select">
            <option v-for="option in modelOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <p class="model-note">
            O modelo salvo aqui será o usado no chat da página de edição. O teste usa o modelo selecionado e retorna os tokens consumidos e o custo estimado.
          </p>
        </div>
      </article>
    </section>

    <section class="content-grid content-grid-test">
      <article class="panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Teste de viagem</p>
            <h2 class="panel-title">Dados de entrada</h2>
          </div>
          <button type="button" class="btn btn-p" :disabled="testing || loading || saving || restoringDefault || !testInput.trim()" @click="testPrompt">
            {{ testing ? "Testando..." : "Testar Prompt" }}
          </button>
        </div>

        <textarea
          v-model="testInput"
          class="prompt-textarea prompt-textarea-test"
          placeholder="Ex.: Destino Gramado e Canela, 12 a 15 de julho, ônibus leito, hotel 4 estrelas..."
        />
      </article>

      <article class="panel">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Resultado do teste</p>
            <h2 class="panel-title">Resposta gerada</h2>
          </div>
          <button type="button" class="btn btn-o" :disabled="!testResult.trim()" @click="copyResult">
            Copiar
          </button>
        </div>

        <div v-if="testDebugInfo" class="test-debug">
          {{ testDebugInfo }}
        </div>
        <div v-if="testUsageInfo" class="test-usage">
          {{ testUsageInfo }}
        </div>
        <div v-if="testValidationError" class="alert alert-error test-warning">
          {{ testValidationError }}
        </div>

        <pre class="result-box">{{ testResult || "O resultado do teste aparece aqui." }}</pre>
      </article>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <p class="panel-kicker">Histórico</p>
          <h2 class="panel-title">Versões do prompt</h2>
        </div>
      </div>

      <div v-if="!(config?.versions || []).length" class="empty-state">
        Nenhuma versão salva ainda.
      </div>
      <div v-else class="version-list">
        <article v-for="version in config?.versions || []" :key="version.id" class="version-card">
          <div class="version-copy">
            <div class="version-meta">
              <span>#{{
                version.id
              }}</span>
              <span>{{ version.source }}</span>
              <span>{{ formatDateTime(version.created_at) }}</span>
            </div>
            <p class="version-user">{{ version.created_by_name || "Sistema" }}</p>
            <p class="version-snippet">{{ snippet(version.prompt_text) }}</p>
          </div>
          <button type="button" class="btn btn-o btn-sm" :disabled="savingVersionId === version.id" @click="restoreVersion(version.id)">
            {{ savingVersionId === version.id ? "Restaurando..." : "Restaurar" }}
          </button>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  fetchPromptConstructorConfig,
  restoreDefaultPromptConstructorConfig,
  restorePromptConstructorVersion,
  savePromptConstructorConfig,
  testPromptConstructorConfig,
  type PromptConstructorConfig
} from "../../services/promptConstructor";

const modelOptions = [
  { value: "gpt-4.1", label: "GPT-4.1" },
  { value: "gpt-4.1-mini", label: "GPT-4.1 mini" },
  { value: "gpt-4.1-nano", label: "GPT-4.1 nano" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o mini" },
  { value: "gpt-4", label: "GPT-4" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
  { value: "gpt-5.1", label: "GPT-5.1" },
  { value: "gpt-5.4", label: "GPT-5.4" },
  { value: "gpt-5.4-mini", label: "GPT-5.4 mini" }
];

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const restoringDefault = ref(false);
const savingVersionId = ref<number | null>(null);
const config = ref<PromptConstructorConfig | null>(null);
const promptText = ref("");
const selectedModel = ref("gpt-4.1");
const testInput = ref("");
const testResult = ref("");
const testDebugInfo = ref("");
const testUsageInfo = ref("");
const testValidationError = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const defaultPrompt = ref("");

const promptLength = computed(() => promptText.value.trim().length);

const clearMessages = () => {
  errorMessage.value = "";
  successMessage.value = "";
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleString("pt-BR");
};

const formatCurrency = (value?: number | null) => {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(amount);
};

const snippet = (value: string) => {
  const text = (value || "").replace(/\s+/g, " ").trim();
  if (!text) return "";
  return text.length > 220 ? `${text.slice(0, 220)}...` : text;
};

const loadPrompt = async () => {
  loading.value = true;
  clearMessages();
  try {
    const data = await fetchPromptConstructorConfig();
    config.value = data;
    promptText.value = data.active_prompt || "";
    defaultPrompt.value = data.default_prompt || "";
    selectedModel.value = data.gpt_model || "gpt-4.1";
    if (!testInput.value.trim()) {
      testInput.value = "Destino: Gramado e Canela\nData: 12 a 15 de julho\nTransporte: ônibus leito\nHospedagem: hotel 4 estrelas\nIncluso: transporte, hotel, café da manhã e city tour\nValor: R$ 1.290 por pessoa\nPúblico: famílias e casais";
    }
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || "Não foi possível carregar o prompt.";
  } finally {
    loading.value = false;
  }
};

const reloadPrompt = async () => {
  await loadPrompt();
};

const savePrompt = async () => {
  const nextPrompt = promptText.value.trim();
  if (!nextPrompt) {
    errorMessage.value = "O prompt não pode ficar vazio.";
    return;
  }
  saving.value = true;
  clearMessages();
  try {
    const data = await savePromptConstructorConfig(nextPrompt, selectedModel.value);
    config.value = data;
    promptText.value = data.active_prompt || nextPrompt;
    defaultPrompt.value = data.default_prompt || defaultPrompt.value;
    selectedModel.value = data.gpt_model || selectedModel.value;
    successMessage.value = "Prompt salvo com sucesso.";
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || "Não foi possível salvar o prompt.";
  } finally {
    saving.value = false;
  }
};

const restoreDefaultPrompt = async () => {
  restoringDefault.value = true;
  clearMessages();
  try {
    const data = await restoreDefaultPromptConstructorConfig();
    config.value = data;
    promptText.value = data.active_prompt || "";
    defaultPrompt.value = data.default_prompt || defaultPrompt.value;
    successMessage.value = "Prompt padrão restaurado.";
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || "Não foi possível restaurar o prompt padrão.";
  } finally {
    restoringDefault.value = false;
  }
};

const restoreVersion = async (versionId: number) => {
  savingVersionId.value = versionId;
  clearMessages();
  try {
    const data = await restorePromptConstructorVersion(versionId);
    config.value = data;
    promptText.value = data.active_prompt || "";
    defaultPrompt.value = data.default_prompt || defaultPrompt.value;
    successMessage.value = "Versão restaurada com sucesso.";
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || "Não foi possível restaurar a versão.";
  } finally {
    savingVersionId.value = null;
  }
};

const testPrompt = async () => {
  const input = testInput.value.trim();
  if (!input) {
    errorMessage.value = "Informe os dados da viagem para testar o prompt.";
    return;
  }
  testing.value = true;
  clearMessages();
  testDebugInfo.value = "";
  testUsageInfo.value = "";
  testValidationError.value = "";
  try {
    const data = await testPromptConstructorConfig(input, selectedModel.value);
    testResult.value = data.reply || "";
    testValidationError.value = data.validation_error || "";
    testDebugInfo.value = `Modelo usado: ${data.model || selectedModel.value} | Prompt usado: ${data.prompt_source || "active"} | ${data.prompt_length || 0} caracteres`;
    if (data.usage) {
      testUsageInfo.value = `Tokens: ${data.usage.total_tokens} (entrada ${data.usage.input_tokens} / saída ${data.usage.output_tokens}) | Custo estimado: ${formatCurrency(data.usage.estimated_cost_usd)}`;
    } else {
      testUsageInfo.value = "";
    }
    successMessage.value = "Teste executado com sucesso.";
  } catch (err: any) {
    console.error(err);
    errorMessage.value = err?.response?.data?.detail || "Não foi possível testar o prompt.";
  } finally {
    testing.value = false;
  }
};

const copyResult = async () => {
  if (!testResult.value.trim()) return;
  if (typeof navigator === "undefined" || !navigator.clipboard) return;
  await navigator.clipboard.writeText(testResult.value);
  successMessage.value = "Resultado copiado.";
};

onMounted(() => {
  void loadPrompt();
});
</script>

<style scoped>
.page-wrap {
  padding: 28px 32px 64px;
  width: 100%;
  max-width: 1380px;
}

.page-topbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
}

@media (min-width: 768px) {
  .page-topbar {
    flex-direction: row;
    align-items: center;
  }
}

.page-title {
  margin-top: 4px;
  font-size: 24px;
  line-height: 1.15;
  font-weight: 800;
  color: #0b1b2b;
}

.page-sub {
  margin-top: 6px;
  color: #5f7990;
  font-size: 14px;
  line-height: 1.55;
  max-width: 920px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
  font-family: inherit;
  transition: all 0.15s ease;
  white-space: nowrap;
  line-height: 1.3;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-p {
  background: #3dcc5f;
  color: #0f1f14;
}

.btn-p:hover:not(:disabled) {
  background: #32b453;
}

.btn-o {
  background: #fff;
  color: #203647;
  border-color: #dbe4de;
}

.btn-o:hover:not(:disabled) {
  border-color: #cbd6cb;
  background: #f8fafc;
}

.btn-o:focus-visible,
.btn-p:focus-visible,
.prompt-textarea:focus-visible {
  outline: 2px solid rgba(61, 204, 95, 0.28);
  outline-offset: 2px;
}

.prompt-constructor-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-eyebrow,
.panel-kicker,
.summary-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #5f7990;
}

.top-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.alert {
  border-radius: 16px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
}

.alert-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.alert-success {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.summary-row,
.content-grid {
  display: grid;
  gap: 14px;
}

.summary-row {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.content-grid {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 1024px) {
  .summary-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  }

  .content-grid-test {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }
}

.summary-card,
.panel {
  border-radius: 20px;
  border: 1px solid #dbe4de;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 31, 20, 0.06), 0 4px 12px rgba(15, 31, 20, 0.04);
  padding: 18px;
}

.summary-value {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 800;
  color: #0b1b2b;
  word-break: break-word;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel-main {
  min-width: 0;
}

.panel-side {
  min-width: 0;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 800;
  color: #0b1b2b;
}

.panel-badge {
  border-radius: 999px;
  border: 1px solid #d6e3db;
  background: #f8fafc;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #4b6476;
  white-space: nowrap;
}

.prompt-textarea {
  min-height: 360px;
  width: 100%;
  resize: vertical;
  border-radius: 16px;
  border: 1px solid #d6e3db;
  background: #fbfcfd;
  color: #0b1b2b;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.6;
}

.prompt-textarea-readonly {
  min-height: 360px;
  background: #f8fafc;
}

.model-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}

.model-label {
  font-size: 13px;
  font-weight: 700;
  color: #24364a;
}

.model-select {
  width: 100%;
  border-radius: 14px;
  border: 1px solid #d6e3db;
  background: #fbfcfd;
  color: #0b1b2b;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.4;
}

.model-note {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.prompt-textarea-test {
  min-height: 220px;
}

.panel-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.result-box {
  min-height: 300px;
  max-height: 520px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 16px;
  border: 1px solid #d6e3db;
  background: #0b1220;
  color: #f8fafc;
  padding: 16px;
  font-size: 13px;
  line-height: 1.7;
}

.test-debug {
  border-radius: 12px;
  border: 1px solid #dbe4de;
  background: #f8fafc;
  color: #64748b;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.4;
}

.test-usage {
  border-radius: 12px;
  border: 1px solid #d6e3db;
  background: #effdf3;
  color: #166534;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.4;
}

.test-warning {
  margin-top: 0;
  margin-bottom: 0;
}

.empty-state {
  border-radius: 16px;
  border: 1px dashed #d6e3db;
  padding: 18px;
  text-align: center;
  color: #64748b;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.version-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  border-radius: 16px;
  border: 1px solid #dbe4de;
  background: #fff;
  padding: 14px 16px;
}

.version-copy {
  min-width: 0;
}

.version-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #5f7990;
  font-weight: 700;
}

.version-user {
  margin-top: 4px;
  font-weight: 700;
  color: #0b1b2b;
}

.version-snippet {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .page-wrap {
    padding: 20px 16px 40px;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .panel-footer {
    justify-content: stretch;
  }

  .panel-footer .btn,
  .top-actions .btn {
    width: 100%;
  }

  .version-card {
    flex-direction: column;
  }
}
</style>

