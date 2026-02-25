<template>
  <div class="w-full space-y-6 px-4 py-10 md:px-8">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm uppercase tracking-wide text-slate-500">Editor</p>
        <h1 class="text-3xl font-bold text-slate-900">{{ page?.title || "Roteiro" }}</h1>
        <p class="text-sm text-slate-500">Monte a página por seções, salve e visualize ao lado.</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <label class="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" v-model="previewEnabled" class="h-4 w-4" />
          Mostrar preview
        </label>

        <button
          @click="saveTemplate"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          Salvar como meu template
        </button>

        <button
          @click="goBack"
          class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          Voltar
        </button>

        <button
          @click="saveConfig"
          class="rounded-lg border border-brand px-4 py-2 text-sm font-semibold text-brand hover:bg-sky-50"
        >
          Salvar
        </button>

        <button
          v-if="!isPublished"
          @click="publishPage"
          class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          Publicar
        </button>

        <span
          v-else
          class="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100"
        >
          Publicada
        </span>
      </div>
    </div>

    <!-- Selecionar pixel e eventos -->
    <div class="rounded-2xl bg-white p-4 shadow-md">
      <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div class="space-y-1">
          <p class="text-sm font-semibold text-slate-700">Pixel de rastreamento</p>
          <p class="text-xs text-slate-500">
            Escolha um pixel cadastrado em Integrações e quais eventos deseja enviar. Disponível a partir do plano Essencial.
          </p>
        </div>

        <div class="w-full max-w-xl space-y-3">
          <div
            v-if="!canSelectPixel"
            class="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
          >
            Adicione pixels na página Integrações (plano Essencial ou superior).
          </div>

          <template v-else>
            <select v-model="selectedPixel" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800">
              <option value="">Selecione</option>
              <option v-for="p in pixels" :key="p.name" :value="p.name">
                {{ p.name }} · {{ p.type === "meta" ? "Meta" : "GA4" }}
              </option>
            </select>

            <div class="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <p class="font-semibold text-slate-800">Eventos a enviar</p>

              <label class="mt-2 flex items-center gap-2">
                <input type="checkbox" v-model="trackingEvents.pageView" class="h-4 w-4" />
                Page view (carregamento da página)
              </label>

              <label class="mt-1 flex items-center gap-2">
                <input type="checkbox" v-model="trackingEvents.ctaClicks" class="h-4 w-4" />
                Cliques em CTAs (botões principais)
              </label>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Dialog de limite de plano (reutilizado também para "template no free") -->
    <div v-if="limitModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Limite do plano</p>
        <h3 class="mt-2 text-xl font-bold text-slate-900">Ação indisponível</h3>
        <p class="mt-2 text-sm text-slate-600">
          {{ limitModal.message || "Seu plano atual atingiu o limite. Atualize para continuar." }}
        </p>

        <div class="mt-4 flex flex-wrap gap-2">
          <button
            @click="limitModal.open = false"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Fechar
          </button>

          <button
            @click="goPlans"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
          >
            Ver planos
          </button>
        </div>
      </div>
    </div>

    <!-- Dialog de sucesso ao publicar -->
    <div v-if="successModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <p class="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Publicação</p>
        <h3 class="mt-2 text-xl font-bold text-slate-900">Página publicada com sucesso</h3>
        <p class="mt-2 text-sm text-slate-600">Escolha o que deseja fazer em seguida.</p>

        <div class="mt-4 flex flex-wrap gap-2">
          <button
            @click="successModal.open = false"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Fechar
          </button>

          <button
            @click="goPages"
            class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Voltar para páginas
          </button>

          <button
            :disabled="!publicUrl"
            @click="viewPublicPage"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:opacity-50"
          >
            Ver página
          </button>
        </div>
      </div>
    </div>

    <div class="grid gap-4" :class="gridLayoutClass">
      <div class="space-y-4">
        <div class="rounded-2xl bg-white p-4 shadow-md">
          <label class="text-sm font-semibold text-slate-600">Título</label>
          <input v-model="pageTitle" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />

          <div class="mt-3 flex flex-wrap items-center gap-2">
            <label class="block text-sm font-semibold text-slate-600">Slug</label>
            <span class="text-xs text-slate-500">
              Slug é a parte do link depois da barra, sem espaços ou acentos. Ex.: meu-roteiro-incrivel.
            </span>
          </div>
          <input v-model="pageSlug" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />

          <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-600">
            <label class="flex items-center gap-2">
              <span>Cor 1</span>
              <input type="color" v-model="colorA" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
            </label>

            <label class="flex items-center gap-2">
              <span>Cor 2</span>
              <input type="color" v-model="colorB" class="h-9 w-9 cursor-pointer rounded border border-slate-200 bg-white" />
            </label>

            <span class="text-xs text-slate-500">Aplica alternância em todas as seções (exceto hero).</span>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-md">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-sm font-semibold text-slate-700">Adicionar seção:</span>
            <button
              v-for="type in sectionTypes"
              :key="type"
              class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100"
              @click="addSection(type)"
            >
              {{ sectionLabels[type] || type }}
            </button>
          </div>
        </div>

        <template v-for="(section, index) in sections" :key="index">
          <div v-if="section" class="rounded-2xl bg-white p-4 shadow-md ring-1 ring-slate-100">
            <div class="mb-3 flex items-center justify-between">
              <div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <button
                  class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                  @click="toggleCollapse(index)"
                >
                  {{ isCollapsed(index) ? "Expandir" : "Recolher" }}
                </button>

                <span>
                  Seção: {{ sectionLabels[(section as any).type] || (section as any).type }}
                  <span v-if="!(section as any).enabled" class="text-red-500">(desativada)</span>
                </span>
              </div>

              <div class="flex items-center gap-2 text-xs">
                <button
                  class="rounded-full border border-red-200 px-3 py-1 font-semibold text-red-600 hover:bg-red-50"
                  @click="removeSection(index)"
                >
                  Excluir
                </button>

                <button
                  class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-700 hover:bg-slate-100"
                  @click="duplicateSection(index)"
                >
                  Duplicar
                </button>

                <button
                  class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-40"
                  :disabled="index === 0"
                  @click="moveSection(index, -1)"
                >
                  ↑
                </button>

                <button
                  class="rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-40"
                  :disabled="index === sections.length - 1"
                  @click="moveSection(index, 1)"
                >
                  ↓
                </button>
              </div>
            </div>

            <component
              v-if="!isCollapsed(index)"
              :is="formComponents[(section as any).type]"
              v-model:modelValue="sections[index]"
            />
          </div>
        </template>
      </div>

      <div v-if="previewEnabled" class="space-y-4">
        <div class="rounded-2xl bg-white p-4 shadow-md">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-lg font-semibold text-slate-900">Preview visual (usando os mesmos componentes públicos)</h2>
            <div class="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-semibold text-slate-600">
              <button
                type="button"
                class="rounded-full px-3 py-1 transition"
                :class="previewDevice === 'desktop' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
                @click="previewDevice = 'desktop'"
              >
                Desktop
              </button>
              <button
                type="button"
                class="rounded-full px-3 py-1 transition"
                :class="previewDevice === 'mobile' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
                @click="previewDevice = 'mobile'"
              >
                Mobile
              </button>
            </div>
          </div>

          <div class="mt-4">
            <div
              :class="previewDevice === 'mobile'
                ? 'mx-auto w-full max-w-[420px] overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-xl'
                : ''"
            >
              <div :class="previewDevice === 'mobile' ? 'max-h-[80vh] overflow-y-auto' : ''">
                <div class="space-y-6">
                  <template v-for="(section, idx) in previewSections" :key="'preview-' + idx">
                <component
                  v-if="section && (section as any).enabled"
                  :is="publicComponents[(section as any).type]"
                  :section="section"
                  :previewDevice="previewDevice"
                  v-bind="(section as any).type === 'hero' ? { branding } : {}"
                />
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div
        v-if="snackbar.open"
        class="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-2xl"
      >
        {{ snackbar.text }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
import SectionHeroForm from "../../components/admin/SectionHeroForm.vue";
import SectionPricesForm from "../../components/admin/SectionPricesForm.vue";
import SectionItineraryForm from "../../components/admin/SectionItineraryForm.vue";
import SectionFaqForm from "../../components/admin/SectionFaqForm.vue";
import SectionTestimonialsForm from "../../components/admin/SectionTestimonialsForm.vue";
import SectionCtaForm from "../../components/admin/SectionCtaForm.vue";
import SectionStoryForm from "../../components/admin/SectionStoryForm.vue";
import SectionReasonsForm from "../../components/admin/SectionReasonsForm.vue";
import SectionCountdownForm from "../../components/admin/SectionCountdownForm.vue";
import PublicHeroSection from "../../components/public/PublicHeroSection.vue";
import PublicPricesSection from "../../components/public/PublicPricesSection.vue";
import PublicItinerarySection from "../../components/public/PublicItinerarySection.vue";
import PublicFaqSection from "../../components/public/PublicFaqSection.vue";
import PublicTestimonialsSection from "../../components/public/PublicTestimonialsSection.vue";
import PublicCtaSection from "../../components/public/PublicCtaSection.vue";
import PublicStorySection from "../../components/public/PublicStorySection.vue";
import PublicReasonsSection from "../../components/public/PublicReasonsSection.vue";
import PublicCountdownSection from "../../components/public/PublicCountdownSection.vue";
import PublicFreeFooterBrandSection from "../../components/public/PublicFreeFooterBrandSection.vue";
import { useAuthStore } from "../../store/useAuthStore";
import { useAgencyStore } from "../../store/useAgencyStore";
import type {
  CtaSection,
  EditorPreferences,
  FaqSection,
  HeroSection,
  ItinerarySection,
  PageConfig,
  PageSection,
  PricesSection,
  TestimonialsSection,
  StorySection,
  ReasonsSection,
  CountdownSection,
  SectionType,
  ThemeConfig
} from "../../types/page";
import { sectionsInjectionKey } from "../../components/admin/sectionsContext";
import { sectionLabels as defaultSectionLabels } from "../../utils/sectionLabels";

interface Page {
  id: number;
  title: string;
  slug: string;
  status: string;
  config_json?: PageConfig | string | null;
  cover_image_url?: string;
}

const route = useRoute();
const router = useRouter();
const pageId = Number(route.params.id);

const page = ref<Page | null>(null);
const pageTitle = ref("");
const pageSlug = ref("");

const auth = useAuthStore();
const agencyStore = useAgencyStore();

const message = ref("");
const errorMessage = ref("");

const limitModal = ref({ open: false, message: "" });
const successModal = ref({ open: false });
const snackbar = ref({ open: false, text: "" });

const isPublished = computed(() => page.value?.status === "published");
const collapsed = ref<Record<number, boolean>>({});

const fallbackPrimaryColor = "#0ea5e9";
const heroDefaultGradient = "#0b0f19";
const legacyHeroGradient = "#0a4ddf";

const branding = ref({
  agency_name: "Agencia",
  logo_url: "",
  primary_color: fallbackPrimaryColor,
  secondary_color: fallbackPrimaryColor
});

const theme = ref<ThemeConfig>({
  color1: "#ffffff",
  color2: "#f8fafc",
  heroTheme: "immersive",
  ctaDefaultColor: fallbackPrimaryColor,
  ctaTextColor: "#0f172a",
  sidebarTheme: "light"
});

const editorPrefs = ref<EditorPreferences>({
  previewEnabled: true,
  previewLayout: "split",
  previewDevice: "desktop"
});

const colorA = ref(theme.value.color1);
const colorB = ref(theme.value.color2);
const previewEnabled = ref(editorPrefs.value.previewEnabled);
const previewDevice = ref<"desktop" | "mobile">(editorPrefs.value.previewDevice || "desktop");

const buildCountdownTargetDate = () => {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16);
};

