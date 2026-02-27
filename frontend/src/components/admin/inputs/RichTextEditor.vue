<template>
  <div class="rich-text-editor">
    <QuillEditor
      v-model:content="contentValue"
      content-type="html"
      theme="snow"
      :placeholder="placeholder"
      :toolbar="toolbarOptions"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { QuillEditor } from "@vueup/vue-quill";
import "@vueup/vue-quill/dist/vue-quill.snow.css";

const props = defineProps<{
  modelValue?: string;
  placeholder?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

const contentValue = computed({
  get: () => props.modelValue || "",
  set: value => emit("update:modelValue", value || "")
});

const toolbarOptions = [
  ["bold", "italic", "underline"],
  [{ list: "ordered" }, { list: "bullet" }],
  [{ align: [] }],
  ["clean"]
];
</script>

<style scoped>
:deep(.ql-toolbar.ql-snow) {
  border-color: #e2e8f0;
  border-radius: 0.5rem 0.5rem 0 0;
}
:deep(.ql-container.ql-snow) {
  border-color: #e2e8f0;
  border-radius: 0 0 0.5rem 0.5rem;
  background: #fff;
}
:deep(.ql-editor) {
  min-height: 140px;
}
</style>
