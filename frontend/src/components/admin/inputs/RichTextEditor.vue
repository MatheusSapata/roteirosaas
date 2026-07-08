<template>
  <div class="rich-text-editor">
    <QuillEditor
      v-model:content="contentValue"
      content-type="html"
      theme="snow"
      :placeholder="placeholder"
      :toolbar="toolbarOptions"
      @ready="handleReady"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { QuillEditor } from "@vueup/vue-quill";
import "@vueup/vue-quill/dist/vue-quill.snow.css";
import type Quill from "quill";

const props = defineProps<{
  modelValue?: string;
  placeholder?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

const editor = ref<Quill | null>(null);
const editorRoot = ref<HTMLElement | null>(null);

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

const normalizeClipboardText = (event: ClipboardEvent) => {
  const clipboardData = event.clipboardData;
  if (!clipboardData) return "";

  const plainText = clipboardData.getData("text/plain");
  if (plainText) return plainText;

  const htmlText = clipboardData.getData("text/html");
  if (!htmlText) return "";

  const wrapper = document.createElement("div");
  wrapper.innerHTML = htmlText;
  return wrapper.textContent || "";
};

const handlePaste = (event: ClipboardEvent) => {
  if (!editor.value) return;
  if (!event.clipboardData) return;

  event.preventDefault();
  const text = normalizeClipboardText(event);
  if (text === "") return;

  const selection = editor.value.getSelection(true);
  const index = selection?.index ?? editor.value.getLength();
  editor.value.insertText(index, text, "user");
  editor.value.setSelection(index + text.length, 0, "silent");
};

const handleReady = (quill: Quill) => {
  editorRoot.value?.removeEventListener("paste", handlePaste);
  editor.value = quill;
  editorRoot.value = quill.root;
  editorRoot.value.addEventListener("paste", handlePaste);
};

onBeforeUnmount(() => {
  editorRoot.value?.removeEventListener("paste", handlePaste);
  editorRoot.value = null;
  editor.value = null;
});
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
