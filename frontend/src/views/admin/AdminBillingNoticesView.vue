<template>
  <main class="admin-master-surface am-page w-full billing-notices">
    <AdminMasterHeader
      title="Avisos de cobrança"
      subtitle="Mensagens de fatura e pagamento que os clientes recebem por WhatsApp e e-mail."
    >
      <button type="button" class="am-btn" :disabled="!settings?.enabled || running" @click="runNow">
        <AmIcon name="play" />{{ running ? "Rodando…" : "Rodar a rotina agora" }}
      </button>
      <button type="button" class="am-btn am-btn-primary" :disabled="!settings || saving || !dirty" @click="save">
        {{ saving ? "Salvando…" : "Salvar alterações" }}
      </button>
    </AdminMasterHeader>

    <div v-if="error" class="am-notice am-tone-danger" role="alert"><AmIcon name="alert" /><span>{{ error }}</span></div>
    <div v-if="message" class="am-notice am-tone-success" role="status"><AmIcon name="check" /><span>{{ message }}</span></div>

    <section v-if="settings" class="am-grid-4">
      <AdminMasterKpi
        icon="bell"
        :tone="settings.enabled ? 'success' : 'neutral'"
        label="Envio aos clientes"
        :value="settings.enabled ? 'Ligado' : 'Desligado'"
        :hint="settings.enabled ? `Rotina diária às ${settings.daily_run_at}${settings.ran_today ? ' · já rodou hoje' : ''}` : 'Nada sai enquanto estiver desligado'"
      />
      <AdminMasterKpi
        icon="wa"
        :tone="whatsappTone"
        label="WhatsApp que envia"
        :value="settings.whatsapp_connection?.name || 'Não escolhido'"
        :hint="settings.whatsapp_connection ? connectionStatusLabel(settings.whatsapp_connection.status) : 'Escolha em Configuração'"
      />
      <AdminMasterKpi icon="check" tone="info" label="Enviados em 7 dias" :value="formatInt(settings.stats.sent_7d)" />
      <AdminMasterKpi
        icon="alert"
        :tone="settings.stats.failed_7d ? 'danger' : 'neutral'"
        label="Falhas em 7 dias"
        :value="formatInt(settings.stats.failed_7d)"
        hint="Novas tentativas automáticas até 3 vezes"
      />
    </section>

    <section v-if="settings" class="am-card am-card-flush">
      <nav class="am-tabs px-2.5" aria-label="Seções dos avisos de cobrança">
        <button v-for="item in tabs" :key="item.id" type="button" class="am-tab" :class="{ on: tab === item.id }" @click="tab = item.id">
          {{ item.label }}
        </button>
      </nav>

      <!-- Configuração -->
      <div v-if="tab === 'config'" class="tab-body space-y-5">
        <div class="setting-row">
          <div>
            <p class="setting-title">Enviar avisos aos clientes</p>
            <p class="setting-hint">Chave geral. Desligada, nada sai; a prévia em Próximos envios continua funcionando.</p>
          </div>
          <button type="button" class="am-btn" role="switch" :aria-checked="form.enabled" @click="form.enabled = !form.enabled">
            <span class="am-switch" :class="{ on: form.enabled }" aria-hidden="true"></span>{{ form.enabled ? "Ligado" : "Desligado" }}
          </button>
        </div>

        <div class="am-grid-2">
          <div class="am-field">
            <label for="bn-connection">WhatsApp que envia as mensagens</label>
            <select id="bn-connection" v-model="form.whatsapp_connection_id" class="am-input">
              <option :value="null">Nenhum (não envia por WhatsApp)</option>
              <option v-for="connection in settings.connections" :key="connection.id" :value="connection.id">
                {{ connection.name }}{{ connection.phone_number ? ` · ${connection.phone_number}` : "" }}{{ connection.agency_name ? ` · ${connection.agency_name}` : "" }} — {{ connectionStatusLabel(connection.status) }}
              </option>
            </select>
            <p class="setting-hint mt-1.5">As conexões ficam em Admin master › WhatsApp.</p>
          </div>
          <div class="am-field">
            <label for="bn-lead">“Fatura disponível” sai quando faltam até</label>
            <div class="flex items-center gap-2">
              <input id="bn-lead" v-model.number="form.available_lead_days" class="am-input" style="max-width: 96px" type="number" min="1" max="60" />
              <span class="setting-hint">dias para o vencimento (de 1 a 60)</span>
            </div>
            <p class="setting-hint mt-1.5">Faturas que vencem mais longe que isso recebem o aviso nesse prazo, pela rotina das {{ settings.daily_run_at }}.</p>
          </div>
        </div>

        <div class="setting-row">
          <div>
            <p class="setting-title">Avisos do próprio Asaas</p>
            <p class="setting-hint">
              E-mails e SMS que o Asaas manda das faturas. Com os dois ligados, o cliente recebe as mensagens do Asaas e as nossas.
              A mudança vale na hora para todos os clientes e para os novos.
            </p>
          </div>
          <button
            type="button"
            class="am-btn"
            role="switch"
            :aria-checked="settings.asaas_notifications_enabled"
            :disabled="asaasSaving || !settings.asaas_configured"
            @click="toggleAsaas"
          >
            <span class="am-switch" :class="{ on: settings.asaas_notifications_enabled }" aria-hidden="true"></span>
            {{ asaasSaving ? "Aplicando…" : settings.asaas_notifications_enabled ? "Ligados" : "Desligados" }}
          </button>
        </div>

        <ul class="checks">
          <li :class="settings.asaas_configured ? 'ok' : 'bad'">
            <AmIcon :name="settings.asaas_configured ? 'check' : 'alert'" />
            {{ settings.asaas_configured ? "Asaas conectado: as faturas são lidas na hora antes de cada aviso." : "A chave da API do Asaas não está configurada no servidor." }}
          </li>
          <li :class="settings.email_configured ? 'ok' : 'bad'">
            <AmIcon :name="settings.email_configured ? 'check' : 'alert'" />
            {{ settings.email_configured ? "E-mail (SMTP) configurado." : "O envio de e-mail (SMTP) não está configurado: os e-mails vão falhar." }}
          </li>
          <li :class="whatsappTone === 'success' ? 'ok' : 'bad'">
            <AmIcon :name="whatsappTone === 'success' ? 'check' : 'alert'" />
            {{ whatsappTone === "success" ? "WhatsApp conectado." : "WhatsApp sem conexão ativa: as mensagens de WhatsApp vão falhar." }}
          </li>
        </ul>

        <details class="rules">
          <summary>Regras de envio</summary>
          <ul>
            <li>Nada retroativo: ao ligar os avisos ou mudar o prazo, só vale daqui para a frente. Avisos que deveriam ter saído antes não saem atrasados, e editar textos nunca dispara mensagem.</li>
            <li>Cada etapa sai uma vez por fatura e canal. Se falhar, o sistema tenta de novo até 3 vezes.</li>
            <li>Antes de avisar, a fatura é lida no Asaas: paga, apagada, estornada ou trocada por outra não recebe aviso.</li>
            <li>Nada sai no dia em que a cobrança é criada (o cliente pode estar pagando no checkout).</li>
            <li>No dia da “Fatura disponível”, os lembretes de 3 dias e do vencimento não saem juntos.</li>
            <li>Cartão de crédito e Pix Automático não recebem lembretes antes do vencimento, porque são cobrados sozinhos. Os avisos de atraso saem para todos.</li>
            <li>Conta encerrada e conta interna (admin) não recebem avisos.</li>
            <li>“Pagamento confirmado” não sai na primeira compra, que já tem o e-mail de boas-vindas.</li>
          </ul>
        </details>
      </div>

      <!-- Etapas e textos -->
      <div v-else-if="tab === 'steps'" class="steps-layout">
        <aside class="step-list" aria-label="Etapas">
          <button
            v-for="step in settings.steps"
            :key="step.key"
            type="button"
            class="step-item"
            :class="{ on: selectedStep === step.key }"
            @click="selectedStep = step.key"
          >
            <span class="step-name">{{ step.label }}</span>
            <span class="step-desc">{{ step.description }}</span>
            <span class="step-channels">
              <span class="am-badge" :class="form.channels[step.key]?.whatsapp ? 'am-tone-success' : 'am-tone-neutral'">WhatsApp</span>
              <span class="am-badge" :class="form.channels[step.key]?.email ? 'am-tone-success' : 'am-tone-neutral'">E-mail</span>
              <span v-if="isCustom(step.key)" class="am-badge am-tone-violet">Texto próprio</span>
            </span>
          </button>
        </aside>

        <div v-if="currentStep" class="step-editor space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="am-card-title">{{ currentStep.label }}</h2>
              <p class="am-card-sub">{{ currentStep.description }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="channel in channelList"
                :key="channel.id"
                type="button"
                class="am-btn am-btn-sm"
                role="switch"
                :aria-checked="form.channels[currentStep.key][channel.id]"
                @click="form.channels[currentStep.key][channel.id] = !form.channels[currentStep.key][channel.id]"
              >
                <span class="am-switch" :class="{ on: form.channels[currentStep.key][channel.id] }" aria-hidden="true"></span>{{ channel.label }}
              </button>
            </div>
          </div>

          <div class="variables">
            <span class="setting-hint">Variáveis (entram no campo em que você clicou por último):</span>
            <button v-for="variable in settings.variables" :key="variable.key" type="button" class="am-chip" :title="variable.label" @click="insertVariable(variable.key)">
              {{ varToken(variable.key) }}
            </button>
          </div>

          <div class="am-grid-2">
            <div class="space-y-3">
              <div class="am-field">
                <label for="bn-wa">Mensagem de WhatsApp</label>
                <textarea
                  id="bn-wa"
                  ref="waField"
                  v-model="form.templates[currentStep.key].whatsapp"
                  class="am-input"
                  rows="9"
                  @focus="lastField = 'whatsapp'"
                ></textarea>
                <p class="setting-hint mt-1">*texto* fica em negrito no WhatsApp.</p>
              </div>
              <div class="am-field">
                <label for="bn-subject">Assunto do e-mail</label>
                <input id="bn-subject" ref="subjectField" v-model="form.templates[currentStep.key].email_subject" class="am-input" @focus="lastField = 'email_subject'" />
              </div>
              <div class="am-field">
                <label for="bn-email">Texto do e-mail</label>
                <textarea
                  id="bn-email"
                  ref="emailField"
                  v-model="form.templates[currentStep.key].email_body"
                  class="am-input"
                  rows="7"
                  @focus="lastField = 'email_body'"
                ></textarea>
                <p class="setting-hint mt-1">Texto simples: *negrito*, e uma linha em branco abre um parágrafo novo. O botão com o link da fatura entra sozinho.</p>
              </div>
              <button type="button" class="am-btn am-btn-sm" :disabled="!isCustom(currentStep.key)" @click="restoreDefault(currentStep.key)">
                <AmIcon name="undo" />Restaurar texto padrão
              </button>
            </div>

            <div class="space-y-3">
              <p class="am-label">Prévia com dados de exemplo</p>
              <div class="wa-preview" aria-label="Prévia do WhatsApp">
                <div class="wa-bubble" v-html="whatsappPreview"></div>
              </div>
              <div class="email-preview" aria-label="Prévia do e-mail">
                <p class="email-subject">{{ emailSubjectPreview }}</p>
                <div class="email-body" v-html="emailBodyPreview"></div>
              </div>

              <div class="test-box">
                <p class="am-label">Enviar teste desta etapa</p>
                <p class="setting-hint">Usa os textos que estão na tela, já salvos. Salve antes de testar uma mudança.</p>
                <div class="flex flex-wrap gap-2 mt-2">
                  <select v-model="testChannel" class="am-input w-auto" aria-label="Canal do teste">
                    <option value="whatsapp">WhatsApp</option>
                    <option value="email">E-mail</option>
                  </select>
                  <input
                    v-model="testTo"
                    class="am-input flex-1 min-w-[180px]"
                    :placeholder="testChannel === 'whatsapp' ? 'WhatsApp com DDD' : 'E-mail'"
                    :aria-label="testChannel === 'whatsapp' ? 'WhatsApp para o teste' : 'E-mail para o teste'"
                  />
                  <button type="button" class="am-btn" :disabled="testing || !testTo.trim() || dirty" @click="sendTest">
                    {{ testing ? "Enviando…" : "Enviar teste" }}
                  </button>
                </div>
                <p v-if="dirty" class="setting-hint mt-1.5">Há alterações não salvas.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Próximos envios -->
      <div v-else-if="tab === 'upcoming'">
        <div class="am-toolbar">
          <div class="am-seg" role="group" aria-label="Período">
            <button v-for="option in [7, 15, 30]" :key="option" type="button" :class="{ on: upcomingDays === option }" @click="upcomingDays = option; loadUpcoming()">
              {{ option }} dias
            </button>
          </div>
          <button v-for="option in upcomingFilters" :key="option.id" type="button" class="am-chip" :class="{ on: upcomingFilter === option.id }" @click="upcomingFilter = option.id">
            {{ option.label }} <span class="am-count">{{ upcomingCount(option.id) }}</span>
          </button>
          <button type="button" class="am-btn am-btn-sm ml-auto" :disabled="upcomingLoading" @click="loadUpcoming">
            <AmIcon name="refresh" :class="upcomingLoading ? 'animate-spin' : ''" />Atualizar
          </button>
        </div>
        <p class="setting-hint px-4 pt-3">
          Lido no Asaas agora. Mostra o que a rotina vai mandar até {{ upcomingDays }} dias e por que algum aviso não sai. Nada é enviado por aqui.
        </p>
        <div v-if="upcomingLoading && !upcoming" class="am-empty"><span class="am-spinner"></span>Consultando o Asaas…</div>
        <div v-else-if="upcomingError" class="am-notice am-tone-danger m-4"><AmIcon name="alert" /><span>{{ upcomingError }}</span></div>
        <div v-else-if="!visibleUpcoming.length" class="am-empty">Nenhum aviso neste período.</div>
        <div v-else class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Dia</th>
                <th>Cliente</th>
                <th>Etapa</th>
                <th>Fatura</th>
                <th>WhatsApp</th>
                <th>E-mail</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in visibleUpcoming" :key="`${item.payment_id}-${item.step}-${item.date}`">
                <td class="whitespace-nowrap">{{ dayLabel(item.date) }}</td>
                <td>
                  <b class="font-semibold">{{ item.name || "—" }}</b>
                  <small class="am-muted block">{{ item.email }}</small>
                </td>
                <td>{{ item.step_label }}</td>
                <td class="whitespace-nowrap">
                  {{ currency(item.value) }}
                  <small class="am-muted block">
                    vence {{ formatDate(item.due_date) }} · {{ billingTypeLabel(item.billing_type) }}
                    <a v-if="item.invoice_url" :href="item.invoice_url" target="_blank" rel="noopener" class="link">abrir</a>
                  </small>
                </td>
                <td v-for="channel in item.channels" :key="channel.channel">
                  <span class="am-badge" :class="stateTone(channel.state)">{{ stateLabel(channel.state) }}</span>
                  <small v-if="channel.reason" class="am-muted block reason">{{ channel.reason }}</small>
                  <button
                    v-if="channel.state === 'scheduled' || channel.state === 'off'"
                    type="button"
                    class="link block mt-1"
                    @click="cancelUpcoming(item, channel.channel)"
                  >
                    Cancelar
                  </button>
                  <button v-else-if="channel.state === 'cancelled'" type="button" class="link block mt-1" @click="reactivateUpcoming(item, channel.channel)">
                    Reativar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Histórico -->
      <div v-else-if="tab === 'history'">
        <div class="am-toolbar">
          <label class="am-search">
            <AmIcon name="search" />
            <input v-model="historyQuery" type="search" placeholder="Buscar por cliente, e-mail, número ou fatura" aria-label="Buscar no histórico" @keyup.enter="loadHistory(true)" />
          </label>
          <button v-for="option in historyFilters" :key="option.id" type="button" class="am-chip" :class="{ on: historyStatus === option.id }" @click="historyStatus = option.id; loadHistory(true)">
            {{ option.label }}
          </button>
          <select v-model="historyStep" class="am-select" aria-label="Etapa" @change="loadHistory(true)">
            <option value="">Todas as etapas</option>
            <option v-for="step in settings.steps" :key="step.key" :value="step.key">{{ step.label }}</option>
          </select>
        </div>
        <div v-if="historyLoading && !history.length" class="am-empty"><span class="am-spinner"></span>Carregando…</div>
        <div v-else-if="!history.length" class="am-empty">Nenhum envio ainda.</div>
        <div v-else class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Cliente</th>
                <th>Etapa</th>
                <th>Canal</th>
                <th>Situação</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in history" :key="row.id">
                <td class="whitespace-nowrap">{{ dateTime(row.sent_at || row.updated_at) }}</td>
                <td>
                  <b class="font-semibold">{{ row.name || "—" }}</b>
                  <small class="am-muted block">{{ row.recipient }}</small>
                </td>
                <td>
                  {{ row.step_label }}
                  <small class="am-muted block">{{ row.value || "" }}{{ row.due_date ? ` · vence ${formatDate(row.due_date)}` : "" }}</small>
                </td>
                <td>{{ row.channel === "whatsapp" ? "WhatsApp" : "E-mail" }}</td>
                <td>
                  <span class="am-badge" :class="stateTone(row.status)">{{ stateLabel(row.status) }}</span>
                  <small class="am-muted block">{{ row.attempts }} {{ row.attempts === 1 ? "tentativa" : "tentativas" }}</small>
                  <small v-if="row.error" class="am-muted block reason">{{ row.error }}</small>
                </td>
                <td class="text-right">
                  <button v-if="row.status === 'failed' || row.status === 'sending'" type="button" class="am-btn am-btn-sm" :disabled="retrying === row.id" @click="retry(row)">
                    {{ retrying === row.id ? "Enviando…" : "Tentar de novo" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="history.length < historyTotal" class="flex justify-center p-4">
          <button type="button" class="am-btn am-btn-sm" :disabled="historyLoading" @click="loadHistory(false)">Ver mais</button>
        </div>
      </div>
    </section>

    <div v-else-if="loading" class="am-empty"><span class="am-spinner"></span>Carregando…</div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";

type ChannelId = "whatsapp" | "email";
type Templates = Record<string, { whatsapp: string; email_subject: string; email_body: string }>;
type Channels = Record<string, Record<ChannelId, boolean>>;
type Connection = { id: number; name: string; phone_number: string | null; status: string; agency_name?: string | null };
type Settings = {
  enabled: boolean;
  whatsapp_connection_id: number | null;
  whatsapp_connection: Connection | null;
  available_lead_days: number;
  asaas_notifications_enabled: boolean;
  steps: { key: string; label: string; description: string; kind: string }[];
  channels: Channels;
  templates: Templates;
  default_templates: Templates;
  custom_fields: Record<string, string[]>;
  variables: { key: string; label: string }[];
  sample: Record<string, string>;
  connections: Connection[];
  email_configured: boolean;
  asaas_configured: boolean;
  daily_run_at: string;
  ran_today: boolean;
  stats: { sent_7d: number; failed_7d: number; cancelled_7d: number };
};
type UpcomingChannel = { channel: ChannelId; state: string; reason: string | null; send_id: number | null };
type UpcomingItem = {
  date: string;
  step: string;
  step_label: string;
  payment_id: string;
  user_id: number;
  name: string | null;
  email: string | null;
  value: number;
  due_date: string;
  billing_type: string | null;
  invoice_url: string | null;
  reason: string | null;
  channels: UpcomingChannel[];
};
type HistoryRow = {
  id: number;
  payment_id: string;
  step: string;
  step_label: string;
  channel: ChannelId;
  status: string;
  attempts: number;
  recipient: string | null;
  error: string | null;
  due_date: string | null;
  value: string | null;
  name: string | null;
  sent_at: string | null;
  updated_at: string | null;
};

const tabs = [
  { id: "config", label: "Configuração" },
  { id: "steps", label: "Etapas e textos" },
  { id: "upcoming", label: "Próximos envios" },
  { id: "history", label: "Histórico" }
] as const;
const channelList: { id: ChannelId; label: string }[] = [
  { id: "whatsapp", label: "WhatsApp" },
  { id: "email", label: "E-mail" }
];

const tab = ref<(typeof tabs)[number]["id"]>("config");
const settings = ref<Settings | null>(null);
const loading = ref(false);
const saving = ref(false);
const running = ref(false);
const asaasSaving = ref(false);
const error = ref("");
const message = ref("");
const form = reactive({
  enabled: false,
  whatsapp_connection_id: null as number | null,
  available_lead_days: 10,
  channels: {} as Channels,
  templates: {} as Templates
});
const savedSnapshot = ref("");
const snapshot = () => JSON.stringify(form);
const dirty = computed(() => Boolean(settings.value) && snapshot() !== savedSnapshot.value);

const detail = (e: any, fallback: string) => (typeof e?.response?.data?.detail === "string" ? e.response.data.detail : fallback);
function flash(text: string) {
  message.value = text;
  error.value = "";
  window.setTimeout(() => {
    if (message.value === text) message.value = "";
  }, 5000);
}

function applySettings(data: Settings) {
  settings.value = data;
  form.enabled = data.enabled;
  form.whatsapp_connection_id = data.whatsapp_connection_id;
  form.available_lead_days = data.available_lead_days;
  form.channels = JSON.parse(JSON.stringify(data.channels));
  form.templates = JSON.parse(JSON.stringify(data.templates));
  savedSnapshot.value = snapshot();
  if (!selectedStep.value && data.steps.length) selectedStep.value = data.steps[0].key;
}

async function load() {
  loading.value = true;
  try {
    const { data } = await api.get<Settings>("/admin/billing-notices/settings");
    applySettings(data);
  } catch (e) {
    error.value = detail(e, "Não foi possível carregar os avisos de cobrança.");
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (form.enabled && !form.whatsapp_connection_id && Object.values(form.channels).some(c => c.whatsapp)) {
    if (!window.confirm("Nenhum WhatsApp foi escolhido: as mensagens de WhatsApp vão falhar. Salvar assim mesmo?")) return;
  }
  saving.value = true;
  try {
    const { data } = await api.put<Settings>("/admin/billing-notices/settings", {
      enabled: form.enabled,
      whatsapp_connection_id: form.whatsapp_connection_id,
      available_lead_days: form.available_lead_days,
      steps: form.channels,
      templates: form.templates
    });
    applySettings(data);
    flash("Alterações salvas.");
  } catch (e) {
    error.value = detail(e, "Não foi possível salvar.");
  } finally {
    saving.value = false;
  }
}

async function toggleAsaas() {
  if (!settings.value) return;
  const next = !settings.value.asaas_notifications_enabled;
  const question = next
    ? "Ligar os avisos do Asaas para todos os clientes? Eles voltam a receber os e-mails e SMS do Asaas."
    : "Desligar os avisos do Asaas para todos os clientes? Só os nossos avisos vão sair. Confira antes se os nossos estão ligados.";
  if (!window.confirm(question)) return;
  asaasSaving.value = true;
  try {
    const { data } = await api.post<Settings>("/admin/billing-notices/asaas-notifications", { enabled: next });
    settings.value = { ...settings.value, asaas_notifications_enabled: data.asaas_notifications_enabled };
    flash(next ? "Avisos do Asaas ligados. Os clientes estão sendo atualizados no Asaas." : "Avisos do Asaas desligados. Os clientes estão sendo atualizados no Asaas.");
  } catch (e) {
    error.value = detail(e, "Não foi possível mudar os avisos do Asaas.");
  } finally {
    asaasSaving.value = false;
  }
}

async function runNow() {
  if (!window.confirm("Rodar a rotina de hoje agora? O que já saiu hoje não sai de novo.")) return;
  running.value = true;
  try {
    const { data } = await api.post("/admin/billing-notices/run-now", {}, { timeout: 180000 });
    flash(`Rotina concluída: ${data.sent || 0} enviados, ${data.failed || 0} com falha, ${data.skipped || 0} sem envio.`);
    await load();
    if (tab.value === "upcoming") await loadUpcoming();
    if (tab.value === "history") await loadHistory(true);
  } catch (e) {
    error.value = detail(e, "A rotina não rodou.");
  } finally {
    running.value = false;
  }
}

// ---------------------------------------------------------------- etapas e textos

const selectedStep = ref("");
const currentStep = computed(() => settings.value?.steps.find(step => step.key === selectedStep.value) || null);
const lastField = ref<"whatsapp" | "email_subject" | "email_body">("whatsapp");
const waField = ref<HTMLTextAreaElement | null>(null);
const subjectField = ref<HTMLInputElement | null>(null);
const emailField = ref<HTMLTextAreaElement | null>(null);

function isCustom(key: string) {
  const defaults = settings.value?.default_templates[key];
  const current = form.templates[key];
  if (!defaults || !current) return false;
  return (["whatsapp", "email_subject", "email_body"] as const).some(field => (current[field] || "").trim() !== defaults[field]);
}

function restoreDefault(key: string) {
  const defaults = settings.value?.default_templates[key];
  if (defaults) form.templates[key] = { ...defaults };
}

const varToken = (key: string) => ["{", "{", key, "}", "}"].join("");

function insertVariable(variable: string) {
  const key = selectedStep.value;
  if (!key) return;
  const token = `{{${variable}}}`;
  const field = lastField.value;
  const element = field === "whatsapp" ? waField.value : field === "email_subject" ? subjectField.value : emailField.value;
  const value = form.templates[key][field] || "";
  const start = element?.selectionStart ?? value.length;
  const end = element?.selectionEnd ?? value.length;
  form.templates[key][field] = value.slice(0, start) + token + value.slice(end);
  requestAnimationFrame(() => {
    element?.focus();
    element?.setSelectionRange(start + token.length, start + token.length);
  });
}

const escapeHtml = (text: string) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const renderSample = (text: string) => (text || "").replace(/\{\{\s*([a-z_]+)\s*\}\}/g, (match, key) => settings.value?.sample[key] ?? match);
const boldify = (html: string) => html.replace(/\*([^*\n]+)\*/g, "<b>$1</b>");

const whatsappPreview = computed(() => {
  const template = form.templates[selectedStep.value]?.whatsapp || "";
  return boldify(escapeHtml(renderSample(template))).replace(/\n/g, "<br>");
});
const emailSubjectPreview = computed(() => renderSample(form.templates[selectedStep.value]?.email_subject || ""));
const emailBodyPreview = computed(() => {
  const body = renderSample(form.templates[selectedStep.value]?.email_body || "");
  return body
    .split(/\n\s*\n/)
    .map(block => block.trim())
    .filter(Boolean)
    .map(block => `<p>${boldify(escapeHtml(block)).replace(/\n/g, "<br>")}</p>`)
    .join("");
});

const testChannel = ref<ChannelId>("whatsapp");
const testTo = ref("");
const testing = ref(false);
async function sendTest() {
  testing.value = true;
  try {
    await api.post("/admin/billing-notices/test", { step: selectedStep.value, channel: testChannel.value, to: testTo.value.trim() });
    flash("Teste enviado.");
  } catch (e) {
    error.value = detail(e, "O teste não saiu.");
  } finally {
    testing.value = false;
  }
}

// ---------------------------------------------------------------- próximos envios

const upcoming = ref<{ items: UpcomingItem[]; ran_today: boolean } | null>(null);
const upcomingLoading = ref(false);
const upcomingError = ref("");
const upcomingDays = ref(7);
const upcomingFilter = ref("all");
const upcomingFilters = [
  { id: "all", label: "Todos" },
  { id: "scheduled", label: "Vão sair" },
  { id: "skipped", label: "Não saem" },
  { id: "done", label: "Já saíram" }
];
const matchesUpcoming = (item: UpcomingItem, filter: string) => {
  if (filter === "all") return true;
  if (filter === "scheduled") return item.channels.some(c => c.state === "scheduled" || c.state === "off");
  if (filter === "done") return item.channels.some(c => c.state === "sent" || c.state === "failed" || c.state === "sending");
  return item.channels.every(c => !["scheduled", "off", "sent", "sending"].includes(c.state));
};
const upcomingCount = (filter: string) => (upcoming.value?.items || []).filter(item => matchesUpcoming(item, filter)).length;
const visibleUpcoming = computed(() => (upcoming.value?.items || []).filter(item => matchesUpcoming(item, upcomingFilter.value)));

async function loadUpcoming() {
  upcomingLoading.value = true;
  upcomingError.value = "";
  try {
    const { data } = await api.get("/admin/billing-notices/upcoming", { params: { days: upcomingDays.value }, timeout: 150000 });
    upcoming.value = data;
  } catch (e) {
    upcomingError.value = detail(e, "Não foi possível consultar o Asaas.");
  } finally {
    upcomingLoading.value = false;
  }
}

async function cancelUpcoming(item: UpcomingItem, channel: ChannelId) {
  try {
    await api.post("/admin/billing-notices/upcoming/cancel", {
      payment_id: item.payment_id,
      step: item.step,
      channel,
      user_id: item.user_id,
      due_date: item.due_date
    });
    await loadUpcoming();
  } catch (e) {
    error.value = detail(e, "Não foi possível cancelar.");
  }
}

async function reactivateUpcoming(item: UpcomingItem, channel: ChannelId) {
  try {
    await api.post("/admin/billing-notices/upcoming/reactivate", { payment_id: item.payment_id, step: item.step, channel });
    await loadUpcoming();
  } catch (e) {
    error.value = detail(e, "Não foi possível reativar.");
  }
}

// ---------------------------------------------------------------- histórico

const history = ref<HistoryRow[]>([]);
const historyTotal = ref(0);
const historyLoading = ref(false);
const historyQuery = ref("");
const historyStatus = ref("");
const historyStep = ref("");
const historyFilters = [
  { id: "", label: "Todos" },
  { id: "sent", label: "Enviados" },
  { id: "failed", label: "Com falha" },
  { id: "cancelled", label: "Cancelados" }
];
const retrying = ref<number | null>(null);

async function loadHistory(reset: boolean) {
  historyLoading.value = true;
  try {
    const { data } = await api.get("/admin/billing-notices/history", {
      params: {
        status: historyStatus.value || undefined,
        step: historyStep.value || undefined,
        q: historyQuery.value.trim() || undefined,
        limit: 50,
        offset: reset ? 0 : history.value.length
      }
    });
    history.value = reset ? data.items : [...history.value, ...data.items];
    historyTotal.value = data.total;
  } catch (e) {
    error.value = detail(e, "Não foi possível carregar o histórico.");
  } finally {
    historyLoading.value = false;
  }
}

async function retry(row: HistoryRow) {
  retrying.value = row.id;
  try {
    const { data } = await api.post<HistoryRow>(`/admin/billing-notices/history/${row.id}/retry`);
    history.value = history.value.map(item => (item.id === row.id ? data : item));
    if (data.status === "sent") flash("Enviado.");
    else error.value = data.error ? `Não saiu: ${data.error}` : "Não saiu.";
  } catch (e) {
    error.value = detail(e, "Não foi possível tentar de novo.");
  } finally {
    retrying.value = null;
  }
}

watch(tab, value => {
  if (value === "upcoming" && !upcoming.value) loadUpcoming();
  if (value === "history" && !history.value.length) loadHistory(true);
});

// ---------------------------------------------------------------- formatos

const whatsappTone = computed(() => {
  const connection = settings.value?.whatsapp_connection;
  if (!connection) return "neutral";
  return connection.status === "connected" ? "success" : "danger";
});
const connectionStatusLabel = (status: string) =>
  ({ connected: "Conectado", connecting: "Conectando", disconnected: "Desconectado" } as Record<string, string>)[status] || status;
const stateLabel = (state: string) =>
  (
    {
      scheduled: "Vai sair",
      off: "Desligado",
      skipped: "Não sai",
      sent: "Enviado",
      failed: "Falhou",
      sending: "Enviando",
      cancelled: "Cancelado"
    } as Record<string, string>
  )[state] || state;
const stateTone = (state: string) =>
  (
    {
      scheduled: "am-tone-info",
      off: "am-tone-neutral",
      skipped: "am-tone-neutral",
      sent: "am-tone-success",
      failed: "am-tone-danger",
      sending: "am-tone-warning",
      cancelled: "am-tone-neutral"
    } as Record<string, string>
  )[state] || "am-tone-neutral";
const billingTypeLabel = (value: string | null) =>
  ({ PIX: "Pix", CREDIT_CARD: "Cartão", BOLETO: "Boleto", UNDEFINED: "A escolher" } as Record<string, string>)[value || ""] || value || "—";
const formatInt = (value: number | undefined | null) => new Intl.NumberFormat("pt-BR").format(value || 0);
const currency = (value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
const formatDate = (value: string | null) => (value ? value.slice(0, 10).split("-").reverse().join("/") : "");
const dateTime = (value: string | null) => (value ? new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" }) : "—");
const todayIso = () => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
function dayLabel(value: string) {
  if (value === todayIso()) return "Hoje";
  const date = new Date(`${value}T12:00:00`);
  return date.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });
}

onMounted(load);
</script>

<style scoped>
.tab-body {
  padding: 18px;
}
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
}
.setting-title {
  font-size: 14px;
  font-weight: 600;
}
.setting-hint {
  font-size: 12.5px;
  color: var(--muted-foreground);
  line-height: 1.5;
}
.checks {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
}
.checks li {
  display: flex;
  align-items: center;
  gap: 8px;
}
.checks li svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
.checks li.ok svg {
  color: var(--status-success-foreground);
}
.checks li.bad {
  color: var(--status-danger-foreground);
}
.rules {
  font-size: 13px;
  color: var(--muted-foreground);
  line-height: 1.7;
}
.rules summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--foreground);
}
.rules ul {
  margin-top: 8px;
  padding-left: 18px;
  list-style: disc;
}
.steps-layout {
  display: grid;
  grid-template-columns: minmax(0, 260px) minmax(0, 1fr);
}
.step-list {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  padding: 8px;
  gap: 4px;
}
.step-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  text-align: left;
}
.step-item:hover {
  background: var(--muted);
}
.step-item.on {
  background: var(--accent);
  color: var(--accent-foreground);
}
.step-name {
  font-size: 13.5px;
  font-weight: 600;
}
.step-desc {
  font-size: 12px;
  color: var(--muted-foreground);
}
.step-channels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}
.step-editor {
  padding: 18px;
  min-width: 0;
}
.variables {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.wa-preview {
  padding: 14px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--status-success) 55%, var(--muted));
}
.wa-bubble {
  max-width: 92%;
  padding: 9px 12px;
  border-radius: 10px 10px 10px 2px;
  background: var(--card);
  font-size: 13px;
  line-height: 1.5;
  overflow-wrap: anywhere;
  box-shadow: var(--shadow-soft);
}
.email-preview {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
}
.email-subject {
  font-weight: 600;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.email-body :deep(p) {
  margin-bottom: 8px;
}
.test-box {
  padding: 14px 16px;
  border: 1px dashed var(--border);
  border-radius: 14px;
}
.link {
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
}
.reason {
  max-width: 220px;
  font-size: 11.5px;
  margin-top: 4px;
}
@media (max-width: 900px) {
  .steps-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .step-list {
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }
  .setting-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
