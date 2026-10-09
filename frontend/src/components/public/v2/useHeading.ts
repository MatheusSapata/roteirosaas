import { computed, type Ref } from "vue";
import type { SectionType } from "../../../types/page";
import { createLocalizer, getCurrentLanguage, type LocalizedString } from "../../../utils/i18n";
import { resolveHeadingAlign, resolveHeadingLabel } from "../../../utils/sectionHeadings";
import { plainTextToHtml, sanitizeHtml } from "../../../utils/sanitizeHtml";

export const localize = createLocalizer(getCurrentLanguage());

export const text = (value: LocalizedString) => localize(value).trim();
export const html = (value: LocalizedString) => sanitizeHtml(plainTextToHtml(localize(value))) || "";

interface HeadingFields {
  headingLabel?: LocalizedString;
  title?: LocalizedString;
  subtitle?: LocalizedString;
  headingAlign?: "left" | "center";
}

/**
 * Selo, título e texto de uma seção e o alinhamento escolhido. Só aparece o que está salvo:
 * campo vazio (ou que a seção antiga nem tinha) fica vazio, sem texto padrão no lugar.
 */
export const useHeading = (section: Ref<HeadingFields>, type: SectionType) => {
  const label = computed(() => resolveHeadingLabel(section.value.headingLabel, "", localize));
  const title = computed(() => text(section.value.title));
  const subtitleHtml = computed(() => (text(section.value.subtitle) ? html(section.value.subtitle) : ""));
  const align = computed(() => (resolveHeadingAlign(type, section.value.headingAlign) === "left" ? "start" : "center"));
  return { label, title, subtitleHtml, align };
};
