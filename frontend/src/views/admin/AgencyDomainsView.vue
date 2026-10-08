<template>
  <div v-if="isBootstrappingDomains" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-border border-t-primary"></div>
  </div>
  <div v-else class="relative w-full domains-premium">
    <div class="page-wrap">
      <div class="dm-head">
        <div class="min-w-0">
          <p class="dm-eyebrow">Configurar</p>
          <h1 class="dm-title">Domínios</h1>
          <p class="dm-sub">Use o endereço da sua agência nas páginas, como viagens.suaagencia.com.br.</p>
        </div>
        <span v-if="planName" class="dm-plan">Plano {{ planName }}</span>
      </div>

      <div :class="{ 'select-none opacity-60 blur-sm': !domainsAllowed }">
        <div v-if="!currentAgencyId" class="dm-alert">
          <p class="font-semibold">{{ viewCopy.noAgency.title }}</p>
          <p class="mt-1 text-sm">{{ viewCopy.noAgency.helper }}</p>
        </div>

        <div v-else class="dm-grid">
          <section class="dm-card">
            <header class="dm-card-head">
              <div>
                <h2>Domínios da agência</h2>
                <p>{{ domains.length }} {{ domains.length === 1 ? "domínio" : "domínios" }} · {{ activeCount }} no ar</p>
              </div>
              <button type="button" class="dm-btn-ghost" :disabled="loadingDomains" @click="fetchDomains">
                <RotateCwIcon aria-hidden="true" />
                Atualizar
              </button>
            </header>

            <div v-if="listError" class="dm-msg is-error">{{ listError }}</div>
            <div v-if="loadingDomains" class="dm-empty">{{ viewCopy.list.loading }}</div>
            <div v-else-if="!domains.length" class="dm-empty">{{ viewCopy.list.empty }}</div>

            <article v-for="domain in loadingDomains ? [] : domains" :key="domain.id" class="dm-domain">
              <div class="dm-domain-top">
                <span class="dm-globe" :class="domain.is_active ? 'is-on' : 'is-pending'" aria-hidden="true">
                  <GlobeIcon aria-hidden="true" />
                </span>
                <div class="dm-domain-main">
                  <div class="dm-domain-title">
                    <b>{{ domain.host }}</b>
                    <span class="dm-pill" :class="domainStateTone(domain)">{{ domainStateLabel(domain) }}</span>
                    <span v-if="domain.is_primary" class="dm-pill is-info">Principal</span>
                  </div>
                  <p class="dm-domain-meta">
                    Adicionado em {{ formatDay(domain.created_at) }}<template v-if="domain.is_primary && domain.is_active"> · todas as páginas usam este endereço</template>
                  </p>
                </div>
                <button
                  v-if="!domain.is_verified"
                  type="button"
                  class="dm-btn-primary dm-btn-sm"
                  :disabled="isActionRunning(domain.id)"
                  @click="verifyDomain(domain)"
                >
                  {{ isActionRunning(domain.id, 'verify') ? viewCopy.actions.verifying : "Verificar DNS" }}
                </button>
                <div class="dm-menu-wrap">
                  <button type="button" class="dm-icon-btn" aria-label="Mais ações" title="Mais ações" @click.stop="openMenuId = openMenuId === domain.id ? null : domain.id">
                    <EllipsisVerticalIcon aria-hidden="true" />
                  </button>
                  <div v-if="openMenuId === domain.id" class="dm-menu" @click="openMenuId = null">
                    <button v-if="domain.is_verified" type="button" :disabled="isActionRunning(domain.id)" @click="verifyDomain(domain)">Verificar DNS de novo</button>
                    <button type="button" :disabled="isActionRunning(domain.id) || domain.is_primary" @click="setPrimary(domain)">Tornar principal</button>
                    <button v-if="domain.is_active" type="button" :disabled="isActionRunning(domain.id)" @click="deactivateDomain(domain)">Desativar</button>
                    <button type="button" class="danger" :disabled="isActionRunning(domain.id) || domain.is_active" :title="domain.is_active ? 'Desative o domínio antes de excluir' : ''" @click="removeDomain(domain)">Excluir</button>
                  </div>
                </div>
              </div>

              <div class="dm-chips">
                <span class="dm-chip" :class="domain.is_verified ? 'is-ok' : 'is-wait'">
                  <CheckIcon v-if="domain.is_verified" aria-hidden="true" />
                  <ClockIcon v-else aria-hidden="true" />
                  {{ domain.is_verified ? "DNS verificado" : "DNS pendente" }}
                </span>
                <span class="dm-chip" :class="sslReady(domain) ? 'is-ok' : 'is-neutral'">
                  <LockIcon aria-hidden="true" />
                  {{ sslReady(domain) ? "Cadeado (SSL) ativo" : "Cadeado (SSL) aguardando" }}
                </span>
                <span v-if="domain.is_active" class="dm-chip is-ok">
                  <CheckIcon aria-hidden="true" />
                  Ativo
                </span>
                <button
                  v-else
                  type="button"
                  class="dm-chip is-action"
                  :disabled="isActionRunning(domain.id) || !domain.is_verified"
                  :title="domain.is_verified ? '' : 'Verifique o DNS antes de ativar'"
                  @click="activateDomain(domain)"
                >
                  {{ isActionRunning(domain.id, 'activate') ? viewCopy.actions.activating : "Ativar" }}
                </button>
              </div>

              <div v-if="!domain.is_verified" class="dm-dns">
                <p class="dm-dns-title">Crie estes dois registros no painel onde o domínio foi comprado</p>
                <table>
                  <thead>
                    <tr><th>Tipo</th><th>Nome</th><th>Valor</th><th></th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="record in dnsRecords(domain)" :key="record.key">
                      <td>{{ record.type }}</td>
                      <td><code>{{ record.name }}</code></td>
                      <td><code>{{ record.value }}</code></td>
                      <td class="text-right">
                        <button type="button" class="dm-copy" :disabled="!record.value || record.value === '-'" @click="copyText(record.value, `${record.key}-${domain.id}`)">
                          <CopyIcon aria-hidden="true" />
                          {{ copiedState[`${record.key}-${domain.id}`] ? "Copiado" : "Copiar" }}
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <p class="dm-dns-note">A mudança no DNS pode levar algumas horas. Depois, clique em "Verificar DNS".</p>
              </div>

              <div v-if="domain.ssl_last_error" class="dm-msg is-error">{{ domain.ssl_last_error }}</div>
              <div v-if="domainMessages[domain.id]" class="dm-msg is-ok">{{ domainMessages[domain.id] }}</div>
            </article>
          </section>

          <aside class="dm-side">
            <section class="dm-card">
              <header class="dm-card-head dm-card-head-plain">
                <div>
                  <h2>Adicionar domínio</h2>
                  <p>Use só o endereço, sem https://.</p>
                </div>
              </header>
              <form class="dm-form" @submit.prevent="createDomain">
                <input
                  v-model="form.host"
                  type="text"
                  :placeholder="viewCopy.form.hostPlaceholder"
                  class="dm-input"
                  :disabled="creating || loadingDomains"
                />
                <label class="dm-toggle-row">
                  <span>
                    <b>Tornar principal ao ativar</b>
                    <small>As páginas passam a usar este endereço.</small>
                  </span>
                  <button
                    type="button"
                    role="switch"
                    class="dm-switch"
                    :class="{ on: form.is_primary }"
                    :aria-checked="form.is_primary"
                    :disabled="creating || loadingDomains"
                    @click="form.is_primary = !form.is_primary"
                  ><i></i></button>
                </label>
                <button type="submit" class="dm-btn-primary dm-btn-block" :disabled="creating || loadingDomains">
                  <PlusIcon aria-hidden="true" />
                  {{ creating ? viewCopy.form.submitSaving : "Adicionar domínio" }}
                </button>
                <p v-if="formError" class="dm-msg is-error">{{ formError }}</p>
                <p v-if="formSuccess" class="dm-msg is-ok">{{ formSuccess }}</p>
              </form>
            </section>

            <section class="dm-card">
              <header class="dm-card-head dm-card-head-plain">
                <div>
                  <h2>Ícone da aba (favicon)</h2>
                  <p>Aparece na aba do navegador nas páginas do seu domínio.</p>
                </div>
              </header>
              <div class="dm-favicon" :class="{ 'is-disabled': !hasActiveCustomDomain }">
                <ImageUploadField
                  v-model="faviconUrl"
                  layout="row"
                  replace-label="Trocar"
                  hint="PNG quadrado, 64 × 64 px ou maior"
                  :label="''"
                  :enable-crop="true"
                  :crop-aspect="1"
                  :editor-title="viewCopy.favicon.editorTitle"
                />
              </div>
              <p v-if="!hasActiveCustomDomain" class="dm-hint">{{ viewCopy.favicon.disabledHint }}</p>
              <button
                v-if="faviconChanged"
                type="button"
                class="dm-btn-primary dm-btn-block"
                :disabled="savingFavicon || !hasActiveCustomDomain"
                @click="saveFavicon"
              >
                {{ savingFavicon ? viewCopy.favicon.saving : "Salvar ícone" }}
              </button>
              <p v-if="faviconMessage" class="dm-msg is-ok">{{ faviconMessage }}</p>
              <p v-if="faviconError" class="dm-msg is-error">{{ faviconError }}</p>
            </section>
          </aside>
        </div>
      </div>
    </div>
    <div
      v-if="!domainsAllowed"
      class="pointer-events-auto fixed inset-y-0 left-0 right-0 z-[120] flex items-center justify-center bg-black/60 px-4 text-center backdrop-blur-[2px] md:left-[var(--admin-sidebar-offset)]"
    >
      <div class="max-w-md rounded-3xl border border-border bg-card p-6 text-card-foreground shadow-elegant">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-muted-foreground">{{ viewCopy.overlay.eyebrow }}</p>
        <h2 class="mt-2 font-display text-2xl font-semibold text-foreground">{{ viewCopy.overlay.title }}</h2>
        <p class="mt-2 text-sm text-muted-foreground">
          {{ viewCopy.overlay.description }}
        </p>
        <button
          type="button"
          class="mt-4 w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-soft transition-colors hover:bg-brand-dark"
          @click="goToPlans"
        >
          {{ viewCopy.overlay.cta }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  CheckIcon,
  ClockIcon,
  CopyIcon,
  EllipsisVerticalIcon,
  GlobeIcon,
  LockIcon,
  PlusIcon,
  RotateCwIcon
} from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import ImageUploadField from "../../components/admin/inputs/ImageUploadField.vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { canAccessPermission } from "../../utils/permissions";

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

