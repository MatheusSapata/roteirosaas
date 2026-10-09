import { pagina } from '../lib/demo.mjs';

export default {
  id: 'precos-e-pacotes',
  titulo: 'Preços e pacotes',
  rota: () => `/admin/pages/${pagina('jalapao-6-dias')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Preços e pacotes', alvo: '.ed-section-main:has-text("Preços e pacotes")', esperar: 1400 },
    { legenda: 'Ofertas: nome, preço, parcelas e o que está incluso', detalhe: 'Destaque a mais vendida com um selo.', alvo: '#ved-panel-content .ved-group-head:has-text("Ofertas")' },
    { legenda: 'Botão da oferta: WhatsApp, link ou formulário', alvo: '#ved-panel-content .ved-group-head:has-text("Botão da oferta")', esperar: 1300 },
    { legenda: 'Formas de pagamento aparecem embaixo dos preços', alvo: '#ved-panel-content .ved-group-head:has-text("Formas de pagamento")', acao: 'nenhuma' },
  ],
};
