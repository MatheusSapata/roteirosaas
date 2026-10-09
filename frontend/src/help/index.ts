/**
 * CENTRAL DE AJUDA
 * Conteúdo em ./content.ts; mídia (telas, demonstrações e vídeos) em ./media, gerada por
 * tools/help-media. Ao mudar uma tela ou um fluxo do sistema:
 *   1. atualize o artigo em content.ts e a data `atualizado`;
 *   2. regenere a mídia do roteiro (`node gerar.mjs <id>` em tools/help-media);
 *   3. se o artigo cobre o assunto de uma aula, liste a aula em `substituiAulas`
 *      (ou ligue a aula ao artigo no Admin Master): enquanto o vídeo da aula for mais
 *      antigo que a data `atualizado`, a aula mostra o artigo no lugar dela. Um vídeo
 *      novo na aula faz ela voltar a aparecer.
 * Detalhes do gerador em tools/help-media/README.md.
 */
import type { Component } from "vue";
import { HELP_ARTICLES, HELP_MODULES, FIRST_STEPS } from "./content";

export type HelpModuleId = "comece" | "paginas" | "editor" | "secoes" | "leads" | "integracoes" | "agencia" | "conta";

export interface HelpModule {
  id: HelpModuleId;
  titulo: string;
  descricao: string;
  icone: Component;
}

export interface HelpStep {
  titulo: string;
  texto?: string;
  /** Passo da demonstração (1, 2…) que ilustra este passo; abre a demonstração nele. */
  tela?: number;
}

export type HelpBlock =
  | { tipo: "texto"; texto: string }
  | { tipo: "dica"; texto: string }
  | { tipo: "atencao"; texto: string }
  | { tipo: "lista"; titulo?: string; itens: string[] }
  | { tipo: "tabela"; titulo?: string; colunas: string[]; linhas: string[][] };

export interface HelpArticle {
  id: string;
  modulo: HelpModuleId;
  titulo: string;
  resumo: string;
  /** Data da última revisão (AAAA-MM-DD). Vale para trocar aulas mais antigas. */
  atualizado: string;
  /** Tela do sistema que o artigo explica. */
  rota?: string;
  rotaRotulo?: string;
  /** Palavras extras para a busca (sinônimos, nomes antigos). */
  busca?: string;
  /** Pasta da mídia em ./media (padrão: o próprio id). */
  demo?: string;
  passos?: HelpStep[];
  blocos?: HelpBlock[];
  duvidas?: [string, string][];
  relacionados?: string[];
  /** Trechos do título das aulas que este artigo substitui. */
  substituiAulas?: string[];
}

export { HELP_ARTICLES, HELP_MODULES, FIRST_STEPS };

const BY_ID = new Map(HELP_ARTICLES.map(article => [article.id, article]));

export const getArticle = (id?: string | null) => (id ? BY_ID.get(id) || null : null);
export const getModule = (id: HelpModuleId) => HELP_MODULES.find(module => module.id === id)!;
export const articlesOf = (id: HelpModuleId) => HELP_ARTICLES.filter(article => article.modulo === id);

export const normalizar = (texto: string) =>
  (texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

const textoDoArtigo = (article: HelpArticle) =>
  normalizar(
    [
      article.titulo,
      article.resumo,
      article.busca || "",
      ...(article.passos || []).flatMap(passo => [passo.titulo, passo.texto || ""]),
      ...(article.blocos || []).flatMap(bloco =>
        bloco.tipo === "lista" ? bloco.itens : bloco.tipo === "tabela" ? bloco.linhas.flat() : [bloco.texto]
      ),
      ...(article.duvidas || []).flat()
    ].join(" ")
  );

const INDICE = HELP_ARTICLES.map(article => ({ article, titulo: normalizar(article.titulo), texto: textoDoArtigo(article) }));

/** Busca por palavras (todas precisam aparecer); título pesa mais que o corpo. */
export const searchArticles = (consulta: string): HelpArticle[] => {
  const termos = normalizar(consulta).split(" ").filter(Boolean);
  if (!termos.length) return [];
  return INDICE.map(item => {
    if (!termos.every(termo => item.texto.includes(termo))) return null;
    const pontos = termos.reduce((soma, termo) => soma + (item.titulo.includes(termo) ? 3 : 1), 0);
    return { article: item.article, pontos };
  })
    .filter((item): item is { article: HelpArticle; pontos: number } => !!item)
    .sort((a, b) => b.pontos - a.pontos)
    .map(item => item.article);
};

/** Artigo que substitui a aula: o ligado a ela ou o que cita o título, se foi revisado depois do vídeo. */
export const articleReplacingLesson = (lesson: { titulo: string; artigo?: string | null; atualizadaEm?: string | null }) => {
  const ligado = getArticle(lesson.artigo || undefined);
  const titulo = normalizar(lesson.titulo);
  const artigo =
    ligado ||
    HELP_ARTICLES.find(article => (article.substituiAulas || []).some(trecho => titulo.includes(normalizar(trecho)))) ||
    null;
  if (!artigo) return null;
  const aula = (lesson.atualizadaEm || "").slice(0, 10);
  return !aula || artigo.atualizado >= aula ? artigo : null;
};

export const formatDate = (iso: string) => {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
};
