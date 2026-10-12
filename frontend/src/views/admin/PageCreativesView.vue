<template>
  <div class="cv">
    <div class="cv-head">
      <router-link :to="{ name: 'page-edit', params: { id } }" class="ed-icon-btn cv-back" aria-label="Voltar para a página" title="Voltar para a página">
        <ChevronLeftIcon aria-hidden="true" />
      </router-link>
      <div class="cv-head-text">
        <p class="cv-crumb">Páginas · {{ page?.title || "Viagem" }}</p>
        <div class="cv-title-row">
          <h1 class="cv-title">Criativos</h1>
          <span class="cv-beta">Beta</span>
        </div>
      </div>
      <button type="button" class="ed-btn ed-btn-primary cv-download" :disabled="downloading || loading || !data" @click="download">
        <DownloadIcon aria-hidden="true" />
        {{ downloadLabel }}
      </button>
    </div>

    <p v-if="error" class="cv-alert">{{ error }}</p>

    <div v-if="loading" class="cv-shell cv-loading">Carregando a página…</div>

    <div v-else-if="data" class="cv-shell">
      <!-- Passo a passo -->
      <aside class="cv-steps ved">
        <section v-for="(step, index) in steps" :key="step.id" class="cv-step" :class="{ open: openStep === step.id, done: index < stepIndex }">
          <button type="button" class="cv-step-head" :aria-expanded="openStep === step.id" @click="openStep = openStep === step.id ? '' : step.id">
            <span class="cv-step-num">
              <CheckIcon v-if="index < stepIndex && openStep !== step.id" aria-hidden="true" />
              <template v-else>{{ index + 1 }}</template>
            </span>
            <span class="cv-step-text">
              <b>{{ step.title }}</b>
              <small>{{ step.summary }}</small>
            </span>
            <ChevronDownIcon class="cv-step-chev" aria-hidden="true" />
          </button>

          <div v-if="openStep === step.id" class="cv-step-body">
            <!-- 1. O que criar -->
            <template v-if="step.id === 'kind'">
              <div class="cv-kinds">
                <button v-for="option in KINDS" :key="option.id" type="button" class="cv-kind" :class="{ on: kind === option.id }" @click="chooseKind(option.id)">
                  <span class="cv-kind-shape" :class="`is-${option.id}`" aria-hidden="true"><i></i><i v-if="option.id === 'carousel'"></i><i v-if="option.id === 'carousel'"></i></span>
                  <b>{{ option.name }}</b>
                  <small>{{ option.hint }}</small>
                </button>
              </div>
              <div v-if="kind === 'carousel'" class="ved-field">
                <span class="ved-label">Estilo do carrossel</span>
                <div class="ved-seg">
                  <button v-for="(item, key) in CAROUSEL_STYLES" :key="key" type="button" :class="{ on: carouselStyle === key }" :title="item.hint" @click="carouselStyle = key">{{ item.label }}</button>
                </div>
                <p class="ved-hint">{{ CAROUSEL_STYLES[carouselStyle].hint }}</p>
              </div>
              <div v-if="kind === 'carousel'" class="ved-field">
                <span class="ved-label">Formato dos slides</span>
                <div class="ved-seg">
                  <button type="button" :class="{ on: format === 'feed' }" @click="format = 'feed'">Feed 4:5</button>
                  <button type="button" :class="{ on: format === 'story' }" @click="format = 'story'">Stories</button>
                </div>
              </div>
              <div v-else-if="kind === 'post'" class="ved-field">
                <span class="ved-label">Proporção</span>
                <div class="ved-seg">
                  <button type="button" :class="{ on: format === 'feed' }" @click="format = 'feed'">Retrato 4:5</button>
                  <button type="button" :class="{ on: format === 'square' }" @click="format = 'square'">Quadrado</button>
                </div>
              </div>
            </template>

            <!-- 2. Modelo ou slides -->
            <template v-else-if="step.id === 'layout'">
              <template v-if="kind !== 'carousel'">
                <div v-for="(label, category) in CATEGORY_LABELS" :key="category" class="cv-templates">
                  <span class="ved-label">{{ label }}</span>
                  <div class="cv-template-grid">
                    <button
                      v-for="item in templatesBy(category)"
                      :key="item.id"
                      type="button"
                      class="cv-template"
                      :class="{ on: template === item.id }"
                      :title="item.description"
                      @click="template = item.id"
                    >
                      <span class="cv-mini" :style="boxStyle(miniWidth)">
                        <CreativeArtboard :template="item.id" :format="format" :data="data" :photos="previewPhotos" :show-logo="showLogo" :style="scaleStyle(miniWidth)" />
                      </span>
                      <b>{{ item.name }}</b>
                    </button>
                  </div>
                </div>
              </template>
              <template v-else>
                <p class="ved-hint">Montamos os slides com o que a página tem. Desmarque o que não quiser postar e clique na miniatura para escolher a foto de cada slide.</p>
                <ul class="ved-list">
                  <li v-for="item in slides" :key="item.key" class="ved-item" :class="{ open: pickerFor === item.key }">
                    <div class="cv-slide-row">
                      <input
                        type="checkbox"
                        :checked="!excluded.includes(item.key)"
                        :disabled="item.slide.kind === 'cover' || item.slide.kind === 'final'"
                        :aria-label="`Incluir ${slideLabel(item.slide)}`"
                        @change="toggleSlide(item.key)"
                      />
                      <span>{{ slideLabel(item.slide) }}</span>
                      <small v-if="item.slide.kind === 'cover' || item.slide.kind === 'final'">sempre</small>
                      <button
                        v-if="item.slide.kind !== 'section'"
                        type="button"
                        class="cv-slide-photo"
                        :title="`Trocar a foto de ${slideLabel(item.slide)}`"
                        :disabled="excluded.includes(item.key)"
                        @click="pickerFor = pickerFor === item.key ? '' : item.key"
                      >
                        <img v-if="slidePhoto(item.key, 'preview')" :src="slidePhoto(item.key, 'preview')" alt="" />
                        <ImageIcon v-else aria-hidden="true" />
                      </button>
                    </div>
                    <div v-if="pickerFor === item.key" class="cv-picker">
                      <button type="button" class="cv-picker-auto" :class="{ on: !slidePhotos[item.key] }" @click="setSlidePhoto(item.key, '')">Automática</button>
                      <button
                        v-for="photo in photos"
                        :key="photo.src"
                        type="button"
                        class="cv-picker-photo"
                        :class="{ on: slidePhotos[item.key] === photo.src, failed: photo.status === 'failed' }"
                        @click="setSlidePhoto(item.key, photo.src)"
                      >
                        <img :src="photo.ready || photo.src" alt="" loading="lazy" />
                      </button>
                    </div>
                  </li>
                </ul>
              </template>
            </template>

            <!-- 3. Fotos -->
            <template v-else-if="step.id === 'photos'">
              <p class="ved-hint">{{ photoHint }}. Clique para escolher a ordem; a primeira é a principal.</p>
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
                  <span>Enviar</span>
                  <input type="file" accept="image/*" multiple @change="onUpload" />
                </label>
              </div>
              <p v-if="!photos.length" class="ved-hint">A página ainda não tem fotos. Envie uma imagem do seu computador.</p>
            </template>

            <!-- 4. Conteúdo -->
            <template v-else-if="step.id === 'content'">
              <EdText v-model="data.title" label="Título" :maxlength="90" />
              <EdText v-model="data.destination" label="Destino (curto)" hint="Usado em letras grandes nos modelos de oferta." :maxlength="32" />
              <EdText v-model="data.subtitle" label="Subtítulo" multiline :maxlength="160" />
              <EdText v-model="data.dates" label="Datas" placeholder="Ex.: 12/07 a 19/07/2026" />
              <div class="ved-pair">
                <EdText v-model="data.duration" label="Duração" placeholder="8 dias" />
                <EdText v-model="data.departure" label="Saída" placeholder="Saída de Campinas" />
              </div>
              <div class="ved-pair">
                <EdText v-model="data.priceValue" label="Preço total" placeholder="R$ 1.860" />
                <EdText v-model="data.installmentCount" label="Parcelas" placeholder="12" hint="Vazio = mostra o total" />
              </div>
              <div class="ved-pair">
                <EdText v-model="data.oldPrice" label="De (preço antigo)" placeholder="R$ 2.240" />
                <EdText v-model="data.pricePrefix" label="Antes do preço" placeholder="A partir de" />
              </div>
              <EdText v-model="data.priceSuffix" label="Depois do preço" placeholder="por pessoa" />
              <EdText v-model="data.disclaimer" label="Condições (letras miúdas)" multiline :maxlength="180" />

              <span class="ved-label">O que inclui <small class="cv-muted">até 8 · o ícone vem do texto</small></span>
              <ul class="ved-list">
                <li v-for="(_, index) in data.benefits" :key="`b${index}`" class="cv-row-input">
                  <input v-model="data.benefits[index]" class="ved-input" maxlength="60" />
                  <button type="button" class="cv-x" aria-label="Remover benefício" @click="data.benefits.splice(index, 1)"><XIcon aria-hidden="true" /></button>
                </li>
              </ul>
              <button v-if="data.benefits.length < 8" type="button" class="ved-add" @click="data.benefits.push('')"><PlusIcon aria-hidden="true" /> Adicionar benefício</button>

              <template v-if="kind === 'carousel'">
                <span class="ved-label">Roteiro <small class="cv-muted">{{ data.itinerary.length }} dias</small></span>
                <ul class="ved-list">
                  <li v-for="(day, index) in data.itinerary" :key="`d${index}`" class="ved-item cv-card-item">
                    <div class="cv-row-input">
                      <span class="cv-day">{{ index + 1 }}</span>
                      <input v-model="day.title" class="ved-input" maxlength="70" placeholder="Título do dia" />
                      <button type="button" class="cv-x" aria-label="Remover dia" @click="data.itinerary.splice(index, 1)"><XIcon aria-hidden="true" /></button>
                    </div>
                    <textarea v-model="day.description" class="ved-input" rows="2" maxlength="140" placeholder="Resumo do dia"></textarea>
                  </li>
                </ul>
                <button type="button" class="ved-add" @click="data.itinerary.push({ day: '', title: '', description: '' })"><PlusIcon aria-hidden="true" /> Adicionar dia</button>

                <span class="ved-label">Valores</span>
                <ul class="ved-list">
                  <li v-for="(item, index) in data.prices" :key="`p${index}`" class="ved-item cv-card-item">
                    <div class="cv-row-input">
                      <input v-model="item.title" class="ved-input" maxlength="50" placeholder="Ex.: Quarto duplo" />
                      <input v-model="item.value" class="ved-input cv-short" maxlength="20" placeholder="R$ 2.990" />
                      <button type="button" class="cv-x" aria-label="Remover valor" @click="data.prices.splice(index, 1)"><XIcon aria-hidden="true" /></button>
                    </div>
                    <input v-model="item.note" class="ved-input" maxlength="90" placeholder="Observação (opcional)" />
                  </li>
                </ul>
                <button type="button" class="ved-add" @click="data.prices.push({ title: '', prefix: '', value: '', note: '' })"><PlusIcon aria-hidden="true" /> Adicionar valor</button>

                <span class="ved-label">Voos</span>
                <ul class="ved-list">
                  <li v-for="(flight, index) in data.flights" :key="`f${index}`" class="ved-item cv-card-item">
                    <div class="cv-row-input">
                      <input v-model="flight.label" class="ved-input cv-short" maxlength="20" placeholder="Ida" />
                      <input v-model="flight.date" class="ved-input cv-short" maxlength="12" placeholder="12/07" />
                      <button type="button" class="cv-x" aria-label="Remover voo" @click="data.flights.splice(index, 1)"><XIcon aria-hidden="true" /></button>
                    </div>
                    <input v-model="flight.route" class="ved-input" maxlength="80" placeholder="São Paulo (GRU) → Recife (REC)" />
                    <input v-model="flight.details" class="ved-input" maxlength="80" placeholder="LATAM · Voo direto" />
                  </li>
                </ul>
                <button type="button" class="ved-add" @click="data.flights.push({ label: 'Ida', date: '', route: '', times: '', details: '' })"><PlusIcon aria-hidden="true" /> Adicionar voo</button>
              </template>
            </template>

            <!-- 5. Botão e contato -->
            <template v-else-if="step.id === 'cta'">
              <EdToggle v-model="data.ctaEnabled" label="Mostrar botão na arte" hint="A imagem não é clicável: use como chamada, igual aos anúncios." />
              <template v-if="data.ctaEnabled">
                <EdText v-model="data.cta" label="Texto do botão" :maxlength="28" placeholder="Saiba mais" />
                <div class="cv-chips">
                  <button v-for="option in CTA_SUGGESTIONS" :key="option" type="button" :class="{ on: data.cta === option }" @click="data.cta = option">{{ option }}</button>
                </div>
              </template>
              <EdText v-model="data.contact" label="WhatsApp" hint="Aparece como texto, não como botão." placeholder="(11) 99999-0000" />
            </template>

            <!-- 6. Campanha, cores e logo -->
            <template v-else-if="step.id === 'style'">
              <div class="ved-field">
                <span class="ved-label">Campanha temporária</span>
                <div class="ved-seg">
                  <button type="button" :class="{ on: !data.campaign }" @click="setCampaign('')">Nenhuma</button>
                  <button v-for="(item, key) in CAMPAIGNS" :key="key" type="button" :class="{ on: data.campaign === key }" @click="setCampaign(key)">{{ item.label }}</button>
                </div>
                <p v-if="data.campaign" class="ved-hint">Preto e amarelo enquanto a campanha estiver ligada; suas cores voltam ao desligar.</p>
              </div>
              <EdToggle v-model="data.tapes" label="Faixas cruzadas no topo" hint="Fitas com o texto da campanha ou da tag." />
              <EdText v-model="data.badge" label="Tag" placeholder="Oferta" hint="Selo, fita ou etiqueta da arte. Vazio = sem tag." :maxlength="28" />
              <div class="cv-chips">
                <button v-for="option in BADGE_SUGGESTIONS" :key="option" type="button" :class="{ on: data.badge === option }" @click="data.badge = option">{{ option }}</button>
              </div>
              <p v-if="isBlackTemplate" class="ved-hint">Os modelos de Black Friday usam sempre preto e amarelo.</p>
              <div class="ved-pair">
                <label class="cv-color"><input v-model="data.primary" type="color" /><span><b>Fundo</b><small>{{ data.primary }}</small></span></label>
                <label class="cv-color"><input v-model="data.secondary" type="color" /><span><b>Destaque</b><small>{{ data.secondary }}</small></span></label>
              </div>
              <EdToggle v-if="data.logoUrl" v-model="showLogo" label="Mostrar o logo" />
              <p v-else class="ved-hint">A página não tem logo.</p>
              <button type="button" class="ved-add" @click="resetData"><RotateCcwIcon aria-hidden="true" /> Voltar aos dados da página</button>
            </template>

            <div class="cv-step-foot">
              <button v-if="index < steps.length - 1" type="button" class="ed-btn ed-btn-primary" @click="openStep = steps[index + 1].id">
                Continuar <ArrowRightIcon aria-hidden="true" />
              </button>
              <button v-else type="button" class="ed-btn ed-btn-primary" :disabled="downloading" @click="download">
                <DownloadIcon aria-hidden="true" /> {{ downloadLabel }}
              </button>
            </div>
          </div>
        </section>
      </aside>

      <!-- Prévia -->
      <section class="cv-stage">
        <div class="cv-toolbar">
          <span class="cv-toolbar-label">{{ previewLabel }}</span>
          <div v-if="kind === 'carousel'" class="ved-seg cv-view">
            <button type="button" :class="{ on: view === 'all' }" @click="view = 'all'"><LayoutGridIcon aria-hidden="true" /> Todos</button>
            <button type="button" :class="{ on: view === 'one' }" @click="view = 'one'"><SquareIcon aria-hidden="true" /> Um por um</button>
          </div>
          <div class="cv-zoom">
            <button type="button" class="ed-icon-btn" aria-label="Diminuir zoom" @click="zoomBy(-0.1)"><MinusIcon aria-hidden="true" /></button>
            <button type="button" class="cv-zoom-value" title="Ajustar à tela" @click="zoom = 'fit'">{{ zoom === "fit" ? "Ajustar" : `${Math.round(scale * 100)}%` }}</button>
            <button type="button" class="ed-icon-btn" aria-label="Aumentar zoom" @click="zoomBy(0.1)"><PlusIcon aria-hidden="true" /></button>
          </div>
        </div>

        <div ref="canvasRef" class="cv-canvas" :class="{ 'is-fit': zoom === 'fit', 'is-grid': kind === 'carousel' && view === 'all' }">
          <!-- Arte única -->
          <div v-if="kind !== 'carousel'" class="cv-frame" :style="boxStyle(size.width * scale)">
            <CreativeArtboard :template="template" :format="format" :data="data" :photos="previewPhotos" :show-logo="showLogo" :style="scaleStyle(size.width * scale)" />
          </div>

          <!-- Carrossel: todos -->
          <div v-else-if="view === 'all'" class="cv-grid">
            <button
              v-for="(item, index) in activeSlides"
              :key="item.key"
              type="button"
              class="cv-grid-item"
              :title="`Ver ${slideLabel(item.slide)}`"
              @click="openOne(index)"
            >
              <span class="cv-frame" :style="boxStyle(size.width * scale)">
                <component
                  :is="slideComponent"
                  v-bind="sectionBindings(item.slide, 'preview')"
                  :slide="item.slide"
                  :format="format"
                  :data="data"
                  :photo="slidePhoto(item.key, 'preview', index)"
                  :photos="slideGallery(item.key, 'preview', index)"
                  :index="index"
                  :total="activeSlides.length"
                  :show-logo="showLogo"
                  :style="scaleStyle(size.width * scale)"
                />
              </span>
              <small>{{ index + 1 }}. {{ slideLabel(item.slide) }}</small>
            </button>
          </div>

          <!-- Carrossel: um por um -->
          <div v-else class="cv-one">
            <button type="button" class="ed-icon-btn cv-nav" aria-label="Slide anterior" :disabled="current === 0" @click="current -= 1"><ChevronLeftIcon aria-hidden="true" /></button>
            <div v-if="currentSlide" class="cv-frame" :style="boxStyle(size.width * scale)">
              <component
                  :is="slideComponent"
                  v-bind="sectionBindings(currentSlide.slide, 'preview')"
                :slide="currentSlide.slide"
                :format="format"
                :data="data"
                :photo="slidePhoto(currentSlide.key, 'preview', current)"
                  :photos="slideGallery(currentSlide.key, 'preview', current)"
                :index="current"
                :total="activeSlides.length"
                :show-logo="showLogo"
                :style="scaleStyle(size.width * scale)"
              />
            </div>
            <button type="button" class="ed-icon-btn cv-nav" aria-label="Próximo slide" :disabled="current >= activeSlides.length - 1" @click="current += 1"><ChevronRightIcon aria-hidden="true" /></button>
          </div>
        </div>

        <div v-if="kind === 'carousel' && view === 'one'" class="cv-dots">
          <button
            v-for="(item, index) in activeSlides"
            :key="item.key"
            type="button"
            :class="{ on: index === current }"
            :aria-label="`Slide ${index + 1}: ${slideLabel(item.slide)}`"
            @click="current = index"
          ></button>
          <span>{{ current + 1 }} de {{ activeSlides.length }} · {{ currentSlide ? slideLabel(currentSlide.slide) : "" }}</span>
        </div>
        <div v-if="kind === 'carousel' && view === 'one' && currentSlide && photos.length && currentSlide.slide.kind !== 'section'" class="cv-strip">
          <span>Foto deste slide</span>
          <button type="button" class="cv-picker-auto" :class="{ on: !slidePhotos[currentSlide.key] }" @click="setSlidePhoto(currentSlide.key, '')">Automática</button>
          <button
            v-for="photo in photos"
            :key="photo.src"
            type="button"
            class="cv-picker-photo"
            :class="{ on: slidePhotos[currentSlide.key] === photo.src, failed: photo.status === 'failed' }"
            @click="setSlidePhoto(currentSlide.key, photo.src)"
          >
            <img :src="photo.ready || photo.src" alt="" loading="lazy" />
          </button>
        </div>
      </section>

      <!-- Cópia em tamanho real, fora da tela, usada só para gerar os PNGs. -->
      <div class="cv-offscreen" aria-hidden="true">
        <div ref="exportRef">
          <CreativeArtboard v-if="kind !== 'carousel'" :template="template" :format="format" :data="exportData" :photos="exportPhotos" :show-logo="showLogo" />
          <template v-else>
            <component
                  :is="slideComponent"
                  v-bind="sectionBindings(item.slide, 'export')"
              v-for="(item, index) in activeSlides"
              :key="item.key"
              :slide="item.slide"
              :format="format"
              :data="exportData"
              :photo="slidePhoto(item.key, 'export', index)"
                  :photos="slideGallery(item.key, 'export', index)"
              :index="index"
              :total="activeSlides.length"
              :show-logo="showLogo"
            />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Criativos a partir da viagem, em passos: o que criar → modelo/slides → fotos → conteúdo →
 * botão → cores. A prévia ao lado tem zoom e, no carrossel, mostra todos ou um por um.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  ArrowRightIcon,
  CheckIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DownloadIcon,
  ImageIcon,
  LayoutGridIcon,
  MinusIcon,
  PlusIcon,
  RotateCcwIcon,
  SquareIcon,
  UploadIcon,
  XIcon
} from "lucide-vue-next";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import type { PageConfig } from "../../types/page";
import EdText from "../../components/admin/v2edit/EdText.vue";
import EdToggle from "../../components/admin/v2edit/EdToggle.vue";
import "../../components/admin/v2edit/v2edit.css";
import CreativeArtboard from "../../components/creatives/CreativeArtboard.vue";
import CreativeCarouselSlide from "../../components/creatives/CreativeCarouselSlide.vue";
import CreativeRoteiroSlide from "../../components/creatives/CreativeRoteiroSlide.vue";
import CreativeSectionSlide from "../../components/creatives/CreativeSectionSlide.vue";
import { v2Components } from "../../components/public/v2/registry";
import { sectionNameV2 } from "../../utils/sectionCatalogV2";
import { resolveMediaUrl } from "../../utils/media";
import type { PageSection } from "../../types/page";
import {
  BADGE_SUGGESTIONS,
  CAMPAIGNS,
  CTA_SUGGESTIONS,
  FORMAT_SIZES,
  extractCreativeData,
  type CreativeCampaign,
  type CreativeData,
  type CreativeFormat
} from "../../components/creatives/creativeData";
import { CAROUSEL_STYLES, SLIDE_LABELS, buildCarousel, type CarouselSlide, type CarouselStyle } from "../../components/creatives/carousel";
import { BLACK_TEMPLATES, CATEGORY_LABELS, CREATIVE_TEMPLATES, type CreativeCategory } from "../../components/creatives/creativeTemplates";

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
type Kind = "story" | "post" | "carousel";

