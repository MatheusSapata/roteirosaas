<template>
  <div class="rich-text-editor">
    <QuillEditor
      content-type="html"
      theme="snow"
      :placeholder="placeholder"
      :toolbar="toolbarOptions"
      @ready="handleReady"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { Delta, QuillEditor } from "@vueup/vue-quill";
import "@vueup/vue-quill/dist/vue-quill.snow.css";
import type Quill from "quill";
import type { RangeStatic } from "quill";

const props = defineProps<{
  modelValue?: string;
  placeholder?: string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

const editor = ref<Quill | null>(null);
const editorRoot = ref<HTMLElement | null>(null);
const lastSelection = ref<RangeStatic | null>(null);
let lastEmittedValue = "";
let selectAllRequested = false;

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
  if (plainText) return cleanClipboardText(plainText);

  const htmlText = clipboardData.getData("text/html");
  if (!htmlText) return "";

  const wrapper = document.createElement("div");
  wrapper.innerHTML = htmlText;
  return cleanClipboardText(wrapper.textContent || "");
};

// Some editors put a BOM/zero-width space in copied text. In Quill these can
// look like an empty character and make Backspace appear to do nothing.
const cleanClipboardText = (value: string) =>
  value.replace(/\r\n?/g, "\n").replace(/[\u200B\uFEFF]/g, "");

const handleSelectionChange = (range: RangeStatic | null) => {
  if (!range) return;
  lastSelection.value = { index: range.index, length: range.length };
};

const normalizeSelectionText = (value: string) =>
  value.normalize("NFC").replace(/[\s\u00A0\u200B\uFEFF]/g, "");

const isAllBrowserTextSelected = () => {
  if (!editor.value) return false;
  const contentLength = Math.max(0, editor.value.getLength() - 1);
  const editorText = normalizeSelectionText(editor.value.getText(0, contentLength));
  const browserSelection = window.getSelection();
  const anchorInsideEditor = !!browserSelection?.anchorNode && editor.value.root.contains(browserSelection.anchorNode);
  const focusInsideEditor = !!browserSelection?.focusNode && editor.value.root.contains(browserSelection.focusNode);
  const selectedText = normalizeSelectionText(browserSelection?.toString() || "");
  return anchorInsideEditor && focusInsideEditor && editorText.length > 0 && selectedText === editorText;
};

const hasMeaningfulContent = () => {
  if (!editor.value) return false;
  return editor.value
    .getText()
    .replace(/[\s\u00A0\u200B\uFEFF]/g, "")
    .length > 0;
};

const updateBlankState = () => {
  editor.value?.root.classList.toggle("ql-blank", !hasMeaningfulContent());
};

const getEditorValue = () => {
  if (!editor.value || !hasMeaningfulContent()) return "";
  return editor.value.root.innerHTML;
};

const emitEditorValue = () => {
  const value = getEditorValue();
  if (value === lastEmittedValue) return;
  lastEmittedValue = value;
  emit("update:modelValue", value);
};

const handleTextChange = (_delta: unknown, _oldContents: unknown, source: string) => {
  if (source === "silent") return;

  // Quill always retains a terminal newline. Copied content may also leave
  // spaces or invisible characters behind, so explicitly collapse a visually
  // empty document to Quill's canonical empty state.
  if (!hasMeaningfulContent()) {
    editor.value?.setText("", "silent");
  }

  updateBlankState();
  emitEditorValue();
};

const syncEditorContent = (value?: string) => {
  const quill = editor.value;
  if (!quill) return;

  const nextValue = value || "";
  if (nextValue === getEditorValue()) return;

  if (!nextValue) {
    quill.setText("", "silent");
  } else {
    quill.setContents(quill.clipboard.convert(nextValue), "silent");
  }
  updateBlankState();
  lastEmittedValue = getEditorValue();
};

