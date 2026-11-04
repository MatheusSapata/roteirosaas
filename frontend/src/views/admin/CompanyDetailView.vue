<template>
  <main class="admin-master-surface am-page w-full">
    <RouterLink :to="backLink" class="cd-back"><AmIcon name="chevron-left" />Empresas</RouterLink>

    <div v-if="loading && !company" class="am-card"><div class="am-empty"><div class="am-spinner"></div>Carregando empresa...</div></div>
    <div v-else-if="loadError && !company" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ loadError }}</span></div>

    <template v-else-if="company">
      <AdminMasterHeader :title="company.name" :subtitle="`/${company.slug} · cadastrada em ${formatDate(company.created_at)} · ${relativeDay(company.created_at)}`">
        <a v-if="company.online" :href="`/${company.slug}`" target="_blank" rel="noopener noreferrer" class="am-btn"><AmIcon name="eye" />Página pública</a>
        <a v-if="whatsappLink" :href="whatsappLink" target="_blank" rel="noopener noreferrer" class="am-btn"><AmIcon name="wa" />WhatsApp</a>
        <button type="button" class="am-btn" :disabled="loading" @click="reload"><AmIcon name="refresh" :class="loading ? 'animate-spin' : ''" />Atualizar</button>
      </AdminMasterHeader>

      <div class="cd-status">
        <span class="am-badge am-dot" :class="statusTone(company.status)">{{ company.status_label }}</span>
        <span class="text-[13px]">{{ statusDetail(company) }}</span>
        <span class="am-muted text-[13px]">· {{ planLabel(company.plan) }} · {{ gatewayLabel(billingProvider(company)) }}</span>
      </div>

      <div v-if="successMessage" class="am-notice am-tone-success"><AmIcon name="check" /><span>{{ successMessage }}</span></div>

      <nav class="am-tabs" aria-label="Seções da empresa">
        <button
          v-for="item in tabs"
          :key="item.id"
          type="button"
          class="am-tab"
          :class="{ on: tab === item.id }"
          :aria-current="tab === item.id ? 'page' : undefined"
          @click="setTab(item.id)"
        >
          {{ item.label }}
          <span v-if="item.count !== undefined" class="am-count">{{ item.count }}</span>
        </button>
      </nav>

      <!-- VISÃO GERAL -->
      <div v-if="tab === 'overview'" class="space-y-4">
        <section class="am-grid-4">
          <AdminMasterKpi
            icon="wallet"
            tone="success"
            label="MRR"
            :value="isCombo(company) ? 'Combo' : company.mrr_amount ? formatMoney(company.mrr_amount) : '—'"
            :hint="isCombo(company) ? 'Pago na Viaje On (fora do MRR)' : `${planLabel(company.plan)} · ${gatewayLabel(billingProvider(company))}`"
          />
          <AdminMasterKpi
            icon="cal"
            tone="info"
            label="Acesso até"
            :value="formatDate(company.access_until)"
            :hint="accessLeft || 'Sem prazo definido'"
          />
          <AdminMasterKpi
            icon="pages"
            tone="violet"
            label="Páginas publicadas"
            :value="`${company.pages_published}/${company.pages_total}`"
            :hint="`${formatInt(company.visits_30d)} visitas em 30 dias`"
          />
          <AdminMasterKpi
            icon="user"
            tone="neutral"
            label="Último acesso"
            :value="company.last_access_at ? relativeDay(company.last_access_at) : 'Nunca'"
            :hint="`${plural(company.members_count, 'pessoa na equipe', 'pessoas na equipe')}`"
          />
        </section>

        <div class="am-grid-2">
          <section class="am-card">
            <div class="am-card-head">
              <div>
                <div class="am-card-title">Dono da conta</div>
              </div>
              <RouterLink
                v-if="company.owner_email"
                :to="{ path: '/admin/administracao/usuarios', query: { busca: company.owner_email } }"
                class="am-btn am-btn-sm"
              >
                <AmIcon name="users" />Ver em Usuários
              </RouterLink>
            </div>
            <div v-if="company.owner_id" class="flex items-center gap-3">
              <span class="am-avatar">{{ initials(company.owner_name) }}</span>
              <div class="min-w-0 flex-1 select-text">
                <b class="block font-semibold">{{ company.owner_name }}</b>
                <span class="am-muted block text-xs">{{ company.owner_email }}</span>
                <span class="am-muted block text-xs">{{ company.owner_whatsapp || "Sem WhatsApp" }}</span>
              </div>
              <span v-if="company.owner_is_superuser" class="am-badge am-tone-violet">Superusuário</span>
            </div>
            <p v-else class="am-muted text-sm">Empresa sem dono.</p>
          </section>

          <section class="am-card">
            <div class="am-card-head">
              <div>
                <div class="am-card-title">Situação</div>
                <div class="am-card-sub">{{ company.next_step || "Sem próximo passo pendente." }}</div>
              </div>
              <button type="button" class="am-btn am-btn-sm" @click="setTab('subscription')"><AmIcon name="card" />Gerenciar assinatura</button>
            </div>
            <dl class="cd-facts">
              <div><dt>Situação</dt><dd>{{ company.status_label }}</dd></div>
              <div><dt>Desde</dt><dd>{{ company.status_since ? formatDate(company.status_since) : "—" }}<span v-if="company.since_estimated" class="am-muted"> (estimado)</span></dd></div>
              <div><dt>Cobrança</dt><dd>{{ subscriptionStatusLabel(company) }}</dd></div>
              <div><dt>Arquivos</dt><dd>{{ storageLabel }}</dd></div>
            </dl>
          </section>
        </div>

        <section class="am-card">
          <div class="am-card-head">
            <div>
              <div class="am-card-title">Origem do cadastro</div>
              <div class="am-card-sub">UTMs e de onde o dono veio quando criou a conta.</div>
            </div>
          </div>
          <div v-if="detail?.tracking.length" class="space-y-2">
            <div v-for="entry in detail.tracking" :key="entry.id" class="cd-box p-3">
              <div class="flex flex-wrap gap-1.5">
                <span v-for="chip in utmChips(entry)" :key="chip.label" class="am-badge am-tone-neutral">
                  <span class="am-muted">{{ chip.label }}:</span>{{ chip.value }}
                </span>
              </div>
              <p class="am-muted mt-2 text-[11px]">Capturado em {{ formatDateTime(entry.created_at) }}</p>
            </div>
          </div>
          <p v-else class="am-muted text-sm">Nenhuma UTM registrada.</p>
        </section>
      </div>

      <CompanySubscriptionTab
        v-else-if="tab === 'subscription'"
        :company="company"
        :free-days="freeDays"
        @changed="handleChanged"
        @deleted="handleDeleted"
      />
      <CompanyBillingTab v-else-if="tab === 'billing'" :company-id="company.id" @changed="handleChanged" />
      <CompanyNoticesTab v-else-if="tab === 'notices'" :company-id="company.id" />
      <CompanyMessagesTab v-else-if="tab === 'messages'" :company-id="company.id" />
      <CompanyPagesTab
        v-else-if="tab === 'pages'"
        :company-id="company.id"
        :company-name="company.name"
        :slug="company.slug"
        :pages="detail?.pages || []"
        :loading="loading && !detail"
        @changed="handleChanged"
      />

      <!-- EQUIPE -->
      <section v-else-if="tab === 'team'" class="am-card am-card-flush">
        <div v-if="detail?.members.length" class="am-list">
          <div v-for="member in detail.members" :key="member.user_id" class="flex flex-wrap items-center gap-3 px-4 py-3">
            <span class="am-avatar">{{ initials(member.name) }}</span>
            <div class="min-w-0 flex-1 select-text">
              <b class="block truncate text-[13.5px] font-semibold">{{ member.name }}</b>
              <small class="am-muted block truncate text-xs">{{ member.email }}</small>
            </div>
            <span class="am-badge" :class="member.is_owner ? 'am-tone-success' : 'am-tone-neutral'">{{ member.is_owner ? "Dono" : roleLabel(member.role) }}</span>
            <span class="am-muted w-[130px] text-right text-xs">{{ member.last_access_at ? `Entrou ${relativeDay(member.last_access_at)}` : "Nunca entrou" }}</span>
            <RouterLink :to="{ path: '/admin/administracao/usuarios', query: { busca: member.email } }" class="am-btn am-btn-sm">Ver usuário</RouterLink>
          </div>
        </div>
        <div v-else class="am-empty">Ninguém na equipe.</div>
      </section>

      <CompanyLogsTab v-else-if="tab === 'logs'" :company-id="company.id" :reload-key="logsKey" />
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getCompanyDetail, type Company, type CompanyDetail, type CompanyTracking } from "../../services/companies";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import AdminMasterKpi from "../../components/admin/master/AdminMasterKpi.vue";
import {
  daysUntil,
  formatDate,
  formatDateTime,
  formatInt,
  formatMoney,
  gatewayLabel,
  initials,
  planLabel,
  plural,
  relativeDay,
  statusTone
} from "../../components/admin/master/format";
import { billingProvider, isCombo, statusDetail } from "../../components/admin/companies/companyStatus";
import { roleLabel, subscriptionStatusLabel } from "../../components/admin/companies/companyLabels";
import CompanySubscriptionTab from "../../components/admin/companies/CompanySubscriptionTab.vue";
import CompanyBillingTab from "../../components/admin/companies/CompanyBillingTab.vue";
import CompanyNoticesTab from "../../components/admin/companies/CompanyNoticesTab.vue";
import CompanyMessagesTab from "../../components/admin/companies/CompanyMessagesTab.vue";
import CompanyPagesTab from "../../components/admin/companies/CompanyPagesTab.vue";
import CompanyLogsTab from "../../components/admin/companies/CompanyLogsTab.vue";

