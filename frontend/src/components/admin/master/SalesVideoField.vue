<template>
  <div class="am-card sv-card">
    <div class="am-card-head">
      <div>
        <div class="am-card-title">Vídeo da capa</div>
        <div class="am-card-sub">
          Toca na capa da página de vendas (/lp) no player próprio: prévia muda em laço com o aviso "Clique aqui para ativar o
          som" e, ao clicar, o vídeo recomeça com som e a barra de progresso. Sem vídeo aqui, a página usa o do Panda.
        </div>
      </div>
    </div>

    <div class="sv-grid">
      <!-- Prévia no mesmo formato da capa (quadrado). -->
      <div class="sv-preview">
        <VslVideoPlayer
          v-if="video"
          :src="resolveMediaUrl(video.url) || video.url"
          :poster="resolveMediaUrl(video.poster_url)"
          :color="video.color"
          title="Prévia do vídeo da capa"
        />
        <div v-else class="sv-empty">
          <AmIcon name="video" />
          <span>Nenhum vídeo enviado.<br />A página está usando o do Panda.</span>
        </div>
      </div>

      <div class="sv-side">
        <div class="sv-actions">
          <button type="button" class="am-btn am-btn-primary" :disabled="busy" @click="fileInput?.click()">
            {{ video ? "Trocar vídeo" : "Enviar vídeo" }}
          </button>
          <button v-if="video && !busy" type="button" class="am-btn am-btn-danger" @click="emit('update:modelValue', null)">Remover vídeo</button>
          <input ref="fileInput" type="file" accept="video/mp4,video/webm" class="hidden" @change="onFileChange" />
        </div>

        <div v-if="busy" class="sv-status" aria-live="polite">
          <div class="sv-status-row">
            <span>{{ stepLabel }}</span>
            <b v-if="step === 'upload'">{{ Math.round(progress * 100) }}%</b>
          </div>
          <div class="am-bar"><i :style="{ width: `${step === 'upload' ? progress * 100 : 4}%` }"></i></div>
          <p class="sv-note">Não feche esta tela até terminar.</p>
        </div>
        <p v-else-if="error" class="sv-error" role="alert">{{ error }}</p>
        <p v-else-if="justUploaded" class="sv-ok" role="status">Vídeo enviado. Clique em "Salvar alterações" para publicar na página.</p>

        <div v-if="video" class="sv-meta">
          <span v-if="video.width && video.height">{{ video.width }} × {{ video.height }} px</span>
          <span v-if="video.width && video.height" class="am-badge am-dot" :class="isSquare ? 'am-tone-success' : 'am-tone-warning'">
            {{ isSquare ? "Quadrado, como a capa" : "Fora do quadrado: a capa corta as bordas" }}
          </span>
        </div>

        <ImageUploadField
          v-if="video"
          :model-value="video.poster_url || null"
          label="Capa"
          hint="Aparece enquanto o vídeo carrega. Ao enviar um vídeo, a capa vira o primeiro quadro dele."
          layout="row"
          replace-label="Trocar"
          :enable-crop="true"
          :crop-aspect="1"
          editor-title="Ajuste a capa do vídeo"
          @update:model-value="patch({ poster_url: $event })"
        />

        <div v-if="video" class="am-field">
          <label for="sv-color">Cor do aviso de som e da barra</label>
          <div class="sv-color">
            <input id="sv-color" type="color" :value="video.color || DEFAULT_COLOR" @input="patch({ color: ($event.target as HTMLInputElement).value })" />
            <span class="sv-color-code">{{ (video.color || DEFAULT_COLOR).toUpperCase() }}</span>
            <button v-if="video.color" type="button" class="am-btn am-btn-sm" @click="patch({ color: null })">Usar a padrão</button>
          </div>
        </div>

        <p class="sv-note">
          MP4 (H.264) ou WebM, até 300 MB, de preferência quadrado (1080 × 1080). Para abrir rápido no celular, exporte em
          1080p ou 720p. O vídeo é preparado no navegador para começar a tocar antes de baixar inteiro.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onBeforeUnmount, ref } from "vue";
import AmIcon from "./AmIcon.vue";
import ImageUploadField from "../inputs/ImageUploadField.vue";
import VslVideoPlayer from "../../public/VslVideoPlayer.vue";
import { uploadSalesVideo, type SalesVideo } from "../../../services/checkout";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { resolveMediaUrl, uploadImageFile } from "../../../utils/media";
import { mp4Faststart } from "../../../utils/mp4Faststart";

const props = defineProps<{ modelValue: SalesVideo | null }>();
const emit = defineEmits<{ (event: "update:modelValue", value: SalesVideo | null): void }>();

const DEFAULT_COLOR = "#12B981";
const MAX_BYTES = 300 * 1024 * 1024;
const TYPES = ["video/mp4", "video/webm"];

const agencyStore = useAgencyStore();
const fileInput = ref<HTMLInputElement | null>(null);
const step = ref<"idle" | "read" | "prepare" | "upload" | "poster">("idle");
const progress = ref(0);
const error = ref("");
const justUploaded = ref(false);

const video = computed(() => props.modelValue);
const busy = computed(() => step.value !== "idle");
const isSquare = computed(() => {
  const { width, height } = video.value || {};
  return Boolean(width && height && Math.abs(width / height - 1) < 0.02);
});
const stepLabel = computed(
  () =>
    ({
      idle: "",
      read: "Lendo o vídeo...",
      prepare: "Preparando para tocar rápido...",
      upload: "Enviando o vídeo...",
      poster: "Gerando a capa..."
    })[step.value]
);

