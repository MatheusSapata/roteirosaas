export default {
  id: 'conectar-viajeon',
  titulo: 'Conectar o Viaje On',
  rota: '/admin/integracoes/viajeon',
  pronto: page => page.locator('main button', { hasText: 'Conectar Viaje On' }).first().waitFor(),
  passos: [
    { legenda: 'Em Integrações > Viaje On, clique em Conectar Viaje On', alvo: page => page.locator('main button', { hasText: 'Conectar Viaje On' }).first(), esperar: 1200 },
    { legenda: 'Cole o token e o secret do painel do Viaje On', detalhe: 'O secret fica guardado de forma criptografada.', alvo: page => page.locator('input[placeholder^="rvo_"]').first(), acao: 'nenhuma' },
    { legenda: 'Clique em Conectar e testar', detalhe: 'Depois, a seção Compra Online (Viaje On) fica liberada no editor.', alvo: page => page.getByRole('button', { name: 'Conectar e testar' }).first(), acao: 'nenhuma' },
  ],
};
