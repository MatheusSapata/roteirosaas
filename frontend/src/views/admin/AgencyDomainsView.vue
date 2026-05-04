<template>
  <div v-if="isBootstrappingDomains" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>
  <div v-else class="relative w-full domains-premium">
    <div class="page-wrap">
      <div class="space-y-1">
        <h1 class="page-title">{{ viewCopy.hero.title }}</h1>
        <p class="page-sub">Conecte seu domínio para usar sua marca nas páginas.</p>
      </div>

      <div
        class="space-y-6"
        :class="{ 'select-none opacity-60 blur-sm': !domainsAllowed }"
      >
        <div v-if="!currentAgencyId" class="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
          <p class="font-semibold">{{ viewCopy.noAgency.title }}</p>
          <p class="mt-1 text-sm">{{ viewCopy.noAgency.helper }}</p>
        </div>

        <div v-else class="main-grid">
          <section class="space-y-3">
            <div class="list-card">
              <h2 class="card-title">{{ viewCopy.form.title }}</h2>
              <form class="mt-4 space-y-3" @submit.prevent="createDomain">
                <div class="space-y-1.5">
                  <label class="field-label">{{ viewCopy.form.hostLabel }}</label>
                  <input
                    v-model="form.host"
                    type="text"
                    :placeholder="viewCopy.form.hostPlaceholder"
                    class="fi"
                    :disabled="creating || loadingDomains"
                  />
                  <p class="helper-text">Use apenas o domínio</p>
                </div>
                <label class="inline-check">
                  <input
                    v-model="form.is_primary"
                    type="checkbox"
                    class="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                    :disabled="creating || loadingDomains"
                  />
                  {{ viewCopy.form.primaryOption }}
                </label>
                <div class="space-y-2">
                  <button type="submit" class="btn btn-p w-full justify-center" :disabled="creating || loadingDomains">
                    <span v-if="creating">{{ viewCopy.form.submitSaving }}</span>
                    <span v-else>{{ viewCopy.form.submitLabel }}</span>
                  </button>
                  <p v-if="formError" class="err-msg">{{ formError }}</p>
                  <p v-if="formSuccess" class="ok-msg">{{ formSuccess }}</p>
                </div>
              </form>
            </div>

            <section class="list-card tips-card">
              <p class="tips-summary">{{ viewCopy.tips.title }}</p>
              <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
                <li>{{ viewCopy.tips.subdomainPrefix }} <span class="font-mono">roteiros.suaagencia.com</span> {{ viewCopy.tips.subdomainSuffix }}</li>
                <li>{{ viewCopy.tips.protocolPrefix }} <span class="font-mono">http://</span> {{ viewCopy.tips.protocolSuffix }}</li>
                <li>{{ viewCopy.tips.reserved(platformExample) }}</li>
              </ul>
            </section>
          </section>

          <section class="list-card">
            <div class="list-header">
              <div>
                <h2 class="card-title">{{ viewCopy.list.title }}</h2>
                <p class="text-sm text-slate-500">
                  {{ viewCopy.list.currentAgencyLabel }} <span class="font-semibold text-slate-700">{{ currentAgencyName }}</span>
                </p>
              </div>
              <button
                type="button"
                class="btn btn-o btn-sm"
                @click="fetchDomains"
                :disabled="loadingDomains"
              >
                {{ viewCopy.list.refresh }}
              </button>
            </div>

            <div v-if="listError" class="alert-error">
              {{ listError }}
            </div>
            <div v-if="loadingDomains" class="alert-muted">
              {{ viewCopy.list.loading }}
            </div>
            <div v-else-if="!domains.length" class="alert-empty">
              {{ viewCopy.list.empty }}
            </div>

            <div v-else class="domain-list">
              <article v-for="domain in domains" :key="domain.id" class="domain-item">
                <div class="domain-head">
                  <div class="domain-ident">
                    <p class="domain-host">🌐 {{ domain.host }}</p>
                    <span :class="domain.is_active ? 'badge badge-green' : 'badge badge-muted'">
                      {{ domain.is_active ? viewCopy.statuses.active : viewCopy.statuses.inactive }}
                    </span>
                    <span v-if="domain.is_primary" class="badge badge-info">{{ viewCopy.statuses.primary }}</span>
                  </div>
                  <p class="domain-meta">{{ viewCopy.domainInfo.createdAt }} {{ formatDate(domain.created_at) }}</p>
                </div>

                <div class="status-row">
                  <span class="status-label">Status:</span>
                  <span class="badge badge-warn">{{ domain.is_verified ? "DNS verificado" : "DNS pendente" }}</span>
                  <span :class="domain.ssl_status === 'issued' ? 'badge badge-green' : 'badge badge-ssl'">
                    {{ domain.ssl_status === "issued" ? "SSL pronto" : "SSL aguardando" }}
                  </span>
                </div>

                <div class="step-title">Configuração necessária</div>
                <div class="steps-grid">
                  <div class="step-card">
                    <p class="step-label">Passo 1</p>
                    <p class="step-name">Adicionar registro TXT</p>
                    <div class="step-meta">
                      <div class="copy-row">
                        <p><span>Host:</span> <strong>{{ domain.instructions?.verification.host || "-" }}</strong></p>
                        <button type="button" class="copy-icon-btn" @click="copyText(domain.instructions?.verification.host || '', `txt-host-${domain.id}`)" aria-label="Copiar host TXT">
                          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                            <path d="M5 15V6a2 2 0 0 1 2-2h9"></path>
                          </svg>
                        </button>
                      </div>
                      <div class="copy-row">
                        <p><span>Valor:</span> <strong>{{ domain.verification_token || "-" }}</strong></p>
                        <button type="button" class="copy-icon-btn" @click="copyText(domain.verification_token, `txt-value-${domain.id}`)" aria-label="Copiar valor TXT">
                          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                            <path d="M5 15V6a2 2 0 0 1 2-2h9"></path>
                          </svg>
                        </button>
                      </div>
                      <div class="copy-row">
                        <p><span>FQDN:</span> <strong>{{ domain.instructions?.verification.fqdn || "-" }}</strong></p>
                        <button type="button" class="copy-icon-btn" @click="copyText(domain.instructions?.verification.fqdn || '', `txt-fqdn-${domain.id}`)" aria-label="Copiar FQDN TXT">
                          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                            <path d="M5 15V6a2 2 0 0 1 2-2h9"></path>
                          </svg>
                        </button>
                      </div>
                    </div>
                    <p v-if="copiedState[`txt-host-${domain.id}`] || copiedState[`txt-value-${domain.id}`] || copiedState[`txt-fqdn-${domain.id}`]" class="copy-ok">Copiado!</p>
                  </div>
                  <div class="step-card">
                    <p class="step-label">Passo 2</p>
                    <p class="step-name">Configurar {{ domain.instructions?.target.type || "CNAME" }}</p>
                    <div class="step-meta">
                      <div class="copy-row">
                        <p><span>Host:</span> <strong>{{ domain.instructions?.target.host || "-" }}</strong></p>
                        <button type="button" class="copy-icon-btn" @click="copyText(domain.instructions?.target.host || '', `target-host-${domain.id}`)" aria-label="Copiar host apontamento">
                          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                            <path d="M5 15V6a2 2 0 0 1 2-2h9"></path>
                          </svg>
                        </button>
                      </div>
                      <div class="copy-row">
                        <p><span>Valor:</span> <strong>{{ domain.instructions?.target.value || "-" }}</strong></p>
                        <button type="button" class="copy-icon-btn" @click="copyText(domain.instructions?.target.value || '', `target-value-${domain.id}`)" aria-label="Copiar valor apontamento">
                          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                            <path d="M5 15V6a2 2 0 0 1 2-2h9"></path>
                          </svg>
                        </button>
                      </div>
                      <p><span>Tipo:</span> <strong>{{ domain.instructions?.target.type || "-" }}</strong></p>
                    </div>
                    <p class="step-hint" v-if="domain.instructions?.target.type === 'CNAME'">Use apenas "www" como host/subdomínio.</p>
                    <p v-if="copiedState[`target-host-${domain.id}`] || copiedState[`target-value-${domain.id}`]" class="copy-ok">Copiado!</p>
                  </div>
                </div>

                <div v-if="domain.ssl_last_error" class="alert-error mt-3">
                  {{ domain.ssl_last_error }}
                </div>
                <div v-if="domainMessages[domain.id]" class="ok-msg mt-2">
                  {{ domainMessages[domain.id] }}
                </div>

                <div class="domain-actions">
                  <button type="button" class="btn btn-p btn-sm" :disabled="isActionRunning(domain.id)" @click="verifyDomain(domain)">
                    {{ isActionRunning(domain.id, 'verify') ? viewCopy.actions.verifying : viewCopy.actions.verify }}
                  </button>
                  <button
                    v-if="!domain.is_active"
                    type="button"
                    class="btn btn-o btn-sm"
                    :disabled="isActionRunning(domain.id) || !domain.is_verified"
                    @click="activateDomain(domain)"
                  >
                    {{ isActionRunning(domain.id, 'activate') ? viewCopy.actions.activating : viewCopy.actions.activate }}
                  </button>
                  <button
                    v-else
                    type="button"
                    class="btn btn-o btn-sm"
                    :disabled="isActionRunning(domain.id)"
                    @click="deactivateDomain(domain)"
                  >
                    {{ isActionRunning(domain.id, 'deactivate') ? viewCopy.actions.deactivating : viewCopy.actions.deactivate }}
                  </button>
                  <button
                    type="button"
                    class="btn btn-o btn-sm"
                    :disabled="isActionRunning(domain.id) || domain.is_primary"
                    @click="setPrimary(domain)"
                  >
                    {{ isActionRunning(domain.id, 'primary') ? viewCopy.actions.primarying : viewCopy.actions.setPrimary }}
                  </button>
                  <button
                    type="button"
                    class="btn btn-danger btn-sm"
                    :disabled="isActionRunning(domain.id) || domain.is_active"
                    @click="removeDomain(domain)"
                  >
                    {{ isActionRunning(domain.id, 'delete') ? viewCopy.actions.deleting : viewCopy.actions.delete }}
                  </button>
                </div>
              </article>
            </div>
          </section>
        </div>

        <section class="list-card guide-card">
          <div class="guide-head">
            <div>
              <p class="guide-eyebrow">{{ viewCopy.dnsGuide.title }}</p>
              <h2 class="card-title">{{ viewCopy.dnsGuide.subdomainTitle }}</h2>
            </div>
          </div>
          <div class="guide-grid">
            <div class="guide-block">
              <p class="guide-block-title">{{ viewCopy.dnsGuide.subdomainTitle }}</p>
              <ul class="guide-list">
                <li>{{ viewCopy.dnsGuide.subdomainHostPrefix }} <span class="font-mono">www.suaagencia.com</span> {{ viewCopy.dnsGuide.subdomainHostConnector }} <span class="font-mono">roteiros.suaagencia.com</span>.</li>
                <li>{{ viewCopy.dnsGuide.subdomainCname }} <span class="font-mono">roteiroonline.com</span>.</li>
                <li>{{ viewCopy.dnsGuide.subdomainTxt }}</li>
              </ul>
            </div>
            <div class="guide-block">
              <p class="guide-block-title">{{ viewCopy.dnsGuide.apexTitle }}</p>
              <ul class="guide-list">
                <li>{{ viewCopy.dnsGuide.apexRecord }}</li>
                <li>{{ viewCopy.dnsGuide.apexValuePrefix }}<span class="font-mono">{{ apexTargetExample }}</span>{{ viewCopy.dnsGuide.apexValueSuffix }}</li>
                <li>{{ viewCopy.dnsGuide.apexTxt }}</li>
              </ul>
            </div>
          </div>
          <p class="guide-footer">{{ viewCopy.dnsGuide.footer }}</p>
        </section>
      </div>
    </div>
    <div
      v-if="!domainsAllowed"
      class="pointer-events-auto absolute inset-0 z-10 flex items-center justify-center bg-black/80 px-4 text-center text-white backdrop-blur-sm"
    >
      <div class="max-w-md rounded-3xl bg-[#202020] p-6 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-300">{{ viewCopy.overlay.eyebrow }}</p>
        <h2 class="mt-2 text-2xl font-bold text-white">{{ viewCopy.overlay.title }}</h2>
        <p class="mt-2 text-sm text-slate-200">
          {{ viewCopy.overlay.description }}
        </p>
        <button
          type="button"
          class="mt-4 w-full rounded-full bg-[#3EBD59] px-4 py-3 text-sm font-semibold text-white shadow transition hover:bg-[#34a04c]"
          @click="goToPlans"
        >
          {{ viewCopy.overlay.cta }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
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
    if (newId && domainsAllowed.value) {
      await fetchDomains();
    } else {
      domains.value = [];
    }
  }
);

