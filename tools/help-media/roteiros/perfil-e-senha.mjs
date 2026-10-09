export default {
  id: 'perfil-e-senha',
  titulo: 'Perfil e senha',
  rota: '/admin/perfil',
  pronto: page => page.locator('.pf-card').first().waitFor(),
  passos: [
    { legenda: 'Seu plano, renovação e forma de pagamento', alvo: '.pf-plan', acao: 'nenhuma' },
    { legenda: 'Atualize nome, foto e telefone', alvo: page => page.locator('.pf-card').filter({ hasText: 'Salvar dados' }).first(), acao: 'nenhuma' },
    { legenda: 'Troque a senha', detalhe: 'Mínimo de 8 caracteres, com maiúsculas, minúsculas e número.', alvo: page => page.locator('.pf-card').filter({ hasText: 'Alterar senha' }).first(), acao: 'nenhuma' },
  ],
};
