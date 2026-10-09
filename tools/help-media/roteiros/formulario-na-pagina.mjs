import { pagina } from '../lib/demo.mjs';

export default {
  id: 'formulario-na-pagina',
  titulo: 'Captar leads na página',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'No editor, clique em Captação de leads', alvo: '.ed-rail-btn[aria-label="Captação de leads"]' },
    { legenda: 'Escolha o formulário', detalhe: 'Ele abre antes do visitante ver a página.', alvo: '.ed-side select', acao: 'selecionar', valor: { index: 1 } },
    { legenda: 'Decida se o visitante pode fechar sem enviar', alvo: page => page.locator('.ed-side').getByText('Permitir fechar sem enviar').first(), acao: 'nenhuma' },
    { legenda: 'Clique em Ver prévia para testar', alvo: page => page.locator('.ed-side button', { hasText: 'Ver prévia' }).first(), esperar: 1800 },
    { legenda: 'É assim que o visitante vê. Salve a página para valer.' },
  ],
};
