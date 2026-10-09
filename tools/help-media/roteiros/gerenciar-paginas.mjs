export default {
  id: 'gerenciar-paginas',
  titulo: 'Encontrar e gerenciar páginas',
  rota: '/admin/pages',
  pronto: page => page.locator('.pl-card').first().waitFor(),
  passos: [
    { legenda: 'Filtre por situação', detalhe: 'Todas, publicadas ou rascunhos.', alvo: '.pl-filters', acao: 'nenhuma' },
    { legenda: 'Busque pelo nome da página', alvo: '.pl-search input', acao: 'digitar', texto: 'Chile', esperar: 1200 },
    { legenda: 'Copie o link para divulgar', alvo: '.pl-card:has-text("Chile") .pl-link', acao: 'nenhuma' },
    { legenda: 'Visitas, cliques e leads de cada página', alvo: '.pl-card:has-text("Chile") .pl-metrics', acao: 'nenhuma' },
    { legenda: 'Abra o menu de ações', alvo: '.pl-card:has-text("Chile") .pl-icon-btn[aria-label="Mais ações"]' },
    { legenda: 'Duplique, defina como principal, despublique ou exclua', detalhe: 'A página principal abre no link da agência, sem o nome da página.', alvo: '.pl-card:has-text("Chile") .pl-menu', acao: 'nenhuma' },
  ],
};
