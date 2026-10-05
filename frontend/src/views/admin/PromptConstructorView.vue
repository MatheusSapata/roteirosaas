<template>
  <div class="admin-master-surface am-page w-full">
    <AdminMasterHeader
      title="Prompt do construtor"
      subtitle="O texto que orienta a IA do construtor de páginas. Teste com uma viagem antes de salvar."
    >
      <button type="button" class="am-btn" :disabled="saving || loading || restoringDefault" @click="restoreDefaultPrompt">
        <AmIcon name="undo" />{{ restoringDefault ? "Restaurando..." : "Restaurar padrão" }}
      </button>
      <button type="button" class="am-btn am-btn-primary" :disabled="saving || loading || restoringDefault || !promptText.trim()" @click="savePrompt">
        {{ saving ? "Salvando..." : "Salvar prompt" }}
      </button>
    </AdminMasterHeader>

    <div v-if="errorMessage" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>
    <div v-if="hasUnsavedChanges" class="am-notice am-tone-warning">
      <AmIcon name="info" />
      <span><b>Alterações não salvas.</b> O construtor continua usando o prompt salvo em {{ formatDateTime(config?.updated_at) }}.</span>
    </div>

    <section class="am-grid-4">
      <AdminMasterKpi icon="history" tone="info" label="Última atualização" :value="formatDateTime(config?.updated_at)" />
      <AdminMasterKpi icon="user" tone="neutral" label="Alterado por" :value="config?.updated_by_name || '—'" />
      <AdminMasterKpi icon="layout" tone="violet" label="Versões salvas" :value="String(config?.versions?.length || 0)" />
      <AdminMasterKpi icon="spark" tone="success" label="Tamanho do prompt" :value="`${formatInt(promptLength)} caracteres`" :hint="`~${formatInt(Math.round(promptLength / 4))} tokens`" />
    </section>

    <section class="grid gap-3.5 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
      <article class="am-card flex flex-col">
        <div class="am-card-head flex-wrap">
          <div>
            <h2 class="am-card-title">Prompt</h2>
            <p class="am-card-sub">Texto principal que a IA recebe em toda conversa do construtor</p>
          </div>
          <div class="am-field flex items-center gap-2">
            <label for="prompt-model" class="!mb-0 whitespace-nowrap">Modelo</label>
            <select id="prompt-model" v-model="selectedModel" class="am-input !h-8 !w-auto !py-0">
              <option v-for="option in modelOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </div>
        </div>
        <textarea
          v-model="promptText"
          class="pc-code min-h-[420px] flex-1"
          placeholder="Cole aqui o prompt completo do construtor"
          aria-label="Prompt do construtor"
        ></textarea>
        <div class="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p class="am-card-sub !mt-0">O modelo salvo é o usado no chat do editor de página.</p>
          <button type="button" class="am-btn am-btn-sm" :disabled="loading || saving" @click="reloadPrompt"><AmIcon name="refresh" />Desfazer alterações</button>
        </div>
      </article>

      <article class="am-card flex flex-col">
        <div class="am-card-head">
          <div>
            <h2 class="am-card-title">Testar com uma viagem</h2>
            <p class="am-card-sub">Usa o texto acima, sem salvar e sem afetar as agências</p>
          </div>
          <button type="button" class="am-btn am-btn-sm am-btn-primary" :disabled="testing || loading || saving || restoringDefault || !testInput.trim()" @click="testPrompt">
            <AmIcon name="play" />{{ testing ? "Testando..." : "Testar" }}
          </button>
        </div>
        <textarea
          v-model="testInput"
          class="am-input !min-h-[130px]"
          placeholder="Ex.: Destino Gramado e Canela, 12 a 15 de julho, ônibus leito, hotel 4 estrelas..."
          aria-label="Dados da viagem para testar"
        ></textarea>

        <div class="mb-1.5 mt-4 flex items-center justify-between">
          <p class="am-eyebrow">Resposta</p>
          <button type="button" class="am-btn am-btn-sm" :disabled="!testResult.trim()" @click="copyResult"><AmIcon name="copy" />Copiar</button>
        </div>
        <div v-if="testValidationError" class="am-notice am-tone-warning mb-2"><AmIcon name="alert" /><span>{{ testValidationError }}</span></div>
        <pre class="pc-code pc-result flex-1">{{ testResult || "O resultado do teste aparece aqui." }}</pre>
        <div v-if="testUsageInfo || testDebugInfo" class="am-card-sub mt-2 space-y-0.5">
          <p v-if="testUsageInfo">{{ testUsageInfo }}</p>
          <p v-if="testDebugInfo">{{ testDebugInfo }}</p>
        </div>
      </article>
    </section>

    <section class="am-card am-card-flush">
      <div class="am-toolbar justify-between">
        <div>
          <h2 class="am-card-title">Versões</h2>
          <p class="am-card-sub">Cada vez que o prompt é salvo, a versão anterior fica guardada aqui</p>
        </div>
      </div>
      <div v-if="!(config?.versions || []).length" class="am-empty">Nenhuma versão salva ainda.</div>
      <div v-else class="am-table-wrap">
        <table class="am-table">
          <thead>
            <tr>
              <th>Versão</th>
              <th>Salva por</th>
              <th>Quando</th>
              <th>Início do texto</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="version in config?.versions || []" :key="version.id">
              <td>
                <b class="am-num">#{{ version.id }}</b>
                <small class="am-muted block text-xs">{{ sourceLabel(version.source) }}</small>
              </td>
              <td>{{ version.created_by_name || "Sistema" }}</td>
              <td class="am-num">{{ formatDateTime(version.created_at) }}</td>
              <td><span class="am-muted line-clamp-2 max-w-[520px] text-xs">{{ snippet(version.prompt_text) }}</span></td>
              <td class="am-right">
                <button type="button" class="am-btn am-btn-sm" :disabled="savingVersionId === version.id" @click="restoreVersion(version.id)">
                  {{ savingVersionId === version.id ? "Restaurando..." : "Restaurar" }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
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
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";

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
const formatInt = (value: number) => new Intl.NumberFormat("pt-BR").format(Number(value || 0));
const hasUnsavedChanges = computed(
  () => Boolean(config.value) && !loading.value && promptText.value.trim() !== String(config.value?.active_prompt || "").trim()
);
const sourceLabel = (value?: string | null) => {
  if (!value) return "—";
  if (value === "manual") return "Salva na tela";
  if (value === "seed") return "Versão inicial";
  if (value === "restore-default") return "Padrão restaurado";
  if (value.startsWith("restore-version:")) return `Restaurada da #${value.split(":")[1]}`;
  return value;
};

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
.pc-code {
  width: 100%;
  resize: vertical;
  border: 1px solid var(--border) !important;
  border-radius: 14px;
  background: color-mix(in srgb, var(--background) 70%, var(--muted)) !important;
  padding: 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px;
  line-height: 20px;
  color: var(--foreground) !important;
  white-space: pre-wrap;
}
.pc-code:focus-visible {
  outline: 2px solid var(--ring);
  outline-offset: 1px;
}
.pc-result {
  min-height: 180px;
  max-height: 420px;
  overflow: auto;
  margin: 0;
  color: var(--muted-foreground) !important;
}
</style>
