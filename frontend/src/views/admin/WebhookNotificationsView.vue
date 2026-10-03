<template>
  <div class="admin-master-surface am-page w-full">
    <AdminMasterHeader title="Webhooks e push" subtitle="Quais eventos mandam aviso no celular (ntfy), com o texto e o ícone de cada um.">
      <button type="button" class="am-btn am-btn-primary" @click="createNewRule"><AmIcon name="plus" />Novo evento</button>
    </AdminMasterHeader>

    <section class="grid gap-3.5 lg:grid-cols-[300px_minmax(0,1fr)]">
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
            <small class="am-mono am-muted block truncate">{{ rule.event_key }}</small>
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
              <input id="wh-title" v-model="form.title_template" class="am-input am-mono" placeholder="Assinatura criada - {{plan_name}}" />
            </div>
            <div class="am-field">
              <label for="wh-body">Texto</label>
              <input id="wh-body" v-model="form.body_template" class="am-input am-mono" placeholder="{{amount}} | {{user_name}} | {{payment_method}}" />
            </div>
            <div class="grid gap-3.5 sm:grid-cols-3">
              <div class="am-field">
                <label for="wh-topic">Tópico</label>
                <input id="wh-topic" v-model="form.topic" class="am-input am-mono" placeholder="roteiro_online_assinaturas" />
              </div>
              <div class="am-field">
                <label for="wh-priority">Prioridade</label>
                <select id="wh-priority" v-model.number="form.priority" class="am-input">
                  <option v-for="option in priorityOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </div>
              <div class="am-field">
                <label for="wh-order">Ordem na lista</label>
                <input id="wh-order" v-model.number="form.sort_order" type="number" class="am-input" />
              </div>
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
              <p class="am-eyebrow mb-2">Ícone · a tag precisa existir no ntfy</p>
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
                  <span class="min-w-0">
                    <b class="block truncate text-[12.5px]">{{ icon.label }}</b>
                    <small class="am-mono am-muted block truncate">{{ icon.tag }}</small>
                  </span>
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
                <p class="am-card-sub mt-2.5 text-center">ntfy · {{ form.topic || "sem tópico" }} · agora</p>
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";

const priorityOptions = [
  { value: 1, label: "Mínima (1)" },
  { value: 2, label: "Baixa (2)" },
  { value: 3, label: "Normal (3)" },
  { value: 4, label: "Alta (4)" },
  { value: 5, label: "Urgente (5)" }
];

type Rule = {
  id: number;
  event_key: string;
  display_name: string;
  description?: string | null;
  enabled: boolean;
  title_template: string;
  body_template: string;
  icon_tag?: string | null;
  priority: number;
  topic?: string | null;
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
const defaultAvailableFields = ["event_label", "user_name", "amount", "payment_method", "plan_name", "offer_name", "previous_plan_name", "upgraded_plan_name", "cancelled_item", "occurred_at"];

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
  title_template: "Assinatura criada - {{plan_name}}",
  body_template: "{{amount}} | {{user_name}} | {{payment_method}}",
  icon_tag: "rocket",
  priority: 3,
  topic: "roteiro_online_assinaturas",
  sort_order: 0,
  is_builtin: false
});

const form = reactive<Rule>(emptyForm());

const isBuiltinSelected = computed(() => Boolean(selectedRule.value?.is_builtin));
const activeRulesCount = computed(() => rules.value.filter(rule => rule.enabled).length);

const formTitle = computed(() => (form.id ? form.display_name || form.event_key || "Evento" : "Novo evento"));

const iconEmoji = (tag?: string | null) => meta.value?.icons.find(icon => icon.tag === tag)?.emoji || defaultIcons.find(icon => icon.tag === tag)?.emoji || "🔔";
const tokenForField = (field: string) => `{{${field}}}`;

const loadData = async () => {
  const [rulesRes, metaRes] = await Promise.all([
    api.get<Rule[]>("/admin-master/webhook-notifications"),
    api.get<MetaResponse>("/admin-master/webhook-notifications/meta")
  ]);
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
  form.title_template = rule.title_template;
  form.body_template = rule.body_template;
  form.icon_tag = rule.icon_tag || "";
  form.priority = rule.priority;
  form.topic = rule.topic || "";
  form.sort_order = rule.sort_order;
  form.is_builtin = rule.is_builtin;
};

const selectRule = (rule: Rule) => {
  selectedRuleId.value = rule.id;
  resetFormFromRule(rule);
};

const createNewRule = () => {
  selectedRuleId.value = null;
  const next = emptyForm();
  Object.assign(form, next);
};

const saveRule = async () => {
  saving.value = true;
  try {
    const payload = {
      event_key: form.event_key.trim(),
      display_name: form.display_name.trim(),
      description: form.description?.trim() || null,
      enabled: form.enabled,
      title_template: form.title_template.trim(),
      body_template: form.body_template.trim(),
      icon_tag: form.icon_tag?.trim() || null,
      priority: Number(form.priority || 3),
      topic: form.topic?.trim() || null,
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
  try {
    await api.post(`/admin-master/webhook-notifications/${selectedRule.value.id}/test`, {
      event_key: selectedRule.value.event_key,
      context: buildTestContext()
    });
  } finally {
    testing.value = false;
  }
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