const KINDS: { id: Kind; name: string; hint: string }[] = [
  { id: "story", name: "Stories", hint: "1080×1920, uma arte" },
  { id: "post", name: "Post no feed", hint: "1080×1350, uma arte" },
  { id: "carousel", name: "Carrossel", hint: "Feed ou Stories, com tudo" }
];

const agencyStore = useAgencyStore();
const page = ref<PagePayload | null>(null);
const data = ref<CreativeData | null>(null);
const loading = ref(true);
const error = ref("");
const downloading = ref(false);
const kind = ref<Kind>("post");
const format = ref<CreativeFormat>("feed");
const template = ref(CREATIVE_TEMPLATES[0].id);
const showLogo = ref(true);
const photos = ref<Photo[]>([]);
const chosen = ref<string[]>([]);
const excluded = ref<string[]>([]);
const carouselStyle = ref<CarouselStyle>("photo");
const slideComponent = computed(() =>
  carouselStyle.value === "sections" ? CreativeSectionSlide : carouselStyle.value === "pages" ? CreativeRoteiroSlide : CreativeCarouselSlide
);
const logoReady = ref("");
const exportRef = ref<HTMLElement | null>(null);
const canvasRef = ref<HTMLElement | null>(null);
const openStep = ref("kind");
const view = ref<"all" | "one">("all");
const current = ref(0);
const zoom = ref<number | "fit">("fit");
const canvasSize = ref({ width: 600, height: 700 });
const miniWidth = 150;
const objectUrls: string[] = [];

