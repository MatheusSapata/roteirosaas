export default {
  id: 'configurar-agencia',
  titulo: 'Configurar os dados da agência',
  rota: '/admin/agency',
  video: true,
  pronto: page => page.locator('.as-row').first().waitFor(),
  passos: [
    { legenda: 'Em Minha Agência, confira o nome', detalhe: 'Aparece no topo e no rodapé das páginas.', alvo: '.as-row:has-text("Nome da agência") .as-row-field', acao: 'nenhuma' },
    { legenda: 'Escreva um resumo curto da agência', alvo: '.as-row:has-text("Sobre a agência") textarea', acao: 'digitar', texto: 'Roteiros em grupo pelo Brasil e América do Sul, com guia local e grupos pequenos.' },
    { legenda: 'O link da agência abre o endereço de todas as páginas', detalhe: 'roteiroonline.com/link-da-agencia/nome-da-pagina', alvo: '.as-row:has-text("Link da agência") .as-row-field', acao: 'nenhuma' },
    { legenda: 'Cor principal: a base dos botões', alvo: '.as-row:has-text("Cor principal") .as-row-field', acao: 'nenhuma' },
    { legenda: 'WhatsApp que recebe os cliques das páginas', alvo: '.as-row:has-text("WhatsApp") .as-row-field', acao: 'nenhuma' },
    { legenda: 'Logo e redes sociais entram em todas as páginas', alvo: '.as-row:has-text("Logo da agência") .as-row-field', acao: 'nenhuma' },
    { legenda: 'Salve para aplicar', alvo: page => page.locator('.as-savebar button').last(), acao: 'nenhuma' },
  ],
};
