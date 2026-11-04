<template>
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
        {{ option.label }} <span class="am-count am-num">{{ formatInt(count(option.value)) }}</span>
      </button>
      <button type="button" class="am-btn am-btn-sm ml-auto" :disabled="loading" @click="load"><AmIcon name="refresh" />Atualizar</button>
    </div>

    <div v-if="loading && !items.length" class="am-empty"><div class="am-spinner"></div>Carregando mensagens...</div>
    <div v-else-if="loadError" class="am-notice am-tone-danger m-4"><AmIcon name="alert" /><span>{{ loadError }}</span></div>
    <div v-else-if="!filtered.length" class="am-empty">Nenhuma mensagem enviada para esta empresa.</div>
    <ul v-else class="am-list">
      <li v-for="item in filtered" :key="item.id" class="cm-row">
        <span class="am-tile" :class="item.channel === 'whatsapp' ? 'am-tone-success' : 'am-tone-info'">
          <AmIcon :name="item.channel === 'whatsapp' ? 'wa' : 'pages'" />
        </span>
        <div class="min-w-0 flex-1">
          <b class="block truncate text-[13.5px] font-semibold">{{ item.title }}</b>
          <small class="am-muted block truncate">
            {{ channelLabel(item.channel) }} · {{ item.recipient || "sem destinatário" }}
            <template v-if="item.kind_label && item.kind_label !== item.title"> · {{ item.kind_label }}</template>
            <template v-if="item.payment_id"> · fatura {{ item.payment_id }}</template>
          </small>
          <small v-if="item.error" class="cm-error block">{{ item.error }}</small>
        </div>
        <div class="text-right">
          <span class="am-badge am-dot" :class="(sendStatusMeta[item.status] || sendStatusMeta.sending).tone">
            {{ (sendStatusMeta[item.status] || { label: item.status }).label }}
          </span>
          <small class="am-muted block whitespace-nowrap">{{ formatDateTime(item.at) }}</small>
        </div>
      </li>
    </ul>
    <div class="am-foot">
      <span>Avisos de cobrança (WhatsApp e e-mail) e e-mails do sistema para a equipe. Os e-mails passaram a ser registrados agora: os anteriores não aparecem.</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getCompanyMessages, type CompanyMessage } from "../../../services/companies";
import AmIcon from "../master/AmIcon.vue";
import { formatDateTime, formatInt } from "../master/format";
import { channelLabel, sendStatusMeta } from "./companyLabels";

const props = defineProps<{ companyId: number }>();

const items = ref<CompanyMessage[]>([]);
const loading = ref(false);
const loadError = ref("");

const load = async () => {
  loading.value = true;
  loadError.value = "";
  try {
    items.value = (await getCompanyMessages(props.companyId)).items;
  } catch (error: any) {
    loadError.value = error?.response?.data?.detail || "Não foi possível carregar as mensagens.";
  } finally {
    loading.value = false;
  }
};
onMounted(load);
watch(() => props.companyId, load);

type Filter = "all" | "whatsapp" | "email" | "billing_notice" | "system_email" | "failed";
const filter = ref<Filter>("all");
const filters: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "email", label: "E-mail" },
  { value: "billing_notice", label: "Avisos de cobrança" },
  { value: "system_email", label: "E-mails do sistema" },
  { value: "failed", label: "Não saíram" }
];
const matches = (item: CompanyMessage, value: Filter) => {
  if (value === "all") return true;
  if (value === "whatsapp" || value === "email") return item.channel === value;
  if (value === "failed") return ["failed", "not_configured"].includes(item.status);
  return item.source === value;
};
const count = (value: Filter) => items.value.filter(item => matches(item, value)).length;
const filtered = computed(() => items.value.filter(item => matches(item, filter.value)));
</script>

<style scoped>
.cm-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}
.cm-error {
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--status-danger-foreground);
  overflow-wrap: anywhere;
}
</style>
