import type { HeroSection, PageConfig, PageSection } from "../types/page";
import type { PageTemplate } from "../types/templates";

export const TEMPLATE_WHATSAPP_PLACEHOLDER = "{{WHATSAPP_LINK}}";
export const TEMPLATE_LOGO_PLACEHOLDER = "{{AGENCY_LOGO_URL}}";

const cloneConfig = <T>(value: T): T => JSON.parse(JSON.stringify(value));

const walkStructure = (node: unknown, visitor: (container: any, key: any, value: any) => void) => {
  if (Array.isArray(node)) {
    node.forEach((item, index) => {
      visitor(node, index, item);
      walkStructure(item, visitor);
    });
    return;
  }
  if (node && typeof node === "object") {
    Object.entries(node as Record<string, unknown>).forEach(([key, value]) => {
      visitor(node, key, value);
      walkStructure(value, visitor);
    });
  }
};

interface TemplateBrandingOptions {
  logoUrl?: string | null;
  whatsappLink?: string | null;
  primaryColor?: string | null;
  enforcePrimaryColor?: boolean;
}

const CTA_COLOR_KEYS = new Set(["ctaColor", "highlightColor", "ctaDefaultColor"]);
const CTA_BACKGROUND_KEYS = new Set(["backgroundColor"]);
const ACCENT_BACKGROUND_TYPES = new Set(["countdown"]);

export const applyTemplateBranding = <T extends PageConfig | null | undefined>(
  config: T,
  branding: TemplateBrandingOptions
): T => {
  if (!config) return config;
  const cloned = cloneConfig(config);
  walkStructure(cloned, (container, key, value) => {
    if (typeof value === "string") {
      if (value === TEMPLATE_WHATSAPP_PLACEHOLDER) {
        container[key] = branding.whatsappLink || "";
      } else if (value === TEMPLATE_LOGO_PLACEHOLDER) {
        container[key] = branding.logoUrl || "";
      }
    }
    if (typeof key === "string" && key === "logoUrl" && typeof container[key] === "string") {
      if (container[key] === TEMPLATE_LOGO_PLACEHOLDER) {
        container[key] = branding.logoUrl || "";
      }
    }
    if (branding.enforcePrimaryColor && branding.primaryColor && typeof key === "string") {
      if (CTA_COLOR_KEYS.has(key)) {
        container[key] = branding.primaryColor;
      } else if (
        CTA_BACKGROUND_KEYS.has(key) &&
        container &&
        typeof container === "object" &&
        ACCENT_BACKGROUND_TYPES.has((container as any).type)
      ) {
        container[key] = branding.primaryColor;
      }
    }
  });
  return cloned;
};

export const extractTemplatePreviewImage = (template: PageTemplate): string => {
  const sections = template?.config_json?.sections || [];
  const hero = sections.find(section => section?.type === "hero") as HeroSection | undefined;
  return hero?.backgroundImage || "";
};

export const extractTemplateSections = (template: PageTemplate): PageSection[] => {
  return template?.config_json?.sections || [];
};

export const summarizeTemplate = (template: PageTemplate) => {
  const sections = extractTemplateSections(template);
  const enabledSections = sections.filter(section => section?.enabled !== false);
  return {
    totalSections: sections.length,
    enabledSections: enabledSections.length,
  };
};
