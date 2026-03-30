<template>
  <div class="profile-view space-y-6">
    <header class="flex flex-col gap-2">
      <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">{{ viewCopy.header.eyebrow }}</p>
      <h1 class="text-2xl font-bold text-slate-900">{{ viewCopy.header.title }}</h1>
      <p class="text-sm text-slate-600">{{ viewCopy.header.description }}</p>
    </header>

    <div
      v-if="trialInfo"
      class="flex flex-col gap-3 rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-5 text-slate-800 shadow-sm md:flex-row md:items-center md:justify-between"
    >
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-600">{{ viewCopy.trial.eyebrow }}</p>
        <h3 class="text-lg font-bold">{{ viewCopy.trial.planMessage(trialInfo.plan, trialInfo.endsAt) }}</h3>
        <p class="text-sm text-slate-600">
          {{ viewCopy.trial.description }}
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-full bg-amber-600 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-amber-500"
        @click="goPlans"
      >
        {{ viewCopy.trial.cta }}
      </button>
    </div>

    <div class="space-y-4">
      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm space-y-4">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.subscription.eyebrow }}</p>
            <h2 class="text-xl font-bold text-slate-900">{{ viewCopy.subscription.title }}</h2>
            <p class="text-sm text-slate-600">{{ viewCopy.subscription.description }}</p>
          </div>
          <button
            class="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
            @click="goPlans"
          >
            {{ viewCopy.subscription.viewPlans }}
          </button>
        </div>

        <div class="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <span :class="statusBadgeClass">{{ billingStatusLabel }}</span>
          <span class="font-semibold text-slate-900">{{ currentPlanLabel }}</span>
          <span v-if="billing?.valid_until">{{ viewCopy.subscription.validUntilPrefix }} {{ formatDate(billing?.valid_until) }}</span>
          <span class="text-xs uppercase tracking-[0.2em] text-slate-400">
            {{ billingCycleLabel }}
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- <button
            class="inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            style="background-color: #41ce5f"
            :disabled="!isPaidPlan"
            @click="toggleCardForm"
          >
            <span>{{ showCardForm ? "Fechar formulário" : "Atualizar cartão" }}</span>
          </button>-->

          <a
            href="#"
            class="text-xs font-semibold text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline"
            :class="{ 'pointer-events-none opacity-40': !isPaidPlan || actionLoading }"
            @click.prevent="cancelSubscription"
          >
            {{ viewCopy.subscription.cancelLink }}
          </a>
        </div>

        <div
          v-if="showCardForm"
          class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm text-slate-700"
        >
          <p class="mb-3 text-xs text-slate-500">
            {{ viewCopy.cardForm.note }}
          </p>

          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-1 text-xs font-semibold">
              {{ viewCopy.cardForm.fields.holderNameLabel }}
              <input
                v-model="cardForm.holderName"
                type="text"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                :placeholder="viewCopy.cardForm.fields.holderNamePlaceholder"
              />
            </label>

            <label class="space-y-1 text-xs font-semibold">
              {{ viewCopy.cardForm.fields.numberLabel }}
              <input
                v-model="cardForm.number"
                type="text"
                inputmode="numeric"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                :placeholder="viewCopy.cardForm.fields.numberPlaceholder"
              />
            </label>

            <label class="space-y-1 text-xs font-semibold">
              {{ viewCopy.cardForm.fields.expiryMonthLabel }}
              <input
                v-model="cardForm.expiryMonth"
                type="text"
                inputmode="numeric"
                maxlength="2"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                :placeholder="viewCopy.cardForm.fields.expiryMonthPlaceholder"
              />
            </label>

            <label class="space-y-1 text-xs font-semibold">
              {{ viewCopy.cardForm.fields.expiryYearLabel }}
              <input
                v-model="cardForm.expiryYear"
                type="text"
                inputmode="numeric"
                maxlength="4"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                :placeholder="viewCopy.cardForm.fields.expiryYearPlaceholder"
              />
            </label>

            <label class="space-y-1 text-xs font-semibold">
              {{ viewCopy.cardForm.fields.ccvLabel }}
              <input
                v-model="cardForm.ccv"
                type="text"
                inputmode="numeric"
                maxlength="4"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                :placeholder="viewCopy.cardForm.fields.ccvPlaceholder"
              />
            </label>
          </div>

          <div class="mt-4 flex flex-wrap gap-3">
            <button
              class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 disabled:opacity-60"
              :disabled="cardSubmitting"
              @click="submitCardUpdate"
            >
              <span v-if="cardSubmitting">{{ viewCopy.cardForm.actions.saving }}</span>
              <span v-else>{{ viewCopy.cardForm.actions.save }}</span>
            </button>

            <button
              type="button"
              class="text-xs font-semibold text-slate-500 hover:text-slate-700"
              @click="resetCardForm"
            >
              {{ viewCopy.cardForm.actions.reset }}
            </button>
          </div>
        </div>

        <p class="text-xs text-slate-500">
          {{ viewCopy.subscription.keepAccessNote }}
        </p>
        <p v-if="message" class="text-xs font-semibold text-emerald-600">{{ message }}</p>
        <p v-if="error" class="text-xs font-semibold text-rose-600">{{ error }}</p>
      </div>

      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.profileSection.eyebrow }}</p>
            <h2 class="text-xl font-bold text-slate-900">{{ viewCopy.profileSection.title }}</h2>
            <p class="text-sm text-slate-600">{{ viewCopy.profileSection.description }}</p>
          </div>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.profileSection.fields.nameLabel }}
            <input
              v-model="profileForm.name"
              type="text"
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
              :placeholder="viewCopy.profileSection.fields.namePlaceholder"
            />
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.profileSection.fields.emailLabel }}
            <input
              v-model="profileForm.email"
              type="email"
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
              :placeholder="viewCopy.profileSection.fields.emailPlaceholder"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.profileSection.fields.cpfLabel }}
            <input
              type="text"
              :value="formattedCpf"
              readonly
              disabled
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.profileSection.fields.phoneLabel }}
            <input
              v-model="profileForm.whatsapp"
              type="text"
              class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 bg-white"
              :placeholder="viewCopy.profileSection.fields.phonePlaceholder"
            />
          </label>
        </div>
        <div class="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            style="background-color: #41ce5f"
            :disabled="profileSaving"
            @click="saveProfile"
          >
            {{ profileSaving ? viewCopy.profileSection.actions.saving : viewCopy.profileSection.actions.save }}
          </button>
          <span v-if="profileMessage" class="text-xs font-semibold text-emerald-600">{{ profileMessage }}</span>
          <span v-if="profileError" class="text-xs font-semibold text-rose-600">{{ profileError }}</span>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm space-y-4">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500">{{ viewCopy.passwordSection.eyebrow }}</p>
          <h2 class="text-xl font-bold text-slate-900">{{ viewCopy.passwordSection.title }}</h2>
          <p class="text-sm text-slate-600">
            {{ viewCopy.passwordSection.description }}
          </p>
        </div>
        <div class="grid gap-4 md:grid-cols-3">
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.passwordSection.fields.currentLabel }}
            <input
              v-model="passwordForm.current"
              type="password"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              :placeholder="viewCopy.passwordSection.fields.currentPlaceholder"
              autocomplete="current-password"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.passwordSection.fields.newLabel }}
            <input
              v-model="passwordForm.new"
              type="password"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              :placeholder="viewCopy.passwordSection.fields.newPlaceholder"
              autocomplete="new-password"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.passwordSection.fields.confirmLabel }}
            <input
              v-model="passwordForm.confirm"
              type="password"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              :placeholder="viewCopy.passwordSection.fields.confirmPlaceholder"
              autocomplete="new-password"
            />
          </label>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-full px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            :disabled="passwordSaving"
            style="background-color: #41ce5f"
            @click="changePassword"
          >
            {{ passwordSaving ? viewCopy.passwordSection.actions.saving : viewCopy.passwordSection.actions.save }}
          </button>
          <span v-if="passwordMessage" class="text-xs font-semibold text-emerald-600">{{ passwordMessage }}</span>
          <span v-if="passwordError" class="text-xs font-semibold text-rose-600">{{ passwordError }}</span>
        </div>
      </div>
    </div>

    <div
      v-if="showCancelModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-md rounded-3xl bg-white p-6 text-left shadow-2xl shadow-emerald-900/20">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">{{ viewCopy.modal.title }}</h3>
          <button class="text-slate-400 transition hover:text-slate-600" @click="closeCancelModal">
            <span class="sr-only">{{ viewCopy.modal.closeLabel }}</span>
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <p class="mt-3 text-sm text-slate-600">
          {{ viewCopy.modal.description }}
        </p>
        <div class="mt-6 flex flex-wrap gap-3">
          <button
            class="inline-flex flex-1 items-center justify-center rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500"
            @click="confirmCancelContact"
          >
            {{ viewCopy.modal.confirmCta }}
          </button>
          <button
            type="button"
            class="flex-1 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
            @click="closeCancelModal"
          >
            {{ viewCopy.modal.cancelCta }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, reactive, watch } from "vue";