const chooseKind = (value: Kind) => {
  kind.value = value;
  if (value === "story") format.value = "story";
  else if (value === "post" && format.value === "story") format.value = "feed";
  else if (value === "carousel" && format.value === "square") format.value = "feed";
  current.value = 0;
  zoom.value = "fit";
};

const size = computed(() => FORMAT_SIZES[format.value]);
const isBlackTemplate = computed(() => kind.value !== "carousel" && BLACK_TEMPLATES.has(template.value));
// Campanha: liga as fitas e a tag dela; ao desligar, volta ao normal.
const setCampaign = (value: CreativeCampaign) => {
  if (!data.value) return;
  const previous = data.value.campaign ? CAMPAIGNS[data.value.campaign].badge : "";
  data.value.campaign = value;
  data.value.tapes = Boolean(value);
  if (value && (!data.value.badge || data.value.badge === "Oferta")) data.value.badge = CAMPAIGNS[value].badge;
  else if (!value && data.value.badge === previous) data.value.badge = "Oferta";
};
const currentTemplate = computed(() => CREATIVE_TEMPLATES.find(item => item.id === template.value));
const templatesBy = (category: string) => CREATIVE_TEMPLATES.filter(item => item.category === (category as CreativeCategory));

// --- Carrossel ---
const slides = computed(() => {
  if (!data.value) return [];
  const counts: Record<string, number> = {};
  if (carouselStyle.value === "sections") return sectionSlides.value;
  return buildCarousel(data.value, format.value, carouselStyle.value).map(slide => {
    counts[slide.kind] = (counts[slide.kind] || 0) + 1;
    return { slide, key: `${slide.kind}-${counts[slide.kind]}` };
  });
});
const activeSlides = computed(() => slides.value.filter(item => !excluded.value.includes(item.key)));
const currentSlide = computed(() => activeSlides.value[Math.min(current.value, activeSlides.value.length - 1)]);
watch(activeSlides, list => {
  if (current.value > list.length - 1) current.value = Math.max(0, list.length - 1);
});
const toggleSlide = (key: string) => {
  excluded.value = excluded.value.includes(key) ? excluded.value.filter(item => item !== key) : [...excluded.value, key];
};
const slideLabel = (slide: CarouselSlide) => {
  if (slide.kind === "section") return slide.label;
  return slide.kind === "itinerary" && slide.parts > 1 ? `${SLIDE_LABELS.itinerary} ${slide.part}/${slide.parts}` : SLIDE_LABELS[slide.kind];
};
/** Cada slide usa a próxima foto escolhida (e recomeça quando acabam). */
const photoFor = (index: number, list: string[]) => (list.length ? list[index % list.length] : "");
// Foto escolhida para cada slide (chave do slide → foto); sem escolha, segue a ordem das fotos.
const slidePhotos = ref<Record<string, string>>({});
const pickerFor = ref("");
const setSlidePhoto = (key: string, src: string) => {
  const next = { ...slidePhotos.value };
  if (src) next[key] = src;
  else delete next[key];
  slidePhotos.value = next;
};
const slidePhoto = (key: string, use: "preview" | "export", fallbackIndex?: number) => {
  const chosenSrc = slidePhotos.value[key];
  const photo = chosenSrc ? photos.value.find(item => item.src === chosenSrc) : undefined;
  if (photo) return use === "export" ? photo.ready : photo.ready || photo.src;
  const index = fallbackIndex ?? Math.max(0, activeSlides.value.findIndex(item => item.key === key));
  return photoFor(index, use === "export" ? exportPhotos.value : previewPhotos.value);
};
/** Foto do slide e as seguintes (o estilo em páginas usa mais de uma: fileira, polaroides). */
const slideGallery = (key: string, use: "preview" | "export", index: number) => {
  const list = use === "export" ? exportPhotos.value : previewPhotos.value;
  const main = slidePhoto(key, use, index);
  const rest = list.length ? Array.from({ length: Math.min(3, list.length) }, (_, step) => list[(index + step + 1) % list.length]) : [];
  return [main, ...rest.filter(url => url && url !== main)];
};
const openOne = (index: number) => {
  current.value = index;
  view.value = "one";
  zoom.value = "fit";
};

