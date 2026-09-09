<template>
  <div class="field media-upload-field">
    <label>{{ label }} <span class="help">?</span></label>
    <div class="media-item">
      <input :ref="setInputRef" type="file" accept="image/*" class="hidden" @change="$emit('upload', $event, field)" />
      <button type="button" class="media-thumb-button" @click="inputElement?.click()"><img v-if="preview" :src="preview" :alt="title" /><div v-else class="media-preview">IMG</div></button>
      <div class="media-info"><strong>{{ title }} <span class="help">?</span></strong><p>{{ description }}</p></div>
      <div class="btn-row"><button type="button" @click="inputElement?.click()">{{ uploading ? 'Enviando...' : (hasCustom ? 'Substituir' : 'Adicionar') }}</button><button v-if="hasCustom" type="button" class="danger" @click="$emit('remove', field)">Remover</button></div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
defineProps<{label:string;title:string;description:string;field:string;preview?:string;hasCustom?:boolean;uploading?:boolean}>();
defineEmits<{(e:"upload",event:Event,field:string):void;(e:"remove",field:string):void}>();
const inputElement=ref<HTMLInputElement|null>(null);const setInputRef=(el:any)=>{inputElement.value=el};
</script>
<style scoped>
.media-upload-field{display:grid;gap:6px}.media-upload-field>label{font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:800;color:var(--muted-foreground)}.hidden{display:none}.media-item{display:grid;grid-template-columns:86px 1fr auto;gap:12px;align-items:center;border:1px solid var(--border);background:var(--card);border-radius:12px;padding:8px}.media-thumb-button{border:0;padding:0;background:transparent;cursor:pointer}.media-thumb-button img,.media-preview{width:86px;height:58px;object-fit:cover;border-radius:8px;display:block}.media-preview{display:grid;place-items:center;background:var(--muted);color:var(--muted-foreground);font-size:12px;font-weight:700}.media-info strong{display:flex;align-items:center;gap:4px;margin-bottom:3px;font-size:13px;color:var(--foreground)}.media-info p{margin:0;color:var(--muted-foreground);font-size:12px;line-height:1.35}.help{display:inline-grid;width:16px;height:16px;place-items:center;border:1px solid var(--border);border-radius:50%;font-size:10px}.btn-row{display:flex;gap:8px;align-items:center}.btn-row button{border:1px solid var(--border);border-radius:8px;padding:7px 10px;min-height:32px;background:var(--muted);color:var(--foreground);font-size:12px;font-weight:700}.btn-row .danger{background:#fff1f1;color:#e13c3c;border-color:#ffd4d4}@media(max-width:680px){.media-item{grid-template-columns:70px 1fr}.media-thumb-button img,.media-preview{width:70px;height:52px}.btn-row{grid-column:1/-1;justify-content:flex-end}}
</style>