const sectionTypes: SectionType[] = ["hero", "prices", "itinerary", "faq", "testimonials", "cta", "story", "reasons", "countdown"];
const sectionLabels = defaultSectionLabels;

const formComponents: Partial<Record<SectionType, any>> = {
  hero: SectionHeroForm,
  prices: SectionPricesForm,
  itinerary: SectionItineraryForm,
  faq: SectionFaqForm,
  testimonials: SectionTestimonialsForm,
  cta: SectionCtaForm,
  story: SectionStoryForm,
  reasons: SectionReasonsForm,
  countdown: SectionCountdownForm
};

const publicComponents: Partial<Record<SectionType, any>> = {
  hero: PublicHeroSection,
  prices: PublicPricesSection,
  itinerary: PublicItinerarySection,
  faq: PublicFaqSection,
  testimonials: PublicTestimonialsSection,
  cta: PublicCtaSection,
  story: PublicStorySection,
  reasons: PublicReasonsSection,
  countdown: PublicCountdownSection,
  free_footer_brand: PublicFreeFooterBrandSection
};

const sections = ref<PageSection[]>([]);
const previewSections = ref<PageSection[]>([]);
const previewReady = ref(false);
const hasWindow = typeof window !== "undefined";
const getBrowserStorage = () => {
  if (!hasWindow) return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
};
provide(sectionsInjectionKey, sections);