const router = useRouter();
const auth = useAuthStore();
const agencyStore = useAgencyStore();
const t = createAdminLocalizer();

const viewCopy = {
  hero: {
    title: t({ pt: "Domínios personalizados", es: "Dominios personalizados" }),
    description: (example: string) =>
      t({
        pt: `Use um domínio próprio para compartilhar seus roteiros sem depender do link padrão ${example}. Com um domínio customizado você ganha mais autoridade e mantém a marca da sua agência.`,
        es: `Usa un dominio propio para compartir tus itinerarios sin depender del enlace estándar ${example}. Con un dominio personalizado ganas autoridad y mantienes la marca de tu agencia.`
      })
  },
  noAgency: {
    title: t({
      pt: "Selecione ou crie uma agência antes de configurar domínios.",
      es: "Selecciona o crea una agencia antes de configurar dominios."
    }),
    helper: t({
      pt: "Assim que uma agência estiver ativa, esta tela mostrará os hosts configurados e instruções de DNS.",
      es: "En cuanto una agencia esté activa, esta pantalla mostrará los hosts configurados y las instrucciones de DNS."
    })
  },
  form: {
    title: t({ pt: "Cadastrar novo domínio", es: "Registrar nuevo dominio" }),
    examplePrefix: t({ pt: "Exemplo:", es: "Ejemplo:" }),
    exampleOr: t({ pt: "ou", es: "o" }),
    hostLabel: t({ pt: "Host", es: "Host" }),
    hostPlaceholder: t({ pt: "www.suaagencia.com", es: "www.tuagencia.com" }),
    primaryOption: t({ pt: "Tornar domínio principal ao ativar", es: "Marcar como dominio principal al activar" }),
    submitSaving: t({ pt: "Salvando...", es: "Guardando..." }),
    submitLabel: t({ pt: "Adicionar domínio", es: "Agregar dominio" }),
    errors: {
      planOnly: t({ pt: "Recurso disponível apenas no plano Infinity.", es: "Función disponible solo en el plan Infinity." }),
      selectAgency: t({ pt: "Selecione uma agência para continuar.", es: "Selecciona una agencia para continuar." })
    },
    success: t({ pt: "Domínio cadastrado com sucesso.", es: "Dominio registrado con éxito." }),
    failure: t({
      pt: "Não foi possível cadastrar o domínio. Revise o host informado.",
      es: "No fue posible registrar el dominio. Revisa el host informado."
    }),
    validation: {
      emptyHost: t({ pt: "Informe um host.", es: "Ingresa un host." }),
      noProtocol: t({ pt: "Informe apenas o host, sem http:// ou https://.", es: "Ingresa solo el host, sin http:// o https://." }),
      noSpaces: t({ pt: "O host não deve conter espaços ou barras.", es: "El host no debe contener espacios ni barras." }),
      fullDomain: t({ pt: "Use um domínio completo (ex.: minhaagencia.com).", es: "Usa un dominio completo (ej.: miagencia.com)." })
    }
  },
  tips: {
    title: t({ pt: "Dicas rápidas", es: "Consejos rápidos" }),
    subdomainPrefix: t({ pt: "Prefira um subdomínio (ex.:", es: "Prefiere un subdominio (ej.:" }),
    subdomainSuffix: t({ pt: ") para configurações mais simples.", es: ") para configuraciones más simples." }),
    protocolPrefix: t({ pt: "Não inclua", es: "No incluyas" }),
    protocolSuffix: t({ pt: "ou caminhos extras — apenas o host.", es: "ni rutas adicionales — solo el host." }),
    reserved: (example: string) =>
      t({
        pt: `Domínios da plataforma (${example} e variações) são reservados.`,
        es: `Los dominios de la plataforma (${example} y variaciones) están reservados.`
      })
  },
  list: {
    title: t({ pt: "Domínios da agência", es: "Dominios de la agencia" }),
    currentAgencyLabel: t({ pt: "Agência atual:", es: "Agencia actual:" }),
    refresh: t({ pt: "Atualizar", es: "Actualizar" }),
    loading: t({ pt: "Carregando domínios...", es: "Cargando dominios..." }),
    empty: t({
      pt: "Nenhum domínio cadastrado ainda. Adicione um host para ver as instruções de DNS e verificação.",
      es: "Aún no hay dominios registrados. Agrega un host para ver las instrucciones de DNS y verificación."
    }),
    unnamedAgency: t({ pt: "Agência sem nome", es: "Agencia sin nombre" })
  },
  favicon: {
    title: t({ pt: "Favicon da agência", es: "Favicon de la agencia" }),
    subtitle: t({ pt: "Ícone exibido nas páginas públicas do seu domínio.", es: "Ícono mostrado en las páginas públicas de tu dominio." }),
    disabledHint: t({
      pt: "Ative um domínio personalizado para habilitar o favicon.",
      es: "Activa un dominio personalizado para habilitar el favicon."
    }),
    editorTitle: t({ pt: "Ajuste o favicon", es: "Ajusta el favicon" }),
    save: t({ pt: "Salvar favicon", es: "Guardar favicon" }),
    saving: t({ pt: "Salvando...", es: "Guardando..." }),
    success: t({ pt: "Favicon atualizado com sucesso.", es: "Favicon actualizado con éxito." }),
    error: t({ pt: "Não foi possível salvar o favicon.", es: "No fue posible guardar el favicon." })
  },
  domainInfo: {
    createdAt: t({ pt: "Criado em", es: "Creado el" }),
    verificationTitle: t({ pt: "Registro TXT (verificação)", es: "Registro TXT (verificación)" }),
    hostLabel: t({ pt: "Host:", es: "Host:" }),
    valueLabel: t({ pt: "Valor:", es: "Valor:" }),
    fqdnLabel: t({ pt: "FQDN:", es: "FQDN:" }),
    targetTitle: t({ pt: "Apontamento principal", es: "Apuntador principal" }),
    typeLabel: t({ pt: "Tipo:", es: "Tipo:" })
  },
  actions: {
    verifying: t({ pt: "Verificando...", es: "Verificando..." }),
    verify: t({ pt: "Verificar DNS", es: "Verificar DNS" }),
    activating: t({ pt: "Ativando...", es: "Activando..." }),
    activate: t({ pt: "Ativar domínio", es: "Activar dominio" }),
    deactivating: t({ pt: "Desativando...", es: "Desactivando..." }),
    deactivate: t({ pt: "Desativar", es: "Desactivar" }),
    primarying: t({ pt: "Atualizando...", es: "Actualizando..." }),
    setPrimary: t({ pt: "Tornar primário", es: "Marcar como primario" }),
    deleting: t({ pt: "Removendo...", es: "Eliminando..." }),
    delete: t({ pt: "Excluir", es: "Eliminar" })
  },
  dnsGuide: {
    title: t({ pt: "Como configurar o DNS", es: "Cómo configurar el DNS" }),
    subdomainTitle: t({ pt: "Subdomínio (recomendado)", es: "Subdominio (recomendado)" }),
    subdomainHostPrefix: t({ pt: "Use um host como", es: "Usa un host como" }),
    subdomainHostConnector: t({ pt: "ou", es: "o" }),
    subdomainCname: t({ pt: "Crie um registro CNAME apontando para", es: "Crea un registro CNAME apuntando a" }),
    subdomainTxt: t({
      pt: "Adicione o registro TXT exatamente como exibido no card do domínio.",
      es: "Agrega el registro TXT exactamente como aparece en la tarjeta del dominio."
    }),
    apexTitle: t({ pt: "Domínio raiz", es: "Dominio raíz" }),
    apexRecord: t({ pt: "Use um registro A com host @.", es: "Usa un registro A con host @." }),
    apexValuePrefix: t({ pt: "O valor deve apontar para o IP configurado no painel (", es: "El valor debe apuntar al IP configurado en el panel (" }),
    apexValueSuffix: t({ pt: ").", es: ")." }),
    apexTxt: t({ pt: "Configure também o registro TXT de verificação.", es: "Configura también el registro TXT de verificación." }),
    footer: t({
      pt: "Assim que a verificação DNS for concluída, solicitaremos o SSL automaticamente (ou registraremos que a emissão será manual). A ativação só será permitida quando o certificado estiver pronto ou quando você confirmar que já possui SSL para o host.",
      es: "Cuando la verificación DNS termine, solicitaremos el SSL automáticamente (o registraremos que la emisión será manual). La activación solo se permitirá cuando el certificado esté listo o cuando confirmes que ya tienes SSL para el host."
    })
  },
  overlay: {
    eyebrow: t({ pt: "Recurso premium", es: "Función premium" }),
    title: t({ pt: "Disponível no plano Escala", es: "Disponible en el plan Escala" }),
    description: t({
      pt: "Domínios personalizados ficam liberados apenas no plano Escala. Faça upgrade para configurar seu host.",
      es: "Los dominios personalizados se habilitan solo en el plan Escala. Haz upgrade para configurar tu host."
    }),
    cta: t({ pt: "Conhecer planos", es: "Conocer planes" })
  },
  messages: {
    fetchError: t({
      pt: "Não foi possível carregar os domínios desta agência.",
      es: "No fue posible cargar los dominios de esta agencia."
    }),
    dnsVerified: t({
      pt: "DNS verificado. Vamos atualizar o status automaticamente.",
      es: "DNS verificado. Actualizaremos el estado automáticamente."
    }),
    domainActivated: t({ pt: "Domínio ativado com sucesso.", es: "Dominio activado con éxito." }),
    domainDeactivated: t({ pt: "Domínio desativado.", es: "Dominio desactivado." }),
    domainPrimary: t({ pt: "Domínio marcado como primário.", es: "Dominio marcado como primario." }),
    domainGeneric: t({ pt: "Ação concluída.", es: "Acción completada." }),
    domainActionError: t({
      pt: "Não foi possível completar a ação. Tente novamente.",
      es: "No fue posible completar la acción. Intenta de nuevo."
    }),
    disableBeforeDelete: t({ pt: "Desative o domínio antes de excluir.", es: "Desactiva el dominio antes de eliminarlo." }),
    confirmDelete: (host: string) =>
      t({
        pt: `Remover o domínio ${host}? Esta ação não pode ser desfeita.`,
        es: `¿Eliminar el dominio ${host}? Esta acción no se puede deshacer.`
      }),
    noDate: t({ pt: "sem data", es: "sin fecha" })
  },
  statuses: {
    active: t({ pt: "Ativo", es: "Activo" }),
    inactive: t({ pt: "Inativo", es: "Inactivo" }),
    primary: t({ pt: "Primário", es: "Primario" }),
    verified: t({ pt: "DNS verificado", es: "DNS verificado" }),
    pending: t({ pt: "DNS pendente", es: "DNS pendiente" }),
    sslError: t({ pt: "Erro de SSL", es: "Error de SSL" })
  }
};
const domains = ref<AgencyDomain[]>([]);
const isBootstrappingDomains = ref(true);
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
const copiedState = ref<Record<string, boolean>>({});
const faviconUrl = ref("");
const savingFavicon = ref(false);
const faviconMessage = ref("");
const faviconError = ref("");

