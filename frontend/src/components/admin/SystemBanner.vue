<template>
  <section class="system-banner" :class="backgroundClass">
    <div class="system-banner-left">
      <div v-if="hasIcon" class="system-banner-icon" aria-hidden="true">
        <svg v-if="iconName === 'TrendingUp'" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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

    <button v-if="hasCta && ctaLabel" type="button" class="system-banner-cta" @click="$emit('cta')">{{ ctaLabel }}</button>
    <button v-if="dismissible" type="button" class="system-banner-close" @click="$emit('close')" aria-label="Fechar">✕</button>
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
  }>(),
  {
    subtitle: "",
    hasIcon: true,
    iconName: "TrendingUp",
    backgroundVariant: "green_gradient",
    hasCta: true,
    ctaLabel: "Conectar Pixel",
    dismissible: true
  }
);

defineEmits<{
  (e: "cta"): void;
  (e: "close"): void;
}>();

const backgroundClass = computed(() => {
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
</script>

<style scoped>
.system-banner {
  border-radius: 16px;
  padding: 20px 24px;
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
  background: radial-gradient(circle, rgba(61, 204, 95, 0.2) 0%, transparent 70%);
  pointer-events: none;
}

.system-banner--green-gradient {
  background: linear-gradient(135deg, #1a3d25 0%, #2a5c38 50%, #1f4a2d 100%);
}

.system-banner--green-solid {
  background: #1a3d25;
}

.system-banner--green-light {
  background: linear-gradient(135deg, #2a5c38 0%, #3dcc5f 100%);
}

.system-banner--success {
  background: linear-gradient(135deg, #14532d 0%, #166534 100%);
}

.system-banner--warning {
  background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
}

.system-banner--info {
  background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
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
  background: rgba(61, 204, 95, 0.2);
  flex-shrink: 0;
}

.system-banner-icon svg {
  width: 20px;
  height: 20px;
  stroke: #3dcc5f;
}

.system-banner-title {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  margin: 0;
}

.system-banner-sub {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  margin-top: 2px;
  margin-bottom: 0;
}

.system-banner-cta {
  border: none;
  border-radius: 10px;
  background: #3dcc5f;
  color: #0f1f14;
  font-weight: 700;
  font-size: 13px;
  padding: 9px 18px;
  cursor: pointer;
  z-index: 1;
}

.system-banner-close {
  position: absolute;
  top: 10px;
  right: 10px;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.1);
  z-index: 2;
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
