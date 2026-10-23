<template>
  <div class="admin-master-surface am-page w-full">
    <AdminMasterHeader
      title="ViajeHub"
      subtitle="Manda os passos da jornada do Roteiro Online (início do checkout e assinatura paga) para o funil e o painel de vendas do ViajeHub."
    />

    <div v-if="errorMessage" class="am-notice am-tone-danger mb-3.5"><AmIcon name="alert" /><span>{{ errorMessage }}</span></div>
    <div v-if="successMessage" class="am-notice am-tone-success mb-3.5"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

    <section class="am-card max-w-[720px]">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="am-card-title">Conexão com o funil</h2>
          <p class="am-card-sub">Copie os dois dados no ViajeHub, em Funil › Conexão dos produtos.</p>
        </div>
        <span class="am-badge am-dot" :class="statusTone">{{ statusLabel }}</span>
      </div>

      <div v-if="loading" class="am-empty"><div class="am-spinner"></div>Carregando...</div>
      <form v-else class="mt-4 grid gap-4" @submit.prevent="save">
        <div class="am-field">
          <label for="vh-url">Endereço</label>
          <input
            id="vh-url"
            v-model="form.url"
            class="am-input am-mono"
            type="url"
            inputmode="url"
            autocomplete="off"
            placeholder="https://hub.viajeon.com/api/public/funil/evento"
          />
          <small class="am-muted mt-1.5 block text-xs">No quadro "Como cada produto envia os passos", botão de copiar ao lado da linha POST.</small>
        </div>
        <div class="am-field">
          <label for="vh-key">Chave do Roteiro Online</label>
          <input
            id="vh-key"
            v-model="form.key"
            class="am-input am-mono"
            type="password"
            autocomplete="off"
            :placeholder="connection.has_key ? `Salva: ${connection.key_masked}. Deixe em branco para manter.` : 'Cole a chave do Roteiro Online'"
          />
          <small class="am-muted mt-1.5 block text-xs">No quadro "Chaves dos produtos", a linha Roteiro Online. Fica guardada criptografada e não aparece de novo.</small>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button type="submit" class="am-btn am-btn-primary" :disabled="saving">
            <AmIcon name="check" />{{ saving ? "Salvando..." : "Salvar" }}
          </button>
          <button type="button" class="am-btn" :disabled="testing || !connection.source" @click="test">
            <AmIcon name="link" />{{ testing ? "Testando..." : "Testar conexão" }}
          </button>
          <button v-if="connection.has_key" type="button" class="am-btn ml-auto" :disabled="saving" @click="remove">
            <AmIcon name="trash" />Remover
          </button>
        </div>
      </form>
    </section>

    <section v-if="connection.source === 'ambiente'" class="am-notice am-tone-info mt-3.5 max-w-[720px]">
      <AmIcon name="info" />
      <span>Hoje o envio usa HUB_FUNNEL_URL e HUB_FUNNEL_KEY do servidor. O que for salvo aqui passa a valer no lugar deles.</span>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import {
  deleteViajeHubConnection,
  getViajeHubConnection,
  saveViajeHubConnection,
  testViajeHubConnection,
  type ViajeHubConnection
} from "../../services/viajehub";

const connection = ref<ViajeHubConnection>({ url: "", key_masked: "", has_key: false, source: "" });
const form = reactive({ url: "", key: "" });
const loading = ref(true);
const saving = ref(false);
const testing = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const statusLabel = computed(() => {
  if (connection.value.source === "painel") return "Conectado";
  if (connection.value.source === "ambiente") return "Conectado pelo servidor";
  return "Sem conexão";
});
const statusTone = computed(() => (connection.value.source ? "am-tone-success" : "am-tone-neutral"));

const errorText = (error: unknown, fallback: string) => {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
};

const apply = (data: ViajeHubConnection) => {
  connection.value = data;
  form.url = data.url;
  form.key = "";
};

const load = async () => {
  loading.value = true;
  try {
    apply(await getViajeHubConnection());
  } catch (error) {
    errorMessage.value = errorText(error, "Não foi possível carregar a conexão.");
  } finally {
    loading.value = false;
  }
};

const save = async () => {
  errorMessage.value = "";
  successMessage.value = "";
  saving.value = true;
  try {
    apply(await saveViajeHubConnection({ url: form.url, key: form.key.trim() || undefined }));
    const result = await testViajeHubConnection();
    if (result.ok) successMessage.value = `Conexão salva. ${result.message}`;
    else errorMessage.value = `Conexão salva, mas o teste falhou: ${result.message}`;
  } catch (error) {
    errorMessage.value = errorText(error, "Não foi possível salvar a conexão.");
  } finally {
    saving.value = false;
  }
};

const test = async () => {
  errorMessage.value = "";
  successMessage.value = "";
  testing.value = true;
  try {
    const result = await testViajeHubConnection();
    if (result.ok) successMessage.value = result.message;
    else errorMessage.value = result.message;
  } catch (error) {
    errorMessage.value = errorText(error, "Não foi possível testar a conexão.");
  } finally {
    testing.value = false;
  }
};

const remove = async () => {
  if (!window.confirm("Remover a conexão salva aqui? O Roteiro Online para de mandar os passos ao ViajeHub, a não ser que o servidor tenha a configuração própria.")) return;
  errorMessage.value = "";
  successMessage.value = "";
  saving.value = true;
  try {
    apply(await deleteViajeHubConnection());
    successMessage.value = "Conexão removida.";
  } catch (error) {
    errorMessage.value = errorText(error, "Não foi possível remover a conexão.");
  } finally {
    saving.value = false;
  }
};

onMounted(load);
</script>
