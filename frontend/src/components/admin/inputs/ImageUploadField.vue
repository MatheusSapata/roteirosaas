<template>
  <div class="space-y-2">
    <label v-if="label" class="text-sm font-semibold text-slate-600">{{ label }}</label>
    <div class="rounded-xl border border-slate-200 p-3">
      <div
        v-if="previewUrl"
        class="mb-3 overflow-hidden rounded-lg border border-slate-200 bg-slate-50"
      >
        <img :src="previewUrl" alt="Pré-visualização" class="h-40 w-full object-cover" />
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
          <span v-else>{{ previewUrl ? "Substituir imagem" : "Enviar imagem" }}</span>
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
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6"
      >
        <div class="w-full max-w-5xl rounded-3xl bg-white p-6 shadow-2xl">
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
import { computed, nextTick, ref, watch } from "vue";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { resolveMediaUrl, uploadImageFile } from "../../../utils/media";

const props = defineProps<{
  modelValue?: string | null;
  label?: string;
  hint?: string;
  enableCrop?: boolean;
  cropAspect?: number;
  editorTitle?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string | null): void }>();

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

const cropperModal = ref({
  open: false,
  src: "",
  originalSrc: "",
  bgEdited: false
});

const previewUrl = computed(() => resolveMediaUrl(props.modelValue));
const aspectRatio = computed(() => (typeof props.cropAspect === "number" ? props.cropAspect : NaN));
const croppingEnabled = computed(() => !!props.enableCrop);

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
    error.value = "Selecione ou crie uma agência antes de enviar imagens.";
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

const closeCropper = () => {
  cropperModal.value.open = false;
  removingBackground.value = false;
  cropping.value = false;
  pendingFile.value = null;
  dialogError.value = "";
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
          dragMode: "move",
          movable: true,
          cropBoxMovable: true,
          cropBoxResizable: true,
          zoomOnTouch: true,
          zoomOnWheel: true
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
  if (!cropperInstance.value || !pendingFile.value) return;
  cropping.value = true;
  dialogError.value = "";
  try {
    const canvas = cropperInstance.value.getCroppedCanvas({
      width: 800,
      imageSmoothingEnabled: true,
      imageSmoothingQuality: "high"
    });
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(blobInstance => {
        if (blobInstance) resolve(blobInstance);
        else reject(new Error("Falha ao gerar arquivo da logo."));
      }, "image/png", 0.95);
    });
    const baseName = pendingFile.value.name.replace(/\.[^.]+$/, "") || "logo";
    const finalFile = new File([blob], `${baseName}-edit.png`, { type: "image/png" });
    await uploadProcessedFile(finalFile);
    closeCropper();
  } catch (err) {
    console.error(err);
    dialogError.value = "Não foi possível aplicar o recorte. Tente novamente.";
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
    const result = await removeBackgroundFromDataUrl(cropperModal.value.src);
    cropperModal.value = { ...cropperModal.value, src: result, bgEdited: true };
    await nextTick();
    cropperInstance.value?.replace(result, false);
  } catch (err) {
    console.error(err);
    dialogError.value = "Não conseguimos remover o fundo desta imagem.";
  } finally {
    removingBackground.value = false;
  }
};

const removeBackgroundFromDataUrl = (src: string) => {
  return new Promise<string>((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas não suportado."));
        return;
      }
      ctx.drawImage(image, 0, 0);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const processed = stripBackground(imageData);
      ctx.putImageData(processed, 0, 0);
      resolve(canvas.toDataURL("image/png"));
    };
    image.onerror = reject;
    image.src = src;
  });
};

interface RGB {
  r: number;
  g: number;
  b: number;
}

const stripBackground = (imageData: ImageData) => {
  const { data, width, height } = imageData;
  const samples: RGB[] = [
    getColor(data, width, 0, 0),
    getColor(data, width, width - 1, 0),
    getColor(data, width, 0, height - 1),
    getColor(data, width, width - 1, height - 1),
    getColor(data, width, Math.floor(width / 2), 0),
    getColor(data, width, Math.floor(width / 2), height - 1)
  ].filter(Boolean) as RGB[];

  const base = samples.reduce(
    (acc, color) => ({ r: acc.r + color.r, g: acc.g + color.g, b: acc.b + color.b }),
    { r: 0, g: 0, b: 0 }
  );
  const safeLength = samples.length || 1;
  const baseColor = {
    r: base.r / safeLength,
    g: base.g / safeLength,
    b: base.b / safeLength
  };

  const threshold = 48;
  for (let i = 0; i < data.length; i += 4) {
    const color: RGB = { r: data[i], g: data[i + 1], b: data[i + 2] };
    const distance = colorDistance(color, baseColor);
    if (distance < threshold) {
      data[i + 3] = 0;
    }
  }
  return imageData;
};

const getColor = (data: Uint8ClampedArray, width: number, x: number, y: number): RGB => {
  const idx = (y * width + x) * 4;
  return { r: data[idx], g: data[idx + 1], b: data[idx + 2] };
};

const colorDistance = (a: RGB, b: RGB) => {
  const dr = a.r - b.r;
  const dg = a.g - b.g;
  const db = a.b - b.b;
  return Math.sqrt(dr * dr + dg * dg + db * db);
};
</script>
