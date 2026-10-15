/**
 * Aba aberta antes de um deploy: as telas do painel são carregadas sob demanda em arquivos com hash
 * no nome (ex.: ProfileView-D7dHXpBb.js). O deploy troca esses arquivos, e a aba antiga, ao abrir
 * uma tela que ainda não tinha carregado, pede um arquivo que não existe mais. Sem tratamento, o
 * clique "não faz nada" (a navegação é cancelada em silêncio). Aqui a página recarrega uma vez, já
 * no destino, e passa a usar a versão nova.
 */
const RELOAD_KEY = "stale_build_reload";
const RELOAD_WINDOW_MS = 15_000;

const CHUNK_ERROR =
  /Failed to fetch dynamically imported module|error loading dynamically imported module|Importing a module script failed|Unable to preload CSS|ChunkLoadError/i;

export const isStaleBuildError = (error: unknown) => {
  const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error ?? "");
  return CHUNK_ERROR.test(message);
};

/** Recarrega a página no caminho indicado; não repete se já recarregou há pouco (evita laço). */
export const reloadForNewBuild = (path?: string) => {
  if (typeof window === "undefined") return false;
  const target = path || `${window.location.pathname}${window.location.search}${window.location.hash}`;
  try {
    const last = JSON.parse(sessionStorage.getItem(RELOAD_KEY) || "null") as { path: string; at: number } | null;
    if (last && last.path === target && Date.now() - last.at < RELOAD_WINDOW_MS) return false;
    sessionStorage.setItem(RELOAD_KEY, JSON.stringify({ path: target, at: Date.now() }));
  } catch {
    // Sem sessionStorage (modo privado restrito): recarrega mesmo assim, uma vez por clique.
  }
  if (target !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
    window.history.pushState(window.history.state, "", target);
  }
  // reload (e não só trocar a URL) revalida o index.html e traz os arquivos do deploy novo.
  window.location.reload();
  return true;
};
