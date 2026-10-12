<template>
  <div class="cv">
    <div class="cv-head">
      <div>
        <router-link :to="{ name: 'page-edit', params: { id } }" class="cv-back"><ArrowLeftIcon aria-hidden="true" /> Voltar para a página</router-link>
        <h1 class="cv-title">Criativos</h1>
        <p class="cv-sub">Artes prontas para divulgar <b>{{ page?.title || "esta viagem" }}</b>: stories, post no feed ou carrossel com todas as informações. Tudo sai com as cores, as fotos e o logo da página.</p>
      </div>
      <div class="cv-actions">
        <button type="button" class="cv-btn cv-btn-primary" :disabled="downloading || loading" @click="download">
          <DownloadIcon aria-hidden="true" /> {{ downloading ? "Gerando…" : mode === "carousel" ? `Baixar carrossel (${activeSlides.length} imagens)` : "Baixar PNG" }}
        </button>
      </div>
    </div>

    <p v-if="error" class="cv-alert">{{ error }}</p>
    <p v-if="loading" class="cv-muted">Carregando a página…</p>

    <template v-else-if="data">
      <div class="cv-bar">
        <div class="cv-formats" role="tablist" aria-label="Tipo">
          <button type="button" role="tab" :aria-selected="mode === 'single'" :class="{ on: mode === 'single' }" @click="mode = 'single'">Arte única</button>
          <button type="button" role="tab" :aria-selected="mode === 'carousel'" :class="{ on: mode === 'carousel' }" @click="mode = 'carousel'">Carrossel</button>
        </div>
        <div class="cv-formats" role="tablist" aria-label="Formato">
          <button
            v-for="key in formats"
            :key="key"
            type="button"
            role="tab"
            :aria-selected="format === key"
            :class="{ on: format === key }"
            @click="format = key"
          >
            {{ FORMAT_SIZES[key].label }} <small>{{ FORMAT_SIZES[key].width }}×{{ FORMAT_SIZES[key].height }}</small>
          </button>
        </div>
      </div>

      <template v-if="mode === 'single'">
        <section v-for="(label, category) in CATEGORY_LABELS" :key="category" class="cv-group">
          <h2>{{ label }}</h2>
          <div class="cv-gallery">
            <button
              v-for="item in templatesBy(category)"
              :key="item.id"
              type="button"
              class="cv-thumb"
              :class="{ on: template === item.id }"
              :title="item.description"
              @click="template = item.id"
            >
              <span class="cv-thumb-stage" :style="stageStyle(thumbWidth)">
                <CreativeArtboard :template="item.id" :format="format" :data="data" :photos="previewPhotos" :show-logo="showLogo" :style="scaleStyle(thumbWidth)" />
              </span>
              <span class="cv-thumb-name">{{ item.name }}</span>
              <small>{{ item.photos > 1 ? `${item.photos} fotos` : "1 foto" }}</small>
            </button>
          </div>
        </section>
      </template>

      <div class="cv-work" :class="{ 'is-carousel': mode === 'carousel' }">
        <div v-if="mode === 'single'" class="cv-preview">
          <div ref="previewBox" class="cv-preview-stage" :style="stageStyle(previewWidth)">
            <CreativeArtboard :template="template" :format="format" :data="data" :photos="previewPhotos" :show-logo="showLogo" :style="scaleStyle(previewWidth)" />
          </div>
          <p class="cv-muted">{{ currentTemplate?.description }}</p>
        </div>

        <div v-else class="cv-slides">
          <p class="cv-muted">
            {{ activeSlides.length }} slides montados com as informações da página. Desmarque o que não quiser postar; cada slide usa a próxima foto escolhida.
          </p>
          <div class="cv-slide-grid">
            <div v-for="(item, index) in slides" :key="item.key" class="cv-slide" :class="{ off: excluded.includes(item.key) }">
              <span class="cv-thumb-stage" :style="stageStyle(slideWidth)">
                <CreativeCarouselSlide
                  :slide="item.slide"
                  :format="format"
                  :data="data"
                  :photo="photoFor(activeIndex(index), previewPhotos)"
                  :index="activeIndex(index)"
                  :total="activeSlides.length"
                  :show-logo="showLogo"
                  :style="scaleStyle(slideWidth)"
                />
              </span>
              <label class="cv-check">
                <input type="checkbox" :checked="!excluded.includes(item.key)" :disabled="item.slide.kind === 'cover'" @change="toggleSlide(item.key)" />
                <span>{{ slideLabel(item.slide) }}</span>
              </label>
            </div>
          </div>
        </div>

        <div class="cv-panel">
          <h3>Fotos <small>{{ photoHint }}</small></h3>
          <p class="cv-muted">Clique para escolher a ordem. A primeira é a principal.</p>
          <div class="cv-photos">
            <button
              v-for="photo in photos"
              :key="photo.src"
              type="button"
              class="cv-photo"
              :class="{ on: chosen.includes(photo.src), failed: photo.status === 'failed' }"
              :title="photo.status === 'failed' ? 'Não conseguimos preparar essa foto para o download.' : ''"
              @click="toggle(photo.src)"
            >
              <img :src="photo.ready || photo.src" alt="" loading="lazy" />
              <b v-if="chosen.includes(photo.src)">{{ chosen.indexOf(photo.src) + 1 }}</b>
              <i v-if="photo.status === 'loading'" class="cv-spin"></i>
            </button>
            <label class="cv-photo cv-upload">
              <UploadIcon aria-hidden="true" />
              <span>Enviar imagem</span>
              <input type="file" accept="image/*" multiple @change="onUpload" />
            </label>
          </div>
          <p v-if="!photos.length" class="cv-muted">A página ainda não tem fotos. Envie uma imagem do seu computador.</p>

          <h3>Textos</h3>
          <label class="cv-field"><span>Título</span><input v-model="data.title" maxlength="90" /></label>
          <label class="cv-field"><span>Subtítulo</span><textarea v-model="data.subtitle" rows="2" maxlength="160"></textarea></label>
          <label class="cv-field"><span>Datas</span><input v-model="data.dates" placeholder="Ex.: 12/07 a 19/07/2026" /></label>
          <div class="cv-row">
            <label class="cv-field"><span>Antes do preço</span><input v-model="data.pricePrefix" placeholder="A partir de" /></label>
            <label class="cv-field"><span>Preço</span><input v-model="data.priceValue" placeholder="R$ 2.990" /></label>
          </div>
          <div class="cv-row">
            <label class="cv-field"><span>Depois do preço</span><input v-model="data.priceSuffix" placeholder="por pessoa" /></label>
            <label class="cv-field"><span>Parcelas</span><input v-model="data.installments" placeholder="em até 10x sem juros" /></label>
          </div>

          <h3>Botão <small>a arte não é clicável; use como chamada</small></h3>
          <label class="cv-switch">
            <input v-model="data.ctaEnabled" type="checkbox" />
            <span>{{ data.ctaEnabled ? "Mostrar botão na arte" : "Sem botão" }}</span>
          </label>
          <template v-if="data.ctaEnabled">
            <label class="cv-field"><span>Texto do botão</span><input v-model="data.cta" maxlength="28" placeholder="Saiba mais" /></label>
            <div class="cv-chips">
              <button v-for="option in CTA_SUGGESTIONS" :key="option" type="button" :class="{ on: data.cta === option }" @click="data.cta = option">{{ option }}</button>
            </div>
          </template>
          <label class="cv-field"><span>WhatsApp (aparece como texto)</span><input v-model="data.contact" placeholder="(11) 99999-0000" /></label>

          <h3>Benefícios <small>até 8</small></h3>
          <div v-for="(_, index) in data.benefits" :key="`b${index}`" class="cv-benefit">
            <input v-model="data.benefits[index]" maxlength="60" />
            <button type="button" class="cv-icon" aria-label="Remover" @click="data.benefits.splice(index, 1)"><XIcon aria-hidden="true" /></button>
          </div>
          <button v-if="data.benefits.length < 8" type="button" class="cv-btn cv-btn-ghost" @click="data.benefits.push('')"><PlusIcon aria-hidden="true" /> Adicionar benefício</button>

          <template v-if="mode === 'carousel'">
            <h3>Roteiro <small>{{ data.itinerary.length }} dias</small></h3>
            <div v-for="(day, index) in data.itinerary" :key="`d${index}`" class="cv-item">
              <div class="cv-item-head">
                <b>{{ index + 1 }}</b>
                <input v-model="day.title" maxlength="70" placeholder="Título do dia" />
                <button type="button" class="cv-icon" aria-label="Remover dia" @click="data.itinerary.splice(index, 1)"><XIcon aria-hidden="true" /></button>
              </div>
              <textarea v-model="day.description" rows="2" maxlength="140" placeholder="Resumo do dia"></textarea>
            </div>
            <button type="button" class="cv-btn cv-btn-ghost" @click="data.itinerary.push({ day: '', title: '', description: '' })"><PlusIcon aria-hidden="true" /> Adicionar dia</button>

            <h3>Valores</h3>
            <div v-for="(item, index) in data.prices" :key="`p${index}`" class="cv-item">
              <div class="cv-item-head">
                <input v-model="item.title" maxlength="50" placeholder="Ex.: Quarto duplo" />
                <input v-model="item.value" class="cv-short" maxlength="20" placeholder="R$ 2.990" />
                <button type="button" class="cv-icon" aria-label="Remover valor" @click="data.prices.splice(index, 1)"><XIcon aria-hidden="true" /></button>
              </div>
              <input v-model="item.note" maxlength="90" placeholder="Observação (opcional)" />
            </div>
            <button type="button" class="cv-btn cv-btn-ghost" @click="data.prices.push({ title: '', prefix: '', value: '', note: '' })"><PlusIcon aria-hidden="true" /> Adicionar valor</button>

            <h3>Voos</h3>
            <div v-for="(flight, index) in data.flights" :key="`f${index}`" class="cv-item">
              <div class="cv-item-head">
                <input v-model="flight.label" class="cv-short" maxlength="20" placeholder="Ida" />
                <input v-model="flight.date" class="cv-short" maxlength="12" placeholder="12/07" />
                <button type="button" class="cv-icon" aria-label="Remover voo" @click="data.flights.splice(index, 1)"><XIcon aria-hidden="true" /></button>
              </div>
              <input v-model="flight.route" maxlength="80" placeholder="São Paulo (GRU) → Recife (REC)" />
              <input v-model="flight.details" maxlength="80" placeholder="LATAM · Voo direto" />
            </div>
            <button type="button" class="cv-btn cv-btn-ghost" @click="data.flights.push({ label: 'Ida', date: '', route: '', times: '', details: '' })"><PlusIcon aria-hidden="true" /> Adicionar voo</button>
          </template>

          <h3>Cores e logo</h3>
          <div class="cv-row">
            <label class="cv-color"><input v-model="data.primary" type="color" /><span>Principal</span></label>
            <label class="cv-color"><input v-model="data.secondary" type="color" /><span>Destaque</span></label>
          </div>
          <label class="cv-check" :class="{ disabled: !data.logoUrl }">
            <input v-model="showLogo" type="checkbox" :disabled="!data.logoUrl" />
            <span>{{ data.logoUrl ? "Mostrar o logo" : "A página não tem logo" }}</span>
          </label>
          <button type="button" class="cv-btn cv-btn-ghost" @click="resetData"><RotateCcwIcon aria-hidden="true" /> Voltar aos dados da página</button>
        </div>
      </div>

      <!-- Cópia em tamanho real, fora da tela, usada só para gerar o PNG. -->
      <div class="cv-offscreen" aria-hidden="true">
        <div ref="exportRef">
          <CreativeArtboard v-if="mode === 'single'" :template="template" :format="format" :data="exportData" :photos="exportPhotos" :show-logo="showLogo" />
          <template v-else>
            <CreativeCarouselSlide
              v-for="(item, index) in activeSlides"
              :key="item.key"
              :slide="item.slide"
              :format="format"
              :data="exportData"
              :photo="photoFor(index, exportPhotos)"
              :index="index"
              :total="activeSlides.length"
              :show-logo="showLogo"
            />
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/** Criativos/flyers a partir da viagem: modelos prontos com a capa, logo, benefícios, preço e cores da página. */
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ArrowLeftIcon, DownloadIcon, PlusIcon, RotateCcwIcon, UploadIcon, XIcon } from "lucide-vue-next";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import type { PageConfig } from "../../types/page";
import CreativeArtboard from "../../components/creatives/CreativeArtboard.vue";
import CreativeCarouselSlide from "../../components/creatives/CreativeCarouselSlide.vue";
import { CTA_SUGGESTIONS, FORMAT_SIZES, extractCreativeData, type CreativeData, type CreativeFormat } from "../../components/creatives/creativeData";
import { SLIDE_LABELS, buildCarousel, type CarouselSlide } from "../../components/creatives/carousel";
import { CATEGORY_LABELS, CREATIVE_TEMPLATES, type CreativeCategory } from "../../components/creatives/creativeTemplates";