const createAnchorId = () => `section-${Math.random().toString(36).slice(2, 9)}`;
const ensureSectionAnchor = <T extends PageSection>(section: T): T => {
  if (section.anchorId) return section;
  return { ...section, anchorId: createAnchorId() } as T;
};
const cloneWithNewAnchor = <T extends PageSection>(section: T): T => ({ ...section, anchorId: createAnchorId() } as T);

const templateKey = computed(() => (auth.user ? `page_template_${auth.user.id}` : null));
const whatsappDigits = computed(() => (auth.user?.whatsapp || "").replace(/\D/g, ""));
const buildWhatsappLink = (title: string) => {
  if (!whatsappDigits.value) return "";
  const text = encodeURIComponent(`Oi, tenho interesse no roteiro: ${title || "Roteiro"}`);
  return `https://wa.me/${whatsappDigits.value}?text=${text}`;
};
const lastAutoWhatsAppLink = ref<string | null>(null);

const pixels = ref<{ id: number; name: string; type: "meta" | "ga"; value: string }[]>([]);
const selectedPixel = ref<string | null>(null);
const trackingEvents = ref({ pageView: true, ctaClicks: true });

const canSelectPixel = computed(() => (auth.user?.plan || "free") !== "free" && pixels.value.length > 0);

const currentAgency = computed(() => {
  const selected = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  return selected || agencyStore.agencies[0] || null;
});

