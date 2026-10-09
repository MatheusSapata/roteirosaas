import { pagina, restaurarPagina } from '../lib/demo.mjs';

const restaurar = () => restaurarPagina('bonito-em-familia');

export default {
  id: 'editar-secao',
  titulo: 'Editar uma seção',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  video: true,
  antesDeTudo: restaurar,
  depoisDeTudo: restaurar,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique na seção em Camadas', detalhe: 'Ou passe o mouse nela na prévia e clique em Editar seção.', alvo: '.ed-section-main:has-text("Banner Inicial")', esperar: 1500 },
    { legenda: 'Abra o grupo que quer mudar', detalhe: 'Conteúdo tem textos, fotos e botões; Aparência tem layout e cores.', alvo: '.ved-group-head:has-text("Texto")' },
    { legenda: 'Troque o texto: a prévia muda na hora', alvo: page => page.locator('.ed-section-panel input').first(), acao: 'digitar', texto: 'Bonito com as crianças', esperar: 1400 },
    { legenda: 'Em Aparência, escolha o visual', alvo: '.ved-tab:has-text("Aparência")' },
    { legenda: 'Teste outro layout', alvo: page => page.locator('.ed-section-panel button', { hasText: 'Imersivo' }).first(), esperar: 1600 },
    { legenda: 'Clique em Salvar seção', detalhe: 'Descartar volta ao que estava antes.', alvo: page => page.locator('.ed-section-panel button', { hasText: 'Salvar seção' }).first(), acao: 'nenhuma' },
  ],
};
