import { pagina } from '../lib/demo.mjs';
import { APP } from '../lib/api.mjs';

export default {
  id: 'pixel-meta-google',
  titulo: 'Pixel do Meta e Google Analytics',
  rota: '/admin/integracoes/rastreamento',
  video: true,
  pronto: page => page.locator('main').getByText('Códigos cadastrados').first().waitFor(),
  passos: [
    { legenda: 'Em Integrações > Rastreamento, clique em Novo código', alvo: page => page.locator('main button', { hasText: 'Novo código' }).first(), esperar: 1200 },
    { legenda: 'Dê um nome para reconhecer depois', alvo: page => page.locator('input[placeholder^="Ex.: Roteiro"]').first(), acao: 'digitar', texto: 'Meta campanha Jalapão' },
    { legenda: 'Escolha Meta ou Google', alvo: page => page.locator('select').filter({ hasText: 'Google' }).first(), acao: 'nenhuma' },
    { legenda: 'Cole o código do pixel ou o G- do Google', alvo: page => page.locator('input[placeholder^="Ex.: 1234567890"]').first(), acao: 'digitar', texto: '987654321012345' },
    {
      legenda: 'Salve a integração',
      alvo: page => page.getByRole('button', { name: 'Salvar integração' }).first(),
      acao: 'nenhuma',
      depois: async page => {
        await page.goto(`${APP}/admin/pages/${pagina('jalapao-6-dias')}/edit`, { waitUntil: 'networkidle' }).catch(() => {});
        await page.locator('.ed-section-main').first().waitFor();
      },
    },
    { legenda: 'Na página, abra Rastreamento', alvo: '.ed-rail-btn[aria-label="Rastreamento"]' },
    { legenda: 'Escolha o pixel e os eventos que quer enviar', detalhe: 'Page view, cliques em CTAs e leads (envios de formulário).', alvo: page => page.locator('.ed-side select').first(), acao: 'nenhuma' },
  ],
};