type Tab = "overview" | "subscription" | "billing" | "notices" | "messages" | "pages" | "team" | "logs";
const TAB_SLUGS: Record<Tab, string> = {
  overview: "visao-geral",
  subscription: "assinatura",
  billing: "faturas",
  notices: "avisos",
  messages: "mensagens",
  pages: "paginas",
  team: "equipe",
  logs: "logs"
};

const route = useRoute();
const router = useRouter();

const companyId = computed(() => Number(route.params.id) || 0);
const detail = ref<CompanyDetail | null>(null);
const company = computed<Company | null>(() => detail.value?.company || null);
const loading = ref(false);
const loadError = ref("");
const successMessage = ref("");
const logsKey = ref(0);
const freeDays = 7;

const tabFromQuery = (): Tab => {
  const value = String(route.query.aba || "");
  return (Object.keys(TAB_SLUGS) as Tab[]).find(key => TAB_SLUGS[key] === value) || "overview";
};
const tab = ref<Tab>(tabFromQuery());
const setTab = (value: Tab) => {
  tab.value = value;
  successMessage.value = "";
  void router.replace({ query: { ...route.query, aba: value === "overview" ? undefined : TAB_SLUGS[value] } });
};
watch(
  () => route.query.aba,
  () => {
    tab.value = tabFromQuery();
  }
);

