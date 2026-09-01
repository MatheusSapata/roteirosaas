<template>
  <div v-if="showSpacer" class="header-spacer" aria-hidden="true"></div>
  <header
    ref="headerElement"
    class="site-header"
    :class="[`mode-${section.mode || 'solid'}`, { 'is-preview': previewDevice, 'is-stuck': isStuck }]"
    :style="headerStyle"
  >
    <div v-if="previewBannerImage && section.mode !== 'solid'" class="preview-banner-bg" :class="{ blurred: section.mode === 'blurred' }" :style="previewBannerStyle"></div>
    <div v-if="previewBannerImage && section.mode !== 'solid'" class="preview-banner-overlay" :style="previewOverlayStyle"></div>
    <div class="header-inner" :class="{ 'without-actions': !hasActions }">
      <a class="brand" :href="logoHref" :target="section.logoOpenInNewTab && isLogoLink ? '_blank' : undefined" :rel="section.logoOpenInNewTab && isLogoLink ? 'noopener noreferrer' : undefined" aria-label="Logo da agência" @click="handleLogoClick">
        <img v-if="resolvedLogo" :src="resolvedLogo" alt="Logo" :style="logoStyle" />
        <span v-else class="brand-fallback">{{ agencyName || "Roteiro" }}</span>
      </a>

      <button class="menu-toggle" type="button" :aria-expanded="menuOpen" aria-label="Abrir menu" @click="menuOpen = !menuOpen">
        <span></span><span></span><span></span>
      </button>

      <nav class="navigation" :class="[{ open: menuOpen }, `hover-${section.linkHoverAnimation || 'none'}`]" aria-label="Navegação principal">
        <a
          v-for="item in visibleLinks"
          :key="item.id"
          :href="linkHref(item)"
          :target="item.openInNewTab ? '_blank' : undefined"
          :rel="item.openInNewTab ? 'noopener noreferrer' : undefined"
          @click="handleLinkClick(item, $event)"
        >{{ localize(item.label) }}</a>

        <div v-if="hasActions" class="mobile-actions">
          <template v-if="section.actionType === 'social'">
            <a v-for="social in activeSocialLinks" :key="social.platform" class="social-button" :href="normalizeUrl(social.url)" target="_blank" rel="noopener noreferrer" :aria-label="socialLabel(social.platform)" v-html="socialIcon(social.platform)"></a>
          </template>
          <a v-else-if="section.actionType === 'contact'" class="contact-button" :href="contactHref" :target="section.contactType === 'link' ? '_blank' : undefined" :style="contactStyle">{{ localize(section.contactLabel) || "Entrar em contato" }}</a>
        </div>
      </nav>

      <div v-if="hasActions" class="desktop-actions">
        <template v-if="section.actionType === 'social'">
          <a v-for="social in activeSocialLinks" :key="social.platform" class="social-button" :href="normalizeUrl(social.url)" target="_blank" rel="noopener noreferrer" :aria-label="socialLabel(social.platform)" v-html="socialIcon(social.platform)"></a>
        </template>
        <a v-else-if="section.actionType === 'contact'" class="contact-button" :href="contactHref" :target="section.contactType === 'link' ? '_blank' : undefined" :style="contactStyle">{{ localize(section.contactLabel) || "Entrar em contato" }}</a>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { siFacebook, siInstagram, siLinkedin, siTiktok, siYoutube } from "simple-icons/icons";
import type { HeaderLinkItem, HeaderSection, HeaderSocialLink } from "../../types/page";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import { getReadableTextColor } from "../../utils/colorContrast";
import { resolveMediaUrl } from "../../utils/media";

