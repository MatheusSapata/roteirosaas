<template>
  <div class="admin-master-surface am-page w-full">
    <AdminMasterHeader title="Webhooks e push" subtitle="Quais eventos mandam aviso no celular pelo Pushover: o texto, o som e quem recebe cada um.">
      <button v-if="tab === 'events'" type="button" class="am-btn am-btn-primary" @click="createNewRule"><AmIcon name="plus" />Novo evento</button>
      <button v-else type="button" class="am-btn am-btn-primary" @click="newAccount"><AmIcon name="plus" />Nova conta</button>
    </AdminMasterHeader>

    <nav class="am-tabs mb-3.5" aria-label="Seções de webhooks e push">
      <button type="button" class="am-tab" :class="{ on: tab === 'events' }" @click="tab = 'events'">
        Eventos <span class="am-count">{{ rules.length }}</span>
      </button>
      <button type="button" class="am-tab" :class="{ on: tab === 'pushover' }" @click="tab = 'pushover'">
        Pushover <span class="am-count">{{ accounts.length }}</span>
      </button>
    </nav>

    <section v-if="tab === 'events'" class="grid gap-3.5 lg:grid-cols-[300px_minmax(0,1fr)]">
      <aside class="am-card !p-2.5">
        <div class="flex items-center justify-between px-2 pb-2.5 pt-1.5">
          <b class="text-[13.5px]">Eventos</b>
          <span class="am-card-sub !mt-0">{{ activeRulesCount }} de {{ rules.length }} ligados</span>
        </div>
        <button
          v-for="rule in rules"
          :key="rule.id"
          type="button"
          class="wh-event"
          :class="{ on: selectedRuleId === rule.id }"
          @click="selectRule(rule)"
        >
          <span class="text-lg leading-none">{{ iconEmoji(rule.icon_tag) }}</span>
          <span class="min-w-0 flex-1 text-left">
            <b class="block truncate text-[13px]">{{ rule.display_name }}</b>
            <small class="am-muted block truncate">{{ channelSummary(rule) }}</small>
          </span>
          <span class="am-badge am-dot" :class="rule.enabled ? 'am-tone-success' : 'am-tone-neutral'">{{ rule.enabled ? "Ligado" : "Desligado" }}</span>
        </button>
        <p v-if="!rules.length" class="am-empty">Nenhum evento cadastrado.</p>
      </aside>

      <section class="am-card">
        <div class="am-card-head flex-wrap">
          <div>
            <h2 class="am-card-title">{{ formTitle }}</h2>
            <p class="am-card-sub">
              {{ selectedRule?.is_builtin ? "Evento padrão do sistema" : selectedRule ? "Evento personalizado" : "Novo evento personalizado" }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button type="button" class="am-btn am-btn-sm" :disabled="!selectedRule || testing" @click="testSelectedRule">
              <AmIcon name="play" />{{ testing ? "Enviando..." : "Enviar teste" }}
            </button>
            <button type="button" class="am-btn am-btn-sm am-btn-primary" :disabled="saving" @click="saveRule">
              {{ saving ? "Salvando..." : "Salvar" }}
            </button>
          </div>
        </div>

        <div v-if="testResult" class="am-notice mb-4" :class="testResult.success ? 'am-tone-success' : 'am-tone-warning'" role="status">
          <AmIcon :name="testResult.success ? 'check' : 'alert'" />
          <span>
            {{ testResult.message }}
            <span v-for="item in testResult.deliveries" :key="`${item.channel}-${item.target}`" class="wh-delivery">
              {{ item.ok ? "✓" : "✗" }} {{ `Pushover · ${item.target}` }}<template v-if="item.error"> ({{ item.error }})</template>
            </span>
          </span>
        </div>

        <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
          <div class="space-y-4">
            <div class="grid gap-3.5 md:grid-cols-2">
              <div class="am-field">
                <label for="wh-key">Evento</label>
                <input id="wh-key" v-model="form.event_key" :disabled="isBuiltinSelected" class="am-input am-mono" placeholder="subscription_created" />
              </div>
              <div class="am-field">
                <label for="wh-name">Nome</label>
                <input id="wh-name" v-model="form.display_name" class="am-input" placeholder="Nova assinatura" />
              </div>
            </div>
            <div class="am-field">
              <label for="wh-desc">Quando dispara</label>
              <textarea id="wh-desc" v-model="form.description" rows="2" class="am-input !min-h-[64px]" placeholder="Explique quando este aviso é enviado"></textarea>
            </div>
            <div class="am-field">
              <label for="wh-title">Título</label>
              <input id="wh-title" v-model="form.title_template" class="am-input am-mono" placeholder="Compra aprovada - {{plan_name}}" />
            </div>
            <div class="am-field">
              <label for="wh-body">Texto</label>
              <input id="wh-body" v-model="form.body_template" class="am-input am-mono" placeholder="{{amount}} | {{user_name}} | {{payment_method}}" />
            </div>
            <div class="grid gap-3.5 sm:grid-cols-2">
              <div class="am-field">
                <label for="wh-priority">Prioridade no celular</label>
                <select id="wh-priority" v-model.number="form.priority" class="am-input">
                  <option v-for="option in priorityOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </div>
              <div class="am-field">
                <label for="wh-order">Ordem na lista</label>
                <input id="wh-order" v-model.number="form.sort_order" type="number" class="am-input" />
              </div>
            </div>
            <div class="rounded-[14px] border border-border px-4 py-3">
              <p class="am-eyebrow mb-2.5">Quem recebe</p>
              <div v-for="account in accounts" :key="account.id" class="wh-channel">
                <div class="min-w-0">
                  <b class="block truncate text-[13px]">Pushover · {{ account.name }}</b>
                  <small class="am-muted text-xs">{{ account.enabled ? (account.device ? `Aparelho ${account.device}` : "Todos os aparelhos") : "Conta desligada" }}</small>
                </div>
                <button
                  type="button"
                  class="am-switch"
                  :class="{ on: account.event_keys.includes(form.event_key) }"
                  role="switch"
                  :aria-checked="account.event_keys.includes(form.event_key)"
                  :aria-label="`Enviar para ${account.name}`"
                  :disabled="!form.id || accountSaving === account.id"
                  :title="form.id ? undefined : 'Salve o evento primeiro'"
                  @click="toggleAccountEvent(account, form.event_key)"
                ></button>
              </div>
              <div v-if="accounts.length" class="mt-2 grid gap-2" :class="{ 'sm:grid-cols-2': soundChoice === CUSTOM_SOUND }">
                <div class="am-field">
                  <label for="wh-sound">Som no Pushover</label>
                  <select id="wh-sound" v-model="soundChoice" class="am-input">
                    <option value="">{{ defaultSoundLabel }}</option>
                    <option v-for="sound in soundOptions" :key="sound.value" :value="sound.value">{{ sound.label }}</option>
                    <option :value="CUSTOM_SOUND">Outro som (pelo nome)...</option>
                  </select>
                </div>
                <div v-if="soundChoice === CUSTOM_SOUND" class="am-field">
                  <label for="wh-sound-name">Nome do som no Pushover</label>
                  <input id="wh-sound-name" v-model.trim="form.pushover_sound" class="am-input am-mono" maxlength="40" placeholder="viajeonvenda" />
                </div>
              </div>
              <p v-if="accounts.length && soundHint" class="am-card-sub !mt-1">{{ soundHint }}</p>
              <p v-if="!accounts.length" class="am-card-sub !mt-1">
                Nenhuma conta do Pushover.
                <button type="button" class="wh-link" @click="tab = 'pushover'; newAccount()">Cadastrar conta</button>
              </p>
              <p v-else class="am-card-sub !mt-1">O som salva com o evento; quem recebe muda na hora.</p>
            </div>
            <div class="flex items-center justify-between gap-3 rounded-[14px] border border-border px-4 py-3">
              <div>
                <b class="block text-[13px]">Evento ligado</b>
                <small class="am-muted text-xs">Desligado, o evento não manda aviso.</small>
              </div>
              <button type="button" class="am-switch" :class="{ on: form.enabled }" role="switch" :aria-checked="form.enabled" aria-label="Evento ligado" @click="form.enabled = !form.enabled"></button>
            </div>

            <div>
              <p class="am-eyebrow mb-2">Variáveis · clique para copiar</p>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="field in meta?.available_fields || defaultAvailableFields"
                  :key="field"
                  type="button"
                  class="wh-var"
                  @click="copyField(field)"
                >
                  {{ tokenForField(field) }}
                </button>
              </div>
            </div>

            <div>
              <p class="am-eyebrow mb-2">Ícone no título do aviso</p>
              <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 2xl:grid-cols-5">
                <button
                  v-for="icon in meta?.icons || defaultIcons"
                  :key="icon.tag"
                  type="button"
                  class="wh-icon"
                  :class="{ on: form.icon_tag === icon.tag }"
                  @click="form.icon_tag = icon.tag"
                >
                  <span class="text-lg">{{ icon.emoji }}</span>
                  <b class="min-w-0 truncate text-[12.5px]">{{ icon.label }}</b>
                </button>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div>
              <p class="am-eyebrow mb-2">Como chega no celular</p>
              <div class="wh-phone">
                <div class="wh-push">
                  <div class="wh-push-icon">{{ iconEmoji(form.icon_tag) }}</div>
                  <div class="min-w-0">
                    <b class="block truncate text-[12.5px]">{{ previewTitle }}</b>
                    <p class="am-muted whitespace-pre-line text-xs leading-5">{{ previewBody }}</p>
                  </div>
                </div>
                <p class="am-card-sub mt-2.5 text-center">{{ channelSummary(form) }} · agora</p>
              </div>
            </div>

            <div v-if="selectedRule && !selectedRule.is_builtin" class="rounded-[14px] border border-border p-4">
              <button type="button" class="am-btn am-btn-sm am-btn-danger" :disabled="deleting" @click="removeRule">
                <AmIcon name="trash" />{{ deleting ? "Excluindo..." : "Excluir evento" }}
              </button>
              <p class="am-card-sub">Só eventos personalizados podem ser excluídos.</p>
            </div>
            <p v-else-if="selectedRule" class="am-card-sub">Eventos padrão do sistema não podem ser excluídos, só desligados.</p>
          </div>
        </div>
      </section>
    </section>

    <section v-else class="grid gap-3.5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div class="space-y-3.5">
        <div class="am-notice am-tone-info">
          <AmIcon name="info" />
          <span>
            Cada pessoa que recebe os avisos tem a própria conta do Pushover (sem Pushover Teams). Um aplicativo criado em
            <a class="wh-link" href="https://pushover.net/apps/build" target="_blank" rel="noopener">pushover.net/apps/build</a>
            serve para todas: o token dele só precisa ser informado na primeira conta.
          </span>
        </div>
        <article v-for="account in accounts" :key="account.id" class="am-card wh-account" :class="{ on: editingAccountId === account.id }">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="min-w-0">
              <b class="block text-[14px]">{{ account.name }}</b>
              <small class="am-mono am-muted block">Usuário {{ account.user_key_masked }} · Aplicativo {{ account.app_token_masked }}</small>
              <small class="am-muted block">{{ account.device ? `Aparelho ${account.device}` : "Todos os aparelhos da conta" }}</small>
            </div>
            <div class="flex items-center gap-2">
              <span class="am-badge am-dot" :class="account.enabled ? 'am-tone-success' : 'am-tone-neutral'">{{ account.enabled ? "Ligada" : "Desligada" }}</span>
            </div>
          </div>
          <div class="mt-3 flex flex-wrap gap-1.5">
            <span v-for="key in account.event_keys" :key="key" class="am-chip on">{{ ruleName(key) }}</span>
            <span v-if="!account.event_keys.length" class="am-muted text-xs">Nenhum evento escolhido: não recebe avisos.</span>
          </div>
          <p v-if="account.last_error" class="am-notice am-tone-danger mt-3"><AmIcon name="alert" /><span>Último envio falhou: {{ account.last_error }}</span></p>
          <p v-else-if="account.last_sent_at" class="am-card-sub mt-3">Último aviso entregue em {{ formatDate(account.last_sent_at) }}.</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <button type="button" class="am-btn am-btn-sm" :disabled="accountTesting === account.id" @click="testAccount(account)">
              <AmIcon name="play" />{{ accountTesting === account.id ? "Enviando..." : "Enviar teste" }}
            </button>
            <button type="button" class="am-btn am-btn-sm" @click="editAccount(account)">Editar</button>
            <button type="button" class="am-btn am-btn-sm am-btn-danger" @click="removeAccount(account)"><AmIcon name="trash" />Excluir</button>
          </div>
        </article>
        <p v-if="!accounts.length" class="am-card am-empty">Nenhuma conta cadastrada. Cadastre a primeira ao lado.</p>
      </div>

      <form class="am-card space-y-3.5 self-start" @submit.prevent="saveAccount">
        <div>
          <h2 class="am-card-title">{{ editingAccountId ? "Editar conta" : "Nova conta" }}</h2>
          <p class="am-card-sub">As chaves ficam guardadas criptografadas; depois de salvar, só o final delas aparece.</p>
        </div>
        <div class="am-field">
          <label for="po-name">Nome</label>
          <input id="po-name" v-model="accountForm.name" class="am-input" placeholder="Ex.: Matheus" required />
        </div>
        <div class="am-field">
          <label for="po-user">Chave do usuário (User Key)</label>
          <input
            id="po-user"
            v-model="accountForm.user_key"
            class="am-input am-mono"
            autocomplete="off"
            :placeholder="editingAccount ? `Em branco: mantém ${editingAccount.user_key_masked}` : 'Aparece no topo do painel em pushover.net'"
          />
        </div>
        <div class="am-field">
          <label for="po-token">Token do aplicativo (API Token)</label>
          <input
            id="po-token"
            v-model="accountForm.app_token"
            class="am-input am-mono"
            autocomplete="off"
            :placeholder="editingAccount ? `Em branco: mantém ${editingAccount.app_token_masked}` : accounts.length ? 'Em branco: usa o token já cadastrado' : 'Do aplicativo criado em pushover.net/apps'"
          />
        </div>
        <div class="am-field">
          <label for="po-device">Aparelho (opcional)</label>
          <input id="po-device" v-model="accountForm.device" class="am-input am-mono" placeholder="Em branco: todos os aparelhos" />
        </div>
        <div>
          <p class="am-eyebrow mb-2">Eventos que esta conta recebe</p>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="rule in rules"
              :key="rule.event_key"
              type="button"
              class="am-chip"
              :class="{ on: accountForm.event_keys.includes(rule.event_key) }"
              :aria-pressed="accountForm.event_keys.includes(rule.event_key)"
              @click="toggleFormEvent(rule.event_key)"
            >
              {{ rule.display_name }}
            </button>
          </div>
        </div>
        <div class="flex items-center justify-between gap-3 rounded-[14px] border border-border px-4 py-3">
          <div>
            <b class="block text-[13px]">Conta ligada</b>
            <small class="am-muted text-xs">Desligada, não recebe nenhum aviso.</small>
          </div>
          <button type="button" class="am-switch" :class="{ on: accountForm.enabled }" role="switch" :aria-checked="accountForm.enabled" aria-label="Conta ligada" @click="accountForm.enabled = !accountForm.enabled"></button>
        </div>
        <p v-if="accountError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ accountError }}</span></p>
        <p v-if="accountMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ accountMessage }}</span></p>
        <div class="flex flex-wrap gap-2">
          <button type="submit" class="am-btn am-btn-primary" :disabled="accountSaving === 'form'">
            {{ accountSaving === "form" ? "Conferindo com o Pushover..." : editingAccountId ? "Salvar conta" : "Cadastrar conta" }}
          </button>
          <button v-if="editingAccountId" type="button" class="am-btn" @click="newAccount">Cancelar</button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";

// O que cada prioridade faz no Pushover (a 5 antiga era igual à 4).
const priorityOptions = [
  { value: 1, label: "Mínima · fica só na lista do app" },
  { value: 2, label: "Baixa · sem som nem vibração" },
  { value: 3, label: "Normal" },
  { value: 4, label: "Alta · toca mesmo nas horas de silêncio" }
];

type Rule = {
  id: number;
  event_key: string;
  display_name: string;
  description?: string | null;
  enabled: boolean;
  // Vazio: o padrão do evento (default_pushover_sound) ou, sem ele, o som padrão do app.
  pushover_sound?: string | null;
  default_pushover_sound?: string | null;
  title_template: string;
  body_template: string;
  icon_tag?: string | null;
  priority: number;
  sort_order: number;
  is_builtin: boolean;
};

type MetaIcon = { tag: string; label: string; emoji: string };
type MetaResponse = { icons: MetaIcon[]; available_fields: string[] };

const defaultIcons: MetaIcon[] = [
  { tag: "rocket", label: "Foguete", emoji: "🚀" },
  { tag: "arrow_up", label: "Seta para cima", emoji: "⬆️" },
  { tag: "heavy_check_mark", label: "Confirmado", emoji: "✔️" },
  { tag: "loudspeaker", label: "Aviso", emoji: "📢" },
  { tag: "warning", label: "Alerta", emoji: "⚠️" },
  { tag: "rotating_light", label: "Urgente", emoji: "🚨" },
  { tag: "skull", label: "Cancelamento", emoji: "💀" },
  { tag: "moneybag", label: "Financeiro", emoji: "💰" },
  { tag: "tada", label: "Celebração", emoji: "🎉" },
  { tag: "partying_face", label: "Comemoração", emoji: "🥳" }
];
const defaultAvailableFields = [
  "event_label", "user_name", "amount", "payment_method", "plan_name", "offer_name", "previous_plan_name",
  "upgraded_plan_name", "cancelled_item", "occurred_at", "purchase_kind", "customer_email", "customer_phone", "due_date"
];

// Contas do Pushover: uma por pessoa; cada uma escolhe os eventos que recebe.
type PushoverAccount = {
  id: number;
  name: string;
  user_key_masked: string;
  app_token_masked: string;
  device?: string | null;
  enabled: boolean;
  event_keys: string[];
  last_sent_at?: string | null;
  last_error?: string | null;
};
type Delivery = { channel: string; target: string; ok: boolean; error?: string | null };
type TestResult = { success: boolean; message?: string | null; deliveries: Delivery[] };
// Conta nova recebe os de vendas: dinheiro entrando (compra, renovação, upgrade), checkout e cobrança vencida.
const SALES_EVENTS = ["purchase_approved", "subscription_renewed", "upgrade_realizado", "checkout_started", "payment_overdue"];
// Sons do Pushover (pushover.net/api#sounds). Receita nova (compra, renovação, upgrade) toca por
// padrão o "viajeonvenda", som personalizado da conta dona do aplicativo (toca para todas as contas).
type PushoverSound = { value: string; label: string };
const REVENUE_SOUND = "viajeonvenda";
const CUSTOM_SOUND = "__custom__";
const pushoverSounds: PushoverSound[] = [
  { value: REVENUE_SOUND, label: "Venda Viaje On (viajeonvenda)" },
  { value: "cashregister", label: "Caixa registradora (cha-ching)" },
  { value: "pushover", label: "Pushover" },
  { value: "magic", label: "Mágica" },
  { value: "incoming", label: "Chegando" },
  { value: "gamelan", label: "Gamelão" },
  { value: "bike", label: "Campainha de bicicleta" },
  { value: "bugle", label: "Corneta" },
  { value: "classical", label: "Clássica" },
  { value: "cosmic", label: "Cósmica" },
  { value: "falling", label: "Caindo" },
  { value: "intermission", label: "Intervalo" },
  { value: "mechanical", label: "Mecânica" },
  { value: "pianobar", label: "Piano bar" },
  { value: "siren", label: "Sirene" },
  { value: "spacealarm", label: "Alarme espacial" },
  { value: "tugboat", label: "Rebocador" },
  { value: "alien", label: "Alarme alienígena (longo)" },
  { value: "climb", label: "Subida (longo)" },
  { value: "persistent", label: "Persistente (longo)" },
  { value: "echo", label: "Eco do Pushover (longo)" },
  { value: "updown", label: "Sobe e desce (longo)" },
  { value: "vibrate", label: "Só vibrar" },
  { value: "none", label: "Sem som" }
];
// Sons que tocam para as contas, com os personalizados do aplicativo (vazio: sem conta ou sem resposta).
const accountSounds = ref<PushoverSound[] | null>(null);
const soundOptions = computed<PushoverSound[]>(() => {
  const known = new Set(pushoverSounds.map(sound => sound.value));
  const extra = (accountSounds.value || [])
    .filter(sound => !known.has(sound.value))
    .map(sound => ({ value: sound.value, label: `${sound.label} (personalizado)` }));
  return [...pushoverSounds, ...extra];
});
const soundLabel = (value: string) => soundOptions.value.find(sound => sound.value === value)?.label || value;

const tab = ref<"events" | "pushover">("events");
const accounts = ref<PushoverAccount[]>([]);
const accountSaving = ref<number | "form" | null>(null);
const accountTesting = ref<number | null>(null);
const editingAccountId = ref<number | null>(null);
const editingAccount = computed(() => accounts.value.find(account => account.id === editingAccountId.value) || null);
const accountError = ref("");
const accountMessage = ref("");
const testResult = ref<TestResult | null>(null);
const emptyAccountForm = () => ({ name: "", user_key: "", app_token: "", device: "", enabled: true, event_keys: [...SALES_EVENTS] });
const accountForm = reactive(emptyAccountForm());

const rules = ref<Rule[]>([]);
const meta = ref<MetaResponse | null>(null);
const selectedRuleId = ref<number | null>(null);
const selectedRule = computed(() => rules.value.find(rule => rule.id === selectedRuleId.value) || null);
const saving = ref(false);
const deleting = ref(false);
const testing = ref(false);

const emptyForm = (): Rule => ({
  id: 0,
  event_key: "",
  display_name: "",
  description: "",
  enabled: true,
  pushover_sound: "",
  default_pushover_sound: null,
  title_template: "Aviso - {{plan_name}}",
  body_template: "{{amount}} | {{user_name}} | {{payment_method}}",
  icon_tag: "loudspeaker",
  priority: 3,
  sort_order: 0,
  is_builtin: false
});

const form = reactive<Rule>(emptyForm());

// Som do evento: vazio usa o padrão do evento; "Outro som personalizado" abre o campo do nome.
const customSoundMode = ref(false);
const soundChoice = computed({
  get: () => {
    const value = form.pushover_sound || "";
    if (customSoundMode.value || (value && !soundOptions.value.some(sound => sound.value === value))) return CUSTOM_SOUND;
    return value;
  },
  set: (value: string) => {
    customSoundMode.value = value === CUSTOM_SOUND;
    form.pushover_sound = value === CUSTOM_SOUND ? "" : value;
  }
});
const defaultSoundLabel = computed(() =>
  form.default_pushover_sound ? `Padrão: ${soundLabel(form.default_pushover_sound)}` : "Padrão do app Pushover"
);
const soundHint = computed(() => {
  const sound = (form.pushover_sound || "").trim() || form.default_pushover_sound || "";
  if (!sound || pushoverSounds.some(item => item.value === sound && item.value !== REVENUE_SOUND)) return "";
  if (accountSounds.value?.some(item => item.value === sound)) return `O som "${sound}" está no Pushover e toca para todas as contas.`;
  return `"${sound}" é um som personalizado: suba o arquivo com esse nome em pushover.net (Your Custom Sounds), na conta dona do aplicativo (a do token). Ele passa a tocar para todas as contas; sem ele, o aviso toca o som padrão do app.`;
});

const isBuiltinSelected = computed(() => Boolean(selectedRule.value?.is_builtin));
const activeRulesCount = computed(() => rules.value.filter(rule => rule.enabled).length);

const formTitle = computed(() => (form.id ? form.display_name || form.event_key || "Evento" : "Novo evento"));

const iconEmoji = (tag?: string | null) => meta.value?.icons.find(icon => icon.tag === tag)?.emoji || defaultIcons.find(icon => icon.tag === tag)?.emoji || "🔔";
const tokenForField = (field: string) => `{{${field}}}`;

const errorText = (error: any, fallback: string) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
};
const ruleName = (key: string) => rules.value.find(rule => rule.event_key === key)?.display_name || key;
const formatDate = (value: string) => new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
// "Pushover (Matheus)", "Pushover (2 contas)", "Nenhuma conta".
const channelSummary = (rule: Pick<Rule, "event_key">) => {
  const names = accounts.value.filter(account => account.enabled && account.event_keys.includes(rule.event_key)).map(account => account.name);
  return names.length === 1 ? `Pushover (${names[0]})` : names.length ? `Pushover (${names.length} contas)` : "Nenhuma conta";
};

