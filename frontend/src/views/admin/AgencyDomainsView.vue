<template>
  <div class="space-y-6">
    <div class="space-y-2 md:pl-2">
      <h1 class="text-2xl font-bold text-slate-900">Dominios personalizados</h1>
      <p class="mt-2 text-sm text-slate-600">
        Use um dominio proprio para compartilhar seus roteiros sem depender do link padrao
        {{ platformExample }}. Com um dominio customizado voce ganha mais autoridade e pode manter a marca da sua agencia.
      </p>
    </div>

    <div v-if="!currentAgencyId" class="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
      <p class="font-semibold">Selecione ou crie uma agencia antes de configurar dominios.</p>
      <p class="text-sm mt-1">Assim que uma agencia estiver ativa, esta tela mostrara os hosts configurados e instrucoes de DNS.</p>
    </div>

    <div v-else class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
        <h2 class="text-lg font-semibold text-slate-900">Cadastrar novo dominio</h2>
        <p class="text-sm text-slate-500">
          Exemplo: <span class="font-mono">www.suaagencia.com</span> ou <span class="font-mono">roteiros.suaagencia.com</span>
        </p>
        <form class="mt-4 space-y-4" @submit.prevent="createDomain">
          <div>
           <label class="text-sm font-medium text-slate-700">Host</label>
            <input
              v-model="form.host"
              type="text"
              placeholder="www.suaagencia.com"
              class="host-input mt-1 w-full rounded-xl px-3 py-2 text-sm text-white focus:border-[#3EBD59] focus:outline-none focus:ring-1 focus:ring-[#3EBD59]/40"
              :disabled="creating || loadingDomains"
            />
          </div>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input
              v-model="form.is_primary"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              :disabled="creating || loadingDomains"
            />
            Tornar dominio principal ao ativar
          </label>
          <div class="space-y-2 text-sm">