const resolvePrimaryColor = () => currentAgency.value?.primary_color || fallbackPrimaryColor;

const fillHeroLogoFromAgency = () => {
  const logo = currentAgency.value?.logo_url;
  if (!logo) return;
  sections.value = sections.value.map(section => {
    if ((section as any).type === "hero" && !(section as any).logoUrl) {
      return { ...(section as any), logoUrl: logo } as PageSection;
    }
    return section;
  });
};

const applyAgencyBranding = () => {
  const primary = resolvePrimaryColor();
  const agency = currentAgency.value;
  branding.value = {
    ...branding.value,
    agency_name: agency?.name || branding.value.agency_name,
    logo_url: agency?.logo_url || branding.value.logo_url,
    primary_color: primary,
    secondary_color: agency?.secondary_color || primary
  };
  theme.value.ctaDefaultColor = primary;
  fillHeroLogoFromAgency();
};

const applyPrimaryToThemeAndSections = (oldDefault?: string) => {
  const primary = resolvePrimaryColor();
  const previous = oldDefault || theme.value.ctaDefaultColor;
  theme.value.ctaDefaultColor = primary;

  sections.value = applySectionBackgrounds(
    sections.value.map(section => {
      if (!section) return section;
      const current = (section as any).ctaColor as string | undefined;
      const shouldReplace =
        !current ||
        current.toLowerCase?.() === fallbackPrimaryColor.toLowerCase() ||
        (!!previous && current.toLowerCase?.() === previous.toLowerCase());
      return shouldReplace ? ({ ...(section as any), ctaColor: primary } as any) : section;
    })
  );
};

const loadPixels = async () => {
  try {
    const res = await api.get("/pixels/");
    pixels.value = res.data;
  } catch (err) {
    console.error("Erro ao carregar pixels", err);
  }
};

const clone = <T>(val: T): T => {
  try {
    // structuredClone pode não existir em browsers antigos; fallback seguro
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    return typeof structuredClone === "function" ? structuredClone(val) : JSON.parse(JSON.stringify(val));
  } catch {
    return JSON.parse(JSON.stringify(val));
  }
};

