<template>
  <AdminMasterDrawer
    :open="Boolean(company)"
    :title="company?.name || ''"
    :subtitle="company ? `/${company.slug} · cadastrada em ${formatDate(company.created_at)}` : ''"
    icon="building"
    :tone="company ? statusTone(company.status).replace('am-tone-', '') : 'neutral'"
    :width="720"
    @close="$emit('close')"
  >
    <template v-if="company">
      <div class="cd-status">
        <span class="am-badge am-dot" :class="statusTone(company.status)">{{ company.status_label }}</span>
        <span class="text-[13px]">{{ statusDetail(company) }}</span>
        <a v-if="company.online" :href="`/${company.slug}`" target="_blank" rel="noopener noreferrer" class="am-btn am-btn-sm ml-auto">
          <AmIcon name="eye" />Ver página pública
        </a>
      </div>

      <!-- DONO -->
      <section class="cd-section">
        <p class="am-eyebrow">Dono da conta</p>
        <div v-if="company.owner_id" class="mt-2 flex flex-wrap items-center gap-3">
          <span class="am-avatar">{{ initials(company.owner_name) }}</span>
          <div class="min-w-0 flex-1 select-text">
            <b class="block font-semibold">{{ company.owner_name }}</b>
            <span class="am-muted block text-xs">{{ company.owner_email }}</span>
            <span class="am-muted block text-xs">{{ company.owner_whatsapp || "Sem WhatsApp" }}</span>
          </div>
          <span v-if="company.owner_is_superuser" class="am-badge am-tone-violet">Superusuário</span>
          <a v-if="whatsappLink" :href="whatsappLink" target="_blank" rel="noopener noreferrer" class="am-btn am-btn-sm"><AmIcon name="wa" />WhatsApp</a>
          <RouterLink :to="{ path: '/admin/administracao/usuarios', query: { busca: company.owner_email || '' } }" class="am-btn am-btn-sm">
            <AmIcon name="users" />Ver em Usuários
          </RouterLink>
        </div>
        <p v-else class="am-muted mt-2 text-sm">Empresa sem dono: as ações de assinatura não estão disponíveis.</p>
      </section>

      <!-- ASSINATURA -->
      <section v-if="company.owner_id" class="cd-section">
        <p class="am-eyebrow">Assinatura</p>
        <dl class="cd-facts">
          <div><dt>Plano</dt><dd>{{ planLabel(company.plan) }}</dd></div>
          <div><dt>Situação da cobrança</dt><dd>{{ subscriptionStatusLabel(company) }}</dd></div>
          <div><dt>Cobrança</dt><dd>{{ gatewayLabel(billingProvider(company)) }}<span v-if="methodLabel && billingProvider(company)" class="am-muted"> · {{ methodLabel }}</span></dd></div>
          <div><dt>Valor</dt><dd>{{ company.mrr_amount ? `${formatMoney(chargeAmount)} ${cycleLabel}` : "—" }}</dd></div>
          <div><dt>{{ accessLabel }}</dt><dd>{{ formatDate(company.access_until) }}<span v-if="accessLeft" class="am-muted"> · {{ accessLeft }}</span></dd></div>
          <div><dt>ID na cobrança</dt><dd class="am-mono select-text">{{ providerId }}</dd></div>
          <div v-if="company.failed_attempts"><dt>Falhas de cobrança</dt><dd class="text-status-danger-foreground">{{ company.failed_attempts }}</dd></div>
          <div v-if="company.trial_plan"><dt>Teste</dt><dd>{{ planLabel(company.trial_plan) }} até {{ formatDate(company.trial_ends_at) }}</dd></div>
        </dl>

        <div class="cd-actions">
          <div class="am-field">
            <label for="cd-plan">Plano</label>
            <div class="flex gap-2">
              <select id="cd-plan" v-model="form.plan" class="am-input">
                <option v-for="option in planOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <button type="button" class="am-btn am-btn-sm !h-[38px]" :disabled="form.plan === currentPlan" @click="ask('plan')">Alterar</button>
            </div>
          </div>
          <div class="am-field">
            <label for="cd-status">Situação da cobrança</label>
            <div class="flex gap-2">
              <select id="cd-status" v-model="form.status" class="am-input">
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <button type="button" class="am-btn am-btn-sm !h-[38px]" :disabled="form.status === currentStatus" @click="ask('status')">Alterar</button>
            </div>
          </div>
          <div class="am-field">
            <label for="cd-valid">{{ isFree ? "Prazo do acesso gratuito" : "Validade" }}</label>
            <div class="flex gap-2">
              <input id="cd-valid" v-model="form.validUntil" type="date" class="am-input" />
              <button type="button" class="am-btn am-btn-sm !h-[38px]" :disabled="!form.validUntil || form.validUntil === currentValidity" @click="ask('validity')">Salvar</button>
            </div>
          </div>
        </div>
        <p class="am-card-sub">
          Plano, situação e validade mudam só no Roteiro Online: não geram, não alteram e não cancelam cobrança na Asaas nem na Cakto.
          <template v-if="isFree"> Sem validade definida, o acesso gratuito vale {{ freeDays }} dias a partir do cadastro.</template>
        </p>

        <div class="mt-3 flex flex-wrap gap-2">
          <button v-if="!company.owner_is_superuser" type="button" class="am-btn am-btn-sm" :disabled="trialActive" @click="ask('trial')">
            <AmIcon name="history" />{{ trialActive ? "Teste já ativo" : `Liberar 7 dias do plano ${planLabels.infinity}` }}
          </button>
          <button v-if="canSchedule" type="button" class="am-btn am-btn-sm" @click="ask('schedule')"><AmIcon name="cal" />Cancelar no fim da validade</button>
          <button v-if="isScheduled" type="button" class="am-btn am-btn-sm" @click="ask('unschedule')"><AmIcon name="undo" />Desfazer cancelamento programado</button>
          <button v-if="canCancelNow" type="button" class="am-btn am-btn-sm" @click="ask('cancel')"><AmIcon name="x" />Cancelar agora</button>
          <button v-if="canRefund" type="button" class="am-btn am-btn-sm" @click="ask('refund')"><AmIcon name="wallet" />Reembolsar</button>
        </div>
      </section>

      <!-- EQUIPE -->
      <section class="cd-section">
        <p class="am-eyebrow">Equipe <span v-if="detail">· {{ detail.members.length }}</span></p>
        <div v-if="loadingDetail" class="am-empty !py-6"><div class="am-spinner"></div></div>
        <div v-else-if="detail?.members.length" class="cd-box am-list mt-2">
          <div v-for="member in detail.members" :key="member.user_id" class="flex flex-wrap items-center gap-3 px-3 py-2.5">
            <span class="am-avatar">{{ initials(member.name) }}</span>
            <div class="min-w-0 flex-1">
              <b class="block truncate text-[13px] font-semibold">{{ member.name }}</b>
              <small class="am-muted block truncate text-xs">{{ member.email }}</small>
            </div>
            <span class="am-badge" :class="member.is_owner ? 'am-tone-success' : 'am-tone-neutral'">{{ member.is_owner ? "Dono" : roleLabel(member.role) }}</span>
            <span class="am-muted w-[110px] text-right text-xs">{{ member.last_access_at ? relativeDay(member.last_access_at) : "Nunca entrou" }}</span>
          </div>
        </div>
        <p v-else-if="detail" class="am-muted mt-2 text-sm">Ninguém na equipe.</p>
      </section>

      <!-- PÁGINAS -->
      <section class="cd-section">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <p class="am-eyebrow">Páginas <span v-if="detail">· {{ publishedPages.length }} publicadas · {{ draftPages.length }} rascunhos</span></p>
          <button type="button" class="am-btn am-btn-sm" :disabled="!agencyStore.currentAgencyId" @click="openLinkPage">
            <AmIcon name="link" />Vincular uma página minha
          </button>
        </div>
        <div v-if="pageNotice" class="am-notice mt-2" :class="`am-tone-${pageNotice.tone}`">
          <AmIcon :name="pageNotice.tone === 'success' ? 'check' : 'alert'" /><span>{{ pageNotice.text }}</span>
        </div>
        <div v-if="detail?.pages.length" class="cd-box mt-2 overflow-x-auto">
          <table class="am-table">
            <thead>
              <tr>
                <th>Página</th>
                <th class="am-right">Visitas</th>
                <th class="am-right">Cliques</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="page in detail.pages" :key="page.id">
                <td>
                  <b class="font-semibold">{{ page.title }}</b>
                  <span class="am-badge ml-1.5" :class="page.status === 'published' ? 'am-tone-success' : 'am-tone-neutral'">
                    {{ page.status === "published" ? "Publicada" : "Rascunho" }}
                  </span>
                  <div class="am-mono am-muted">/{{ page.slug }}</div>
                </td>
                <td class="am-right am-num">{{ formatInt(page.visits) }}</td>
                <td class="am-right am-num">{{ formatInt(page.clicks) }}</td>
                <td class="am-right whitespace-nowrap">
                  <a v-if="page.status === 'published'" :href="`/${company.slug}/${page.slug}`" target="_blank" rel="noopener noreferrer" class="am-btn am-btn-sm">Ver</a>
                  <RouterLink v-else :to="{ name: 'page-edit', params: { id: page.id } }" class="am-btn am-btn-sm">Editar</RouterLink>
                  <button
                    type="button"
                    class="am-btn am-btn-sm ml-1"
                    :disabled="copyingPageId === page.id || !agencyStore.currentAgencyId"
                    @click="copyToMe(page)"
                  >
                    {{ copyingPageId === page.id ? "Copiando..." : "Copiar para mim" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else-if="detail" class="am-muted mt-2 text-sm">Nenhuma página criada.</p>
      </section>

      <!-- UTMs -->
      <section class="cd-section">
        <p class="am-eyebrow">Origem do cadastro</p>
        <div v-if="detail?.tracking.length" class="mt-2 space-y-2">
          <div v-for="entry in detail.tracking" :key="entry.id" class="cd-box p-3">
            <div class="flex flex-wrap gap-1.5">
              <span v-for="chip in utmChips(entry)" :key="chip.label" class="am-badge am-tone-neutral">
                <span class="am-muted">{{ chip.label }}:</span>{{ chip.value }}
              </span>
            </div>
            <p class="am-muted mt-2 text-[11px]">Capturado em {{ formatDateTime(entry.created_at) }}</p>
          </div>
        </div>
        <p v-else-if="detail" class="am-muted mt-2 text-sm">Nenhuma UTM registrada.</p>
      </section>

      <section v-if="company.owner_id && !company.owner_is_superuser" class="cd-section">
        <p class="am-eyebrow">Zona de perigo</p>
        <div class="mt-2 flex flex-wrap items-center justify-between gap-3">
          <p class="am-muted text-[13px]">Apaga a conta do dono, a empresa, as páginas e o histórico de origem. Não dá para desfazer.</p>
          <button type="button" class="am-btn am-btn-sm am-btn-danger" @click="ask('delete')"><AmIcon name="trash" />Excluir empresa</button>
        </div>
      </section>
    </template>
  </AdminMasterDrawer>

  <AdminMasterConfirm
    :open="Boolean(pending)"
    :title="confirmCopy.title"
    :confirm-label="confirmCopy.button"
    :busy="busy"
    :busy-label="confirmCopy.busy"
    :error="actionError"
    :icon="confirmCopy.icon"
    :tone="confirmCopy.tone"
    :disabled="pending === 'delete' && deleteText.trim().toLowerCase() !== (company?.slug || '').toLowerCase()"
    @close="closeConfirm"
    @confirm="runAction"
  >
    <p>{{ confirmCopy.text }}</p>
    <div v-if="pending === 'delete'" class="am-field mt-3">
      <label for="cd-delete">Para confirmar, digite <b class="am-mono">{{ company?.slug }}</b></label>
      <input id="cd-delete" v-model="deleteText" type="text" class="am-input am-mono" autocomplete="off" />
    </div>
  </AdminMasterConfirm>

  <AdminMasterConfirm
    :open="linkDialog.open"
    :title="`Vincular página a ${company?.name || ''}`"
    confirm-label="Copiar para a empresa"
    busy-label="Copiando..."
    :busy="linkDialog.saving"
    :error="linkDialog.error"
    icon="link"
    tone="info"
    :disabled="!linkDialog.pageId || !linkDialog.title.trim()"
    @close="linkDialog.open = false"
    @confirm="confirmLinkPage"
  >
    <p>Uma cópia de uma página da sua agência atual vai para esta empresa, publicada.</p>
    <div v-if="linkDialog.loading" class="am-empty !py-4"><div class="am-spinner"></div></div>
    <template v-else-if="linkDialog.pages.length">
      <div class="am-field mt-3">
        <label for="cd-link-page">Página de origem</label>
        <select id="cd-link-page" v-model="linkDialog.pageId" class="am-input">
          <option v-for="page in linkDialog.pages" :key="page.id" :value="page.id">
            {{ page.title }} · {{ page.status === "published" ? "Publicada" : "Rascunho" }}
          </option>
        </select>
      </div>
      <div class="am-field mt-3">
        <label for="cd-link-title">Nome do roteiro na empresa</label>
        <input id="cd-link-title" v-model="linkDialog.title" type="text" class="am-input" />
      </div>
    </template>
    <p v-else class="mt-3">Sua agência atual não tem páginas para copiar.</p>
  </AdminMasterConfirm>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import api from "../../../services/api";
import { getCompanyDetail, type Company, type CompanyDetail, type CompanyPage, type CompanyTracking } from "../../../services/companies";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { planLabels } from "../../../utils/planLabels";
import AmIcon from "../master/AmIcon.vue";
import AdminMasterDrawer from "../master/AdminMasterDrawer.vue";
import AdminMasterConfirm from "../master/AdminMasterConfirm.vue";
import {
  daysUntil,
  formatDate,
  formatDateTime,
  formatInt,
  formatMoney,
  gatewayLabel,
  initials,
  planLabel,
  relativeDay,
  statusTone
} from "../master/format";
import { billingProvider, statusDetail } from "./companyStatus";

const props = defineProps<{ company: Company | null; freeDays: number }>();
const emit = defineEmits<{ (e: "close"): void; (e: "changed", message: string): void }>();

const agencyStore = useAgencyStore();

const planOptions = [
  { value: "free", label: "Começo (gratuito)" },
  { value: "essencial", label: "Profissional" },
  { value: "growth", label: "Agência" },
  { value: "infinity", label: "Escala" },
  { value: "trial", label: "Trial" },
  { value: "teste", label: "Teste (interno)" }
];
const statusOptions = [
  { value: "active", label: "Ativa" },
  { value: "pending", label: "Pendente" },
  { value: "failed", label: "Falha" },
  { value: "past_due", label: "Em atraso" },
  { value: "cancel_at_period_end", label: "Cancelar no fim da validade" },
  { value: "cancelled", label: "Cancelada" },
  { value: "cancelled_admin", label: "Cancelada pelo admin" },
  { value: "inactive", label: "Inativa" }
];
const roleLabels: Record<string, string> = { owner: "Dono", admin: "Administrador", editor: "Editor", viewer: "Leitura", member: "Membro" };
const roleLabel = (role: string) => roleLabels[role] || role || "Membro";

const toDateInput = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("en-CA");
};

const detail = ref<CompanyDetail | null>(null);
const loadingDetail = ref(false);
const form = reactive({ plan: "", status: "", validUntil: "" });
const currentPlan = computed(() => (props.company?.plan || "").toLowerCase());
const currentStatus = computed(() => (props.company?.subscription_status || "").toLowerCase());
const currentValidity = computed(() => toDateInput(props.company?.valid_until));

const loadDetail = async (id: number) => {
  loadingDetail.value = true;
  detail.value = null;
  try {
    const data = await getCompanyDetail(id);
    if (props.company?.id === id) detail.value = data;
  } catch (error: any) {
    if (props.company?.id === id) detail.value = { id, slug: props.company.slug, members: [], pages: [], tracking: [] };
  } finally {
    loadingDetail.value = false;
  }
};

watch(
  () => props.company,
  (company, previous) => {
    if (!company) return;
    form.plan = currentPlan.value;
    form.status = currentStatus.value;
    form.validUntil = toDateInput(company.valid_until || (company.status.startsWith("free") ? company.access_until : null));
    if (company.id !== previous?.id) {
      pageNotice.value = null;
      void loadDetail(company.id);
    }
  },
  { immediate: true }
);

const publishedPages = computed(() => detail.value?.pages.filter(page => page.status === "published") || []);
const draftPages = computed(() => detail.value?.pages.filter(page => page.status !== "published") || []);

const isFree = computed(() => ["free", "free_expired"].includes(props.company?.status || ""));
const trialActive = computed(() => props.company?.status === "trial");
const isScheduled = computed(() => currentStatus.value === "cancel_at_period_end");
const hasPaidProvider = computed(() => Boolean(props.company && ["asaas", "cakto"].includes(billingProvider(props.company))));
const canSchedule = computed(
  () => hasPaidProvider.value && ["active", "past_due"].includes(currentStatus.value) && Boolean(props.company?.valid_until)
);
const canCancelNow = computed(() => hasPaidProvider.value && ["active", "past_due", "cancel_at_period_end"].includes(currentStatus.value));
const canRefund = computed(
  () =>
    (props.company?.subscription_provider || "").toLowerCase() === "cakto" &&
    Boolean(props.company?.subscription_cakto_order_id) &&
    currentStatus.value === "active" &&
    !props.company?.owner_is_superuser
);

const subscriptionStatusLabel = (company: Company) => {
  const raw = (company.subscription_status || "").toLowerCase();
  // Antes do "cancelled_admin", o cancelamento imediato da Asaas ficava como "past_due" sem id de assinatura.
  if (raw === "past_due" && company.subscription_provider === "asaas" && !company.subscription_asaas_subscription_id) return "Cancelada";
  return statusOptions.find(option => option.value === raw)?.label || company.subscription_status || "Sem assinatura";
};
const methodLabel = computed(() => {
  const method = (props.company?.payment_method || "").toLowerCase();
  return ({ card: "Cartão", credit_card: "Cartão", pix: "Pix", pix_automatic: "Pix automático", boleto: "Boleto" } as Record<string, string>)[method] || "";
});
const isAnnual = computed(() => (props.company?.billing_cycle || "").toLowerCase() === "annual");
const chargeAmount = computed(() => (props.company?.mrr_amount || 0) * (isAnnual.value ? 12 : 1));
const cycleLabel = computed(() => (isAnnual.value ? "por ano" : "por mês"));
const accessLabel = computed(() => {
  const status = props.company?.status;
  if (status === "trial" || status === "trial_ended") return "Fim do teste";
  if (status === "free" || status === "free_expired") return "Prazo do gratuito";
  return "Validade";
});
const accessLeft = computed(() => {
  const left = daysUntil(props.company?.access_until);
  if (left === null) return "";
  if (left < 0) return `venceu há ${-left} ${left === -1 ? "dia" : "dias"}`;
  if (left === 0) return "vence hoje";
  return `faltam ${left} ${left === 1 ? "dia" : "dias"}`;
});
const providerId = computed(() => {
  const company = props.company;
  if (!company) return "—";
  return (
    company.subscription_asaas_subscription_id ||
    company.subscription_cakto_subscription_code ||
    company.subscription_cakto_order_id ||
    "—"
  );
});
const whatsappLink = computed(() => {
  const digits = String(props.company?.owner_whatsapp || "").replace(/\D/g, "");
  if (!digits) return "";
  return `https://wa.me/${digits.length <= 11 ? `55${digits}` : digits}`;
});

const utmFields: Array<{ key: keyof CompanyTracking; label: string }> = [
  { key: "utm_source", label: "Fonte" },
  { key: "utm_medium", label: "Mídia" },
  { key: "utm_campaign", label: "Campanha" },
  { key: "utm_term", label: "Termo" },
  { key: "utm_content", label: "Conteúdo" },
  { key: "referrer", label: "Veio de" }
];
const utmChips = (entry: CompanyTracking) =>
  utmFields.filter(field => entry[field.key]).map(field => ({ label: field.label, value: String(entry[field.key]) }));

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

const confirmCopy = computed(() => {
  const company = props.company;
  const name = company?.name || "";
  const optionLabel = (list: Array<{ value: string; label: string }>, value: string) => list.find(item => item.value === value)?.label || value;
  const copies: Record<Action, { title: string; text: string; button: string; busy?: string; icon: string; tone: "danger" | "warning" | "info" }> = {
    plan: {
      title: "Alterar o plano?",
      text: `${name}: de ${planLabel(company?.plan)} para ${optionLabel(planOptions, form.plan)}. Muda só no Roteiro Online, sem mexer na cobrança.`,
      button: "Alterar plano",
      icon: "tag",
      tone: "info"
    },
    status: {
      title: "Alterar a situação da cobrança?",
      text: `${name}: de ${company ? subscriptionStatusLabel(company) : ""} para ${optionLabel(statusOptions, form.status)}. Muda só no Roteiro Online, sem mexer na cobrança.`,
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
      text: `${name} continua com acesso até ${formatDate(company?.valid_until)} e a cobrança não renova depois disso.`,
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
      text: `A cobrança de ${name} é cancelada na ${gatewayLabel(company?.subscription_provider)} agora e o acesso pago termina.`,
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
  if (!company?.owner_id || !action) return;
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
    emit("changed", message);
    if (action === "delete") emit("close");
  } catch (error: any) {
    actionError.value = error?.response?.data?.detail || "Não foi possível concluir agora. Tente de novo.";
    busy.value = false;
  }
};

// ---------- Páginas ----------
const copyingPageId = ref<number | null>(null);
const pageNotice = ref<{ tone: "success" | "danger"; text: string } | null>(null);
const copyToMe = async (page: CompanyPage) => {
  if (!agencyStore.currentAgencyId || !props.company) return;
  copyingPageId.value = page.id;
  try {
    await api.post(`/admin/pages/${page.id}/clone`, {
      target_agency_id: agencyStore.currentAgencyId,
      title: `${page.title} - ${props.company.name}`
    });
    pageNotice.value = { tone: "success", text: `“${page.title}” foi copiada para a sua agência atual.` };
  } catch (error: any) {
    pageNotice.value = { tone: "danger", text: error?.response?.data?.detail || "Não foi possível copiar esta página." };
  } finally {
    copyingPageId.value = null;
  }
};

const linkDialog = reactive({
  open: false,
  loading: false,
  saving: false,
  error: "",
  pages: [] as Array<{ id: number; title: string; status: string }>,
  pageId: null as number | null,
  title: ""
});
watch(
  () => linkDialog.pageId,
  id => {
    linkDialog.title = linkDialog.pages.find(page => page.id === id)?.title || "";
  }
);
const openLinkPage = async () => {
  if (!agencyStore.currentAgencyId) return;
  Object.assign(linkDialog, { open: true, loading: true, saving: false, error: "", pages: [], pageId: null, title: "" });
  try {
    const { data } = await api.get<Array<{ id: number; title: string; status: string }>>("/pages", {
      params: { agency_id: agencyStore.currentAgencyId }
    });
    linkDialog.pages = data || [];
    linkDialog.pageId = linkDialog.pages[0]?.id ?? null;
  } catch {
    linkDialog.error = "Não foi possível carregar as suas páginas.";
  } finally {
    linkDialog.loading = false;
  }
};
const confirmLinkPage = async () => {
  if (!props.company || !linkDialog.pageId) return;
  linkDialog.saving = true;
  linkDialog.error = "";
  try {
    await api.post(`/admin/pages/${linkDialog.pageId}/clone`, { target_agency_id: props.company.id, title: linkDialog.title.trim() });
    linkDialog.open = false;
    pageNotice.value = { tone: "success", text: `“${linkDialog.title.trim()}” foi copiada e publicada na empresa.` };
    void loadDetail(props.company.id);
    emit("changed", "");
  } catch (error: any) {
    linkDialog.error = error?.response?.data?.detail || "Não foi possível vincular a página.";
  } finally {
    linkDialog.saving = false;
  }
};

defineExpose({ reload: () => props.company && loadDetail(props.company.id) });
</script>

<style scoped>
.cd-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--muted);
}
.cd-section {
  margin-top: 22px;
}
.cd-box {
  border: 1px solid var(--border);
  border-radius: 14px;
}
.cd-facts {
  display: grid;
  gap: 12px 18px;
  margin-top: 10px;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}
.cd-facts dt {
  font-size: 12px;
  color: var(--muted-foreground);
}
.cd-facts dd {
  margin-top: 1px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--foreground);
  overflow-wrap: anywhere;
}
.cd-actions {
  display: grid;
  gap: 12px;
  margin: 16px 0 6px;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}
</style>
