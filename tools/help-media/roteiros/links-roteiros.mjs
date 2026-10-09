import { pagina } from '../lib/demo.mjs';

export default {
  id: 'links-roteiros',
  titulo: 'Links/Roteiros',
  rota: () => `/admin/pages/${pagina('chile-santiago-vinicolas')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Links/Roteiros', alvo: '.ed-section-main:has-text("Links/Roteiros")', esperar: 1400 },
    { legenda: 'Cada card leva para outra página ou link', detalhe: 'Cole o link de uma página sua e o card puxa título, foto e datas.', alvo: '#ved-panel-content .ved-group-head:has-text("Links/Roteiros")' },
    { legenda: 'Na prévia, as setas passam os cards', detalhe: 'Até 4 cards por vez no computador.', alvo: page => page.locator('.v2ed-sec', { hasText: 'Links/Roteiros' }).first(), acao: 'nenhuma' },
  ],
};