// --- Carrossel "Seções da página": cada seção ativa vira um slide, com o componente do site ---
// Seções que não fazem sentido numa imagem (menu, formulários, vídeos, checkout) ficam de fora.
// A contagem regressiva parada e o rodapé também não funcionam como imagem de post.
const SECTION_SKIP = new Set(["header", "internal_form", "viajeon_checkout", "video_vsl", "featured_video", "free_footer_brand", "countdown", "agency_footer"]);
const pageSections = computed(() => ((page.value?.config_json?.sections || []) as PageSection[]).filter(section => section.enabled !== false));
const sectionSlides = computed(() =>
  pageSections.value
    .map((section, sectionIndex) => ({ section, sectionIndex }))
    .filter(({ section }) => !SECTION_SKIP.has(section.type) && v2Components[section.type])
    .map(({ section, sectionIndex }) => ({
      slide: { kind: "section", sectionIndex, label: sectionNameV2(section.type) || section.type } as CarouselSlide,
      key: `section-${sectionIndex}`
    }))
);
const sectionBranding = computed(() => {
  const agency = agencyStore.agencies.find(item => item.id === page.value?.agency_id);
  return {
    agency_name: agency?.name || "",
    logo_url: agency?.logo_url || "",
    primary_color: data.value?.secondary || "",
    secondary_color: agency?.secondary_color || data.value?.secondary || "",
    agency_profile: {},
    theme: page.value?.config_json?.theme
  };
});
// Na exportação, as fotos da seção viram as cópias locais (sem bloqueio de CORS no PNG).
const swapPhotos = (value: unknown): unknown => {
  if (typeof value === "string") {
    const resolved = resolveMediaUrl(value) || value;
    const photo = photos.value.find(item => item.src === resolved || item.src === value);
    return photo?.ready || value;
  }
  if (Array.isArray(value)) return value.map(swapPhotos);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, swapPhotos(item)]));
  return value;
};
const sectionBindings = (slide: CarouselSlide, use: "preview" | "export") => {
  if (slide.kind !== "section") return {};
  const section = pageSections.value[slide.sectionIndex];
  const hero = pageSections.value.find(item => item.type === "hero") as any;
  return {
    section: use === "export" ? swapPhotos(section) : section,
    allSections: pageSections.value,
    branding: sectionBranding.value,
    accent: page.value?.config_json?.theme?.ctaDefaultColor || data.value?.secondary || "#12B981",
    tripStartDate: hero?.departureDate || ""
  };
};