const loadAccounts = async () => {
  const { data } = await api.get<PushoverAccount[]>("/admin-master/webhook-notifications/pushover-accounts");
  accounts.value = data || [];
  if (accountSounds.value === null && accounts.value.some(account => account.enabled)) void loadAccountSounds();
};

// Uma vez por visita: só ajuda a listar os sons personalizados da conta.
const loadAccountSounds = async () => {
  accountSounds.value = [];
  try {
    const { data } = await api.get<PushoverSound[]>("/admin-master/webhook-notifications/pushover-sounds");
    accountSounds.value = data || [];
  } catch {
    accountSounds.value = [];
  }
};

const loadData = async () => {
  // Eventos antes das contas: listar os eventos acerta, uma vez, os eventos de cada conta (o
  // "Nova assinatura" virou a "Compra aprovada").
  const [rulesRes, metaRes] = await Promise.all([
    api.get<Rule[]>("/admin-master/webhook-notifications"),
    api.get<MetaResponse>("/admin-master/webhook-notifications/meta")
  ]);
  await loadAccounts();
  rules.value = rulesRes.data || [];
  meta.value = metaRes.data || null;
  if (!selectedRuleId.value && rules.value.length) {
    selectRule(rules.value[0]);
  }
};

const resetFormFromRule = (rule: Rule) => {
  form.id = rule.id;
  form.event_key = rule.event_key;
  form.display_name = rule.display_name;
  form.description = rule.description || "";
  form.enabled = rule.enabled;
  form.pushover_sound = rule.pushover_sound || "";
  form.default_pushover_sound = rule.default_pushover_sound || null;
  customSoundMode.value = false;
  form.title_template = rule.title_template;
  form.body_template = rule.body_template;
  form.icon_tag = rule.icon_tag || "";
  form.priority = Math.min(Math.max(Number(rule.priority) || 3, 1), 4);
  form.sort_order = rule.sort_order;
  form.is_builtin = rule.is_builtin;
};

