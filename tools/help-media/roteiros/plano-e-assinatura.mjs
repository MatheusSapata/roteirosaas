export default {
  id: 'plano-e-assinatura',
  titulo: 'Planos e assinatura',
  rota: '/admin/perfil',
  pronto: page => page.locator('.pf-plan').first().waitFor(),
  passos: [
    { legenda: 'No Perfil, veja o plano atual e a próxima renovação', alvo: '.pf-plan', acao: 'nenhuma' },
    { legenda: 'Clique em Ver planos', alvo: '.pf-plan-btn', esperar: 2000 },
    { legenda: 'Compare os planos e mude quando quiser', detalhe: 'O plano atual aparece marcado.' },
  ],
};