<button
              type="submit"
              class="inline-flex w-full items-center justify-center rounded-xl bg-[#3EBD59] px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-[#34a04c] disabled:cursor-not-allowed disabled:bg-[#3EBD59]/60"
              :disabled="creating || loadingDomains"
            >
              <span v-if="creating" class="animate-pulse">Salvando...</span>
              <span v-else>Adicionar dominio</span>
            </button>
            <p v-if="formError" class="text-sm text-red-600">{{ formError }}</p>
            <p v-if="formSuccess" class="text-sm text-emerald-600">{{ formSuccess }}</p>
          </div>
        </form>
        <div class="mt-6 rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">
          <p class="font-semibold text-slate-800">Dicas rapidas</p>
          <ul class="mt-2 list-disc space-y-1 pl-5">
            <li>Prefira um subdominio (ex.: <span class="font-mono">roteiros.suaagencia.com</span>) para configuracoes mais simples.</li>
            <li>Nao inclua <span class="font-mono">http://</span> ou caminhos extras — apenas o host.</li>
            <li>Dominios da plataforma ({{ platformExample }} e variacoes) sao reservados.</li>
          </ul>
        </div>
      </div>

      <div class="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100 dark:bg-[#202020] dark:ring-slate-800">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Dominios da agencia</h2>
            <p class="text-sm text-slate-500">
              Agencia atual: <span class="font-semibold text-slate-700">{{ currentAgencyName }}</span>
            </p>
          </div>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:border-slate-300 dark:border-slate-600 dark:text-slate-200 dark:hover:border-slate-500"
            @click="fetchDomains"
            :disabled="loadingDomains"
          >
            Atualizar
          </button>
        </div>
        <div
          v-if="listError"
          class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200"
        >
          {{ listError }}
        </div>
        <div
          v-if="loadingDomains"
          class="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300"
        >
          Carregando dominios...
        </div>
        <div
          v-else-if="!domains.length"
          class="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-400"
        >
          Nenhum dominio cadastrado ainda. Adicione um host para ver as instrucoes de DNS e verificacao.
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="domain in domains"
            :key="domain.id"
            class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 shadow-sm dark:border-slate-800 dark:bg-[#05070F]"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="text-lg font-semibold text-slate-900">{{ domain.host }}</p>
                <p class="text-xs text-slate-500">Criado em {{ formatDate(domain.created_at) }}</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="badge in buildStatusBadges(domain)"
                  :key="badge.label"
                  :class="[
                    'rounded-full px-3 py-1 text-xs font-semibold',
                    badge.variant === 'active' ? 'bg-[#3EBD59] text-white dark:bg-[#34a04c]' :
                    badge.variant === 'success' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-100' :
                    badge.variant === 'warning' ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-100' :
                    badge.variant === 'info' ? 'bg-sky-100 text-sky-800 dark:bg-sky-500/20 dark:text-sky-100' :
                    badge.variant === 'danger' ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-100' : 'bg-slate-200 text-slate-700 dark:bg-slate-600/30 dark:text-slate-100'
                  ]"
                >
                  {{ badge.label }}
                </span>
              </div>
            </div>

            <div
              v-if="domain.ssl_last_error"
              class="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200"
            >
              {{ domain.ssl_last_error }}
            </div>

            <div v-if="domainMessages[domain.id]" class="mt-2 text-xs text-emerald-700 dark:text-emerald-300">
              {{ domainMessages[domain.id] }}
            </div>

            <div class="mt-4 grid gap-4 md:grid-cols-2">
              <div class="rounded-xl border border-slate-200 bg-white/80 p-3 text-sm dark:border-slate-800 dark:bg-[#05070F]">
                <p class="font-semibold text-slate-900">Registro TXT (verificacao)</p>
                <p class="text-xs text-slate-500">Host: <span class="font-mono text-slate-800">{{ domain.instructions?.verification.host }}</span></p>
                <p class="text-xs text-slate-500">Valor: <span class="font-mono text-slate-800">{{ domain.verification_token }}</span></p>
                <p class="text-xs text-slate-500">FQDN: {{ domain.instructions?.verification.fqdn }}</p>
                <p v-if="domain.instructions?.verification.description" class="mt-1 text-xs text-slate-500">
                  {{ domain.instructions?.verification.description }}
                </p>
              </div>
              <div class="rounded-xl border border-slate-200 bg-white/80 p-3 text-sm dark:border-slate-800 dark:bg-[#05070F]">
                <p class="font-semibold text-slate-900">
                  Apontamento principal ({{ domain.instructions?.target.type }})
                </p>
                <p class="text-xs text-slate-500">
                  Host: <span class="font-mono text-slate-800">{{ domain.instructions?.target.host }}</span>
                </p>
                <p class="text-xs text-slate-500">
                  Valor: <span class="font-mono text-slate-800">{{ domain.instructions?.target.value }}</span>
                </p>
                <p class="text-xs text-slate-500">Tipo: {{ domain.instructions?.target.type }}</p>
                <p v-if="domain.instructions?.target.description" class="mt-1 text-xs text-slate-500">
                  {{ domain.instructions?.target.description }}
                </p>
              </div>
            </div>

            <div class="mt-4 flex flex-wrap gap-2 text-sm">
              <button
                type="button"
                class="rounded-xl border border-slate-300 px-3 py-1 font-semibold text-slate-700 hover:border-slate-400 disabled:opacity-50 dark:border-slate-600 dark:text-slate-100"
                :disabled="isActionRunning(domain.id)"
                @click="verifyDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'verify') ? 'Verificando...' : 'Verificar DNS' }}
              </button>
              <button
                v-if="!domain.is_active"
                type="button"
                class="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1 font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-100 dark:hover:bg-emerald-500/20"
                :disabled="isActionRunning(domain.id) || !domain.is_verified"
                @click="activateDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'activate') ? 'Ativando...' : 'Ativar dominio' }}
              </button>
              <button
                v-else
                type="button"
                class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-1 font-semibold text-amber-700 hover:bg-amber-100 disabled:opacity-50 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100 dark:hover:bg-amber-500/20"
                :disabled="isActionRunning(domain.id)"
                @click="deactivateDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'deactivate') ? 'Desativando...' : 'Desativar' }}
              </button>
              <button
                type="button"
                class="rounded-xl border border-sky-200 bg-sky-50 px-3 py-1 font-semibold text-sky-700 hover:bg-sky-100 disabled:opacity-50 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-100 dark:hover:bg-sky-500/20"
                :disabled="isActionRunning(domain.id) || domain.is_primary"
                @click="setPrimary(domain)"
              >
                {{ isActionRunning(domain.id, 'primary') ? 'Atualizando...' : 'Tornar primario' }}
              </button>
              <button
                type="button"
                class="rounded-xl border border-red-200 bg-red-50 px-3 py-1 font-semibold text-red-700 hover:bg-red-100 disabled:opacity-50 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-100 dark:hover:bg-red-500/20"
                :disabled="isActionRunning(domain.id) || domain.is_active"
                @click="removeDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'delete') ? 'Removendo...' : 'Excluir' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <h2 class="text-lg font-semibold text-slate-900">Como configurar o DNS</h2>
      <div class="mt-3 grid gap-6 md:grid-cols-2">
        <div class="space-y-2 text-sm text-slate-600">
          <p class="font-semibold text-slate-800">Subdominio (recomendado)</p>
          <ul class="list-disc space-y-1 pl-5">
            <li>Use um host como <span class="font-mono">www</span> ou <span class="font-mono">roteiros</span>.</li>
            <li>Crie um registro <span class="font-semibold">CNAME</span> apontando para <span class="font-mono">{{ cnameTarget }}</span>.</li>
            <li>Adicione o registro TXT exatamente como exibido no card do dominio.</li>
          </ul>
        </div>
        <div class="space-y-2 text-sm text-slate-600">
          <p class="font-semibold text-slate-800">Dominio raiz</p>
          <ul class="list-disc space-y-1 pl-5">
            <li>Use um registro <span class="font-semibold">A</span> com host <span class="font-mono">@</span>.</li>
            <li>O valor deve apontar para o IP configurado no painel (<span class="font-mono">{{ apexTarget }}</span>).</li>
            <li>Configure tambem o registro TXT de verificacao.</li>
          </ul>
        </div>
      </div>
      <p class="mt-4 text-sm text-slate-600">
        Assim que a verificacao DNS for concluida, vamos solicitar o SSL automaticamente (ou registrar que a emissao sera manual).
        A ativacao so sera permitida quando o certificado estiver pronto ou quando voce confirmar que ja possui SSL para o host.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";