const selectRule = (rule: Rule) => {
  selectedRuleId.value = rule.id;
  testResult.value = null;
  resetFormFromRule(rule);
};

const createNewRule = () => {
  selectedRuleId.value = null;
  const next = emptyForm();
  Object.assign(form, next);
  customSoundMode.value = false;
};

const saveRule = async () => {
  saving.value = true;
  try {
    const payload = {
      event_key: form.event_key.trim(),
      display_name: form.display_name.trim(),
      description: form.description?.trim() || null,
      enabled: form.enabled,
      // Texto vazio = som padrão do evento ("viajeonvenda" nas receitas; nos outros, o do app).
      pushover_sound: (form.pushover_sound || "").trim(),
      title_template: form.title_template.trim(),
      body_template: form.body_template.trim(),
      icon_tag: form.icon_tag?.trim() || null,
      priority: Number(form.priority || 3),
      sort_order: Number(form.sort_order || 0),
      is_builtin: Boolean(form.is_builtin)
    };
    const { data } = form.id
      ? await api.put<Rule>(`/admin-master/webhook-notifications/${form.id}`, payload)
      : await api.post<Rule>("/admin-master/webhook-notifications", payload);
    await loadData();
    const updated = rules.value.find(rule => rule.id === data.id) || data;
    selectRule(updated);
  } finally {
    saving.value = false;
  }
};

