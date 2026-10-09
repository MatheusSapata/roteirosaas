export default {
  id: 'oportunidades',
  titulo: 'Acompanhar oportunidades',
  rota: '/admin/leads/opportunities',
  video: true,
  pronto: page => page.locator('.status-chip-button').first().waitFor(),
  passos: [
    { legenda: 'Cada etapa do funil, com contatos e valor', alvo: '.lv-stage-grid', acao: 'nenhuma' },
    { legenda: 'Filtre por etapa, página ou tempo sem interação', alvo: '.opportunities-filter-bar', acao: 'nenhuma' },
    { legenda: 'Mude a etapa direto na lista', alvo: '.status-chip-button', esperar: 900 },
    { legenda: 'Escolha a nova etapa', detalhe: 'O lead muda de grupo e o histórico registra a mudança.', alvo: '.status-dropdown-portal button:has-text("Em atendimento")', acao: 'nenhuma', depois: page => page.mouse.click(700, 60) },
    { legenda: 'Clique na oportunidade para abrir os detalhes', alvo: 'button[title="Ver oportunidade"]', esperar: 1600 },
    { legenda: 'Marque como ganha ou perdida, com valor e notas', detalhe: 'Vincule a um cliente para juntar todo o histórico dele.', alvo: page => page.getByRole('button', { name: 'Ganha' }).first(), acao: 'nenhuma' },
  ],
};
