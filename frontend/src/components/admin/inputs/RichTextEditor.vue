<template>
  <div class="rich-text-editor" :class="{ 'is-article': variant === 'article' }">
    <div ref="editorHost"></div>
    <p v-if="uploadMessage" class="rte-status" :class="{ 'is-error': uploadFailed }">{{ uploadMessage }}</p>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import Quill, { type EmitterSource } from "quill";
import "quill/dist/quill.snow.css";
import { useAgencyStore } from "../../../store/useAgencyStore";
import { resolveMediaUrl, uploadImageFile } from "../../../utils/media";
import { toVideoEmbedUrl } from "../../../utils/video";

// Vídeo colado como link comum (YouTube, Vimeo) vira o endereço de incorporação.
const BaseVideo = Quill.import("formats/video") as any;
class EmbedVideo extends BaseVideo {
  static sanitize(url: string) {
    return toVideoEmbedUrl(url) || "about:blank";
  }
}
Quill.register(EmbedVideo as any, true);

type EditorDelta = ReturnType<Quill["getContents"]>;

const props = defineProps<{
  modelValue?: string;
  placeholder?: string;
  /** "article": texto longo, com títulos, citações, links, imagens e vídeos. */
  variant?: "basic" | "article";
  /** Sem o botão de alinhar: o alinhamento vem da seção, não do texto. */
  noAlign?: boolean;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: string): void }>();

const editorHost = ref<HTMLElement | null>(null);
let editor: Quill | null = null;
let lastEmittedValue = "";

const alignTools = [{ align: [] }];
const basicToolbar = [
  ["bold", "italic", "underline"],
  [{ list: "ordered" }, { list: "bullet" }],
  alignTools,
  ["clean"]
];
const articleToolbar = [
  [{ header: [2, 3, false] }],
  ["bold", "italic", "underline", "strike"],
  ["link", "blockquote"],
  [{ list: "ordered" }, { list: "bullet" }],
  [{ align: [] }],
  ["image", "video"],
  ["clean"]
];
const basicFormats = ["bold", "italic", "underline", "list", "indent", "align"];
const basicToolbarNoAlign = basicToolbar.filter(group => group !== alignTools);
const basicFormatsNoAlign = basicFormats.filter(format => format !== "align");
const articleFormats = [...basicFormats, "header", "strike", "link", "blockquote", "image", "video"];

const agencyStore = useAgencyStore();
const uploadMessage = ref("");
const uploadFailed = ref(false);
// Imagem do computador: envia para a biblioteca da agência e entra onde o cursor está.
const insertImage = () => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file || !editor) return;
    const index = editor.getSelection(true)?.index ?? editor.getLength();
    uploadFailed.value = false;
    uploadMessage.value = "Enviando imagem…";
    try {
      if (!agencyStore.currentAgencyId) await agencyStore.loadAgencies().catch(() => undefined);
      const agencyId = agencyStore.currentAgencyId;
      if (!agencyId) throw new Error("no-agency");
      const asset = await uploadImageFile(file, agencyId);
      editor?.insertEmbed(index, "image", resolveMediaUrl(asset.url) || asset.url, "user");
      editor?.setSelection(index + 1, 0, "silent");
      uploadMessage.value = "";
    } catch {
      uploadFailed.value = true;
      uploadMessage.value = "Não foi possível enviar a imagem. Tente de novo.";
    }
  };
  input.click();
};

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
      toolbar:
        props.variant === "article"
          ? { container: articleToolbar, handlers: { image: insertImage } }
          : props.noAlign
            ? basicToolbarNoAlign
            : basicToolbar,
      history: { userOnly: true }
    },
    formats: props.variant === "article" ? articleFormats : props.noAlign ? basicFormatsNoAlign : basicFormats,
    // A caixa de link/vídeo fica dentro do campo, sem sair pela lateral do painel.
    bounds: editorHost.value.parentElement || editorHost.value
  });
  const textbox = (editor.theme as any)?.tooltip?.textbox as HTMLInputElement | undefined;
  if (textbox) {
    textbox.dataset.link = "https://";
    textbox.dataset.video = "youtube.com/watch?v=… ou vimeo.com/…";
  }

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
.rte-status {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted-foreground);
}
.rte-status.is-error {
  color: #c2261c;
}

/* Artigo: área maior e mídia dentro do texto no mesmo jeito da página. */
.is-article :deep(.ql-editor) {
  min-height: 260px;
}
.is-article :deep(.ql-editor h2) {
  font-size: 1.45em;
  font-weight: 700;
  margin: 0.8em 0 0.3em;
}
.is-article :deep(.ql-editor h3) {
  font-size: 1.2em;
  font-weight: 700;
  margin: 0.7em 0 0.3em;
}
.is-article :deep(.ql-editor blockquote) {
  margin: 0.6em 0;
  padding-left: 12px;
  border-left: 3px solid var(--primary, #12b981);
  font-style: italic;
}
.is-article :deep(.ql-editor img) {
  display: block;
  max-width: 100%;
  margin: 8px 0;
  border-radius: 10px;
}
.is-article :deep(.ql-editor .ql-video) {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  height: auto;
  margin: 8px 0;
  border-radius: 10px;
}

/* Textos da barra e das caixas de link/vídeo em português. */
:deep(.ql-snow .ql-picker.ql-header .ql-picker-label::before),
:deep(.ql-snow .ql-picker.ql-header .ql-picker-item::before) {
  content: "Texto";
}
:deep(.ql-snow .ql-picker.ql-header .ql-picker-label[data-value="2"]::before),
:deep(.ql-snow .ql-picker.ql-header .ql-picker-item[data-value="2"]::before) {
  content: "Título";
}
:deep(.ql-snow .ql-picker.ql-header .ql-picker-label[data-value="3"]::before),
:deep(.ql-snow .ql-picker.ql-header .ql-picker-item[data-value="3"]::before) {
  content: "Subtítulo";
}
:deep(.ql-snow .ql-tooltip) {
  z-index: 20;
  border-radius: 10px;
}
/* No painel estreito a caixa ocupa a largura do campo e quebra a linha se precisar. */
:deep(.ql-snow .ql-tooltip.ql-editing) {
  left: 8px !important;
  right: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  white-space: normal;
}
:deep(.ql-snow .ql-tooltip.ql-editing input[type="text"]) {
  flex: 1 1 160px;
  width: auto;
  min-width: 0;
}
:deep(.ql-snow .ql-tooltip::before) {
  content: "Abrir link:";
}
:deep(.ql-snow .ql-tooltip[data-mode="link"]::before) {
  content: "Link:";
}
:deep(.ql-snow .ql-tooltip[data-mode="video"]::before) {
  content: "Link do YouTube ou Vimeo:";
}
:deep(.ql-snow .ql-tooltip a.ql-action::after) {
  content: "Editar";
}
:deep(.ql-snow .ql-tooltip a.ql-remove::before) {
  content: "Remover";
}
:deep(.ql-snow .ql-tooltip.ql-editing a.ql-action::after) {
  content: "Salvar";
}
</style>