import { useRouter } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/useAuthStore";
import { getPlanLabel } from "../../utils/planLabels";
import { createAdminLocalizer, getAdminLanguage } from "../../utils/adminI18n";

interface BillingInfo {
  plan: string;
  status: string;
  valid_until: string | null;
  failed_attempts: number;
  preapproval_id?: string | null;
  billing_cycle?: string | null;
}

const authStore = useAuthStore();
const router = useRouter();
const adminLanguage = getAdminLanguage();
const t = createAdminLocalizer(adminLanguage);

const viewCopy = {
  header: {
    eyebrow: t({ pt: "Conta", es: "Cuenta" }),
    title: t({ pt: "Perfil e Assinatura", es: "Perfil y Suscripción" }),
    description: t({ pt: "Veja seus dados principais, plano atual e validade.", es: "Consulta tus datos principales, el plan actual y su vigencia." })
  },
  trial: {
    eyebrow: t({ pt: "Trial ativo", es: "Prueba activa" }),
    planMessage: (plan: string, endsAt: string) =>
      t({
        pt: `Plano ${plan} liberado até ${endsAt}`,
        es: `Plan ${plan} habilitado hasta ${endsAt}`
      }),
    description: t({
      pt: "Aproveite todos os recursos premium durante o período de experiência. Assine agora para manter o acesso.",
      es: "Aprovecha todos los recursos premium durante el período de prueba. Suscríbete ahora para mantener el acceso."
    }),
    cta: t({ pt: "Ativar plano", es: "Activar plan" })
  },
  subscription: {
    eyebrow: t({ pt: "Assinatura", es: "Suscripción" }),
    title: t({ pt: "Gestão do meu plano", es: "Gestión de mi plan" }),
    description: t({
      pt: "Atualize o cartão ou encerre a renovação quando precisar.",
      es: "Actualiza la tarjeta o detén la renovación cuando lo necesites."
    }),
    viewPlans: t({ pt: "Ver planos disponíveis", es: "Ver planes disponibles" }),
    validUntilPrefix: t({ pt: "Válido até", es: "Válido hasta" }),
    cancelLink: t({ pt: "Cancelar renovação", es: "Cancelar renovación" }),
    keepAccessNote: t({
      pt: "Você manterá o acesso até o fim do período pago mesmo após cancelar ou voltar ao plano gratuito.",
      es: "Mantendrás el acceso hasta el final del período pagado incluso después de cancelar o volver al plan gratuito."
    })
  },
  cardForm: {
    note: t({
      pt: "Nenhuma cobrança será feita agora. O novo cartão será usado automaticamente na próxima renovação.",
      es: "No se realizará ningún cobro ahora. La nueva tarjeta se usará automáticamente en la próxima renovación."
    }),
    fields: {
      holderNameLabel: t({ pt: "Nome impresso", es: "Nombre en la tarjeta" }),
      holderNamePlaceholder: t({ pt: "Nome completo", es: "Nombre completo" }),
      numberLabel: t({ pt: "Número do cartão", es: "Número de la tarjeta" }),
      numberPlaceholder: t({ pt: "0000 0000 0000 0000", es: "0000 0000 0000 0000" }),
      expiryMonthLabel: t({ pt: "Mês de validade", es: "Mes de validez" }),
      expiryMonthPlaceholder: t({ pt: "MM", es: "MM" }),
      expiryYearLabel: t({ pt: "Ano de validade", es: "Año de validez" }),
      expiryYearPlaceholder: t({ pt: "AAAA", es: "AAAA" }),
      ccvLabel: t({ pt: "Código de segurança", es: "Código de seguridad" }),
      ccvPlaceholder: t({ pt: "CVV", es: "CVV" })
    },
    actions: {
      saving: t({ pt: "Enviando...", es: "Enviando..." }),
      save: t({ pt: "Salvar novo cartão", es: "Guardar nueva tarjeta" }),
      reset: t({ pt: "Limpar campos", es: "Limpiar campos" })
    },
    errors: {
      required: t({ pt: "Preencha todos os campos do cartão.", es: "Completa todos los campos de la tarjeta." }),
      failure: t({ pt: "Não foi possível atualizar o cartão. Verifique os dados e tente novamente.", es: "No fue posible actualizar la tarjeta. Verifica los datos e inténtalo de nuevo." })
    },
    success: t({ pt: "Cartão atualizado com sucesso. Ele será usado na próxima renovação.", es: "Tarjeta actualizada con éxito. Se usará en la próxima renovación." })
  },
  profileSection: {
    eyebrow: t({ pt: "Dados", es: "Datos" }),
    title: t({ pt: "Informações pessoais", es: "Información personal" }),
    description: t({ pt: "Revise ou ajuste os dados exibidos no painel.", es: "Revisa o ajusta los datos mostrados en el panel." }),
    fields: {
      nameLabel: t({ pt: "Nome completo", es: "Nombre completo" }),
      namePlaceholder: t({ pt: "Seu nome", es: "Tu nombre" }),
      emailLabel: t({ pt: "E-mail", es: "E-mail" }),
      emailPlaceholder: t({ pt: "email@exemplo.com", es: "correo@ejemplo.com" }),
      cpfLabel: t({ pt: "CPF", es: "Documento (CPF)" }),
      phoneLabel: t({ pt: "Telefone", es: "Teléfono" }),
      phonePlaceholder: t({ pt: "(00) 00000-0000", es: "(00) 00000-0000" })
    },
    actions: {
      saving: t({ pt: "Salvando...", es: "Guardando..." }),
      save: t({ pt: "Salvar dados", es: "Guardar datos" })
    },
    success: t({ pt: "Dados atualizados com sucesso.", es: "Datos actualizados con éxito." }),
    errors: {
      required: t({ pt: "Informe nome e e-mail.", es: "Ingresa nombre y e-mail." }),
      invalidPhone: t({ pt: "Informe um telefone válido com DDD.", es: "Ingresa un teléfono válido con código de área." }),
      failure: t({ pt: "Não foi possível salvar os dados.", es: "No fue posible guardar los datos." })
    }
  },
  passwordSection: {
    eyebrow: t({ pt: "Segurança", es: "Seguridad" }),
    title: t({ pt: "Alterar senha", es: "Cambiar contraseña" }),
    description: t({
      pt: "A senha precisa ter pelo menos 8 caracteres, conter letras maiúsculas e minúsculas e pelo menos um número.",
      es: "La contraseña debe tener al menos 8 caracteres e incluir mayúsculas, minúsculas y al menos un número."
    }),
    fields: {
      currentLabel: t({ pt: "Senha atual", es: "Contraseña actual" }),
      currentPlaceholder: t({ pt: "••••••••", es: "••••••••" }),
      newLabel: t({ pt: "Nova senha", es: "Nueva contraseña" }),
      newPlaceholder: t({ pt: "Nova senha", es: "Nueva contraseña" }),
      confirmLabel: t({ pt: "Confirmar nova senha", es: "Confirmar nueva contraseña" }),
      confirmPlaceholder: t({ pt: "Repita a nova senha", es: "Repite la nueva contraseña" })
    },
    actions: {
      saving: t({ pt: "Alterando...", es: "Actualizando..." }),
      save: t({ pt: "Salvar nova senha", es: "Guardar nueva contraseña" })
    },
    success: t({ pt: "Senha atualizada com sucesso.", es: "Contraseña actualizada con éxito." }),
    errors: {
      missing: t({ pt: "Informe a senha atual e a nova senha duas vezes.", es: "Ingresa la contraseña actual y la nueva dos veces." }),
      mismatch: t({ pt: "As senhas novas precisam coincidir.", es: "Las contraseñas nuevas deben coincidir." }),
      failure: t({ pt: "Não foi possível alterar a senha.", es: "No fue posible cambiar la contraseña." })
    }
  },
  billing: {
    statuses: {
      active: t({ pt: "Ativa", es: "Activa" }),
      past_due: t({ pt: "Pagamento pendente", es: "Pago pendiente" }),
      cancelled: t({ pt: "Cancelada", es: "Cancelada" }),
      cancel_at_period_end: t({ pt: "Cancela no fim do ciclo", es: "Cancela al final del ciclo" }),
      pending: t({ pt: "Aguardando pagamento", es: "Esperando pago" }),
      inactive: t({ pt: "Inativa", es: "Inactiva" })
    },
    cycle: {
      annual: t({ pt: "Plano anual", es: "Plan anual" }),
      monthly: t({ pt: "Plano mensal", es: "Plan mensual" }),
      default: t({ pt: "Ciclo padrão", es: "Ciclo estándar" })
    }
  },
  modal: {
    title: t({ pt: "Deseja prosseguir com o cancelamento?", es: "¿Deseas continuar con la cancelación?" }),
    closeLabel: t({ pt: "Fechar", es: "Cerrar" }),
    description: t({
      pt: "Vamos continuar o atendimento pelo WhatsApp. Confirme para abrir a conversa com nossa equipe.",
      es: "Seguiremos la atención por WhatsApp. Confirma para abrir la conversación con nuestro equipo."
    }),
    confirmCta: t({ pt: "Falar no WhatsApp", es: "Hablar por WhatsApp" }),
    cancelCta: t({ pt: "Voltar", es: "Volver" }),
    defaultClientName: t({ pt: "cliente", es: "cliente" }),
    whatsappMessage: (name: string) =>
      t({
        pt: `Olá, meu nome é ${name}. Eu gostaria de fazer o cancelamento da minha assinatura.`,
        es: `Hola, mi nombre es ${name}. Me gustaría cancelar mi suscripción.`
      })
  },
  errors: {
    loadBilling: t({ pt: "Não foi possível carregar a assinatura.", es: "No fue posible cargar la suscripción." })
  }
};

