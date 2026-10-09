import { pagina, restaurarPagina } from '../lib/demo.mjs';

const restaurar = () => restaurarPagina('bonito-em-familia');

export default {
  id: 'adicionar-secao',
  titulo: 'Adicionar uma seção',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  video: true,
  antesDeTudo: restaurar,
  depoisDeTudo: restaurar,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Em Camadas, clique em + Seção', alvo: '.ed-layers-add', esperar: 1500 },
    { legenda: 'Escolha uma categoria', detalhe: 'Ou busque pelo nome da seção.', alvo: '.spk-chip:has-text("Detalhamento")' },
    { legenda: 'Clique na seção que quer inserir', detalhe: 'O cartão mostra a seção de verdade, com textos de exemplo.', alvo: '.spk-card:has-text("Roteiro dia a dia")', esperar: 2200 },
    { legenda: 'A seção entra no fim da página, antes do rodapé', detalhe: 'Clique nela para trocar os textos de exemplo.', alvo: '.ed-section-row:has-text("Roteiro dia a dia")', acao: 'nenhuma' },
    { legenda: 'Clique em Salvar para guardar', alvo: page => page.locator('.ed-actions button', { hasText: 'Salvar' }).last(), acao: 'nenhuma' },
  ],
};
