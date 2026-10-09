import { pagina, restaurarPagina } from '../lib/demo.mjs';

const restaurar = () => restaurarPagina('jalapao-6-dias');

export default {
  id: 'organizar-secoes',
  titulo: 'Mudar a ordem, esconder e duplicar seções',
  rota: () => `/admin/pages/${pagina('jalapao-6-dias')}/edit`,
  antesDeTudo: restaurar,
  depoisDeTudo: restaurar,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Arraste a camada pela alça para mudar a ordem', alvo: '.ed-section-row:has-text("Diferenciais") .ed-grip', acao: 'nenhuma' },
    { legenda: 'O interruptor esconde a seção sem apagar', detalhe: 'Ela some da página publicada e volta quando você ligar de novo.', alvo: '.ed-section-row:has-text("Contagem") .ed-switch', esperar: 1400 },
    { legenda: 'Na prévia, passe o mouse sobre uma seção', alvo: '.v2ed-sec:has-text("Seis dias no coração")', acao: 'passar', esperar: 900 },
    { legenda: 'Suba, desça, duplique, esconda ou exclua por aqui', detalhe: 'Excluir pede confirmação; esconder é reversível.', alvo: '.v2ed-sec:has-text("Seis dias no coração") .v2ed-bar', acao: 'nenhuma', antes: page => page.locator('.v2ed-sec:has-text("Seis dias no coração")').first().hover() },
  ],
};