const removeRule = async () => {
  if (!selectedRule.value || selectedRule.value.is_builtin) return;
  deleting.value = true;
  try {
    await api.delete(`/admin-master/webhook-notifications/${selectedRule.value.id}`);
    selectedRuleId.value = null;
    createNewRule();
    await loadData();
  } finally {
    deleting.value = false;
  }
};

const previewContext = computed(() => {
  const rule = selectedRule.value;
  if (!rule) {
    return {
      event_label: form.display_name || "Evento",
      user_name: "Daniel Teste",
      amount: "R$ 149,90",
      payment_method: "Cartão de crédito",
      plan_name: "Plano Growth",
      offer_name: "Oferta Growth Mensal",
      previous_plan_name: "Plano Essencial",
      upgraded_plan_name: "Plano Growth",
      cancelled_item: "Assinatura mensal do Plano Growth",
      occurred_at: "02/06/2026 13:00"
    };
  }
  const sales = {
    event_label: rule.display_name,
    user_name: "Ana Teste",
    amount: "R$ 67,00",
    payment_method: "PIX",
    plan_name: "Roteiro Online Mensal",
    offer_name: "mensal",
    customer_email: "ana@exemplo.com",
    customer_phone: "(11) 98765-4321",
    occurred_at: "02/06/2026 13:00"
  };
  if (rule.event_key === "purchase_approved") return { ...sales, purchase_kind: "Nova assinatura" };
  if (rule.event_key === "checkout_started") return { ...sales, payment_method: "", purchase_kind: "Nova compra" };
  if (rule.event_key === "payment_overdue") return { ...sales, amount: "R$ 97,00", due_date: "10/06/2026", purchase_kind: "Renovação" };
  if (rule.event_key === "subscription_cancelled") {
    return {
      event_label: rule.display_name,
      user_name: "Carla Teste",
      amount: "R$ 297,00",
      payment_method: "",
      plan_name: "Plano Growth",
      offer_name: "Oferta Growth Mensal",
      cancelled_item: "Assinatura mensal do Plano Growth",
      occurred_at: "02/06/2026 13:00"
    };
  }
  if (rule.event_key === "upgrade_realizado") {
    return {
      event_label: rule.display_name,
      user_name: "Daniel Teste",
      amount: "R$ 149,90",
      payment_method: "",
      plan_name: "Plano Growth",
      previous_plan_name: "Plano Essencial",
      upgraded_plan_name: "Plano Growth",
      occurred_at: "02/06/2026 13:00"
    };
  }
  return {
    event_label: rule.display_name,
    user_name: "Ana Teste",
    amount: "R$ 197,00",
    payment_method: "PIX",
    plan_name: "Plano Essencial",
    offer_name: "Oferta Essencial Mensal",
    previous_plan_name: "Plano Essencial",
    upgraded_plan_name: "Plano Growth",
    cancelled_item: "Assinatura mensal do Plano Growth",
    occurred_at: "02/06/2026 13:00"
  };
});

