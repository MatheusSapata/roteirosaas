<template>
  <div class="image-upload-field flex h-full flex-col gap-2">
    <div v-if="label" class="space-y-1">
      <label class="text-sm font-semibold text-slate-600">{{ label }}</label>
      <p v-if="labelDescription" class="text-xs text-slate-500">{{ labelDescription }}</p>
    </div>
    <div
      v-if="props.layout === 'row'"
      class="flex flex-1 items-center gap-3 rounded-xl border border-slate-200 p-3"
    >
      <button
        type="button"
        class="h-16 w-24 shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-slate-100"
        @click="previewUrl && croppingEnabled ? openCropperForCurrent() : openFileDialog()"
      >
        <img v-if="previewUrl" :src="previewUrl" alt="Pré-visualização" class="h-full w-full object-cover" />
        <span v-else class="inline-flex h-full w-full items-center justify-center text-xs font-semibold text-slate-500">IMG</span>
      </button>
      <div class="min-w-0 flex-1">
        <p v-if="hint" class="text-xs text-slate-500">{{ hint }}</p>
        <p v-if="error" class="mt-1 text-xs text-red-500">{{ error }}</p>
      </div>
      <div class="flex w-[220px] shrink-0 items-center justify-end gap-2">
        <label
          class="inline-flex h-10 w-[106px] cursor-pointer items-center justify-center rounded-lg border border-dashed border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onFileChange"
          />
          <span v-if="uploading">Enviando...</span>
          <span v-else>{{ previewUrl ? (props.replaceLabel || "Substituir") : "Adicionar" }}</span>
        </label>
        <button
          type="button"
          class="h-10 w-[96px] rounded-lg border px-3 text-sm font-semibold transition"
          :class="modelValue ? 'border-red-200 text-red-500 hover:bg-red-50' : 'pointer-events-none border-slate-200 text-transparent'"
          @click="clearImage"
        >
          Remover
        </button>
      </div>
    </div>
    <div v-else class="flex flex-1 flex-col rounded-xl border border-slate-200 p-3">
      <div v-if="previewUrl" class="mb-3">
        <div
          v-if="supportsRounded"
          class="flex w-full items-center justify-center"
        >
          <div :style="previewRoundedBoxStyle">
            <img :src="previewUrl" alt="Pré-visualização" :style="previewRoundedImageStyle" />
          </div>
        </div>
        <div
          v-else
          class="flex max-h-[320px] min-h-[220px] w-full items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-slate-50"
        >
          <img :src="previewUrl" alt="Pré-visualização" class="image-upload-preview h-full min-h-[220px] w-full object-cover" />
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <label
          class="inline-flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onFileChange"
          />
          <span v-if="uploading">Enviando...</span>
          <span v-else>{{ previewUrl ? (props.replaceLabel || "Substituir imagem") : "Enviar imagem" }}</span>
        </label>
        <button
          v-if="modelValue"
          type="button"
          class="text-sm font-semibold text-red-500"
          @click="clearImage"
        >
          Remover
        </button>
      </div>
      <p v-if="hint" class="text-xs text-slate-500">{{ hint }}</p>
      <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
    </div>
    <transition name="fade">
      <div
        v-if="cropperModal.open"
        class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
      >
        <div class="image-editor-modal w-full max-w-5xl p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Editor de logo</p>
              <h3 class="text-2xl font-bold text-slate-900">
                {{ editorTitle || "Ajuste sua marca" }}
              </h3>
              <p class="text-sm text-slate-500">Corte, limpe o fundo e envie com acabamento profissional.</p>
            </div>
            <button type="button" class="text-sm font-semibold text-slate-500" @click="closeCropper">
              Fechar
            </button>
          </div>
          <div class="mt-6 grid gap-6 md:grid-cols-[minmax(0,1fr)_220px]">
            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <img
                ref="cropperImage"
                :src="cropperModal.src"
                alt="Editor"
                class="max-h-[420px] w-full rounded-xl bg-white object-contain"
              />
            </div>
            <div class="space-y-4">
              <p class="text-xs text-slate-500">
                Use as ações abaixo para remover fundo, aproximar ou reposicionar a logo antes de salvar.
              </p>
              <div class="space-y-2">
                <button
                  type="button"
                  class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  @click="handleRemoveBackground"
                  :disabled="removingBackground"
                >
                  {{ removingBackground ? "Processando fundo..." : "Remover fundo" }}
                </button>
                <button
                  type="button"
                  class="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="!cropperModal.bgEdited"
                  @click="restoreOriginal"
                >
                  Restaurar imagem
                </button>
              </div>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="zoom(-0.2)"
                >
                  -
                </button>
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="zoom(0.2)"
                >
                  +
                </button>
              </div>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="rotate(-10)"
                >
                  Rotacionar -
                </button>
                <button
                  type="button"
                  class="flex-1 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="rotate(10)"
                >
                  Rotacionar +
                </button>
              </div>
              <div v-if="supportsRounded" class="space-y-2 rounded-xl border border-dashed border-slate-200/80 bg-slate-50/70 p-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-semibold text-slate-600">Arredondar logo</span>
                  <span class="text-xs font-semibold text-slate-500">{{ Math.round(roundedControl) }} px</span>
                </div>
                <div class="flex items-center gap-3">
                  <input
                    type="range"
                    class="flex-1 accent-brand"
                    min="0"
                    :max="roundedMaxValue"
                    step="2"
                    v-model.number="roundedControl"
                  />
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                    @click="roundedControl = circleTarget"
                  >
                    Circular
                  </button>
                </div>
                <div class="space-y-1">
                  <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Prévia final</p>
                  <div class="flex justify-center">
                    <div :style="previewRoundedBoxStyle">
                      <img :src="roundedPreviewSrc" alt="Prévia" :style="previewRoundedImageStyle" />
                    </div>
                  </div>
                </div>
              </div>
              <p v-if="dialogError" class="text-xs text-red-500">{{ dialogError }}</p>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3">
            <button
              type="button"
              class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="closeCropper"
            >
              Cancelar
            </button>
            <button
              type="button"
              class="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="cropping"
              @click="confirmCrop"
            >
              {{ cropping ? "Aplicando..." : "Aplicar recorte" }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import Cropper from "cropperjs";
import "cropperjs/dist/cropper.css";
import { computed, inject, nextTick, onBeforeUnmount, ref, watch } from "vue";
import api from "../../../services/api";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { removeImageBackground, resolveMediaUrl, uploadImageFile } from "../../../utils/media";
import { sectionUploadGuardKey } from "../sectionUploadGuard";

const props = defineProps<{
  modelValue?: string | null;
  label?: string;
  labelDescription?: string;
  hint?: string;
  replaceLabel?: string;
  enableCrop?: boolean;
  cropAspect?: number;
  editorTitle?: string;
  roundedValue?: number;
  roundedMax?: number;
  layout?: "card" | "row";
}>();
const emit = defineEmits<{
  (e: "update:modelValue", value: string | null): void;
  (e: "update:roundedValue", value: number): void;
}>();

const agencyStore = useAgencyStore();
const uploading = ref(false);
const cropping = ref(false);
const removingBackground = ref(false);
const error = ref("");
const dialogError = ref("");
const fileInput = ref<HTMLInputElement | null>(null);
const cropperImage = ref<HTMLImageElement | null>(null);
const cropperInstance = ref<Cropper | null>(null);
const pendingFile = ref<File | null>(null);
const cropperObjectUrl = ref<string | null>(null);
const sectionUploadGuard = inject(sectionUploadGuardKey, null);
const uploadToken = Symbol("image-upload-field");

const roundedControl = ref(props.roundedValue ?? 0);
const supportsRounded = computed(() => typeof props.roundedMax === "number");
const roundedMaxValue = computed(() => {
  if (typeof props.roundedMax === "number") {
    return Math.max(0, props.roundedMax);
  }
  return 0;
});
const circleTarget = computed(() => roundedMaxValue.value || 0);
const previewBoxHeight = 160;
const previewSquareStyle = {
  width: "100%",
  height: `${previewBoxHeight}px`
};
const previewRoundedPixels = computed(() => {
  if (!supportsRounded.value || !roundedMaxValue.value) return roundedControl.value || 0;
  const max = previewBoxHeight / 2;
  return Math.min(max, (roundedControl.value / roundedMaxValue.value) * max);
});

watch(
  () => props.roundedValue,
  value => {
    const normalized = typeof value === "number" ? value : 0;
    if (normalized !== roundedControl.value) {
      roundedControl.value = normalized;
    }
  }
);

watch(uploading, value => {
  if (!sectionUploadGuard) return;
  sectionUploadGuard.setUploading(uploadToken, Boolean(value));
});

onBeforeUnmount(() => {
  sectionUploadGuard?.setUploading(uploadToken, false);
  revokeCropperObjectUrl();
});

watch(roundedControl, value => {
  if (supportsRounded.value) {
    const clamped = Math.min(roundedMaxValue.value, Math.max(0, value || 0));
    if (clamped !== value) {
      roundedControl.value = clamped;
      return;
    }
    emit("update:roundedValue", clamped);
  }
});

watch(
  () => props.roundedMax,
  max => {
    if (typeof max === "number" && roundedControl.value > max) {
      roundedControl.value = max;
    }
  }
);

const cropperModal = ref({
  open: false,
  src: "",
  originalSrc: "",
  bgEdited: false
});

const previewUrl = computed(() => resolveMediaUrl(props.modelValue));
const roundedPreviewSrc = computed(() => {
  if (cropperModal.value.open && cropperModal.value.src) {
    return cropperModal.value.src;
  }
  return previewUrl.value || "";
});
const aspectRatio = computed(() => (typeof props.cropAspect === "number" ? props.cropAspect : NaN));
const croppingEnabled = computed(() => !!props.enableCrop);
const previewRoundedBoxStyle = computed(() => {
  if (!supportsRounded.value) return {};
  return {
    ...previewSquareStyle,
    borderRadius: `${previewRoundedPixels.value}px`,
    border: "1px solid #e2e8f0",
    background: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "inset 0 0 0 1px rgba(15,23,42,0.04)"
  };
});
const previewRoundedImageStyle = computed(() => {
  if (!supportsRounded.value) return {};
  return {
    maxWidth: "85%",
    maxHeight: "85%",
    objectFit: "contain",
    borderRadius: `${previewRoundedPixels.value}px`
  };
});

const ensureAgency = async () => {
  if (!agencyStore.currentAgencyId) {
    try {
      await agencyStore.loadAgencies();
    } catch {
      /* ignore */
    }
  }
  return agencyStore.currentAgencyId;
};

const resetFileInput = () => {
  if (fileInput.value) {
    fileInput.value.value = "";
  }
};

const uploadProcessedFile = async (file: File) => {
  const agencyId = await ensureAgency();
  if (!agencyId) {
    error.value = "Selecione ou crie uma agÃªncia antes de enviar imagens.";
    return;
  }

  uploading.value = true;
  error.value = "";
  try {
    const asset = await uploadImageFile(file, agencyId);
    emit("update:modelValue", asset.url);
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível enviar a imagem. Tente novamente.";
  } finally {
    uploading.value = false;
  }
};

const onFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  if (croppingEnabled.value) {
    const reader = new FileReader();
    pendingFile.value = file;
    reader.onload = () => {
      cropperModal.value = {
        open: true,
        src: reader.result as string,
        originalSrc: reader.result as string,
        bgEdited: false
      };
      dialogError.value = "";
    };
    reader.readAsDataURL(file);
    resetFileInput();
    return;
  }

  await uploadProcessedFile(file);
  resetFileInput();
};

