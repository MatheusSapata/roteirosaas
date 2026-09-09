<template>
  <section class="w-full" :style="sectionStyle" :id="section.anchorId || undefined" data-video-vsl>
    <div v-if="backgroundImage" class="vsl-background" :style="backgroundStyle"></div>
    <div class="relative z-[1] mx-auto w-full max-w-5xl px-6 text-center" :class="previewDevice ? 'py-16' : 'pb-16 pt-8'">
      <div v-if="section.logoEnabled !== false && resolvedLogo" class="mb-4 flex justify-center">
        <img :src="resolvedLogo" :alt="title" class="vsl-brand-logo" :style="logoStyle" />
      </div>
      <h2 class="text-3xl font-bold leading-tight md:text-4xl" :style="{ color: primaryText }">{{ title }}</h2>
      <div v-if="subtitleHtml" class="mt-2 text-base leading-relaxed md:text-lg" :style="{ color: mutedText }" v-html="subtitleHtml"></div>

      <div v-if="playerUrl" class="group mx-auto mt-8 w-full overflow-hidden rounded-[28px] shadow-2xl ring-1 ring-slate-200" :class="videoContainerClass">
        <div class="relative" :style="{ aspectRatio: videoAspectRatioCss }">
          <iframe ref="iframeRef" class="pointer-events-none absolute inset-0 h-full w-full" :src="playerUrl" :title="title" frameborder="0" tabindex="-1"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
          <img v-if="!hasStarted && thumbnailUrl" :src="thumbnailUrl" alt="" class="pointer-events-none absolute inset-0 z-[1] h-full w-full object-cover" />
          <button type="button" class="vsl-play-button" :style="{ background: progressColor }" :aria-label="isPlaying ? 'Pausar vídeo' : 'Reproduzir vídeo'" @click="togglePlayback">
            <svg v-if="isPlaying" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zm6 0h4v14h-4z" /></svg>
            <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="m8 5 11 7-11 7z" /></svg>
          </button>
          <div v-if="section.progressBarEnabled !== false" class="vsl-progress-track" aria-hidden="true">
            <div class="vsl-progress-fill" :style="{ width: `${visualProgress}%`, background: progressColor }"></div>
          </div>
        </div>
      </div>
      <div v-else class="mt-8 rounded-3xl border border-dashed border-slate-200 bg-white/60 px-6 py-16 text-sm text-slate-500">
        Adicione um link do YouTube para exibir a VSL.
      </div>

      <Transition name="vsl-cta-fade">
        <div v-if="showButton && ctaLink" class="mt-8">
          <a :href="normalizedCtaLink" :target="section.ctaOpenInNewTab !== false ? '_blank' : null"
            :rel="section.ctaOpenInNewTab !== false ? 'noopener' : null" data-track-event="cta" data-track-type="cta"
            class="vsl-cta-button inline-flex min-h-14 items-center justify-center rounded-full px-8 py-4 text-base font-semibold shadow-lg transition hover:shadow-xl"
            :style="{ background: ctaColor, color: ctaTextColor }">{{ ctaLabel }}</a>
        </div>
      </Transition>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import type { VideoVslSection } from "../../types/page";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { deriveTextPalette, getReadableTextColor } from "../../utils/colorContrast";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import { normalizeExternalLink } from "../../utils/links";
import { extractYoutubeId, normalizeYoutubePlayerUrl } from "../../utils/video";
import { resolveMediaUrl } from "../../utils/media";

