<template>
  <section
    v-if="section.enabled !== false"
    :id="section.anchorId || undefined"
    class="px-4 py-12 sm:px-6 lg:px-12"
    :style="{ background: sectionBackground }"
  >
    <div class="mx-auto w-full max-w-6xl">
      <div
        class="flex flex-col gap-10"
        :class="{
          'md:flex-row md:items-start md:justify-between': layoutMode !== 'stacked',
          'md:flex-col': layoutMode === 'stacked'
        }"
      >
        <div class="flex-1 space-y-8">
          <div class="max-w-2xl space-y-4">
            <p
              :class="[
                'text-[11px] font-semibold uppercase tracking-[0.45em]',
                isLight ? 'text-slate-500' : 'text-white/45'
              ]"
            >
              Agência
            </p>

            <div class="space-y-3">
              <h4 :class="['text-xl font-semibold tracking-tight sm:text-2xl', textPrimaryClass]">
                {{ companyName || "Sua agência cadastrada" }}
              </h4>

              <p v-if="cnpjText" :class="['text-sm', textSecondaryClass]">
                <span class="font-medium">CNPJ</span>
                <span class="ml-2">{{ cnpjText }}</span>
              </p>
            </div>
          </div>

          <!-- REDES SOCIAIS MOBILE -->
          <div
            v-if="socialLinks.length"
            :class="[
              'md:hidden rounded-[22px] border p-4',
              isLight ? 'border-slate-200 bg-white/70' : 'border-white/15 bg-white/5'
            ]"
          >
            <div class="flex flex-col items-center gap-4 text-center">
              <p
                :class="[
                  'text-xs font-semibold uppercase tracking-[0.3em]',
                  isLight ? 'text-slate-500' : 'text-white/60'
                ]"
              >
                Acesse agora nossas redes sociais
              </p>

              <div class="flex gap-3">
                <a
                  v-for="link in socialLinks"
                  :key="`mobile-${link.network}`"
                  :class="[
                    'inline-flex h-10 w-10 items-center justify-center rounded-full border transition',
                    isLight
                      ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'
                      : 'border-white/20 bg-white/5 text-white hover:bg-white/20'
                  ]"
                  :href="link.url"
                  target="_blank"
                  rel="noopener"
                >
                  <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor">
                    <path :d="link.iconPath" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- CONTATOS / ENDEREÇO -->
          <div class="grid gap-6 text-sm md:grid-cols-2">
            <div class="space-y-2">
              <p
                :class="[
                  'text-xs font-semibold uppercase tracking-widest',
                  isLight ? 'text-slate-500' : 'text-white/50'
                ]"
              >
                Contatos
              </p>

              <template v-if="hasContactInfo">
                <p v-if="phoneText" :class="['font-medium', textPrimaryClass]">
                  Telefone:
                  <span :class="['font-normal', textSecondaryClass]">{{ phoneText }}</span>
                </p>

                <p v-if="contactEmail" :class="textPrimaryClass">
                  Email:
                  <a class="text-emerald-600 hover:underline" :href="`mailto:${contactEmail}`">
                    {{ contactEmail }}
                  </a>
                </p>
              </template>

              <p v-else :class="textSecondaryClass">
                Atualize os contatos da agência para exibir telefone e email.
              </p>
            </div>

            <div class="space-y-2">
              <p
                :class="[
                  'text-xs font-semibold uppercase tracking-widest',
                  isLight ? 'text-slate-500' : 'text-white/50'
                ]"
              >
                Endereço
              </p>

              <template v-if="addressText">
                <p :class="['font-medium', textPrimaryClass]">
                  {{ addressLine1 }}
                </p>
                <p v-if="addressLine2" :class="textSecondaryClass">
                  {{ addressLine2 }}
                </p>
              </template>

              <p v-else :class="textSecondaryClass">
                Informe CEP e endereço completos nas configurações.
              </p>
            </div>
          </div>

          <!-- REDES SOCIAIS DESKTOP -->
          <div
            v-if="socialLinks.length"
            :class="[
              'hidden md:block rounded-[22px] border p-4',
              isLight ? 'border-slate-200 bg-white/70' : 'border-white/15 bg-white/5'
            ]"
          >
            <div class="flex flex-col items-center gap-4 text-center md:flex-col md:items-start md:text-left lg:flex-row lg:items-center lg:justify-between">
              <p
                :class="[
                  'text-xs font-semibold uppercase tracking-[0.3em]',
                  isLight ? 'text-slate-500' : 'text-white/60'
                ]"
              >
                Acesse agora nossas redes sociais
              </p>

              <div class="flex gap-3">
                <a
                  v-for="link in socialLinks"
                  :key="`desktop-${link.network}`"
                  :class="[
                    'inline-flex h-10 w-10 items-center justify-center rounded-full border transition',
                    isLight
                      ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'
                      : 'border-white/20 bg-white/5 text-white hover:bg-white/20'
                  ]"
                  :href="link.url"
                  target="_blank"
                  rel="noopener"
                >
                  <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor">
                    <path :d="link.iconPath" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- MAPA MOBILE -->
          <div v-if="mapEmbedUrl" class="w-full md:hidden">
            <div :class="['flex items-center justify-between pb-3 text-xs font-semibold', textSecondaryClass]">
              <span>Localização da agência</span>

              <a
                v-if="mapLink"
                :href="mapLink"
                :class="[
                  'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[10px] uppercase tracking-widest transition',
                  isLight
                    ? 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                    : 'border-white/20 text-emerald-300 hover:bg-white/10'
                ]"
                target="_blank"
                rel="noopener"
              >
                Abrir no Maps
                <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M7 17 17 7M7 7h10v10" />
                </svg>
              </a>
            </div>

            <div
              :class="[
                'overflow-hidden rounded-[24px] border shadow-inner',
                isLight ? 'border-slate-200 bg-white/70' : 'border-white/10 bg-white/5'
              ]"
            >
              <iframe
                class="h-80 w-full"
                :src="mapEmbedUrl"
                frameborder="0"
                loading="lazy"
              ></iframe>
            </div>
          </div>

          <!-- CADASTUR -->
          <a
            v-if="shouldShowCadastur && cadasturLink"
            :href="cadasturLink"
            :class="[cadasturWrapperClasses, 'w-full justify-center md:w-fit md:justify-start']"
            target="_blank"
            rel="noopener"
          >
            <img :src="cadasturLogo" alt="Cadastur" class="h-6 w-auto sm:h-4 md:h-6" />
          </a>
        </div>

        <!-- MAPA DESKTOP -->
        <div
          v-if="mapEmbedUrl"
          class="hidden w-full md:block md:w-[420px] md:flex-shrink-0"
        >
          <div :class="['flex items-center justify-between pb-3 text-xs font-semibold', textSecondaryClass]">
            <span>Localização da agência</span>

            <a
              v-if="mapLink"
              :href="mapLink"
              :class="[
                'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[10px] uppercase tracking-widest transition',
                isLight
                  ? 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                  : 'border-white/20 text-emerald-300 hover:bg-white/10'
              ]"
              target="_blank"
              rel="noopener"
            >
              Abrir no Maps
              <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M7 17 17 7M7 7h10v10" />
              </svg>
            </a>
          </div>

          <div
            :class="[
              'overflow-hidden rounded-[24px] border shadow-inner',
              isLight ? 'border-slate-200 bg-white/70' : 'border-white/10 bg-white/5'
            ]"
          >
            <iframe
              class="h-80 w-full"
              :src="mapEmbedUrl"
              frameborder="0"
              loading="lazy"
            ></iframe>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { siFacebook, siInstagram, siTiktok, siYoutube } from "simple-icons";
