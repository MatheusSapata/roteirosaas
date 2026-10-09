/**
 * Mídia da Central de Ajuda, gerada por tools/help-media a partir do sistema rodando:
 * cada pasta em ./media/<id>/ tem passos.json, a tela de cada passo nos temas claro e
 * escuro (passo-NN-light.webp / passo-NN-dark.webp) e, às vezes, video.mp4.
 */
export interface HelpTourStep {
  legenda: string;
  detalhe?: string;
  /** Ponto de clique em % da tela (x, y, largura, altura); null na tela final. */
  ponto: { x: number; y: number; w: number; h: number } | null;
}

export interface HelpTour {
  id: string;
  titulo: string;
  gerado: string;
  passos: HelpTourStep[];
  telas: { light: string; dark: string }[];
  video?: string;
}

type TourJson = { id: string; titulo: string; gerado: string; passos: HelpTourStep[] };

const jsons = import.meta.glob<TourJson>("./media/*/passos.json", { eager: true, import: "default" });
const imagens = import.meta.glob<string>("./media/*/*.webp", { eager: true, query: "?url", import: "default" });
const videos = import.meta.glob<string>("./media/*/video.mp4", { eager: true, query: "?url", import: "default" });

const TOURS = new Map<string, HelpTour>();
for (const [caminho, dados] of Object.entries(jsons)) {
  const pasta = caminho.slice(0, caminho.lastIndexOf("/"));
  const telas = dados.passos.map((_, i) => {
    const n = String(i + 1).padStart(2, "0");
    return { light: imagens[`${pasta}/passo-${n}-light.webp`] || "", dark: imagens[`${pasta}/passo-${n}-dark.webp`] || "" };
  });
  TOURS.set(dados.id, { ...dados, telas, video: videos[`${pasta}/video.mp4`] });
}

export const getTour = (id?: string | null) => (id ? TOURS.get(id) || null : null);
