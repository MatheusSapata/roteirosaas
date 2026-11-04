<template>
  <div class="space-y-4">
    <div v-if="loading && !data" class="am-card"><div class="am-empty"><div class="am-spinner"></div>Carregando avisos...</div></div>
    <div v-else-if="loadError" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ loadError }}</span></div>

    <template v-else-if="data">
      <div v-if="!data.enabled" class="am-notice am-tone-warning">
        <AmIcon name="alert" />
        <span>
          Os avisos de cobrança estão desligados: nada sai para os clientes até ligar em
          <RouterLink to="/admin/administracao/avisos-cobranca" class="underline">Avisos de cobrança</RouterLink>.
        </span>
      </div>
      <div v-if="notice" class="am-notice" :class="`am-tone-${notice.tone}`">
        <AmIcon :name="notice.tone === 'success' ? 'check' : 'alert'" /><span>{{ notice.text }}</span>
      </div>

      <section class="am-grid-4">
        <AdminMasterKpi icon="check" tone="success" label="Enviados" :value="formatInt(data.counts.sent || 0)" />
        <AdminMasterKpi icon="alert" tone="danger" label="Falharam" :value="formatInt(data.counts.failed || 0)" />
        <AdminMasterKpi icon="x" tone="neutral" label="Cancelados" :value="formatInt(data.counts.cancelled || 0)" />
        <AdminMasterKpi
          icon="bell"
          tone="info"
          label="Avisos do Asaas"
          :value="data.asaas_notifications_enabled ? 'Ligados' : 'Desligados'"
          hint="E-mail e SMS que o próprio Asaas manda"
        />
      </section>

      <section class="am-card am-card-flush">
        <div class="am-toolbar">
          <button
            v-for="option in filters"
            :key="option.value"
            type="button"
            class="am-chip"
            :class="{ on: filter === option.value }"
            @click="filter = option.value"
          >
            {{ option.label }}
          </button>
          <select v-model="step" class="am-select ml-auto" aria-label="Filtrar por etapa">
            <option value="">Etapa: todas</option>
            <option v-for="item in data.steps" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
          <button type="button" class="am-btn am-btn-sm" :disabled="loading" @click="load"><AmIcon name="refresh" />Atualizar</button>
        </div>
        <div class="am-table-wrap">
          <table class="am-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Etapa</th>
                <th>Canal</th>
                <th>Situação</th>
                <th>Fatura</th>
                <th class="am-right">Valor</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filtered" :key="item.id">
                <td class="am-num">{{ formatDateTime(item.sent_at || item.updated_at || item.created_at) }}</td>
                <td>{{ item.step_label }}</td>
                <td>
                  {{ channelLabel(item.channel) }}
                  <small class="am-muted block max-w-[220px] truncate">{{ item.recipient || "Sem destinatário" }}</small>
                </td>
                <td>
                  <span class="am-badge am-dot" :class="(sendStatusMeta[item.status] || sendStatusMeta.sending).tone">
                    {{ (sendStatusMeta[item.status] || { label: item.status }).label }}
                  </span>
                  <small v-if="item.attempts > 1" class="am-muted block">{{ item.attempts }} tentativas</small>
                  <small v-if="item.error" class="cn-error block">{{ item.error }}</small>
                </td>
                <td class="am-num">
                  <span class="am-mono">{{ item.payment_id }}</span>
                  <small class="am-muted block">vence {{ formatPlainDate(item.due_date) }}</small>
                </td>
                <td class="am-right am-num">{{ item.value ?? "—" }}</td>
                <td class="am-right whitespace-nowrap">
                  <a v-if="item.link" :href="item.link" target="_blank" rel="noopener noreferrer" class="am-btn am-btn-sm">Fatura</a>
                  <button
                    v-if="item.status === 'failed'"
                    type="button"
                    class="am-btn am-btn-sm ml-1"
                    :disabled="retryingId === item.id"
                    @click="retry(item)"
                  >
                    {{ retryingId === item.id ? "Enviando..." : "Tentar de novo" }}
                  </button>
                </td>
              </tr>
              <tr v-if="!filtered.length">
                <td colspan="7"><div class="am-empty">Nenhum aviso de cobrança para esta empresa.</div></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="am-foot">
          <span>Próximos avisos de todas as empresas ficam em <RouterLink to="/admin/administracao/avisos-cobranca" class="underline">Avisos de cobrança</RouterLink>.</span>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getCompanyNotices, retryBillingNotice, type CompanyNotice, type CompanyNotices } from "../../../services/companies";
import AmIcon from "../master/AmIcon.vue";
import AdminMasterKpi from "../master/AdminMasterKpi.vue";
import { formatDateTime, formatInt } from "../master/format";
import { channelLabel, formatPlainDate, sendStatusMeta } from "./companyLabels";

const props = defineProps<{ companyId: number }>();

const data = ref<CompanyNotices | null>(null);
const loading = ref(false);
const loadError = ref("");
const notice = ref<{ tone: "success" | "danger"; text: string } | null>(null);

const load = async () => {
  loading.value = true;
  loadError.value = "";
  try {
    data.value = await getCompanyNotices(props.companyId);
  } catch (error: any) {
    loadError.value = error?.response?.data?.detail || "Não foi possível carregar os avisos de cobrança.";
  } finally {
    loading.value = false;
  }
};
onMounted(load);
watch(() => props.companyId, load);

type Filter = "all" | "sent" | "failed" | "cancelled" | "whatsapp" | "email";
const filter = ref<Filter>("all");
const step = ref("");
const filters: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "Todos" },
  { value: "sent", label: "Enviados" },
  { value: "failed", label: "Falharam" },
  { value: "cancelled", label: "Cancelados" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "email", label: "E-mail" }
];
const filtered = computed(() =>
  (data.value?.items || []).filter(item => {
    if (step.value && item.step !== step.value) return false;
    if (filter.value === "all") return true;
    if (filter.value === "whatsapp" || filter.value === "email") return item.channel === filter.value;
    return item.status === filter.value;
  })
);

const retryingId = ref<number | null>(null);
const retry = async (item: CompanyNotice) => {
  retryingId.value = item.id;
  notice.value = null;
  try {
    await retryBillingNotice(item.id);
    notice.value = { tone: "success", text: `${item.step_label} por ${channelLabel(item.channel)} enviado de novo.` };
    await load();
  } catch (error: any) {
    notice.value = { tone: "danger", text: error?.response?.data?.detail || "O envio falhou de novo." };
  } finally {
    retryingId.value = null;
  }
};
</script>

<style scoped>
.cn-error {
  max-width: 260px;
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--status-danger-foreground);
  overflow-wrap: anywhere;
}
</style>
