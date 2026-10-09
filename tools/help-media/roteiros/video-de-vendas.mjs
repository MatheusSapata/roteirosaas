import { pagina } from '../lib/demo.mjs';

export default {
  id: 'video-de-vendas',
  titulo: 'Vídeo de Vendas (VSL)',
  rota: () => `/admin/pages/${pagina('aula-jalapao')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Vídeo de Vendas (VSL)', detalhe: 'Ela fica sempre no topo da página.', alvo: '.ed-section-main:has-text("Vídeo de Vendas")', esperar: 1400 },
    { legenda: 'Cole o link do vídeo', detalhe: 'YouTube, Vimeo ou Panda.', alvo: '#ved-panel-content .ved-group-head:has-text("Vídeo")' },
    { legenda: 'Liberação do botão: escolha o momento do vídeo', detalhe: 'O botão e o resto da página aparecem só a partir desse ponto.', alvo: '#ved-panel-content .ved-group-head:has-text("Liberação do botão")', esperar: 1300 },
    { legenda: 'Salve a seção', alvo: page => page.locator('.ed-section-panel button', { hasText: 'Salvar seção' }).first(), acao: 'nenhuma' },
  ],
};
