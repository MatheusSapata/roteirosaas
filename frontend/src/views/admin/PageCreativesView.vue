<template>
  <div class="cv">
    <div class="cv-head">
      <div>
        <router-link :to="{ name: 'page-edit', params: { id } }" class="cv-back"><ArrowLeftIcon aria-hidden="true" /> Voltar para a página</router-link>
        <h1 class="cv-title">Criativos</h1>
        <p class="cv-sub">Artes prontas para divulgar <b>{{ page?.title || "esta viagem" }}</b> no Instagram, WhatsApp e Facebook. Tudo sai com as cores, a foto e o logo da página.</p>
      </div>
      <div class="cv-actions">
        <button type="button" class="cv-btn cv-btn-primary" :disabled="downloading || loading" @click="download">
          <DownloadIcon aria-hidden="true" /> {{ downloading ? "Gerando…" : "Baixar PNG" }}
        </button>
      </div>
    </div>

    <p v-if="error" class="cv-alert">{{ error }}</p>
    <p v-if="loading" class="cv-muted">Carregando a página…</p>

    <template v-else-if="data">
      <div class="cv-formats" role="tablist" aria-label="Formato">
        <button
          v-for="(info, key) in FORMAT_SIZES"
          :key="key"
          type="button"
          role="tab"
          :aria-selected="format === key"
          :class="{ on: format === key }"
          @click="format = key"
        >
          {{ info.label }} <small>{{ info.width }}×{{ info.height }}</small>
        </button>
      </div>

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

      <div class="cv-work">
        <div class="cv-preview">
          <div ref="previewBox" class="cv-preview-stage" :style="stageStyle(previewWidth)">
            <CreativeArtboard :template="template" :format="format" :data="data" :photos="previewPhotos" :show-logo="showLogo" :style="scaleStyle(previewWidth)" />
          </div>
          <p class="cv-muted">{{ currentTemplate?.description }}</p>
        </div>

        <div class="cv-panel">
          <h3>Fotos <small>{{ currentTemplate && currentTemplate.photos > 1 ? `este modelo usa ${currentTemplate.photos}` : "este modelo usa 1" }}</small></h3>
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

          <h3>Benefícios <small>até 6</small></h3>
          <div v-for="(_, index) in data.benefits" :key="index" class="cv-benefit">
            <input v-model="data.benefits[index]" maxlength="60" />
            <button type="button" class="cv-icon" aria-label="Remover" @click="data.benefits.splice(index, 1)"><XIcon aria-hidden="true" /></button>
          </div>
          <button v-if="data.benefits.length < 6" type="button" class="cv-btn cv-btn-ghost" @click="data.benefits.push('')"><PlusIcon aria-hidden="true" /> Adicionar benefício</button>

          <h3>Chamada</h3>
          <div class="cv-row">
            <label class="cv-field"><span>Botão</span><input v-model="data.cta" maxlength="40" /></label>
            <label class="cv-field"><span>Contato</span><input v-model="data.contact" placeholder="(11) 99999-0000" /></label>
          </div>

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
          <CreativeArtboard :template="template" :format="format" :data="exportData" :photos="exportPhotos" :show-logo="showLogo" />
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
import { FORMAT_SIZES, extractCreativeData, type CreativeData, type CreativeFormat } from "../../components/creatives/creativeData";
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
const format = ref<CreativeFormat>("feed");
const template = ref(CREATIVE_TEMPLATES[0].id);
const showLogo = ref(true);
const photos = ref<Photo[]>([]);
const chosen = ref<string[]>([]);
const logoReady = ref("");
const exportRef = ref<HTMLElement | null>(null);
const previewBox = ref<HTMLElement | null>(null);
const previewWidth = ref(420);
const thumbWidth = 150;
const objectUrls: string[] = [];

const currentTemplate = computed(() => CREATIVE_TEMPLATES.find(item => item.id === template.value));
const templatesBy = (category: string) => CREATIVE_TEMPLATES.filter(item => item.category === (category as CreativeCategory));

const ordered = computed(() => {
  const picked = chosen.value.map(src => photos.value.find(photo => photo.src === src)).filter(Boolean) as Photo[];
  return picked.length ? picked : photos.value.slice(0, 1);
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

const download = async () => {
  if (!exportRef.value || !data.value) return;
  error.value = "";
  const needed = Math.max(1, currentTemplate.value?.photos || 1);
  const missing = ordered.value.slice(0, needed).some(photo => !photo.ready);
  if (missing) {
    error.value = ordered.value.some(photo => photo.status === "loading")
      ? "As fotos ainda estão sendo preparadas. Tente de novo em alguns segundos."
      : "Uma das fotos escolhidas não pôde ser preparada para o download. Escolha outra ou envie a imagem do seu computador.";
    return;
  }
  downloading.value = true;
  try {
    const { toPng } = await import("html-to-image");
    const size = FORMAT_SIZES[format.value];
    const node = exportRef.value.firstElementChild as HTMLElement;
    await document.fonts?.ready;
    const png = await toPng(node, { width: size.width, height: size.height, pixelRatio: 1, cacheBust: false });
    const link = document.createElement("a");
    const slug = page.value?.slug || "criativo";
    link.download = `${slug}-${template.value}-${format.value}.png`;
    link.href = png;
    link.click();
  } catch {
    error.value = "Não foi possível gerar a imagem. Tente de novo.";
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
watch(format, measure);
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
.cv-offscreen { position: fixed; left: -20000px; top: 0; pointer-events: none; }

@media (max-width: 900px) {
  .cv-work { grid-template-columns: minmax(0, 1fr); }
  .cv-preview { position: static; padding: 12px; }
  .cv-photos { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .cv-row { flex-direction: column; }
}
</style>
