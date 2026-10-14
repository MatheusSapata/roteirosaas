export default {
  id: 'plano-e-assinatura',
  titulo: 'Assinatura',
  rota: '/admin/perfil',
  pronto: page => page.locator('.pf-plan').first().waitFor(),
  passos: [
    { legenda: 'No Perfil, veja sua assinatura e a próxima renovação', alvo: '.pf-plan', acao: 'nenhuma' },
    { legenda: 'Clique em Ver assinatura', alvo: '.pf-plan-btn', esperar: 2000 },
    { legenda: 'Escolha mensal ou anual', detalhe: 'Os recursos são os mesmos: muda só a forma de pagar.', alvo: '.pv-cycle', acao: 'nenhuma' },
  ],
};
