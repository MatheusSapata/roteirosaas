import { computed, type Ref } from "vue";

const plainLength = (value: string) => value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().length;

/** Quanto o título encolhe pelo tamanho do texto (1 = tamanho normal). */
export const titleScaleFor = (value: string) => {
  const length = plainLength(value || "");
  if (length <= 42) return 1;
  if (length <= 70) return 0.84;
  if (length <= 100) return 0.72;
  return 0.62;
};

/** Variável de CSS para títulos de seção: `--v2-title-scale` (usada no tamanho da letra). */
export const titleScaleStyle = (value: string) => {
  const scale = titleScaleFor(value);
  return scale === 1 ? undefined : { "--v2-title-scale": String(scale) };
};

/**
 * Capas e banners com texto longo: a letra diminui e o cartão alarga, em vez de a
 * seção crescer sem fim. Devolve variáveis de CSS (`--v2-title-scale`,
 * `--v2-sub-scale`, `--v2-card-grow`) que cada seção usa no próprio tamanho.
 */
export const useCopyFit = (title: Ref<string>, subtitle: Ref<string>) => {
  const titleLength = computed(() => plainLength(title.value));
  const subtitleLength = computed(() => plainLength(subtitle.value));
  const titleScale = computed(() => titleScaleFor(title.value));
  const subtitleScale = computed(() => {
    const length = subtitleLength.value;
    if (length <= 160) return 1;
    if (length <= 280) return 0.93;
    return 0.87;
  });
  // 0 = curto, 1 = longo, 2 = muito longo (soma título e texto).
  const level = computed(() => {
    const total = titleLength.value * 2 + subtitleLength.value;
    if (total > 420) return 2;
    if (total > 220) return 1;
    return 0;
  });
  const vars = computed(() => ({
    "--v2-title-scale": String(titleScale.value),
    "--v2-sub-scale": String(subtitleScale.value),
    "--v2-card-grow": `${level.value * 110}px`
  }));
  return { vars, level };
};
