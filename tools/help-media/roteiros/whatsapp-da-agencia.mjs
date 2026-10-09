export default {
  id: 'whatsapp-da-agencia',
  titulo: 'Conectar o WhatsApp da agência',
  rota: '/admin/integracoes/atendimento',
  pronto: page => page.locator('.cv-panel').first().waitFor(),
  passos: [
    { legenda: 'Em Integrações > WhatsApp, veja a situação da conexão', alvo: '.cv-facts', acao: 'nenhuma' },
    { legenda: 'Clique em Conectar WhatsApp e leia o QR Code', detalhe: 'No celular: WhatsApp > Aparelhos conectados > Conectar aparelho.', alvo: page => page.locator('main button', { hasText: 'Conectar WhatsApp' }).first(), acao: 'nenhuma' },
    { legenda: 'Atualize o status para conferir se segue conectado', alvo: page => page.locator('main button', { hasText: 'Atualizar status' }).first(), acao: 'nenhuma' },
  ],
};
