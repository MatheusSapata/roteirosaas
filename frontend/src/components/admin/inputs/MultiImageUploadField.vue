<template>
  <div class="space-y-2">
    <label v-if="label" class="text-sm font-semibold text-slate-600">{{ label }}</label>
    <div class="space-y-3 rounded-xl border border-slate-200 p-3">
      <div v-if="modelValue.length" class="grid gap-3 md:grid-cols-2">
        <div
          v-for="(url, index) in modelValue"
          :key="`${url}-${index}`"
          class="overflow-hidden rounded-lg border border-slate-200 bg-slate-50"
        >
          <img :src="resolveMediaUrl(url)" alt="Imagem da galeria" class="h-36 w-full object-cover" />
          <div class="flex items-center justify-between px-3 py-2 text-xs text-slate-600">
            <span class="truncate">{{ url }}</span>
            <button class="font-semibold text-red-500" type="button" @click="removeImage(index)">Remover</button>
          </div>
        </div>
      </div>
      <label
        class="flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        <input type="file" accept="image/*" multiple class="hidden" @change="onFilesChange" />
        <span v-if="uploading">Enviando imagens...</span>
        <span v-else>Adicionar imagens</span>
      </label>
      <p v-if="hint" class="text-xs text-slate-500">{{ hint }}</p>
      <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { resolveMediaUrl, uploadImageFile } from "../../../utils/media";

const props = defineProps<{
  modelValue: string[];
  label?: string;
  hint?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string[]): void }>();

const agencyStore = useAgencyStore();
const uploading = ref(false);
const error = ref("");

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

const onFilesChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files ? Array.from(target.files) : [];
  if (!files.length) return;

  const agencyId = await ensureAgency();
  if (!agencyId) {
    error.value = "Selecione ou crie uma agência antes de enviar imagens.";
    target.value = "";
    return;
  }

  uploading.value = true;
  error.value = "";

  const uploadedUrls: string[] = [];
  try {
    for (const file of files) {
      const asset = await uploadImageFile(file, agencyId);
      uploadedUrls.push(asset.url);
    }
    const next = [...props.modelValue, ...uploadedUrls];
    emit("update:modelValue", next);
  } catch (err) {
    console.error(err);
    error.value = "Não foi possível enviar todas as imagens. Tente novamente.";
  } finally {
    uploading.value = false;
    target.value = "";
  }
};

const removeImage = (index: number) => {
  const next = props.modelValue.filter((_, i) => i !== index);
  emit("update:modelValue", next);
};
</script>
