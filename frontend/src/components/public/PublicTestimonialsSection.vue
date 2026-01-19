<template>
  <section class="w-full" :style="{ background: section.backgroundColor || '#ffffff' }" :id="section.anchorId || undefined">
    <div class="mx-auto flex max-w-6xl flex-col items-center px-6 py-12">
      <h2 class="text-center text-3xl font-bold leading-tight text-slate-900 md:text-4xl">
        {{ section.title || "Depoimentos de clientes" }}
      </h2>
      <p class="mt-2 text-center text-sm text-slate-600 md:text-base">
        {{ section.subtitle || "O que dizem depois de viajar conosco" }}
      </p>

      <div class="mt-8 grid w-full gap-6 md:gap-6 justify-items-stretch" :class="gridClass">
        <article
          v-for="(item, index) in displayedWithMedia"
          :key="index"
          class="h-full w-full rounded-[20px] p-6 text-slate-900 shadow-xl md:p-7"
          :style="{ background: cardColor }"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full bg-slate-100 text-sm font-semibold text-slate-500">
                <img v-if="item.avatarUrl" :src="item.avatarUrl" alt="Avatar" class="h-full w-full object-cover" />
                <span v-else>{{ initials(item.name) }}</span>
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ item.name }}</p>
                <p class="text-xs text-slate-500">{{ item.role }}</p>
              </div>
            </div>
          </div>

          <div class="mt-4 flex items-center gap-1 text-lg" :style="{ color: '#f59e0b' }">
            <span v-for="star in 5" :key="star">★</span>
          </div>

          <p class="mt-4 text-base leading-relaxed text-slate-800">
            {{ item.text }}
          </p>
        </article>
      </div>

      <div v-if="ctaHasTarget" class="mt-6">
        <a
          :href="ctaHref"
          :data-scroll-target="ctaIsScroll ? 'true' : null"
          target="_blank"
          rel="noopener"
          data-track-event="cta"
          :data-track-type="ctaTrackType"
          class="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
          :style="{ background: accent }"
        >
          {{ section.ctaLabel || "Falar com especialista" }}
        </a>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { resolveMediaUrl } from "../../utils/media";
import { isWhatsappLink } from "../../utils/links";
import type { TestimonialsSection } from "../../types/page";

const props = defineProps<{ section: TestimonialsSection }>();

const accent = computed(() => props.section.ctaColor || "#5b49ff");
const accentBackground = computed(() => props.section.backgroundColor || "linear-gradient(135deg,#5b49ff,#3b82f6)");
const cardColor = computed(() => props.section.cardColor || "#ffffff");

const toRgba = (hex: string, alpha: number) => {
  const cleaned = hex.replace("#", "");
  const full = cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned;
  if (full.length !== 6) return `rgba(91,73,255,${alpha})`;
  const r = parseInt(full.substring(0, 2), 16);
  const g = parseInt(full.substring(2, 4), 16);
  const b = parseInt(full.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const accentSoft = computed(() => toRgba(accent.value, 0.35));

const initials = (name?: string) => {
  if (!name) return "—";
  const parts = name.trim().split(" ").filter(Boolean);
  const first = parts[0]?.[0] || "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase() || "—";
};
const displayed = computed(() => props.section.items?.slice(0, 3) || []);
const displayedWithMedia = computed(() =>
  displayed.value.map(item => ({
    ...item,
    avatarUrl: resolveMediaUrl(item.avatar) || item.avatar || ""
  }))
);
const gridClass = computed(() => {
  const count = displayedWithMedia.value.length;
  if (count === 1) return "grid-cols-1";
  if (count === 2) return "grid-cols-1 md:grid-cols-2";
  return "grid-cols-1 md:grid-cols-3";
});
const ctaMode = computed(() => props.section.ctaMode || "link");
const ctaHref = computed(() =>
  ctaMode.value === "section" && props.section.ctaSectionId ? `#${props.section.ctaSectionId}` : props.section.ctaLink || "#"
);
const ctaHasTarget = computed(() =>
  ctaMode.value === "section" ? !!props.section.ctaSectionId : !!props.section.ctaLink
);
const ctaIsScroll = computed(() => ctaMode.value === "section" && !!props.section.ctaSectionId);
const ctaTrackType = computed(() =>
  ctaMode.value === "section" ? "cta" : isWhatsappLink(props.section.ctaLink || undefined) ? "whatsapp" : "cta"
);
</script>
