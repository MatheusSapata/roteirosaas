import { pagina, restaurarPagina } from '../lib/demo.mjs';

const restaurar = () => restaurarPagina('jalapao-6-dias');

export default {
  id: 'menu-do-topo',
  titulo: 'Menu do topo',
  rota: () => `/admin/pages/${pagina('jalapao-6-dias')}/edit`,
  antesDeTudo: restaurar,
  depoisDeTudo: restaurar,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Menu do topo', alvo: '.ed-section-main:has-text("Menu do topo")', esperar: 1400 },
    { legenda: 'Links: cada um leva a uma seção da página', detalhe: 'Até 7 links. O botão da direita pode abrir o WhatsApp.', alvo: '#ved-panel-content .ved-group-head:has-text("Links")' },
    { legenda: 'Em Aparência, escolha o fundo do menu', alvo: '.ved-tab:has-text("Aparência")' },
    { legenda: 'Transparente ou desfoque ficam sobre a foto da capa', detalhe: 'Ganham fundo quando o visitante rola a página.', alvo: page => page.locator('#ved-panel-look button', { hasText: 'Desfoque' }).first(), esperar: 1500 },
    { legenda: 'Clique em Salvar seção', alvo: page => page.locator('.ed-section-panel button', { hasText: 'Salvar seção' }).first(), acao: 'nenhuma' },
  ],
};