const props = withDefaults(defineProps<{ section: VideoVslSection; previewDevice?: "desktop" | "mobile"; highlightColor?: string; logoUrl?: string; replaceHeadingWithLogo?: boolean }>(), { replaceHeadingWithLogo: true });
const emit = defineEmits<{ (event: "unlocked"): void }>();
const localize = createLocalizer(getCurrentLanguage());
const resolvedLogo = computed(() => resolveMediaUrl(props.section.logoUrl || props.logoUrl));
const logoStyle = computed(() => ({ maxHeight: `${Math.max(32, Math.min(180, Number(props.section.logoSize) || 88))}px` }));
const backgroundImage = computed(() => resolveMediaUrl(props.section.backgroundImage));
const backgroundStyle = computed(() => ({ backgroundImage: backgroundImage.value ? `url("${backgroundImage.value}")` : undefined, opacity: 1 - Math.max(0, Math.min(100, props.section.backgroundImageOpacity ?? 70)) / 100 }));
const sectionStyle = computed(() => ({
  background: props.section.backgroundColor || "#f5f7fb",
  position: "relative" as const,
  overflow: "hidden",
  minHeight: props.previewDevice ? undefined : "111.112vh",
  display: props.previewDevice ? undefined : "grid",
  alignItems: props.previewDevice ? undefined : "start",
  boxSizing: "border-box" as const,
  paddingTop: !props.previewDevice && !props.replaceHeadingWithLogo ? "var(--vsl-header-clearance)" : undefined
}));
const iframeRef = ref<HTMLIFrameElement | null>(null);
const unlocked = ref(false);
const isPlaying = ref(false);
const currentTime = ref(0);
const videoDuration = ref(0);
const hasEnded = ref(false);
const hasStarted = ref(false);
let pollTimer: number | null = null;

const title = computed(() => localize(props.section.title).trim() || "Assista antes de continuar");
const subtitleHtml = computed(() => sanitizeHtml(localize(props.section.subtitle)));
const palette = computed(() => deriveTextPalette(props.section.textColor));
const primaryText = computed(() => palette.value.primary);
const mutedText = computed(() => palette.value.muted);
const ctaColor = computed(() => props.section.ctaColor || "#41ce5f");
const progressColor = computed(() => props.highlightColor || props.section.ctaColor || "#41ce5f");
const ctaTextColor = computed(() => getReadableTextColor(ctaColor.value));
const playerUrl = computed(() => normalizeYoutubePlayerUrl(props.section.videoUrl));
const thumbnailUrl = computed(() => {
  const custom = resolveMediaUrl(props.section.thumbnailUrl);
  const id = extractYoutubeId(props.section.videoUrl);
  return custom || (id ? `https://i.ytimg.com/vi/${id}/maxresdefault.jpg` : "");
});
const resolvedVideoFormat = computed(() => {
  return props.section.videoAspectRatio === "vertical" || props.section.videoAspectRatio === "square"
    ? props.section.videoAspectRatio
    : "horizontal";
});
const videoAspectRatioCss = computed(() => resolvedVideoFormat.value === "vertical" ? "9 / 16" : resolvedVideoFormat.value === "square" ? "1 / 1" : "16 / 9");
const videoContainerClass = computed(() => resolvedVideoFormat.value === "vertical" ? "max-w-[420px]" : resolvedVideoFormat.value === "square" ? "max-w-2xl" : "max-w-4xl");
const ctaLabel = computed(() => localize(props.section.ctaLabel).trim() || "Quero saber mais");
const ctaLink = computed(() => props.section.ctaLink?.trim() || "");
const normalizedCtaLink = computed(() => normalizeExternalLink(ctaLink.value) || "#");
const unlockSeconds = computed(() => Math.max(0, Number(props.section.unlockAfterSeconds) || 0));
const visualProgress = computed(() => {
  const elapsed = Math.max(0, currentTime.value);
  const duration = Math.max(0, videoDuration.value);
  if (hasEnded.value || (duration > 0 && elapsed >= duration - 0.25)) return 100;
  if (duration > 0 && duration <= 60) return Math.min(99.5, (elapsed / duration) * 100);
  if (elapsed <= 30) return Math.min(50, (elapsed / 30) * 50);
  if (elapsed <= 60) return 50 + ((elapsed - 30) / 30) * 20;
  if (duration > 60) return Math.min(99.5, 70 + ((elapsed - 60) / (duration - 60)) * 30);
  return 70;
});
const showButton = computed(() => unlocked.value && props.section.unlockAction !== "reveal_page");

