<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-4xl space-y-6">
      <div v-if="loading" class="card">
        <p class="text-sm text-slate-600">Validando documento...</p>
      </div>

      <div v-else-if="errorMessage" class="card card--error">
        <p class="text-sm text-rose-600">{{ errorMessage }}</p>
        <button type="button" class="btn-secondary mt-3" @click="loadDetail">Tentar novamente</button>
      </div>

      <template v-else-if="detail">
        <PublicBrandHeader
          :agency-name="detail.agency_name"
          :agency-logo="detail.agency_logo_url"
          :platform-name="platformName"
          :platform-logo="platformLogo"
        />

        <section class="card hero-card">
          <div class="hero-icon">✔</div>
          <div class="hero-content">
            <p class="eyebrow">Documento verificado</p>
            <h1 class="hero-title">Documento válido e íntegro</h1>
            <p class="hero-subtitle">
              {{ detail.message || "Este documento corresponde ao registro original armazenado em nossa plataforma." }}
            </p>
          </div>
          <div class="hero-status">
            <span :class="['status-pill', statusToneClass(detail.status)]">{{ statusLabel(detail.status) }}</span>
            <span class="hero-id">ID #{{ detail.contract_id }}</span>
          </div>
          <div class="hero-actions">
            <button type="button" class="btn-primary" :disabled="!detail.verification_url" @click="openVerificationPage">
              Verificar documento
            </button>
            <button
              type="button"
              class="btn-secondary"
              :disabled="!detail.verification_url"
              @click="copyLink(verificationLink)"
            >
              Copiar link de verificação
            </button>
          </div>
        </section>

        <section class="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <div class="card">
            <p class="eyebrow">Resumo do documento</p>
            <div class="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p class="label">Comprador</p>
                <p class="value">{{ detail.buyer_name || "Não informado" }}</p>
              </div>
              <div>
                <p class="label">Agência</p>
                <p class="value">{{ detail.agency_name || "Não informado" }}</p>
              </div>
              <div>
                <p class="label">Produto</p>
                <p class="value">{{ detail.product_name || "Contrato" }}</p>
              </div>
              <div>
                <p class="label">Gerado em</p>
                <p class="value">{{ formatDate(detail.generated_at || detail.created_at) }}</p>
              </div>
              <div>
                <p class="label">Assinado em</p>
                <p class="value">{{ formatDateTime(detail.signature_signed_at) || "Pendente" }}</p>
              </div>
              <div>
                <p class="label">Tipo de assinatura</p>
                <p class="value">{{ signatureLabel(detail.signature_type) }}</p>
              </div>
            </div>

            <div class="mt-6 rounded-2xl bg-slate-50 p-4 text-xs text-slate-500">
              Este documento é autêntico e foi validado com base no registro original armazenado em nossa plataforma.
            </div>
          </div>

          <div class="card">
            <p class="eyebrow">Integridade e QR code</p>

            <div class="mt-4 flex flex-col items-center gap-4 rounded-2xl border border-dashed border-slate-200 p-4">
              <img
                v-if="detail.verification_qr_image_data"
                :src="detail.verification_qr_image_data"
                alt="QR Code"
                class="h-40 w-40"
              />
              <p class="text-sm font-semibold text-slate-700">Escaneie para validar este documento</p>
              <p class="break-all text-xs text-slate-500">{{ verificationLink }}</p>
              <button type="button" class="btn-secondary" @click="copyLink(verificationLink)">
                Copiar link
              </button>
            </div>

            <div class="mt-6 space-y-2">
              <p class="label">Hash ({{ (detail.document_hash_algorithm || "SHA-256").toUpperCase() }})</p>
              <p class="hash-box">{{ detail.document_hash || "Em processamento" }}</p>
            </div>
            <p class="mt-2 text-xs text-slate-500">
              Tamanho do PDF: {{ formatBytes(detail.signed_pdf_size_bytes) || "—" }}
            </p>
          </div>
        </section>

        <section class="grid gap-5 lg:grid-cols-2">
          <DocumentStatusSummary
            :items="documentStatusItems"
            :footer-text="documentStatusFooter"
            class="h-full"
          />
          <div class="card">
            <p class="eyebrow">PDF assinado</p>
            <p class="mt-2 text-sm text-slate-600">
              Acesse o PDF final para confer?ncia visual do documento assinado e registrado.
            </p>

            <div class="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                class="btn-primary"
                :disabled="!detail.signed_pdf_url"
                @click="openPdf(detail.signed_pdf_url || detail.pdf_url)"
              >
                Abrir PDF assinado
              </button>
              <button
                type="button"
                class="btn-secondary"
                :disabled="!detail.pdf_url"
                @click="openPdf(detail.pdf_url)"
              >
                Vers?o original
              </button>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { isAxiosError } from "axios";
import PublicBrandHeader from "../../components/legal/PublicBrandHeader.vue";
import DocumentStatusSummary from "../../components/legal/DocumentStatusSummary.vue";
import PlatformLogo from "../../assets/sidebar-logo.svg";
import { getPublicContractVerification } from "../../services/legal";
import type { LegalContractVerificationDetail, LegalContractVerificationStatus } from "../../types/legal";

const route = useRoute();
const loading = ref(true);
const detail = ref<LegalContractVerificationDetail | null>(null);
const errorMessage = ref("");
const currentUrl = window.location.href;
const platformName = "Roteiro Online";
const platformLogo = PlatformLogo;
const verificationToken = computed(() => String(route.params.token || "").trim());