const props = defineProps<{ id: string }>();

interface PagePayload {
  id: number;
  agency_id: number;
  title: string;
  slug: string;
  config_json: PageConfig;
}
interface Photo {
  src: string;
  ready: string;
  status: "loading" | "ready" | "failed";
}

const agencyStore = useAgencyStore();
const page = ref<PagePayload | null>(null);
const data = ref<CreativeData | null>(null);
const loading = ref(true);
const error = ref("");
const downloading = ref(false);
const mode = ref<"single" | "carousel">("single");
const format = ref<CreativeFormat>("feed");
const excluded = ref<string[]>([]);
const template = ref(CREATIVE_TEMPLATES[0].id);
const showLogo = ref(true);
const photos = ref<Photo[]>([]);
const chosen = ref<string[]>([]);
const logoReady = ref("");
const exportRef = ref<HTMLElement | null>(null);
const previewBox = ref<HTMLElement | null>(null);
const previewWidth = ref(420);
const thumbWidth = 150;
const slideWidth = 220;
const objectUrls: string[] = [];

// Carrossel: só Stories e Feed (o Instagram corta o carrossel quadrado do mesmo jeito que o 4:5).
const formats = computed<CreativeFormat[]>(() => (mode.value === "carousel" ? ["story", "feed"] : ["story", "feed", "square"]));
watch(mode, value => {
  if (value === "carousel" && format.value === "square") format.value = "feed";
});