const renderTemplate = (template: string, context: Record<string, string>) => {
  if (!template) return "";
  return template.replace(/{{\s*([a-zA-Z0-9_.-]+)\s*}}/g, (_, key) => context[key] || "");
};

const previewTitle = computed(() => renderTemplate(form.title_template, previewContext.value as Record<string, string>));
const previewBody = computed(() => renderTemplate(form.body_template, previewContext.value as Record<string, string>));

const copyField = async (field: string) => {
  const token = `{{${field}}}`;
  try {
    await navigator.clipboard.writeText(token);
  } catch {
    window.prompt("Copie o campo:", token);
  }
};

const buildTestContext = () => {
  const rule = selectedRule.value;
  if (!rule) return {};
  return previewContext.value;
};

const testSelectedRule = async () => {
  if (!selectedRule.value) return;
  testing.value = true;
  testResult.value = null;
  try {
    const { data } = await api.post<TestResult>(`/admin-master/webhook-notifications/${selectedRule.value.id}/test`, {
      event_key: selectedRule.value.event_key,
      context: buildTestContext()
    });
    testResult.value = data;
    await loadAccounts();
  } catch (error) {
    testResult.value = { success: false, message: errorText(error, "Não foi possível enviar o teste."), deliveries: [] };
  } finally {
    testing.value = false;
  }
};