const user = computed(() => authStore.user);
const formattedCpf = computed(() => formatCpf(user.value?.cpf || ""));
const billing = ref<BillingInfo | null>(null);

const message = ref<string | null>(null);
const error = ref<string | null>(null);
const passwordForm = reactive({
  current: "",
  new: "",
  confirm: ""
});
const passwordSaving = ref(false);
const passwordMessage = ref<string | null>(null);
const passwordError = ref<string | null>(null);
const profileForm = reactive({
  name: "",
  email: "",
  whatsapp: ""
});
const profileSaving = ref(false);
const profileMessage = ref<string | null>(null);
const profileError = ref<string | null>(null);

const actionLoading = ref(false);
const showCardForm = ref(false);
const showCancelModal = ref(false);
const cardSubmitting = ref(false);

const cardForm = reactive({
  holderName: "",
  number: "",
  expiryMonth: "",
  expiryYear: "",
  ccv: ""
});

const billingStatusLabel = computed(() => {
  const status = billing.value?.status || "inactive";
  const statusMap: Record<string, string> = {
    active: viewCopy.billing.statuses.active,
    past_due: viewCopy.billing.statuses.past_due,
    cancelled: viewCopy.billing.statuses.cancelled,
    cancel_at_period_end: viewCopy.billing.statuses.cancel_at_period_end,
    pending: viewCopy.billing.statuses.pending,
    inactive: viewCopy.billing.statuses.inactive
  };
  return statusMap[status] || status;
});

