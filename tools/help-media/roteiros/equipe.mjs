export default {
  id: 'equipe',
  titulo: 'Convidar pessoas para a equipe',
  rota: '/admin/agency/team',
  pronto: page => page.locator('main button', { hasText: 'Convidar pessoa' }).first().waitFor(),
  passos: [
    { legenda: 'Em Minha Agência > Equipe, clique em Convidar pessoa', alvo: page => page.locator('main button', { hasText: 'Convidar pessoa' }).first(), esperar: 1200 },
    { legenda: 'Nome e e-mail de quem vai entrar', alvo: page => page.locator('input[placeholder="Nome"]').first(), acao: 'digitar', texto: 'Paulo Lima' },
    { legenda: 'O e-mail recebe o convite para criar a senha', alvo: page => page.locator('input[placeholder="E-mail"]').first(), acao: 'digitar', texto: 'paulo@rotasulviagens.com.br' },
    { legenda: 'Escolha o nível de acesso', detalhe: 'Admin, Editor, Visualizador ou Personalizado, área por área.', alvo: page => page.getByText('Visualizador', { exact: true }).first() },
    { legenda: 'Clique em Enviar convite', alvo: page => page.getByRole('button', { name: 'Enviar convite' }).first(), acao: 'nenhuma' },
  ],
};
