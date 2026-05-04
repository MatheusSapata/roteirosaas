<template>
  <div v-if="isBootstrappingProfile" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>
  <div v-else class="profile-ref page-wrap">
    <div class="page-eyebrow">{{ viewCopy.header.eyebrow }}</div>
    <div class="page-title">{{ viewCopy.header.title }}</div>
    <div class="page-sub">{{ viewCopy.header.description }}</div>

    <div class="card">
      <div class="card-body card-body-plan">
        <div class="subscription-top">
          <div class="plan-left">
            <div class="card-eye">{{ viewCopy.subscription.eyebrow }}</div>
            <div class="card-title">{{ viewCopy.subscription.title }}</div>
          </div>
          <div class="plan-actions">
            <button class="btn btn-o btn-sm" @click="goPlans">{{ viewCopy.subscription.viewPlans }}</button>
            <button class="btn-text" :class="{ 'is-disabled': !isPaidPlan || actionLoading }" @click="cancelSubscription">
              {{ viewCopy.subscription.cancelLink }}
            </button>
          </div>
        </div>

        <div class="subscription-meta">
          <div class="meta-item">
            <span class="meta-label">Status da assinatura</span>
            <span class="badge badge-green"><span class="badge-dot"></span>{{ billingStatusLabel }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Plano atual</span>
            <span class="badge badge-muted">{{ currentPlanLabel }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Tipo de ciclo</span>
            <span class="badge badge-muted">{{ billingCycleLabel }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Data de renovação</span>
            <span class="badge badge-muted">
              {{ billing?.valid_until ? formatDate(billing?.valid_until) : "--" }}
            </span>
          </div>
        </div>
      </div>
      <div class="card-foot notes">
        <p v-if="message" class="ok-msg">{{ message }}</p>
        <p v-if="error" class="err-msg">{{ error }}</p>
      </div>
    </div>

    <div class="card-row">
      <div class="card">
        <div class="card-head">
          <div class="card-eye">{{ viewCopy.profileSection.eyebrow }}</div>
          <div class="card-title">{{ viewCopy.profileSection.title }}</div>
          <div class="card-sub">{{ viewCopy.profileSection.description }}</div>
        </div>
        <div class="card-body">
          <div class="profile-layout">
            <div class="profile-top">
              <div class="profile-photo-col">
                <label class="fl">Foto de perfil</label>
                <button type="button" class="profile-photo-upload" @click="openProfilePhotoEditor">
                  <img
                    v-if="profilePhotoPreview"
                    :src="profilePhotoPreview"
                    alt="Foto de perfil"
                    class="profile-photo-img"
                  />
                  <div v-else class="profile-photo-empty">
                    <span class="profile-photo-plus">+</span>
                    <span>Enviar foto</span>
                  </div>
                </button>
                <input
                  ref="profilePhotoInputRef"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="onProfilePhotoSelected"
                />
              </div>

              <div class="profile-identity-col">
                <div class="fg">
                  <label class="fl">{{ viewCopy.profileSection.fields.nameLabel }}</label>
                  <input v-model="profileForm.name" class="fi" type="text" :placeholder="viewCopy.profileSection.fields.namePlaceholder" />
                </div>
                <div class="profile-cpf-phone-row">
                  <div class="fg">
                    <label class="fl">{{ viewCopy.profileSection.fields.cpfLabel }}</label>
                    <input class="fi" type="text" :value="formattedCpf" readonly disabled />
                  </div>
                  <div class="fg">
                    <label class="fl">{{ viewCopy.profileSection.fields.phoneLabel }}</label>
                    <input v-model="profileForm.whatsapp" class="fi" type="text" :placeholder="viewCopy.profileSection.fields.phonePlaceholder" />
                  </div>
                </div>
                <div class="fg">
                  <label class="fl">{{ viewCopy.profileSection.fields.emailLabel }}</label>
                  <input v-model="profileForm.email" class="fi" type="email" :placeholder="viewCopy.profileSection.fields.emailPlaceholder" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="card-foot">
          <button type="button" class="btn btn-p" :disabled="profileSaving" @click="saveProfile">
            {{ profileSaving ? viewCopy.profileSection.actions.saving : viewCopy.profileSection.actions.save }}
          </button>
          <span v-if="profileMessage" class="ok-msg">{{ profileMessage }}</span>
          <span v-if="profileError" class="err-msg">{{ profileError }}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="card-eye">{{ viewCopy.passwordSection.eyebrow }}</div>
          <div class="card-title">{{ viewCopy.passwordSection.title }}</div>
          <div class="card-sub">{{ viewCopy.passwordSection.description }}</div>
        </div>
        <div class="card-body">
          <div class="fg">
            <label class="fl">{{ viewCopy.passwordSection.fields.currentLabel }}</label>
            <input v-model="passwordForm.current" class="fi" type="password" :placeholder="viewCopy.passwordSection.fields.currentPlaceholder" autocomplete="current-password" />
          </div>
          <div class="fg">
            <label class="fl">{{ viewCopy.passwordSection.fields.newLabel }}</label>
            <input v-model="passwordForm.new" class="fi" type="password" :placeholder="viewCopy.passwordSection.fields.newPlaceholder" autocomplete="new-password" />
          </div>
          <div class="fg">
            <label class="fl">{{ viewCopy.passwordSection.fields.confirmLabel }}</label>
            <input v-model="passwordForm.confirm" class="fi" type="password" :placeholder="viewCopy.passwordSection.fields.confirmPlaceholder" autocomplete="new-password" />
          </div>
        </div>
        <div class="card-foot">
          <button type="button" class="btn btn-p" :disabled="passwordSaving" @click="changePassword">
            {{ passwordSaving ? viewCopy.passwordSection.actions.saving : viewCopy.passwordSection.actions.save }}
          </button>
          <span v-if="passwordMessage" class="ok-msg">{{ passwordMessage }}</span>
          <span v-if="passwordError" class="err-msg">{{ passwordError }}</span>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div
        v-if="cropperModalOpen"
        class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
      >
        <div class="w-full max-w-5xl rounded-3xl bg-white p-6 shadow-2xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Editor de perfil</p>
              <h3 class="text-2xl font-bold text-slate-900">Recortar foto de perfil</h3>
              <p class="text-sm text-slate-500">Ajuste o enquadramento da sua foto antes de salvar.</p>
            </div>
            <button type="button" class="text-sm font-semibold text-slate-500 hover:text-slate-700" @click="closeCropperModal">
              Fechar
            </button>
          </div>
          <div class="mt-6 grid gap-6 md:grid-cols-[minmax(0,1fr)_220px]">
            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <img ref="cropperImageRef" :src="cropperSource" alt="Recorte de perfil" class="cropper-target max-h-[420px] w-full rounded-xl bg-white object-contain" />
            </div>
            <div class="space-y-4">
              <p class="text-xs text-slate-500">Use os controles para reposicionar a foto e aplicar o recorte final.</p>
              <div class="space-y-2">
                <button
                  type="button"
                  class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="openProfilePhotoPicker"
                >
                  Substituir foto
                </button>
                <button
                  type="button"
                  class="w-full rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50"
                  @click="removeProfilePhoto"
                >
                  Remover foto
                </button>
              </div>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="zoom(-0.2)"
                >
                  -
                </button>
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="zoom(0.2)"
                >
                  +
                </button>
              </div>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="rotate(-10)"
                >
                  Rotacionar -
                </button>
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="rotate(10)"
                >
                  Rotacionar +
                </button>
              </div>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="closeCropperModal"
            >
              Cancelar
            </button>
            <button
              type="button"
              class="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="cropperApplying"
              @click="applyProfileCrop"
            >
              {{ cropperApplying ? "Aplicando..." : "Aplicar recorte" }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <div
      v-if="showCancelModal"
      class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4"
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
import Cropper from "cropperjs";
import "cropperjs/dist/cropper.css";
import { onMounted, ref, computed, reactive, watch, nextTick, onBeforeUnmount } from "vue";
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
const isBootstrappingProfile = ref(true);

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
const profilePhotoInputRef = ref<HTMLInputElement | null>(null);
const profilePhotoPreview = ref<string | null>(null);
const profilePhotoFile = ref<File | null>(null);
let profilePhotoObjectUrl: string | null = null;
const profilePhotoRemoved = ref(false);
const cropperModalOpen = ref(false);
const cropperSource = ref("");
const cropperImageRef = ref<HTMLImageElement | null>(null);
const cropperInstance = ref<Cropper | null>(null);
const cropperApplying = ref(false);

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
  profilePhotoPreview.value =
    (user.value as any)?.profile_photo_url ||
    (user.value as any)?.avatar_url ||
    (user.value as any)?.photo_url ||
    null;
  profileMessage.value = null;
  profileError.value = null;
};

const openProfilePhotoPicker = () => {
  profilePhotoInputRef.value?.click();
};

const openProfilePhotoEditor = () => {
  if (profilePhotoPreview.value) {
    cropperSource.value = profilePhotoPreview.value;
    cropperModalOpen.value = true;
    return;
  }
  openProfilePhotoPicker();
};

const onProfilePhotoSelected = (event: Event) => {
  const target = event.target as HTMLInputElement | null;
  const file = target?.files?.[0];
  if (!file) return;
  if (profilePhotoObjectUrl) URL.revokeObjectURL(profilePhotoObjectUrl);
  profilePhotoObjectUrl = URL.createObjectURL(file);
  profilePhotoRemoved.value = false;
  cropperSource.value = profilePhotoObjectUrl;
  cropperModalOpen.value = true;
  if (target) target.value = "";
};

const closeCropperModal = () => {
  cropperModalOpen.value = false;
};

watch(
  () => cropperModalOpen.value,
  async open => {
    if (open) {
      await nextTick();
      if (!cropperImageRef.value) return;
      cropperInstance.value?.destroy();
      cropperInstance.value = new Cropper(cropperImageRef.value, {
        viewMode: 1,
        dragMode: "crop",
        autoCrop: true,
        autoCropArea: 0.65,
        aspectRatio: 1,
        background: true,
        guides: true,
        center: true,
        highlight: true,
        modal: true,
        cropBoxMovable: true,
        cropBoxResizable: true,
        movable: true,
        zoomable: true,
        zoomOnWheel: true,
        ready() {
          const instance = cropperInstance.value;
          if (!instance) return;
          const container = instance.getContainerData();
          const side = Math.min(container.width, container.height) * 0.62;
          instance.setCropBoxData({
            width: side,
            height: side,
            left: (container.width - side) / 2,
            top: (container.height - side) / 2
          });
        }
      });
      return;
    }
    cropperInstance.value?.destroy();
    cropperInstance.value = null;
  }
);

const applyProfileCrop = async () => {
  if (!cropperInstance.value) return;
  cropperApplying.value = true;
  try {
    const canvas = cropperInstance.value.getCroppedCanvas({
      maxWidth: 1200,
      maxHeight: 1200,
      imageSmoothingEnabled: true,
      imageSmoothingQuality: "high"
    });
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(result => {
        if (result) resolve(result);
        else reject(new Error("Falha ao gerar recorte."));
      }, "image/png", 0.95);
    });
    const file = new File([blob], `avatar-${Date.now()}.png`, { type: "image/png" });
    profilePhotoFile.value = file;
    profilePhotoRemoved.value = false;
    if (profilePhotoObjectUrl) URL.revokeObjectURL(profilePhotoObjectUrl);
    profilePhotoObjectUrl = URL.createObjectURL(file);
    profilePhotoPreview.value = profilePhotoObjectUrl;
    closeCropperModal();
  } catch (err) {
    console.error(err);
  } finally {
    cropperApplying.value = false;
  }
};

const zoom = (value: number) => {
  cropperInstance.value?.zoom(value);
};

const rotate = (value: number) => {
  cropperInstance.value?.rotate(value);
};

const removeProfilePhoto = () => {
  profilePhotoRemoved.value = true;
  profilePhotoFile.value = null;
  profilePhotoPreview.value = null;
  closeCropperModal();
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
    if (profilePhotoRemoved.value) {
      await api.delete("/auth/me/avatar");
      profilePhotoRemoved.value = false;
      if (profilePhotoObjectUrl) {
        URL.revokeObjectURL(profilePhotoObjectUrl);
        profilePhotoObjectUrl = null;
      }
    }
    if (profilePhotoFile.value) {
      const formData = new FormData();
      formData.append("file", profilePhotoFile.value);
      await api.post("/auth/me/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      profilePhotoFile.value = null;
      if (profilePhotoObjectUrl) {
        URL.revokeObjectURL(profilePhotoObjectUrl);
        profilePhotoObjectUrl = null;
      }
    }
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

onMounted(async () => {
  try {
    if (authStore.token && !authStore.user) {
      await authStore.ensureHydrated();
    }
    await loadBilling();
  } finally {
    isBootstrappingProfile.value = false;
  }
});

onBeforeUnmount(() => {
  cropperInstance.value?.destroy();
  if (profilePhotoObjectUrl) URL.revokeObjectURL(profilePhotoObjectUrl);
});

watch(
  () => user.value,
  () => {
    if (profilePhotoObjectUrl) {
      URL.revokeObjectURL(profilePhotoObjectUrl);
      profilePhotoObjectUrl = null;
    }
  }
);
</script>

<style scoped>
.profile-ref {
  --verde: #3dcc5f;
  --verde-d: #2ead4c;
  --verde-dim: rgba(61, 204, 95, 0.1);
  --verde-border: rgba(61, 204, 95, 0.22);
  --bg: #f2f4f2;
  --surface: #fff;
  --surface2: #f5f7f5;
  --border: #e4e9e4;
  --border2: #cdd8cd;
  --text: #111a14;
  --text-2: #4a5e4a;
  --text-3: #8a9e8a;
  --sh-sm: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  --radius: 12px;
  --radius-sm: 8px;
  color: var(--text);
}

.page-wrap {
  padding: 28px 32px 64px;
  width: 100%;
  max-width: none;
}

.page-eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-3);
  margin-bottom: 3px;
}

.page-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.3px;
  line-height: 1.2;
}

