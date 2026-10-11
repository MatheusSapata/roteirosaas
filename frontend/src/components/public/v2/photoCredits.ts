import { computed, inject, type ComputedRef, type InjectionKey } from "vue";
import type { PageSection } from "../../../types/page";
import { resolveMediaUrl } from "../../../utils/media";

/** Crédito de uma foto de banco gratuito (Unsplash, Pexels), guardado na seção que a usa. */
export interface PhotoCredit {
  url: string;
  name: string;
  link?: string;
  provider: string;
  providerLink?: string;
}

export const PHOTO_CREDITS_KEY: InjectionKey<ComputedRef<Map<string, PhotoCredit>>> = Symbol("photo-credits");

/** Endereço → crédito, de todas as seções da página (só fotos ainda em uso na seção). */
export const buildPhotoCredits = (sections: PageSection[]): Map<string, PhotoCredit> => {
  const map = new Map<string, PhotoCredit>();
  for (const section of sections || []) {
    const credits = (section as { photoCredits?: PhotoCredit[] }).photoCredits;
    if (!Array.isArray(credits) || !credits.length) continue;
    const json = JSON.stringify(section);
    for (const credit of credits) {
      if (!credit?.url || !credit.name || json.split(credit.url).length <= 2) continue;
      // As seções mostram o endereço já resolvido ("/uploads/..." vira o endereço completo).
      map.set(credit.url, credit);
      const resolved = resolveMediaUrl(credit.url);
      if (resolved) map.set(resolved, credit);
    }
  }
  return map;
};

export const usePhotoCredit = (src: () => string | null | undefined) => {
  const credits = inject(PHOTO_CREDITS_KEY, null);
  return computed(() => {
    const url = src();
    return (url && credits?.value.get(url)) || null;
  });
};