const patch = (changes: Partial<SalesVideo>) => {
  if (!video.value) return;
  emit("update:modelValue", { ...video.value, ...changes });
};

type VideoInfo = { width: number; height: number; poster: Blob | null };

/** Abre o vídeo no navegador: tamanho e o primeiro quadro (vira a capa). Se nem aqui abre, o
 *  visitante também não vai conseguir assistir. */
const readVideo = (file: File): Promise<VideoInfo> =>
  new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const element = document.createElement("video");
    // Codec que o navegador não abre às vezes nem dá erro: depois de 20 s, desiste.
    const timer = window.setTimeout(() => finish(new Error("Este navegador não conseguiu abrir o vídeo. Exporte em MP4 (H.264) e envie de novo.")), 20000);
    const finish = (result: VideoInfo | Error) => {
      window.clearTimeout(timer);
      element.onloadeddata = null;
      element.onerror = null;
      element.removeAttribute("src");
      element.load();
      URL.revokeObjectURL(url);
      if (result instanceof Error) reject(result);
      else resolve(result);
    };
    element.muted = true;
    element.playsInline = true;
    element.preload = "auto";
    element.onerror = () => finish(new Error("Este navegador não conseguiu abrir o vídeo. Exporte em MP4 (H.264) e envie de novo."));
    element.onloadeddata = () => {
      const width = element.videoWidth;
      const height = element.videoHeight;
      if (!width || !height) {
        finish(new Error("O arquivo não tem imagem de vídeo."));
        return;
      }
      const scale = Math.min(1, 1080 / Math.max(width, height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
      try {
        canvas.getContext("2d")?.drawImage(element, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(poster => finish({ width, height, poster }), "image/jpeg", 0.88);
      } catch {
        finish({ width, height, poster: null });
      }
    };
    element.src = url;
  });

const uploadPoster = async (poster: Blob | null): Promise<string | null> => {
  if (!poster) return null;
  try {
    if (!agencyStore.currentAgencyId) await agencyStore.loadAgencies();
    const agencyId = agencyStore.currentAgencyId;
    if (!agencyId) return null;
    const asset = await uploadImageFile(new File([poster], "capa-video.jpg", { type: "image/jpeg" }), agencyId);
    return asset.url;
  } catch {
    // Sem capa o vídeo funciona igual (mostra o primeiro quadro quando carrega).
    return null;
  }
};

// Erro do servidor: a mensagem dele; erro ao abrir o vídeo aqui: a nossa; o resto: a genérica.
const errorMessage = (err: unknown, fallback: string) => {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    return typeof detail === "string" && detail ? detail : fallback;
  }
  return err instanceof Error && err.message ? err.message : fallback;
};

const onFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  error.value = "";
  justUploaded.value = false;
  if (!TYPES.includes(file.type)) {
    error.value = "Envie o vídeo em MP4 ou WebM.";
    return;
  }
  if (file.size > MAX_BYTES) {
    error.value = "O vídeo passa de 300 MB. Exporte em 1080p ou 720p e envie de novo.";
    return;
  }
  try {
    step.value = "read";
    const info = await readVideo(file);
    step.value = "prepare";
    const ready = file.type === "video/mp4" ? await mp4Faststart(file) : file;
    step.value = "upload";
    progress.value = 0;
    const url = await uploadSalesVideo(ready, fraction => (progress.value = fraction));
    step.value = "poster";
    const posterUrl = await uploadPoster(info.poster);
    emit("update:modelValue", { url, poster_url: posterUrl, width: info.width, height: info.height, color: video.value?.color || null });
    justUploaded.value = true;
  } catch (err) {
    error.value = errorMessage(err, "Não foi possível enviar o vídeo. Confira a internet e tente de novo.");
  } finally {
    step.value = "idle";
  }
};

// Sair da tela no meio do envio perde o vídeo: o navegador pergunta antes.
const warnBeforeLeaving = (event: BeforeUnloadEvent) => {
  if (!busy.value) return;
  event.preventDefault();
  event.returnValue = "";
};
window.addEventListener("beforeunload", warnBeforeLeaving);
onBeforeUnmount(() => window.removeEventListener("beforeunload", warnBeforeLeaving));
</script>

<style scoped>
.sv-grid {
  display: grid;
  grid-template-columns: minmax(0, 340px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
.sv-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: #0c100e;
}
.sv-empty {
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  text-align: center;
}
.sv-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.sv-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.sv-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sv-status-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--foreground);
}
.sv-status .am-bar > i {
  transition: width 0.3s ease;
}
.sv-note {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--muted-foreground);
}
.sv-error {
  font-size: 13px;
  font-weight: 600;
  color: var(--status-danger-foreground);
}
.sv-ok {
  font-size: 13px;
  font-weight: 600;
  color: var(--status-success-foreground);
}
.sv-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--muted-foreground);
}
.sv-color {
  display: flex;
  align-items: center;
  gap: 10px;
}
.sv-color input[type="color"] {
  width: 44px;
  height: 36px;
  padding: 2px;
  border: 1px solid var(--input);
  border-radius: 10px;
  background: var(--background);
  cursor: pointer;
}
.sv-color-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
  color: var(--foreground);
}
@media (max-width: 860px) {
  .sv-grid {
    grid-template-columns: 1fr;
  }
  .sv-preview {
    max-width: 340px;
  }
}
</style>