// Liga ou desliga um evento numa conta do Pushover (vale na hora).
const toggleAccountEvent = async (account: PushoverAccount, eventKey: string) => {
  if (!eventKey) return;
  const event_keys = account.event_keys.includes(eventKey)
    ? account.event_keys.filter(key => key !== eventKey)
    : [...account.event_keys, eventKey];
  accountSaving.value = account.id;
  try {
    const { data } = await api.put<PushoverAccount>(`/admin-master/webhook-notifications/pushover-accounts/${account.id}`, { event_keys });
    accounts.value = accounts.value.map(item => (item.id === data.id ? data : item));
  } finally {
    accountSaving.value = null;
  }
};

const newAccount = () => {
  editingAccountId.value = null;
  accountError.value = "";
  accountMessage.value = "";
  Object.assign(accountForm, emptyAccountForm());
};

const editAccount = (account: PushoverAccount) => {
  editingAccountId.value = account.id;
  accountError.value = "";
  accountMessage.value = "";
  Object.assign(accountForm, {
    name: account.name,
    user_key: "",
    app_token: "",
    device: account.device || "",
    enabled: account.enabled,
    event_keys: [...account.event_keys]
  });
};

const toggleFormEvent = (key: string) => {
  accountForm.event_keys = accountForm.event_keys.includes(key)
    ? accountForm.event_keys.filter(item => item !== key)
    : [...accountForm.event_keys, key];
};