interface DnsRecordInstruction {
  type: string;
  host: string;
  value: string;
  description?: string | null;
  fqdn?: string | null;
}

interface DomainInstructions {
  is_apex: boolean;
  verification: DnsRecordInstruction;
  target: DnsRecordInstruction;
}

interface AgencyDomain {
  id: number;
  agency_id: number;
  host: string;
  is_primary: boolean;
  is_verified: boolean;
  verification_token: string;
  dns_target_type?: string | null;
  dns_target_value?: string | null;
  ssl_status: string;
  ssl_last_error?: string | null;
  is_active: boolean;
  verified_at?: string | null;
  activated_at?: string | null;
  created_at?: string | null;
  instructions?: DomainInstructions | null;
}

const agencyStore = useAgencyStore();
const domains = ref<AgencyDomain[]>([]);
const loadingDomains = ref(false);
const listError = ref("");
const platformHosts = ["roteiroonline.com", "www.roteiroonline.com"];
const cnameTarget = ref(import.meta.env.VITE_CUSTOM_DOMAIN_CNAME_TARGET || "roteiroonline.com");
const apexTarget = ref(import.meta.env.VITE_CUSTOM_DOMAIN_APEX_IP || "1.1.1.1");
const form = reactive({
  host: "",
  is_primary: false
});
const formError = ref("");
const formSuccess = ref("");
const creating = ref(false);
const actionState = ref<string | null>(null);
const domainMessages = ref<Record<number, string>>({});

const currentAgencyId = computed(() => agencyStore.currentAgencyId);
const currentAgencyName = computed(() => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.name || "Agencia sem nome";
});
const platformExample = computed(() => `${platformHosts[0] || "seusite.com"}/agencia/roteiro`);

const clearFormFeedback = () => {
  formError.value = "";
  formSuccess.value = "";
};

const fetchDomains = async () => {
  domainMessages.value = {};
  if (!currentAgencyId.value) {
    domains.value = [];
    return;
  }
  loadingDomains.value = true;
  listError.value = "";
  try {
    const res = await api.get<AgencyDomain[]>("/agencies/me/domains", {
      params: { agency_id: currentAgencyId.value }
    });
    domains.value = res.data;
  } catch (err) {
    console.error(err);
    listError.value =
      (err as any)?.response?.data?.detail || "Nao foi possivel carregar os dominios desta agencia.";
  } finally {
    loadingDomains.value = false;
  }
};

