import { limparPaginasNovas } from '../lib/demo.mjs';

export default {
  id: 'duplicar-pagina',
  titulo: 'Duplicar uma página',
  rota: '/admin/pages',
  video: true,
  antesDeTudo: limparPaginasNovas,
  depoisDeTudo: limparPaginasNovas,
  pronto: page => page.locator('.pl-card').first().waitFor(),
  passos: [
    { legenda: 'No card da página, abra o menu de ações', alvo: '.pl-card:has-text("Chile") .pl-icon-btn[aria-label="Mais ações"]' },
    { legenda: 'Clique em Duplicar', alvo: '.pl-card:has-text("Chile") .pl-menu button:has-text("Duplicar")', esperar: 1300 },
    { legenda: 'Dê um título à cópia', alvo: page => page.locator('input[placeholder="Novo título"]').first(), acao: 'digitar', texto: 'Chile: Atacama e Santiago' },
    { legenda: 'Confira o link da nova página', alvo: page => page.locator('input[placeholder="novo-slug"]').first(), acao: 'nenhuma' },
    { legenda: 'Clique em Duplicar', detalhe: 'A cópia nasce como rascunho, com todas as seções.', alvo: page => page.getByRole('button', { name: 'Duplicar', exact: true }).last(), esperar: 2400 },
    { legenda: 'Pronto: edite a cópia e publique quando quiser' },
  ],
};