const saveAccount = async () => {
  accountSaving.value = "form";
  accountError.value = "";
  accountMessage.value = "";
  const payload: Record<string, unknown> = {
    name: accountForm.name.trim(),
    device: accountForm.device.trim() || null,
    enabled: accountForm.enabled,
    event_keys: accountForm.event_keys
  };
  // Em branco ao editar: o servidor mantém a chave e o token atuais.
  if (accountForm.user_key.trim()) payload.user_key = accountForm.user_key.trim();
  if (accountForm.app_token.trim()) payload.app_token = accountForm.app_token.trim();
  try {
    const { data } = editingAccountId.value
      ? await api.put<PushoverAccount>(`/admin-master/webhook-notifications/pushover-accounts/${editingAccountId.value}`, payload)
      : await api.post<PushoverAccount>("/admin-master/webhook-notifications/pushover-accounts", payload);
    await loadAccounts();
    editAccount(data);
    accountMessage.value = "Conta salva. Use \"Enviar teste\" para conferir no celular.";
  } catch (error) {
    accountError.value = errorText(error, "Não foi possível salvar a conta.");
  } finally {
    accountSaving.value = null;
  }
};

const testAccount = async (account: PushoverAccount) => {
  accountTesting.value = account.id;
  try {
    const { data } = await api.post<PushoverAccount>(`/admin-master/webhook-notifications/pushover-accounts/${account.id}/test`);
    accounts.value = accounts.value.map(item => (item.id === data.id ? data : item));
  } catch (error) {
    await loadAccounts();
    if (!accounts.value.find(item => item.id === account.id)?.last_error) {
      accountError.value = errorText(error, "O Pushover não entregou o teste.");
    }
  } finally {
    accountTesting.value = null;
  }
};

