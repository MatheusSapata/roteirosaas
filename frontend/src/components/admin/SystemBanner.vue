<template>
  <section class="system-banner" :class="[backgroundClass, { 'system-banner--compact': compact }]" :style="customBackgroundStyle">
    <div class="system-banner-left">
      <div
        v-if="hasIcon"
        class="system-banner-icon"
        :class="{ 'system-banner-icon--custom-svg': sanitizedIconSvg && !showIconBackground }"
        aria-hidden="true"
      >
        <span v-if="sanitizedIconSvg" class="system-banner-icon-svg" v-html="sanitizedIconSvg"></span>
        <svg v-else-if="iconName === 'TrendingUp'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        <svg v-else-if="iconName === 'Megaphone'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m3 11 18-5v12L3 13v-2Z" />
          <path d="M11 13.5V19a2 2 0 0 0 2 2h1" />
        </svg>
        <svg v-else-if="iconName === 'AlertCircle'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <svg v-else-if="iconName === 'Sparkles'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 3 1.9 4.1L18 9l-4.1 1.9L12 15l-1.9-4.1L6 9l4.1-1.9Z" />
          <path d="m5 17 .9 2 .9-2 2-.9-2-.9-.9-2-.9 2-2 .9 2 .9Z" />
        </svg>
        <svg v-else-if="iconName === 'Zap'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13 2 3 14h7l-1 8 10-12h-7z" />
        </svg>
        <svg v-else-if="iconName === 'Globe'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
        <svg v-else-if="iconName === 'Users'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        <svg v-else-if="iconName === 'CreditCard'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="5" width="20" height="14" rx="2" />
          <line x1="2" y1="10" x2="22" y2="10" />
        </svg>
        <svg v-else-if="iconName === 'Calendar'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <svg v-else-if="iconName === 'Settings'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.08V21a2 2 0 0 1-4 0v-.12a1.7 1.7 0 0 0-.4-1.08 1.7 1.7 0 0 0-1-.6 1.7 1.7 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.08-.4H2.8a2 2 0 0 1 0-4h.12a1.7 1.7 0 0 0 1.08-.4 1.7 1.7 0 0 0 .6-1 1.7 1.7 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.08V2.8a2 2 0 0 1 4 0v.12a1.7 1.7 0 0 0 .4 1.08 1.7 1.7 0 0 0 1 .6 1.7 1.7 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.26.3.46.65.6 1 .1.35.14.72.12 1.08a1.7 1.7 0 0 0 .4 1.08c.3.26.65.46 1 .6.35.1.72.14 1.08.12h.12a2 2 0 0 1 0 4h-.12a1.7 1.7 0 0 0-1.08.4 1.7 1.7 0 0 0-.6 1z" />
        </svg>
        <svg v-else-if="iconName === 'ExternalLink'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
        <svg v-else-if="iconName === 'CheckCircle'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="9 12 12 15 16 10" />
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      </div>
      <div>
        <p class="system-banner-title">{{ title }}</p>
        <p v-if="subtitle" class="system-banner-sub">{{ subtitle }}</p>
      </div>
    </div>

    <button v-if="hasCta && ctaLabel" type="button" class="system-banner-cta" :style="ctaButtonStyle" @click="$emit('cta')">{{ ctaLabel }}</button>
    <button v-if="dismissible" type="button" class="system-banner-close" @click="$emit('close')" aria-label="Fechar" title="Fechar">×</button>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    subtitle?: string;
    hasIcon?: boolean;
    iconName?: string | null;
    backgroundVariant?: string;
    hasCta?: boolean;
    ctaLabel?: string | null;
    dismissible?: boolean;
    compact?: boolean;
    iconSvg?: string | null;
    customBackground?: string | null;
    ctaBackground?: string | null;
    ctaTextColor?: string | null;
    showIconBackground?: boolean;
  }>(),
  {
    subtitle: "",
    hasIcon: true,
    iconName: "TrendingUp",
    backgroundVariant: "green_gradient",
    hasCta: true,
    ctaLabel: "Conectar Pixel",
    dismissible: true,
    compact: false,
    iconSvg: null,
    customBackground: null,
    ctaBackground: null,
    ctaTextColor: null,
    showIconBackground: true
  }
);

defineEmits<{
  (e: "cta"): void;
  (e: "close"): void;
}>();

const backgroundClass = computed(() => {
  if (props.customBackground) return "";
  const map: Record<string, string> = {
    green_gradient: "system-banner--green-gradient",
    green_solid: "system-banner--green-solid",
    green_light: "system-banner--green-light",
    success: "system-banner--success",
    warning: "system-banner--warning",
    info: "system-banner--info"
  };
  return map[props.backgroundVariant || "green_gradient"] || map.green_gradient;
});

const customBackgroundStyle = computed(() => (props.customBackground ? { background: props.customBackground } : undefined));

const ctaButtonStyle = computed(() => ({
  ...(props.ctaBackground ? { background: props.ctaBackground } : {}),
  ...(props.ctaTextColor ? { color: props.ctaTextColor } : {})
}));

