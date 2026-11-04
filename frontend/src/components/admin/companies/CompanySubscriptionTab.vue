<template>
  <div class="space-y-4">
    <section v-if="!company.owner_id" class="am-card">
      <p class="am-muted text-sm">Empresa sem dono: as ações de assinatura não estão disponíveis.</p>
    </section>

    <template v-else>
      <section class="am-card">
        <div class="am-card-head">
          <div>
            <div class="am-card-title">Assinatura atual</div>
            <div class="am-card-sub">Como a cobrança está hoje no Roteiro Online.</div>
          </div>
        </div>
        <dl class="cs-facts">
          <div><dt>Plano</dt><dd>{{ planLabel(company.plan) }}</dd></div>
          <div><dt>Situação da cobrança</dt><dd>{{ subscriptionStatusLabel(company) }}</dd></div>
          <div>
            <dt>Cobrança</dt>
            <dd>{{ gatewayLabel(billingProvider(company)) }}<span v-if="methodLabel && billingProvider(company)" class="am-muted"> · {{ methodLabel }}</span></dd>
          </div>
          <div>
            <dt>Valor</dt>
            <dd>{{ isCombo(company) ? "Pago na Viaje On (fora do MRR)" : company.mrr_amount ? `${formatMoney(chargeAmount)} ${cycleLabel}` : "—" }}</dd>
          </div>
          <div><dt>MRR</dt><dd>{{ company.mrr_amount ? `${formatMoney(company.mrr_amount)}/mês` : "—" }}</dd></div>
          <div><dt>{{ accessLabel }}</dt><dd>{{ formatDate(company.access_until) }}<span v-if="accessLeft" class="am-muted"> · {{ accessLeft }}</span></dd></div>
          <div><dt>ID na cobrança</dt><dd class="am-mono select-text">{{ providerId }}</dd></div>
          <div v-if="company.subscription_cakto_order_id"><dt>Pedido Cakto</dt><dd class="am-mono select-text">{{ company.subscription_cakto_order_id }}</dd></div>
          <div><dt>Falhas de cobrança</dt><dd :class="company.failed_attempts ? 'text-status-danger-foreground' : ''">{{ company.failed_attempts || 0 }}</dd></div>
          <div v-if="company.trial_plan"><dt>Teste</dt><dd>{{ planLabel(company.trial_plan) }} até {{ formatDate(company.trial_ends_at) }}</dd></div>
        </dl>
      </section>

      <section class="am-card">
        <div class="am-card-head">
          <div>
            <div class="am-card-title">Ajustes no Roteiro Online</div>
            <div class="am-card-sub">
              Plano, situação e validade mudam só no Roteiro Online: não geram, não alteram e não cancelam cobrança na Asaas nem na Cakto.
              <template v-if="isFree"> Sem validade definida, o acesso gratuito vale {{ freeDays }} dias a partir do cadastro.</template>
            </div>
          </div>
        </div>
        <div class="cs-actions">
          <div class="am-field">
            <label for="cs-plan">Plano</label>
            <div class="flex gap-2">
              <select id="cs-plan" v-model="form.plan" class="am-input">
                <option v-for="option in planOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <button type="button" class="am-btn am-btn-sm !h-[38px]" :disabled="form.plan === currentPlan" @click="ask('plan')">Alterar</button>
            </div>
          </div>
          <div class="am-field">
            <label for="cs-status">Situação da cobrança</label>
            <div class="flex gap-2">
              <select id="cs-status" v-model="form.status" class="am-input">
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <button type="button" class="am-btn am-btn-sm !h-[38px]" :disabled="form.status === currentStatus" @click="ask('status')">Alterar</button>
            </div>
          </div>
          <div class="am-field">
            <label for="cs-valid">{{ isFree ? "Prazo do acesso gratuito" : "Validade" }}</label>
            <div class="flex gap-2">
              <input id="cs-valid" v-model="form.validUntil" type="date" class="am-input" />
              <button type="button" class="am-btn am-btn-sm !h-[38px]" :disabled="!form.validUntil || form.validUntil === currentValidity" @click="ask('validity')">
                Salvar
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="am-card">
        <div class="am-card-head">
          <div>
            <div class="am-card-title">Ações na cobrança</div>
            <div class="am-card-sub">Estas mexem na Asaas ou na Cakto. Tudo fica registrado na aba Logs.</div>
          </div>
        </div>
        <div class="flex flex-wrap gap-2">
          <button v-if="!company.owner_is_superuser" type="button" class="am-btn am-btn-sm" :disabled="trialActive" @click="ask('trial')">
            <AmIcon name="history" />{{ trialActive ? "Teste já ativo" : `Liberar 7 dias do plano ${planLabels.infinity}` }}
          </button>
          <button v-if="canSchedule" type="button" class="am-btn am-btn-sm" @click="ask('schedule')"><AmIcon name="cal" />Cancelar no fim da validade</button>
          <button v-if="isScheduled" type="button" class="am-btn am-btn-sm" @click="ask('unschedule')"><AmIcon name="undo" />Desfazer cancelamento programado</button>
          <button v-if="canCancelNow" type="button" class="am-btn am-btn-sm" @click="ask('cancel')"><AmIcon name="x" />Cancelar agora</button>
          <button v-if="canRefund" type="button" class="am-btn am-btn-sm" @click="ask('refund')"><AmIcon name="wallet" />Reembolsar</button>
          <span v-if="!hasActions" class="am-muted text-sm">Nenhuma ação disponível para a situação atual.</span>
        </div>
      </section>

      <section v-if="!company.owner_is_superuser" class="am-card cs-danger">
        <div class="am-card-head">
          <div>
            <div class="am-card-title">Zona de perigo</div>
            <div class="am-card-sub">Apaga a conta do dono, a empresa, as páginas e o histórico de origem. Não dá para desfazer.</div>
          </div>
          <button type="button" class="am-btn am-btn-sm am-btn-danger" @click="ask('delete')"><AmIcon name="trash" />Excluir empresa</button>
        </div>
      </section>
    </template>

    <AdminMasterConfirm
      :open="Boolean(pending)"
      :title="confirmCopy.title"
      :confirm-label="confirmCopy.button"
      :busy="busy"
      :busy-label="confirmCopy.busy"
      :error="actionError"
      :icon="confirmCopy.icon"
      :tone="confirmCopy.tone"
      :disabled="pending === 'delete' && deleteText.trim().toLowerCase() !== (company.slug || '').toLowerCase()"
      @close="closeConfirm"
      @confirm="runAction"
    >
      <p>{{ confirmCopy.text }}</p>
      <div v-if="pending === 'delete'" class="am-field mt-3">
        <label for="cs-delete">Para confirmar, digite <b class="am-mono">{{ company.slug }}</b></label>
        <input id="cs-delete" v-model="deleteText" type="text" class="am-input am-mono" autocomplete="off" />
      </div>
    </AdminMasterConfirm>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import api from "../../../services/api";
