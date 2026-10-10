<template>
  <V2Section type="agency_footer" :background="section.backgroundColor" fallback-background="#0E1A15" :anchor-id="section.anchorId" flush>
    <div class="v2-ft">
      <div class="v2-ft-cols v2-in">
        <div v-if="logo || description || socialLinks.length" class="v2-ft-col v2-ft-brand">
          <img v-if="logo" :src="logo" :alt="companyName" class="v2-ft-logo" :style="{ borderRadius: `${Math.max(0, logoRadius || 0)}px` }" loading="lazy" />
          <p v-if="description" class="v2-ft-about">{{ description }}</p>
          <div v-if="socialLinks.length" class="v2-ft-social" :aria-label="copy.social">
            <a v-for="link in socialLinks" :key="link.network" :href="link.url" target="_blank" rel="noopener noreferrer" :aria-label="link.label" :title="link.label">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path :d="link.iconPath" /></svg>
            </a>
          </div>
        </div>
        <div v-if="phoneText || email" class="v2-ft-col">
          <span class="v2-ft-h">{{ copy.contacts }}</span>
          <a v-if="phoneText" :href="phoneLink || undefined" target="_blank" rel="noopener" data-track-event="cta" data-track-type="whatsapp">{{ phoneText }}</a>
          <a v-if="email" :href="`mailto:${email}`">{{ email }}</a>
        </div>
        <div v-if="addressText" class="v2-ft-col">
          <span class="v2-ft-h">{{ copy.address }}</span>
          <span class="v2-ft-muted">{{ addressText }}</span>
          <a v-if="mapLink" :href="mapLink" target="_blank" rel="noopener" class="v2-ft-map-btn">{{ copy.map }}</a>
        </div>
        <div v-if="mapEmbedUrl" class="v2-ft-col v2-ft-mapcol">
          <iframe :src="mapEmbedUrl" :title="copy.mapTitle" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
        </div>
      </div>
      <div class="v2-ft-bottom v2-in v2-d2">
        <a v-if="hasCadastur" :href="cadasturLink" target="_blank" rel="noopener" class="v2-ft-cadastur">
          <img :src="cadasturLogo" alt="Cadastur" />
          <span>{{ copy.cadastur }}</span>
        </a>
        <!-- À vista só o © com o CNPJ; o aviso de responsabilidade abre num balão no (i). -->
        <div class="v2-ft-legal">
          <V2LegalInfo :company-name="companyName" :cnpj="cnpjText" :has-contacts="!!(phoneText || email)" :id="section.anchorId || 'rodape'" />
        </div>
      </div>
    </div>
  </V2Section>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { siFacebook, siInstagram, siTiktok, siYoutube } from "simple-icons";
import type { AgencyFooterSection } from "../../../types/page";
import cadasturLogo from "../../../assets/cadastur-logo.png";
import { PUBLIC_BRANDING_KEY } from "../../../utils/brandingKeys";
import { getCurrentLanguage } from "../../../utils/i18n";
import { resolveMediaUrl } from "../../../utils/media";
import { normalizeWhatsappDigits } from "../../../utils/whatsapp";
import V2Section from "./V2Section.vue";
import V2LegalInfo from "./V2LegalInfo.vue";
import { localize } from "./useHeading";

const props = defineProps<{
  section: AgencyFooterSection;
  branding?: Record<string, any>;
  previewDevice?: "desktop" | "mobile";
  /** Logo da página (Banner Inicial › Logo) e cantos dele; sem ele, o logo da agência. */
  logoUrl?: string;
  logoRadius?: number;
}>();
const copy = {
  social: localize({ pt: "Redes sociais", es: "Redes sociales" }),
  contacts: localize({ pt: "Contatos", es: "Contactos" }),
  address: localize({ pt: "Endereço", es: "Dirección" }),
  map: localize({ pt: "Abrir no Maps", es: "Abrir en Maps" }),
  mapTitle: localize({ pt: "Localização da agência", es: "Ubicación de la agencia" }),
  cadastur: localize({ pt: "Agência cadastrada no Cadastur", es: "Agencia registrada en Cadastur" }),
  legalToggle: localize({ pt: "Sobre o conteúdo desta página", es: "Sobre el contenido de esta página" })
};