const clearImage = () => {
  emit("update:modelValue", "");
  pendingFile.value = null;
};

const openFileDialog = () => {
  fileInput.value?.click();
};

const revokeCropperObjectUrl = () => {
  if (cropperObjectUrl.value) {
    URL.revokeObjectURL(cropperObjectUrl.value);
    cropperObjectUrl.value = null;
  }
};

const openCropperForCurrent = async () => {
  if (!croppingEnabled.value || !previewUrl.value) return;
  let src = previewUrl.value;
  let loadedFromProxy = false;
  const proxyCandidates = [previewUrl.value, props.modelValue || ""].filter(Boolean) as string[];
  try {
    revokeCropperObjectUrl();
    for (const candidateUrl of proxyCandidates) {
      try {
        const response = await api.get("/media/proxy", {
          params: { url: candidateUrl },
          responseType: "blob"
        });
        if (response?.data instanceof Blob) {
          cropperObjectUrl.value = URL.createObjectURL(response.data);
          src = cropperObjectUrl.value;
          loadedFromProxy = true;
          break;
        }
      } catch {
        // tenta próximo formato de URL
      }
    }
  } catch {
    // fallback para URL direta
  }
  if (!loadedFromProxy && /^https?:\/\//i.test(previewUrl.value)) {
    dialogError.value = "Não foi possível carregar a imagem para recorte. Tente substituir a imagem.";
    return;
  }
  cropperModal.value = {
    open: true,
    src,
    originalSrc: src,
    bgEdited: false
  };
  dialogError.value = "";
};

