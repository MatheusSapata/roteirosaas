export default {
  id: 'clientes',
  titulo: 'Base de clientes',
  rota: '/admin/leads/clients',
  pronto: page => page.locator('main table tbody tr').first().waitFor(),
  passos: [
    { legenda: 'Busque por nome, CPF, telefone ou e-mail', alvo: page => page.locator('main input[type="search"], main input').first(), acao: 'nenhuma' },
    { legenda: 'Abra o cliente', alvo: 'main table tbody tr button >> nth=0', esperar: 1800 },
    { legenda: 'Oportunidades, notas, documentos e histórico em um lugar', detalhe: 'Daqui você chama no WhatsApp ou cria uma nova oportunidade.', alvo: page => page.locator('main button', { hasText: 'Nova oportunidade' }).first(), acao: 'nenhuma' },
  ],
};