const domainsAllowed = computed(() =>
  canAccessPermission("domains", {
    isOwner: auth.user?.is_owner,
    selected: auth.user?.permissions || [],
    plan: auth.user?.trial_plan || auth.user?.plan || null,
    effective: auth.user?.effective_permissions || []
  })
);
const currentAgencyId = computed(() => agencyStore.currentAgencyId);
const currentAgencyName = computed(() => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.name || viewCopy.list.unnamedAgency;
});
const currentAgency = computed(() => agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId) || null);
const hasActiveCustomDomain = computed(() => domains.value.some(domain => domain.is_active));
const platformExample = computed(() => `${platformHosts[0] || "seusite.com"}/agencia/roteiro`);
const apexTargetExample = computed(() => {
  const fromDomain = domains.value.find(domain => domain.instructions?.target?.value)?.instructions?.target?.value;
  return fromDomain || "SEU_IP_AQUI";
});
const goToPlans = () => {
  router.push("/admin/planos");
};

const clearFormFeedback = () => {
  formError.value = "";
  formSuccess.value = "";
};
const clearFaviconFeedback = () => {
  faviconMessage.value = "";
  faviconError.value = "";
};

const fetchDomains = async () => {
  domainMessages.value = {};
  if (!currentAgencyId.value || !domainsAllowed.value) {
    domains.value = [];
    loadingDomains.value = false;
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
    listError.value = (err as any)?.response?.data?.detail || viewCopy.messages.fetchError;
  } finally {
    loadingDomains.value = false;
  }
};

