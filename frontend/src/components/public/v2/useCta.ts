import { computed, type Ref } from "vue";
import { isWhatsappLink, normalizeExternalLink } from "../../../utils/links";

export interface CtaFields {
  ctaEnabled?: boolean;
  ctaMode?: "link" | "section";
  ctaLink?: string;
  ctaSectionId?: string | null;
  ctaOpenInNewTab?: boolean;
}

/** Destino do botão de uma seção, no mesmo formato que as seções antigas usam. */
export const useCta = (fields: Ref<CtaFields | null | undefined>) => {
  const mode = computed(() => fields.value?.ctaMode || "link");
  const isScroll = computed(() => mode.value === "section" && !!fields.value?.ctaSectionId);
  const hasTarget = computed(() => (mode.value === "section" ? !!fields.value?.ctaSectionId : !!fields.value?.ctaLink));
  const enabled = computed(() => fields.value?.ctaEnabled !== false && hasTarget.value);
  const href = computed(() =>
    isScroll.value ? `#${fields.value?.ctaSectionId}` : normalizeExternalLink(fields.value?.ctaLink) || "#"
  );
  const newTab = computed(() => !isScroll.value && fields.value?.ctaOpenInNewTab !== false);
  const trackType = computed(() => (!isScroll.value && isWhatsappLink(fields.value?.ctaLink || undefined) ? "whatsapp" : "cta"));
  const attrs = computed(() => ({
    href: href.value,
    target: newTab.value ? "_blank" : undefined,
    rel: newTab.value ? "noopener" : undefined,
    "data-scroll-target": isScroll.value ? "true" : undefined,
    "data-track-event": "cta",
    "data-track-type": trackType.value
  }));
  return { enabled, attrs };
};
