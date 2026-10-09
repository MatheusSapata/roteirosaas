export default {
  id: 'viajechat',
  titulo: 'Enviar leads para o ViajeChat',
  rota: '/admin/integracoes/viajechat',
  pronto: page => page.locator('main').getByText('Chave da API').first().waitFor(),
  passos: [
    { legenda: 'Em Integrações > ViajeChat, cole a chave da API', detalhe: 'A chave é gerada nas configurações do ViajeChat.', alvo: page => page.locator('main input[placeholder="Cole a chave aqui"]').first(), acao: 'nenhuma' },
    { legenda: 'Clique em Conectar', alvo: page => page.locator('main button', { hasText: 'Conectar' }).last(), acao: 'nenhuma' },
    { legenda: 'Depois, cada formulário escolhe o funil, a coluna e a etiqueta', detalhe: 'Em Captação de leads > Formulários, aba Destino do Lead.', alvo: page => page.locator('main').getByText('Configure isso em Captação de leads').first(), acao: 'nenhuma' },
  ],
};