import type { Company } from "../../../services/companies";
import { planLabels } from "../../../utils/planLabels";
import { cycleMonths, cyclePeriod } from "../../../utils/billingCycle";
import AmIcon from "../master/AmIcon.vue";
import AdminMasterConfirm from "../master/AdminMasterConfirm.vue";
import { daysUntil, formatDate, formatMoney, gatewayLabel, planLabel } from "../master/format";
import { billingProvider, isCombo } from "./companyStatus";
import { planOptions, statusOptions, subscriptionStatusLabel } from "./companyLabels";

const props = defineProps<{ company: Company; freeDays: number }>();
const emit = defineEmits<{ (e: "changed", message: string): void; (e: "deleted", message: string): void }>();

const toDateInput = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("en-CA");
};

const form = reactive({ plan: "", status: "", validUntil: "" });
const currentPlan = computed(() => (props.company.plan || "").toLowerCase());
const currentStatus = computed(() => (props.company.subscription_status || "").toLowerCase());
const currentValidity = computed(() => toDateInput(props.company.valid_until));

watch(
  () => props.company,
  company => {
    form.plan = currentPlan.value;
    form.status = currentStatus.value;
    form.validUntil = toDateInput(company.valid_until || (company.status.startsWith("free") ? company.access_until : null));
  },
  { immediate: true }
);

