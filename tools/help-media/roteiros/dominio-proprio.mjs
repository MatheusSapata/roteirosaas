export default {
  id: 'dominio-proprio',
  titulo: 'Usar um domínio próprio',
  rota: '/admin/domains',
  pronto: page => page.locator('.dm-form').first().waitFor(),
  passos: [
    { legenda: 'Em Domínios, digite o endereço', detalhe: 'Só o endereço, sem https://. Ex.: viagens.suaagencia.com.br', alvo: '.dm-form input', acao: 'digitar', texto: 'viagens.rotasul.com.br' },
    { legenda: 'Marque se ele vira o principal', detalhe: 'As páginas passam a abrir neste endereço quando ele for ativado.', alvo: '.dm-toggle-row', acao: 'nenhuma' },
    { legenda: 'Clique em Adicionar domínio', detalhe: 'Em seguida aparecem os registros de DNS para configurar no seu provedor.', alvo: page => page.locator('.dm-form button', { hasText: 'Adicionar domínio' }).first(), acao: 'nenhuma' },
    { legenda: 'Com o domínio ativo, envie o ícone da aba', alvo: '.dm-favicon', acao: 'nenhuma' },
  ],
};
