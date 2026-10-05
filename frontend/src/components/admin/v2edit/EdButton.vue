<template>
  <EdGroup :title="title || 'Botão'">
    <EdToggle v-if="keys.enabled" :model-value="enabled" :label="toggleLabel || 'Mostrar botão'" @update:model-value="patch({ [keys.enabled!]: $event })" />
    <template v-if="enabled">
      <EdText :model-value="labelText" label="Texto do botão" :placeholder="placeholder" @update:model-value="patch({ [keys.label]: writeText(value[keys.label], $event) })" />
      <template v-if="!linkOnly">
        <EdSeg :model-value="uiMode" label="Ao clicar" :options="modeOptions" @update:model-value="setMode" />
        <label v-if="uiMode === 'section'" class="ved-field">
          <span class="ved-label">Seção</span>
          <select class="ved-select" :value="value[keys.section || 'ctaSectionId'] || ''" @change="patch({ [keys.mode!]: 'section', [keys.section!]: ($event.target as HTMLSelectElement).value || null })">
            <option value="">Escolher seção…</option>
            <option v-for="option in sectionOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
          </select>
          <p class="ved-hint">A página rola até a seção escolhida.</p>
        </label>
        <template v-else-if="uiMode === 'whatsapp'">
          <EdText :model-value="whatsapp.number" label="WhatsApp" type="tel" placeholder="(11) 99999-9999" @update:model-value="setWhatsapp($event, whatsapp.message)" />
          <EdText :model-value="whatsapp.message" label="Mensagem" multiline placeholder="Oi! Quero saber mais sobre o roteiro." @update:model-value="setWhatsapp(whatsapp.number, $event)" />
        </template>
      </template>
      <EdText
        v-if="linkOnly || uiMode === 'link'"
        :model-value="value[keys.link] || ''"
        label="Link"
        type="url"
        placeholder="https://"
        @update:model-value="patch({ ...(keys.mode ? { [keys.mode]: 'link' } : {}), [keys.link]: $event })"
      />
    </template>
  </EdGroup>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useAgencyStore } from "../../../store/useAgencyStore";
import type { PageSection } from "../../../types/page";
import { isWhatsappLink } from "../../../utils/links";
import { sectionNameV2 } from "../../../utils/sectionCatalogV2";
import { normalizeWhatsappDigits } from "../../../utils/whatsapp";
import { sectionsInjectionKey } from "../sectionsContext";
import EdGroup from "./EdGroup.vue";
import EdSeg from "./EdSeg.vue";
import EdText from "./EdText.vue";
import EdToggle from "./EdToggle.vue";
import { readText, writeText } from "./useDraft";

interface ButtonKeys {
  enabled?: string;
  label: string;
  mode?: string;
  link: string;
  section?: string;
}

const props = withDefaults(
  defineProps<{
    value: Record<string, any>;
    keys?: ButtonKeys;
    title?: string;
    toggleLabel?: string;
    placeholder?: string;
    /** Botão que só aceita link (sem rolar até seção). */
    linkOnly?: boolean;
  }>(),
  {
    keys: () => ({ enabled: "ctaEnabled", label: "ctaLabel", mode: "ctaMode", link: "ctaLink", section: "ctaSectionId" }),
    title: "",
    toggleLabel: "",
    placeholder: "Quero reservar",
    linkOnly: false
  }
);
const emit = defineEmits<{ (e: "patch", value: Record<string, any>): void }>();
const patch = (changes: Record<string, any>) => emit("patch", changes);

const enabled = computed(() => (props.keys.enabled ? props.value[props.keys.enabled] !== false : true));
const labelText = computed(() => readText(props.value[props.keys.label]));

const modeOptions = [
  { value: "whatsapp", label: "WhatsApp" },
  { value: "link", label: "Link" },
  { value: "section", label: "Seção" }
];
const dataMode = () => {
  if (props.keys.mode && props.keys.section && props.value[props.keys.mode] === "section") return "section";
  return isWhatsappLink(props.value[props.keys.link]) ? "whatsapp" : "link";
};
const uiMode = ref<"whatsapp" | "link" | "section">(dataMode());
watch(
  () => [props.value[props.keys.link], props.keys.mode ? props.value[props.keys.mode] : null],
  () => {
    const next = dataMode();
    // "WhatsApp" vazio ainda não tem link salvo: mantém a escolha da pessoa.
    if (!(uiMode.value === "whatsapp" && next === "link" && !props.value[props.keys.link])) uiMode.value = next;
  }
);

const agencyStore = useAgencyStore();
const agencyWhatsapp = computed(() => agencyStore.agencies.find(agency => agency.id === agencyStore.currentAgencyId)?.cta_whatsapp || "");

const whatsapp = computed(() => {
  const link = String(props.value[props.keys.link] || "");
  if (!isWhatsappLink(link)) return { number: "", message: "" };
  try {
    const url = new URL(link.startsWith("http") ? link : `https://${link}`);
    const digits = url.pathname.replace(/\D/g, "") || url.searchParams.get("phone") || "";
    return { number: digits, message: url.searchParams.get("text") || "" };
  } catch {
    return { number: link.replace(/\D/g, ""), message: "" };
  }
});
const setWhatsapp = (number: string, message: string) => {
  const digits = normalizeWhatsappDigits(number);
  const link = digits || message ? `https://wa.me/${digits}${message ? `?text=${encodeURIComponent(message)}` : ""}` : "";
  patch({ ...(props.keys.mode ? { [props.keys.mode]: "link" } : {}), [props.keys.link]: link });
};
const setMode = (mode: "whatsapp" | "link" | "section") => {
  uiMode.value = mode;
  if (mode === "section") {
    if (props.keys.mode) patch({ [props.keys.mode]: "section" });
  } else if (mode === "whatsapp" && !isWhatsappLink(props.value[props.keys.link])) {
    setWhatsapp(agencyWhatsapp.value, "");
  } else if (mode === "link") {
    patch({ ...(props.keys.mode ? { [props.keys.mode]: "link" } : {}), ...(isWhatsappLink(props.value[props.keys.link]) ? { [props.keys.link]: "" } : {}) });
  }
};

const sections = inject(sectionsInjectionKey, ref<PageSection[]>([]));
const sectionOptions = computed(() =>
  sections.value
    .map((section, index) => ({ section, index }))
    .filter(({ section }) => section?.enabled && section.anchorId && section.type !== "header" && section.anchorId !== props.value.anchorId)
    .map(({ section, index }) => ({ id: section.anchorId as string, label: `${index + 1}. ${sectionNameV2(section.type) || section.type}` }))
);
</script>
