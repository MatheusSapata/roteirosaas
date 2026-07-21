<template>
  <div class="admin-master-surface w-full space-y-6 px-4 py-8 md:px-8">
    <section class="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div class="max-w-3xl">
          <p class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">Admin master</p>
          <h1 class="mt-2 text-2xl font-bold text-slate-900 md:text-3xl">Gestão de webhooks e push</h1>
          <p class="mt-2 text-sm leading-6 text-slate-500">
            Configure quais eventos disparam push, edite o título, corpo e ícone permitido, e teste tudo antes de ativar em produção.
          </p>
        </div>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div class="rounded-2xl bg-slate-50 px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Eventos</p>
            <p class="mt-1 text-xl font-bold text-slate-900">{{ rules.length }}</p>
          </div>
          <div class="rounded-2xl bg-emerald-50 px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-wide text-emerald-500">Ativos</p>
            <p class="mt-1 text-xl font-bold text-emerald-700">{{ activeRulesCount }}</p>
          </div>
          <div class="rounded-2xl bg-sky-50 px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-wide text-sky-500">Padrão</p>
            <p class="mt-1 text-xl font-bold text-sky-700">{{ builtinCount }}</p>
          </div>
          <div class="rounded-2xl bg-violet-50 px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-wide text-violet-500">Custom</p>
            <p class="mt-1 text-xl font-bold text-violet-700">{{ customCount }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 lg:grid-cols-[340px_1fr]">
      <aside class="rounded-3xl bg-white p-4 shadow-sm ring-1 ring-slate-100 md:p-5">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-bold text-slate-900">Eventos</h2>
            <p class="text-sm text-slate-500">Ative, desative e selecione um evento para editar.</p>
          </div>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            @click="createNewRule"
          >
            + Novo
          </button>
        </div>

        <div class="mt-4 space-y-3">
          <button
            v-for="rule in rules"
            :key="rule.id"
            type="button"
            class="w-full rounded-2xl border p-4 text-left transition"
            :class="selectedRuleId === rule.id ? 'border-slate-900 bg-slate-50' : 'border-slate-200 bg-white hover:bg-slate-50'"
            @click="selectRule(rule)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-lg leading-none">{{ iconEmoji(rule.icon_tag) }}</span>
                  <p class="truncate text-sm font-semibold text-slate-900">{{ rule.display_name }}</p>
                </div>
                <p class="mt-1 truncate text-xs text-slate-500">{{ rule.event_key }}</p>
              </div>
              <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="rule.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'">
                {{ rule.enabled ? "Ativo" : "Inativo" }}
              </span>
            </div>
            <p class="mt-3 line-clamp-2 text-xs leading-5 text-slate-500">{{ rule.description || "Sem descrição." }}</p>
          </button>
        </div>
      </aside>

      <div class="space-y-6">
        <section class="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-100 md:p-6">
          <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <h2 class="text-lg font-bold text-slate-900">{{ formTitle }}</h2>
              <p class="text-sm text-slate-500">Use variáveis prontas para montar o texto e testar antes de salvar.</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                :disabled="!selectedRule || testing"
                @click="testSelectedRule"
              >
                {{ testing ? "Testando..." : "Testar" }}
              </button>
              <button
                type="button"
                class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
                :disabled="saving"
                @click="saveRule"
              >
                {{ saving ? "Salvando..." : "Salvar" }}
              </button>
            </div>
          </div>

          <div class="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
            <div class="space-y-4">
              <div class="grid gap-4 md:grid-cols-2">
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Evento</span>
                  <input
                    v-model="form.event_key"
                    :disabled="isBuiltinSelected"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-900 disabled:bg-slate-50"
                    placeholder="subscription_created"
                  />
                </label>
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Nome</span>
                  <input
                    v-model="form.display_name"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-900"
                    placeholder="Nova assinatura"
                  />
                </label>
              </div>

              <label class="block space-y-2">
                <span class="text-sm font-semibold text-slate-700">Descrição</span>
                <textarea
                  v-model="form.description"
                  rows="3"
                  class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-900"
                  placeholder="Explique quando este webhook é disparado"
                />
              </label>

              <div class="grid gap-4 md:grid-cols-2">
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Título</span>
                  <input
                    v-model="form.title_template"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-mono outline-none transition focus:border-slate-900"
                    placeholder="Assinatura criada - {{plan_name}}"
                  />
                </label>
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Corpo</span>
                  <input
                    v-model="form.body_template"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-mono outline-none transition focus:border-slate-900"
                    placeholder="{{amount}} | {{user_name}} | {{payment_method}}"
                  />
                </label>
              </div>

              <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Topic</span>
                  <input
                    v-model="form.topic"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-900"
                    placeholder="roteiro_online_assinaturas"
                  />
                </label>
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Prioridade</span>
                  <select
                    v-model.number="form.priority"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-900"
                  >
                    <option v-for="n in [1,2,3,4,5]" :key="n" :value="n">{{ n }}</option>
                  </select>
                </label>
                <label class="space-y-2">
                  <span class="text-sm font-semibold text-slate-700">Ordem</span>
                  <input
                    v-model.number="form.sort_order"
                    type="number"
                    class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-900"
                  />
                </label>
                <label class="flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3">
                  <input v-model="form.enabled" type="checkbox" class="h-4 w-4" />
                  <span class="text-sm font-semibold text-slate-700">Ativo</span>
                </label>
              </div>

              <div>
                <div class="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <h3 class="text-sm font-bold text-slate-900">Campos disponíveis</h3>
                    <p class="text-xs text-slate-500">Clique para copiar a variável.</p>
                  </div>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="field in meta?.available_fields || defaultAvailableFields"
                    :key="field"
                    type="button"
                    class="rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                    @click="copyField(field)"
                  >
                    {{ tokenForField(field) }}
                  </button>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div class="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <h3 class="text-sm font-bold text-slate-900">Ícone permitido</h3>
                    <p class="text-xs text-slate-500">A tag precisa existir no ntfy para virar emoji.</p>
                  </div>
                  <div class="flex items-center gap-2 rounded-full bg-white px-3 py-2 text-sm font-semibold text-slate-700">
                    <span>{{ iconEmoji(form.icon_tag) }}</span>
                    <span>{{ form.icon_tag || "sem ícone" }}</span>
                  </div>
                </div>
                <div class="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
                  <button
                    v-for="icon in meta?.icons || defaultIcons"
                    :key="icon.tag"
                    type="button"
                    class="rounded-2xl border p-3 text-left transition"
                    :class="form.icon_tag === icon.tag ? 'border-slate-900 bg-white' : 'border-slate-200 bg-white hover:bg-slate-50'"
                    @click="form.icon_tag = icon.tag"
                  >
                    <div class="text-lg">{{ icon.emoji }}</div>
                    <div class="mt-2 text-sm font-semibold text-slate-900">{{ icon.label }}</div>
                    <div class="text-xs text-slate-500">{{ icon.tag }}</div>
                  </button>
                </div>
              </div>

              <div class="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <h3 class="text-sm font-bold text-slate-900">Pré-visualização</h3>
                <div class="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div class="flex items-start gap-3">
                    <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-xl">
                      {{ iconEmoji(form.icon_tag) }}
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-sm font-bold text-slate-900">{{ previewTitle }}</p>
                      <p class="mt-2 whitespace-pre-line text-sm leading-6 text-slate-600">{{ previewBody }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="selectedRule && !selectedRule.is_builtin" class="rounded-3xl border border-slate-200 bg-white p-4">
                <button
                  type="button"
                  class="rounded-full border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                  :disabled="deleting"
                  @click="removeRule"
                >
                  {{ deleting ? "Excluindo..." : "Excluir custom" }}
                </button>
                <p class="mt-2 text-xs text-slate-500">Regras padrão não podem ser excluídas.</p>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-100 md:p-6">
          <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <h2 class="text-lg font-bold text-slate-900">Regras customizadas</h2>
              <p class="text-sm text-slate-500">Você pode adicionar webhooks novos sem mexer no código.</p>
            </div>
            <p class="text-sm text-slate-500">{{ customCount }} regras criadas</p>
          </div>
          <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="rule in customRules"
              :key="rule.id"
              class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-sm font-bold text-slate-900">{{ rule.display_name }}</p>
                  <p class="text-xs text-slate-500">{{ rule.event_key }}</p>
                </div>
                <span class="text-lg">{{ iconEmoji(rule.icon_tag) }}</span>
              </div>
              <p class="mt-3 line-clamp-2 text-xs text-slate-500">{{ rule.description || "Sem descrição." }}</p>
            </article>
            <div v-if="!customRules.length" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
              Nenhuma regra customizada ainda.
            </div>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";

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
const builtinCount = computed(() => rules.value.filter(rule => rule.is_builtin).length);
const customCount = computed(() => rules.value.filter(rule => !rule.is_builtin).length);
const customRules = computed(() => rules.value.filter(rule => !rule.is_builtin));

const formTitle = computed(() => (form.id ? `Editando: ${form.display_name || form.event_key || "regra"}` : "Nova regra"));

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
