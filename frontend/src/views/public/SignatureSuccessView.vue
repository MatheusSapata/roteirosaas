<template>
  <div class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-4xl space-y-6">
      <div v-if="loading" class="card">
        <p class="text-sm text-slate-600">Preparando sua confirmação...</p>
      </div>

      <div v-else-if="errorMessage" class="card card--error">
        <p class="text-sm text-rose-600">{{ errorMessage }}</p>
        <button type="button" class="btn-secondary mt-3" @click="loadContract">Tentar novamente</button>
      </div>

      <template v-else-if="contract">
        <PublicBrandHeader
          :agency-name="contract.agency_name"
          :agency-logo="contract.agency_logo_url"
          :platform-name="platformName"
          :platform-logo="platformLogo"
        />

        <section class="card hero-card">
          <div class="hero-icon">✔</div>
          <div class="hero-content">
            <p class="eyebrow">Documento assinado</p>
            <h1 class="hero-title">Assinatura concluída com sucesso</h1>
            <p class="hero-subtitle">
              Sua assinatura foi registrada com integridade verificável. O documento já pode ser validado online.
            </p>
          </div>
          <div class="hero-actions">
            <button type="button" class="btn-primary" :disabled="!contract.verification_url" @click="openVerification">
              Verificar documento
            </button>
            <button type="button" class="btn-secondary" :disabled="!contract.signed_pdf_url" @click="openSignedPdf">
              Abrir PDF assinado
            </button>
            <button type="button" class="btn-ghost" :disabled="!verificationLink" @click="copyVerificationLink">
              Copiar link de verificação
            </button>
          </div>
        </section>

        <section class="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div class="card">
            <p class="eyebrow">Resumo da assinatura</p>
            <div class="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p class="label">Assinante</p>
                <p class="value">{{ contract.signature_name || contract.buyer_name }}</p>
              </div>
              <div>
                <p class="label">Agência responsável</p>
                <p class="value">{{ contract.agency_name || "Agência" }}</p>
              </div>
              <div>
                <p class="label">Data e hora</p>
                <p class="value">{{ formatDateTime(contract.signature_signed_at) }}</p>
              </div>
              <div>
                <p class="label">Contrato</p>
                <p class="value">#{{ contract.contract_id }}</p>
              </div>
            </div>

            <div class="mt-6 rounded-2xl bg-slate-50 p-4 text-xs text-slate-500">
              Este documento foi registrado na plataforma {{ platformName }} com hash criptográfico para garantir sua
              integridade.
            </div>

            <div class="mt-6 grid gap-3 sm:grid-cols-2">
              <div class="status-pill status-pill--success">
                Cliente: {{ signatureStatusLabel(contract.signature_status) }}
              </div>
              <div class="status-pill status-pill--success">
                Agência: {{ signatureStatusLabel(contract.agency_signature_status) }}
              </div>
            </div>
          </div>

          <div class="card">
            <p class="eyebrow">QR code de verificação</p>
            <div class="mt-4 flex flex-col items-center gap-4 rounded-2xl border border-dashed border-slate-200 p-5">
              <img
                v-if="contract.verification_qr_image_data"
                :src="contract.verification_qr_image_data"
                alt="QR Code de verificação"
                class="h-40 w-40"
              />
              <div v-else class="qr-fallback">QR indisponível</div>
              <p class="text-center text-xs text-slate-500">{{ verificationLink }}</p>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { isAxiosError } from "axios";
import PublicBrandHeader from "../../components/legal/PublicBrandHeader.vue";
import PlatformLogo from "../../assets/sidebar-logo.svg";
import { getPublicSignatureContract } from "../../services/legal";
import type { LegalContractSignaturePublic } from "../../types/legal";

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const contract = ref<LegalContractSignaturePublic | null>(null);
const errorMessage = ref("");
const platformName = "Roteiro Online";
const platformLogo = PlatformLogo;

const loadContract = async () => {
  loading.value = true;
  errorMessage.value = "";
  const token = String(route.params.token || "").trim();
  if (!token) {
    errorMessage.value = "Link inválido.";
    loading.value = false;
    return;
  }
  try {
    const { data } = await getPublicSignatureContract(token);
    if (data.signature_status !== "signed") {
      router.replace({ name: "contract-signature", params: { token } });
      return;
    }
    contract.value = data;
  } catch (error) {
    if (isAxiosError(error)) {
      errorMessage.value = (error.response?.data as { detail?: string })?.detail || "Assinatura não encontrada.";
    } else {
      errorMessage.value = "Não foi possível carregar os dados da assinatura.";
    }
  } finally {
    loading.value = false;
  }
};

onMounted(loadContract);

const verificationLink = computed(() => contract.value?.verification_url || contract.value?.signature_link || "");

const openVerification = () => {
  if (!contract.value?.verification_url) return;
  window.open(contract.value.verification_url, "_blank");
};

const openSignedPdf = () => {
  if (!contract.value?.signed_pdf_url) return;
  window.open(contract.value.signed_pdf_url, "_blank");
};

const copyVerificationLink = async () => {
  const target = verificationLink.value;
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
    console.error("Não foi possível copiar o link de verificação", error);
  }
};

const signatureStatusLabel = (status?: string | null) => {
  if (!status) return "Indisponível";
  if (status === "signed") return "Assinado";
  if (status === "pending") return "Pendente";
  return status;
};

const formatDateTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const day = date.toLocaleDateString("pt-BR");
  const time = date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${day} ${time}`;
};
</script>

<style scoped>
.card {
  @apply rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.card--error {
  @apply border-rose-200 bg-rose-50;
}
.btn-primary {
  @apply rounded-full bg-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-emerald-600;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:border-emerald-400 hover:text-emerald-600;
}
.btn-ghost {
  @apply rounded-full border border-transparent px-4 py-2 text-sm font-semibold text-slate-600 transition hover:text-emerald-600;
}
.hero-card {
  @apply flex flex-col gap-4;
}
.hero-icon {
  @apply flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-3xl text-emerald-700;
}
.hero-actions {
  @apply flex flex-wrap gap-3;
}
.hero-title {
  @apply text-2xl font-semibold text-slate-900;
}
.hero-subtitle {
  @apply mt-1 text-sm text-slate-600;
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
.status-pill {
  @apply rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700;
}
.qr-fallback {
  @apply flex h-40 w-40 items-center justify-center rounded-2xl border border-dashed border-slate-300 text-xs font-semibold text-slate-500;
}
</style>
