import { limparPaginasNovas } from '../lib/demo.mjs';

export default {
  id: 'criar-pagina',
  titulo: 'Criar uma página',
  rota: '/admin/pages',
  video: true,
  antesDeTudo: limparPaginasNovas,
  pronto: page => page.locator('.pl-card').first().waitFor(),
  passos: [
    { legenda: 'Em Páginas, clique em Nova Página', alvo: page => page.locator('main button', { hasText: 'Nova Página' }).first() },
    { legenda: 'Escolha Criar página do zero', detalhe: 'Ou comece por um modelo pronto e troque só o conteúdo.', alvo: '.np-option:has-text("Criar página do zero")', esperar: 2500 },
    { legenda: 'A página nasce como rascunho e abre no editor', detalhe: 'Agora é só adicionar as seções.', alvo: page => page.getByRole('button', { name: /Adicionar (primeira )?seção/ }).first(), acao: 'nenhuma' },
  ],
};