import type { AgencyFooterSection } from "../../types/page";
import type { AgencySocialNetwork } from "../../store/useAgencyStore";
import cadasturLogo from "../../assets/cadastur-logo.png";
import { PUBLIC_BRANDING_KEY } from "../../utils/brandingKeys";

const props = defineProps<{
  section: AgencyFooterSection;
  branding?: Record<string, any>;
  previewDevice?: "desktop" | "mobile";
}>();

const providedBranding = inject(PUBLIC_BRANDING_KEY, null) as any;

const resolvedBranding = computed<Record<string, any>>(() => {
  if (props.branding) return props.branding;
  if (providedBranding && typeof providedBranding === "object" && "value" in providedBranding) {
    return providedBranding.value as Record<string, any>;
  }
  return providedBranding || {};
});

const agencyProfile = computed<Record<string, any>>(() => resolvedBranding.value?.agency_profile || {});

const companyName = computed(() => agencyProfile.value?.name || resolvedBranding.value?.agency_name || "");
const cnpjText = computed(() => formatCnpj(agencyProfile.value?.cnpj));
const contactEmail = computed(() => agencyProfile.value?.email || "");
const phoneText = computed(() => formatPhone(agencyProfile.value?.phone || ""));
const hasContactInfo = computed(() => !!phoneText.value || !!contactEmail.value);