.page-sub {
  font-size: 13px;
  color: var(--text-3);
  margin-top: 4px;
  margin-bottom: 24px;
}

.card {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--sh-sm);
  width: 100%;
  margin-bottom: 14px;
}

.card-head {
  padding: 18px 22px 14px;
  border-bottom: 1.5px solid var(--border);
}

.card-eye {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-3);
  margin-bottom: 3px;
}

.card-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.2px;
}

.card-sub {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
  line-height: 1.45;
}

.card-body {
  padding: 20px 22px;
}

.card-foot {
  padding: 14px 22px;
  border-top: 1.5px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.card-body-plan {
  padding: 0;
}

.plan-left {
  flex-shrink: 0;
}

.subscription-top {
  padding: 18px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  border-bottom: 1.5px solid var(--border);
}

.plan-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.subscription-meta {
  padding: 14px 22px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-3);
}

.badge-muted {
  background: var(--surface2);
  color: var(--text-2);
  border: 1.5px solid var(--border);
}

.notes {
  display: block;
}

.notes p + p {
  margin-top: 4px;
}

.ok-msg {
  font-size: 12px;
  color: #1a7a35;
  font-weight: 600;
}

.err-msg {
  font-size: 12px;
  color: #c0392b;
  font-weight: 600;
}

.card-row {
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: 14px;
  margin-bottom: 14px;
  width: 100%;
}