const unlock = () => {
  if (unlocked.value) return;
  unlocked.value = true;
  emit("unlocked");
};
const postPlayerCommand = (func: string) => iframeRef.value?.contentWindow?.postMessage(JSON.stringify({ event: "command", func, args: [] }), "https://www.youtube.com");
const connectPlayer = () => iframeRef.value?.contentWindow?.postMessage(JSON.stringify({ event: "listening", id: "video-vsl" }), "https://www.youtube.com");
const togglePlayback = () => {
  hasStarted.value = true;
  connectPlayer();
  postPlayerCommand(isPlaying.value ? "pauseVideo" : "playVideo");
};
const handleMessage = (event: MessageEvent) => {
  if (event.origin !== "https://www.youtube.com" || !iframeRef.value || event.source !== iframeRef.value.contentWindow) return;
  let payload: any;
  try { payload = typeof event.data === "string" ? JSON.parse(event.data) : event.data; } catch { return; }
  const reportedTime = Number(payload?.info?.currentTime);
  const duration = Number(payload?.info?.duration);
  const playerState = Number(payload?.info?.playerState);
  if (Number.isFinite(playerState)) isPlaying.value = playerState === 1;
  if (playerState === 0) hasEnded.value = true;
  if (playerState === 1) hasEnded.value = false;
  if (Number.isFinite(duration) && duration > 0) videoDuration.value = duration;
  if (Number.isFinite(reportedTime)) {
    currentTime.value = reportedTime;
    if (reportedTime >= unlockSeconds.value) unlock();
  }
};

onMounted(() => {
  if (props.previewDevice) return;
  if (unlockSeconds.value === 0) { unlock(); return; }
  window.addEventListener("message", handleMessage);
  pollTimer = window.setInterval(() => { connectPlayer(); postPlayerCommand("getCurrentTime"); postPlayerCommand("getDuration"); }, 500);
});
onBeforeUnmount(() => {
  window.removeEventListener("message", handleMessage);
  if (pollTimer !== null) window.clearInterval(pollTimer);
});
</script>

<style scoped>
.vsl-play-button{position:absolute;left:50%;top:50%;z-index:2;display:flex;width:68px;height:68px;transform:translate(-50%,-50%);align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.55);border-radius:9999px;background:rgba(0,0,0,.72);color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.3);opacity:0;pointer-events:none;transition:opacity 1000ms ease,transform .2s ease,background .2s ease}.group:hover .vsl-play-button,.vsl-play-button:focus-visible{opacity:1;pointer-events:auto}.vsl-play-button:hover{transform:translate(-50%,-50%) scale(1.06);background:rgba(0,0,0,.88)}.vsl-play-button:focus-visible{outline:3px solid rgba(255,255,255,.9);outline-offset:3px}.vsl-play-button svg{width:30px;height:30px;fill:currentColor}@media(hover:none){.vsl-play-button{opacity:1;pointer-events:auto}}
.vsl-cta-fade-enter-active,.vsl-cta-fade-leave-active{transition:opacity 1000ms ease}.vsl-cta-fade-enter-from,.vsl-cta-fade-leave-to{opacity:0}.vsl-cta-fade-enter-to,.vsl-cta-fade-leave-from{opacity:1}
.vsl-progress-track{position:absolute;right:0;bottom:0;left:0;z-index:3;height:14px;background:rgba(255,255,255,.22);pointer-events:none}.vsl-progress-fill{height:100%;width:0;border-radius:0 9999px 9999px 0;box-shadow:0 0 10px rgba(0,0,0,.18);transition:width 500ms linear}
.vsl-cta-button{animation:vsl-cta-pulse 2.4s ease-in-out infinite;will-change:transform,box-shadow}.vsl-cta-button:hover{animation-play-state:paused;transform:translateY(-2px)}@keyframes vsl-cta-pulse{0%,100%{transform:scale(1);box-shadow:0 10px 22px rgba(0,0,0,.16)}50%{transform:scale(1.025);box-shadow:0 13px 30px rgba(0,0,0,.24)}}@media(prefers-reduced-motion:reduce){.vsl-cta-button{animation:none}}
.vsl-brand-logo{display:block;width:auto;max-width:min(260px,70vw);max-height:88px;object-fit:contain}
.vsl-background{position:absolute;inset:0;z-index:0;background-position:center;background-size:cover;background-repeat:no-repeat;pointer-events:none}
:global(:root){--vsl-header-clearance:96px}@media(max-width:860px){:global(:root){--vsl-header-clearance:84px}}
</style>
