import { pagina } from '../lib/demo.mjs';

export default {
  id: 'cores-da-pagina',
  titulo: 'Cores da página',
  rota: () => `/admin/pages/${pagina('jalapao-6-dias')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Cores', alvo: '.ed-rail-btn[aria-label="Cores"]' },
    { legenda: 'Cor de destaque', detalhe: 'Vale para botões, selos e ícones de todas as seções.', alvo: '.ved-group-head:has-text("Cor de destaque")', acao: 'nenhuma' },
    { legenda: 'Fundo das seções', detalhe: 'As duas cores que as seções alternam no fundo.', alvo: '.ved-group-head:has-text("Fundo das seções")', esperar: 1300 },
    { legenda: 'Visual das seções', detalhe: 'Cantos, sombras e títulos de todas as seções de uma vez.', alvo: '.ved-group-head:has-text("Visual das seções")', esperar: 1300 },
    { legenda: 'Salve para aplicar na página publicada', alvo: page => page.locator('.ed-actions button', { hasText: 'Salvar' }).last(), acao: 'nenhuma' },
  ],
};