// --- Passos ---
const steps = computed(() => {
  const d = data.value;
  const kindName = KINDS.find(item => item.id === kind.value)?.name || "";
  return [
    { id: "kind", title: "O que você quer criar?", summary: `${kindName} · ${size.value.width}×${size.value.height}` },
    {
      id: "layout",
      title: kind.value === "carousel" ? "Slides" : "Modelo",
      summary: kind.value === "carousel" ? `${activeSlides.value.length} slides` : currentTemplate.value?.name || ""
    },
    { id: "photos", title: "Fotos", summary: chosen.value.length ? `${chosen.value.length} escolhida(s)` : "Fotos da página" },
    { id: "content", title: "Textos e informações", summary: d?.title || "" },
    { id: "cta", title: "Botão e contato", summary: d?.ctaEnabled ? `Botão: ${d.cta}` : "Sem botão" },
    {
      id: "style",
      title: "Campanha, tag e cores",
      summary: [d?.campaign ? CAMPAIGNS[d.campaign].label : "", d?.badge ? `Tag: ${d.badge}` : "Sem tag", showLogo.value && d?.logoUrl ? "com logo" : ""].filter(Boolean).join(" · ")
    }
  ];
});
const stepIndex = computed(() => Math.max(0, steps.value.findIndex(step => step.id === openStep.value)));