const closeCropper = () => {
  cropperModal.value.open = false;
  removingBackground.value = false;
  cropping.value = false;
  pendingFile.value = null;
  dialogError.value = "";
  revokeCropperObjectUrl();
};

watch(
  () => cropperModal.value.open,
  async opened => {
    if (!croppingEnabled.value) return;
    if (opened) {
      await nextTick();
      if (cropperImage.value) {
        cropperInstance.value?.destroy();
        const options: Cropper.Options = {
          viewMode: 1,
          background: false,
          autoCropArea: 0.85,
          autoCrop: true,
          dragMode: "move",
          movable: true,
          cropBoxMovable: true,
          cropBoxResizable: true,
          zoomOnTouch: true,
          zoomOnWheel: true,
          checkCrossOrigin: false,
          checkOrientation: false,
          ready() {
            const cropper = cropperInstance.value;
            if (!cropper) return;
            cropper.crop();
            const ratio = aspectRatio.value;
            const canvas = cropper.getCanvasData();
            const targetArea = 0.9;
            let width = canvas.width * targetArea;
            let height = canvas.height * targetArea;
            if (!Number.isNaN(ratio) && ratio > 0) {
              if (width / height > ratio) {
                width = height * ratio;
              } else {
                height = width / ratio;
              }
            }
            cropper.setCropBoxData({
              left: canvas.left + (canvas.width - width) / 2,
              top: canvas.top + (canvas.height - height) / 2,
              width,
              height
            });
          }
        };
        if (!Number.isNaN(aspectRatio.value)) {
          options.aspectRatio = aspectRatio.value;
        }
        cropperInstance.value = new Cropper(cropperImage.value, options);
      }
    } else {
      cropperInstance.value?.destroy();
      cropperInstance.value = null;
    }
  }
);