const slides = computed(() => {
  if (!data.value) return [];
  const counts: Record<string, number> = {};
  return buildCarousel(data.value, format.value).map(slide => {
    counts[slide.kind] = (counts[slide.kind] || 0) + 1;
    return { slide, key: `${slide.kind}-${counts[slide.kind]}` };
  });
});
const activeSlides = computed(() => slides.value.filter(item => !excluded.value.includes(item.key)));
const activeIndex = (index: number) => {
  const key = slides.value[index]?.key;
  const position = activeSlides.value.findIndex(item => item.key === key);
  return position >= 0 ? position : index;
};
const toggleSlide = (key: string) => {
  excluded.value = excluded.value.includes(key) ? excluded.value.filter(item => item !== key) : [...excluded.value, key];
};
const slideLabel = (slide: CarouselSlide) =>
  slide.kind === "itinerary" && slide.parts > 1 ? `${SLIDE_LABELS.itinerary} ${slide.part}/${slide.parts}` : SLIDE_LABELS[slide.kind];
/** Cada slide usa a próxima foto escolhida (e recomeça quando acabam). */
const photoFor = (index: number, list: string[]) => (list.length ? list[index % list.length] : "");
const photoHint = computed(() => {
  if (mode.value === "carousel") return "uma por slide, na ordem";
  const count = currentTemplate.value?.photos || 1;
  return count > 1 ? `este modelo usa ${count}` : "este modelo usa 1";
});