const props = defineProps<{
  section: HeaderSection;
  logoUrl?: string;
  agencyName?: string;
  agencySocialLinks?: Array<{ network?: string; platform?: string; url?: string }>;
  previewBackgroundImage?: string;
  previewOverlayColor?: string;
  previewDevice?: "desktop" | "mobile";
}>();
const localize = createLocalizer(getCurrentLanguage());
const menuOpen = ref(false);
const headerElement = ref<HTMLElement | null>(null);
const isStuck = ref(false);
const showSpacer = computed(() => isStuck.value && props.section.mode === "solid" && !props.previewDevice);
const resolvedLogo = computed(() => resolveMediaUrl(props.logoUrl));
const previewBannerImage = computed(() => props.previewDevice ? resolveMediaUrl(props.previewBackgroundImage) : "");
const previewBannerStyle = computed(() => ({
  backgroundImage: previewBannerImage.value ? `url("${previewBannerImage.value}")` : undefined,
  filter: props.section.mode === "blurred" ? `blur(${Math.min(30, Math.max(0, props.section.blurAmount ?? 14))}px)` : undefined
}));
const rgba = (color:string,alpha:number) => {
  const hex=color.replace(/^#/,"");const full=hex.length===3?hex.split("").map(char=>char+char).join(""):hex;
  if(!/^[0-9a-f]{6}$/i.test(full))return `rgba(14,165,233,${alpha})`;
  return `rgba(${parseInt(full.slice(0,2),16)},${parseInt(full.slice(2,4),16)},${parseInt(full.slice(4,6),16)},${alpha})`;
};
const previewOverlayStyle = computed(() => {
  const accent=props.previewOverlayColor || "#05060f";
  return { background:`linear-gradient(90deg, ${rgba(accent,.9)} 0%, ${rgba(accent,.65)} 40%, rgba(0,0,0,.38) 65%, rgba(0,0,0,0) 100%)` };
});
const visibleLinks = computed(() => (props.section.links || []).filter(item => localize(item.label).trim() && item.target).slice(0, 7));
const activeSocialLinks = computed(() => (props.agencySocialLinks || []).map(item => ({ platform:(item.network || item.platform || "") as HeaderSocialLink["platform"],url:(item.url || "").trim() })).filter(item => item.url && item.platform in icons));
const hasActions = computed(() => props.section.actionType === "contact" || (props.section.actionType === "social" && activeSocialLinks.value.length > 0));
const headerStyle = computed(() => ({
  backgroundColor: isStuck.value && props.section.mode !== "solid" ? "#ffffff" : props.section.mode === "transparent" || props.section.mode === "blurred" ? "transparent" : (props.section.backgroundColor || "#ffffff"),
  backdropFilter: !isStuck.value && props.section.mode === "blurred" ? `blur(${Math.min(30, Math.max(0, props.section.blurAmount ?? 14))}px)` : undefined,
  WebkitBackdropFilter: !isStuck.value && props.section.mode === "blurred" ? `blur(${Math.min(30, Math.max(0, props.section.blurAmount ?? 14))}px)` : undefined,
  color: isStuck.value && props.section.mode !== "solid" ? "#0f172a" : props.section.linkTextColor || props.section.textColor || (props.section.mode === "transparent" ? "#ffffff" : getReadableTextColor(props.section.backgroundColor || "#ffffff")),
  "--header-link-color": isStuck.value && props.section.mode !== "solid" ? "#0f172a" : props.section.linkTextColor || props.section.textColor || (props.section.mode === "transparent" ? "#ffffff" : getReadableTextColor(props.section.backgroundColor || "#ffffff")),
  "--header-font-size": `${Math.min(20, Math.max(11, props.section.linkFontSize || 14))}px`,
  "--header-hover-color": props.section.linkHoverColor || "#22c55e"
}));
const logoStyle = computed(() => ({ maxHeight: `${Math.min(96, Math.max(36, props.section.logoSize || 56))}px` }));
const contactStyle = computed(() => {
  const backgroundColor = props.section.buttonColor || "#22c55e";
  return { backgroundColor, color: getReadableTextColor(backgroundColor) };
});
const normalizeUrl = (value: string) => !value || value === "#" ? "#" : (/^(https?:\/\/|mailto:|tel:)/i.test(value) ? value : `https://${value}`);
const linkHref = (item: HeaderLinkItem) => item.targetType === "section" ? `#${item.target.replace(/^#/, "")}` : item.targetType === "external" ? normalizeUrl(item.target) : item.target;
const handleLinkClick = (item: HeaderLinkItem, event: MouseEvent) => {
  menuOpen.value = false;
  if (item.targetType !== "section") return;
  event.preventDefault();
  document.getElementById(item.target.replace(/^#/, ""))?.scrollIntoView({ behavior: "smooth", block: "start" });
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
  if (type === "none") { event.preventDefault(); return; }
  if (type === "top") { event.preventDefault(); window.scrollTo({ top: 0, behavior: "smooth" }); return; }
  if (type === "section") {
    event.preventDefault();
    const target = (props.section.logoActionTarget || "").replace(/^#/, "");
    document.getElementById(target)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
};
const contactHref = computed(() => {
  const value = (props.section.contactValue || "").trim();
  if (props.section.contactType !== "whatsapp") return normalizeUrl(value || "#");
  const digits = value.replace(/\D/g, "");
  const message = (props.section.whatsappMessage || "").trim();
  return digits ? `https://wa.me/${digits}${message ? `?text=${encodeURIComponent(message)}` : ""}` : "#";
});
const icons = { instagram: siInstagram, facebook: siFacebook, youtube: siYoutube, tiktok: siTiktok, linkedin: siLinkedin };
const socialIcon = (platform: HeaderSocialLink["platform"]) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="${icons[platform].path}"/></svg>`;
const socialLabel = (platform: HeaderSocialLink["platform"]) => icons[platform].title;
const updateStickyState = () => {
  if (props.section.stickyEnabled === false || props.previewDevice || typeof window === "undefined") { isStuck.value = false; return; }
  isStuck.value = window.scrollY > 4;
};
onMounted(() => { updateStickyState(); window.addEventListener("scroll", updateStickyState, { passive:true }); });
onUnmounted(() => window.removeEventListener("scroll", updateStickyState));
</script>

<style scoped>
.header-spacer{height:84px}.site-header{position:relative;z-index:40;width:100%;height:84px;overflow:hidden;transition:background-color .25s ease,box-shadow .25s ease,backdrop-filter .25s ease}.preview-banner-bg{position:absolute;inset:-18px;z-index:0;background-position:center top;background-size:cover}.preview-banner-bg.blurred{transform:scale(1.06)}.mode-transparent:not(.is-preview),.mode-blurred:not(.is-preview){position:absolute;left:0;top:0}.site-header.is-stuck:not(.is-preview){position:fixed;left:0;top:0;z-index:100;width:100%;box-shadow:0 8px 28px rgba(15,23,42,.14)}.mode-transparent:not(.is-preview):not(.is-stuck){background:transparent!important}.header-inner{position:relative;z-index:1;display:grid;grid-template-columns:minmax(120px,1fr) minmax(280px,auto) minmax(120px,1fr);align-items:center;gap:28px;width:min(100%,1240px);height:100%;margin:auto;padding:12px 28px}.header-inner.without-actions{grid-template-columns:minmax(120px,1fr) auto}.brand{display:flex;min-width:0;justify-self:start;align-items:center;color:var(--header-link-color);text-decoration:none}.brand img{display:block;max-width:210px;width:auto;object-fit:contain}.brand-fallback{font-size:20px;font-weight:800}.navigation{display:flex;align-items:center;justify-content:center;gap:clamp(14px,2vw,28px)}.navigation>a{color:var(--header-link-color);text-decoration:none;font-size:var(--header-font-size);font-weight:700;white-space:nowrap;opacity:.9}.navigation>a:hover{opacity:1}.desktop-actions{display:flex;justify-self:end;align-items:center;gap:8px}.social-button{display:grid;width:38px;height:38px;place-items:center;border:1px solid currentColor;border-radius:50%;color:var(--header-link-color);opacity:.88}.social-button:hover{opacity:1}.social-button :deep(svg){width:17px;height:17px}.contact-button{display:inline-flex;min-height:42px;align-items:center;justify-content:center;border-radius:999px;padding:10px 18px;text-decoration:none;font-size:var(--header-font-size);font-weight:800;white-space:nowrap}.menu-toggle,.mobile-actions{display:none}@media(max-width:860px){.header-spacer{height:74px}.site-header{height:74px}.header-inner,.header-inner.without-actions{position:relative;display:flex;justify-content:space-between;padding:10px 18px}.brand img{max-width:160px}.menu-toggle{display:grid;width:42px;height:42px;place-content:center;gap:5px;border:1px solid currentColor;border-radius:12px;background:transparent;color:var(--header-link-color)}.menu-toggle span{display:block;width:20px;height:2px;background:currentColor}.navigation{position:absolute;left:14px;right:14px;top:calc(100% + 4px);display:none;align-items:stretch;gap:2px;border-radius:16px;background:#ffffff;padding:10px;color:#0f172a;box-shadow:0 18px 50px rgba(15,23,42,.25)}.navigation.open{display:flex;flex-direction:column}.navigation>a{padding:11px 12px;border-radius:9px;color:#0f172a}.navigation>a:hover{background:#f1f5f9}.desktop-actions{display:none}.mobile-actions{display:flex;align-items:center;gap:8px;border-top:1px solid #e2e8f0;margin-top:6px;padding:12px}.mobile-actions .social-button{color:#0f172a}.mobile-actions .contact-button{width:100%}}
.navigation>a{position:relative;transition:color .2s ease,transform .2s ease}.navigation>a:hover{color:var(--header-hover-color)}.navigation.hover-underline>a::after{position:absolute;left:0;right:0;bottom:-5px;height:2px;border-radius:2px;background:var(--header-hover-color);content:"";transform:scaleX(0);transform-origin:center;transition:transform .22s ease}.navigation.hover-underline>a:hover::after{transform:scaleX(1)}.navigation.hover-lift>a:hover{transform:translateY(-3px)}.navigation.hover-scale>a:hover{transform:scale(1.08)}
.site-header{overflow:visible}.site-header.is-preview{overflow:hidden}
.preview-banner-overlay{position:absolute;inset:0;z-index:0;pointer-events:none}
@media(max-width:860px){.navigation>a:hover{color:#0f172a}.navigation.hover-underline>a::after{display:none}.navigation.hover-lift>a:hover,.navigation.hover-scale>a:hover{transform:none}}
</style>