const tabs = computed(() => {
  const pages = detail.value?.pages.length;
  const members = detail.value?.members.length;
  return [
    { id: "overview" as Tab, label: "Visão geral" },
    { id: "subscription" as Tab, label: "Assinatura" },
    { id: "billing" as Tab, label: "Faturas e pagamentos" },
    { id: "notices" as Tab, label: "Avisos de cobrança" },
    { id: "messages" as Tab, label: "Mensagens" },
    { id: "pages" as Tab, label: "Páginas", count: pages },
    { id: "team" as Tab, label: "Equipe", count: members },
    { id: "logs" as Tab, label: "Logs" }
  ];
});

// A volta para a lista mantém os filtros que estavam lá.
const backLink = computed(() => {
  const query = { ...route.query };
  delete query.aba;
  return { path: "/admin/administracao/empresas", query };
});

const load = async () => {
  const id = companyId.value;
  if (!id) return;
  loading.value = true;
  loadError.value = "";
  try {
    const data = await getCompanyDetail(id);
    if (id === companyId.value) detail.value = data;
  } catch (error: any) {
    loadError.value = error?.response?.status === 404 ? "Empresa não encontrada." : error?.response?.data?.detail || "Não foi possível carregar a empresa.";
  } finally {
    loading.value = false;
  }
};
const reload = async () => {
  logsKey.value += 1;
  await load();
};
watch(companyId, () => {
  detail.value = null;
  void load();
}, { immediate: true });

const handleChanged = async (message: string) => {
  if (message) successMessage.value = message;
  await reload();
};
const handleDeleted = (message: string) => {
  void router.push({ path: "/admin/administracao/empresas", query: { aviso: message } });
};

const accessLeft = computed(() => {
  const left = daysUntil(company.value?.access_until);
  if (left === null) return "";
  if (left < 0) return `venceu há ${-left} ${left === -1 ? "dia" : "dias"}`;
  if (left === 0) return "vence hoje";
  return `faltam ${left} ${left === 1 ? "dia" : "dias"}`;
});
const whatsappLink = computed(() => {
  const digits = String(company.value?.owner_whatsapp || "").replace(/\D/g, "");
  if (!digits) return "";
  return `https://wa.me/${digits.length <= 11 ? `55${digits}` : digits}`;
});
const storageLabel = computed(() => {
  const item = company.value;
  if (!item) return "—";
  const stages: Record<string, string> = { hot: "No ar", cool: "Guardados", archive: "Arquivados", restoring: "Restaurando", deleted: "Apagados" };
  const size = item.media_bytes ? `${(item.media_bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB` : "";
  return [stages[item.media_stage] || item.media_stage, item.media_files ? `${formatInt(item.media_files)} arquivos` : "", size].filter(Boolean).join(" · ");
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
</script>

<style scoped>
.cd-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted-foreground);
}
.cd-back:hover {
  color: var(--foreground);
}
.cd-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--muted);
}
.cd-box {
  border: 1px solid var(--border);
  border-radius: 14px;
}
.cd-facts {
  display: grid;
  gap: 12px 18px;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
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
</style>