// --- Fotos ---
const ordered = computed(() => {
  const picked = chosen.value.map(src => photos.value.find(photo => photo.src === src)).filter(Boolean) as Photo[];
  if (picked.length) return picked;
  // Sem escolha: arte única usa a capa; o carrossel passa por todas as fotos da página.
  return kind.value === "carousel" ? photos.value.filter(photo => photo.status !== "failed") : photos.value.slice(0, 1);
});
const previewPhotos = computed(() => ordered.value.map(photo => photo.ready || photo.src));
const exportPhotos = computed(() => ordered.value.map(photo => photo.ready).filter(Boolean));
const exportData = computed<CreativeData>(() => ({ ...(data.value as CreativeData), logoUrl: logoReady.value }));
const photoHint = computed(() => {
  if (kind.value === "carousel") return "Uma foto por slide, na ordem";
  const count = currentTemplate.value?.photos || 1;
  return count > 1 ? `Este modelo usa ${count} fotos` : "Este modelo usa 1 foto";
});

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

// --- Prévia e zoom ---
const fitScale = computed(() => {
  const { width, height } = canvasSize.value;
  const pad = 48;
  if (kind.value === "carousel" && view.value === "all") {
    // Grade: 3 slides por linha no feed, 4 no stories.
    const columns = width < 560 ? 2 : format.value === "story" ? 4 : 3;
    return Math.max(0.08, (width - pad - (columns - 1) * 20) / columns / size.value.width);
  }
  const side = kind.value === "carousel" ? 120 : 0;
  return Math.max(0.1, Math.min((width - pad - side) / size.value.width, (height - pad) / size.value.height));
});
const scale = computed(() => (zoom.value === "fit" ? fitScale.value : zoom.value));
const zoomBy = (delta: number) => {
  zoom.value = Math.min(1, Math.max(0.1, Math.round((scale.value + delta) * 10) / 10));
};
const boxStyle = (width: number) => ({ width: `${Math.round(width)}px`, height: `${Math.round((width * size.value.height) / size.value.width)}px` });
const scaleStyle = (width: number) => ({ transform: `scale(${width / 1080})`, transformOrigin: "top left" });

const previewLabel = computed(() => `${size.value.label} · ${size.value.width}×${size.value.height}`);

// --- Download ---
const downloadLabel = computed(() => {
  if (downloading.value) return "Gerando…";
  return kind.value === "carousel" ? `Baixar ${activeSlides.value.length} slides (.zip)` : "Baixar PNG";
});

const BLANK_PIXEL = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
const toPngOf = async (node: HTMLElement) => {
  const { toPng } = await import("html-to-image");
  // Foto que não carrega (link quebrado na página) vira transparente em vez de travar o download.
  return toPng(node, { width: size.value.width, height: size.value.height, pixelRatio: 1, cacheBust: false, imagePlaceholder: BLANK_PIXEL });
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
  const needed = kind.value === "carousel" ? Math.min(activeSlides.value.length, ordered.value.length) : Math.max(1, currentTemplate.value?.photos || 1);
  const overrides = kind.value === "carousel" ? activeSlides.value.map(item => slidePhotos.value[item.key]).filter(Boolean) : [];
  const missing =
    ordered.value.slice(0, needed).some(photo => !photo.ready) ||
    overrides.some(src => !photos.value.find(photo => photo.src === src)?.ready);
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
    if (kind.value !== "carousel") {
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
watch(canvasRef, element => {
  observer?.disconnect();
  if (!element) return;
  observer = new ResizeObserver(() => {
    canvasSize.value = { width: element.clientWidth, height: element.clientHeight };
  });
  observer.observe(element);
});

const onKey = (event: KeyboardEvent) => {
  if (kind.value !== "carousel" || view.value !== "one") return;
  const target = event.target as HTMLElement | null;
  if (target && /INPUT|TEXTAREA|SELECT/.test(target.tagName)) return;
  if (event.key === "ArrowRight") current.value = Math.min(activeSlides.value.length - 1, current.value + 1);
  if (event.key === "ArrowLeft") current.value = Math.max(0, current.value - 1);
};

onMounted(() => {
  load();
  window.addEventListener("keydown", onKey);
});
onBeforeUnmount(() => {
  observer?.disconnect();
  window.removeEventListener("keydown", onKey);
  objectUrls.forEach(url => URL.revokeObjectURL(url));
});
</script>

<style scoped>
.cv { display: flex; flex-direction: column; gap: 16px; min-width: 0; font-family: var(--font-sans); color: var(--foreground); }
.cv > * { min-width: 0; }

/* Botões iguais aos do editor de páginas (lá ficam em estilo restrito à tela) */
.ed-btn { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; transition: background 0.15s, opacity 0.15s; }
.ed-btn:disabled { cursor: not-allowed; opacity: 0.55; }
.ed-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.ed-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); }
.ed-icon-btn { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 999px; background: var(--card); color: var(--muted-foreground); box-shadow: var(--shadow-card); }
.ed-icon-btn:hover:not(:disabled) { color: var(--foreground); background: var(--accent); }