const applySectionBackgrounds = (list: PageSection[]): PageSection[] => {
  const applyWhatsAppDefaults = (sections: PageSection[]) => {
    const newAuto = buildWhatsappLink(pageTitle.value);
    const isAutoLink = (link?: string) => {
      if (!link) return true;
      const normalized = link.toLowerCase();
      const candidates = [lastAutoWhatsAppLink.value, "https://wa.me/559999999", "https://wa.me/5599999999"].filter(Boolean) as string[];
      if (candidates.some(c => normalized === c.toLowerCase())) return true;
      return normalized.includes("wa.me") && normalized.includes("interesse");
    };

    const updated = sections.map(section => {
      const type = (section as any).type as SectionType;
      if (!["hero", "story", "cta"].includes(type) || !newAuto) return section;
      if ((section as any).ctaMode === "section") return section;
      if (type === "story" && (section as any).ctaEnabled === false) return section;
      const key = type === "cta" ? "link" : "ctaLink";
      const current = (section as any)[key] as string | undefined;
      if (!current || isAutoLink(current)) {
        return { ...(section as any), [key]: newAuto } as any;
      }
      return section;
    });

    if (newAuto) lastAutoWhatsAppLink.value = newAuto;
    return updated;
  };

  const normalizeHeroGradient = (section: PageSection) => {
    if ((section as any).type !== "hero") return section;
    const current = (section as any).gradientColor as string | undefined;
    const isMissing = !current;
    const isLegacy = current?.toLowerCase?.() === legacyHeroGradient.toLowerCase();
    if (isMissing || isLegacy) {
      return { ...(section as any), gradientColor: heroDefaultGradient } as any;
    }
    return section;
  };

  const ensureButtonColor = (section: PageSection) => {
    const type = (section as any).type as SectionType;
    const typesWithButton: SectionType[] = ["hero", "prices", "testimonials", "story", "cta"];
    if (typesWithButton.includes(type)) {
      const currentColor = (section as any).ctaColor;
      const needsDefault =
        !currentColor || currentColor.toLowerCase() === fallbackPrimaryColor.toLowerCase();
      if (needsDefault) {
        return { ...(section as any), ctaColor: theme.value.ctaDefaultColor } as any;
      }
    }
    return section;
  };

  let altIndex = 0;
  const withWhatsApp = applyWhatsAppDefaults(list || []);
  return withWhatsApp.map(section => {
    if (!section) return section;
    const anchored = ensureSectionAnchor(section);
    const withHeroGradient = normalizeHeroGradient(anchored);
    const withButtonColor = ensureButtonColor(withHeroGradient);
    if (
      (withButtonColor as any).type === "hero" ||
      (withButtonColor as any).type === "countdown" ||
      (withButtonColor as any).type === "free_footer_brand"
    ) {
      return withButtonColor;
    }
    const backgroundColor = altIndex % 2 === 0 ? colorA.value : colorB.value;
    altIndex += 1;
    return { ...(withButtonColor as any), backgroundColor } as any;
  });
};

const buildConfig = (): PageConfig => ({
  version: 1,
  theme: { ...theme.value, color1: colorA.value, color2: colorB.value },
  editor: { ...editorPrefs.value, previewEnabled: previewEnabled.value, previewDevice: previewDevice.value },
  sections: applySectionBackgrounds(sections.value),
  tracking: selectedPixel.value
    ? {
        pixel: pixels.value.find(p => p.name === selectedPixel.value) || null,
        events: { ...trackingEvents.value }
      }
    : undefined
});

const hydratePreviewSections = () => {
  previewSections.value = applySectionBackgrounds(sections.value);
};

let previewFrame: number | null = null;
let previewTimeout: ReturnType<typeof setTimeout> | null = null;
let previewIdle: number | null = null;
const clearPreviewScheduler = () => {
  if (previewFrame !== null) {
    if (hasWindow && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(previewFrame);
    }
    previewFrame = null;
  }
  if (previewIdle !== null) {
    if (hasWindow && typeof (window as any).cancelIdleCallback === "function") {
      (window as any).cancelIdleCallback(previewIdle);
    }
    previewIdle = null;
  }
  if (previewTimeout) {
    clearTimeout(previewTimeout);
    previewTimeout = null;
  }
};

const schedulePreviewHydration = (immediate = false) => {
  if (!previewEnabled.value || !previewReady.value) {
    clearPreviewScheduler();
    return;
  }

  const run = () => {
    clearPreviewScheduler();
    hydratePreviewSections();
  };

  if (immediate) {
    run();
    return;
  }

  if (hasWindow) {
    const idle = (window as any).requestIdleCallback;
    if (typeof idle === "function") {
      previewIdle = idle(run, { timeout: 200 });
      return;
    }
    if (typeof window.requestAnimationFrame === "function") {
      previewFrame = window.requestAnimationFrame(run);
      return;
    }
  }

  previewTimeout = setTimeout(run, 120);
};

onBeforeUnmount(() => {
  clearPreviewScheduler();
});

const gridLayoutClass = computed(() => {
  if (!previewEnabled.value) return "grid-cols-1";
  return "lg:grid-cols-[40%_60%]";
});

