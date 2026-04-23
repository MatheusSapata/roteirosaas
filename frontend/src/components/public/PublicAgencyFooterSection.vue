<template>
  <section
    v-if="section.enabled !== false"
    :id="section.anchorId || undefined"
    class="px-4 py-12 sm:px-6"
    :style="{ background: sectionBackground }"
  >
    <div class="mx-auto w-full max-w-6xl px-6">
      <div
        class="flex flex-col gap-10"
        :class="layoutClass"
      >
        <div class="flex-1 space-y-8">
          <div class="max-w-2xl space-y-4">
            <p
              :class="[
                'text-[11px] font-semibold uppercase tracking-[0.45em]',
                isLight ? 'text-slate-500' : 'text-white/45'
              ]"
            >
              {{ agencyHeadingText }}
            </p>

            <div class="space-y-3">
              <h4 :class="['text-xl font-semibold tracking-tight sm:text-2xl', textPrimaryClass]">
                {{ companyName || fallbackCompanyName }}
              </h4>

              <p v-if="cnpjText" :class="['text-sm', textSecondaryClass]">
                <span class="font-medium">{{ cnpjLabel }}</span>
                <span class="ml-2">{{ cnpjText }}</span>
              </p>
            </div>
          </div>

          <!-- REDES SOCIAIS MOBILE -->
          <div
            v-if="socialLinks.length"
            :class="[
              mobileOnlyClass,
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
                {{ socialHeading }}
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
                  <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" :style="{ color: socialIconColor }">
                    <path :d="link.iconPath" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- CONTATOS / ENDEREÇO -->
          <div :class="['grid gap-6 text-sm', isMobilePreview ? 'grid-cols-1' : 'md:grid-cols-2']">
            <div class="space-y-2">
              <p
                :class="[
                  'text-xs font-semibold uppercase tracking-widest',
                  isLight ? 'text-slate-500' : 'text-white/50'
                ]"
              >
                {{ contactsHeading }}
              </p>

              <template v-if="hasContactInfo">
                <p v-if="phoneText" :class="['font-medium', textPrimaryClass]">
                  {{ phoneLabel }}
                  <span :class="['font-normal', textSecondaryClass]">{{ phoneText }}</span>
                </p>

                <p v-if="contactEmail" :class="textPrimaryClass">
                  {{ emailLabel }}
                  <a :class="[textLinkClass, 'hover:underline']" :href="`mailto:${contactEmail}`">
                    {{ contactEmail }}
                  </a>
                </p>
              </template>

              <p v-else :class="textSecondaryClass">
                {{ contactsEmptyMessage }}
              </p>
            </div>

            <div v-if="addressText" class="space-y-2">
              <p
                :class="[
                  'text-xs font-semibold uppercase tracking-widest',
                  isLight ? 'text-slate-500' : 'text-white/50'
                ]"
              >
                {{ addressHeadingText }}
              </p>

              <p :class="['font-medium', textPrimaryClass]">
                {{ addressLine1 }}
              </p>
              <p v-if="addressLine2" :class="textSecondaryClass">
                {{ addressLine2 }}
              </p>
            </div>
          </div>

          <!-- REDES SOCIAIS DESKTOP -->
          <div
            v-if="socialLinks.length"
            :class="[
              desktopOnlyClass,
              isLight ? 'border-slate-200 bg-white/70' : 'border-white/15 bg-white/5'
            ]"
          >
            <div :class="desktopSocialInnerClass">
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
                  <svg viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor" :style="{ color: socialIconColor }">
                    <path :d="link.iconPath" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- MAPA MOBILE -->
          <div v-if="mapEmbedUrl" :class="mobileMapClass">
            <div :class="['flex items-center justify-between pb-3 text-xs font-semibold', textSecondaryClass]">
              <span>Localização da agência</span>

              <a
                v-if="mapLink"
                :href="mapLink"
                :class="[
                  'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[10px] uppercase tracking-widest transition',
                  mapButtonClass
                ]"
                target="_blank"
                rel="noopener"
              >
                {{ mapButtonText }}
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
        <div v-if="mapEmbedUrl" :class="desktopMapClass">
          <div :class="['flex items-center justify-between pb-3 text-xs font-semibold', textSecondaryClass]">
            <span>{{ mapHeadingText }}</span>

            <a
              v-if="mapLink"
              :href="mapLink"
              :class="[
                'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[10px] uppercase tracking-widest transition',
                mapButtonClass
              ]"
              target="_blank"
              rel="noopener"
            >
              {{ mapButtonText }}
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
import { createLocalizer, getCurrentLanguage, type LocalizedString } from "../../utils/i18n";

const props = defineProps<{
  section: AgencyFooterSection;
  branding?: Record<string, any>;
  previewDevice?: "desktop" | "mobile";
}>();

