<template>
  <div class="rich-text-editor">
    <div ref="editorHost"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import Quill, { type EmitterSource } from "quill";
import "quill/dist/quill.snow.css";

type EditorDelta = ReturnType<Quill["getContents"]>;

const props = defineProps<{
  modelValue?: string;
  placeholder?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

const editorHost = ref<HTMLElement | null>(null);
let editor: Quill | null = null;
let lastEmittedValue = "";

const toolbarOptions = [
  ["bold", "italic", "underline"],
  [{ list: "ordered" }, { list: "bullet" }],
  [{ align: [] }],
  ["clean"]
];

const serializeEditorHtml = () => {
  if (!editor) return "";

  const lineAlignments: Array<string | undefined> = [];
  let hasAlignedLine = false;
  editor.getContents().eachLine((_line, attributes) => {
    const alignment = typeof attributes.align === "string" ? attributes.align : undefined;
    lineAlignments.push(alignment);
    hasAlignedLine ||= !!alignment;
  });

  const html = editor.getSemanticHTML();
  if (!hasAlignedLine) return html;

  // Quill 2 omits alignment from list items in getSemanticHTML(). Restore it
  // from the Delta so saved list formatting matches what the user sees.
  const wrapper = document.createElement("div");
  wrapper.innerHTML = html;
  const blocks = wrapper.querySelectorAll<HTMLElement>("p, li");
  const supportedAlignments = new Set(["left", "center", "right", "justify"]);
  blocks.forEach((block, index) => {
    const alignment = lineAlignments[index];
    if (alignment && supportedAlignments.has(alignment)) {
      block.classList.add(`ql-align-${alignment}`);
    }
  });
  return wrapper.innerHTML;
};

const getEditorValue = () => {
  if (!editor || editor.getLength() <= 1) return "";
  return serializeEditorHtml();
};

const ensureTerminalNewline = (delta: EditorDelta) => {
  const lastOperation = delta.ops[delta.ops.length - 1];
  const endsWithNewline =
    typeof lastOperation?.insert === "string" && lastOperation.insert.endsWith("\n");

  return endsWithNewline ? delta : delta.insert("\n");
};

const convertHtml = (value?: string) => {
  if (!editor || !value) return null;
  return ensureTerminalNewline(editor.clipboard.convert({ html: value, text: "" }));
};

const contentsEqual = (incoming: EditorDelta) => {
  if (!editor) return true;
  return editor.getContents().diff(incoming).ops.length === 0;
};

const syncEditorContent = (value?: string) => {
  if (!editor) return;

  const range = editor.getSelection();
  const incoming = convertHtml(value);

  if (!incoming || incoming.length() <= 1) {
    if (editor.getLength() <= 1) return;
    editor.setText("", "silent");
  } else {
    if (contentsEqual(incoming)) return;
    editor.setContents(incoming, "silent");
  }

  lastEmittedValue = getEditorValue();

  if (range && editor.hasFocus()) {
    const maxIndex = Math.max(0, editor.getLength() - 1);
    const index = Math.min(range.index, maxIndex);
    const length = Math.min(range.length, maxIndex - index);
    editor.setSelection(index, length, "silent");
  }
};

const handleTextChange = (_delta: EditorDelta, _oldContents: EditorDelta, source: EmitterSource) => {
  if (source === "silent") return;
  const value = getEditorValue();
  if (value === lastEmittedValue) return;
  lastEmittedValue = value;
  emit("update:modelValue", value);
};

onMounted(() => {
  if (!editorHost.value) return;

  editor = new Quill(editorHost.value, {
    theme: "snow",
    placeholder: props.placeholder || "",
    modules: {
      toolbar: toolbarOptions,
      history: { userOnly: true }
    },
    formats: ["bold", "italic", "underline", "list", "indent", "align"]
  });

  syncEditorContent(props.modelValue);
  lastEmittedValue = getEditorValue();
  editor.on("text-change", handleTextChange);
});

watch(
  () => props.modelValue,
  value => {
    if (!editor) return;
    if ((value || "") === lastEmittedValue) return;
    syncEditorContent(value);
  }
);

watch(
  () => props.placeholder,
  value => {
    if (!editor) return;
    editor.root.dataset.placeholder = value || "";
  }
);

onBeforeUnmount(() => {
  editor?.off("text-change", handleTextChange);
  editor = null;
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
