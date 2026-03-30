<template>
  <div class="relative w-full">
    <div
      class="space-y-6"
      :class="{ 'select-none opacity-60 blur-sm': !domainsAllowed }"
    >
      <div class="space-y-2 md:pl-2">
        <h1 class="text-2xl font-bold text-slate-900">{{ viewCopy.hero.title }}</h1>
        <p class="mt-2 text-sm text-slate-600">
          {{ viewCopy.hero.description(platformExample) }}
        </p>
      </div>

    <div v-if="!currentAgencyId" class="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
      <p class="font-semibold">{{ viewCopy.noAgency.title }}</p>
      <p class="text-sm mt-1">{{ viewCopy.noAgency.helper }}</p>
    </div>

    <div v-else class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
        <h2 class="text-lg font-semibold text-slate-900">{{ viewCopy.form.title }}</h2>
        <p class="text-sm text-slate-500">
          {{ viewCopy.form.examplePrefix }}
          <span class="font-mono">www.suaagencia.com</span>&nbsp;{{ viewCopy.form.exampleOr }}&nbsp;<span class="font-mono">roteiros.suaagencia.com</span>
        </p>
        <form class="mt-4 space-y-4" @submit.prevent="createDomain">
          <div>
            <label class="text-sm font-medium text-slate-700">{{ viewCopy.form.hostLabel }}</label>
            <input
              v-model="form.host"
              type="text"
              :placeholder="viewCopy.form.hostPlaceholder"
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
            {{ viewCopy.form.primaryOption }}
          </label>
          <div class="space-y-2 text-sm">