const validateHostInput = (value: string) => {
  if (!value) return "Informe um host.";
  if (/^https?:\/\//i.test(value)) return "Informe apenas o host, sem http:// ou https://.";
  if (/[\s/]/.test(value)) return "O host nao deve conter espacos ou barras.";
  if (!value.includes(".")) return "Use um dominio completo (ex.: minhaagencia.com).";
  return "";
};

const createDomain = async () => {
  clearFormFeedback();
  if (!currentAgencyId.value) {
    formError.value = "Selecione uma agencia para continuar.";
    return;
  }
  const sanitized = form.host.trim().toLowerCase();
  const validationError = validateHostInput(sanitized);
  if (validationError) {
    formError.value = validationError;
    return;
  }
  creating.value = true;
  try {
    await api.post("/agencies/me/domains", {
      host: sanitized,
      is_primary: form.is_primary,
      agency_id: currentAgencyId.value
    });
    form.host = "";
    form.is_primary = false;
    formSuccess.value = "Dominio cadastrado com sucesso.";
    await fetchDomains();
  } catch (err) {
    console.error(err);
    formError.value =
      (err as any)?.response?.data?.detail ||
      "Nao foi possivel cadastrar o dominio. Revise o host informado.";
  } finally {
    creating.value = false;
  }
};

const isActionRunning = (domainId: number, action?: string) => {
  if (!actionState.value) return false;
  const [currentAction, currentId] = actionState.value.split(":");
  if (Number(currentId) !== domainId) return false;
  return action ? currentAction === action : true;
};

const runDomainAction = async (domainId: number, action: string, handler: () => Promise<void>) => {
  actionState.value = `${action}:${domainId}`;
  domainMessages.value = { ...domainMessages.value, [domainId]: "" };
  try {
    await handler();
    await fetchDomains();
    domainMessages.value = {
      ...domainMessages.value,
      [domainId]:
        action === "verify"
          ? "DNS verificado. Vamos atualizar o status automaticamente."
          : action === "activate"
            ? "Dominio ativado com sucesso."
            : action === "deactivate"
              ? "Dominio desativado."
              : action === "primary"
                ? "Dominio marcado como primario."
                : action === "delete"
                  ? ""
                  : "Acao concluida."
    };
  } catch (err) {
    console.error(err);
    domainMessages.value = {
      ...domainMessages.value,
      [domainId]:
        (err as any)?.response?.data?.detail ||
        "Nao foi possivel completar a acao. Tente novamente."
    };
  } finally {
    actionState.value = null;
  }
};

const verifyDomain = (domain: AgencyDomain) =>
  runDomainAction(domain.id, "verify", async () => {
    await api.post(`/agencies/me/domains/${domain.id}/verify`);
  });

const activateDomain = (domain: AgencyDomain) =>
  runDomainAction(domain.id, "activate", async () => {
    await api.post(`/agencies/me/domains/${domain.id}/activate`);
  });

const deactivateDomain = (domain: AgencyDomain) =>
  runDomainAction(domain.id, "deactivate", async () => {
    await api.post(`/agencies/me/domains/${domain.id}/deactivate`);
  });

const setPrimary = (domain: AgencyDomain) =>
  runDomainAction(domain.id, "primary", async () => {
    await api.post(`/agencies/me/domains/${domain.id}/set-primary`);
  });

const removeDomain = (domain: AgencyDomain) => {
  if (domain.is_active) {
    domainMessages.value = {
      ...domainMessages.value,
      [domain.id]: "Desative o dominio antes de excluir."
    };
    return;
  }
  const confirmed = window.confirm(`Remover o dominio ${domain.host}? Esta acao nao pode ser desfeita.`);
  if (!confirmed) return;
  runDomainAction(domain.id, "delete", async () => {
    await api.delete(`/agencies/me/domains/${domain.id}`);
  });
};

const buildStatusBadges = (domain: AgencyDomain) => {
  const badges: { label: string; variant: "active" | "success" | "warning" | "danger" | "info" | "neutral" }[] = [];
  if (domain.is_active) {
    badges.push({ label: "Ativo", variant: "active" });
  } else {
    badges.push({ label: "Inativo", variant: "neutral" });
  }
  if (domain.is_primary) {
    badges.push({ label: "Primario", variant: "info" });
  }
  if (domain.is_verified) {
    badges.push({ label: "DNS verificado", variant: "success" });
  } else {
    badges.push({ label: "DNS pendente", variant: "warning" });
  }
  if (domain.ssl_status !== "issued" && domain.is_active) {
    badges.push({ label: `SSL ${domain.ssl_status}`, variant: "warning" });
  }
  if (domain.ssl_last_error) {
    badges.push({ label: "Erro de SSL", variant: "danger" });
  }
  return badges;
};

const formatDate = (value?: string | null) => {
  if (!value) return "sem data";
  try {
    return new Date(value).toLocaleString("pt-BR");
  } catch {
    return value;
  }
};

onMounted(async () => {
  if (!agencyStore.agencies.length) {
    await agencyStore.loadAgencies();
  }
  await fetchDomains();
});

watch(
  () => agencyStore.currentAgencyId,
  async newId => {
    if (newId) {
      await fetchDomains();
    } else {
      domains.value = [];
    }
  }
);
</script>

<style scoped>
:global(.dark-theme .host-input) {
  background-color: #05070f;
  color: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.12);
}
</style>

