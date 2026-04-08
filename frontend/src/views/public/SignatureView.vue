<template>
  <div class="min-h-screen bg-slate-50 py-10 px-4">
    <div class="mx-auto max-w-5xl space-y-6">
      <div v-if="loading" class="status-card">
        <p class="text-sm text-slate-600">Carregando link de assinatura...</p>
      </div>
      <div v-else-if="errorMessage" class="status-card status-card--error">
        <p class="text-sm text-rose-600">{{ errorMessage }}</p>
        <button type="button" class="btn-secondary mt-3" @click="loadContract">Tentar novamente</button>
      </div>
      <template v-else-if="contract">
        <header class="text-center">
          <img
            v-if="contract.agency_logo_url"
            :src="contract.agency_logo_url"
            alt="Logotipo da agência"
            class="mx-auto mb-4 h-16 w-auto"
          />
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            {{ contract.agency_name || "Jurídico" }}
          </p>
          <h1 class="mt-2 text-3xl font-semibold text-slate-900">Assinatura de contrato</h1>
          <p class="mt-2 text-sm text-slate-600">
            Revise os detalhes abaixo e finalize a assinatura digital com segurança.
          </p>
        </header>

        <div class="grid gap-4 md:grid-cols-2">
          <div class="summary-card">
            <p class="summary-label">Comprador</p>
            <p class="summary-value">{{ contract.buyer_name }}</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">Produto</p>
            <p class="summary-value">{{ contract.product_name }}</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">Valor</p>
            <p class="summary-value">{{ formatCurrency(contract.total_amount, contract.currency) }}</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">Gerado em</p>
            <p class="summary-value">{{ formatDate(contract.generated_at || contract.created_at) }}</p>
          </div>
        </div>
        <div v-if="agencySignature" class="agency-signature-card">
          <p class="agency-signature-eyebrow">Assinatura institucional da contratada</p>
          <div class="agency-signature-visual">
            <img
              v-if="agencySignature.image"
              :src="agencySignature.image"
              alt="Assinatura da agência"
              class="agency-signature-image"
            />
            <p v-else :class="agencySignatureTypedClass">
              {{ agencySignature.typed_value || agencySignature.name }}
            </p>
          </div>
          <p class="agency-signature-name">{{ agencySignature.name }}</p>
          <p v-if="agencySignature.role" class="agency-signature-role">{{ agencySignature.role }}</p>
          <p v-if="agencySignature.company" class="agency-signature-company">{{ agencySignature.company }}</p>
          <p v-if="agencySignature.city" class="agency-signature-company">{{ agencySignature.city }}</p>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Documento</p>
              <h2 class="text-lg font-semibold text-slate-900">Contrato disponível</h2>
            </div>
            <button
              v-if="documentPdfUrl"
              type="button"
              class="btn-secondary"
              @click="openPdf(documentPdfUrl)"
            >
              Abrir PDF
            </button>
          </div>
          <div class="mt-4 rounded-2xl border border-slate-100 bg-slate-50">
            <object
              v-if="documentPdfUrl"
              :data="documentPdfUrl"
              type="application/pdf"
              class="h-[520px] w-full rounded-2xl"
            >
              <p class="p-4 text-sm text-slate-600">
                Abra o PDF em uma nova aba
                <a class="text-emerald-600 underline" :href="documentPdfUrl" target="_blank" rel="noopener"
                  >clicando aqui</a
                >.
              </p>
            </object>
            <p v-else class="p-4 text-sm text-slate-600">Arquivo em processamento.</p>
          </div>
        </div>

        <div class="status-card" :class="isAlreadySigned ? 'status-card--success' : 'status-card--info'">
          <div class="flex flex-wrap items-center gap-3">
            <span :class="['status-badge', signatureBadgeClass(contract.signature_status)]">
              {{ signatureStatusLabel(contract.signature_status) }}
            </span>
            <span v-if="contract.signature_signed_at" class="text-sm font-semibold text-slate-600">
              Assinado em {{ formatDateTime(contract.signature_signed_at) }}
            </span>
          </div>
          <p v-if="agencySignature" class="text-xs text-slate-600">
            A contratada {{ agencySignature.name }} já autorizou este documento.
          </p>
          <p v-if="contract.signature_status === 'pending'" class="text-sm text-slate-600">
            Escolha uma das formas abaixo para concluir a assinatura.
          </p>
          <p v-else-if="contract.signature_status === 'signed'" class="text-sm text-slate-600">
            Documento assinado por {{ contract.signature_name || contract.buyer_name }}.
          </p>
          <div v-if="contract.signed_pdf_url" class="mt-3">
            <button type="button" class="btn-secondary" @click="openPdf(contract.signed_pdf_url)">
              Baixar contrato assinado
            </button>
          </div>
        </div>

        <div
          v-if="isPendingSignature && isReadyForSignature"
          class="space-y-4 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm"
        >
          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="mode-pill"
              :class="signatureMode === 'typed' ? 'mode-pill--active' : ''"
              @click="switchMode('typed')"
            >
              Assinar digitando
            </button>
            <button
              type="button"
              class="mode-pill"
              :class="signatureMode === 'drawn' ? 'mode-pill--active' : ''"
              @click="switchMode('drawn')"
            >
              Assinar desenhando
            </button>
          </div>
          <label class="flex items-start gap-3 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
            <input
              v-model="acceptedTerms"
              type="checkbox"
              class="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600"
            />
            <span>Li e concordo com os termos deste contrato.</span>
          </label>
          <p v-if="signatureError" class="text-sm text-rose-500">{{ signatureError }}</p>
          <TypedSignatureForm
            v-show="signatureMode === 'typed'"
            v-model="typedName"
            :loading="submitting"
            :disabled="!isPendingSignature"
            :can-submit="acceptedTerms"
            @submit="handleTypedSubmit"
          />
          <SignatureDrawPad
            v-show="signatureMode === 'drawn'"
            :loading="submitting"
            :disabled="!isPendingSignature"
            :can-submit="acceptedTerms"
            @submit="handleDrawSubmit"
          />
        </div>

        <div
          v-else-if="isAlreadySigned"
          class="rounded-3xl border border-emerald-100 bg-emerald-50 p-6 shadow-sm text-emerald-900"
        >
          <h3 class="text-xl font-semibold">Contrato assinado com sucesso</h3>
          <p class="mt-2 text-sm">
            {{ contract.signature_name || contract.buyer_name }} confirmou a assinatura em
            {{ formatDateTime(contract.signature_signed_at) }}.
          </p>
          <img
            v-if="contract.signature_image_url"
            :src="contract.signature_image_url"
            alt="Assinatura digital"
            class="mt-4 max-h-48 w-full rounded-xl border border-emerald-100 bg-white p-4"
          />
          <p v-else class="mt-4 text-lg font-semibold">
            {{ contract.signature_name || contract.buyer_name }}
          </p>
          <button
            v-if="contract.signed_pdf_url"
            type="button"
            class="btn-secondary mt-4"
            @click="openPdf(contract.signed_pdf_url)"
          >
            Baixar contrato assinado
          </button>
        </div>

        <div
          v-else-if="!isReadyForSignature"
          class="rounded-3xl border border-slate-100 bg-white p-6 text-sm text-slate-600 shadow-sm"
        >
          Estamos preparando o documento. Volte em alguns instantes para concluir a assinatura.
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { isAxiosError } from "axios";
import TypedSignatureForm from "../../components/legal/TypedSignatureForm.vue";
import SignatureDrawPad from "../../components/legal/SignatureDrawPad.vue";
import {
  getPublicSignatureContract,
  submitSignatureContract,
} from "../../services/legal";
import type { LegalContractSignaturePublic } from "../../types/legal";