const statusBadgeClass = computed(() => {
  const status = billing.value?.status || "inactive";
  if (status === "active") return "rounded-full bg-[#3EBD59] px-3 py-1 text-xs font-semibold text-white";
  if (status === "cancel_at_period_end")
    return "rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700";
  if (status === "past_due") return "rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700";
  if (status === "cancelled") return "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600";
  return "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500";
});

const billingCycleLabel = computed(() => {
  const cycle = billing.value?.billing_cycle;
  if (cycle === "annual") return viewCopy.billing.cycle.annual;
  if (cycle === "monthly") return viewCopy.billing.cycle.monthly;
  return viewCopy.billing.cycle.default;
});

const currentPlanLabel = computed(() => getPlanLabel(billing.value?.plan || user.value?.plan));

const isPaidPlan = computed(() => {
  const plan = billing.value?.plan || user.value?.plan;
  return !!plan && plan !== "free";
});

const formatDate = (iso?: string | null) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString();
};

function formatCpf(cpf?: string | null) {
  if (!cpf) return "";
  const digits = cpf.replace(/\D/g, "").slice(0, 11);
  if (!digits) return "";
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatPhone(phone?: string | null) {
  if (!phone) return "";
  const digits = phone.replace(/\D/g, "").slice(0, 11);
  if (!digits) return "";
  if (digits.length <= 2) return `(${digits}`;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}


const syncProfileForm = () => {
  profileForm.name = user.value?.name || "";
  profileForm.email = user.value?.email || "";
  profileForm.whatsapp = formatPhone(user.value?.whatsapp || "");
  profileMessage.value = null;
  profileError.value = null;
};

watch(
  () => user.value,
  () => {
    syncProfileForm();
  },
  { immediate: true }
);

watch(
  () => profileForm.whatsapp,
  value => {
    if (value == null) return;
    const formatted = formatPhone(value);
    if (value !== formatted) profileForm.whatsapp = formatted;
  }
);

const loadBilling = async () => {
  try {
    const res = await api.get<BillingInfo>("/billing/me");
    billing.value = res.data;
  } catch (err) {
    console.error(err);
    error.value = viewCopy.errors.loadBilling;
  }
};

const cancelSubscription = () => {
  if (!isPaidPlan.value) return;
  showCancelModal.value = true;
};

const closeCancelModal = () => {
  showCancelModal.value = false;
};

const confirmCancelContact = () => {
  const formName = profileForm.name.trim();
  const storedName = (user.value?.name || "").trim();
  const clientName = formName || storedName || viewCopy.modal.defaultClientName;
  const message = viewCopy.modal.whatsappMessage(clientName);
  const whatsappUrl = `https://wa.me/5553991754616?text=${encodeURIComponent(message)}`;
  window.open(whatsappUrl, "_blank", "noopener");
  showCancelModal.value = false;
};

const toggleCardForm = () => {
  if (!isPaidPlan.value) return;
  showCardForm.value = !showCardForm.value;
  if (!showCardForm.value) resetCardForm();
};

const resetCardForm = () => {
  cardForm.holderName = "";
  cardForm.number = "";
  cardForm.expiryMonth = "";
  cardForm.expiryYear = "";
  cardForm.ccv = "";
};

const submitCardUpdate = async () => {
  if (!isPaidPlan.value) return;

  if (!cardForm.holderName || !cardForm.number || !cardForm.expiryMonth || !cardForm.expiryYear || !cardForm.ccv) {
    error.value = viewCopy.cardForm.errors.required;
    return;
  }

  cardSubmitting.value = true;
  message.value = null;
  error.value = null;

  try {
    await api.post("/billing/update-card", {
      holder_name: cardForm.holderName,
      number: cardForm.number.replace(/\s+/g, ""),
      expiry_month: cardForm.expiryMonth,
      expiry_year: cardForm.expiryYear,
      ccv: cardForm.ccv
    });

    message.value = viewCopy.cardForm.success;
    showCardForm.value = false;
    resetCardForm();
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    error.value = detail || viewCopy.cardForm.errors.failure;
  } finally {
    cardSubmitting.value = false;
  }
};

const changePassword = async () => {
  passwordError.value = "";
  passwordMessage.value = "";
  if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
    passwordError.value = viewCopy.passwordSection.errors.missing;
    return;
  }
  if (passwordForm.new !== passwordForm.confirm) {
    passwordError.value = viewCopy.passwordSection.errors.mismatch;
    return;
  }
  passwordSaving.value = true;
  try {
    await api.post("/auth/me/password", {
      current_password: passwordForm.current,
      new_password: passwordForm.new
    });
    passwordMessage.value = viewCopy.passwordSection.success;
    passwordForm.current = "";
    passwordForm.new = "";
    passwordForm.confirm = "";
  } catch (err) {
    console.error(err);
    passwordError.value = (err as any)?.response?.data?.detail || viewCopy.passwordSection.errors.failure;
  } finally {
    passwordSaving.value = false;
  }
};

