<template>
  <div v-if="showSpacer" class="v2-hd-spacer" aria-hidden="true"></div>
  <header class="v2-hd" :class="[`is-${mode}`, { 'is-preview': previewDevice, 'is-stuck': isStuck }]" :style="vars">
    <div v-if="previewBannerImage && mode !== 'solid'" class="v2-hd-preview-bg" :style="{ backgroundImage: `url(&quot;${previewBannerImage}&quot;)` }" aria-hidden="true"></div>
    <div class="v2-hd-inner">
      <a
        class="v2-hd-brand"
        :href="logoHref"
        :target="section.logoOpenInNewTab && isLogoLink ? '_blank' : undefined"
        :rel="section.logoOpenInNewTab && isLogoLink ? 'noopener noreferrer' : undefined"
        :aria-label="copy.logo"
        @click="handleLogoClick"
      >
        <img v-if="logo" :src="logo" :alt="agencyName || copy.logo" :style="logoStyle" />
        <span v-else class="v2-hd-name">{{ agencyName || "Roteiro" }}</span>
      </a>
      <nav class="v2-hd-nav" :class="{ open: menuOpen }" :aria-label="copy.nav">
        <a
          v-for="item in links"
          :key="item.key"
          :href="item.href"
          :target="item.newTab ? '_blank' : undefined"
          :rel="item.newTab ? 'noopener noreferrer' : undefined"
          @click="handleLinkClick(item, $event)"
        >{{ item.label }}</a>
        <div v-if="hasActions" class="v2-hd-mobile-actions">
          <template v-if="section.actionType === 'social'">
            <a v-for="s in socials" :key="s.platform" class="v2-hd-social" :href="s.url" target="_blank" rel="noopener noreferrer" :aria-label="s.label">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" :d="s.path" /></svg>
            </a>
          </template>
          <a v-else class="v2-btn v2-hd-contact" :href="contactHref" :target="section.contactType === 'link' ? '_blank' : undefined" data-track-event="cta" :data-track-type="section.contactType === 'whatsapp' ? 'whatsapp' : 'cta'">{{ contactLabel }}</a>
        </div>
      </nav>
      <div class="v2-hd-actions">
        <template v-if="hasActions">
          <template v-if="section.actionType === 'social'">
            <a v-for="s in socials" :key="s.platform" class="v2-hd-social" :href="s.url" target="_blank" rel="noopener noreferrer" :aria-label="s.label">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" :d="s.path" /></svg>
            </a>
          </template>
          <a v-else class="v2-btn v2-hd-contact" :href="contactHref" :target="section.contactType === 'link' ? '_blank' : undefined" data-track-event="cta" :data-track-type="section.contactType === 'whatsapp' ? 'whatsapp' : 'cta'">{{ contactLabel }}</a>
        </template>
        <button v-if="links.length || hasActions" class="v2-hd-toggle" type="button" :aria-expanded="menuOpen" :aria-label="copy.menu" @click="menuOpen = !menuOpen">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { siFacebook, siInstagram, siLinkedin, siTiktok, siYoutube } from "simple-icons";