const localize = createLocalizer(getCurrentLanguage());
const footerCopy = {
  agencyHeading: { pt: "Agência", es: "Agencia" },
  fallbackAgencyName: { pt: "Sua agência cadastrada", es: "Tu agencia registrada" },
  cnpjLabel: { pt: "CNPJ", es: "CNPJ" },
  socialHeading: { pt: "Acesse agora nossas redes sociais", es: "Accede ahora a nuestras redes sociales" },
  contactsHeading: { pt: "Contatos", es: "Contactos" },
  phoneLabel: { pt: "Telefone:", es: "Teléfono:" },
  emailLabel: { pt: "Email:", es: "Correo:" },
  contactsEmpty: {
    pt: "Atualize os contatos da agência para exibir telefone e email.",
    es: "Actualiza los contactos de la agencia para mostrar teléfono y correo."
  },
  addressHeading: { pt: "Endereço", es: "Dirección" },
  mapButton: { pt: "Abrir no Maps", es: "Abrir en Maps" },
  mapHeading: { pt: "Localização da agência", es: "Ubicación de la agencia" }
} as const;
const agencyHeadingText = localize(footerCopy.agencyHeading);
const fallbackCompanyName = localize(footerCopy.fallbackAgencyName);
const cnpjLabel = localize(footerCopy.cnpjLabel);
const socialHeading = localize(footerCopy.socialHeading);
const contactsHeading = localize(footerCopy.contactsHeading);
const phoneLabel = localize(footerCopy.phoneLabel);
const emailLabel = localize(footerCopy.emailLabel);
const contactsEmptyMessage = localize(footerCopy.contactsEmpty);
const addressHeadingText = localize(footerCopy.addressHeading);
const mapButtonText = localize(footerCopy.mapButton);
const mapHeadingText = localize(footerCopy.mapHeading);

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

const SOCIAL_LABELS: Record<AgencySocialNetwork, LocalizedString> = {
  instagram: { pt: "Instagram", es: "Instagram" },
  facebook: { pt: "Facebook", es: "Facebook" },
  youtube: { pt: "YouTube", es: "YouTube" },
  tiktok: { pt: "TikTok", es: "TikTok" }
};

const socialLinks = computed(() => {
  const links = Array.isArray(agencyProfile.value?.social_links) ? agencyProfile.value.social_links : [];
  return links
    .filter(
      link =>
        typeof link?.network === "string" &&
        typeof link?.url === "string" &&
        link.url.trim().length > 0
    )
    .map(link => ({
      ...link,
      network: link.network as AgencySocialNetwork,
      url: link.url.trim(),
      iconPath: SOCIAL_ICON_MAP[link.network as AgencySocialNetwork],
      label: localize(SOCIAL_LABELS[link.network as AgencySocialNetwork])
    }))
    .filter(link => !!link.iconPath);
});

const cadasturLink = computed(() => agencyProfile.value?.cadastur_url || buildCadasturLink(agencyProfile.value?.cnpj_digits));
const shouldShowCadastur = computed(() => props.section.showCadastur !== false);

const layoutMode = computed(() => props.section.displayVariant || "auto");
const isMobilePreview = computed(() => props.previewDevice === "mobile");
const layoutClass = computed(() => {
  if (layoutMode.value === "stacked") {
    return isMobilePreview.value ? "flex-col" : "md:flex-col";
  }
  return isMobilePreview.value ? "flex-col" : "md:flex-row md:items-start md:justify-between";
});
const mobileOnlyClass = computed(() => (isMobilePreview.value ? "rounded-[22px] border p-4" : "md:hidden rounded-[22px] border p-4"));
const desktopOnlyClass = computed(() =>
  isMobilePreview.value ? "hidden rounded-[22px] border p-4" : "hidden md:block rounded-[22px] border p-4"
);
const desktopSocialInnerClass = computed(() =>
  isMobilePreview.value
    ? "flex flex-col items-center gap-4 text-center"
    : "flex flex-col items-center gap-4 text-center md:flex-col md:items-start md:text-left lg:flex-row lg:items-center lg:justify-between"
);
const mobileMapClass = computed(() => (isMobilePreview.value ? "w-full" : "w-full md:hidden"));
const desktopMapClass = computed(() =>
  isMobilePreview.value ? "hidden w-full" : "hidden w-full md:block md:w-[420px] md:flex-shrink-0"
);

const DEFAULT_ACCENT_COLOR = "#41ce5f";

const accentBaseColor = computed(() => {
  const themeAccent = resolvedBranding.value?.theme?.ctaDefaultColor;
  if (typeof themeAccent === "string" && themeAccent.trim()) {
    return themeAccent;
  }

  const primary = resolvedBranding.value?.primary_color;
  if (typeof primary === "string" && primary.trim()) {
    return primary;
  }

  return DEFAULT_ACCENT_COLOR;
});