type SignatureMode = "typed" | "drawn";

const route = useRoute();
const router = useRouter();
const token = computed(() => String(route.params.token || ""));

const loading = ref(true);
const submitting = ref(false);
const contract = ref<LegalContractSignaturePublic | null>(null);
const errorMessage = ref("");
const signatureMode = ref<SignatureMode>("typed");
const typedName = ref("");
const acceptedTerms = ref(false);
const signatureError = ref("");

const signatureLabels: Record<string, string> = {
  pending: "Pendente",
  signed: "Assinado",
};

const signatureStatusLabel = (status: string) => signatureLabels[status] || status;

const signatureBadgeClass = (status: string) => {
  if (status === "signed") return "status-badge--success";
  return "status-badge--muted";
};

const loadContract = async () => {
  if (!token.value) {
    errorMessage.value = "Link de assinatura inválido.";
    loading.value = false;
    return;
  }
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await getPublicSignatureContract(token.value);
    contract.value = data;
    typedName.value = data.buyer_name || "";
    acceptedTerms.value = false;
    signatureMode.value = data.signature_type === "drawn" ? "drawn" : "typed";
    signatureError.value = "";
  } catch (error) {
    console.error("Erro ao carregar contrato para assinatura", error);
    errorMessage.value = extractErrorMessage(error) ?? "Não foi possível carregar este contrato.";
    contract.value = null;
  } finally {
    loading.value = false;
  }
};

watch(
  () => token.value,
  () => {
    loadContract();
  },
  { immediate: true }
);