const currentTemplate = computed(() => CREATIVE_TEMPLATES.find(item => item.id === template.value));
const templatesBy = (category: string) => CREATIVE_TEMPLATES.filter(item => item.category === (category as CreativeCategory));

const ordered = computed(() => {
  const picked = chosen.value.map(src => photos.value.find(photo => photo.src === src)).filter(Boolean) as Photo[];
  if (picked.length) return picked;
  // Sem escolha: arte única usa a capa; o carrossel passa por todas as fotos da página.
  return mode.value === "carousel" ? photos.value.filter(photo => photo.status !== "failed") : photos.value.slice(0, 1);
});
const previewPhotos = computed(() => ordered.value.map(photo => photo.ready || photo.src));
const exportPhotos = computed(() => ordered.value.map(photo => photo.ready).filter(Boolean));
const exportData = computed<CreativeData>(() => ({ ...(data.value as CreativeData), logoUrl: logoReady.value }));

const stageStyle = (width: number) => {
  const size = FORMAT_SIZES[format.value];
  return { width: `${width}px`, height: `${Math.round((width * size.height) / size.width)}px` };
};
const scaleStyle = (width: number) => ({ transform: `scale(${width / 1080})`, transformOrigin: "top left" });

const toggle = (src: string) => {
  const index = chosen.value.indexOf(src);
  if (index >= 0) chosen.value.splice(index, 1);
  else chosen.value.push(src);
};

