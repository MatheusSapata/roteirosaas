import { pagina } from '../lib/demo.mjs';

export default {
  id: 'titulo-e-link',
  titulo: 'Título, link e descrição da página',
  rota: () => `/admin/pages/${pagina('jalapao-6-dias')}/edit`,
  pronto: page => page.locator('.ed-section-main').first().waitFor(),
  passos: [
    { legenda: 'Clique em Título e link', alvo: '.ed-rail-btn[aria-label="Título e link"]' },
    { legenda: 'Título da página', detalhe: 'Aparece na aba do navegador, no Google e na sua lista de páginas.', alvo: page => page.locator('.ed-side label', { hasText: 'Título da página' }).first(), acao: 'nenhuma' },
    { legenda: 'Link da página', detalhe: 'É o endereço que você divulga. Só letras, números e hífens.', alvo: page => page.locator('.ed-side label', { hasText: 'Link da página' }).first(), acao: 'nenhuma' },
    { legenda: 'Descrição curta', detalhe: 'Aparece no Google e na prévia do link no WhatsApp.', alvo: page => page.locator('.ed-side label', { hasText: 'Descrição curta' }).first(), acao: 'nenhuma' },
  ],
};