/* Cabeçalho no padrão do editor de páginas */
.cv-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.cv-back svg { width: 18px; height: 18px; }
.cv-head-text { flex: 1; min-width: 0; }
.cv-crumb { margin: 0; overflow: hidden; color: var(--muted-foreground); font-size: 12.5px; white-space: nowrap; text-overflow: ellipsis; }
.cv-title-row { display: flex; align-items: center; gap: 10px; }
.cv-title { margin: 0; font-family: var(--font-display); font-size: 22px; font-weight: 700; }
.cv-beta { padding: 3px 9px; border-radius: 999px; background: var(--accent); color: var(--accent-foreground); font-size: 11px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
.cv-download svg { width: 16px; height: 16px; }
.cv-alert { margin: 0; padding: 10px 14px; border-radius: 12px; background: var(--status-danger); color: var(--status-danger-foreground); font-size: 14px; }
.cv-muted { color: var(--muted-foreground); font-weight: 500; }

/* Card único, como o editor */
.cv-shell {
  display: grid;
  grid-template-columns: minmax(0, 400px) minmax(0, 1fr);
  height: calc(100vh - 150px);
  min-height: 560px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}
.cv-loading { display: grid; place-items: center; color: var(--muted-foreground); }

/* Passos */
.cv-steps { display: flex; min-height: 0; flex-direction: column; gap: 8px; overflow-y: auto; padding: 16px; border-right: 1px solid var(--border); }
.cv-step { flex: none; border-radius: 16px; background: var(--card); box-shadow: inset 0 0 0 1px var(--border); }
.cv-step.open { box-shadow: inset 0 0 0 1.5px var(--primary); }
.cv-step-head { display: flex; align-items: center; gap: 12px; width: 100%; padding: 12px 14px; text-align: left; }
.cv-step-num { display: grid; place-items: center; flex: none; width: 28px; height: 28px; border-radius: 50%; background: var(--muted); color: var(--muted-foreground); font-size: 13px; font-weight: 800; }
.cv-step-num svg { width: 15px; height: 15px; }
.cv-step.open .cv-step-num { background: var(--primary); color: var(--primary-foreground); }
.cv-step.done .cv-step-num { background: var(--accent); color: var(--accent-foreground); }
.cv-step-text { display: flex; flex: 1; min-width: 0; flex-direction: column; }
.cv-step-text b { font-size: 14.5px; font-weight: 700; }
.cv-step-text small { overflow: hidden; color: var(--muted-foreground); font-size: 12.5px; white-space: nowrap; text-overflow: ellipsis; }
.cv-step-chev { flex: none; width: 16px; height: 16px; color: var(--muted-foreground); transition: transform 0.2s ease; }
.cv-step.open .cv-step-chev { transform: rotate(180deg); }
.cv-step-body { display: flex; flex-direction: column; gap: 14px; padding: 2px 14px 14px; }
.cv-step-foot { display: flex; justify-content: flex-end; padding-top: 4px; }
.cv-step-foot svg { width: 16px; height: 16px; }

.cv-kinds { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.cv-kind { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 14px 8px 12px; border-radius: 14px; background: var(--card); box-shadow: inset 0 0 0 1px var(--border); text-align: center; }
.cv-kind:hover { background: var(--accent); }
.cv-kind.on { background: var(--accent); box-shadow: inset 0 0 0 1.5px var(--primary); }
.cv-kind b { font-size: 13.5px; }
.cv-kind small { color: var(--muted-foreground); font-size: 11.5px; line-height: 1.3; }
.cv-kind-shape { display: flex; align-items: flex-end; gap: 3px; height: 44px; margin-bottom: 4px; }
.cv-kind-shape i { display: block; border-radius: 5px; background: var(--primary); opacity: 0.85; }
.cv-kind-shape.is-story i { width: 25px; height: 44px; }
.cv-kind-shape.is-post i { width: 32px; height: 40px; }
.cv-kind-shape.is-carousel i { width: 22px; height: 28px; }
.cv-kind-shape.is-carousel i + i { opacity: 0.45; }

.cv-templates { display: flex; flex-direction: column; gap: 8px; }
.cv-template-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.cv-template { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 8px; border-radius: 14px; box-shadow: inset 0 0 0 1px var(--border); font-size: 12.5px; }
.cv-template.on { background: var(--accent); box-shadow: inset 0 0 0 1.5px var(--primary); }
.cv-mini,
.cv-frame { position: relative; display: block; flex: none; overflow: hidden; border-radius: 8px; background: var(--muted); }
.cv-mini > :deep(*),
.cv-frame > :deep(*) { position: absolute; top: 0; left: 0; }

.cv-slide-row { display: flex; align-items: center; gap: 10px; padding: 8px 8px 8px 12px; font-size: 14px; font-weight: 600; }
.cv-slide-photo { display: grid; place-items: center; flex: none; width: 40px; height: 40px; overflow: hidden; margin-left: auto; border-radius: 10px; background: var(--muted); color: var(--muted-foreground); box-shadow: inset 0 0 0 1px var(--border); }
.cv-slide-row small + .cv-slide-photo { margin-left: 8px; }
.cv-slide-photo:disabled { opacity: 0.4; }
.cv-slide-photo img { width: 100%; height: 100%; object-fit: cover; }
.cv-slide-photo svg { width: 16px; height: 16px; }
.cv-picker, .cv-strip { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 0 10px 10px; }
.cv-strip { justify-content: center; padding: 0 16px 14px; }
.cv-strip > span { margin-right: 4px; color: var(--muted-foreground); font-size: 12.5px; font-weight: 600; }
.cv-picker-auto { height: 40px; padding: 0 12px; border-radius: 10px; box-shadow: inset 0 0 0 1px var(--border); background: var(--card); font-size: 12.5px; font-weight: 600; }
.cv-picker-photo { width: 40px; height: 40px; overflow: hidden; padding: 0; border-radius: 10px; box-shadow: inset 0 0 0 1px var(--border); }
.cv-picker-photo img { display: block; width: 100%; height: 100%; object-fit: cover; }
.cv-picker-photo.failed img { opacity: 0.4; }
.cv-picker-auto.on, .cv-picker-photo.on { box-shadow: 0 0 0 2.5px var(--primary); }
.cv-slide-row input { width: 16px; height: 16px; accent-color: var(--primary); }
.cv-slide-row small { margin-left: auto; color: var(--muted-foreground); font-weight: 500; }

.cv-photos { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.cv-photo { position: relative; aspect-ratio: 1; overflow: hidden; padding: 0; border-radius: 12px; background: var(--muted); box-shadow: inset 0 0 0 1px var(--border); cursor: pointer; }
.cv-photo img { display: block; width: 100%; height: 100%; object-fit: cover; }
.cv-photo.on { box-shadow: 0 0 0 2.5px var(--primary); }
.cv-photo.failed img { opacity: 0.4; }
.cv-photo b { position: absolute; top: 4px; left: 4px; display: grid; place-items: center; min-width: 22px; height: 22px; border-radius: 999px; background: var(--primary); color: var(--primary-foreground); font-size: 12px; }
.cv-spin { position: absolute; right: 6px; bottom: 6px; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: cv-spin 0.8s linear infinite; }
@keyframes cv-spin { to { transform: rotate(360deg); } }
.cv-upload { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border: 1.5px dashed var(--border); box-shadow: none; color: var(--muted-foreground); font-size: 12px; font-weight: 700; }
.cv-upload svg { width: 18px; height: 18px; }
.cv-upload input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }

.cv-row-input { display: flex; align-items: center; gap: 6px; }
.cv-row-input .ved-input { min-width: 0; }
.cv-card-item { display: flex; flex-direction: column; gap: 6px; padding: 8px; }
.cv-short { flex: 0 0 34%; }
.cv-day { display: grid; place-items: center; flex: none; width: 26px; height: 26px; border-radius: 50%; background: var(--muted); font-size: 12px; font-weight: 800; }
.cv-x { display: grid; place-items: center; flex: none; width: 32px; height: 32px; border-radius: 10px; color: var(--muted-foreground); }
.cv-x:hover { background: var(--status-danger); color: var(--status-danger-foreground); }
.cv-x svg { width: 15px; height: 15px; }
.cv-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.cv-chips button { padding: 6px 12px; border-radius: 999px; box-shadow: inset 0 0 0 1px var(--border); font-size: 13px; font-weight: 600; }
.cv-chips button.on { background: var(--accent); color: var(--accent-foreground); box-shadow: inset 0 0 0 1.5px var(--primary); }
.cv-color { display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 12px; box-shadow: inset 0 0 0 1px var(--border); cursor: pointer; }
.cv-color input { flex: none; width: 36px; height: 36px; padding: 0; border: 0; border-radius: 10px; background: none; cursor: pointer; }
.cv-color span { display: flex; flex-direction: column; }
.cv-color b { font-size: 13px; }
.cv-color small { color: var(--muted-foreground); font-size: 12px; text-transform: uppercase; }

/* Prévia */
.cv-stage { display: flex; min-width: 0; min-height: 0; flex-direction: column; background: var(--surface-muted); }
.cv-toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 10px 16px; border-bottom: 1px solid var(--border); background: var(--card); }
.cv-toolbar-label { color: var(--muted-foreground); font-size: 13px; font-weight: 600; }
.cv-view { margin-left: auto; }
.cv-view button { display: inline-flex; align-items: center; gap: 6px; padding: 0 12px; white-space: nowrap; }
.cv-view svg { width: 15px; height: 15px; }
.cv-zoom { display: flex; align-items: center; gap: 6px; margin-left: auto; }
.cv-view + .cv-zoom { margin-left: 8px; }
.cv-zoom .ed-icon-btn { width: 34px; height: 34px; }
.cv-zoom .ed-icon-btn svg { width: 15px; height: 15px; }
.cv-zoom-value { min-width: 72px; height: 34px; padding: 0 10px; border-radius: 999px; background: var(--muted); font-size: 13px; font-weight: 700; }
.cv-canvas { position: relative; flex: 1; min-height: 0; overflow: auto; padding: 24px; }
.cv-canvas.is-fit:not(.is-grid) { display: grid; place-items: center; overflow: hidden; }
.cv-canvas > .cv-frame { margin: 0 auto; box-shadow: 0 18px 50px -18px rgba(15, 23, 19, 0.35); }
.cv-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }
.cv-grid-item { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.cv-grid-item .cv-frame { box-shadow: 0 10px 30px -14px rgba(15, 23, 19, 0.35); transition: transform 0.15s ease; }
.cv-grid-item:hover .cv-frame { transform: translateY(-2px); }
.cv-grid-item small { color: var(--muted-foreground); font-size: 12.5px; font-weight: 600; }
.cv-one { display: flex; align-items: center; justify-content: center; gap: 16px; min-height: 100%; }
.cv-one .cv-frame { box-shadow: 0 18px 50px -18px rgba(15, 23, 19, 0.35); }
.cv-nav { flex: none; }
.cv-nav svg { width: 18px; height: 18px; }
.cv-nav:disabled { opacity: 0.35; }
.cv-dots { display: flex; align-items: center; justify-content: center; gap: 6px; flex-wrap: wrap; padding: 10px 16px 14px; }
.cv-dots button { width: 8px; height: 8px; border-radius: 50%; background: var(--border); }
.cv-dots button.on { width: 22px; border-radius: 999px; background: var(--primary); }
.cv-dots span { margin-left: 8px; color: var(--muted-foreground); font-size: 12.5px; font-weight: 600; }
.cv-offscreen { position: fixed; top: 0; left: -20000px; pointer-events: none; }

@media (max-width: 980px) {
  .cv-shell { grid-template-columns: minmax(0, 1fr); height: auto; }
  .cv-stage { order: -1; height: 58vh; border-bottom: 1px solid var(--border); }
  .cv-steps { border-right: 0; overflow: visible; }
  .cv-download { width: 100%; justify-content: center; }
}
</style>
