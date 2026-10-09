import { pagina } from '../lib/demo.mjs';

export default {
  id: 'compra-online',
  titulo: 'Compra Online (Viaje On)',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em + Seção', alvo: '.ed-layers-add', esperar: 1500 },
    { legenda: 'Abra a categoria Venda', alvo: '.spk-chip:has-text("Venda")' },
    { legenda: 'Compra Online (Viaje On): pacotes com compra direta', detalhe: 'Sem a integração, o cartão fica travado e leva para conectar.', alvo: '.spk-card:has-text("Compra Online")', acao: 'nenhuma' },
  ],
};