function defaultSection(type: SectionType): PageSection {
  if (type === "hero") {
    return ensureSectionAnchor({
      type: "hero",
      enabled: true,
      layout: "immersive",
      title: "Viajar com conforto e segurança nunca foi tão fácil.",
      subtitle: "Conectamos você aos melhores destinos do Brasil com frota premium e atendimento próximo.",
      backgroundImage: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80",
      gradientColor: heroDefaultGradient,
      logoUrl: currentAgency.value?.logo_url || "",
      chips: ["Leito-cama 180º", "Wi-Fi a bordo", "Tomadas individuais", "Massagem a bordo"],
      ctaLabel: "Quero falar no WhatsApp",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaColor: theme.value.ctaDefaultColor,
      ctaMode: "link",
      ctaSectionId: null
    } as HeroSection);
  }

  if (type === "prices") {
    return ensureSectionAnchor({
      type: "prices",
      enabled: true,
      layout: "cards",
      items: [{ title: "Apartamento duplo", price: 3490, description: "Por pessoa" }],
      ctaColor: theme.value.ctaDefaultColor
    } as PricesSection);
  }

  if (type === "itinerary") {
    return ensureSectionAnchor({
      type: "itinerary",
      enabled: true,
      layout: "timeline",
      days: [
        { day: "Dia 1", title: "Chegada", description: "Recepção no aeroporto e traslado." },
        { day: "Dia 2", title: "Trilhas", description: "Passeio pelas dunas e cachoeiras." }
      ]
    } as ItinerarySection);
  }

  if (type === "faq") {
    return ensureSectionAnchor({
      type: "faq",
      enabled: true,
      layout: "accordion",
      items: [
        { question: "O que está incluído?", answer: "Hospedagem, transporte interno e passeios." },
        { question: "Como reservar?", answer: "Clique no botão de WhatsApp e fale com a equipe." }
      ]
    } as FaqSection);
  }

  if (type === "testimonials") {
    return ensureSectionAnchor({
      type: "testimonials",
      enabled: true,
      layout: "grid",
      title: "Quem já viajou com a gente",
      subtitle: "Feedbacks reais de clientes",
      items: [{ name: "Mariana", text: "Viagem incrível, super bem organizada!", avatar: "" }],
      cardColor: "#ffffff",
      ctaColor: theme.value.ctaDefaultColor,
      ctaMode: "link",
      ctaSectionId: null
    } as TestimonialsSection);
  }

  if (type === "story") {
    return ensureSectionAnchor({
      type: "story",
      enabled: true,
      layout: "single",
      imagePosition: "right",
      badge: "Sobre nós",
      title: "Conheça nossa história",
      subtitle: "Somos uma equipe apaixonada por criar experiências memoráveis de viagem, com atendimento próximo e cuidadoso.",
      ctaLabel: "Quero saber mais",
      ctaLink: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
      ctaColor: theme.value.ctaDefaultColor,
      ctaEnabled: true,
      ctaMode: "link",
      ctaSectionId: null,
      borderEnabled: false,
      borderColor: "#cbd5e1",
      images: [
        "https://images.unsplash.com/photo-1502920514313-52581002a659?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"
      ]
    } as StorySection);
  }

  if (type === "countdown") {
    return ensureSectionAnchor({
      type: "countdown",
      enabled: true,
      label: "Garanta sua vaga agora mesmo!",
      targetDate: buildCountdownTargetDate(),
      backgroundColor: "#ef4444",
      textColor: "#ffffff",
      layout: "cards"
    } as CountdownSection);
  }

  if (type === "reasons") {
    return ensureSectionAnchor({
      type: "reasons",
      enabled: true,
      title: "Por que escolher a nossa agência?",
      subtitle: "Benefícios claros para ajudar na conversão",
      items: [
        { icon: "coin", title: "Economize dinheiro", description: "Aproveite negociações especiais e otimize seu orçamento." },
        { icon: "compass", title: "Mais liberdade", description: "Planeje quando quiser com apoio de especialistas locais." },
        { icon: "support", title: "Apoio dedicado", description: "Suporte próximo antes, durante e depois da viagem." },
        { icon: "spark", title: "Experiência única", description: "Curadoria de passeios e hospedagens memoráveis." }
      ]
    } as ReasonsSection);
  }

  return ensureSectionAnchor({
    type: "cta",
    enabled: true,
    layout: "simple",
    label: "Quero reservar pelo WhatsApp",
    link: buildWhatsappLink(pageTitle.value) || "https://wa.me/",
    description: "Fale com um especialista agora mesmo.",
    ctaColor: theme.value.ctaDefaultColor,
    textColor: theme.value.ctaTextColor,
    fullWidth: true,
    ctaMode: "link",
    ctaSectionId: null
  } as CtaSection);
}

