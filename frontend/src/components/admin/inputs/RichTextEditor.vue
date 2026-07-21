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
.rich-text-editor {
  color: var(--foreground);
}

:deep(.ql-toolbar.ql-snow) {
  border-color: var(--input);
  border-radius: 0.5rem 0.5rem 0 0;
  background: var(--muted);
}

:deep(.ql-container.ql-snow) {
  border-color: var(--input);
  border-radius: 0 0 0.5rem 0.5rem;
  background: var(--card);
  color: var(--foreground);
}

:deep(.ql-editor) {
  min-height: 140px;
  background: var(--card);
  color: var(--foreground);
}

:deep(.ql-editor.ql-blank::before) {
  color: color-mix(in srgb, var(--muted-foreground) 76%, transparent);
}

:deep(.ql-snow .ql-stroke) {
  stroke: var(--muted-foreground);
}

:deep(.ql-snow .ql-fill),
:deep(.ql-snow .ql-stroke.ql-fill) {
  fill: var(--muted-foreground);
}

:deep(.ql-snow .ql-picker) {
  color: var(--muted-foreground);
}

:deep(.ql-snow button:hover .ql-stroke),
:deep(.ql-snow button:focus .ql-stroke),
:deep(.ql-snow button.ql-active .ql-stroke),
:deep(.ql-snow .ql-picker-label:hover .ql-stroke),
:deep(.ql-snow .ql-picker-label.ql-active .ql-stroke) {
  stroke: var(--primary);
}

:deep(.ql-snow button:hover .ql-fill),
:deep(.ql-snow button:focus .ql-fill),
:deep(.ql-snow button.ql-active .ql-fill) {
  fill: var(--primary);
}

:deep(.ql-toolbar.ql-snow + .ql-container.ql-snow:focus-within) {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent);
}
</style>
