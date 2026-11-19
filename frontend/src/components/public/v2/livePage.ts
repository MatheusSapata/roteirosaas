import type { ComputedRef, InjectionKey } from "vue";

/**
 * Só a página publicada (PublicPageView) fornece esta chave. Prévia do editor, miniaturas do
 * catálogo e criativos não fornecem: ali nada pode sair da tela (ex.: o redirecionamento).
 */
export const LIVE_PAGE_KEY: InjectionKey<boolean> = Symbol("live-page");

/**
 * Destino da logo do Banner Inicial e do Menu: a página principal da agência. Só a página
 * publicada fornece; vazio/ausente = a logo não redireciona (página principal, ou desligado).
 */
export const LOGO_HOME_PATH_KEY: InjectionKey<ComputedRef<string | null>> = Symbol("logo-home-path");
