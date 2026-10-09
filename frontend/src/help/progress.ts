/** Passos de "Comece por aqui" marcados como feitos (fica só neste navegador). */
const CHAVE = "ro-help-feitos";

export const readHelpProgress = (): string[] => {
  try {
    const lista = JSON.parse(localStorage.getItem(CHAVE) || "[]");
    return Array.isArray(lista) ? lista.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
};

export const setHelpProgress = (id: string, feito: boolean) => {
  const atual = new Set(readHelpProgress());
  if (feito) atual.add(id);
  else atual.delete(id);
  try {
    localStorage.setItem(CHAVE, JSON.stringify([...atual]));
  } catch {
    /* navegador sem armazenamento: o progresso só não fica salvo */
  }
  return [...atual];
};