const stripSvgCanvasBackground = (svg: string) => {
  const viewBoxMatch = svg.match(/\bviewBox=["']\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)\s*["']/i);
  const viewBoxWidth = viewBoxMatch?.[1];
  const viewBoxHeight = viewBoxMatch?.[2];
  return svg.replace(/(<svg\b[^>]*>\s*)<rect\b([^>]*)\/?>/i, (match, openTag, attrs) => {
    const widthMatch = String(attrs).match(/\bwidth=["']([^"']+)["']/i);
    const heightMatch = String(attrs).match(/\bheight=["']([^"']+)["']/i);
    const width = widthMatch?.[1];
    const height = heightMatch?.[1];
    const fillsCanvas =
      (width === "100%" && height === "100%") ||
      (viewBoxWidth && viewBoxHeight && width === viewBoxWidth && height === viewBoxHeight);
    return fillsCanvas ? openTag : match;
  });
};

const sanitizedIconSvg = computed(() => {
  const raw = String(props.iconSvg || "").trim();
  if (!raw || !raw.toLowerCase().startsWith("<svg")) return "";
  const safeSvg = raw
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    .replace(/\son\w+="[^"]*"/gi, "")
    .replace(/\son\w+='[^']*'/gi, "")
    .replace(/\s(?:href|xlink:href)=["']javascript:[^"']*["']/gi, "");
  return stripSvgCanvasBackground(safeSvg);
});
</script>

<style scoped>
.system-banner {
  border-radius: var(--radius-lg);
  padding: 20px 72px 20px 24px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
}

.system-banner::before {
  content: "";
  position: absolute;
  top: -30px;
  right: -30px;
  width: 160px;
  height: 160px;
  background: radial-gradient(circle, color-mix(in srgb, var(--primary) 22%, transparent) 0%, transparent 70%);
  pointer-events: none;
}

.system-banner--green-gradient {
  background: var(--gradient-brand);
}

.system-banner--green-solid {
  background: var(--brand-dark);
}

.system-banner--green-light {
  background: linear-gradient(135deg, var(--brand-dark), var(--primary));
}

.system-banner--success {
  background: linear-gradient(135deg, var(--brand-dark), var(--status-success-foreground));
}

.system-banner--warning {
  background: linear-gradient(135deg, var(--status-warning-foreground), var(--chart-8));
}

.system-banner--info {
  background: linear-gradient(135deg, var(--status-info-foreground), var(--chart-3));
}

.system-banner-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.system-banner-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--primary) 22%, transparent);
  flex-shrink: 0;
}

.system-banner-icon--custom-svg {
  width: auto;
  height: auto;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.system-banner-icon svg,
.system-banner-icon :deep(svg) {
  width: 20px;
  height: 20px;
  stroke: var(--primary-accent);
}

.system-banner-icon-svg {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.system-banner-icon--custom-svg .system-banner-icon-svg {
  width: auto;
  height: auto;
}

.system-banner-icon--custom-svg :deep(svg) {
  width: 40px;
  height: 40px;
}

.system-banner-title {
  color: var(--primary-foreground);
  font-size: 15px;
  font-weight: 700;
  margin: 0;
}

.system-banner-sub {
  color: color-mix(in srgb, var(--primary-foreground) 72%, transparent);
  font-size: 13px;
  margin-top: 2px;
  margin-bottom: 0;
}

.system-banner-cta {
  border: none;
  min-height: 36px;
  border-radius: var(--radius-lg);
  background: var(--primary);
  color: var(--primary-foreground);
  font-weight: 700;
  font-size: 13px;
  padding: 9px 18px;
  cursor: pointer;
  z-index: 1;
}

.system-banner-close {
  position: absolute;
  top: 14px;
  right: 14px;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--primary-foreground);
  background: color-mix(in srgb, var(--primary-foreground) 14%, transparent);
  z-index: 2;
}

.system-banner--compact {
  padding: 14px 48px 14px 16px;
  margin-bottom: 0;
  border-radius: var(--radius-lg);
  min-height: 84px;
}

.system-banner--compact::before {
  top: -40px;
  right: -42px;
  width: 120px;
  height: 120px;
}

.system-banner--compact .system-banner-left {
  gap: 12px;
  min-width: 0;
}

.system-banner--compact .system-banner-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
}

.system-banner--compact .system-banner-icon--custom-svg {
  width: auto;
  height: auto;
}

.system-banner--compact .system-banner-icon svg,
.system-banner--compact .system-banner-icon :deep(svg) {
  width: 16px;
  height: 16px;
}

.system-banner--compact .system-banner-icon-svg {
  width: 16px;
  height: 16px;
}

.system-banner--compact .system-banner-icon--custom-svg .system-banner-icon-svg {
  width: auto;
  height: auto;
}

.system-banner--compact .system-banner-icon--custom-svg :deep(svg) {
  width: 32px;
  height: 32px;
}

.system-banner--compact .system-banner-title {
  font-size: 12px;
  line-height: 1.15;
}

.system-banner--compact .system-banner-sub {
  font-size: 10px;
  line-height: 1.2;
  margin-top: 3px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.system-banner--compact .system-banner-cta {
  border-radius: 10px;
  font-size: 11px;
  padding: 7px 12px;
  min-height: 38px;
  max-width: 128px;
}

.system-banner--compact .system-banner-close {
  top: 10px;
  right: 10px;
  width: 20px;
  height: 20px;
  border-radius: 5px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .system-banner {
    padding-right: 56px;
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
  }

  .system-banner-cta {
    align-self: flex-start;
  }
}
</style>
