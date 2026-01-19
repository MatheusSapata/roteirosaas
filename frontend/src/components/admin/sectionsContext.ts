import type { InjectionKey, Ref } from "vue";
import type { PageSection } from "../../types/page";

export const sectionsInjectionKey: InjectionKey<Ref<PageSection[]>> = Symbol("editor-sections");
