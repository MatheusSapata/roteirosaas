import { pagina } from '../lib/demo.mjs';

export default {
  id: 'conhecer-o-editor',
  titulo: 'Conhecer o editor',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Camadas: as seções da página, na ordem em que aparecem', detalhe: 'Clique numa camada para editar a seção.', alvo: '.ed-sections', acao: 'nenhuma' },
    { legenda: 'Prévia: a página como o visitante vê', detalhe: 'Passe o mouse numa seção da prévia para ver as ações dela.', alvo: '.ed-stage', acao: 'nenhuma' },
    { legenda: 'Veja como fica no celular', alvo: page => page.locator('button', { hasText: 'Celular' }).first(), esperar: 1600 },
    { legenda: 'Configurações da página', detalhe: 'Título e link, cores, rastreamento e captação de leads.', alvo: '.ed-rail', acao: 'nenhuma' },
    { legenda: 'O Assistente IA cria e ajusta seções com você', alvo: '.ed-btn-ai', acao: 'nenhuma' },
    { legenda: 'Salvar guarda as mudanças; Publicar coloca a página no ar', alvo: '.ed-actions', acao: 'nenhuma' },
  ],
};