const confirmCrop = async () => {
  if (!cropperInstance.value) return;
  cropping.value = true;
  dialogError.value = "";
  try {
    const isSquareCrop = !Number.isNaN(aspectRatio.value) && Math.abs(aspectRatio.value - 1) < 0.001;
    const canvas = cropperInstance.value.getCroppedCanvas({
      ...(isSquareCrop ? { width: 512, height: 512 } : { maxWidth: 2560, maxHeight: 2560 }),
      imageSmoothingEnabled: true,
      imageSmoothingQuality: "high"
    });
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(blobInstance => {
        if (blobInstance) resolve(blobInstance);
        else reject(new Error("Falha ao gerar arquivo da logo."));
      }, "image/png", 0.95);
    });
    const baseName = pendingFile.value?.name.replace(/\.[^.]+$/, "") || "image";
    const finalFile = new File([blob], `${baseName}-edit.png`, { type: "image/png" });
    await uploadProcessedFile(finalFile);
    closeCropper();
  } catch (err) {
    console.error(err);
    const message = err instanceof Error ? err.message : "";
    if (message.includes("Tainted canvases")) {
      dialogError.value = "Não foi possível recortar esta imagem por bloqueio CORS no servidor da mídia.";
    } else {
      dialogError.value = "Não foi possível aplicar o recorte. Tente novamente.";
    }
  } finally {
    cropping.value = false;
  }
};