/** Foto em endereço local (blob) para o PNG não sair sem ela por bloqueio de CORS do banco de imagens. */
const prepare = async (src: string): Promise<string> => {
  try {
    const response = await api.get(`/pages/${props.id}/creative-image`, { params: { url: src }, responseType: "blob" });
    if (response.data instanceof Blob && response.data.size) return keep(URL.createObjectURL(response.data));
  } catch {
    // tenta direto abaixo
  }
  try {
    const response = await fetch(src, { mode: "cors" });
    if (response.ok) return keep(URL.createObjectURL(await response.blob()));
  } catch {
    // sem CORS
  }
  return "";
};
const keep = (url: string) => {
  objectUrls.push(url);
  return url;
};

const loadPhotos = (images: string[]) => {
  photos.value = images.map(src => ({ src, ready: "", status: "loading" }));
  images.forEach(async src => {
    const ready = await prepare(src);
    const photo = photos.value.find(item => item.src === src);
    if (photo) Object.assign(photo, { ready, status: ready ? "ready" : "failed" });
  });
};

const onUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files || []).filter(file => file.type.startsWith("image/"));
  const added = files.map(file => {
    const url = keep(URL.createObjectURL(file));
    return { src: url, ready: url, status: "ready" as const };
  });
  photos.value = [...added, ...photos.value];
  chosen.value = [...added.map(photo => photo.src), ...chosen.value];
  input.value = "";
};

const resetData = () => {
  const agency = agencyStore.agencies.find(item => item.id === page.value?.agency_id) || null;
  data.value = extractCreativeData(page.value?.config_json || null, page.value, agency);
};

const load = async () => {
  loading.value = true;
  error.value = "";
  try {
    if (!agencyStore.agencies.length) await agencyStore.loadAgencies().catch(() => undefined);
    page.value = (await api.get<PagePayload>(`/pages/${props.id}`)).data;
    resetData();
    loadPhotos(data.value?.images || []);
    if (data.value?.logoUrl) logoReady.value = await prepare(data.value.logoUrl);
  } catch {
    error.value = "Não conseguimos carregar esta página.";
  } finally {
    loading.value = false;
  }
};

const toPngOf = async (node: HTMLElement) => {
  const { toPng } = await import("html-to-image");
  const size = FORMAT_SIZES[format.value];
  return toPng(node, { width: size.width, height: size.height, pixelRatio: 1, cacheBust: false });
};

const save = (href: string, name: string) => {
  const link = document.createElement("a");
  link.download = name;
  link.href = href;
  link.click();
};

const download = async () => {
  if (!exportRef.value || !data.value) return;
  error.value = "";
  const needed = mode.value === "carousel" ? Math.min(activeSlides.value.length, ordered.value.length) : Math.max(1, currentTemplate.value?.photos || 1);
  const missing = ordered.value.slice(0, needed).some(photo => !photo.ready);
  if (missing) {
    error.value = ordered.value.some(photo => photo.status === "loading")
      ? "As fotos ainda estão sendo preparadas. Tente de novo em alguns segundos."
      : "Uma das fotos escolhidas não pôde ser preparada para o download. Escolha outra ou envie a imagem do seu computador.";
    return;
  }
  downloading.value = true;
  const slug = page.value?.slug || "criativo";
  try {
    await document.fonts?.ready;
    const nodes = Array.from(exportRef.value.children) as HTMLElement[];
    if (mode.value === "single") {
      save(await toPngOf(nodes[0]), `${slug}-${template.value}-${format.value}.png`);
      return;
    }
    const { default: JSZip } = await import("jszip");
    const zip = new JSZip();
    for (const [index, node] of nodes.entries()) {
      const png = await toPngOf(node);
      zip.file(`${String(index + 1).padStart(2, "0")}-${slug}.png`, png.split(",")[1], { base64: true });
    }
    const blob = await zip.generateAsync({ type: "blob" });
    const url = URL.createObjectURL(blob);
    save(url, `${slug}-carrossel-${format.value}.zip`);
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  } catch {
    error.value = "Não foi possível gerar as imagens. Tente de novo.";
  } finally {
    downloading.value = false;
  }
};

