import { pagina } from '../lib/demo.mjs';

export default {
  id: 'assistente-ia',
  titulo: 'Assistente IA',
  rota: () => `/admin/pages/${pagina('bonito-em-familia')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Assistente IA', alvo: '.ed-btn-ai', esperar: 1500 },
    { legenda: 'Comece por um atalho', detalhe: 'Montar a estrutura da página, melhorar a capa ou criar perguntas frequentes.', alvo: page => page.locator('.editor-ai-sidebar button', { hasText: 'Montar estrutura da página' }).first(), acao: 'nenhuma' },
    { legenda: 'Ou escreva o que precisa', detalhe: 'Mande também PDF, prints ou fotos com as informações da viagem.', alvo: '.editor-ai-sidebar textarea', acao: 'digitar', texto: 'Crie perguntas frequentes sobre o passeio em Bonito com crianças', esperar: 900 },
    { legenda: 'Envie e revise a sugestão antes de aplicar', detalhe: 'Você escolhe se insere as seções no fim ou substitui a estrutura.', alvo: page => page.locator('.editor-ai-sidebar button[aria-label]').last(), acao: 'nenhuma' },
  ],
};
