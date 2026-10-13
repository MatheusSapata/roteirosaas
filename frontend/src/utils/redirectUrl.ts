/** Destino do Redirecionamento: só http(s) (nada de "javascript:" ou outros esquemas). */
export const safeRedirectUrl = (value?: string | null) => {
  const url = String(value || "").trim();
  return /^https?:\/\/[^\s]+$/i.test(url) ? url : "";
};
