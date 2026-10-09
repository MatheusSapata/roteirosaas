/**
 * Quantos cards por linha para a grade ficar equilibrada: até `max` lado a lado e,
 * com mais, a quantidade que deixa menos card sobrando na última linha.
 */
export const balancedColumns = (count: number, max = 4) => {
  if (count <= max) return Math.max(1, count);
  if (count % max === 0) return max;
  if (count % (max - 1) === 0 || count % max === 1) return max - 1;
  return max;
};