const isFree = computed(() => ["free", "free_expired"].includes(props.company.status || ""));
const trialActive = computed(() => props.company.status === "trial");
const isScheduled = computed(() => currentStatus.value === "cancel_at_period_end");
const hasPaidProvider = computed(() => ["asaas", "cakto"].includes(billingProvider(props.company)));
const canSchedule = computed(() => hasPaidProvider.value && ["active", "past_due"].includes(currentStatus.value) && Boolean(props.company.valid_until));
const canCancelNow = computed(() => hasPaidProvider.value && ["active", "past_due", "cancel_at_period_end"].includes(currentStatus.value));
const canRefund = computed(
  () =>
    (props.company.subscription_provider || "").toLowerCase() === "cakto" &&
    Boolean(props.company.subscription_cakto_order_id) &&
    currentStatus.value === "active" &&
    !props.company.owner_is_superuser
);
const hasActions = computed(
  () => !props.company.owner_is_superuser || canSchedule.value || isScheduled.value || canCancelNow.value || canRefund.value
);

const methodLabel = computed(() => {
  const method = (props.company.payment_method || "").toLowerCase();
  return ({ card: "Cartão", credit_card: "Cartão", pix: "Pix", pix_automatic: "Pix automático", boleto: "Boleto" } as Record<string, string>)[method] || "";
});
// O MRR guarda o valor por mês: a cobrança é ele vezes os meses do ciclo.
const chargeAmount = computed(() => (props.company.mrr_amount || 0) * cycleMonths((props.company.billing_cycle || "").toLowerCase()));
const cycleLabel = computed(() => `por ${cyclePeriod((props.company.billing_cycle || "").toLowerCase())}`);
const accessLabel = computed(() => {
  const status = props.company.status;
  if (status === "trial" || status === "trial_ended") return "Fim do teste";
  if (status === "free" || status === "free_expired") return "Prazo do gratuito";
  if (status === "past_due") return "No ar até";
  return "Validade";
});
const accessLeft = computed(() => {
  const left = daysUntil(props.company.access_until);
  if (left === null) return "";
  if (left < 0) return `venceu há ${-left} ${left === -1 ? "dia" : "dias"}`;
  if (left === 0) return "vence hoje";
  return `faltam ${left} ${left === 1 ? "dia" : "dias"}`;
});
const providerId = computed(
  () =>
    props.company.subscription_asaas_subscription_id ||
    props.company.subscription_cakto_subscription_code ||
    props.company.subscription_cakto_order_id ||
    "—"
);

// ---------- Ações ----------
type Action = "plan" | "status" | "validity" | "trial" | "schedule" | "unschedule" | "cancel" | "refund" | "delete";
const pending = ref<Action | null>(null);
const busy = ref(false);
const actionError = ref("");
const deleteText = ref("");

const ask = (action: Action) => {
  pending.value = action;
  actionError.value = "";
  deleteText.value = "";
};
const closeConfirm = () => {
  if (busy.value) return;
  pending.value = null;
};

const optionLabel = (list: Array<{ value: string; label: string }>, value: string) => list.find(item => item.value === value)?.label || value;

