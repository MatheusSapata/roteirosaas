export default {
  id: 'faturas',
  titulo: 'Faturas do plano',
  rota: '/admin/agency/invoices',
  pronto: page => page.locator('.ai-stats').first().waitFor(),
  passos: [
    { legenda: 'A vencer, vencidas e pagas', alvo: '.ai-stats', acao: 'nenhuma' },
    { legenda: 'Filtre a lista por situação', alvo: '.ai-filters', acao: 'nenhuma' },
    { legenda: 'Cada fatura mostra valor, vencimento e o link de pagamento' },
  ],
};