const provided = inject(PUBLIC_BRANDING_KEY, null) as any;
const branding = computed<Record<string, any>>(() => props.branding || (provided && "value" in provided ? provided.value : provided) || {});
// O mesmo logo do topo da página: o do Banner Inicial (se a página trocou) ou o da agência.
const logo = computed(() => resolveMediaUrl(props.logoUrl) || resolveMediaUrl(branding.value?.logo_url) || "");
const profile = computed<Record<string, any>>(() => branding.value?.agency_profile || {});
const companyName = computed(() => profile.value?.name || branding.value?.agency_name || "");
const description = computed(() => String(profile.value?.description || "").trim());
const digitsOf = (value?: string | null) => (value || "").replace(/\D/g, "");
const cnpjText = computed(() => {
  const d = digitsOf(profile.value?.cnpj).slice(0, 14);
  return d ? d.replace(/(\d{2})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1/$2").replace(/(\d{4})(\d{1,2})$/, "$1-$2") : "";
});
const email = computed(() => profile.value?.email || "");
const phoneText = computed(() => {
  const normalized = normalizeWhatsappDigits(profile.value?.phone || "");
  if (!normalized) return "";
  const br = normalized.startsWith("55");
  const local = br ? normalized.slice(2) : normalized;
  const formatted =
    local.length === 10 ? local.replace(/(\d{2})(\d{4})(\d{4})/, "($1) $2-$3") : local.length === 11 ? local.replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3") : local;
  return br ? `+55 ${formatted}` : formatted;
});
const phoneLink = computed(() => {
  const digits = normalizeWhatsappDigits(profile.value?.phone || "");
  return digits ? `https://wa.me/${digits}` : "";
});
const addressText = computed(() => {
  const a = profile.value?.address || {};
  const line1 = [a.street, a.number, a.complement].filter(Boolean).join(", ");
  const line2 = [a.neighborhood, a.city, a.state, a.zipcode].filter(Boolean).join(", ");
  return profile.value?.address_text || [line1, line2].filter(Boolean).join(" · ");
});
// Busca do mapa sem o complemento ("Sala 1204", "Bloco B"), que atrapalha o Google a achar o
// endereço; com rua, número, bairro, cidade, UF e CEP o pino cai no lugar e o zoom fica de rua.
const mapQuery = computed(() => {
  const a = profile.value?.address || {};
  const parts = [a.street, a.number, a.neighborhood, a.city, a.state, a.zipcode].map(part => String(part || "").trim()).filter(Boolean);
  return parts.length ? parts.join(", ") : profile.value?.map_query || addressText.value;
});
const mapEmbedUrl = computed(() =>
  mapQuery.value ? `https://www.google.com/maps?q=${encodeURIComponent(mapQuery.value)}&z=16&hl=${getCurrentLanguage() === "es" ? "es" : "pt-BR"}&output=embed` : ""
);
const mapLink = computed(() => (mapQuery.value ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapQuery.value)}` : ""));
const icons: Record<string, { path: string; label: string }> = {
  instagram: { path: siInstagram.path, label: "Instagram" },
  facebook: { path: siFacebook.path, label: "Facebook" },
  youtube: { path: siYoutube.path, label: "YouTube" },
  tiktok: { path: siTiktok.path, label: "TikTok" }
};
const socialLinks = computed(() =>
  (Array.isArray(profile.value?.social_links) ? profile.value.social_links : [])
    .filter((link: any) => typeof link?.url === "string" && link.url.trim() && icons[link.network])
    .map((link: any) => ({ network: link.network, url: link.url.trim(), iconPath: icons[link.network].path, label: icons[link.network].label }))
);
// Usa o documento escolhido em "Documento do Cadastur" quando a agência tem esse documento;
// senão, o que existir. A URL salva tem prioridade; sem ela, monta a do QR code público.
const cadasturLink = computed(() => {
  const cpf = digitsOf(profile.value?.cpf_digits || profile.value?.cpf);
  const cnpj = digitsOf(profile.value?.cnpj_digits || profile.value?.cnpj);
  const chosen = props.section.cadasturDocumentType;
  const type = chosen === "cpf" && cpf ? "cpf" : chosen === "cnpj" && cnpj ? "cnpj" : cnpj ? "cnpj" : cpf ? "cpf" : null;
  if (!type) return "";
  const saved = profile.value?.cadastur_urls?.[type];
  if (typeof saved === "string" && saved) return saved;
  return `https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/${type === "cpf" ? cpf : cnpj}`;
});
const hasCadastur = computed(() => props.section.showCadastur !== false && !!cadasturLink.value);
</script>

<style scoped>
.v2-ft {
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.v2-ft-cols {
  display: flex;
  flex-wrap: wrap;
  gap: 28px 48px;
}
.v2-ft-col {
  flex: 1 1 200px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  font-size: 15px;
}
.v2-ft-brand {
  flex: 1.4 1 240px;
}
.v2-ft-col a {
  color: inherit;
  text-decoration: none;
}
.v2-ft-col a:hover {
  text-decoration: underline;
}
.v2-ft-logo {
  max-height: 56px;
  max-width: 200px;
  object-fit: contain;
}
.v2-ft-about {
  max-width: 340px;
  margin: 0;
  color: var(--v2-muted);
  font-size: 15px;
  line-height: 1.55;
  white-space: pre-line;
}
.v2-ft-h {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--v2-muted);
}
.v2-ft-muted {
  color: var(--v2-muted);
  line-height: 1.5;
}
.v2-ft-social {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}
.v2-ft-social a {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: var(--v2-card);
}
.v2-ft-social a:hover {
  background: var(--v2-accent);
  color: var(--v2-on-accent);
  text-decoration: none;
}
.v2-ft-map-btn {
  margin-top: 4px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--v2-card);
  font-size: 14px;
  font-weight: 600;
}
/* Mapa mais largo e mais alto que as colunas de texto, para o pino e as ruas em volta caberem;
   o fundo aparece enquanto o mapa carrega. */
.v2-ft-mapcol {
  flex: 1.6 1 280px;
}
.v2-ft-mapcol iframe {
  width: 100%;
  height: 200px;
  border: 0;
  border-radius: 16px;
  background: var(--v2-card);
}
.v2-ft-bottom {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px 24px;
  padding-top: 20px;
  border-top: 1px solid var(--v2-line);
  font-size: 13px;
}
.v2-ft-cadastur {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px 10px 12px;
  border-radius: 14px;
  background: #fff;
  color: #0f1713;
  font-weight: 600;
  text-decoration: none;
}
.v2-ft-cadastur img {
  height: 26px;
  width: auto;
}
.v2-ft-legal {
  flex: 1 1 260px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  min-width: 0;
  color: var(--v2-muted);
  font-size: 13px;
  line-height: 1.5;
}
/* Celular: o © fica à esquerda, embaixo do selo do Cadastur. */
@container (max-width: 560px) {
  .v2-ft-legal {
    align-items: flex-start;
  }
  .v2-ft-legal :deep(.v2-legal) {
    justify-content: flex-start;
  }
}
</style>