const zoom = (value: number) => {
  cropperInstance.value?.zoom(value);
};

const rotate = (value: number) => {
  cropperInstance.value?.rotate(value);
};

const restoreOriginal = () => {
  if (!cropperInstance.value) return;
  cropperInstance.value.replace(cropperModal.value.originalSrc, false);
  cropperModal.value = {
    ...cropperModal.value,
    src: cropperModal.value.originalSrc,
    bgEdited: false
  };
};

const handleRemoveBackground = async () => {
  if (!cropperModal.value.src || removingBackground.value) return;
  removingBackground.value = true;
  dialogError.value = "";
  try {
    const agencyId = await ensureAgency();
    if (!agencyId) throw new Error("Agência não encontrada.");
    const result = await removeImageBackground(cropperModal.value.src, agencyId);
    cropperModal.value = { ...cropperModal.value, src: result, bgEdited: true };
    await nextTick();
    cropperInstance.value?.replace(result, false);
  } catch (err) {
    console.error(err);
    dialogError.value = "Não conseguimos remover o fundo. Verifique a imagem e tente novamente.";
  } finally {
    removingBackground.value = false;
  }
};

defineExpose({
  openFileDialog,
  openCropperForCurrent
});
</script>

<style scoped>
.image-upload-field {
  color: var(--foreground);
}

.image-upload-field :deep(.border-slate-200),
.image-upload-field :deep(.border-slate-200\/80),
.image-upload-field :deep(.border-slate-300) {
  border-color: var(--border) !important;
}

.image-upload-field :deep(.bg-white) {
  background-color: var(--card) !important;
}

.image-upload-field :deep(.bg-slate-50),
.image-upload-field :deep(.bg-slate-50\/70),
.image-upload-field :deep(.bg-slate-100) {
  background-color: var(--muted) !important;
}

.image-upload-field :deep(.text-slate-900),
.image-upload-field :deep(.text-slate-800),
.image-upload-field :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.image-upload-field :deep(.text-slate-600),
.image-upload-field :deep(.text-slate-500),
.image-upload-field :deep(.text-slate-400) {
  color: var(--muted-foreground) !important;
}

.image-upload-field :deep(label:hover),
.image-upload-field :deep(button:hover) {
  background-color: var(--accent);
}

.image-editor-modal {
  border: 1px solid var(--border);
  border-radius: var(--radius-2xl);
  background: var(--card);
  color: var(--card-foreground);
  box-shadow: var(--shadow-elegant);
}

.image-editor-modal :deep(.border-slate-200),
.image-editor-modal :deep(.border-slate-200\/80) {
  border-color: var(--border) !important;
}

.image-editor-modal :deep(.bg-white) {
  background-color: var(--card) !important;
}

.image-editor-modal :deep(.bg-slate-50),
.image-editor-modal :deep(.bg-slate-50\/70),
.image-editor-modal :deep(.bg-slate-100) {
  background-color: var(--muted) !important;
}

.image-editor-modal :deep(.text-slate-900),
.image-editor-modal :deep(.text-slate-800),
.image-editor-modal :deep(.text-slate-700) {
  color: var(--foreground) !important;
}

.image-editor-modal :deep(.text-slate-600),
.image-editor-modal :deep(.text-slate-500),
.image-editor-modal :deep(.text-slate-400) {
  color: var(--muted-foreground) !important;
}
</style>