const removeAccount = async (account: PushoverAccount) => {
  if (!window.confirm(`Excluir a conta do Pushover "${account.name}"? Ela deixa de receber os avisos.`)) return;
  await api.delete(`/admin-master/webhook-notifications/pushover-accounts/${account.id}`);
  if (editingAccountId.value === account.id) newAccount();
  await loadAccounts();
};

watch(
  () => selectedRule.value?.id,
  () => {
    if (selectedRule.value) {
      resetFormFromRule(selectedRule.value);
    }
  }
);

onMounted(async () => {
  await loadData();
});
</script>

<style scoped>
.wh-channel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
}
.wh-channel + .wh-channel {
  border-top: 1px solid var(--border);
}
.wh-link {
  font-weight: 600;
  color: var(--primary);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.wh-delivery {
  display: block;
  margin-top: 2px;
  font-size: 12.5px;
}
.wh-account.on {
  box-shadow: inset 0 0 0 1.5px var(--primary);
}
.wh-event {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  border-radius: 12px;
  padding: 10px 12px;
  transition: background-color 0.15s ease;
}
.wh-event:hover {
  background: var(--muted);
}
.wh-event.on {
  background: var(--muted);
  box-shadow: inset 2px 0 0 var(--primary);
}
.wh-var {
  display: inline-flex;
  height: 26px;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--muted);
  padding: 0 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11.5px;
  color: var(--accent-foreground);
}
.wh-var:hover {
  border-color: var(--primary);
}
.wh-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px 10px;
  text-align: left;
}
.wh-icon:hover {
  background: var(--muted);
}
.wh-icon.on {
  border-color: var(--primary);
  background: var(--accent);
}
.wh-phone {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--background);
  padding: 12px;
}
.wh-push {
  display: flex;
  gap: 10px;
  border-radius: 14px;
  background: var(--muted);
  padding: 10px 12px;
}
.wh-push-icon {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: var(--accent);
  font-size: 18px;
}
</style>