const DEFAULT_SECTION_BG = "#2d2d2d";
const ICON_LIGHT_COLOR = "#ffffff";
const ICON_DARK_COLOR = "#0f172a";
const MIN_ICON_CONTRAST_RATIO = 4.5;

const sectionBackground = computed(() => {
  const bg = (props.section.backgroundColor || "").trim();
  if (bg) {
    return bg;
  }
  return DEFAULT_SECTION_BG;
});

const isLight = computed(() => isLightBackground(sectionBackground.value));

const textPrimaryClass = computed(() =>
  isLight.value ? "text-slate-900" : "text-white"
);

const textSecondaryClass = computed(() =>
  isLight.value ? "text-slate-600" : "text-white/70"
);

const textLinkClass = computed(() =>
  isLight.value ? "text-slate-900" : "text-white"
);

const mapButtonClass = computed(() =>
  isLight.value
    ? "border-slate-300 text-slate-900 hover:bg-slate-100"
    : "border-white/20 text-white hover:bg-white/10"
);

const cadasturWrapperClasses = computed(() => {
  const base =
    "inline-flex items-center rounded-2xl px-6 py-3 transition hover:scale-[1.02]";

  return isLight.value
    ? `${base} bg-transparent`
    : `${base} bg-white shadow-sm`;
});

const socialIconColor = computed(() =>
  getContrastAwareColor(sectionBackground.value, ICON_LIGHT_COLOR, ICON_DARK_COLOR, isLight.value)
);

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

function clamp(value: number, min = 0, max = 255) {
  return Math.min(max, Math.max(min, value));
}

function toHex(value: number) {
  return clamp(Math.round(value)).toString(16).padStart(2, "0");
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

function darkenColor(color: string, amount = 0.4) {
  const rgb = parseColor(color);
  if (!rgb) return "#05060f";

  const factor = 1 - amount;

  const r = rgb.r * factor;
  const g = rgb.g * factor;
  const b = rgb.b * factor;

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function ensureMinimumContrast(color: string) {
  const rgb = parseColor(color);
  if (!rgb) return DEFAULT_SECTION_BG;

  const { h, s } = rgbToHsl(rgb.r, rgb.g, rgb.b);
  const darkerRgb = hslToRgb(h, s, 0.1);

  return `#${toHex(darkerRgb.r)}${toHex(darkerRgb.g)}${toHex(darkerRgb.b)}`;
}

function isLightBackground(color?: string | null) {
  const rgb = parseColor(color);
  if (!rgb) return false;
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
  return luminance >= 0.55;
}

function getContrastAwareColor(
  backgroundColor?: string | null,
  lightColor = ICON_LIGHT_COLOR,
  darkColor = ICON_DARK_COLOR,
  fallbackIsLight = false
) {
  const backgroundRgb = parseColor(backgroundColor);
  const lightRgb = parseColor(lightColor);
  const darkRgb = parseColor(darkColor);

  if (!backgroundRgb || !lightRgb || !darkRgb) {
    return fallbackIsLight ? darkColor : lightColor;
  }

  const backgroundLuminance = relativeLuminance(backgroundRgb);
  const lightLuminance = relativeLuminance(lightRgb);
  const darkLuminance = relativeLuminance(darkRgb);

  const contrastWithLight = calculateContrastRatio(backgroundLuminance, lightLuminance);
  const contrastWithDark = calculateContrastRatio(backgroundLuminance, darkLuminance);

  if (contrastWithLight >= MIN_ICON_CONTRAST_RATIO && contrastWithLight >= contrastWithDark) {
    return lightColor;
  }

  if (contrastWithDark >= MIN_ICON_CONTRAST_RATIO) {
    return darkColor;
  }

  return contrastWithLight > contrastWithDark ? lightColor : darkColor;
}

function relativeLuminance(rgb: { r: number; g: number; b: number }) {
  const toLinear = (value: number) => {
    const channel = value / 255;
    return channel <= 0.03928 ? channel / 12.92 : Math.pow((channel + 0.055) / 1.055, 2.4);
  };

  const r = toLinear(rgb.r);
  const g = toLinear(rgb.g);
  const b = toLinear(rgb.b);

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function calculateContrastRatio(l1: number, l2: number) {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function rgbToHsl(r: number, g: number, b: number) {
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }

  return { h, s, l };
}

function hslToRgb(h: number, s: number, l: number) {
  let r: number;
  let g: number;
  let b: number;

  if (s === 0) {
    r = g = b = l; // achromatic
  } else {
    const hue2rgb = (p: number, q: number, t: number) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }

  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255)
  };
}
</script>