const hydrateFromConfig = (config?: PageConfig | string | null) => {
  if (!config) return;

  try {
    const parsed = (typeof config === "string" ? JSON.parse(config) : config) as PageConfig;
    const oldDefaultCta = parsed.theme?.ctaDefaultColor;

    if (parsed.theme) {
      theme.value = { ...theme.value, ...parsed.theme };
      colorA.value = parsed.theme.color1 || colorA.value;
      colorB.value = parsed.theme.color2 || colorB.value;
    }

    if (parsed.editor) {
      editorPrefs.value = { ...editorPrefs.value, ...parsed.editor };
      if (typeof (parsed as any).editor?.previewEnabled === "boolean") {
        previewEnabled.value = (parsed as any).editor.previewEnabled;
      }
      if ((parsed as any).editor?.previewDevice === "mobile" || (parsed as any).editor?.previewDevice === "desktop") {
        previewDevice.value = (parsed as any).editor.previewDevice;
      }
    }

    if (parsed.sections && Array.isArray(parsed.sections) && parsed.sections.length) {
      sections.value = applySectionBackgrounds(parsed.sections as PageSection[]).filter(Boolean);
      fillHeroLogoFromAgency();
    }

    // pixel selecionado e eventos
    const tracking: any = (parsed as any).tracking;
    if (tracking?.pixel?.name) selectedPixel.value = tracking.pixel.name;
    if (tracking?.events) {
      trackingEvents.value = {
        pageView: tracking.events.pageView !== false,
        ctaClicks: tracking.events.ctaClicks !== false
      };
    }

    applyPrimaryToThemeAndSections(oldDefaultCta);
  } catch (err) {
    console.error("Erro ao ler config_json", err);
  }
};

const fetchPage = async () => {
  if (!auth.token) {
    errorMessage.value = "Faça login novamente para editar.";
    return;
  }

  if (!auth.user) {
    try {
      await auth.fetchProfile();
    } catch (err) {
      errorMessage.value = "Sessão expirada. Faça login novamente.";
      return;
    }
  }

  try {
    const res = await api.get<Page>(`/pages/${pageId}`);
    page.value = res.data;
    pageTitle.value = res.data.title;
    pageSlug.value = res.data.slug;

    hydrateFromConfig(res.data.config_json);

    message.value = "";
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possível carregar a página.";
  }
};

const saveConfig = async () => {
  if (!auth.token) {
    errorMessage.value = "Sessão expirada. Faça login novamente.";
    return;
  }

  errorMessage.value = "";
  message.value = "";

  try {
    await api.put(`/pages/${pageId}`, { title: pageTitle.value, slug: pageSlug.value });

    const configPayload = buildConfig();
    await api.put(`/pages/${pageId}/config`, { config: configPayload });

    message.value = "Configuração salva!";
    showSnackbar("Configuração salva");
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = "Erro ao salvar configuração.";
    }
  }
};

const publishPage = async () => {
  if (!auth.token) {
    errorMessage.value = "Sessão expirada. Faça login novamente.";
    return;
  }

  errorMessage.value = "";
  message.value = "";

  try {
    await saveConfig();
    const res = await api.post(`/pages/${pageId}/publish`, { publish: true });
    page.value = res.data;

    message.value = "Página publicada!";
    successModal.value.open = true;
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;

    if (detail) {
      limitModal.value = { open: true, message: String(detail) };
    } else {
      errorMessage.value = "Erro ao publicar. Verifique se está logado e tem acesso à agência.";
    }
  }
};

const goBack = () => {
  router.back();
};

const goPlans = () => {
  router.push({ name: "plans" });
};

const addSection = (type: SectionType) => {
  const next = clone(defaultSection(type));
  sections.value.push(next);
};

watch(pageTitle, () => {
  sections.value = applySectionBackgrounds(sections.value);
});

const duplicateSection = (index: number) => {
  const copy = cloneWithNewAnchor(clone(sections.value[index]));
  sections.value.splice(index + 1, 0, copy);
};

const removeSection = (index: number) => {
  // Permite remover hero apenas se houver mais de um
  if ((sections.value[index] as any)?.type === "hero") {
    const heroCount = sections.value.filter(s => (s as any).type === "hero").length;
    if (heroCount <= 1) return;
  }
  sections.value.splice(index, 1);
};

const moveSection = (index: number, direction: number) => {
  const target = index + direction;
  if (target < 0 || target >= sections.value.length) return;

  const list = [...sections.value];
  const temp = list[index];
  list[index] = list[target];
  list[target] = temp;

  sections.value = list;
};

const isCollapsed = (index: number) => !!collapsed.value[index];
const toggleCollapse = (index: number) => {
  collapsed.value = { ...collapsed.value, [index]: !collapsed.value[index] };
};

watch([colorA, colorB], ([a, b], [_prevA, prevB]) => {
  if (a.toLowerCase() === b.toLowerCase()) {
    colorB.value = prevB || "#ffffff";
  }
});

watch(colorA, value => {
  theme.value.color1 = value;
});

watch(colorB, value => {
  theme.value.color2 = value;
});

watch(
  () => sections.value,
  () => schedulePreviewHydration(),
  { deep: true }
);

