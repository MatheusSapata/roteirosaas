import { pagina, restaurarPagina } from '../lib/demo.mjs';

const restaurar = () => restaurarPagina('bonito-em-familia');

export default {
  id: 'publicar-pagina',
  titulo: 'Publicar a página',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  video: true,
  antesDeTudo: restaurar,
  depoisDeTudo: restaurar,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Rascunho: só você vê a página', alvo: '.ed-pill', acao: 'nenhuma' },
    { legenda: 'Clique em Publicar', alvo: page => page.locator('.ed-actions button', { hasText: 'Publicar' }).first(), esperar: 2600 },
    { legenda: 'Pronto: a página está no ar', detalhe: 'Visualize para copiar o link e divulgar.', alvo: page => page.getByRole('button', { name: 'Visualizar página' }).last(), acao: 'nenhuma' },
  ],
};