watch(domainsAllowed, allowed => {
  if (allowed) {
    fetchDomains();
  } else {
    domains.value = [];
    loadingDomains.value = false;
  }
});
</script>

<style scoped>
.domains-premium {
  --verde:#3DCC5F;--verde-d:#2EAD4C;--verde-dim:rgba(61,204,95,.10);--verde-border:rgba(61,204,95,.22);
  --surface:#fff;--surface2:#F5F7F5;--border:#E4E9E4;--text:#111A14;--text-2:#4A5E4A;--text-3:#8A9E8A;
  --sh-sm:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03);
  --radius:12px;--radius-sm:8px;
}
.page-wrap{padding:28px 32px 64px;width:100%;max-width:1380px}
.page-title{font-size:24px;font-weight:800;color:var(--text);letter-spacing:-.3px;line-height:1.2}
.page-sub{font-size:13px;color:var(--text-3);margin-top:4px}
.guide-card{padding:18px}
.guide-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px}
.guide-eyebrow{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--text-3);margin-bottom:4px}
.guide-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.guide-block{border:1px solid var(--border);border-radius:10px;background:var(--surface2);padding:14px}
.guide-block-title{font-size:12px;font-weight:800;color:var(--text);margin-bottom:8px}
.guide-list{display:grid;gap:8px;font-size:13px;color:var(--text-2);line-height:1.5}
.guide-footer{margin-top:12px;font-size:12px;color:var(--text-3);line-height:1.55}
.main-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.45fr);gap:12px;align-items:start}
.list-card{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);padding:16px;box-shadow:var(--sh-sm)}
.card-title{font-size:16px;font-weight:800;color:var(--text);letter-spacing:-.2px}
.field-label{font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--text-3)}
.helper-text{font-size:12px;color:var(--text-3)}
.inline-check{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-2)}
.fi{padding:9px 11px;border:1.5px solid var(--border);border-radius:var(--radius-sm);font-family:inherit;font-size:13px;color:var(--text);background:var(--surface);outline:none;transition:border-color .15s;width:100%}
.fi:focus{border-color:var(--verde-border)}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;font-size:13px;font-weight:700;cursor:pointer;border:none;font-family:inherit;transition:all .15s;white-space:nowrap;line-height:1.3}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-p{background:var(--verde);color:#0F1F14}
.btn-p:hover{background:var(--verde-d)}
.btn-o{background:#fff;border:1px solid var(--border);color:var(--text-2)}
.btn-o:hover{border-color:#cbd6cb;color:var(--text)}
.btn-danger{background:#fff6f6;border:1px solid #f3caca;color:#c0392b}
.btn-danger:hover{background:#ffeaea}
.ok-msg{font-size:12px;color:#1a7a35;font-weight:600}
.err-msg{font-size:12px;color:#c0392b;font-weight:600}
.tips-card{padding-top:14px;padding-bottom:14px}
.tips-summary{font-size:13px;font-weight:700;color:var(--text-2)}
.list-header{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:12px}
.alert-error{border:1px solid #fecaca;background:#fef2f2;color:#b91c1c;border-radius:10px;padding:10px;font-size:12px}
.alert-muted{border:1px solid var(--border);background:var(--surface2);color:var(--text-2);border-radius:10px;padding:12px;font-size:13px}
.alert-empty{border:1px dashed var(--border);background:var(--surface2);color:var(--text-3);border-radius:10px;padding:14px;font-size:13px}
.domain-list{display:flex;flex-direction:column;gap:12px}
.domain-item{border:1px solid var(--border);border-radius:12px;background:var(--surface2);padding:16px;transition:.15s}
.domain-item:hover{background:#eef3ee}
.domain-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.domain-ident{display:flex;align-items:center;flex-wrap:wrap;gap:6px}
.domain-host{font-size:18px;font-weight:800;color:var(--text);letter-spacing:-.2px}
.domain-meta{font-size:12px;color:var(--text-3);margin-top:4px}
.status-row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:8px}
.status-label{font-size:12px;font-weight:700;color:var(--text-2)}
.step-title{font-size:12px;font-weight:700;color:var(--text-2);margin-top:12px}
.steps-grid{margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.step-card{border:1px solid var(--border);border-radius:10px;background:#fff;padding:14px}
.step-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3)}
.step-name{font-size:12px;font-weight:700;color:var(--text);margin-top:2px}
.step-meta{margin-top:6px;display:grid;gap:2px}
.step-meta p{font-size:12px;color:var(--text-2);line-height:1.35;min-width:0}
.step-meta span{color:var(--text-3);font-weight:600}
.step-meta strong{font-weight:700;color:var(--text)}
.copy-row{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--surface2)}
.copy-icon-btn{display:inline-flex;align-items:center;justify-content:center;height:30px;width:30px;border:1px solid var(--border);border-radius:999px;background:#fff;color:var(--text-2);flex-shrink:0;transition:.15s}
.copy-icon-btn:hover{border-color:#cbd6cb;color:var(--text)}
.step-hint{margin-top:6px;font-size:11px;color:var(--text-3)}
.copy-ok{margin-top:4px;font-size:11px;color:#1a7a35;font-weight:700}
.domain-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;line-height:1.4}
.badge-green{background:var(--verde-dim);color:#1A7A35;border:1.5px solid var(--verde-border)}
.badge-info{background:#e8f3ff;color:#1d5d99;border:1px solid #cde4ff}
.badge-muted{background:#e9eeea;color:#5f6f5f;border:1px solid var(--border)}
.badge-warn{background:#fff1da;color:#ad6a00;border:1px solid #ffd9a1}
.badge-ssl{background:#f1eefb;color:#5f4aa6;border:1px solid #ded6fb}
@media(max-width:1000px){.main-grid,.guide-grid{grid-template-columns:1fr}}
@media(max-width:900px){.page-wrap{padding:20px 16px 40px}}
@media(max-width:640px){.steps-grid{grid-template-columns:1fr}}
</style>

