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
        <ActivityIcon v-else-if="iconName === 'TrendingUp'" aria-hidden="true" />
        <MegaphoneIcon v-else-if="iconName === 'Megaphone'" aria-hidden="true" />
        <CircleAlertIcon v-else-if="iconName === 'AlertCircle'" aria-hidden="true" />
        <SparklesIcon v-else-if="iconName === 'Sparkles'" aria-hidden="true" />
        <ZapIcon v-else-if="iconName === 'Zap'" aria-hidden="true" />
        <GlobeIcon v-else-if="iconName === 'Globe'" aria-hidden="true" />
        <UsersIcon v-else-if="iconName === 'Users'" aria-hidden="true" />
        <CreditCardIcon v-else-if="iconName === 'CreditCard'" aria-hidden="true" />
        <CalendarIcon v-else-if="iconName === 'Calendar'" aria-hidden="true" />
        <SettingsIcon v-else-if="iconName === 'Settings'" aria-hidden="true" />
        <ExternalLinkIcon v-else-if="iconName === 'ExternalLink'" aria-hidden="true" />
        <CircleCheckIcon v-else-if="iconName === 'CheckCircle'" aria-hidden="true" />
        <ActivityIcon v-else aria-hidden="true" />
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
import {
  ActivityIcon,
  CalendarIcon,
  CircleAlertIcon,
  CircleCheckIcon,
  CreditCardIcon,
  ExternalLinkIcon,
  GlobeIcon,
  MegaphoneIcon,
  SettingsIcon,
  SparklesIcon,
  UsersIcon,
  ZapIcon
} from "lucide-vue-next";
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