const saveProfile = async () => {
  profileError.value = null;
  profileMessage.value = null;
  const name = profileForm.name.trim();
  const email = profileForm.email.trim();
  if (!name || !email) {
    profileError.value = viewCopy.profileSection.errors.required;
    return;
  }
  const phoneDigits = profileForm.whatsapp.replace(/\D/g, "");
  if (phoneDigits && phoneDigits.length < 10) {
    profileError.value = viewCopy.profileSection.errors.invalidPhone;
    return;
  }
  profileSaving.value = true;
  try {
    await api.put("/auth/me", {
      name,
      email,
      whatsapp: phoneDigits || null
    });
    await authStore.fetchProfile();
    profileMessage.value = viewCopy.profileSection.success;
  } catch (err: any) {
    console.error(err);
    profileError.value = err?.response?.data?.detail || viewCopy.profileSection.errors.failure;
  } finally {
    profileSaving.value = false;
  }
};

const trialInfo = computed(() => {
  const trialPlan = user.value?.trial_plan;
  const trialEndsAt = user.value?.trial_ends_at;
  if (!trialPlan || !trialEndsAt) return null;
  return {
    plan: getPlanLabel(trialPlan),
    endsAt: formatDate(trialEndsAt)
  };
});

const goPlans = () => {
  router.push("/admin/planos");
};

onMounted(loadBilling);
</script>

<style scoped>
:global(.dark-theme .profile-view input) {
  background-color: #05070f !important;
  color: #f8fafc;
  border-color: rgba(255, 255, 255, 0.15);
}
</style>