<button
              type="submit"
              class="inline-flex w-full items-center justify-center rounded-xl bg-[#3EBD59] px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-[#34a04c] disabled:cursor-not-allowed disabled:bg-[#3EBD59]/60"
              :disabled="creating || loadingDomains"
            >
              <span v-if="creating" class="animate-pulse">{{ viewCopy.form.submitSaving }}</span>
              <span v-else>{{ viewCopy.form.submitLabel }}</span>
            </button>
            <p v-if="formError" class="text-sm text-red-600">{{ formError }}</p>
            <p v-if="formSuccess" class="text-sm text-emerald-600">{{ formSuccess }}</p>
          </div>
        </form>
        <div class="mt-6 rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">
          <p class="font-semibold text-slate-800">{{ viewCopy.tips.title }}</p>
          <ul class="mt-2 list-disc space-y-1 pl-5">
            <li>
              {{ viewCopy.tips.subdomainPrefix }}
              <span class="font-mono">roteiros.suaagencia.com</span>
              {{ viewCopy.tips.subdomainSuffix }}
            </li>
            <li>
              {{ viewCopy.tips.protocolPrefix }} <span class="font-mono">http://</span> {{ viewCopy.tips.protocolSuffix }}
            </li>
            <li>{{ viewCopy.tips.reserved(platformExample) }}</li>
          </ul>
        </div>
      </div>

      <div class="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100 dark:bg-[#202020] dark:ring-slate-800">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">{{ viewCopy.list.title }}</h2>
            <p class="text-sm text-slate-500">
              {{ viewCopy.list.currentAgencyLabel }}&nbsp;<span class="font-semibold text-slate-700">{{ currentAgencyName }}</span>
            </p>
          </div>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:border-slate-300 dark:border-slate-600 dark:text-slate-200 dark:hover:border-slate-500"
            @click="fetchDomains"
            :disabled="loadingDomains"
          >
            {{ viewCopy.list.refresh }}
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
          {{ viewCopy.list.loading }}
        </div>
        <div
          v-else-if="!domains.length"
          class="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-400"
        >
          {{ viewCopy.list.empty }}
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
                <p class="text-xs text-slate-500">{{ viewCopy.domainInfo.createdAt }} {{ formatDate(domain.created_at) }}</p>
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
                <p class="font-semibold text-slate-900">{{ viewCopy.domainInfo.verificationTitle }}</p>
                <p class="text-xs text-slate-500">
                  {{ viewCopy.domainInfo.hostLabel }}
                  <span class="font-mono text-slate-800">{{ domain.instructions?.verification.host }}</span>
                </p>
                <p class="text-xs text-slate-500">
                  {{ viewCopy.domainInfo.valueLabel }}
                  <span class="font-mono text-slate-800">{{ domain.verification_token }}</span>
                </p>
                <p class="text-xs text-slate-500">{{ viewCopy.domainInfo.fqdnLabel }} {{ domain.instructions?.verification.fqdn }}</p>
                <p v-if="domain.instructions?.verification.description" class="mt-1 text-xs text-slate-500">
                  {{ domain.instructions?.verification.description }}
                </p>
              </div>
              <div class="rounded-xl border border-slate-200 bg-white/80 p-3 text-sm dark:border-slate-800 dark:bg-[#05070F]">
                <p class="font-semibold text-slate-900">
                  {{ viewCopy.domainInfo.targetTitle }} ({{ domain.instructions?.target.type }})
                </p>
                <p class="text-xs text-slate-500">
                  {{ viewCopy.domainInfo.hostLabel }}
                  <span class="font-mono text-slate-800">{{ domain.instructions?.target.host }}</span>
                </p>
                <p class="text-xs text-slate-500">
                  {{ viewCopy.domainInfo.valueLabel }}
                  <span class="font-mono text-slate-800">{{ domain.instructions?.target.value }}</span>
                </p>
                <p class="text-xs text-slate-500">{{ viewCopy.domainInfo.typeLabel }} {{ domain.instructions?.target.type }}</p>
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
                {{ isActionRunning(domain.id, 'verify') ? viewCopy.actions.verifying : viewCopy.actions.verify }}
              </button>
              <button
                v-if="!domain.is_active"
                type="button"
                class="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1 font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-100 dark:hover:bg-emerald-500/20"
                :disabled="isActionRunning(domain.id) || !domain.is_verified"
                @click="activateDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'activate') ? viewCopy.actions.activating : viewCopy.actions.activate }}
              </button>
              <button
                v-else
                type="button"
                class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-1 font-semibold text-amber-700 hover:bg-amber-100 disabled:opacity-50 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100 dark:hover:bg-amber-500/20"
                :disabled="isActionRunning(domain.id)"
                @click="deactivateDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'deactivate') ? viewCopy.actions.deactivating : viewCopy.actions.deactivate }}
              </button>
              <button
                type="button"
                class="rounded-xl border border-sky-200 bg-sky-50 px-3 py-1 font-semibold text-sky-700 hover:bg-sky-100 disabled:opacity-50 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-100 dark:hover:bg-sky-500/20"
                :disabled="isActionRunning(domain.id) || domain.is_primary"
                @click="setPrimary(domain)"
              >
                {{ isActionRunning(domain.id, 'primary') ? viewCopy.actions.primarying : viewCopy.actions.setPrimary }}
              </button>
              <button
                type="button"
                class="rounded-xl border border-red-200 bg-red-50 px-3 py-1 font-semibold text-red-700 hover:bg-red-100 disabled:opacity-50 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-100 dark:hover:bg-red-500/20"
                :disabled="isActionRunning(domain.id) || domain.is_active"
                @click="removeDomain(domain)"
              >
                {{ isActionRunning(domain.id, 'delete') ? viewCopy.actions.deleting : viewCopy.actions.delete }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <h2 class="text-lg font-semibold text-slate-900">{{ viewCopy.dnsGuide.title }}</h2>
      <div class="mt-3 grid gap-6 md:grid-cols-2">
        <div class="space-y-2 text-sm text-slate-600">
          <p class="font-semibold text-slate-800">{{ viewCopy.dnsGuide.subdomainTitle }}</p>
          <ul class="list-disc space-y-1 pl-5">
            <li>
              {{ viewCopy.dnsGuide.subdomainHostPrefix }}
              <span class="font-mono">www</span>&nbsp;{{ viewCopy.dnsGuide.subdomainHostConnector }}&nbsp;<span class="font-mono">roteiros</span>.
            </li>
            <li>
              {{ viewCopy.dnsGuide.subdomainCname }} <span class="font-mono">{{ cnameTarget }}</span>.
            </li>
            <li>{{ viewCopy.dnsGuide.subdomainTxt }}</li>
          </ul>
        </div>
        <div class="space-y-2 text-sm text-slate-600">
          <p class="font-semibold text-slate-800">{{ viewCopy.dnsGuide.apexTitle }}</p>
          <ul class="list-disc space-y-1 pl-5">
            <li>{{ viewCopy.dnsGuide.apexRecord }}</li>
            <li>
              {{ viewCopy.dnsGuide.apexValuePrefix }}<span class="font-mono">{{ apexTarget }}</span>{{ viewCopy.dnsGuide.apexValueSuffix }}
            </li>
            <li>{{ viewCopy.dnsGuide.apexTxt }}</li>
          </ul>
        </div>
      </div>
      <p class="mt-4 text-sm text-slate-600">
        {{ viewCopy.dnsGuide.footer }}
      </p>
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

const allowedDomainPlans = ["teste", "infinity"];
const currentPlan = computed(() =>
  (auth.user?.trial_plan || auth.user?.plan || "").toLowerCase()
);
const domainsAllowed = computed(() => allowedDomainPlans.includes(currentPlan.value));
const currentAgencyId = computed(() => agencyStore.currentAgencyId);
const currentAgencyName = computed(() => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return agency?.name || viewCopy.list.unnamedAgency;
});
const platformExample = computed(() => `${platformHosts[0] || "seusite.com"}/agencia/roteiro`);
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

onMounted(async () => {
  if (!agencyStore.agencies.length) {
    await agencyStore.loadAgencies();
  }
  if (domainsAllowed.value) {
    await fetchDomains();
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
:global(.dark-theme .host-input) {
  background-color: #05070f;
  color: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.12);
}
</style>

