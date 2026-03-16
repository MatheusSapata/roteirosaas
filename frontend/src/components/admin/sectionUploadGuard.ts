import type { InjectionKey } from "vue";

export interface SectionUploadGuard {
  setUploading(id: symbol, uploading: boolean): void;
}

export const sectionUploadGuardKey: InjectionKey<SectionUploadGuard> = Symbol("section-upload-guard");