const validateHostInput = (value: string) => {
  if (!value) return viewCopy.form.validation.emptyHost;
  if (/^https?:\/\//i.test(value)) return viewCopy.form.validation.noProtocol;
  if (/[\s/]/.test(value)) return viewCopy.form.validation.noSpaces;
  if (!value.includes(".")) return viewCopy.form.validation.fullDomain;
  return "";
};

const createDomain = async () => {
  clearFormFeedback();
  if (!domainsAllowed.value) {
    formError.value = viewCopy.form.errors.planOnly;
    return;
  }
  if (!currentAgencyId.value) {
    formError.value = viewCopy.form.errors.selectAgency;
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
    formSuccess.value = viewCopy.form.success;
    await fetchDomains();
  } catch (err) {
    console.error(err);
    formError.value = (err as any)?.response?.data?.detail || viewCopy.form.failure;
  } finally {
    creating.value = false;
  }
};

const saveFavicon = async () => {
  clearFaviconFeedback();
  if (!currentAgencyId.value || !hasActiveCustomDomain.value) return;
  savingFavicon.value = true;
  try {
    const res = await api.put(`/agencies/${currentAgencyId.value}`, {
      favicon_url: faviconUrl.value || null
    });
    const idx = agencyStore.agencies.findIndex(item => item.id === currentAgencyId.value);
    if (idx >= 0) {
      agencyStore.agencies[idx] = { ...agencyStore.agencies[idx], ...res.data };
    }
    faviconMessage.value = viewCopy.favicon.success;
  } catch (err) {
    console.error(err);
    faviconError.value = (err as any)?.response?.data?.detail || viewCopy.favicon.error;
  } finally {
    savingFavicon.value = false;
  }
};

const isActionRunning = (domainId: number, action?: string) => {
  if (!actionState.value) return false;
  const [currentAction, currentId] = actionState.value.split(":");
  if (Number(currentId) !== domainId) return false;
  return action ? currentAction === action : true;
};

const runDomainAction = async (domainId: number, action: string, handler: () => Promise<void>) => {
  if (!domainsAllowed.value) return;
  actionState.value = `${action}:${domainId}`;
  domainMessages.value = { ...domainMessages.value, [domainId]: "" };
  try {
    await handler();
    await fetchDomains();
    let successMessage = "";
    if (action === "verify") successMessage = viewCopy.messages.dnsVerified;
    else if (action === "activate") successMessage = viewCopy.messages.domainActivated;
    else if (action === "deactivate") successMessage = viewCopy.messages.domainDeactivated;
    else if (action === "primary") successMessage = viewCopy.messages.domainPrimary;
    else if (action !== "delete") successMessage = viewCopy.messages.domainGeneric;
    domainMessages.value = {
      ...domainMessages.value,
      [domainId]: successMessage
    };
  } catch (err) {
    console.error(err);
    domainMessages.value = {
      ...domainMessages.value,
      [domainId]:
        (err as any)?.response?.data?.detail || viewCopy.messages.domainActionError
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
      [domain.id]: viewCopy.messages.disableBeforeDelete
    };
    return;
  }
  const confirmed = window.confirm(viewCopy.messages.confirmDelete(domain.host));
  if (!confirmed) return;
  runDomainAction(domain.id, "delete", async () => {
    await api.delete(`/agencies/me/domains/${domain.id}`);
  });
};

const buildStatusBadges = (domain: AgencyDomain) => {
  const badges: { label: string; variant: "active" | "success" | "warning" | "danger" | "info" | "neutral" }[] = [];
  if (domain.is_active) {
    badges.push({ label: viewCopy.statuses.active, variant: "active" });
  } else {
    badges.push({ label: viewCopy.statuses.inactive, variant: "neutral" });
  }
  if (domain.is_primary) {
    badges.push({ label: viewCopy.statuses.primary, variant: "info" });
  }
  if (domain.is_verified) {
    badges.push({ label: viewCopy.statuses.verified, variant: "success" });
  } else {
    badges.push({ label: viewCopy.statuses.pending, variant: "warning" });
  }
  if (domain.ssl_status !== "issued" && domain.is_active) {
    badges.push({ label: `SSL ${domain.ssl_status}`, variant: "warning" });
  }
  if (domain.ssl_last_error) {
    badges.push({ label: viewCopy.statuses.sslError, variant: "danger" });
  }
  return badges;
};

const formatDate = (value?: string | null) => {
  if (!value) return viewCopy.messages.noDate;
  try {
    return new Date(value).toLocaleString("pt-BR");
  } catch {
    return value;
  }
};

// ===== Visual da proposta =====
const activeCount = computed(() => domains.value.filter(domain => domain.is_active).length);
const sslReady = (domain: AgencyDomain) => ["issued", "active"].includes(String(domain.ssl_status || "").toLowerCase());
const domainStateLabel = (domain: AgencyDomain) => (domain.is_active ? "No ar" : domain.is_verified ? "Desativado" : "Configurando");
const domainStateTone = (domain: AgencyDomain) => (domain.is_active ? "is-success" : domain.is_verified ? "is-muted" : "is-warning");
const formatDay = (value?: string | null) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleDateString("pt-BR");
};
const dnsRecords = (domain: AgencyDomain) => [
  {
    key: "txt",
    type: domain.instructions?.verification.type || "TXT",
    name: domain.instructions?.verification.host || "-",
    value: domain.verification_token || domain.instructions?.verification.value || "-"
  },
  {
    key: "target",
    type: domain.instructions?.target.type || domain.dns_target_type || "CNAME",
    name: domain.instructions?.target.host || "-",
    value: domain.instructions?.target.value || domain.dns_target_value || "-"
  }
];
const planNames: Record<string, string> = {
  free: "Gratuito", professional: "Essencial", essencial: "Essencial", agency: "Agência", agencia: "Agência", growth: "Agência",
  scale: "Escala", escala: "Escala", infinity: "Escala", test: "Teste", teste: "Teste"
};
const planName = computed(() => {
  const key = String(auth.user?.plan || "").trim().toLowerCase();
  return key ? planNames[key] || key.charAt(0).toUpperCase() + key.slice(1) : "";
});
const faviconChanged = computed(() => (faviconUrl.value || "") !== (currentAgency.value?.favicon_url || ""));
const openMenuId = ref<number | null>(null);
const closeDomainMenu = (event: MouseEvent) => {
  if (!(event.target as HTMLElement | null)?.closest(".dm-menu-wrap")) openMenuId.value = null;
};
onMounted(() => document.addEventListener("click", closeDomainMenu));
onBeforeUnmount(() => document.removeEventListener("click", closeDomainMenu));

