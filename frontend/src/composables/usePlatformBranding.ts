// Marca da plataforma (Admin master › Marca e SEO): logo, favicon e cor. Sem nada configurado,
// valem os arquivos do projeto. Carrega uma vez por sessão e atualiza todas as telas juntas.
import { computed, reactive } from "vue";
import api from "../services/api";
import DefaultColorLogo from "../assets/Logo Cor - Roteiro Online.png";
import DefaultWhiteLogo from "../assets/Logo Branco - Roteiro Online.png";
import DefaultFavicon from "../assets/Favicon.png";

export interface PlatformBranding {
  logo_url: string | null;
  logo_dark_url: string | null;
  favicon_url: string | null;
  site_title: string;
  site_description: string;
  share_image_url: string | null;
  theme_color: string;
}

const state = reactive<{ data: PlatformBranding | null; loading: boolean }>({ data: null, loading: false });
let request: Promise<void> | null = null;

const isPlatformScreen = () => {
  if (typeof window === "undefined") return false;
  // Páginas públicas das agências cuidam do próprio favicon.
  return !document.body?.classList.contains("public-shell");
};

function applyHead(data: PlatformBranding) {
  if (typeof document === "undefined" || !isPlatformScreen()) return;
  if (data.favicon_url) {
    document.querySelectorAll<HTMLLinkElement>("link[rel='icon']").forEach(link => {
      link.href = data.favicon_url as string;
    });
  }
  const theme = document.querySelector<HTMLMetaElement>("meta[name='theme-color']");
  if (theme && data.theme_color) theme.content = data.theme_color;
}

export function loadPlatformBranding(force = false): Promise<void> {
  if (request && !force) return request;
  state.loading = true;
  request = api
    .get<PlatformBranding>("/public/platform-branding")
    .then(({ data }) => {
      state.data = data;
      applyHead(data);
    })
    .catch(() => {
      // Sem resposta, ficam os arquivos do projeto.
    })
    .finally(() => {
      state.loading = false;
    });
  return request;
}

export function setPlatformBranding(data: Partial<PlatformBranding>) {
  state.data = { ...(state.data || ({} as PlatformBranding)), ...data } as PlatformBranding;
  applyHead(state.data);
}

export function usePlatformBranding() {
  loadPlatformBranding();
  return {
    /** Logo colorido, para fundo claro. */
    logoColor: computed(() => state.data?.logo_url || DefaultColorLogo),
    /** Logo branco, para fundo escuro. */
    logoWhite: computed(() => state.data?.logo_dark_url || DefaultWhiteLogo),
    favicon: computed(() => state.data?.favicon_url || DefaultFavicon),
    branding: computed(() => state.data)
  };
}

export const defaultBrandAssets = { logoColor: DefaultColorLogo, logoWhite: DefaultWhiteLogo, favicon: DefaultFavicon };