const handlePaste = (event: ClipboardEvent) => {
  if (!editor.value) return;
  if (!event.clipboardData) return;

  // This listener runs in the capture phase so Quill's own clipboard handler
  // cannot process the same paste a second time using a stale selection.
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();

  const text = normalizeClipboardText(event);
  if (text === "") return;

  const browserSelectedAll = selectAllRequested || isAllBrowserTextSelected();
  // Do not call getSelection(true) here. Refocusing the editor during a paste
  // can collapse a selected range and make the text land at an older cursor.
  const selection = editor.value.getSelection() || lastSelection.value;
  const documentEnd = Math.max(0, editor.value.getLength() - 1);
  const index = browserSelectedAll ? 0 : Math.min(selection?.index ?? documentEnd, documentEnd);
  const selectedLength = browserSelectedAll
    ? documentEnd
    : Math.min(selection?.length ?? 0, documentEnd - index);

  // Replace the selection in one Quill transaction. Emitting a deletion and
  // insertion separately lets the empty intermediate value reach the parent
  // when the whole editor is selected, which can cancel the insertion.
  const change = new Delta().retain(index).delete(selectedLength).insert(text);
  editor.value.updateContents(change, "user");
  editor.value.setSelection(index + text.length, 0, "silent");
  lastSelection.value = { index: index + text.length, length: 0 };
  selectAllRequested = false;
  emitEditorValue();
};

const handleKeydown = (event: KeyboardEvent) => {
  if (!editor.value) return;

  const isSelectAllShortcut =
    (event.ctrlKey || event.metaKey) &&
    !event.altKey &&
    event.key.toLowerCase() === "a";

  if (isSelectAllShortcut) {
    selectAllRequested = true;
    return;
  }

  const isBackspace = event.key === "Backspace" || event.code === "Backspace" || event.keyCode === 8;
  if (!isBackspace) {
    if (!['Control', 'Meta', 'Shift', 'Alt'].includes(event.key)) selectAllRequested = false;
    return;
  }

  const contentLength = Math.max(0, editor.value.getLength() - 1);
  const hasOneCharacter = Array.from(editor.value.getText(0, contentLength)).length === 1;
  if (!selectAllRequested && !isAllBrowserTextSelected() && !hasOneCharacter) return;

  // Quill 1.x reports this DOM selection two positions short even though the
  // browser selected every visible character. It can also fail to delete the
  // sole remaining character. Clear the canonical document directly.
  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation();
  editor.value.setText("", "user");
  editor.value.setSelection(0, 0, "silent");
  lastSelection.value = { index: 0, length: 0 };
  selectAllRequested = false;
  updateBlankState();
};

const handlePointerdown = () => {
  selectAllRequested = false;
};

const detachEditorListeners = () => {
  editorRoot.value?.removeEventListener("paste", handlePaste, { capture: true });
  editorRoot.value?.removeEventListener("keydown", handleKeydown, { capture: true });
  editorRoot.value?.removeEventListener("pointerdown", handlePointerdown, { capture: true });
  editor.value?.off("selection-change", handleSelectionChange);
  editor.value?.off("text-change", handleTextChange);
};

const handleReady = (quill: Quill) => {
  detachEditorListeners();
  editor.value = quill;
  editorRoot.value = quill.root;
  quill.on("selection-change", handleSelectionChange);
  quill.on("text-change", handleTextChange);
  syncEditorContent(props.modelValue);
  updateBlankState();
  editorRoot.value.addEventListener("paste", handlePaste, { capture: true });
  editorRoot.value.addEventListener("keydown", handleKeydown, { capture: true });
  editorRoot.value.addEventListener("pointerdown", handlePointerdown, { capture: true });
};

watch(
  () => props.modelValue,
  value => {
    const nextValue = value || "";

    // The parent echoing the value we just emitted must not rewrite Quill's
    // DOM, selection or blank state.
    if (nextValue === getEditorValue()) return;

    syncEditorContent(value);
  }
);

onBeforeUnmount(() => {
  detachEditorListeners();
  editorRoot.value = null;
  editor.value = null;
  lastSelection.value = null;
  selectAllRequested = false;
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