.fg {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 14px;
}

.fl {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-3);
}

.fi {
  padding: 9px 11px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 13px;
  color: var(--text);
  background: var(--surface);
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
}

.fi:focus {
  border-color: var(--verde-border);
}

.fi:disabled {
  background: var(--surface2);
  color: var(--text-3);
  cursor: not-allowed;
}

.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.profile-layout {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.profile-top {
  display: grid;
  grid-template-columns: 3fr 7fr;
  gap: 24px;
  align-items: stretch;
}

.profile-photo-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 100%;
}

.profile-photo-upload {
  width: 100%;
  height: 185px;
  min-height: 185px;
  margin: 0;
  border: 1.5px dashed var(--border2);
  border-radius: 12px;
  background: var(--surface2);
  padding: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.profile-photo-upload:hover {
  border-color: var(--verde-border);
}

.profile-photo-img {
  width: 100%;
  height: 100%;
  margin: 0;
  object-fit: cover;
  border-radius: 0;
}

.profile-photo-empty {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-3);
  font-size: 12px;
  font-weight: 600;
}

.profile-photo-plus {
  font-size: 20px;
  line-height: 1;
  color: var(--verde-d);
}

.profile-identity-col {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.profile-cpf-phone-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-family: inherit;
  transition: all 0.15s;
  white-space: nowrap;
  line-height: 1.3;
}