const confirmCopy = computed(() => {
  const company = props.company;
  const name = company.name;
  const copies: Record<Action, { title: string; text: string; button: string; busy?: string; icon: string; tone: "danger" | "warning" | "info" }> = {
    plan: {
      title: "Alterar o plano?",
      text: `${name}: de ${planLabel(company.plan)} para ${optionLabel(planOptions, form.plan)}. Muda só no Roteiro Online, sem mexer na cobrança.`,
      button: "Alterar plano",
      icon: "tag",
      tone: "info"
    },
    status: {
      title: "Alterar a situação da cobrança?",
      text: `${name}: de ${subscriptionStatusLabel(company)} para ${optionLabel(statusOptions, form.status)}. Muda só no Roteiro Online, sem mexer na cobrança.`,
      button: "Alterar situação",
      icon: "card",
      tone: "info"
    },
    validity: {
      title: isFree.value ? "Alterar o prazo do acesso gratuito?" : "Alterar a validade?",
      text: `${name}: nova data ${formatDate(form.validUntil ? `${form.validUntil}T12:00:00` : null)}. A assinatura fica como ativa até essa data.`,
      button: "Salvar data",
      icon: "cal",
      tone: "info"
    },
    trial: {
      title: `Liberar 7 dias do plano ${planLabels.infinity}?`,
      text: `${name} recebe acesso total ao plano ${planLabels.infinity} por 7 dias. Os avisos de fim de teste aparecem no painel da empresa.`,
      button: "Liberar teste",
      icon: "history",
      tone: "info"
    },
    schedule: {
      title: "Cancelar no fim da validade?",
      text: `${name} continua com acesso até ${formatDate(company.valid_until)} e a cobrança não renova depois disso.`,
      button: "Programar cancelamento",
      icon: "cal",
      tone: "warning"
    },
    unschedule: {
      title: "Desfazer o cancelamento programado?",
      text: `A assinatura de ${name} volta a renovar normalmente.`,
      button: "Desfazer cancelamento",
      icon: "undo",
      tone: "info"
    },
    cancel: {
      title: "Cancelar a assinatura agora?",
      text: `A cobrança de ${name} é cancelada na ${gatewayLabel(company.subscription_provider)} agora e o acesso pago termina.`,
      button: "Cancelar agora",
      busy: "Cancelando...",
      icon: "x",
      tone: "danger"
    },
    refund: {
      title: "Reembolsar e bloquear?",
      text: `O reembolso de ${name} é pedido na Cakto, a assinatura é cancelada, todas as páginas saem do ar e o acesso é bloqueado. Não dá para desfazer.`,
      button: "Confirmar reembolso",
      busy: "Processando...",
      icon: "wallet",
      tone: "danger"
    },
    delete: {
      title: `Excluir ${name}?`,
      text: "Apaga a conta do dono, a empresa, as páginas e o histórico de origem. Não dá para desfazer.",
      button: "Excluir de vez",
      busy: "Excluindo...",
      icon: "trash",
      tone: "danger"
    }
  };
  const copy = copies[pending.value || "plan"];
  return { ...copy, busy: copy.busy || "Salvando..." };
});

const runAction = async () => {
  const company = props.company;
  const action = pending.value;
  if (!company.owner_id || !action) return;
  const userId = company.owner_id;
  busy.value = true;
  actionError.value = "";
  try {
    let message = "";
    if (action === "plan") {
      await api.patch(`/admin/users/${userId}/subscription`, { plan: form.plan });
      message = "Plano atualizado.";
    } else if (action === "status") {
      await api.patch(`/admin/users/${userId}/subscription`, { status: form.status });
      message = "Situação da cobrança atualizada.";
    } else if (action === "validity") {
      await api.patch(`/admin/users/${userId}/subscription`, { valid_until: form.validUntil });
      message = "Data atualizada.";
    } else if (action === "trial") {
      await api.post(`/admin/users/${userId}/grant-trial`, { plan: "infinity", days: 7 });
      message = "Teste de 7 dias liberado.";
    } else if (action === "schedule") {
      await api.post(`/admin/users/${userId}/asaas-cancel-at-period-end`, {});
      message = "Cancelamento programado para o fim da validade.";
    } else if (action === "unschedule") {
      await api.post(`/admin/users/${userId}/asaas-cancel-scheduled-cancellation`, {});
      message = "Cancelamento programado desfeito.";
    } else if (action === "cancel") {
      await api.post(`/admin/users/${userId}/asaas-cancel-immediate`, {});
      message = "Assinatura cancelada.";
    } else if (action === "refund") {
      await api.post(`/admin/users/${userId}/refund`, {});
      message = "Reembolso pedido e acesso bloqueado.";
    } else if (action === "delete") {
      await api.delete(`/admin/users/${userId}`);
      message = `${company.name} foi excluída.`;
    }
    busy.value = false;
    pending.value = null;
    if (action === "delete") emit("deleted", message);
    else emit("changed", message);
  } catch (error: any) {
    actionError.value = error?.response?.data?.detail || "Não foi possível concluir agora. Tente de novo.";
    busy.value = false;
  }
};
</script>

<style scoped>
.cs-facts {
  display: grid;
  gap: 14px 18px;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
}
.cs-facts dt {
  font-size: 12px;
  color: var(--muted-foreground);
}
.cs-facts dd {
  margin-top: 1px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--foreground);
  overflow-wrap: anywhere;
}
.cs-actions {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}
.cs-danger {
  border-color: color-mix(in srgb, var(--status-danger-foreground) 30%, var(--border));
}
</style>
