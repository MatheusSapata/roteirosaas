export default {
  id: 'etapas-do-funil',
  titulo: 'Etapas do funil',
  rota: '/admin/leads/settings',
  pronto: page => page.locator('.pipeline-step').first().waitFor(),
  passos: [
    { legenda: 'As etapas que suas oportunidades percorrem', alvo: '.pipeline-list', acao: 'nenhuma' },
    { legenda: 'Arraste pela alça para mudar a ordem', alvo: '.drag-handle', acao: 'nenhuma' },
    { legenda: 'Clique em Editar para mudar nome e cor', alvo: page => page.locator('main button', { hasText: 'Editar' }).first(), esperar: 1300 },
    { legenda: 'Troque o nome e a cor e salve', alvo: page => page.getByRole('button', { name: 'Salvar alterações' }).first(), acao: 'nenhuma' },
  ],
};