const statusLabels: Record<LegalContractVerificationStatus, string> = {
  valid: "Documento válido",
  pending: "Assinatura pendente",
  incomplete: "Verificação em processamento",
  invalid: "Documento inválido",
  not_found: "Documento não encontrado",
};

const loadDetail = async () => {
  loading.value = true;
  errorMessage.value = "";
  detail.value = null;
  const token = verificationToken.value;

  try {
    const { data } = await getPublicContractVerification(token);
    detail.value = data;
  } catch (error) {
    if (isAxiosError(error)) {
      errorMessage.value =
        (error.response?.data as { detail?: string })?.detail || "Nǜo foi poss��vel verificar o documento.";
    } else {
      errorMessage.value = "Nǜo foi poss��vel verificar o documento.";
    }
  } finally {
    loading.value = false;
  }
};

onMounted(loadDetail);

const verificationLink = computed(() => detail.value?.verification_url || currentUrl);

const statusLabel = (status: LegalContractVerificationStatus) => statusLabels[status] || "Status indisponível";

const statusToneClass = (status: LegalContractVerificationStatus) => {
  switch (status) {
    case "valid":
      return "status-pill--success";
    case "pending":
    case "incomplete":
      return "status-pill--warning";
    default:
      return "status-pill--danger";
  }
};

const signatureLabel = (value?: string | null) => {
  if (!value) return "Não informado";
  if (value === "typed") return "Assinatura digitada";
  if (value === "drawn") return "Assinatura desenhada";
  return value;
};
type DocumentStatusItem = {
  id: string;
  title: string;
  description?: string;
};

const documentStatusItems = computed<DocumentStatusItem[]>(() => {
  const current = detail.value;
  if (!current) return [];
  const items: DocumentStatusItem[] = [];

  if (current.agency_signature_status === "signed") {
    items.push({
      id: "agency_signature",
      title: "Assinatura institucional aplicada",
      description: current.agency_signature_signed_at
        ? `Concluída em ${formatDateTime(current.agency_signature_signed_at)}`
        : undefined
    });
  }

  if (current.signature_status === "signed") {
    items.push({
      id: "customer_signature",
      title: "Cliente assinou o contrato",
      description: current.signature_signed_at ? `Concluída em ${formatDateTime(current.signature_signed_at)}` : undefined
    });
  }

  if (current.signed_pdf_url || current.signed_pdf_generated_at) {
    items.push({
      id: "signed_pdf",
      title: "Documento final consolidado",
      description: current.signed_pdf_generated_at
        ? `Disponível desde ${formatDateTime(current.signed_pdf_generated_at)}`
        : "Versão assinada pronta para consulta."
    });
  }

  if (current.document_hash) {
    items.push({
      id: "document_hash",
      title: "Integridade verificada",
      description: `Hash ${String(current.document_hash_algorithm || "SHA-256").toUpperCase()} calculado`
    });
  }

  if (current.verification_url) {
    items.push({
      id: "public_verification",
      title: "Verificação pública liberada",
      description: current.verification_generated_at
        ? `Publicado em ${formatDateTime(current.verification_generated_at)}`
        : "Link público disponível."
    });
  }

  return items;
});

const documentStatusFooter = computed(() => {
  const current = detail.value;
  if (
    current &&
    current.agency_signature_status === "signed" &&
    current.signature_status === "signed" &&
    current.document_hash &&
    current.verification_url
  ) {
    return "✔ Documento seguro e totalmente validado";
  }
  return documentStatusItems.value.length ? "Etapas essenciais concluídas" : null;
});

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

const formatBytes = (value?: number | null) => {
  if (!value || value <= 0) return "";
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

const copyLink = async (target: string) => {
  if (!target) return;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(target);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = target;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
  } catch (error) {
    console.error("Falha ao copiar link de verificação", error);
  }
};

const openPdf = (url?: string | null) => {
  if (!url) return;
  window.open(url, "_blank");
};

const openVerificationPage = () => {
  if (!detail.value?.verification_url) return;
  window.open(detail.value.verification_url, "_blank");
};
</script>

<style scoped>
.card {
  @apply rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.card--error {
  @apply border-rose-200 bg-rose-50;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:border-emerald-400 hover:text-emerald-600;
}
.btn-primary {
  @apply rounded-full bg-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-emerald-600;
}
.hero-card {
  @apply flex flex-col gap-4 lg:flex-row lg:items-center;
}
.hero-icon {
  @apply flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-3xl text-emerald-700;
}
.hero-content {
  @apply flex-1;
}
.hero-title {
  @apply text-2xl font-semibold text-slate-900;
}
.hero-subtitle {
  @apply text-sm text-slate-600;
}
.hero-status {
  @apply flex flex-col items-start gap-1;
}
.hero-id {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.hero-actions {
  @apply flex flex-wrap gap-3;
}
.eyebrow {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.label {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.value {
  @apply mt-1 text-base font-semibold text-slate-900;
}
.hash-box {
  @apply mt-1 rounded-2xl bg-slate-900/90 p-3 font-mono text-xs text-emerald-200;
  word-break: break-all;
}
.status-pill {
  @apply rounded-full px-3 py-1 text-xs font-semibold;
}
.status-pill--success {
  @apply bg-emerald-100 text-emerald-700;
}
.status-pill--warning {
  @apply bg-amber-100 text-amber-700;
}
.status-pill--danger {
  @apply bg-rose-100 text-rose-700;
}
</style>