let observer: ResizeObserver | null = null;
const measure = () => {
  const box = previewBox.value?.parentElement;
  if (!box) return;
  const style = getComputedStyle(box);
  const inner = box.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  // Stories é alto: limita pela altura para caber na tela.
  const size = FORMAT_SIZES[format.value];
  const byHeight = (680 * size.width) / size.height;
  previewWidth.value = Math.round(Math.max(200, Math.min(520, inner, byHeight)));
};
watch([format, mode], () => setTimeout(measure));
watch(previewBox, element => {
  observer?.disconnect();
  if (element?.parentElement) {
    observer = new ResizeObserver(measure);
    observer.observe(element.parentElement);
    measure();
  }
});

onMounted(load);
onBeforeUnmount(() => {
  observer?.disconnect();
  objectUrls.forEach(url => URL.revokeObjectURL(url));
});
</script>

<style scoped>
.cv { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.cv > * { min-width: 0; }
.cv-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
.cv-back { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: hsl(var(--muted-foreground)); text-decoration: none; }
.cv-back:hover { color: hsl(var(--foreground)); }
.cv-back svg { width: 15px; height: 15px; }
.cv-title { font-family: var(--font-display); font-size: 26px; font-weight: 700; margin: 6px 0 4px; }
.cv-sub, .cv-muted { color: hsl(var(--muted-foreground)); font-size: 14px; margin: 0; }
.cv-alert { padding: 10px 14px; border-radius: 10px; background: hsl(var(--destructive) / 0.1); color: hsl(var(--destructive)); font-size: 14px; margin: 0; }
.cv-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border-radius: 10px; padding: 10px 16px; font-size: 14px; font-weight: 600; border: 1px solid transparent; cursor: pointer; }
.cv-btn svg { width: 16px; height: 16px; }
.cv-btn:disabled { opacity: 0.6; cursor: default; }
.cv-btn-primary { background: hsl(var(--primary)); color: hsl(var(--primary-foreground)); }
.cv-btn-ghost { background: transparent; border-color: hsl(var(--border)); color: hsl(var(--foreground)); align-self: flex-start; }

.cv-bar { display: flex; flex-wrap: wrap; gap: 12px; }
.cv-formats { display: inline-flex; gap: 4px; padding: 4px; border-radius: 12px; background: hsl(var(--muted)); align-self: flex-start; flex-wrap: wrap; }
.cv-formats button { border: 0; background: transparent; padding: 8px 14px; border-radius: 9px; font-size: 14px; font-weight: 600; color: hsl(var(--muted-foreground)); cursor: pointer; }
.cv-formats button small { font-weight: 500; opacity: 0.7; margin-left: 4px; }
.cv-formats button.on { background: hsl(var(--card)); color: hsl(var(--foreground)); box-shadow: 0 1px 3px rgb(0 0 0 / 0.08); }

.cv-group h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em; color: hsl(var(--muted-foreground)); margin: 0 0 10px; font-weight: 700; }
.cv-gallery { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 6px; }
.cv-thumb { flex: 0 0 auto; display: flex; flex-direction: column; gap: 4px; padding: 8px; border-radius: 14px; border: 2px solid hsl(var(--border)); background: hsl(var(--card)); cursor: pointer; text-align: left; }
.cv-thumb.on { border-color: hsl(var(--primary)); }
.cv-thumb-stage, .cv-preview-stage { display: block; position: relative; overflow: hidden; border-radius: 8px; background: hsl(var(--muted)); }
.cv-thumb-stage > :deep(*), .cv-preview-stage > :deep(*) { position: absolute; top: 0; left: 0; }
.cv-thumb-name { font-size: 13px; font-weight: 600; color: hsl(var(--foreground)); }
.cv-thumb small { font-size: 12px; color: hsl(var(--muted-foreground)); }