.btn-p {
  background: var(--verde);
  color: #0f1f14;
}

.btn-p:hover {
  background: var(--verde-d);
  box-shadow: 0 4px 14px rgba(61, 204, 95, 0.28);
  transform: translateY(-1px);
}

.btn-o {
  background: transparent;
  color: var(--text-2);
  border: 1.5px solid var(--border);
}

.btn-o:hover {
  border-color: var(--border2);
  color: var(--text);
}

.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
}

.btn-text {
  background: transparent;
  border: none;
  color: var(--text-3);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  padding: 0;
}

.btn-text:hover {
  color: #c0392b;
}

.btn-text.is-disabled {
  pointer-events: none;
  opacity: 0.4;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
}

.badge-green {
  background: var(--verde-dim);
  color: #1a7a35;
  border: 1.5px solid var(--verde-border);
}

.badge-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--verde-d);
}

:deep(.cropper-container) {
  max-height: 460px;
}

:deep(.cropper-container img) {
  max-width: none !important;
}

:deep(.cropper-view-box) {
  outline: 2px solid rgba(61, 204, 95, 0.9);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.95);
}

:deep(.cropper-face) {
  background-color: rgba(61, 204, 95, 0.12);
}

:deep(.cropper-line),
:deep(.cropper-point) {
  background-color: #3dcc5f;
  opacity: 1;
}

@media (max-width: 900px) {
  .page-wrap {
    padding: 20px 16px 40px;
  }
}

@media (max-width: 768px) {
  .card-row {
    grid-template-columns: 1fr;
  }

  .subscription-meta {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 600px) {
  .grid2 {
    grid-template-columns: 1fr;
  }

  .profile-top {
    grid-template-columns: 1fr;
  }

  .profile-photo-upload {
    min-height: 180px;
  }

  .profile-cpf-phone-row {
    grid-template-columns: 1fr;
  }

  .subscription-top {
    align-items: flex-start;
  }

  .plan-actions {
    width: 100%;
  }

  .subscription-meta {
    grid-template-columns: 1fr;
  }
}
</style>