const copyText = async (value: string, key: string) => {
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
    copiedState.value = { ...copiedState.value, [key]: true };
    setTimeout(() => {
      copiedState.value = { ...copiedState.value, [key]: false };
    }, 1200);
  } catch (err) {
    console.error(err);
  }
};

onMounted(async () => {
  try {
    if (!agencyStore.agencies.length) {
      await agencyStore.loadAgencies();
    }
    faviconUrl.value = currentAgency.value?.favicon_url || "";
    if (domainsAllowed.value) {
      await fetchDomains();
    }
  } finally {
    isBootstrappingDomains.value = false;
  }
});

watch(
  () => agencyStore.currentAgencyId,
  async newId => {
    clearFaviconFeedback();
    faviconUrl.value = currentAgency.value?.favicon_url || "";
    if (newId && domainsAllowed.value) {
      await fetchDomains();
    } else {
      domains.value = [];
    }
  }
);

watch(domainsAllowed, allowed => {
  if (allowed) {
    faviconUrl.value = currentAgency.value?.favicon_url || "";
    fetchDomains();
  } else {
    domains.value = [];
    loadingDomains.value = false;
  }
});
</script>

<style scoped>
.domains-premium {
  --verde:var(--primary);--verde-d:var(--brand-dark);--verde-dim:color-mix(in srgb, var(--primary) 10%, transparent);--verde-border:color-mix(in srgb, var(--primary) 30%, var(--border));
  --surface:var(--card);--surface2:var(--muted);--text:var(--foreground);--text-2:var(--card-foreground);--text-3:var(--muted-foreground);
  --sh-sm:var(--shadow-soft);
  --radius:var(--radius-xl);--radius-sm:var(--radius-lg);
  color:var(--foreground);
}
.page-wrap{padding:0 0 48px;width:100%;max-width:none}
.page-eyebrow,.guide-eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-3);margin-bottom:4px}
.page-title{font-family:var(--font-display);font-size:26px;font-weight:650;color:var(--text);letter-spacing:-.3px;line-height:1.2}
.page-sub{font-size:13px;color:var(--text-3);margin-top:4px}
.guide-card{padding:18px}
.guide-row{display:grid;grid-template-columns:minmax(0,9fr) minmax(0,2fr);gap:12px;align-items:stretch}
.guide-row > .list-card{height:100%}
.guide-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px}
.guide-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.guide-block{border:1px solid color-mix(in srgb, var(--border) 55%, transparent);border-radius:var(--radius-sm);background:var(--surface2);padding:14px}
.guide-block-title{font-size:12px;font-weight:800;color:var(--text);margin-bottom:8px}
.guide-list{display:grid;gap:8px;font-size:13px;color:var(--text-2);line-height:1.5}
.guide-footer{margin-top:12px;font-size:12px;color:var(--text-3);line-height:1.55}
.main-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.45fr);gap:12px;align-items:start}
.list-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px;box-shadow:var(--sh-sm)}
.card-title{font-family:var(--font-display);font-size:16px;font-weight:650;color:var(--text);letter-spacing:-.2px}
.field-label{font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--text-3)}
.helper-text{font-size:12px;color:var(--text-3)}
.inline-check{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-2)}
.fi{padding:10px 11px;border:1px solid var(--input);border-radius:var(--radius-sm);font-family:inherit;font-size:13px;color:var(--text);background:var(--background);outline:none;transition:border-color .15s,box-shadow .15s;width:100%}
.fi:focus{border-color:var(--ring);box-shadow:0 0 0 3px color-mix(in srgb, var(--ring) 18%, transparent)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:9px 14px;border-radius:var(--radius-lg);font-size:13px;font-weight:700;cursor:pointer;border:1px solid transparent;font-family:inherit;transition:all .15s;white-space:nowrap;line-height:1.3}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-p{background:var(--verde);color:var(--primary-foreground);box-shadow:var(--shadow-soft)}
.btn-p:hover{background:var(--verde-d)}
.btn-o{background:var(--background);border-color:var(--border);color:var(--text)}
.btn-o:hover{background:var(--accent)}
.btn-danger{background:color-mix(in srgb, var(--destructive) 8%, var(--card));border-color:color-mix(in srgb, var(--destructive) 28%, var(--border));color:var(--destructive)}
.btn-danger:hover{background:color-mix(in srgb, var(--destructive) 13%, var(--card))}
.btn:disabled{cursor:not-allowed;opacity:.55}
.ok-msg{font-size:12px;color:var(--status-success-foreground);font-weight:600}
.err-msg{font-size:12px;color:var(--destructive);font-weight:600}
.tips-card{padding-top:14px;padding-bottom:14px}
.tips-summary{font-size:13px;font-weight:700;color:var(--text-2)}
.list-header{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:12px}
.favicon-card-layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:16px;align-items:start}
.favicon-card-copy{display:flex;flex-direction:column;min-height:100%}
.favicon-card-copy .mt-3{margin-top:20px !important}
.favicon-card-copy .btn{width:100%;justify-content:center}
.favicon-upload-compact{max-width:280px}
.favicon-upload-compact :deep(.flex.h-full.flex-col.gap-2){gap:6px}
.favicon-upload-compact :deep(.flex.flex-1.flex-col.rounded-xl.border.border-slate-200.p-3){padding:10px}
.favicon-upload-compact :deep(.mb-3 > .flex.max-h-\[320px\].min-h-\[220px\].w-full.items-center.justify-center.overflow-hidden.rounded-lg.border.border-slate-200.bg-slate-50){
  width:100% !important;
  height:88px !important;
  min-height:88px !important;
  max-height:88px !important;
  border-radius:12px !important;
}
.favicon-upload-compact :deep(.image-upload-preview){
  width:100% !important;
  height:88px !important;
  min-height:88px !important;
  object-fit:contain !important;
}
@media (max-width: 768px){
  .favicon-card-layout{grid-template-columns:1fr}
  .favicon-upload-compact{max-width:100%}
}
.alert-error{border:1px solid color-mix(in srgb, var(--destructive) 25%, var(--border));background:color-mix(in srgb, var(--destructive) 8%, var(--card));color:var(--destructive);border-radius:10px;padding:10px;font-size:12px}
.alert-muted{border:1px solid var(--border);background:var(--surface2);color:var(--text-2);border-radius:10px;padding:12px;font-size:13px}
.alert-empty{border:1px dashed var(--border);background:var(--surface2);color:var(--text-3);border-radius:10px;padding:14px;font-size:13px}
.domain-list{display:flex;flex-direction:column;gap:0}
.domain-item{border-top:1px solid color-mix(in srgb, var(--border) 38%, transparent);background:transparent;padding:18px 2px;transition:.15s}
.domain-item:first-child{border-top:0}
.domain-item:hover{background:color-mix(in srgb, var(--accent) 42%, transparent)}
.domain-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.domain-ident{display:flex;align-items:center;flex-wrap:wrap;gap:6px}
.domain-host{font-size:18px;font-weight:800;color:var(--text);letter-spacing:-.2px}
.domain-meta{font-size:12px;color:var(--text-3);margin-top:4px}
.status-row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:8px}
.status-label{font-size:12px;font-weight:700;color:var(--text-2)}
.step-title{font-size:12px;font-weight:700;color:var(--text-2);margin-top:12px}
.steps-grid{margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.step-card{border:1px solid color-mix(in srgb, var(--border) 62%, transparent);border-radius:var(--radius-sm);background:var(--background);padding:14px}
.step-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3)}
.step-name{font-size:12px;font-weight:700;color:var(--text);margin-top:2px}
.step-meta{margin-top:6px;display:grid;gap:2px}
.step-meta p{font-size:12px;color:var(--text-2);line-height:1.35;min-width:0}
.step-meta span{color:var(--text-3);font-weight:600}
.step-meta strong{font-weight:700;color:var(--text)}
.copy-row{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:8px 10px;border-top:1px solid color-mix(in srgb, var(--border) 34%, transparent)}
.copy-row:first-child{border-top:0}
.copy-icon-btn{display:inline-flex;align-items:center;justify-content:center;height:30px;width:30px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--card);color:var(--text-2);flex-shrink:0;transition:.15s}
.copy-icon-btn:hover{background:var(--accent);color:var(--text)}
.step-hint{margin-top:6px;font-size:11px;color:var(--text-3)}
.copy-ok{margin-top:4px;font-size:11px;color:var(--status-success-foreground);font-weight:700}
.domain-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;line-height:1.4}
.badge-green{background:var(--status-success);color:var(--status-success-foreground);border:1px solid color-mix(in srgb, var(--status-success-foreground) 24%, var(--border))}
.badge-info{background:var(--status-info);color:var(--status-info-foreground);border:1px solid color-mix(in srgb, var(--status-info-foreground) 22%, var(--border))}
.badge-muted{background:var(--status-neutral);color:var(--status-neutral-foreground);border:1px solid var(--border)}
.badge-warn{background:var(--status-warning);color:var(--status-warning-foreground);border:1px solid color-mix(in srgb, var(--status-warning-foreground) 22%, var(--border))}
.badge-ssl{background:color-mix(in srgb, var(--chart-6) 10%, var(--card));color:var(--chart-6);border:1px solid color-mix(in srgb, var(--chart-6) 25%, var(--border))}
@media(max-width:1000px){.main-grid,.guide-grid,.guide-row{grid-template-columns:1fr}}
@media(max-width:900px){.page-wrap{padding:0 0 32px}}
@media(max-width:640px){.steps-grid{grid-template-columns:1fr}}

