export default {
  id: 'criar-formulario',
  titulo: 'Criar um formulário de captação',
  rota: '/admin/leads/forms',
  video: true,
  pronto: page => page.locator('.lv-form-card').first().waitFor(),
  passos: [
    { legenda: 'Em Formulários, clique em Novo formulário', alvo: page => page.locator('main button', { hasText: 'Novo formulário' }).first(), esperar: 1500 },
    { legenda: 'Dê um nome interno', detalhe: 'Só você vê. Serve para achar o formulário depois.', alvo: '.fm-modal input[placeholder="ex: Captação Geral"]', acao: 'digitar', texto: 'Orçamento Bonito' },
    { legenda: 'Escreva o título que o visitante vê', alvo: '.fm-modal input[placeholder="ex: Quero receber mais informações"]', acao: 'digitar', texto: 'Receba o roteiro completo' },
    { legenda: 'Marque os campos que quer coletar', detalhe: 'Nome e WhatsApp bastam para começar a conversa.', alvo: '.fmf-chip:has-text("Nome completo")' },
    { legenda: 'Marque o WhatsApp', alvo: '.fmf-chip:has-text("Telefone")' },
    { legenda: 'A prévia mostra o formulário como o visitante vê', alvo: '.fm-right', acao: 'nenhuma' },
    { legenda: 'Notificação inteligente: mensagem automática no WhatsApp', detalhe: 'Disponível no plano Escala.', alvo: '.fm-tab-btn:has-text("Notificação inteligente")', esperar: 1300 },
    { legenda: 'Clique em Salvar alterações', alvo: page => page.locator('.fm-foot button', { hasText: 'Salvar alterações' }).first(), acao: 'nenhuma' },
  ],
};
