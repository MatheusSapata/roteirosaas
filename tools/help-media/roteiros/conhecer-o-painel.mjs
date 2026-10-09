export default {
  id: 'conhecer-o-painel',
  titulo: 'Conhecer o painel',
  rota: '/admin/dashboard',
  pronto: page => page.locator('.metric-card').first().waitFor(),
  passos: [
    { legenda: 'O menu leva a todas as áreas', detalhe: 'Principal, Configurar e Aprender. O alfinete fixa o menu aberto.', alvo: page => page.locator('aside').first(), acao: 'nenhuma' },
    { legenda: 'Nova página, de qualquer tela', alvo: page => page.locator('aside button, aside a', { hasText: 'Nova página' }).first(), acao: 'nenhuma' },
    { legenda: 'Escolha o período do resumo', alvo: page => page.locator('.period-btn', { hasText: '30 dias' }).first(), esperar: 1500 },
    { legenda: 'Visitas, cliques, leads e páginas no ar', alvo: '.metrics-grid', acao: 'nenhuma' },
    { legenda: 'Do clique ao lead: onde as visitas se perdem', alvo: '.funnel', acao: 'nenhuma' },
    { legenda: 'Os leads que acabaram de chegar', detalhe: 'Chame no WhatsApp ou abra os detalhes direto daqui.', alvo: page => page.locator('.list-card', { hasText: 'Chegaram agora' }).first(), acao: 'nenhuma' },
  ],
};