const isReadyForSignature = computed(() => contract.value?.status === "generated");
const isPendingSignature = computed(
  () => isReadyForSignature.value && contract.value?.signature_status === "pending"
);
const isAlreadySigned = computed(() => contract.value?.signature_status === "signed");
const documentPdfUrl = computed(() => contract.value?.signed_pdf_url || contract.value?.pdf_url || null);
const agencySignature = computed(() => {
  if (contract.value?.agency_signature_status !== "signed") return null;
  return {
    name: contract.value.agency_signature_name,
    role: contract.value.agency_signature_role,
    company: contract.value.agency_signature_company,
    city: contract.value.agency_signature_city,
    type: contract.value.agency_signature_type,
    typed_value: contract.value.agency_signature_typed_value,
    font_style: contract.value.agency_signature_font_style || "classic",
    image: contract.value.agency_signature_image_url,
  };
});
const agencySignatureTypedClass = computed(() => {
  const style = agencySignature.value?.font_style || "classic";
  return `agency-signature-preview__typed agency-signature-preview__typed--${style}`;
});

const switchMode = (mode: SignatureMode) => {
  signatureMode.value = mode;
  signatureError.value = "";
};

const handleTypedSubmit = () => {
  signatureError.value = "";
  const name = typedName.value.trim();
  if (name.length < 3) {
    signatureError.value = "Informe seu nome completo para assinar.";
    return;
  }
  submitSignature("typed", { fullName: name });
};

const handleDrawSubmit = (image: string) => {
  signatureError.value = "";
  if (!image) {
    signatureError.value = "Desenhe sua assinatura para continuar.";
    return;
  }
  submitSignature("drawn", { image });
};

const submitSignature = async (
  type: SignatureMode,
  extra: { fullName?: string; image?: string }
) => {
  if (!contract.value) return;
  if (!acceptedTerms.value) {
    signatureError.value = "É necessário aceitar os termos para assinar.";
    return;
  }
  submitting.value = true;
  signatureError.value = "";
  try {
    const { data } = await submitSignatureContract(token.value, {
      signature_type: type,
      full_name: extra.fullName,
      signature_image: extra.image,
      accepted_terms: true,
    });
    contract.value = data.detail;
    acceptedTerms.value = false;
    signatureError.value = "";
    router.push({ name: "contract-signature-success", params: { token: token.value } });
  } catch (error) {
    console.error("Erro ao enviar assinatura", error);
    signatureError.value = extractErrorMessage(error) ?? "Não foi possível registrar sua assinatura.";
  } finally {
    submitting.value = false;
  }
};

const openPdf = (url: string) => {
  window.open(url, "_blank");
};

const formatCurrency = (amountCents: number, currency: string) => {
  const amount = amountCents / 100;
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currency || "BRL",
    minimumFractionDigits: 2,
  }).format(amount);
};

const formatDate = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const day = date.toLocaleDateString("pt-BR");
  const time = date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${day} ${time}`;
};

const extractErrorMessage = (error: unknown) => {
  if (isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string })?.detail;
    return detail;
  }
  return undefined;
};
</script>

<style scoped>
.summary-card {
  @apply rounded-3xl border border-slate-100 bg-white p-5 shadow-sm;
}
.summary-label {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.summary-value {
  @apply mt-1 text-lg font-semibold text-slate-900;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:border-emerald-400 hover:text-emerald-600;
}
.status-card {
  @apply rounded-3xl border border-slate-100 bg-white p-5 shadow-sm;
}
.status-card--success {
  @apply border-emerald-200 bg-emerald-50;
}
.status-card--info {
  @apply border-slate-100 bg-white;
}
.status-card--error {
  @apply border-rose-200 bg-rose-50;
}
.status-badge {
  @apply rounded-full px-3 py-1 text-xs font-semibold;
}
.status-badge--success {
  @apply bg-emerald-100 text-emerald-700;
}
.status-badge--muted {
  @apply bg-slate-100 text-slate-600;
}
.mode-pill {
  @apply rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-emerald-400 hover:text-emerald-600;
}
.mode-pill--active {
  @apply border-emerald-300 bg-emerald-50 text-emerald-700 shadow-inner;
}
.agency-signature-card {
  @apply rounded-3xl border border-slate-100 bg-white p-5 shadow-sm;
}
.agency-signature-eyebrow {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.agency-signature-visual {
  @apply mt-3 flex items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4;
  min-height: 140px;
}
.agency-signature-image {
  max-width: 220px;
  max-height: 70px;
}
.agency-signature-name {
  @apply mt-4 text-lg font-semibold text-slate-900 text-center;
}
.agency-signature-role,
.agency-signature-company {
  @apply text-xs text-slate-500 text-center;
}
.agency-signature-preview__typed {
  font-size: 20px;
  margin: 0;
}
.agency-signature-preview__typed--classic {
  font-family: "Times New Roman", serif;
  font-style: italic;
}
.agency-signature-preview__typed--cursive {
  font-family: "Georgia", serif;
  font-style: italic;
}
.agency-signature-preview__typed--elegant {
  font-family: "Arial", sans-serif;
  font-weight: 600;
  letter-spacing: 0.15em;
}
</style>
