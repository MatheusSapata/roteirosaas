<template>
  <V2Section type="agency_footer" :background="section.backgroundColor" fallback-background="#0E1A15" :anchor-id="section.anchorId" flush>
    <div class="v2-ft">
      <div class="v2-ft-cols">
        <div class="v2-ft-col v2-ft-brand">
          <img v-if="logo" :src="logo" :alt="companyName" class="v2-ft-logo" loading="lazy" />
          <b class="v2-ft-name">{{ companyName || copy.fallbackName }}</b>
          <span v-if="cnpjText" class="v2-ft-muted">CNPJ {{ cnpjText }}</span>
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
          <iframe :src="mapEmbedUrl" :title="copy.mapTitle" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
      </div>
      <div class="v2-ft-bottom">
        <a v-if="hasCadastur" :href="cadasturLink" target="_blank" rel="noopener" class="v2-ft-cadastur">
          <img :src="cadasturLogo" alt="Cadastur" />
          <span>{{ copy.cadastur }}</span>
        </a>
        <span class="v2-ft-muted">© {{ year }} {{ companyName }}</span>
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
import { resolveMediaUrl } from "../../../utils/media";
import { normalizeWhatsappDigits } from "../../../utils/whatsapp";
import V2Section from "./V2Section.vue";
import { localize } from "./useHeading";

const props = defineProps<{ section: AgencyFooterSection; branding?: Record<string, any>; previewDevice?: "desktop" | "mobile" }>();
const copy = {
  fallbackName: localize({ pt: "Sua agência cadastrada", es: "Tu agencia registrada" }),
  social: localize({ pt: "Redes sociais", es: "Redes sociales" }),
  contacts: localize({ pt: "Contatos", es: "Contactos" }),
  address: localize({ pt: "Endereço", es: "Dirección" }),
  map: localize({ pt: "Abrir no Maps", es: "Abrir en Maps" }),
  mapTitle: localize({ pt: "Localização da agência", es: "Ubicación de la agencia" }),
  cadastur: localize({ pt: "Agência cadastrada no Cadastur", es: "Agencia registrada en Cadastur" })
};
const provided = inject(PUBLIC_BRANDING_KEY, null) as any;
const branding = computed<Record<string, any>>(() => props.branding || (provided && "value" in provided ? provided.value : provided) || {});
const profile = computed<Record<string, any>>(() => branding.value?.agency_profile || {});
const companyName = computed(() => profile.value?.name || branding.value?.agency_name || "");
const logo = computed(() => resolveMediaUrl(branding.value?.logo_url) || "");
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
const mapEmbedUrl = computed(
  () => profile.value?.map_embed_url || (addressText.value ? `https://www.google.com/maps?q=${encodeURIComponent(addressText.value)}&output=embed` : "")
);
const mapLink = computed(() => {
  const query = profile.value?.map_query || addressText.value;
  return query ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}` : "";
});
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
// Mesma regra do rodapé atual: CPF tem prioridade; usa a URL salva ou monta a do QR code público.
const cadasturLink = computed(() => {
  const cpf = digitsOf(profile.value?.cpf_digits || profile.value?.cpf);
  const cnpj = digitsOf(profile.value?.cnpj_digits || profile.value?.cnpj);
  const type = cpf ? "cpf" : cnpj ? "cnpj" : null;
  if (!type) return "";
  const saved = profile.value?.cadastur_urls?.[type];
  if (typeof saved === "string" && saved) return saved;
  return `https://cadastur.turismo.gov.br/cadastur/#!/public/qrcode/${type === "cpf" ? cpf : cnpj}`;
});
const hasCadastur = computed(() => props.section.showCadastur !== false && !!cadasturLink.value);
const year = new Date().getFullYear();
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
  max-height: 48px;
  max-width: 180px;
  object-fit: contain;
}
.v2-ft-name {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 20px;
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
.v2-ft-mapcol iframe {
  width: 100%;
  height: 160px;
  border: 0;
  border-radius: 16px;
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
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 6px;
  border-radius: 12px;
  background: #fff;
  color: #0f1713;
  font-weight: 600;
  text-decoration: none;
}
.v2-ft-cadastur img {
  height: 24px;
  width: auto;
}
</style>