watch([colorA, colorB], () => {
  schedulePreviewHydration();
});

watch(previewEnabled, value => {
  editorPrefs.value.previewEnabled = value;
  schedulePreviewHydration(true);
});

watch(previewDevice, value => {
  editorPrefs.value.previewDevice = value;
});

const setDefaultSectionsByPlan = () => {
  const plan = auth.user?.plan || "free";

  if (plan === "free") {
    sections.value = [defaultSection("hero"), defaultSection("story"), defaultSection("itinerary"), defaultSection("cta")];
  } else {
    const storyRight = defaultSection("story") as any;
    storyRight.imagePosition = "right";

    const storyLeft = defaultSection("story") as any;
    storyLeft.imagePosition = "left";

    sections.value = [
      defaultSection("hero"),
      defaultSection("reasons"),
      storyRight,
      storyLeft,
      defaultSection("itinerary"),
      defaultSection("countdown"),
      defaultSection("cta")
    ];
  }
};

const ensureProfile = async () => {
  if (!auth.user) {
    try {
      await auth.fetchProfile();
    } catch {
      /* ignore */
    }
  }
};

const applySavedTemplate = (): boolean => {
  const key = templateKey.value;
  if (!key) return false;

  const storage = getBrowserStorage();
  if (!storage) return false;

  try {
    const saved = storage.getItem(key);
    if (!saved) return false;

    const parsed = JSON.parse(saved);
    const oldDefaultCta = parsed.theme?.ctaDefaultColor;

    if (parsed.theme) {
      theme.value = { ...theme.value, ...parsed.theme };
      if (parsed.theme.color1) colorA.value = parsed.theme.color1;
      if (parsed.theme.color2) colorB.value = parsed.theme.color2;
    }

    if (parsed.sections && Array.isArray(parsed.sections) && parsed.sections.length) {
      sections.value = applySectionBackgrounds(parsed.sections as PageSection[]);
      applyPrimaryToThemeAndSections(oldDefaultCta);
      return true;
    }
  } catch (err) {
    console.error("Erro ao aplicar template salvo", err);
  }

  return false;
};

const showSnackbar = (text: string) => {
  snackbar.value = { open: true, text };
  setTimeout(() => (snackbar.value.open = false), 3000);
};

/**
 * ✅ BLOQUEIO: plano free NÃO pode salvar template.
 * Deve abrir dialog com Fechar / Ver planos.
 */
const saveTemplate = () => {
  // se não logou
  if (!auth.user) {
    errorMessage.value = "Faça login para salvar um template.";
    return;
  }

  // bloqueio do plano free
  const plan = auth.user?.plan || "free";
  if (plan === "free") {
    limitModal.value = {
      open: true,
      message: "Salvar template está disponível apenas a partir do plano Essencial. Atualize seu plano para liberar."
    };
    return;
  }

  const key = templateKey.value;
  if (!key) {
    errorMessage.value = "Faça login para salvar um template.";
    return;
  }

  try {
    const payload = {
      sections: sections.value,
      theme: { ...theme.value, color1: colorA.value, color2: colorB.value }
    };

    const storage = getBrowserStorage();
    if (!storage) {
      errorMessage.value = "Recurso indisponivel no momento.";
      return;
    }

    storage.setItem(key, JSON.stringify(payload));
    message.value = "Template salvo! Novas páginas iniciarão com essa estrutura.";
    showSnackbar("Template salvo com sucesso");
  } catch (err) {
    console.error(err);
    errorMessage.value = "Não foi possível salvar o template.";
  }
};

const ensureAgencies = async () => {
  if (!agencyStore.agencies.length) {
    try {
      await agencyStore.loadAgencies();
    } catch {
      /* ignore */
    }
  }
  applyPrimaryToThemeAndSections();
};

const publicUrl = computed(() => {
  const agencySlug = agencyStore.agencies[0]?.slug;
  const slug = pageSlug.value || page.value?.slug;
  if (!agencySlug || !slug) return null;
  return `/${agencySlug}/${slug}`;
});

const goPages = () => {
  router.push({ name: "pages" });
};

const viewPublicPage = () => {
  if (!publicUrl.value || !hasWindow) return;
  window.open(publicUrl.value, "_blank");
};

onMounted(async () => {
  await ensureProfile();
  await ensureAgencies();
  applyAgencyBranding();
  loadPixels();

  const applied = applySavedTemplate();
  if (!applied) setDefaultSectionsByPlan();

  previewReady.value = true;
  schedulePreviewHydration(true);

  await fetchPage();
  schedulePreviewHydration(true);
});
</script>