import type { HeaderLinkItem, HeaderSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";
import { usePageDesignContext } from "./designContext";
import { computeSectionTone, toneVars } from "./useSectionTone";
import { localize, text } from "./useHeading";
import "./v2.css";

const props = defineProps<{
  section: HeaderSection;
  logoUrl?: string;
  agencyName?: string;
  agencySocialLinks?: Array<{ network?: string; platform?: string; url?: string }>;
  previewBackgroundImage?: string;
  previewOverlayColor?: string;
  previewDevice?: "desktop" | "mobile";
}>();
const copy = {
  logo: localize({ pt: "Logo da agência", es: "Logo de la agencia" }),
  nav: localize({ pt: "Navegação principal", es: "Navegación principal" }),
  menu: localize({ pt: "Abrir menu", es: "Abrir menú" }),
  contact: localize({ pt: "Entrar em contato", es: "Contactar" })
};
const design = usePageDesignContext();
const menuOpen = ref(false);
const isStuck = ref(false);
// "blurred" segue como transparente: ao rolar, os dois ganham fundo branco.
const mode = computed(() => (props.section.mode === "transparent" || props.section.mode === "blurred" ? "transparent" : "solid"));
const showSpacer = computed(() => isStuck.value && mode.value === "solid" && !props.previewDevice);
const logo = computed(() => resolveMediaUrl(props.logoUrl) || "");
const logoStyle = computed(() => ({ maxHeight: `${Math.min(96, Math.max(36, props.section.logoSize || 52))}px` }));
const previewBannerImage = computed(() => (props.previewDevice ? resolveMediaUrl(props.previewBackgroundImage) || "" : ""));
const surface = computed(() => (mode.value === "transparent" && !isStuck.value ? "#0B1410" : isStuck.value ? "#FFFFFF" : props.section.backgroundColor || "#FFFFFF"));
const vars = computed(() => toneVars(computeSectionTone(surface.value, design.value.accent)));

const normalizeUrl = (value: string) => (!value || value === "#" ? "#" : /^(https?:\/\/|mailto:|tel:)/i.test(value) ? value : `https://${value}`);
const links = computed(() =>
  (props.section.links || [])
    .filter(item => text(item.label) && item.target)
    .slice(0, 7)
    .map((item, idx) => ({
      key: item.id || `${idx}`,
      label: text(item.label),
      raw: item,
      newTab: !!item.openInNewTab,
      href: item.targetType === "section" ? `#${item.target.replace(/^#/, "")}` : item.targetType === "external" ? normalizeUrl(item.target) : item.target
    }))
);
const handleLinkClick = (item: { raw: HeaderLinkItem }, event: MouseEvent) => {
  menuOpen.value = false;
  if (item.raw.targetType !== "section") return;
  event.preventDefault();
  document.getElementById(item.raw.target.replace(/^#/, ""))?.scrollIntoView({ behavior: "smooth", block: "start" });
};
const isLogoLink = computed(() => props.section.logoActionType === "page" || props.section.logoActionType === "external");
const logoHref = computed(() => {
  const type = props.section.logoActionType || "top";
  const target = (props.section.logoActionTarget || "").trim();
  if (type === "section") return target ? `#${target.replace(/^#/, "")}` : "#";
  if (type === "page") return target || "#";
  if (type === "external") return normalizeUrl(target);
  return "#";
});
const handleLogoClick = (event: MouseEvent) => {
  const type = props.section.logoActionType || "top";
  if (type === "none") return event.preventDefault();
  if (type === "top") {
    event.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  if (type === "section") {
    event.preventDefault();
    document.getElementById((props.section.logoActionTarget || "").replace(/^#/, ""))?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
};
const icons: Record<string, { path: string; title: string }> = { instagram: siInstagram, facebook: siFacebook, youtube: siYoutube, tiktok: siTiktok, linkedin: siLinkedin };
const socials = computed(() =>
  (props.agencySocialLinks || [])
    .map(item => ({ platform: item.network || item.platform || "", url: (item.url || "").trim() }))
    .filter(item => item.url && icons[item.platform])
    .map(item => ({ ...item, url: normalizeUrl(item.url), path: icons[item.platform].path, label: icons[item.platform].title }))
);
const hasActions = computed(() => props.section.actionType === "contact" || (props.section.actionType === "social" && socials.value.length > 0));
const contactLabel = computed(() => text(props.section.contactLabel) || copy.contact);
const contactHref = computed(() => {
  const value = (props.section.contactValue || "").trim();
  if (props.section.contactType !== "whatsapp") return normalizeUrl(value || "#");
  const digits = value.replace(/\D/g, "");
  const message = (props.section.whatsappMessage || "").trim();
  return digits ? `https://wa.me/${digits}${message ? `?text=${encodeURIComponent(message)}` : ""}` : "#";
});
const updateStuck = () => {
  isStuck.value = props.section.stickyEnabled !== false && !props.previewDevice && typeof window !== "undefined" && window.scrollY > 4;
};
onMounted(() => {
  updateStuck();
  window.addEventListener("scroll", updateStuck, { passive: true });
});
onUnmounted(() => window.removeEventListener("scroll", updateStuck));
</script>

<style scoped>
.v2-hd-spacer {
  height: 76px;
}
.v2-hd {
  container-type: inline-size;
  position: relative;
  z-index: 40;
  width: 100%;
  height: 76px;
  background: var(--v2-bg);
  color: var(--v2-ink);
  font-family: Figtree, system-ui, sans-serif;
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}
.v2-hd.is-transparent:not(.is-stuck) {
  background: transparent;
}
.v2-hd.is-transparent:not(.is-preview):not(.is-stuck) {
  position: absolute;
  top: 0;
  left: 0;
}
.v2-hd.is-transparent:not(.is-stuck)::before {
  content: "";
  position: absolute;
  inset: 0 0 -24px;
  background: linear-gradient(180deg, rgba(6, 12, 9, 0.45), transparent);
  pointer-events: none;
}
.v2-hd.is-stuck:not(.is-preview) {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  box-shadow: 0 10px 30px -14px rgba(15, 23, 19, 0.35);
}
.v2-hd-preview-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center top;
}
.v2-hd-inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 24px;
  max-width: 1240px;
  height: 100%;
  margin: 0 auto;
  padding: 0 clamp(16px, 4cqi, 40px);
}
.v2-hd-brand {
  display: flex;
  align-items: center;
  min-width: 0;
  color: inherit;
  text-decoration: none;
}
.v2-hd-brand img {
  display: block;
  width: auto;
  max-width: 200px;
  object-fit: contain;
}
.v2-hd-name {
  font-family: "Bricolage Grotesque", Figtree, sans-serif;
  font-size: 20px;
  font-weight: 700;
}
.v2-hd-nav {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: clamp(14px, 2cqi, 28px);
}
.v2-hd-nav > a {
  position: relative;
  color: inherit;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  opacity: 0.88;
}
.v2-hd-nav > a::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6px;
  height: 2px;
  border-radius: 2px;
  background: var(--v2-accent);
  transform: scaleX(0);
  transition: transform 0.22s ease;
}
.v2-hd-nav > a:hover {
  opacity: 1;
}
.v2-hd-nav > a:hover::after {
  transform: scaleX(1);
}
.v2-hd-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.v2-hd-contact {
  min-height: 44px;
  padding: 0 20px;
  font-size: 15px;
}
.v2-hd-social {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: var(--v2-card);
  color: inherit;
}
.v2-hd-social svg {
  width: 17px;
  height: 17px;
}
.v2-hd-toggle,
.v2-hd-mobile-actions {
  display: none;
}
@container (max-width: 860px) {
  .v2-hd {
    height: 68px;
  }
  .v2-hd-nav {
    position: absolute;
    top: calc(100% + 6px);
    left: 12px;
    right: 12px;
    display: none;
    flex-direction: column;
    gap: 2px;
    padding: 10px;
    border-radius: 18px;
    background: #fff;
    color: #0f1713;
    box-shadow: 0 18px 50px rgba(15, 23, 19, 0.25);
  }
  .v2-hd-nav.open {
    display: flex;
  }
  .v2-hd-nav > a {
    padding: 12px;
    border-radius: 10px;
  }
  .v2-hd-nav > a::after {
    display: none;
  }
  .v2-hd-nav > a:hover {
    background: #f1f4f0;
  }
  .v2-hd-actions > a {
    display: none;
  }
  .v2-hd-toggle {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border: 0;
    border-radius: 999px;
    background: var(--v2-card);
    color: inherit;
    cursor: pointer;
  }
  .v2-hd-mobile-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
    padding: 12px 4px 4px;
    border-top: 1px solid #e3e8e2;
  }
  .v2-hd-mobile-actions .v2-hd-contact {
    width: 100%;
  }
  .v2-hd-mobile-actions .v2-hd-social {
    background: #f1f4f0;
  }
}
</style>
