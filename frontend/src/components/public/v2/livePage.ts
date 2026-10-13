import type { InjectionKey } from "vue";

/**
 * Só a página publicada (PublicPageView) fornece esta chave. Prévia do editor, miniaturas do
 * catálogo e criativos não fornecem: ali nada pode sair da tela (ex.: o redirecionamento).
 */
export const LIVE_PAGE_KEY: InjectionKey<boolean> = Symbol("live-page");