const address = computed(() => agencyProfile.value?.address || {});
const addressLine1 = computed(() => {
  const street = address.value?.street;
  const number = address.value?.number;
  const complement = address.value?.complement;
  return [street, number, complement].filter(Boolean).join(", ");
});
const addressLine2 = computed(() => {
  const neighborhood = address.value?.neighborhood;
  const city = address.value?.city;
  const state = address.value?.state;
  const zipcode = address.value?.zipcode;
  return [neighborhood, city, state, zipcode].filter(Boolean).join(", ");
});
const addressText = computed(() => agencyProfile.value?.address_text || addressLine1.value || addressLine2.value || "");

const mapEmbedUrl = computed(() => agencyProfile.value?.map_embed_url || buildMapUrl(addressText.value));
const mapLink = computed(() => {
  const query = agencyProfile.value?.map_query || addressText.value;
  return query ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}` : "";
});

const SOCIAL_ICON_MAP: Record<AgencySocialNetwork, string> = {
  instagram: siInstagram.path,
  facebook: siFacebook.path,
  youtube: siYoutube.path,
  tiktok: siTiktok.path
};

const SOCIAL_LABELS: Record<AgencySocialNetwork, string> = {
  instagram: "Instagram",
  facebook: "Facebook",
  youtube: "YouTube",
  tiktok: "TikTok"
};

const socialLinks = computed(() => {
  const links = Array.isArray(agencyProfile.value?.social_links) ? agencyProfile.value.social_links : [];
  return links
    .filter(link => typeof link?.network === "string" && typeof link?.url === "string")
    .map(link => ({
      ...link,
      network: link.network as AgencySocialNetwork,
      iconPath: SOCIAL_ICON_MAP[link.network as AgencySocialNetwork],
      label: SOCIAL_LABELS[link.network as AgencySocialNetwork]
    }))
    .filter(link => !!link.iconPath);
});

const cadasturLink = computed(() => agencyProfile.value?.cadastur_url || buildCadasturLink(agencyProfile.value?.cnpj_digits));
const shouldShowCadastur = computed(() => props.section.showCadastur !== false);

const layoutMode = computed(() => props.section.displayVariant || "auto");
const sectionBackground = computed(() => props.section.backgroundColor || resolvedBranding.value?.primary_color || "#05060f");

const isLight = computed(() => isLightBackground(sectionBackground.value));

const textPrimaryClass = computed(() =>
  isLight.value ? "text-slate-900" : "text-white"
);

const textSecondaryClass = computed(() =>
  isLight.value ? "text-slate-600" : "text-white/70"
);

const cadasturWrapperClasses = computed(() => {
  const base =
    "inline-flex items-center rounded-2xl px-6 py-3 transition hover:scale-[1.02]";

  return isLight.value
    ? `${base} bg-transparent`
    : `${base} bg-white shadow-sm`;
});

function formatCnpj(value?: string | null) {
  if (!value) return "";
  const digits = value.replace(/\D/g, "").slice(0, 14);
  if (!digits) return "";
  return digits
    .replace(/(\d{2})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1/$2")
    .replace(/(\d{4})(\d{1,2})$/, "$1-$2");
}

function formatPhone(value?: string | null) {
  if (!value) return "";
  const digits = value.replace(/\D/g, "");
  if (!digits) return "";
  if (digits.length === 10) {
    return digits.replace(/(\d{2})(\d{4})(\d{4})/, "($1) $2-$3");
  }
  if (digits.length >= 11) {
    return digits.replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
  }
  return value;
}

function buildMapUrl(query?: string) {
  if (!query) return "";
  return `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`;
}

function buildCadasturLink(cnpjDigits?: string | null) {
  if (!cnpjDigits) return "";
  return `https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/${cnpjDigits.replace(/\D/g, "")}`;
}

function parseColor(value?: string | null): { r: number; g: number; b: number } | null {
  if (!value) return null;
  const trimmed = value.trim();

  if (trimmed.startsWith("#")) {
    let hex = trimmed.slice(1);
    if (hex.length === 3) {
      hex = hex
        .split("")
        .map(char => char + char)
        .join("");
    }
    if (hex.length !== 6) return null;
    const num = Number.parseInt(hex, 16);
    if (Number.isNaN(num)) return null;
    return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
  }

  if (trimmed.startsWith("rgb")) {
    const parts = trimmed
      .replace(/[rgba()]/g, "")
      .split(",")
      .map(part => Number(part.trim()));

    if (parts.length >= 3 && parts.every(n => Number.isFinite(n))) {
      return { r: parts[0], g: parts[1], b: parts[2] };
    }
  }

  return null;
}

function isLightBackground(color?: string | null) {
  const rgb = parseColor(color);
  if (!rgb) return false;
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
  return luminance >= 0.55;
}
</script>