/* Redesign: domínios */
.page-wrap { display: flex; flex-direction: column; gap: 16px; }
.dm-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.dm-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.dm-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; color: var(--foreground); }
.dm-sub { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.dm-plan { flex-shrink: 0; border-radius: 999px; background: var(--status-violet); padding: 2px 10px; font-size: 12px; font-weight: 600; color: var(--status-violet-foreground); }
.dm-alert { border-radius: 16px; background: var(--status-warning); padding: 16px; color: var(--status-warning-foreground); }
.dm-grid { display: grid; grid-template-columns: minmax(0, 1fr) 420px; align-items: start; gap: 16px; }
.dm-side { display: flex; flex-direction: column; gap: 16px; }
.dm-card { border-radius: 20px; background: var(--card); padding: 20px 22px 22px; box-shadow: var(--shadow-card); }
.dm-card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
.dm-card-head-plain { border-bottom: 0; padding-bottom: 0; }
.dm-card-head h2 { font-family: var(--font-display); font-size: 17px; font-weight: 600; color: var(--foreground); }
.dm-card-head p { margin-top: 1px; font-size: 13px; color: var(--muted-foreground); }
.dm-btn-ghost, .dm-btn-primary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; }
.dm-btn-ghost { background: var(--muted); color: var(--foreground); }
.dm-btn-ghost:hover:not(:disabled) { background: var(--accent); color: var(--accent-foreground); }
.dm-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.dm-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); }
.dm-btn-ghost:disabled, .dm-btn-primary:disabled { cursor: not-allowed; opacity: 0.55; }
.dm-btn-ghost svg, .dm-btn-primary svg { width: 15px; height: 15px; }
.dm-btn-sm { height: 34px; padding: 0 14px; font-size: 13px; }
.dm-btn-block { width: 100%; }
.dm-icon-btn { display: grid; place-items: center; width: 32px; height: 32px; flex-shrink: 0; border-radius: 999px; background: var(--muted); color: var(--muted-foreground); }
.dm-icon-btn svg { width: 16px; height: 16px; }
.dm-empty { padding: 24px 0 8px; font-size: 13.5px; color: var(--muted-foreground); }
.dm-domain { border-top: 1px solid var(--border); padding: 16px 0; }
.dm-domain:first-of-type { border-top: 0; }
.dm-domain:last-child { padding-bottom: 0; }
.dm-domain-top { display: flex; align-items: center; gap: 12px; }
.dm-globe { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 999px; }
.dm-globe svg { width: 18px; height: 18px; }
.dm-globe.is-on { background: var(--status-success); color: var(--status-success-foreground); }
.dm-globe.is-pending { background: var(--status-warning); color: var(--status-warning-foreground); }
.dm-domain-main { min-width: 0; flex: 1; }
.dm-domain-title { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.dm-domain-title b { font-family: var(--font-display); font-size: 17px; font-weight: 600; color: var(--foreground); overflow-wrap: anywhere; }
.dm-domain-meta { margin-top: 2px; font-size: 13px; color: var(--muted-foreground); }
.dm-pill { border-radius: 999px; padding: 1px 8px; font-size: 11.5px; font-weight: 600; }
.dm-pill.is-success { background: var(--status-success); color: var(--status-success-foreground); }
.dm-pill.is-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.dm-pill.is-info { background: var(--status-violet); color: var(--status-violet-foreground); }
.dm-pill.is-muted { background: var(--muted); color: var(--muted-foreground); }
.dm-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 0 52px; }
.dm-chip { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border-radius: 999px; font-size: 12.5px; font-weight: 600; }
.dm-chip svg { width: 13px; height: 13px; }
.dm-chip.is-ok { background: var(--status-success); color: var(--status-success-foreground); }
.dm-chip.is-wait { background: var(--status-warning); color: var(--status-warning-foreground); }
.dm-chip.is-neutral { background: var(--muted); color: var(--foreground); }
.dm-chip.is-action { background: var(--muted); color: var(--foreground); }
.dm-chip.is-action:hover:not(:disabled) { background: var(--accent); color: var(--accent-foreground); }
.dm-chip.is-action:disabled { cursor: not-allowed; opacity: 0.6; }
.dm-dns { margin: 14px 0 0 52px; border-radius: 16px; background: var(--muted); padding: 14px; }
.dm-dns-title { font-size: 13.5px; font-weight: 600; color: var(--foreground); }
.dm-dns table { width: 100%; margin-top: 8px; border-collapse: collapse; font-size: 13px; }
.dm-dns th { border-bottom: 1px solid var(--border); padding: 6px 10px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.dm-dns td { border-bottom: 1px solid var(--border); padding: 9px 10px; color: var(--foreground); }
.dm-dns tr:last-child td { border-bottom: 0; }
.dm-dns code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px; overflow-wrap: anywhere; }
.dm-copy { display: inline-flex; align-items: center; gap: 4px; height: 26px; padding: 0 10px; border-radius: 999px; background: var(--card); font-size: 12px; font-weight: 600; color: var(--foreground); }
.dm-copy svg { width: 12px; height: 12px; }
.dm-copy:disabled { opacity: 0.5; }
.dm-dns-note { margin-top: 8px; font-size: 12px; color: var(--muted-foreground); }
.dm-msg { margin-top: 10px; border-radius: 12px; padding: 8px 12px; font-size: 12.5px; }
.dm-msg.is-error { background: var(--status-danger); color: var(--status-danger-foreground); }
.dm-msg.is-ok { background: var(--status-success); color: var(--status-success-foreground); }
.dm-menu-wrap { position: relative; }
.dm-menu { position: absolute; top: calc(100% + 6px); right: 0; z-index: 30; display: flex; min-width: 210px; flex-direction: column; border-radius: 14px; background: var(--popover); padding: 6px; box-shadow: var(--shadow-elegant); }
.dm-menu button { border-radius: 10px; padding: 8px 10px; text-align: left; font-size: 13px; color: var(--popover-foreground); }
.dm-menu button:hover:not(:disabled) { background: var(--muted); }
.dm-menu button:disabled { cursor: not-allowed; opacity: 0.45; }
.dm-menu button.danger { color: var(--status-danger-foreground); }
.dm-form { display: flex; flex-direction: column; gap: 14px; margin-top: 14px; }
.dm-input { width: 100%; height: 42px; border: 0; border-radius: 12px; background: var(--muted); padding: 0 12px; font-size: 13.5px; color: var(--foreground); outline: none; }
.dm-input:focus { box-shadow: 0 0 0 2px var(--ring); }
.dm-toggle-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.dm-toggle-row b { display: block; font-size: 13.5px; font-weight: 600; color: var(--foreground); }
.dm-toggle-row small { display: block; font-size: 12px; color: var(--muted-foreground); }
.dm-switch { position: relative; width: 36px; height: 20px; flex-shrink: 0; border-radius: 999px; background: var(--muted); box-shadow: inset 0 0 0 1px var(--border); transition: background 0.15s; }
.dm-switch i { position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 999px; background: #fff; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25); transition: transform 0.15s; }
.dm-switch.on { background: var(--primary); box-shadow: none; }
.dm-switch.on i { transform: translateX(16px); }
.dm-favicon { margin: 14px 0 10px; border: 1px dashed var(--border); border-radius: 16px; padding: 12px 14px; }
/* Campo de imagem em linha, no formato da proposta: ícone pequeno, texto e botões redondos */
.dm-favicon :deep(.image-upload-field > div:first-of-type) { gap: 12px; border: 0; padding: 0; }
.dm-favicon :deep(.image-upload-field button.h-16) { width: 44px; height: 44px; border: 0; border-radius: 12px; background: #0b1512; }
.dm-favicon :deep(.image-upload-field button.h-16 img) { object-fit: contain; padding: 6px; }
.dm-favicon :deep(.image-upload-field button.h-16 span) { color: rgba(255, 255, 255, 0.7); }
.dm-favicon :deep(.image-upload-field .w-\[220px\]) { width: auto; gap: 6px; }
.dm-favicon :deep(.image-upload-field label.h-10) { width: auto; height: 34px; border: 0; border-radius: 999px; background: var(--muted); padding: 0 14px; font-size: 13px; color: var(--foreground); }
.dm-favicon :deep(.image-upload-field label.h-10:hover) { background: var(--accent); color: var(--accent-foreground); }
.dm-favicon :deep(.image-upload-field button.w-\[96px\]) { width: auto; height: 34px; border: 0; border-radius: 999px; padding: 0 12px; font-size: 13px; }
.dm-favicon :deep(.image-upload-field button.w-\[96px\].text-transparent) { display: none; }
.dm-favicon :deep(.image-upload-field p.text-xs) { font-size: 12.5px; color: var(--muted-foreground); }
.dm-favicon.is-disabled { pointer-events: none; opacity: 0.55; }
.dm-hint { margin-bottom: 10px; font-size: 12.5px; color: var(--muted-foreground); }
@media (max-width: 1100px) { .dm-grid { grid-template-columns: 1fr; } }
@media (max-width: 640px) {
  .dm-head { flex-direction: column; align-items: flex-start; }
  .dm-chips, .dm-dns { margin-left: 0; }
  .dm-domain-top { flex-wrap: wrap; }
}
</style>