.cv-work { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 420px); gap: 24px; align-items: start; }
.cv-preview { display: flex; flex-direction: column; align-items: center; gap: 10px; position: sticky; top: 16px; padding: 20px; border-radius: 16px; background: hsl(var(--muted) / 0.6); }
.cv-preview-stage { box-shadow: 0 12px 40px rgb(0 0 0 / 0.15); }
.cv-panel { display: flex; flex-direction: column; gap: 10px; padding: 20px; border-radius: 16px; border: 1px solid hsl(var(--border)); background: hsl(var(--card)); }
.cv-panel h3 { font-size: 15px; font-weight: 700; margin: 10px 0 0; display: flex; gap: 8px; align-items: baseline; }
.cv-panel h3:first-child { margin-top: 0; }
.cv-panel h3 small { font-size: 12px; font-weight: 500; color: hsl(var(--muted-foreground)); }
.cv-photos { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.cv-photo { position: relative; aspect-ratio: 1; border-radius: 10px; overflow: hidden; border: 2px solid transparent; padding: 0; background: hsl(var(--muted)); cursor: pointer; }
.cv-photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cv-photo.on { border-color: hsl(var(--primary)); }
.cv-photo.failed img { opacity: 0.45; }
.cv-photo b { position: absolute; top: 4px; left: 4px; min-width: 22px; height: 22px; border-radius: 999px; background: hsl(var(--primary)); color: hsl(var(--primary-foreground)); font-size: 12px; display: grid; place-items: center; }
.cv-spin { position: absolute; right: 6px; bottom: 6px; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #fff; border-top-color: transparent; animation: cv-spin 0.8s linear infinite; }
@keyframes cv-spin { to { transform: rotate(360deg); } }
.cv-upload { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border: 2px dashed hsl(var(--border)); font-size: 11px; font-weight: 600; color: hsl(var(--muted-foreground)); text-align: center; }
.cv-upload svg { width: 18px; height: 18px; }
.cv-upload input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.cv-field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 600; flex: 1; min-width: 0; }
.cv-field input, .cv-field textarea, .cv-benefit input { width: 100%; border: 1px solid hsl(var(--border)); border-radius: 9px; padding: 8px 10px; font: inherit; font-weight: 400; font-size: 14px; background: hsl(var(--background)); color: hsl(var(--foreground)); }
.cv-row { display: flex; gap: 10px; }
.cv-benefit { display: flex; gap: 6px; align-items: center; }
.cv-icon { border: 0; background: transparent; color: hsl(var(--muted-foreground)); cursor: pointer; padding: 6px; }
.cv-icon svg { width: 16px; height: 16px; }
.cv-color { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; flex: 1; }
.cv-color input { width: 40px; height: 34px; border: 1px solid hsl(var(--border)); border-radius: 8px; padding: 2px; background: transparent; }
.cv-check { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.cv-check.disabled { color: hsl(var(--muted-foreground)); }
.cv-work.is-carousel { grid-template-columns: minmax(0, 1fr) minmax(0, 400px); }
.cv-slides { display: flex; flex-direction: column; gap: 12px; }
.cv-slide-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; justify-items: start; }
.cv-slide { display: flex; flex-direction: column; gap: 8px; }
.cv-slide .cv-thumb-stage { box-shadow: 0 6px 20px rgb(0 0 0 / 0.12); }
.cv-slide.off .cv-thumb-stage { opacity: 0.35; }
.cv-switch { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 600; }
.cv-switch input { width: 18px; height: 18px; accent-color: hsl(var(--primary)); }
.cv-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.cv-chips button { border: 1px solid hsl(var(--border)); background: hsl(var(--background)); border-radius: 999px; padding: 6px 12px; font-size: 13px; cursor: pointer; color: hsl(var(--foreground)); }
.cv-chips button.on { border-color: hsl(var(--primary)); background: hsl(var(--primary) / 0.1); }
.cv-item { display: flex; flex-direction: column; gap: 6px; padding: 10px; border: 1px solid hsl(var(--border)); border-radius: 12px; }
.cv-item-head { display: flex; align-items: center; gap: 6px; }
.cv-item-head b { flex: none; width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-size: 12px; background: hsl(var(--muted)); }
.cv-item input, .cv-item textarea { width: 100%; min-width: 0; border: 1px solid hsl(var(--border)); border-radius: 9px; padding: 7px 10px; font: inherit; font-size: 14px; background: hsl(var(--background)); color: hsl(var(--foreground)); }
.cv-item .cv-short { flex: 0 0 34%; }
.cv-offscreen { position: fixed; left: -20000px; top: 0; pointer-events: none; }

@media (max-width: 900px) {
  .cv-work, .cv-work.is-carousel { grid-template-columns: minmax(0, 1fr); }
  .cv-slide-grid { grid-template-columns: minmax(0, 1fr); justify-items: center; }
  .cv-preview { position: static; padding: 12px; }
  .cv-photos { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .cv-row { flex-direction: column; }
}
</style>
