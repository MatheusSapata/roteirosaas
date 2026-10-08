import { computed, type Ref } from "vue";
import type { SectionType } from "../../../types/page";
import { createLocalizer, getCurrentLanguage, type LocalizedString } from "../../../utils/i18n";
import { getSectionHeadingDefaults, resolveHeadingAlign, resolveHeadingLabel } from "../../../utils/sectionHeadings";
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

/** Selo, título e texto de uma seção, com os mesmos padrões das seções antigas, e o alinhamento escolhido. */
export const useHeading = (section: Ref<HeadingFields>, type: SectionType, fallbackTitle: LocalizedString = "") => {
  const defaults = getSectionHeadingDefaults(type);
  const label = computed(() => resolveHeadingLabel(section.value.headingLabel, defaults.label, localize));
  const title = computed(() => text(section.value.title) || text(fallbackTitle));
  const subtitleHtml = computed(() => (text(section.value.subtitle) ? html(section.value.subtitle) : ""));
  const align = computed(() => (resolveHeadingAlign(type, section.value.headingAlign) === "left" ? "start" : "center"));
  return { label, title, subtitleHtml, align };
};
